from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('action/fetch-bars/', views.action_fetch_bars, name='action_fetch_bars'),
    path('action/compute-metrics/', views.action_compute_metrics, name='action_compute_metrics'),
    path('action/send-alerts/', views.action_send_alerts, name='action_send_alerts'),
    path('import-tickers/', views.import_tickers_view, name='import_tickers'),
    path('logs/', views.logs_view, name='logs'),
]
