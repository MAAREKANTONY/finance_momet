import requests
import time
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.db import transaction
from ratelimit import limits, sleep_and_retry
from apps.core.models import Symbol, DailyBar, JobLog

class TwelveDataService:
    """Service de collecte des données Twelve Data"""
    BASE_URL = "https://api.twelvedata.com"
    
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'TWELVE_DATA_API_KEY', None)
        if not self.api_key:
            raise ValueError("TWELVE_DATA_API_KEY not configured in settings")
    
    @sleep_and_retry
    @limits(calls=8, period=60)  # Plan gratuit : 8 calls/minute
    def _make_request(self, endpoint, params):
        """Requête avec rate limiting"""
        params['apikey'] = self.api_key
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}", 
                params=params, 
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            JobLog.log('twelve_data', 'ERROR', f'Request error: {str(e)}')
            raise
    
    def fetch_time_series(self, symbol_code, exchange, start_date=None, end_date=None):
        """
        Récupère les barres journalières
        
        Returns:
            {
                'success': bool,
                'data': [{'date': '2024-01-01', 'open': ..., ...}],
                'error': str (si échec)
            }
        """
        try:
            params = {
                'symbol': symbol_code,
                'interval': '1day',
                'exchange': exchange,
                'outputsize': 5000,
                'format': 'JSON',
            }
            
            if start_date:
                params['start_date'] = start_date.strftime('%Y-%m-%d')
            if end_date:
                params['end_date'] = end_date.strftime('%Y-%m-%d')
            
            data = self._make_request('time_series', params)
            
            # Gérer les erreurs API
            if 'status' in data and data['status'] == 'error':
                return {'success': False, 'error': data.get('message', 'Unknown error')}
            
            if 'values' not in data or not data['values']:
                return {'success': False, 'error': 'No data returned'}
            
            # Convertir au format attendu
            bars = []
            for item in data['values']:
                try:
                    bars.append({
                        'date': datetime.strptime(item['datetime'], '%Y-%m-%d').date(),
                        'open': Decimal(item['open']),
                        'high': Decimal(item['high']),
                        'low': Decimal(item['low']),
                        'close': Decimal(item['close']),
                        'volume': int(float(item['volume'])),
                    })
                except (KeyError, ValueError) as e:
                    JobLog.log('twelve_data', 'WARNING', 
                              f'Skipping invalid bar for {symbol_code}: {str(e)}')
                    continue
            
            return {'success': True, 'data': bars}
        
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def validate_symbol(self, symbol_code, exchange):
        """Vérifier si un ticker existe"""
        try:
            params = {
                'symbol': symbol_code,
                'exchange': exchange,
            }
            data = self._make_request('quote', params)
            return 'close' in data or 'price' in data
        except:
            return False


class MarketDataFetcher:
    """Gestion de la collecte incrémentale"""
    
    def __init__(self):
        self.service = TwelveDataService()
    
    def fetch_symbol_incremental(self, symbol: Symbol):
        """Collecte incrémentale pour un ticker"""
        # Trouver la dernière date en base
        last_bar = symbol.bars.order_by('-date').first()
        start_date = last_bar.date + timedelta(days=1) if last_bar else None
        end_date = datetime.now().date()
        
        if start_date and start_date > end_date:
            JobLog.log('fetch_bars', 'INFO', f"{symbol.code}: Already up to date")
            return {'success': True, 'count': 0}
        
        JobLog.log('fetch_bars', 'INFO', 
                  f"{symbol.code}: Fetching from {start_date or 'beginning'} to {end_date}")
        
        result = self.service.fetch_time_series(
            symbol.code,
            symbol.exchange,
            start_date=start_date,
            end_date=end_date
        )
        
        if not result['success']:
            JobLog.log('fetch_bars', 'ERROR', f"{symbol.code}: {result['error']}")
            return result
        
        # Sauvegarder en bulk avec upsert
        bars_to_upsert = []
        for bar_data in result['data']:
            bars_to_upsert.append(DailyBar(
                symbol=symbol,
                date=bar_data['date'],
                open=bar_data['open'],
                high=bar_data['high'],
                low=bar_data['low'],
                close=bar_data['close'],
                volume=bar_data['volume'],
            ))
        
        if bars_to_upsert:
            with transaction.atomic():
                # Bulk upsert (PostgreSQL)
                DailyBar.objects.bulk_create(
                    bars_to_upsert,
                    update_conflicts=True,
                    update_fields=['open', 'high', 'low', 'close', 'volume', 'updated_at'],
                    unique_fields=['symbol', 'date']
                )
        
        count = len(bars_to_upsert)
        JobLog.log('fetch_bars', 'INFO', f"{symbol.code}: {count} bars saved")
        
        return {'success': True, 'count': count}
    
    def fetch_all_active_symbols(self):
        """Collecter tous les tickers actifs"""
        symbols = Symbol.objects.filter(is_active=True)
        total = symbols.count()
        
        JobLog.log('fetch_bars', 'INFO', f"Starting fetch for {total} symbols")
        
        success_count = 0
        error_count = 0
        total_bars = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                result = self.fetch_symbol_incremental(symbol)
                
                if result['success']:
                    success_count += 1
                    total_bars += result['count']
                else:
                    error_count += 1
                
                # Log de progression tous les 10 tickers
                if i % 10 == 0:
                    JobLog.log('fetch_bars', 'INFO', f"Progress: {i}/{total}")
                
                # Respecter le rate limit (pause entre les appels)
                time.sleep(0.5)
                
            except Exception as e:
                error_count += 1
                JobLog.log('fetch_bars', 'ERROR', 
                          f"{symbol.code}: Exception - {str(e)}")
        
        JobLog.log('fetch_bars', 'INFO', 
                  f"Fetch completed: {success_count} OK, {error_count} errors, {total_bars} bars saved")
        
        return {
            'total': total,
            'success': success_count,
            'errors': error_count,
            'total_bars': total_bars,
        }
