#!/bin/bash
# fix_navigation.sh - Correction du menu et autocomplétion

cd ~/projet_finance_moment/V_CL/project/finance_momet

echo "🔧 Correction de la navigation et autocomplétion..."

# ============================================
# MÉTHODE 1 : Entrer dans le conteneur (RECOMMANDÉ)
# ============================================

sudo docker compose exec web bash << 'EOFBASH'

# ⚠️ ICI ON EST DANS LE CONTENEUR
# Donc on utilise /app (avec slash initial)

# 1. Corriger base.html
cat > /app/templates/base.html << 'EOFHTML'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Finance Momet{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-lg border-b-2 border-gray-200">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex space-x-4">
                    <a href="/" class="flex items-center px-3 py-2 text-sm font-semibold text-blue-600">
                        📊 Dashboard
                    </a>
                    <a href="/admin/core/symbol/" class="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-blue-600">
                        📈 Tickers
                    </a>
                    <a href="/admin/core/scenario/" class="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-blue-600">
                        ⚙️ Scénarios
                    </a>
                    <a href="/admin/backtesting/backtestrun/" class="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-blue-600">
                        🚀 Backtests
                    </a>
                    <a href="/admin/core/alert/" class="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-blue-600">
                        🔔 Alertes
                    </a>
                    <a href="/admin/" class="flex items-center px-3 py-2 text-sm text-gray-700 hover:text-blue-600">
                        👨‍💼 Admin
                    </a>
                </div>
                <div class="flex items-center">
                    <span class="text-xs text-gray-500">Finance Momet v2.0</span>
                </div>
            </div>
        </div>
    </nav>
    
    {% if messages %}
    <div class="max-w-7xl mx-auto px-4 mt-4">
        {% for message in messages %}
        <div class="{% if message.tags == 'error' %}bg-red-100 border-red-400 text-red-700{% else %}bg-green-100 border-green-400 text-green-700{% endif %} border px-4 py-3 rounded mb-2">
            {{ message }}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer class="bg-white border-t mt-12 py-4">
        <div class="max-w-7xl mx-auto px-4 text-center text-xs text-gray-500">
            Finance Momet © 2024
        </div>
    </footer>
</body>
</html>
EOFHTML

echo "✅ base.html créé"

# 2. Créer le dossier static/js
mkdir -p /app/static/js

# 3. Créer le fichier JavaScript d'autocomplétion
cat > /app/static/js/ticker_autocomplete.js << 'EOFJS'
class TickerAutocomplete {
    constructor(inputId, apiKey) {
        this.input = document.getElementById(inputId);
        this.apiKey = apiKey;
        this.debounceTimer = null;
        
        if (this.input) {
            this.init();
        }
    }
    
    init() {
        const container = document.createElement('div');
        container.id = 'ticker-suggestions';
        container.className = 'absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg mt-1 max-h-60 overflow-y-auto hidden';
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(container);
        
        this.input.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                this.debounceTimer = setTimeout(() => {
                    this.search(query);
                }, 300);
            } else {
                this.hideSuggestions();
            }
        });
        
        document.addEventListener('click', (e) => {
            if (e.target !== this.input) {
                this.hideSuggestions();
            }
        });
    }
    
    async search(query) {
        try {
            const response = await fetch(
                `https://api.twelvedata.com/symbol_search?symbol=${encodeURIComponent(query)}&apikey=${this.apiKey}`
            );
            
            if (!response.ok) throw new Error('API error');
            
            const data = await response.json();
            
            if (data.data && data.data.length > 0) {
                this.showSuggestions(data.data);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showError();
        }
    }
    
    showSuggestions(results) {
        const container = document.getElementById('ticker-suggestions');
        container.innerHTML = '';
        
        results.slice(0, 10).forEach(item => {
            const div = document.createElement('div');
            div.className = 'px-4 py-2 hover:bg-blue-50 cursor-pointer border-b';
            div.innerHTML = `
                <div class="font-semibold">${item.symbol}</div>
                <div class="text-xs text-gray-600">${item.instrument_name || ''} - ${item.exchange || ''}</div>
            `;
            
            div.addEventListener('click', () => {
                this.selectTicker(item);
            });
            
            container.appendChild(div);
        });
        
        container.classList.remove('hidden');
    }
    
    selectTicker(item) {
        const codeInput = document.querySelector('input[name="code"]');
        if (codeInput) codeInput.value = item.symbol;
        
        const exchangeInput = document.querySelector('input[name="exchange"]');
        if (exchangeInput) exchangeInput.value = item.exchange || '';
        
        const nameInput = document.querySelector('input[name="name"]');
        if (nameInput) nameInput.value = item.instrument_name || '';
        
        this.hideSuggestions();
    }
    
    showNoResults() {
        const container = document.getElementById('ticker-suggestions');
        container.innerHTML = '<div class="px-4 py-3 text-gray-500 text-sm">Aucun ticker trouvé</div>';
        container.classList.remove('hidden');
    }
    
    showError() {
        const container = document.getElementById('ticker-suggestions');
        container.innerHTML = '<div class="px-4 py-3 text-red-500 text-sm">Erreur de recherche</div>';
        container.classList.remove('hidden');
    }
    
    hideSuggestions() {
        const container = document.getElementById('ticker-suggestions');
        if (container) container.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const apiKey = document.body.getAttribute('data-twelve-api-key');
    
    if (apiKey && document.querySelector('input[name="code"]')) {
        new TickerAutocomplete('id_code', apiKey);
    }
});
EOFJS

echo "✅ ticker_autocomplete.js créé"

# 4. Créer le template admin personnalisé
mkdir -p /app/templates/admin/core/symbol

cat > /app/templates/admin/core/symbol/change_form.html << 'EOFTPL'
{% extends "admin/change_form.html" %}
{% load static %}

{% block extrahead %}
{{ block.super }}
<script src="{% static 'js/ticker_autocomplete.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.body.setAttribute('data-twelve-api-key', '{{ TWELVE_DATA_API_KEY }}');
    
    const codeField = document.querySelector('.field-code');
    if (codeField) {
        const helpText = document.createElement('div');
        helpText.className = 'help';
        helpText.innerHTML = '💡 Tapez au moins 2 caractères pour rechercher un ticker';
        codeField.appendChild(helpText);
    }
});
</script>
{% endblock %}
EOFTPL

echo "✅ Template admin créé"

# 5. Vérifier que TWELVE_DATA_API_KEY est dans settings.py
if ! grep -q "TWELVE_DATA_API_KEY" /app/config/settings.py; then
    echo "" >> /app/config/settings.py
    echo "# Twelve Data API" >> /app/config/settings.py
    echo "TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', '')" >> /app/config/settings.py
    echo "✅ Clé API ajoutée à settings.py"
else
    echo "✅ Clé API déjà présente"
fi

# 6. Vérifier les fichiers créés
echo ""
echo "📁 Fichiers créés :"
ls -la /app/templates/base.html
ls -la /app/static/js/ticker_autocomplete.js
ls -la /app/templates/admin/core/symbol/change_form.html

EOFBASH

echo ""
echo "✅ Fichiers créés dans le conteneur"

# ============================================
# Collecter les fichiers statiques
# ============================================
echo "📦 Collecte des fichiers statiques..."
sudo docker compose exec -T web python manage.py collectstatic --noinput

# ============================================
# Redémarrer
# ============================================
echo "🔄 Redémarrage..."
sudo docker compose restart web

sleep 10

echo ""
echo "✅ TERMINÉ !"
echo ""
echo "🌐 Testez maintenant : http://localhost:8000"
echo ""
echo "Le menu doit apparaître en haut de la page"
echo "L'autocomplétion fonctionne dans Admin > Symbols > Ajouter"
echo ""
