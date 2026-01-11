from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import Symbol, Scenario, ScenarioSymbol, DailyBar, DailyMetric, Alert, EmailSettings, JobLog

@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ['code', 'exchange', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'exchange']
    search_fields = ['code', 'name']
    list_per_page = 50
    actions = ['activate_symbols', 'deactivate_symbols']
    
    def activate_symbols(self, request, queryset):
        queryset.update(is_active=True)
    activate_symbols.short_description = "Activer les tickers sélectionnés"
    
    def deactivate_symbols(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_symbols.short_description = "Désactiver les tickers sélectionnés"

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'e', 'N1', 'N2', 'N3', 'N4', 'created_at']
    list_filter = ['is_default']
    search_fields = ['name']
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'is_default')
        }),
        ('Paramètres P', {
            'fields': ('a', 'b', 'c', 'd')
        }),
        ('Paramètre canal', {
            'fields': ('e',)
        }),
        ('Périodes', {
            'fields': ('N1', 'N2', 'N3', 'N4')
        }),
    )

@admin.register(DailyBar)
class DailyBarAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
    list_filter = ['symbol', 'date']
    date_hierarchy = 'date'
    list_per_page = 100
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DailyMetric)
class DailyMetricAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'scenario', 'date', 'ratio_P', 'amp_h', 'P']
    list_filter = ['scenario', 'date']
    date_hierarchy = 'date'
    list_per_page = 100

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'scenario', 'date', 'alert_codes', 'created_at']
    list_filter = ['scenario', 'date']
    date_hierarchy = 'date'
    list_per_page = 100

admin.site.register(EmailSettings, SingletonModelAdmin)

@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'job_name', 'level', 'message_preview']
    list_filter = ['level', 'job_name', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 100
    readonly_fields = ['created_at', 'job_name', 'level', 'message', 'extra_data']
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
