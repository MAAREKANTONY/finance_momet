from django.contrib import admin
from .models import BacktestStrategy, StrategyRule, BacktestRun, BacktestTrade, BacktestDailyStat

class StrategyRuleInline(admin.TabularInline):
    model = StrategyRule
    extra = 2

@admin.register(BacktestStrategy)
class BacktestStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'get_rules_count']
    search_fields = ['name']
    inlines = [StrategyRuleInline]
    
    def get_rules_count(self, obj):
        return obj.rules.count()
    get_rules_count.short_description = 'Règles'

@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ['name', 'scenario', 'strategy', 'status', 'total_trades', 'total_BT', 'created_at']
    list_filter = ['status', 'scenario', 'strategy', 'created_at']
    search_fields = ['name']
    readonly_fields = ['status', 'total_BT', 'total_BMJ', 'total_trades', 'created_at', 'started_at', 'completed_at']
    fieldsets = (
        ('Informations', {
            'fields': ('name', 'description', 'scenario', 'strategy')
        }),
        ('Paramètres', {
            'fields': ('CP', 'CT', 'X')
        }),
        ('Période', {
            'fields': ('date_start', 'date_end')
        }),
        ('Résultats', {
            'fields': ('status', 'total_BT', 'total_BMJ', 'total_trades', 'nb_jours_ouvres', 'error_message')
        }),
        ('Dates', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )

@admin.register(BacktestTrade)
class BacktestTradeAdmin(admin.ModelAdmin):
    list_display = ['run', 'symbol', 'execution_date', 'action', 'signal', 'quantity', 'price', 'gain_pct']
    list_filter = ['run', 'action', 'execution_date']
    date_hierarchy = 'execution_date'

@admin.register(BacktestDailyStat)
class BacktestDailyStatAdmin(admin.ModelAdmin):
    list_display = ['run', 'symbol', 'date', 'N', 'S_G_N', 'BT', 'BMJ']
    list_filter = ['run', 'date']
    date_hierarchy = 'date'
