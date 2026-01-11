from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.db import transaction
from apps.core.models import Symbol, Scenario, DailyBar, DailyMetric, Alert, JobLog

class MetricsCalculator:
    """Moteur de calcul des indicateurs"""
    
    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.a = scenario.a
        self.b = scenario.b
        self.c = scenario.c
        self.d = scenario.d
        self.e = scenario.e
        self.N1 = scenario.N1
        self.N2 = scenario.N2
        self.N3 = scenario.N3
        self.N4 = scenario.N4
    
    def calculate_P(self, bar: DailyBar) -> Decimal:
        """P = (a*Close + b*High + c*Low + d*Open) / (a+b+c+d)"""
        denom = self.a + self.b + self.c + self.d
        if denom == 0:
            raise ValueError("Sum of a,b,c,d cannot be 0")
        
        P = (self.a * bar.close + self.b * bar.high + 
             self.c * bar.low + self.d * bar.open) / denom
        
        return P.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_M_X(self, P_cache: dict, date) -> tuple:
        """M = max(P) sur N1, X = min(P) sur N1"""
        recent_dates = sorted([d for d in P_cache.keys() if d <= date], reverse=True)[:self.N1]
        
        if len(recent_dates) < self.N1:
            return None, None
        
        P_list = [P_cache[d] for d in recent_dates]
        M = max(P_list)
        X = min(P_list)
        
        return M, X
    
    def calculate_M1_X1(self, M_cache: dict, X_cache: dict, date) -> tuple:
        """M1 = moyenne(M) sur N2, X1 = moyenne(X) sur N2"""
        recent_dates = sorted([d for d in M_cache.keys() if d <= date], reverse=True)[:self.N2]
        
        if len(recent_dates) < self.N2:
            return None, None
        
        M_list = [M_cache[d] for d in recent_dates]
        X_list = [X_cache[d] for d in recent_dates]
        
        M1 = sum(M_list) / len(M_list)
        X1 = sum(X_list) / len(X_list)
        
        return M1, X1
    
    def calculate_canal(self, M1: Decimal, X1: Decimal) -> tuple:
        """T = (M1 - X1)/e, Q = M1 - T, S = M1 + T"""
        if self.e == 0:
            raise ValueError("Parameter 'e' cannot be 0")
        
        T = (M1 - X1) / self.e
        Q = M1 - T
        S = M1 + T
        
        return T, Q, S
    
    def calculate_signals(self, P: Decimal, M1: Decimal, X1: Decimal, Q: Decimal, S: Decimal) -> dict:
        """K1 = P - M1, K2 = P - X1, K3 = P - Q, K4 = P - S"""
        return {
            'K1': P - M1,
            'K2': P - X1,
            'K3': P - Q,
            'K4': P - S,
        }
    
    def calculate_V(self, close: Decimal, prev_close: Decimal) -> Decimal:
        """V = (Close - Close_prev) * 100 / Close_prev"""
        if prev_close == 0:
            return Decimal('0')
        
        V = (close - prev_close) * Decimal('100') / prev_close
        return V.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_slope_P(self, V_cache: dict, date) -> Decimal:
        """slope_P = moyenne(V) sur N3"""
        recent_dates = sorted([d for d in V_cache.keys() if d <= date], reverse=True)[:self.N3]
        
        if len(recent_dates) < self.N3:
            return None
        
        V_list = [V_cache[d] for d in recent_dates]
        slope_P = sum(V_list) / len(V_list)
        
        return slope_P.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    
    def calculate_ratio_P_amp_h(self, slope_P_cache: dict, date) -> tuple:
        """
        ratio_P = nb_pos * 100 / N4 (%)
        amp_h = sum_pos * 100 / (nb_pos * N3) (%)
        """
        recent_dates = sorted([d for d in slope_P_cache.keys() if d <= date], reverse=True)[:self.N4]
        
        if len(recent_dates) < self.N4:
            return None, None
        
        slope_list = [slope_P_cache[d] for d in recent_dates]
        positive_slopes = [s for s in slope_list if s > 0]
        
        nb_pos = len(positive_slopes)
        sum_pos = sum(positive_slopes)
        
        ratio_P = (Decimal(nb_pos) * Decimal('100')) / Decimal(self.N4)
        
        if nb_pos > 0:
            amp_h = (sum_pos * Decimal('100')) / (Decimal(nb_pos) * Decimal(self.N3))
        else:
            amp_h = Decimal('0')
        
        return (
            ratio_P.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            amp_h.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
    
    def detect_alerts(self, K_values: dict, prev_K_values: dict) -> list:
        """Détecter les crossings et générer les alertes A1..H1"""
        if not prev_K_values:
            return []
        
        alerts = []
        
        # K1 -> A1/B1
        if prev_K_values['K1'] < 0 and K_values['K1'] > 0:
            alerts.append('A1')
        elif prev_K_values['K1'] > 0 and K_values['K1'] < 0:
            alerts.append('B1')
        
        # K2 -> C1/D1
        if prev_K_values['K2'] < 0 and K_values['K2'] > 0:
            alerts.append('C1')
        elif prev_K_values['K2'] > 0 and K_values['K2'] < 0:
            alerts.append('D1')
        
        # K3 -> E1/F1
        if prev_K_values['K3'] < 0 and K_values['K3'] > 0:
            alerts.append('E1')
        elif prev_K_values['K3'] > 0 and K_values['K3'] < 0:
            alerts.append('F1')
        
        # K4 -> G1/H1
        if prev_K_values['K4'] < 0 and K_values['K4'] > 0:
            alerts.append('G1')
        elif prev_K_values['K4'] > 0 and K_values['K4'] < 0:
            alerts.append('H1')
        
        return alerts
    
    def compute_symbol_incremental(self, symbol: Symbol):
        """Calcul incrémental pour un ticker"""
        # Trouver la dernière métrique calculée
        last_metric = DailyMetric.objects.filter(
            symbol=symbol,
            scenario=self.scenario
        ).order_by('-date').first()
        
        start_date = last_metric.date + timedelta(days=1) if last_metric else None
        
        # Récupérer toutes les barres nécessaires
        max_period = max(self.N1, self.N2, self.N3, self.N4)
        lookback_date = (start_date or datetime.now().date()) - timedelta(days=max_period + 30)
        
        bars = DailyBar.objects.filter(
            symbol=symbol,
            date__gte=lookback_date
        ).order_by('date')
        
        if bars.count() < max_period:
            JobLog.log('compute_metrics', 'WARNING', 
                      f"{symbol.code}: Données insuffisantes ({bars.count()} bars, besoin de {max_period})")
            return {'success': False, 'reason': 'insufficient_data'}
        
        # Caches
        P_cache = {}
        M_cache = {}
        X_cache = {}
        V_cache = {}
        slope_P_cache = {}
        
        metrics_to_create = []
        alerts_to_create = []
        
        prev_close = None
        prev_K_values = None
        
        for bar in bars:
            # 1. Calculer P
            P = self.calculate_P(bar)
            P_cache[bar.date] = P
            
            # 2. Calculer M, X
            M, X = self.calculate_M_X(P_cache, bar.date)
            if M is None:
                continue
            
            M_cache[bar.date] = M
            X_cache[bar.date] = X
            
            # 3. Calculer M1, X1
            M1, X1 = self.calculate_M1_X1(M_cache, X_cache, bar.date)
            if M1 is None:
                continue
            
            # 4. Calculer canal
            try:
                T, Q, S = self.calculate_canal(M1, X1)
            except ValueError as e:
                JobLog.log('compute_metrics', 'ERROR', f"{symbol.code} {bar.date}: {e}")
                continue
            
            # 5. Calculer signaux
            K_values = self.calculate_signals(P, M1, X1, Q, S)
            
            # 6. Calculer V
            if prev_close:
                V = self.calculate_V(bar.close, prev_close)
                V_cache[bar.date] = V
            else:
                V = None
            
            prev_close = bar.close
            
            # 7. Calculer slope_P
            if V is not None:
                slope_P = self.calculate_slope_P(V_cache, bar.date)
                if slope_P is not None:
                    slope_P_cache[bar.date] = slope_P
            else:
                slope_P = None
            
            # 8. Calculer ratio_P et amp_h
            if slope_P is not None:
                ratio_P, amp_h = self.calculate_ratio_P_amp_h(slope_P_cache, bar.date)
            else:
                ratio_P, amp_h = None, None
            
            # 9. Détecter alertes
            alerts = self.detect_alerts(K_values, prev_K_values) if prev_K_values else []
            prev_K_values = K_values
            
            # Ne créer que les métriques à partir de start_date
            if start_date is None or bar.date >= start_date:
                metrics_to_create.append(DailyMetric(
                    symbol=symbol,
                    scenario=self.scenario,
                    date=bar.date,
                    P=P, M=M, X=X, M1=M1, X1=X1,
                    T=T, Q=Q, S=S,
                    K1=K_values['K1'], K2=K_values['K2'],
                    K3=K_values['K3'], K4=K_values['K4'],
                    V=V, slope_P=slope_P,
                    ratio_P=ratio_P, amp_h=amp_h,
                ))
                
                if alerts:
                    alerts_to_create.append(Alert(
                        symbol=symbol,
                        scenario=self.scenario,
                        date=bar.date,
                        alert_codes=','.join(alerts),
                    ))
        
        # Sauvegarder en bulk
        if metrics_to_create:
            with transaction.atomic():
                DailyMetric.objects.bulk_create(
                    metrics_to_create,
                    update_conflicts=True,
                    update_fields=['P', 'M', 'X', 'M1', 'X1', 'T', 'Q', 'S',
                                  'K1', 'K2', 'K3', 'K4', 'V', 'slope_P', 'ratio_P', 'amp_h'],
                    unique_fields=['symbol', 'scenario', 'date']
                )
                
                if alerts_to_create:
                    Alert.objects.bulk_create(
                        alerts_to_create,
                        update_conflicts=True,
                        update_fields=['alert_codes'],
                        unique_fields=['symbol', 'scenario', 'date']
                    )
        
        count = len(metrics_to_create)
        JobLog.log('compute_metrics', 'INFO', f"{symbol.code}: {count} metrics calculated")
        
        return {'success': True, 'count': count}
