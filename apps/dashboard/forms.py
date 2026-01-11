sudo docker compose exec web bash
cd /app
cat > apps/dashboard/forms.py << 'EOFFORMS'
from django import forms
from apps.core.models import Symbol, Scenario
from apps.market_data.services import TwelveDataService

class SymbolForm(forms.ModelForm):
    """Formulaire de création/édition de ticker"""
    class Meta:
        model = Symbol
        fields = ['code', 'exchange', 'name', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Ex: AAPL'
            }),
            'exchange': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Ex: NASDAQ'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Ex: Apple Inc.'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')
        exchange = cleaned_data.get('exchange')
        
        if code and exchange:
            # Valider via Twelve Data API
            try:
                service = TwelveDataService()
                if not service.validate_symbol(code, exchange):
                    raise forms.ValidationError(
                        f"Le ticker {code} sur {exchange} n'existe pas dans Twelve Data"
                    )
            except Exception as e:
                raise forms.ValidationError(f"Erreur de validation : {str(e)}")
        
        return cleaned_data


class ScenarioForm(forms.ModelForm):
    """Formulaire de création/édition de scénario"""
    class Meta:
        model = Scenario
        fields = ['name', 'description', 'is_default', 'a', 'b', 'c', 'd', 'e', 
                  'N1', 'N2', 'N3', 'N4']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'placeholder': 'Ex: Scénario Aggressive'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'rows': 3
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600'
            }),
            'a': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'step': '0.0001'
            }),
            'b': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'step': '0.0001'
            }),
            'c': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'step': '0.0001'
            }),
            'd': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'step': '0.0001'
            }),
            'e': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'step': '0.0001',
                'min': '0.0001'
            }),
            'N1': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'min': '1'
            }),
            'N2': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'min': '1'
            }),
            'N3': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'min': '1'
            }),
            'N4': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md',
                'min': '1'
            }),
        }
    
    def clean_e(self):
        e = self.cleaned_data.get('e')
        if e == 0:
            raise forms.ValidationError("Le paramètre 'e' ne peut pas être 0")
        return e
EOFFORMS
exit
