# Instructions pour agents Copilot

## Vue d'ensemble

**ISBISPORTCLUB** est une application Streamlit pour la gestion d'un club sportif en Afrique (Sénégal) avec support des paiements mobiles (Wave, Orange Money). Architecture : UI Streamlit → couche métier service → SQLite + CSVs.

## Architecture essentielle

### Composants clés et flux de données

| Composant | Responsabilité | Détails |
|-----------|----------------|---------|
| `app_new.py` | Entrypoint UI + init DB | `st.set_page_config(...)` DOIT être la 1ère ligne |
| `payment_service.py` | Paiements B2C multiprotocole | Classes `PaymentService` : génère références, QR, appelle APIs |
| `paiements.py` | Glue UI ↔ APIs + enregistrement DB | `PaiementManager` pour initier paiements, `enregistrer_paiement()` pour persistance |
| `config.py` | Config centralisée | `PAYMENT_CONFIG['wave'/'orange_money']`, `PATHS['qrcodes']`, `NOTIFICATION_CONFIG` |
| `notifications.py` | Emails transactionnels | Templates HTML + logs d'envoi |

**Flux paiement complet** : UI → `PaiementManager.initier_paiement_*()` → `PaymentService.process_*_payment()` → génère QR + appel API → `enregistrer_paiement()` → DB (table `paiements`) → webhook/callback pour confirmation.

### Persistance

- **SQLite** : `isbisport.db` — schéma : `adherents` (id, nom, prenom, telephone, email, statut, type_abonnement, date_inscription, montant_paye, statut_paiement, commentaires, etc.), `seances`, `inscriptions`, `paiements`.
- **CSVs** : `adherents/*.csv`, `abonnements/*.csv`, `factures/*.csv`, `seances/*.csv` — chargement/export manuel.
- **Migration runtime** : `init_db()` utilise `PRAGMA table_info(...)` pour vérifier colonnes, puis `ALTER TABLE ADD COLUMN` pour ajouts idempotents.

## Patterns spécifiques au projet

### Base de données
```python
# Idéal : transactions explicites avec rollback
try:
    c.execute("INSERT INTO adherents ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    return False, f"Erreur : {str(e)}"
```

### Paiements
```python
# Toujours via PAYMENT_CONFIG (ne jamais hardcoder clés)
from config import PAYMENT_CONFIG
api_key = PAYMENT_CONFIG['wave']['api_key']  # provient de .env

# Service retourne dict {success: bool, reference: str, payment_url: str, ...}
# pour testabilité facile avec mocks
```

### Tests
- Moquent `requests.post` via `@patch('payment_service.requests.post')`
- Patchent `PATHS['qrcodes']` avec `tmp_path` (voir `tests/test_payment_service.py`)
- Exemple : `test_payment_service.py` démontre les pattern de mock

### UI Streamlit
- Affichage erreurs : `st.error(...)` pour messages utilisateur
- Pages stateless : données via session state ou DB query
- Composants modulaires : e.g., boutons paiement via `afficher_boutons_paiement()` dans `paiements.py`

## Workflows dev

### Installation & démarrage
```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_new.py
```

### Tests
```bash
pytest tests/test_payment_service.py -q  # paiements
pytest tests/                             # tous
```

### Tester callbacks (webhooks paiements) en local
1. Exposer Streamlit : `ngrok http 8501`
2. Mettre `CALLBACK_URL=https://<ngrok-url>/callback` dans `.env`
3. Configurer Wave/Orange Money pour pointer sur `CALLBACK_URL`

## Secrets & variables d'environnement

**Jamais hardcoder** : `WAVE_API_KEY`, `ORANGE_MONEY_API_KEY`, `ADMIN_EMAIL_PASSWORD`, clés tokens.
Utiliser `.env` + `config.py` (qui charge via `load_dotenv()`). Exemples :
- `WAVE_API_KEY=sk_test_xxx` → `PAYMENT_CONFIG['wave']['api_key']`
- `ORANGE_MONEY_MERCHANT_CODE=...` → `PAYMENT_CONFIG['orange_money']['merchant_code']`

## Fichiers prioritaires à lire

1. `app_new.py` (900 lignes) : UI complète + `init_db()` + CRUD adhérents
2. `config.py` (275 lignes) : `PAYMENT_CONFIG`, `PATHS`, `NOTIFICATION_CONFIG`
3. `payment_service.py` (216 lignes) : `PaymentService` class avec `process_wave_payment()`, `process_orange_money_payment()`, `process_cash_payment()`, génération QR
4. `paiements.py` (218 lignes) : `PaiementManager` + `enregistrer_paiement()` (glue DB)

## Conseils pour nouvelles features

- **Ajouter provider paiement** : 1) créer `PaymentService.process_<provider>_payment()` retournant dict `{success, reference, payment_url}` 2) ajouter config dans `config.py` 3) exposer dans UI via `paiements.py`
- **Migrer DB** : utiliser pattern `PRAGMA table_info(...) + ALTER TABLE ADD COLUMN` pour idempotence
- **Modifier templates email** : valider `NOTIFICATION_CONFIG[<type>]['template']` pointe bien fichier HTML existant
- **Tester API réseau** : moque `requests` (voir `test_payment_service.py`) — pas d'appels réels en tests

## CI/CD & Déploiement

### GitHub Actions (`.github/workflows/ci.yml`)
- Lance `pytest -q` sur chaque `push` vers `main` et PR
- Matrice : Python 3.11
- Cache pip pour performance
- Ajouter étapes supplémentaires si lint/type checking nécessaire

### Options déploiement
| Plateforme | Commande / Config | Secrets | Persistance |
|-----------|------------------|---------|------------|
| **Streamlit Cloud** | Connecter repo → `app_new.py` | Via "Secrets" UI | SQLite dans `/tmp` (limité) |
| **Render** | Build: `pip install -r requirements.txt` / Run: `streamlit run app_new.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` | Env vars dans dashboard | Disque persistant ou DB géré |
| **Heroku** | Procfile fourni | Config Vars | Disque éphémère — migration vers PostgreSQL recommandée |
| **Docker (local/VPS)** | `docker-compose up --build` charge `.env` | `.env` (fichier local) | Bind mount ou volume |

**Note production** : SQLite sur Streamlit Cloud n'est pas persistant. Pour production, migrer vers PostgreSQL via `DB_URL` et adapter code SQLite → SQLAlchemy.

## Secrets & Déploiement

### `.env` local (jamais committer)
```bash
WAVE_API_KEY=sk_test_xxx
WAVE_BUSINESS_ID=biz_xxx
ORANGE_MONEY_API_KEY=om_test_xxx
ORANGE_MONEY_MERCHANT_CODE=merchant_xxx
ORANGE_MONEY_MERCHANT_KEY=key_xxx
ADMIN_EMAIL_PASSWORD=app_password_gmail
CALLBACK_URL=https://votresite.com/callback  # Production uniquement
```

### Procédure déploiement sécurisé
1. **GitHub Secrets** (repo Settings → Secrets) pour CI/CD
2. **PaaS Env Vars** (Render/Heroku dashboards) : jamais dans code
3. **Docker** : créer `.env.production` localement, NE PAS committer
4. Exemple `.env.example` : committer template sans valeurs
```bash
WAVE_API_KEY=sk_test_
ORANGE_MONEY_API_KEY=om_test_
ADMIN_EMAIL_PASSWORD=
CALLBACK_URL=https://your-app-url.com/callback
```

## Intégration API & Webhooks

### Flux paiement avec callback
```python
# 1. Initiation (utilisateur click → PaymentService)
ref = PaymentService.generate_payment_reference('WAVE')
result = PaymentService.process_wave_payment(
    amount=15000, 
    phone='221700000000', 
    description='Abonnement mensuel'
)
# → {success: True, reference: ref, payment_url: checkout_url, ...}

# 2. Redirection utilisateur → checkout_url (Wave/Orange)
# → Utilisateur paie

# 3. Callback webhook (entrant depuis API)
# Dans app_new.py, créer endpoint FastAPI ou route pour:
@app.post("/callback/wave")
async def webhook_wave(request: Request):
    payload = await request.json()
    # Vérifier signature payload (sécurité critique)
    # Récupérer reference depuis payload
    # SELECT FROM paiements WHERE reference = ref
    # UPDATE statut_paiement = 'Confirmé' + commit
    # Envoyer email confirmation via notifications.py

# 4. Configuration production
# CALLBACK_URL=https://votreapp.com/callback/wave
# Wave/Orange settings: webhook URL = CALLBACK_URL
```

### Migration DB (ajouter colonnes)
```python
# Pattern idempotent utilisé dans app_new.py:
c.execute("PRAGMA table_info(adherents)")
columns = [col[1] for col in c.fetchall()]

if 'new_column' not in columns:
    c.execute('ALTER TABLE adherents ADD COLUMN new_column TEXT DEFAULT NULL')
    conn.commit()
```

### Export CSV / Excel
Patterns existants dans `app_new.py` :
```python
# Import Excel
df_import = pd.read_excel(fichier)
for _, row in df_import.iterrows():
    adherent = {'nom': row['Nom'], ...}
    ajouter_adherent(conn, adherent)

# Export (utiliser pour nouveaux exports)
import io
output = io.BytesIO()
df.to_excel(output, index=False, engine='openpyxl')
st.download_button(
    label="Télécharger Excel",
    data=output.getvalue(),
    file_name="adherents.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

### Tables & schéma
- `adherents` : id, nom, prenom, telephone, email, statut, type_abonnement, date_inscription, date_fin_abonnement, montant_paye, statut_paiement, commentaires, etc.
- `seances` : id, jour_semaine, type_seance, heure_debut, heure_fin, capacite_max, coach, description, statut
- `inscriptions` : id, adherent_id (FK), seance_id (FK), date_inscription, statut, presence (booléen)
- `paiements` : reference, adherent_id, montant, methode, statut, date_creation, date_confirmation

## Limites & garde-fous

- ❌ Ne jamais exécuter paiements réels en dev — utiliser clés test/sandbox
- ❌ Ne pas stocker mots de passe/tokens dans Git
- ❌ Callbacks/webhooks = logique critique — révision manuelle obligatoire avant déploiement
- ❌ SQLite en production Streamlit Cloud est limité — utiliser PostgreSQL pour scalabilité
- ✅ Secrets dans `.env` local + GitHub Secrets + PaaS env vars (jamais Code)
- ✅ Tester webhooks localement avec ngrok + `CALLBACK_URL=https://<ngrok>.ngrok.io/callback`
- ✅ Préférer petites fonctions ciblées plutôt que méthodes monolithes

