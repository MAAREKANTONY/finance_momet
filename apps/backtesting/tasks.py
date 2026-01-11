from celery import shared_task
from apps.backtesting.models import BacktestRun
from apps.backtesting.engine import BacktestEngine
from apps.core.models import JobLog

@shared_task
def run_backtest_task(run_id):
    """Exécuter un backtest de manière asynchrone"""
    try:
        run = BacktestRun.objects.get(id=run_id)
        
        engine = BacktestEngine(run)
        result = engine.run_backtest()
        
        return result
        
    except BacktestRun.DoesNotExist:
        JobLog.log('backtest', 'ERROR', f'BacktestRun {run_id} not found')
        raise
    except Exception as e:
        JobLog.log('backtest', 'ERROR', f'Backtest {run_id} failed: {str(e)}')
        raise
