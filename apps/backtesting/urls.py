from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.backtest_create_view, name='backtest_create'),
    path('run/<int:run_id>/', views.backtest_detail_view, name='backtest_detail'),
    path('run/<int:run_id>/ticker/<str:symbol_code>/', views.backtest_ticker_detail_view, name='backtest_ticker_detail'),
    path('archive/', views.backtest_archive_view, name='backtest_archive'),
    path('api/status/<int:run_id>/', views.backtest_status_api, name='backtest_status_api'),
]
