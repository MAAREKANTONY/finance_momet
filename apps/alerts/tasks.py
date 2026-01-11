from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import EmailSettings, Alert, DailyMetric, JobLog

@shared_task
def send_daily_alerts_task():
    """Envoi du résumé quotidien"""
    try:
        config = EmailSettings.get_solo()
        
        if not config.from_email or not config.recipients:
            JobLog.log('send_alerts', 'WARNING', 'Email config incomplete')
            return
        
        today = timezone.now().date()
        alerts = Alert.objects.filter(date=today).select_related('symbol', 'scenario')
        
        if not alerts.exists():
            JobLog.log('send_alerts', 'INFO', 'No alerts today')
            return
        
        subject = f"Alertes Finance Momet - {today.strftime('%d/%m/%Y')}"
        
        body_lines = [
            f"Alertes du {today.strftime('%d/%m/%Y')}",
            "=" * 50,
            ""
        ]
        
        for alert in alerts:
            metric = DailyMetric.objects.filter(
                symbol=alert.symbol,
                scenario=alert.scenario,
                date=today
            ).first()
            
            ratio_P = f"{metric.ratio_P:.2f}%" if metric and metric.ratio_P else "N/A"
            amp_h = f"{metric.amp_h:.2f}%" if metric and metric.amp_h else "N/A"
            
            body_lines.append(
                f"{alert.symbol.code} ({alert.scenario.name}): "
                f"{alert.alert_codes} | ratio_P={ratio_P}, amp_h={amp_h}"
            )
        
        body = "\n".join(body_lines)
        
        send_mail(
            subject,
            body,
            config.from_email,
            config.get_recipients_list(),
            fail_silently=False,
        )
        
        JobLog.log('send_alerts', 'INFO', 
                  f'{alerts.count()} alerts sent to {len(config.get_recipients_list())} recipients')
        
    except Exception as e:
        JobLog.log('send_alerts', 'ERROR', f'Failed: {str(e)}')
        raise


@shared_task
def check_and_send_scheduled_alerts_task():
    """Vérification minute par minute"""
    try:
        config = EmailSettings.get_solo()
        now = timezone.now()
        
        if now.hour == config.send_hour and now.minute == config.send_minute:
            send_daily_alerts_task.delay()
    
    except Exception as e:
        JobLog.log('send_alerts', 'ERROR', f'Check failed: {str(e)}')
