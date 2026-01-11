from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),
    
    # Actions
    path('action/fetch-bars/', views.action_fetch_bars, name='action_fetch_bars'),
    path('action/compute-metrics/', views.action_compute_metrics, name='action_compute_metrics'),
    path('action/send-alerts/', views.action_send_alerts, name='action_send_alerts'),
    
    # Tickers
    path('tickers/', views.symbol_list_view, name='symbol_list'),
    path('tickers/create/', views.symbol_create_view, name='symbol_create'),
    path('tickers/<int:symbol_id>/edit/', views.symbol_edit_view, name='symbol_edit'),
    path('tickers/<int:symbol_id>/delete/', views.symbol_delete_view, name='symbol_delete'),
    
    # API Autocomplétion
    path('api/ticker-autocomplete/', views.ticker_autocomplete_api, name='ticker_autocomplete_api'),
    
    # Scénarios
    path('scenarios/', views.scenario_list_view, name='scenario_list'),
    path('scenarios/create/', views.scenario_create_view, name='scenario_create'),
    path('scenarios/<int:scenario_id>/edit/', views.scenario_edit_view, name='scenario_edit'),
    path('scenarios/<int:scenario_id>/delete/', views.scenario_delete_view, name='scenario_delete'),
    
    # Import
    path('import-tickers/', views.import_tickers_view, name='import_tickers'),
    
    # Logs
    path('logs/', views.logs_view, name='logs'),
]
