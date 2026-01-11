from decimal import Decimal, ROUND_DOWN
from datetime import timedelta, datetime
from django.db import transaction
from django.utils import timezone
from apps.core.models import DailyBar, DailyMetric, Alert, JobLog
from apps.backtesting.models import (
    BacktestRun, BacktestTrade, BacktestDailyStat, 
    BacktestRunSymbolSetting
)

class BacktestEngine:
    """Moteur d'exécution des backtests"""
    
    def __init__(self, run: BacktestRun):
        self.run = run
        self.scenario = run.scenario
        self.strategy = run.strategy
        self.CP = run.CP
        self.CT = run.CT
        self.X = run.X
        
        # Charger les règles
        self.buy_rules = {}
        self.sell_rules = {}
        
        for rule in run.strategy.rules.all():
            if rule.action == 'BUY':
                self.buy_rules[rule.signal] = rule
            else:
                self.sell_rules[rule.signal] = rule
        
        # État par ticker
        self.ticker_states = {}
    
    class TickerState:
        """État d'un ticker pendant le backtest"""
        def __init__(self, symbol, CT):
            self.symbol = symbol
            self.cash = CT
            self.position_qty = 0
            self.position_entry_price = None
            self.position_entry_date = None
            
            # Statistiques
            self.N = 0
            self.gains = []
            self.trades_history = []
            self.pending_orders = []
    
    def run_backtest(self):
        """Exécution principale du backtest"""
        try:
            JobLog.log('backtest', 'INFO', f'Starting backtest run {self.run.id}')
            
            self.run.status = 'RUNNING'
            self.run.started_at = timezone.now()
            self.run.save(update_fields=['status', 'started_at'])
            
            # 1. Récupérer les tickers du scénario
            symbols = self.scenario.symbols.filter(is_active=True)
            
            if not symbols.exists():
                raise ValueError("No active symbols in scenario")
            
            # 2. Déterminer la période
            self._determine_date_range(symbols)
            
            # 3. Initialiser l'état des tickers
            self._initialize_ticker_states(symbols)
            
            # 4. Charger les données en cache
            JobLog.log('backtest', 'INFO', 'Loading data into cache...')
            bars_cache = self._load_bars_cache(symbols)
            metrics_cache = self._load_metrics_cache(symbols)
            alerts_cache = self._load_alerts_cache(symbols)
            
            # 5. Parcourir chaque jour
            current_date = self.run.date_start
            nb_jours_ouvres = 0
            
            while current_date <= self.run.date_end:
                # Tickers tradables ce jour
                tradable_symbols = self._get_tradable_symbols(current_date, metrics_cache)
                
                if tradable_symbols:
                    nb_jours_ouvres += 1
                
                # Exécuter les ordres en attente (J+1)
                self._execute_pending_orders(current_date, bars_cache)
                
                # Détecter de nouveaux signaux
                self._detect_signals(current_date, tradable_symbols, alerts_cache)
                
                # Sauvegarder les stats du jour
                self._save_daily_stats(current_date)
                
                current_date += timedelta(days=1)
            
            # 6. Clôturer les positions restantes
            self._close_all_positions(self.run.date_end, bars_cache)
            
            # 7. Calculer les résultats globaux
            self._calculate_global_results(nb_jours_ouvres)
            
            self.run.status = 'COMPLETED'
            self.run.completed_at = timezone.now()
            self.run.nb_jours_ouvres = nb_jours_ouvres
            self.run.save()
            
            JobLog.log('backtest', 'INFO', f'Backtest {self.run.id} completed successfully')
            
            return {'success': True}
            
        except Exception as e:
            self.run.status = 'FAILED'
            self.run.error_message = str(e)
            self.run.completed_at = timezone.now()
            self.run.save()
            
            JobLog.log('backtest', 'ERROR', f'Backtest {self.run.id} failed: {str(e)}')
            raise
    
    def _determine_date_range(self, symbols):
        """Déterminer la période du backtest"""
        min_dates = []
        max_dates = []
        
        for symbol in symbols:
            first_bar = DailyBar.objects.filter(symbol=symbol).order_by('date').first()
            last_bar = DailyBar.objects.filter(symbol=symbol).order_by('-date').first()
            
            if first_bar and last_bar:
                min_dates.append(first_bar.date)
                max_dates.append(last_bar.date)
        
        if not min_dates:
            raise ValueError("No historical data available")
        
        self.run.date_start = max(min_dates)
        self.run.date_end = min(max_dates)
        self.run.save(update_fields=['date_start', 'date_end'])
        
        JobLog.log('backtest', 'INFO', 
                  f'Date range: {self.run.date_start} to {self.run.date_end}')
    
    def _initialize_ticker_states(self, symbols):
        """Initialiser l'état de chaque ticker"""
        for symbol in symbols:
            override = BacktestRunSymbolSetting.objects.filter(
                run=self.run, symbol=symbol
            ).first()
            
            CT = override.CT_override if override else self.CT
            self.ticker_states[symbol.id] = self.TickerState(symbol, CT)
    
    def _load_bars_cache(self, symbols):
        """Charger toutes les barres en mémoire"""
        bars = DailyBar.objects.filter(
            symbol__in=symbols,
            date__gte=self.run.date_start,
            date__lte=self.run.date_end
        ).select_related('symbol').order_by('date')
        
        cache = {}
        for bar in bars:
            if bar.symbol_id not in cache:
                cache[bar.symbol_id] = {}
            cache[bar.symbol_id][bar.date] = bar
        
        return cache
    
    def _load_metrics_cache(self, symbols):
        """Charger toutes les métriques"""
        metrics = DailyMetric.objects.filter(
            symbol__in=symbols,
            scenario=self.scenario,
            date__gte=self.run.date_start,
            date__lte=self.run.date_end
        ).select_related('symbol')
        
        cache = {}
        for metric in metrics:
            if metric.symbol_id not in cache:
                cache[metric.symbol_id] = {}
            cache[metric.symbol_id][metric.date] = metric
        
        return cache
    
    def _load_alerts_cache(self, symbols):
        """Charger toutes les alertes"""
        alerts = Alert.objects.filter(
            symbol__in=symbols,
            scenario=self.scenario,
            date__gte=self.run.date_start,
            date__lte=self.run.date_end
        ).select_related('symbol')
        
        cache = {}
        for alert in alerts:
            if alert.symbol_id not in cache:
                cache[alert.symbol_id] = {}
            cache[alert.symbol_id][alert.date] = alert
        
        return cache
    
    def _get_tradable_symbols(self, date, metrics_cache):
        """Récupérer les tickers tradables (ratio_P >= X)"""
        tradable = []
        
        for symbol_id, state in self.ticker_states.items():
            if symbol_id not in metrics_cache:
                continue
            
            metric = metrics_cache[symbol_id].get(date)
            if not metric or metric.ratio_P is None:
                continue
            
            if metric.ratio_P >= self.X:
                tradable.append({
                    'symbol_id': symbol_id,
                    'ratio_P': metric.ratio_P,
                    'state': state,
                })
        
        # Trier par ratio_P décroissant
        tradable.sort(key=lambda x: x['ratio_P'], reverse=True)
        
        return tradable
    
    def _detect_signals(self, date, tradable_symbols, alerts_cache):
        """Détecter les signaux BUY/SELL"""
        for item in tradable_symbols:
            symbol_id = item['symbol_id']
            state = item['state']
            
            if symbol_id not in alerts_cache:
                continue
            
            alert = alerts_cache[symbol_id].get(date)
            if not alert:
                continue
            
            alert_codes = alert.get_alerts_list()
            
            # BUY si pas de position
            if state.position_qty == 0:
                for signal in alert_codes:
                    if signal in self.buy_rules:
                        state.pending_orders.append({
                            'signal_date': date,
                            'action': 'BUY',
                            'signal': signal,
                        })
                        break
            
            # SELL si position ouverte
            elif state.position_qty > 0:
                for signal in alert_codes:
                    if signal in self.sell_rules:
                        state.pending_orders.append({
                            'signal_date': date,
                            'action': 'SELL',
                            'signal': signal,
                        })
                        break
    
    def _execute_pending_orders(self, execution_date, bars_cache):
        """Exécuter les ordres en attente (prix Open du jour)"""
        for symbol_id, state in self.ticker_states.items():
            if not state.pending_orders:
                continue
            
            if symbol_id not in bars_cache or execution_date not in bars_cache[symbol_id]:
                continue
            
            bar = bars_cache[symbol_id][execution_date]
            execution_price = bar.open
            
            for order in state.pending_orders:
                if order['action'] == 'BUY':
                    self._execute_buy(state, order, execution_date, execution_price)
                else:
                    self._execute_sell(state, order, execution_date, execution_price)
            
            state.pending_orders = []
    
    def _execute_buy(self, state, order, execution_date, price):
        """Exécuter un ordre BUY"""
        if state.position_qty > 0:
            return
        
        cash_available = state.cash
        qty = int(cash_available / price)
        
        if qty <= 0:
            return
        
        cost = qty * price
        cash_before = state.cash
        state.cash -= cost
        state.position_qty = qty
        state.position_entry_price = price
        state.position_entry_date = order['signal_date']
        
        trade = BacktestTrade(
            run=self.run,
            symbol=state.symbol,
            signal_date=order['signal_date'],
            execution_date=execution_date,
            action='BUY',
            signal=order['signal'],
            quantity=qty,
            price=price,
            cash_before=cash_before,
            cash_after=state.cash,
        )
        
        state.trades_history.append(trade)
    
    def _execute_sell(self, state, order, execution_date, price):
        """Exécuter un ordre SELL"""
        if state.position_qty <= 0:
            return
        
        qty = state.position_qty
        proceeds = qty * price
        
        gain_pct = ((price - state.position_entry_price) / state.position_entry_price) * Decimal('100')
        
        cash_before = state.cash
        state.cash += proceeds
        state.position_qty = 0
        
        state.N += 1
        state.gains.append(gain_pct)
        
        trade = BacktestTrade(
            run=self.run,
            symbol=state.symbol,
            signal_date=order['signal_date'],
            execution_date=execution_date,
            action='SELL',
            signal=order['signal'],
            quantity=qty,
            price=price,
            cash_before=cash_before,
            cash_after=state.cash,
            gain_pct=gain_pct,
        )
        
        state.trades_history.append(trade)
        state.position_entry_price = None
        state.position_entry_date = None
    
    def _close_all_positions(self, last_date, bars_cache):
        """Clôturer toutes les positions en fin de backtest"""
        for symbol_id, state in self.ticker_states.items():
            if state.position_qty > 0:
                if symbol_id in bars_cache and last_date in bars_cache[symbol_id]:
                    bar = bars_cache[symbol_id][last_date]
                    
                    order = {
                        'signal_date': last_date,
                        'signal': 'FORCED_CLOSE',
                    }
                    
                    self._execute_sell(state, order, last_date, bar.close)
    
    def _save_daily_stats(self, date):
        """Sauvegarder les statistiques du jour"""
        stats_to_create = []
        
        for symbol_id, state in self.ticker_states.items():
            S_G_N = sum(state.gains) / len(state.gains) if state.gains else Decimal('0')
            BT = S_G_N * Decimal(state.N)
            
            stat = BacktestDailyStat(
                run=self.run,
                symbol=state.symbol,
                date=date,
                N=state.N,
                G=state.gains[-1] if state.gains else None,
                S_G_N=S_G_N,
                BT=BT,
                cash=state.cash,
                position_qty=state.position_qty,
            )
            
            stats_to_create.append(stat)
        
        if stats_to_create:
            BacktestDailyStat.objects.bulk_create(
                stats_to_create,
                update_conflicts=True,
                update_fields=['N', 'G', 'S_G_N', 'BT', 'cash', 'position_qty'],
                unique_fields=['run', 'symbol', 'date']
            )
    
    def _calculate_global_results(self, nb_jours_ouvres):
        """Calculer les résultats globaux"""
        all_trades = []
        for state in self.ticker_states.values():
            all_trades.extend(state.trades_history)
        
        if all_trades:
            BacktestTrade.objects.bulk_create(all_trades)
        
        total_N = sum(state.N for state in self.ticker_states.values())
        
        if total_N > 0:
            all_gains = []
            for state in self.ticker_states.values():
                all_gains.extend(state.gains)
            
            global_S_G_N = sum(all_gains) / len(all_gains) if all_gains else Decimal('0')
            total_BT = global_S_G_N * Decimal(total_N)
            
            if nb_jours_ouvres > 0:
                total_BMJ = total_BT / Decimal(nb_jours_ouvres)
            else:
                total_BMJ = Decimal('0')
        else:
            total_BT = Decimal('0')
            total_BMJ = Decimal('0')
        
        self.run.total_BT = total_BT
        self.run.total_BMJ = total_BMJ
        self.run.total_trades = len(all_trades)
        self.run.save(update_fields=['total_BT', 'total_BMJ', 'total_trades'])
        
        # Calculer BMJ pour chaque stat
        if nb_jours_ouvres > 0:
            stats = BacktestDailyStat.objects.filter(run=self.run)
            for stat in stats:
                if stat.BT is not None:
                    stat.BMJ = stat.BT / Decimal(nb_jours_ouvres)
            
            BacktestDailyStat.objects.bulk_update(stats, ['BMJ'])
