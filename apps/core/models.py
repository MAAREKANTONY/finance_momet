from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from solo.models import SingletonModel
import hashlib
import json

class Symbol(models.Model):
    """Ticker (action/ETF)"""
    code = models.CharField(max_length=20, unique=True, db_index=True)
    exchange = models.CharField(max_length=50)
    name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    scenarios = models.ManyToManyField('Scenario', through='ScenarioSymbol', related_name='symbols')
    
    class Meta:
        db_table = 'symbols'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'exchange']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} ({self.exchange})"


class Scenario(models.Model):
    """Paramètres de calcul des indicateurs"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    # Paramètres P
    a = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    b = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    c = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    d = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    
    # Paramètre canal (ne peut pas être 0)
    e = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        default=2,
        validators=[MinValueValidator(0.0001)],
        help_text="Ne peut pas être 0"
    )
    
    # Périodes
    N1 = models.IntegerField(default=20, validators=[MinValueValidator(1)])
    N2 = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    N3 = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    N4 = models.IntegerField(default=20, validators=[MinValueValidator(1)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    compute_config_hash = models.CharField(max_length=64, blank=True, editable=False)
    
    class Meta:
        db_table = 'scenarios'
        ordering = ['-is_default', 'name']
    
    def save(self, *args, **kwargs):
        if self.e == 0:
            raise ValidationError("Le paramètre 'e' ne peut pas être 0")
        
        if self.is_default:
            Scenario.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        self.compute_config_hash = self._compute_hash()
        super().save(*args, **kwargs)
    
    def _compute_hash(self):
        config = {
            'a': str(self.a), 'b': str(self.b), 'c': str(self.c), 'd': str(self.d),
            'e': str(self.e), 'N1': self.N1, 'N2': self.N2, 'N3': self.N3, 'N4': self.N4,
        }
        return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    
    def __str__(self):
        return f"{self.name}{' (défaut)' if self.is_default else ''}"


class ScenarioSymbol(models.Model):
    """Association M2M entre Scenario et Symbol"""
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scenario_symbols'
        unique_together = ['scenario', 'symbol']


class DailyBar(models.Model):
    """Barre journalière OHLCV"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='bars')
    date = models.DateField(db_index=True)
    
    open = models.DecimalField(max_digits=12, decimal_places=4)
    high = models.DecimalField(max_digits=12, decimal_places=4)
    low = models.DecimalField(max_digits=12, decimal_places=4)
    close = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_bars'
        unique_together = ['symbol', 'date']
        ordering = ['symbol', '-date']
        indexes = [
            models.Index(fields=['symbol', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.symbol.code} {self.date}"


class DailyMetric(models.Model):
    """Indicateurs calculés par (symbol, scenario, date)"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='metrics')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField(db_index=True)
    
    # Prix pondéré
    P = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Extrêmes
    M = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    X = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    M1 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    X1 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Canal
    T = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    Q = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    S = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Signaux
    K1 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    K2 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    K3 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    K4 = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Tendance
    V = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Variation % jour")
    slope_P = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    ratio_P = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="En %")
    amp_h = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="En %")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_metrics'
        unique_together = ['symbol', 'scenario', 'date']
        ordering = ['symbol', 'scenario', '-date']
        indexes = [
            models.Index(fields=['symbol', 'scenario', 'date']),
            models.Index(fields=['date']),
        ]


class Alert(models.Model):
    """Alerte détectée (A1..H1)"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='alerts')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='alerts')
    date = models.DateField(db_index=True)
    alert_codes = models.CharField(max_length=100, help_text="Ex: A1,E1")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'alerts'
        unique_together = ['symbol', 'scenario', 'date']
        ordering = ['-date', 'symbol']
        indexes = [
            models.Index(fields=['date', 'scenario']),
        ]
    
    def get_alerts_list(self):
        return [a.strip() for a in self.alert_codes.split(',') if a.strip()]


class EmailSettings(SingletonModel):
    """Configuration email (singleton)"""
    smtp_host = models.CharField(max_length=200, default='smtp.gmail.com')
    smtp_port = models.IntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_username = models.CharField(max_length=200, blank=True)
    smtp_password = models.CharField(max_length=200, blank=True)
    from_email = models.EmailField(blank=True)
    recipients = models.TextField(blank=True, help_text="Un email par ligne")
    send_hour = models.IntegerField(default=9, validators=[MinValueValidator(0), MaxValueValidator(23)])
    send_minute = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    
    class Meta:
        verbose_name = "Configuration Email"
    
    def get_recipients_list(self):
        return [email.strip() for email in self.recipients.split('\n') if email.strip()]


class JobLog(models.Model):
    """Journal des exécutions asynchrones"""
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    job_name = models.CharField(max_length=100, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    message = models.TextField()
    extra_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'job_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'job_name']),
            models.Index(fields=['level']),
        ]
    
    @classmethod
    def log(cls, job_name, level, message, **extra):
        return cls.objects.create(
            job_name=job_name,
            level=level,
            message=message,
            extra_data=extra or None
        )
    
    def __str__(self):
        return f"[{self.level}] {self.job_name} - {self.message[:50]}"
