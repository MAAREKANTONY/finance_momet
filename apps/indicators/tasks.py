from celery import shared_task
from apps.core.models import Scenario, JobLog
from .calculator import MetricsCalculator

@shared_task
def compute_metrics_task(scenario_id=None, full_recompute=False):
    """Tâche de calcul des métriques"""
    try:
        JobLog.log('compute_metrics', 'INFO', 'Starting metrics computation')
        
        if scenario_id:
            scenarios = [Scenario.objects.get(id=scenario_id)]
        else:
            scenarios = Scenario.objects.filter(is_default=True)
        
        if not scenarios:
            scenarios = Scenario.objects.all()
        
        total_computed = 0
        
        for scenario in scenarios:
            JobLog.log('compute_metrics', 'INFO', f'Computing for scenario: {scenario.name}')
            
            calculator = MetricsCalculator(scenario)
            symbols = scenario.symbols.filter(is_active=True)
            
            for symbol in symbols:
                try:
                    result = calculator.compute_symbol_incremental(symbol)
                    if result['success']:
                        total_computed += result['count']
                except Exception as e:
                    JobLog.log('compute_metrics', 'ERROR', f"{symbol.code}: {str(e)}")
        
        JobLog.log('compute_metrics', 'INFO', 
                  f'Computation completed: {total_computed} metrics calculated')
        
        return {'total_computed': total_computed}
        
    except Exception as e:
        JobLog.log('compute_metrics', 'ERROR', f'Task failed: {str(e)}')
        raise
