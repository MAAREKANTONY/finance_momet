from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from apps.core.models import Symbol, Scenario, Alert, JobLog, ScenarioSymbol
from apps.dashboard.forms import SymbolForm, ScenarioForm
from apps.market_data.services import TwelveDataService
import csv
import io

# ============================================
# DASHBOARD
# ============================================

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


# ============================================
# ACTIONS
# ============================================

@login_required
def action_fetch_bars(request):
    if request.method == 'POST':
        from apps.market_data.tasks import fetch_daily_bars_task
        fetch_daily_bars_task.delay()
        messages.success(request, "✅ Collecte des données lancée en arrière-plan")
    return redirect('dashboard')


@login_required
def action_compute_metrics(request):
    if request.method == 'POST':
        from apps.indicators.tasks import compute_metrics_task
        compute_metrics_task.delay()
        messages.success(request, "✅ Calcul des métriques lancé en arrière-plan")
    return redirect('dashboard')


@login_required
def action_send_alerts(request):
    if request.method == 'POST':
        from apps.alerts.tasks import send_daily_alerts_task
        send_daily_alerts_task.delay()
        messages.success(request, "✅ Envoi des alertes lancé")
    return redirect('dashboard')


# ============================================
# TICKERS
# ============================================

@login_required
def symbol_list_view(request):
    """Liste des tickers"""
    symbols = Symbol.objects.all().order_by('-created_at')
    
    # Filtres
    search = request.GET.get('search')
    exchange = request.GET.get('exchange')
    is_active = request.GET.get('is_active')
    
    if search:
        symbols = symbols.filter(code__icontains=search) | symbols.filter(name__icontains=search)
    if exchange:
        symbols = symbols.filter(exchange=exchange)
    if is_active:
        symbols = symbols.filter(is_active=is_active == 'true')
    
    # Pagination
    paginator = Paginator(symbols, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'exchanges': Symbol.objects.values_list('exchange', flat=True).distinct().order_by('exchange'),
        'total_count': symbols.count(),
    }
    
    return render(request, 'dashboard/symbol_list.html', context)


@login_required
def symbol_create_view(request):
    """Créer un ticker"""
    if request.method == 'POST':
        form = SymbolForm(request.POST)
        if form.is_valid():
            symbol = form.save()
            messages.success(request, f"✅ Ticker {symbol.code} créé avec succès !")
            return redirect('symbol_list')
    else:
        form = SymbolForm()
    
    return render(request, 'dashboard/symbol_form.html', {
        'form': form, 
        'title': 'Ajouter un Ticker',
        'submit_text': 'Créer le Ticker'
    })


@login_required
def symbol_edit_view(request, symbol_id):
    """Éditer un ticker"""
    symbol = get_object_or_404(Symbol, id=symbol_id)
    
    if request.method == 'POST':
        form = SymbolForm(request.POST, instance=symbol)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Ticker {symbol.code} modifié avec succès !")
            return redirect('symbol_list')
    else:
        form = SymbolForm(instance=symbol)
    
    return render(request, 'dashboard/symbol_form.html', {
        'form': form,
        'title': f'Modifier {symbol.code}',
        'submit_text': 'Enregistrer les Modifications',
        'symbol': symbol
    })


@login_required
def symbol_delete_view(request, symbol_id):
    """Supprimer un ticker"""
    symbol = get_object_or_404(Symbol, id=symbol_id)
    
    if request.method == 'POST':
        code = symbol.code
        symbol.delete()
        messages.success(request, f"✅ Ticker {code} supprimé avec succès")
        return redirect('symbol_list')
    
    return render(request, 'dashboard/symbol_confirm_delete.html', {'symbol': symbol})


# ============================================
# API AUTOCOMPLÉTION TWELVE DATA
# ============================================

@login_required
def ticker_autocomplete_api(request):
    """API pour l'autocomplétion des tickers"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        service = TwelveDataService()
        # Utiliser l'API de recherche
        import requests
        response = requests.get(
            'https://api.twelvedata.com/symbol_search',
            params={
                'symbol': query,
                'apikey': service.api_key
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                results = []
                for item in data['data'][:10]:
                    results.append({
                        'symbol': item.get('symbol', ''),
                        'name': item.get('instrument_name', ''),
                        'exchange': item.get('exchange', ''),
                        'country': item.get('country', ''),
                        'type': item.get('type', '')
                    })
                
                return JsonResponse({'results': results})
        
        return JsonResponse({'results': [], 'error': 'API error'})
    
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})


# ============================================
# SCÉNARIOS
# ============================================

@login_required
def scenario_list_view(request):
    """Liste des scénarios"""
    scenarios = Scenario.objects.all().order_by('-is_default', 'name')
    
    context = {
        'scenarios': scenarios,
    }
    
    return render(request, 'dashboard/scenario_list.html', context)


@login_required
def scenario_create_view(request):
    """Créer un scénario"""
    if request.method == 'POST':
        form = ScenarioForm(request.POST)
        if form.is_valid():
            scenario = form.save()
            messages.success(request, f"✅ Scénario '{scenario.name}' créé avec succès !")
            return redirect('scenario_list')
    else:
        form = ScenarioForm(initial={
            'a': 1, 'b': 1, 'c': 1, 'd': 1,
            'e': 2,
            'N1': 20, 'N2': 5, 'N3': 10, 'N4': 20
        })
    
    return render(request, 'dashboard/scenario_form.html', {
        'form': form,
        'title': 'Créer un Scénario',
        'submit_text': 'Créer le Scénario'
    })


@login_required
def scenario_edit_view(request, scenario_id):
    """Éditer un scénario"""
    scenario = get_object_or_404(Scenario, id=scenario_id)
    
    if request.method == 'POST':
        form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Scénario '{scenario.name}' modifié avec succès !")
            return redirect('scenario_list')
    else:
        form = ScenarioForm(instance=scenario)
    
    return render(request, 'dashboard/scenario_form.html', {
        'form': form,
        'title': f'Modifier "{scenario.name}"',
        'submit_text': 'Enregistrer les Modifications',
        'scenario': scenario
    })


@login_required
def scenario_delete_view(request, scenario_id):
    """Supprimer un scénario"""
    scenario = get_object_or_404(Scenario, id=scenario_id)
    
    if request.method == 'POST':
        name = scenario.name
        scenario.delete()
        messages.success(request, f"✅ Scénario '{name}' supprimé avec succès")
        return redirect('scenario_list')
    
    return render(request, 'dashboard/scenario_confirm_delete.html', {'scenario': scenario})


# ============================================
# IMPORT CSV
# ============================================

@login_required
def import_tickers_view(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, "❌ Aucun fichier sélectionné")
            return redirect('import_tickers')
        
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "❌ Le fichier doit être un CSV")
            return redirect('import_tickers')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            service = TwelveDataService()
            
            success_count = 0
            error_count = 0
            not_found_count = 0
            
            for row in reader:
                ticker_code = row.get('ticker_code', '').strip()
                ticker_market = row.get('ticker_market', '').strip()
                scenario_list = row.get('scenario_list', '').strip()
                
                if not ticker_code or not ticker_market:
                    continue
                
                if not service.validate_symbol(ticker_code, ticker_market):
                    not_found_count += 1
                    JobLog.log('import_tickers', 'WARNING', f'Not found: {ticker_code}')
                    continue
                
                symbol, created = Symbol.objects.get_or_create(
                    code=ticker_code,
                    defaults={'exchange': ticker_market, 'is_active': True}
                )
                
                if scenario_list:
                    for scenario_name in [s.strip() for s in scenario_list.split(',')]:
                        try:
                            scenario = Scenario.objects.get(name=scenario_name)
                            ScenarioSymbol.objects.get_or_create(scenario=scenario, symbol=symbol)
                        except Scenario.DoesNotExist:
                            pass
                
                success_count += 1
            
            messages.success(request, 
                           f"✅ Import terminé : {success_count} tickers importés, {not_found_count} non trouvés")
            
        except Exception as e:
            messages.error(request, f"❌ Erreur : {str(e)}")
        
        return redirect('import_tickers')
    
    return render(request, 'dashboard/import.html')


# ============================================
# LOGS
# ============================================

@login_required
def logs_view(request):
    logs = JobLog.objects.all().order_by('-created_at')
    
    job_name = request.GET.get('job_name')
    level = request.GET.get('level')
    
    if job_name:
        logs = logs.filter(job_name=job_name)
    if level:
        logs = logs.filter(level=level)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'job_names': JobLog.objects.values_list('job_name', flat=True).distinct(),
    }
    
    return render(request, 'dashboard/logs.html', context)
