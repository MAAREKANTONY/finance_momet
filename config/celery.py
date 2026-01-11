import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('finance_momet')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-daily-bars-at-22h': {
        'task': 'apps.market_data.tasks.fetch_daily_bars_task',
        'schedule': crontab(hour=22, minute=0),
    },
    'compute-metrics-at-22h30': {
        'task': 'apps.indicators.tasks.compute_metrics_task',
        'schedule': crontab(hour=22, minute=30),
    },
    'check-scheduled-alerts-every-minute': {
        'task': 'apps.alerts.tasks.check_and_send_scheduled_alerts_task',
        'schedule': crontab(minute='*/1'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
