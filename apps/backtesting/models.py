from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import Symbol, Scenario

class BacktestStrategy(models.Model):
    """Définition d'une stratégie de trading"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backtest_strategies'
        verbose_name_plural = 'Stratégies de backtest'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StrategyRule(models.Model):
    """Règles BUY/SELL d'une stratégie"""
    ACTION_CHOICES = [
        ('BUY', 'Acheter'),
        ('SELL', 'Vendre'),
    ]
    
    SIGNAL_CHOICES = [
        ('A1', 'A1'), ('B1', 'B1'),
        ('C1', 'C1'), ('D1', 'D1'),
        ('E1', 'E1'), ('F1', 'F1'),
        ('G1', 'G1'), ('H1', 'H1'),
    ]
    
    strategy = models.ForeignKey(BacktestStrategy, on_delete=models.CASCADE, related_name='rules')
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    signal = models.CharField(max_length=2, choices=SIGNAL_CHOICES)
    position_size_pct = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100,
        validators=[MinValueValidator(0.01)],
        help_text="% du cash à investir (100 = tout)"
    )
    
    class Meta:
        db_table = 'strategy_rules'
        unique_together = ['strategy', 'action', 'signal']
        ordering = ['strategy', 'action']
    
    def __str__(self):
        return f"{self.strategy.name}: {self.action} on {self.signal}"


class BacktestRun(models.Model):
    """Instance d'exécution d'un backtest"""
    STATUS_CHOICES = [
        ('CREATED', 'Créé'),
        ('RUNNING', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('FAILED', 'Échoué'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='backtest_runs')
    strategy = models.ForeignKey(BacktestStrategy, on_delete=models.CASCADE, related_name='backtest_runs')
    
    # Paramètres
    CP = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text="Capital total (0 = infini)"
    )
    CT = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Capital par ticker"
    )
    X = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Seuil ratio_P (en %)"
    )
    
    # Période (auto-détectée)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    
    # Statut
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='CREATED')
    
    # Résultats globaux
    total_BT = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    total_BMJ = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    nb_jours_ouvres = models.IntegerField(null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'backtest_runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['scenario', 'strategy']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class BacktestRunSymbolSetting(models.Model):
    """Override CT par ticker (optionnel)"""
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='symbol_settings')
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    CT_override = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        db_table = 'backtest_run_symbol_settings'
        unique_together = ['run', 'symbol']


class BacktestTrade(models.Model):
    """Transaction (BUY/SELL)"""
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='trades')
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    
    signal_date = models.DateField(help_text="Date du signal")
    execution_date = models.DateField(help_text="Date d'exécution (J+1)")
    
    action = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    signal = models.CharField(max_length=2)
    
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=4)
    cash_before = models.DecimalField(max_digits=15, decimal_places=2)
    cash_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Pour le SELL : gain du coup
    gain_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="G en %")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'backtest_trades'
        ordering = ['run', 'execution_date', 'symbol']
        indexes = [
            models.Index(fields=['run', 'symbol', 'execution_date']),
            models.Index(fields=['run', 'execution_date']),
        ]


class BacktestDailyStat(models.Model):
    """Statistiques journalières par ticker"""
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='daily_stats')
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, null=True, blank=True)  # NULL = global
    date = models.DateField()
    
    # Métriques ticker
    N = models.IntegerField(default=0, help_text="Nombre de coups")
    G = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Gain dernier coup %")
    S_G_N = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Moyenne gains %")
    BT = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Bénéfice total")
    BMJ = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True, help_text="Bénéfice moyen/jour")
    
    # Cash/position
    cash = models.DecimalField(max_digits=15, decimal_places=2)
    position_qty = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'backtest_daily_stats'
        unique_together = ['run', 'symbol', 'date']
        ordering = ['run', 'symbol', 'date']
        indexes = [
            models.Index(fields=['run', 'date']),
            models.Index(fields=['run', 'symbol', 'date']),
        ]
