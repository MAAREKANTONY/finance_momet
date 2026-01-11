from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from apps.core.models import Symbol, Scenario, Alert, JobLog, ScenarioSymbol
from apps.market_data.services import TwelveDataService
import csv
import io

@login_required
def dashboard_view(request):
    """Dashboard principal"""
    context = {
        'total_symbols': Symbol.objects.filter(is_active=True).count(),
        'total_scenarios': Scenario.objects.count(),
        'alerts_today': Alert.objects.filter(date=timezone.now().date()).count(),
        'recent_logs': JobLog.objects.all()[:20],
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def action_fetch_bars(request):
    """Lancer la collecte"""
    if request.method == 'POST':
        from apps.market_data.tasks import fetch_daily_bars_task
        fetch_daily_bars_task.delay()
        messages.success(request, "✅ Collecte des données lancée")
    return redirect('dashboard')


@login_required
def action_compute_metrics(request):
    """Lancer le calcul"""
    if request.method == 'POST':
        from apps.indicators.tasks import compute_metrics_task
        compute_metrics_task.delay()
        messages.success(request, "✅ Calcul des métriques lancé")
    return redirect('dashboard')


@login_required
def action_send_alerts(request):
    """Envoyer les alertes"""
    if request.method == 'POST':
        from apps.alerts.tasks import send_daily_alerts_task
        send_daily_alerts_task.delay()
        messages.success(request, "✅ Envoi des alertes lancé")
    return redirect('dashboard')


@login_required
def import_tickers_view(request):
    """Import CSV de tickers"""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, "Aucun fichier sélectionné")
            return redirect('import_tickers')
        
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Le fichier doit être un CSV")
            return redirect('import_tickers')
        
        try:
            # Lire le CSV
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            service = TwelveDataService()
            
            success_count = 0
            error_count = 0
            not_found_count = 0
            errors_detail = []
            
            for row in reader:
                ticker_code = row.get('ticker_code', '').strip()
                ticker_market = row.get('ticker_market', '').strip()
                scenario_list = row.get('scenario_list', '').strip()
                
                if not ticker_code or not ticker_market:
                    continue
                
                # Vérifier si le ticker existe via API
                if not service.validate_symbol(ticker_code, ticker_market):
                    not_found_count += 1
                    errors_detail.append(f"{ticker_code}: Non trouvé dans Twelve Data")
                    JobLog.log('import_tickers', 'WARNING', f'Ticker not found: {ticker_code}')
                    continue
                
                # Créer ou récupérer le symbol
                symbol, created = Symbol.objects.get_or_create(
                    code=ticker_code,
                    defaults={
                        'exchange': ticker_market,
                        'is_active': True,
                    }
                )
                
                # Associer aux scénarios
                if scenario_list:
                    scenario_names = [s.strip() for s in scenario_list.split(',')]
                    
                    for scenario_name in scenario_names:
                        try:
                            scenario = Scenario.objects.get(name=scenario_name)
                            ScenarioSymbol.objects.get_or_create(
                                scenario=scenario,
                                symbol=symbol
                            )
                        except Scenario.DoesNotExist:
                            errors_detail.append(f"{ticker_code}: Scénario '{scenario_name}' introuvable")
                
                success_count += 1
                JobLog.log('import_tickers', 'INFO', f'Imported: {ticker_code}')
            
            # Log de synthèse
            JobLog.log('import_tickers', 'INFO', 
                      f'Import completed: {success_count} OK, {not_found_count} not found, {error_count} errors')
            
            messages.success(request, 
                           f"✅ Import terminé: {success_count} tickers importés, {not_found_count} non trouvés")
            
            if errors_detail:
                for error in errors_detail[:10]:  # Limite à 10
                    messages.warning(request, error)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'import: {str(e)}")
            JobLog.log('import_tickers', 'ERROR', f'Import failed: {str(e)}')
        
        return redirect('import_tickers')
    
    return render(request, 'dashboard/import.html')


@login_required
def logs_view(request):
    """Page des logs"""
    logs = JobLog.objects.all().order_by('-created_at')
    
    # Filtres
    job_name = request.GET.get('job_name')
    level = request.GET.get('level')
    
    if job_name:
        logs = logs.filter(job_name=job_name)
    if level:
        logs = logs.filter(level=level)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'job_names': JobLog.objects.values_list('job_name', flat=True).distinct(),
    }
    
    return render(request, 'dashboard/logs.html', context)
