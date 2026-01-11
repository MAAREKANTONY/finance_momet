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
