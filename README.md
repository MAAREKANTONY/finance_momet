# 📊 Finance Momet - Application Complète de Backtesting

Application Django complète pour le backtesting de stratégies boursières avec collecte automatique de données, calcul d'indicateurs techniques et gestion d'alertes.

## 🎯 Fonctionnalités

### ✅ Gestion des Données
- Import massif de tickers via CSV
- Collecte automatique via Twelve Data API
- Validation des tickers en temps réel
- Gestion multi-scénarios

### ✅ Indicateurs Techniques
- Calcul automatique de P, M, X, M1, X1
- Canaux (T, Q, S)
- Signaux K1-K4
- Détection d'alertes A1-H1
- Indicateurs de tendance (ratio_P, amp_h)

### ✅ Backtesting Avancé
- Backtests multi-tickers
- Stratégies personnalisables (BUY/SELL sur signaux)
- Gestion du capital (CP, CT, X)
- Exécution J+1 (réaliste)
- Statistiques détaillées (N, G, S_G_N, BT, BMJ)
- Archive complète des runs

### ✅ Alertes & Notifications
- Envoi d'emails planifiés
- Inclusion de ratio_P et amp_h
- Configuration SMTP flexible

### ✅ Interface Utilisateur
- Dashboard moderne (Tailwind CSS)
- Visualisations graphiques (Chart.js)
- Logs détaillés et filtrables
- Interface d'administration Django

---

## 🚀 Installation Rapide

### Prérequis
- Docker 20.10+
- Docker Compose 2.0+
- Compte Twelve Data (gratuit : https://twelvedata.com/)
- Compte Gmail (pour les alertes email)

### Installation en 5 Minutes

```bash
# 1. Cloner le dépôt
git clone https://github.com/VOTRE_USERNAME/finance_momet.git
cd finance_momet

# 2. Configuration
cp .env.example .env
nano .env  # Éditer avec vos clés

# 3. Lancer
docker-compose up -d --build

# 4. Migrations
docker-compose exec web python manage.py migrate

# 5. Créer un admin
docker-compose exec web python manage.py createsuperuser

# 6. Accéder
http://localhost:8000         # Dashboard
http://localhost:8000/admin   # Administration
```

---

## ⚙️ Configuration

### Variables d'Environnement (.env)

**OBLIGATOIRES :**
```bash
# API Twelve Data
TWELVE_DATA_API_KEY=votre_cle_api_ici

# Email Gmail
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
```

**Optionnelles :**
```bash
DEBUG=False
SECRET_KEY=votre-secret-key-securisee
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com

DB_NAME=finance_momet
DB_USER=postgres
DB_PASSWORD=postgres
```

### Configuration Email Gmail

1. Activer la 2FA : https://myaccount.google.com/security
2. Créer un mot de passe d'application : https://myaccount.google.com/apppasswords
3. Utiliser ce mot de passe dans `EMAIL_HOST_PASSWORD`

---

## 📚 Utilisation

### 1. Importer des Tickers (CSV)

Créez un fichier `tickers.csv` :
```csv
ticker_code,ticker_market,scenario_list
AAPL,NASDAQ,scenario1,scenario2
MSFT,NASDAQ,scenario1
GOOGL,NASDAQ,scenario1
```

Puis : **Dashboard → Import CSV → Uploader le fichier**

### 2. Créer un Scénario

**Admin → Scenarios → Ajouter**

Paramètres recommandés :
- `a=1, b=1, c=1, d=1` (poids OHLC)
- `e=2` (facteur canal, **ne peut pas être 0**)
- `N1=20, N2=5, N3=10, N4=20` (périodes)

### 3. Créer une Stratégie

**Admin → Backtest Strategies → Ajouter**

Exemple : "MA Crossover"
- Règle 1 : BUY sur A1
- Règle 2 : SELL sur B1

### 4. Lancer un Backtest

**Dashboard → Nouveau Backtest**

- Sélectionner scénario + stratégie
- Définir CP (0=infini), CT (capital/ticker), X (seuil ratio_P)
- Lancer

Le backtest s'exécute en arrière-plan (Celery).

### 5. Consulter les Résultats

**Dashboard → Archive → Cliquer sur un backtest**

Visualisez :
- BT, BMJ, nombre de trades
- Résultats par ticker
- Courbes temporelles
- Détail des transactions

---

## 🔧 Commandes Utiles

### Docker

```bash
# Voir les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f celery

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose down -v

# Reconstruire
docker-compose up -d --build
```

### Django

```bash
# Shell Django
docker-compose exec web python manage.py shell

# Créer des migrations
docker-compose exec web python manage.py makemigrations

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Collecter les static files
docker-compose exec web python manage.py collectstatic
```

### Celery

```bash
# Voir les tâches actives
docker-compose exec celery celery -A config inspect active

# Voir les tâches planifiées
docker-compose exec celery celery -A config inspect scheduled

# Révoquer une tâche
docker-compose exec celery celery -A config control revoke <task_id>
```

---

## 📊 Architecture

```
finance_momet/
├── apps/
│   ├── core/           # Modèles principaux (Symbol, Scenario, etc.)
│   ├── market_data/    # Service Twelve Data
│   ├── indicators/     # Calculateur de métriques
│   ├── alerts/         # Gestion des alertes email
│   ├── backtesting/    # Moteur de backtesting
│   └── dashboard/      # Interface web + import CSV
├── config/             # Configuration Django + Celery
├── templates/          # Templates HTML
├── static/             # CSS/JS
├── docker-compose.yml
└── Dockerfile
```

### Stack Technique

- **Backend** : Django 5.0, Python 3.11
- **Base de données** : PostgreSQL 15
- **Cache/Jobs** : Redis 7 + Celery + Celery Beat
- **Frontend** : Tailwind CSS + Chart.js
- **API** : Twelve Data (données de marché)

---

## 🐛 Dépannage

### Problème : Pas de données Twelve Data

```bash
# Vérifier les logs
docker-compose logs -f celery

# Tester manuellement
docker-compose exec web python manage.py shell
>>> from apps.market_data.services import TwelveDataService
>>> service = TwelveDataService()
>>> result = service.fetch_time_series('AAPL', 'NASDAQ')
>>> print(result)
```

### Problème : Emails non envoyés

```bash
# Vérifier la config
docker-compose exec web python manage.py shell
>>> from apps.core.models import EmailSettings
>>> config = EmailSettings.get_solo()
>>> print(config.from_email, config.smtp_username)

# Tester l'envoi
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', config.from_email, ['dest@example.com'])
```

### Problème : Celery down

```bash
# Redémarrer
docker-compose restart celery celery-beat

# Voir les logs
docker-compose logs -f celery
```

### Problème : Calculs incorrects

```bash
# Vérifier les paramètres du scénario
docker-compose exec web python manage.py shell
>>> from apps.core.models import Scenario
>>> s = Scenario.objects.get(name='scenario1')
>>> print(f"e={s.e}, N1={s.N1}, N2={s.N2}")

# Vérifier qu'e != 0
```

---

## 📈 Workflow Complet

```
1. Import Tickers (CSV)
   ↓
2. Collecte Données (Twelve Data - 22h00)
   ↓
3. Calcul Métriques (Celery - 22h30)
   ↓
4. Détection Alertes (A1..H1)
   ↓
5. Envoi Email (heure configurable)
   ↓
6. Backtesting (manuel)
   ↓
7. Analyse Résultats (Dashboard)
```

---

## 🔒 Sécurité

### Checklist Production

- [ ] `DEBUG=False` dans .env
- [ ] `SECRET_KEY` unique et sécurisé (50+ caractères)
- [ ] HTTPS activé (nginx + Let's Encrypt)
- [ ] Firewall configuré (ports 80/443 uniquement)
- [ ] Base de données avec mot de passe fort
- [ ] Backups automatiques PostgreSQL
- [ ] Rate limiting sur endpoints publics
- [ ] Logs centralisés (Sentry/Datadog recommandé)

---

## 🚧 Développement

### Tests

```bash
# Tests unitaires
docker-compose exec web python manage.py test

# Tests avec coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

### Ajout d'une fonctionnalité

```bash
# Créer une branche
git checkout -b feature/nouvelle-fonctionnalite

# Faire vos modifications...

# Créer une migration
docker-compose exec web python manage.py makemigrations

# Appliquer
docker-compose exec web python manage.py migrate

# Commit
git add .
git commit -m "feat: ajout de la fonctionnalité X"
git push origin feature/nouvelle-fonctionnalite
```

---

## 📝 Licence

MIT License - Voir le fichier LICENSE

---

## 👥 Support

- **GitHub Issues** : https://github.com/VOTRE_USERNAME/finance_momet/issues
- **Email** : support@example.com
- **Documentation API Twelve Data** : https://twelvedata.com/docs

---

## 🎓 Ressources

- [Documentation Django](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Twelve Data API](https://twelvedata.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Chart.js](https://www.chartjs.org/docs/)

---

**Finance Momet v2.0** - Application complète de backtesting boursier 📊
