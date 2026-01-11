#!/bin/bash
# generate_templates.sh - Génère tous les templates HTML

cd ~/projet_finance_moment/V_CL/project/finance_momet

echo "╔════════════════════════════════════════════════╗"
echo "║  GÉNÉRATION DES TEMPLATES HTML                 ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# ============================================
# 1. TEMPLATES/DASHBOARD/SYMBOL_LIST.HTML
# ============================================
echo "📝 [1/8] templates/dashboard/symbol_list.html..."

cat > templates/dashboard/symbol_list.html << 'EOFHTML'
{% extends 'base.html' %}

{% block title %}Gestion des Tickers - Finance Momet{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4">
    <!-- En-tête -->
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-4xl font-bold text-gray-900">📈 Mes Tickers</h1>
            <p class="text-gray-600 mt-2">Gérez vos actions et ETF surveillés</p>
        </div>
        <a href="{% url 'symbol_create' %}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-200 flex items-center">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Ajouter un Ticker
        </a>
    </div>
    
    <!-- Filtres -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
        <form method="get" class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">🔍 Recherche</label>
                <input type="text" name="search" value="{{ request.GET.search }}" 
                       placeholder="Code ou nom..."
                       class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">🏛️ Bourse</label>
                <select name="exchange" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    <option value="">Toutes</option>
                    {% for exchange in exchanges %}
                    <option value="{{ exchange }}" {% if request.GET.exchange == exchange %}selected{% endif %}>{{ exchange }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">📊 Statut</label>
                <select name="is_active" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    <option value="">Tous</option>
                    <option value="true" {% if request.GET.is_active == 'true' %}selected{% endif %}>Actifs</option>
                    <option value="false" {% if request.GET.is_active == 'false' %}selected{% endif %}>Inactifs</option>
                </select>
            </div>
            
            <div class="flex items-end">
                <button type="submit" class="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                    Filtrer
                </button>
            </div>
        </form>
    </div>
    
    <!-- Liste des tickers -->
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Code</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Nom</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Bourse</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Statut</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {% for symbol in page_obj %}
                    <tr class="hover:bg-blue-50 transition duration-150">
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="text-lg font-bold text-blue-600 font-mono">{{ symbol.code }}</span>
                        </td>
                        <td class="px-6 py-4">
                            <span class="text-sm text-gray-900">{{ symbol.name|default:"—" }}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="text-sm text-gray-600">{{ symbol.exchange }}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center">
                            {% if symbol.is_active %}
                            <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                                ✓ Actif
                            </span>
                            {% else %}
                            <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                ✗ Inactif
                            </span>
                            {% endif %}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-center space-x-2">
                            <a href="{% url 'symbol_edit' symbol.id %}" 
                               class="inline-flex items-center px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 text-sm font-medium rounded-lg transition">
                                ✏️ Modifier
                            </a>
                            <a href="{% url 'symbol_delete' symbol.id %}" 
                               class="inline-flex items-center px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded-lg transition">
                                🗑️ Supprimer
                            </a>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="5" class="px-6 py-12 text-center">
                            <div class="text-gray-400 text-lg">
                                <p class="mb-4">📭 Aucun ticker trouvé</p>
                                <a href="{% url 'symbol_create' %}" class="text-blue-600 hover:text-blue-800 font-semibold">
                                    Créer votre premier ticker →
                                </a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Pagination -->
        {% if page_obj.has_other_pages %}
        <div class="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div class="flex justify-between items-center">
                <div class="text-sm text-gray-600">
                    Page {{ page_obj.number }} sur {{ page_obj.paginator.num_pages }} • Total : {{ total_count }} ticker(s)
                </div>
                <div class="flex space-x-2">
                    {% if page_obj.has_previous %}
                    <a href="?page={{ page_obj.previous_page_number }}" class="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                        ← Précédent
                    </a>
                    {% endif %}
                    
                    {% if page_obj.has_next %}
                    <a href="?page={{ page_obj.next_page_number }}" class="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                        Suivant →
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
EOFHTML

echo "✅ symbol_list.html créé"

# ============================================
# 2. TEMPLATES/DASHBOARD/SYMBOL_FORM.HTML
# ============================================
echo "📝 [2/8] templates/dashboard/symbol_form.html..."

cat > templates/dashboard/symbol_form.html << 'EOFHTML'
{% extends 'base.html' %}

{% block title %}{{ title }} - Finance Momet{% endblock %}

{% block content %}
<div class="max-w-3xl mx-auto px-4">
    <!-- Breadcrumb -->
    <div class="mb-6">
        <a href="{% url 'symbol_list' %}" class="text-blue-600 hover:text-blue-800 text-sm">← Retour à la liste</a>
    </div>
    
    <!-- En-tête -->
    <div class="mb-8">
        <h1 class="text-4xl font-bold text-gray-900">{{ title }}</h1>
        <p class="text-gray-600 mt-2">Ajoutez un ticker pour commencer à le surveiller</p>
    </div>
    
    <!-- Aide -->
    <div class="bg-blue-50 border-l-4 border-blue-500 p-6 mb-8 rounded-r-lg">
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            </div>
            <div class="ml-3">
                <h3 class="text-lg font-semibold text-blue-900">💡 Astuce</h3>
                <p class="text-blue-800 mt-2">
                    Commencez à taper le code du ticker (au moins 2 caractères) et une liste de suggestions apparaîtra automatiquement.
                    Les champs "Bourse" et "Nom" se rempliront automatiquement lorsque vous sélectionnerez un ticker.
                </p>
            </div>
        </div>
    </div>
    
    <!-- Formulaire -->
    <form method="post" class="bg-white shadow-xl rounded-lg overflow-hidden">
        {% csrf_token %}
        
        <div class="p-8 space-y-6">
            <!-- Code -->
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">
                    {{ form.code.label }}
                    <span class="text-red-500">*</span>
                </label>
                {{ form.code }}
                {% if form.code.help_text %}
                <p class="mt-2 text-sm text-gray-500">{{ form.code.help_text }}</p>
                {% endif %}
                {% if form.code.errors %}
                <p class="mt-2 text-sm text-red-600">{{ form.code.errors.0 }}</p>
                {% endif %}
                
                <!-- Zone de suggestions (remplie par JavaScript) -->
                <div id="ticker-suggestions" class="hidden mt-2"></div>
            </div>
            
            <!-- Exchange -->
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">
                    {{ form.exchange.label }}
                    <span class="text-red-500">*</span>
                </label>
                {{ form.exchange }}
                {% if form.exchange.errors %}
                <p class="mt-2 text-sm text-red-600">{{ form.exchange.errors.0 }}</p>
                {% endif %}
            </div>
            
            <!-- Name -->
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">
                    {{ form.name.label }}
                </label>
                {{ form.name }}
                {% if form.name.errors %}
                <p class="mt-2 text-sm text-red-600">{{ form.name.errors.0 }}</p>
                {% endif %}
            </div>
            
            <!-- Is Active -->
            <div class="flex items-start">
                <div class="flex items-center h-5">
                    {{ form.is_active }}
                </div>
                <div class="ml-3">
                    <label for="{{ form.is_active.id_for_label }}" class="font-medium text-gray-700 cursor-pointer">
                        {{ form.is_active.label }}
                    </label>
                    {% if form.is_active.help_text %}
                    <p class="text-sm text-gray-500">{{ form.is_active.help_text }}</p>
                    {% endif %}
                </div>
            </div>
            
            <!-- Erreurs non-field -->
            {% if form.non_field_errors %}
            <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
                {% for error in form.non_field_errors %}
                <p class="text-red-800">{{ error }}</p>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <!-- Actions -->
        <div class="bg-gray-50 px-8 py-6 flex justify-between items-center border-t">
            <a href="{% url 'symbol_list' %}" class="px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition">
                Annuler
            </a>
            <button type="submit" class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-lg transition duration-200">
                {{ submit_text }}
            </button>
        </div>
    </form>
</div>

<!-- JavaScript pour l'autocomplétion -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('ticker-code-input');
    const suggestionsDiv = document.getElementById('ticker-suggestions');
    const exchangeInput = document.querySelector('input[name="exchange"]');
    const nameInput = document.querySelector('input[name="name"]');
    
    let debounceTimer;
    
    // Styles pour les suggestions
    suggestionsDiv.className = 'absolute z-50 w-full bg-white border-2 border-blue-500 rounded-lg shadow-2xl mt-1 max-h-96 overflow-y-auto';
    
    input.addEventListener('input', function(e) {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        
        if (query.length >= 2) {
            debounceTimer = setTimeout(() => searchTicker(query), 400);
        } else {
            hideSuggestions();
        }
    });
    
    async function searchTicker(query) {
        try {
            const response = await fetch(`{% url 'ticker_autocomplete_api' %}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                showSuggestions(data.results);
            } else {
                showNoResults();
            }
        } catch (error) {
            console.error('Erreur:', error);
            showError();
        }
    }
    
    function showSuggestions(results) {
        suggestionsDiv.innerHTML = results.map(item => `
            <div class="suggestion-item px-6 py-4 hover:bg-blue-50 cursor-pointer border-b last:border-b-0 transition"
                 data-symbol="${item.symbol}"
                 data-exchange="${item.exchange}"
                 data-name="${item.name}">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="font-bold text-lg text-blue-600">${item.symbol}</div>
                        <div class="text-sm text-gray-700 mt-1">${item.name || 'N/A'}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs bg-gray-100 px-2 py-1 rounded font-semibold">${item.exchange || 'N/A'}</div>
                        <div class="text-xs text-gray-500 mt-1">${item.country || ''}</div>
                    </div>
                </div>
            </div>
        `).join('');
        
        suggestionsDiv.classList.remove('hidden');
        
        // Événements de clic
        document.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', function() {
                input.value = this.dataset.symbol;
                exchangeInput.value = this.dataset.exchange;
                nameInput.value = this.dataset.name;
                hideSuggestions();
            });
        });
    }
    
    function showNoResults() {
        suggestionsDiv.innerHTML = `
            <div class="px-6 py-8 text-center text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <p class="font-semibold">Aucun ticker trouvé</p>
                <p class="text-sm mt-1">Essayez un autre code</p>
            </div>
        `;
        suggestionsDiv.classList.remove('hidden');
    }
    
    function showError() {
        suggestionsDiv.innerHTML = `
            <div class="px-6 py-4 text-center text-red-600">
                ⚠️ Erreur de connexion à l'API
            </div>
        `;
        suggestionsDiv.classList.remove('hidden');
    }
    
    function hideSuggestions() {
        suggestionsDiv.classList.add('hidden');
    }
    
    // Fermer au clic extérieur
    document.addEventListener('click', function(e) {
        if (e.target !== input && !suggestionsDiv.contains(e.target)) {
            hideSuggestions();
        }
    });
    
    // Position relative pour le parent
    input.parentElement.style.position = 'relative';
});
</script>
{% endblock %}
EOFHTML

echo "✅ symbol_form.html créé"

# ============================================
# 3. TEMPLATES/DASHBOARD/SYMBOL_CONFIRM_DELETE.HTML
# ============================================
echo "📝 [3/8] templates/dashboard/symbol_confirm_delete.html..."

cat > templates/dashboard/symbol_confirm_delete.html << 'EOFHTML'
{% extends 'base.html' %}

{% block title %}Supprimer {{ symbol.code }} - Finance Momet{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto px-4">
    <div class="bg-white shadow-2xl rounded-lg overflow-hidden">
        <!-- En-tête rouge -->
        <div class="bg-red-600 px-8 py-6">
            <div class="flex items-center">
                <svg class="w-12 h-12 text-white mr-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <div>
                    <h1 class="text-3xl font-bold text-white">Confirmer la Suppression</h1>
                    <p class="text-red-100 mt-1">Cette action est irréversible</p>
                </div>
            </div>
        </div>
        
        <!-- Contenu -->
        <div class="p-8">
            <div class="mb-6">
                <p class="text-lg text-gray-700 mb-4">
                    Êtes-vous sûr de vouloir supprimer le ticker <strong class="text-2xl font-bold text-red-600">{{ symbol.code }}</strong> ?
                </p>
                
                <div class="bg-gray-50 border-l-4 border-gray-400 p-4 rounded-r-lg mb-4">
                    <p class="text-sm text-gray-700">
                        <strong>Bourse :</strong> {{ symbol.exchange }}<br>
                        <strong>Nom :</strong> {{ symbol.name|default:"N/A" }}
                    </p>
                </div>
            </div>
            
            <!-- Avertissement -->
            <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-6 rounded-r-lg">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-6 w-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-sm font-semibold text-yellow-800">⚠️ Attention</h3>
                        <div class="mt-2 text-sm text-yellow-700">
                            <p>Cette action supprimera définitivement :</p>
                            <ul class="list-disc list-inside mt-2 space-y-1">
                                <li>Toutes les données historiques (barres OHLCV)</li>
                                <li>Toutes les métriques calculées</li>
                                <li>Toutes les alertes associées</li>
                                <li>Tous les résultats de backtests</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Actions -->
            <form method="post" class="flex space-x-4">
                {% csrf_token %}
                <a href="{% url 'symbol_list' %}" class="flex-1 px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold rounded-lg text-center transition">
                    ← Annuler
                </a>
                <button type="submit" class="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-lg transition duration-200">
                    🗑️ Supprimer Définitivement
                </button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
EOFHTML

echo "✅ symbol_confirm_delete.html créé"

# Continuer dans le prochain message avec les templates scénarios...
