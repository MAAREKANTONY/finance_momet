from django import forms
from apps.core.models import Symbol, Scenario
from django.core.exceptions import ValidationError

class SymbolForm(forms.ModelForm):
    """Formulaire convivial pour créer/éditer un ticker"""
    
    class Meta:
        model = Symbol
        fields = ['code', 'exchange', 'name', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-lg font-mono',
                'placeholder': 'Ex: AAPL, MSFT, GOOGL...',
                'id': 'ticker-code-input'
            }),
            'exchange': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'placeholder': 'Ex: NASDAQ, NYSE',
                'readonly': 'readonly'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'placeholder': 'Nom de la société',
                'readonly': 'readonly'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
            })
        }
        labels = {
            'code': 'Code du Ticker',
            'exchange': 'Bourse / Exchange',
            'name': 'Nom de la Société',
            'is_active': 'Actif'
        }
        help_texts = {
            'code': '💡 Commencez à taper pour voir les suggestions automatiques',
            'is_active': 'Décochez pour désactiver temporairement ce ticker'
        }


class ScenarioForm(forms.ModelForm):
    """Formulaire convivial pour créer/éditer un scénario"""
    
    class Meta:
        model = Scenario
        fields = ['name', 'description', 'is_default', 'a', 'b', 'c', 'd', 'e', 
                  'N1', 'N2', 'N3', 'N4']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'placeholder': 'Ex: Stratégie Conservative'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'rows': 3,
                'placeholder': 'Décrivez votre scénario...'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
            }),
            'a': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'step': '0.0001',
                'min': '0'
            }),
            'b': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'step': '0.0001',
                'min': '0'
            }),
            'c': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'step': '0.0001',
                'min': '0'
            }),
            'd': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'step': '0.0001',
                'min': '0'
            }),
            'e': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'step': '0.0001',
                'min': '0.0001'
            }),
            'N1': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'min': '1'
            }),
            'N2': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'min': '1'
            }),
            'N3': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'min': '1'
            }),
            'N4': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none',
                'min': '1'
            }),
        }
        labels = {
            'name': 'Nom du Scénario',
            'description': 'Description',
            'is_default': 'Scénario par défaut',
            'a': 'Poids Close (a)',
            'b': 'Poids High (b)',
            'c': 'Poids Low (c)',
            'd': 'Poids Open (d)',
            'e': 'Facteur Canal (e)',
            'N1': 'Période Max/Min (N1)',
            'N2': 'Période Lissage (N2)',
            'N3': 'Période Pente (N3)',
            'N4': 'Période Ratio (N4)',
        }
        help_texts = {
            'e': '⚠️ Ne peut pas être 0',
            'N1': 'Nombre de jours pour calculer Max et Min de P',
            'N2': 'Nombre de jours pour lisser M1 et X1',
            'N3': 'Nombre de jours pour calculer slope_P',
            'N4': 'Nombre de jours pour calculer ratio_P',
        }
    
    def clean_e(self):
        e = self.cleaned_data.get('e')
        if e == 0:
            raise ValidationError("Le paramètre 'e' ne peut pas être 0")
        return e
