from celery import shared_task
from apps.core.models import JobLog
from .services import MarketDataFetcher

@shared_task
def fetch_daily_bars_task():
    """Tâche de collecte des données Twelve Data"""
    try:
        JobLog.log('fetch_bars', 'INFO', 'Starting daily bars fetch')
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_all_active_symbols()
        
        JobLog.log('fetch_bars', 'INFO', 
                  f"Fetch completed: {result['success']} success, {result['errors']} errors, {result['total_bars']} bars")
        
        return result
    except Exception as e:
        JobLog.log('fetch_bars', 'ERROR', f'Task failed: {str(e)}')
        raise
