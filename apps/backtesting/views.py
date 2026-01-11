from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Max, Min, Avg
from apps.backtesting.models import BacktestRun, BacktestStrategy, BacktestDailyStat, BacktestTrade
from apps.backtesting.tasks import run_backtest_task
from apps.core.models import Scenario
import json

@login_required
def backtest_create_view(request):
    """Créer un nouveau backtest"""
    if request.method == 'POST':
        try:
            scenario_id = request.POST.get('scenario')
            strategy_id = request.POST.get('strategy')
            
            run = BacktestRun.objects.create(
                name=request.POST.get('name', f"Backtest {timezone.now()}"),
                description=request.POST.get('description', ''),
                scenario_id=scenario_id,
                strategy_id=strategy_id,
                CP=request.POST.get('CP', 0),
                CT=request.POST.get('CT'),
                X=request.POST.get('X'),
                status='CREATED',
            )
            
            # Lancer en arrière-plan
            run_backtest_task.delay(run.id)
            
            messages.success(request, f"Backtest '{run.name}' lancé avec succès")
            return redirect('backtest_detail', run_id=run.id)
            
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
    
    context = {
        'scenarios': Scenario.objects.all(),
        'strategies': BacktestStrategy.objects.all(),
    }
    
    return render(request, 'backtesting/create.html', context)


@login_required
def backtest_detail_view(request, run_id):
    """Détail d'un backtest"""
    run = get_object_or_404(BacktestRun, id=run_id)
    
    # Statistiques par ticker (dernière valeur)
    ticker_stats = BacktestDailyStat.objects.filter(
        run=run,
        symbol__isnull=False
    ).values('symbol__code').annotate(
        final_N=Max('N'),
        final_BT=Max('BT'),
        final_BMJ=Max('BMJ'),
    ).order_by('-final_BT')
    
    # Trades
    trades_count = BacktestTrade.objects.filter(run=run).count()
    
    # Série temporelle pour graphique
    daily_stats = BacktestDailyStat.objects.filter(
        run=run,
        symbol__isnull=True  # Stats globales
    ).order_by('date')
    
    context = {
        'run': run,
        'ticker_stats': ticker_stats,
        'trades_count': trades_count,
        'daily_stats': daily_stats,
    }
    
    return render(request, 'backtesting/detail.html', context)


@login_required
def backtest_ticker_detail_view(request, run_id, symbol_code):
    """Détail par ticker"""
    run = get_object_or_404(BacktestRun, id=run_id)
    
    daily_stats = BacktestDailyStat.objects.filter(
        run=run,
        symbol__code=symbol_code
    ).order_by('date')
    
    trades = BacktestTrade.objects.filter(
        run=run,
        symbol__code=symbol_code
    ).order_by('execution_date')
    
    # Données pour graphique
    chart_data = {
        'dates': [stat.date.strftime('%Y-%m-%d') for stat in daily_stats],
        'BT': [float(stat.BT) if stat.BT else 0 for stat in daily_stats],
        'BMJ': [float(stat.BMJ) if stat.BMJ else 0 for stat in daily_stats],
        'S_G_N': [float(stat.S_G_N) if stat.S_G_N else 0 for stat in daily_stats],
    }
    
    context = {
        'run': run,
        'symbol_code': symbol_code,
        'daily_stats': daily_stats,
        'trades': trades,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'backtesting/ticker_detail.html', context)


@login_required
def backtest_archive_view(request):
    """Archive des backtests"""
    runs = BacktestRun.objects.all().order_by('-created_at')
    
    # Filtres
    scenario_id = request.GET.get('scenario')
    strategy_id = request.GET.get('strategy')
    status = request.GET.get('status')
    
    if scenario_id:
        runs = runs.filter(scenario_id=scenario_id)
    if strategy_id:
        runs = runs.filter(strategy_id=strategy_id)
    if status:
        runs = runs.filter(status=status)
    
    context = {
        'runs': runs[:50],  # Limite à 50
        'scenarios': Scenario.objects.all(),
        'strategies': BacktestStrategy.objects.all(),
    }
    
    return render(request, 'backtesting/archive.html', context)


@login_required
def backtest_status_api(request, run_id):
    """API pour le statut d'un backtest (AJAX)"""
    run = get_object_or_404(BacktestRun, id=run_id)
    
    data = {
        'id': run.id,
        'status': run.status,
        'total_trades': run.total_trades,
        'total_BT': float(run.total_BT) if run.total_BT else None,
        'total_BMJ': float(run.total_BMJ) if run.total_BMJ else None,
        'error_message': run.error_message,
    }
    
    return JsonResponse(data)
