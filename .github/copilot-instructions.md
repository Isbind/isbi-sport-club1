# Instructions pour les agents Copilot

Objectif rapide
- Aider un agent à être immédiatement productif sur ce dépôt Python/Streamlit pour la gestion d'un club sportif (ISBISPORTCLUB).

Contexte global (big picture)
- Application principale: interface Streamlit (interfaces : `app.py`, `app_new.py`).
- Logique métier / paiements: `payment_service.py` (génération de références, QR codes, intégration Orange Money / Wave) et `paiements.py` (wrapper d'appel API et helpers Streamlit).
- Configuration centralisée: `config.py` et `config.yaml` (valeurs comme `PAYMENT_CONFIG`, `PATHS`, templates d'emails).
- Données persistantes: sqlite DB (fichiers `isbisport.db`/`isbisportclub.db`) et CSV dans dossiers `adherents/`, `abonnements/`, `factures/`, `seances/`.
- Templates d'email: `templates/emails/*.html` (utilisés par `notifications.py`).

Points d'attention pour l'agent
- Entrypoints: `app.py` et `app_new.py` sont des UIs Streamlit — toute modification doit préserver l'appel `st.set_page_config(...)` au tout début.
- Base de données: code initie et altère le schéma SQLite au runtime (`init_db()` dans `app.py`/`app_new.py`) — respecter les migrations implicites (ajout de colonnes sécurisé par checks PRAGMA).
- Paiements: interactions externes avec APIs (Wave, Orange Money). Ne pas hardcoder de clés API; utiliser `config.py` / `.env` et respecter les formats (`PAYMENT_CONFIG['wave']`, `PAYMENT_CONFIG['orange_money']`).
- Fichiers statiques: QR codes et dossiers sont créés via `config.py` (`PATHS['qrcodes']`).

Conventions de code & patterns observés
- Style: fonctions petites et focalisées (ex: `generate_payment_reference`, `generate_qr_code`, `process_payment`).
- DB access: usage direct de `sqlite3` + pandas `read_sql_query` pour affichage. Préférer transactions explicites et rollback on exception.
- UI: composants Streamlit modulaires — boutons de paiement via `afficher_boutons_paiement()` (dans `paiements.py`).
- Notifications: `notifications.py` construit et envoie emails en utilisant les templates de `templates/emails/`.

Commandes utiles (dev local)
- Activer l'environnement virtuel (exemple enregistré dans les terminaux du workspace):
```
source .venv/bin/activate
pip install -r requirements.txt
```
- Lancer l'UI Streamlit:
```
streamlit run app_new.py
# ou
streamlit run app.py
```

Conventions de sécurité et configuration
- Variables sensibles: utiliser `.env` et `config.py` — ne pas écrire de secrets dans le code. Exemple: `WAVE_API_KEY`, `ORANGE_MONEY_API_KEY`, `ADMIN_EMAIL_PASSWORD`.
- Endpoints callback: `PAYMENT_CONFIG[...]['callback_url']` doit être défini dans l'environnement en production.

Exemples concrets à suivre
- Ajouter un nouveau mode de paiement: implémenter `process_<provider>_payment(...)` dans `payment_service.py`, ajouter la configuration dans `config.py` et appeler depuis `paiements.py`/UI.
- Enregistrer un paiement: appeler `enregistrer_paiement(reference, montant, methode, statut)` (défini dans `paiements.py`) puis envoyer notification via `NotificationService`.
- Modifier templates mails: éditer `templates/emails/payment_received.html` et s'assurer que `NOTIFICATION_CONFIG` dans `config.py` référence le bon chemin.

Tests et vérifications rapides
- Il n'y a pas de suite de tests formelle; valider manuellement:
  - activer `.venv`, installer dépendances
  - lancer `streamlit run app_new.py` et vérifier la navigation
  - tester le flux de paiement en mode simulateur (vérifier QR code généré dans `static/qrcodes`)

Que faire quand vous n'êtes pas sûr
- Recherchez les usages dans le dépôt: exemples d'appel live se trouvent dans `app.py`/`app_new.py` et `paiements.py`.
- Pour toute modification touchant aux paiements ou aux emails, demander validation manuelle (clés, URLs de callback, templates).

Demande de feedback
- J'ai ajouté ces instructions à `.github/copilot-instructions.md`. Indiquez si vous voulez: plus d'exemples de patterns, règles de style supplémentaires, ou procédures CI/CD.

---

Sections détaillées (Paiements, Schéma DB, Déploiement, Exemples)

- Paiements (pratiques & tests)
  - Variables d'environnement importantes (placer dans `.env`):
    - `WAVE_API_KEY`, `WAVE_BUSINESS_ID`, `WAVE_CALLBACK_URL`
    - `ORANGE_MONEY_API_KEY`, `ORANGE_MONEY_MERCHANT_CODE`, `ORANGE_MONEY_MERCHANT_KEY`, `ORANGE_MONEY_CALLBACK_URL`
    - `CALLBACK_URL` (général)
  - Flux attendu pour un paiement en ligne:
    1. Générer une référence via `PaymentService.generate_payment_reference()`.
    2. Initier le paiement via `PaymentService.process_payment(...)` ou `PaiementManager.initier_paiement_*`.
    3. Stocker la tentative (table `paiements`) en `statut='en_attente'` puis vérifier via callback ou check API.
    4. À la confirmation, appeler `enregistrer_paiement(...)` et `NotificationService.send_payment_confirmation(...)`.
  - Fichiers et dossiers: les QR codes sont écrits dans `static/qrcodes` (voir `PATHS['qrcodes']` dans `config.py`).
  - Tests manuels:
    - Remplir `.env` avec des clés de test, lancer Streamlit:
      ```bash
      source .venv/bin/activate
      streamlit run app_new.py
      ```
    - Depuis l'UI, utiliser `Payer avec Wave` / `Payer avec Orange Money`, cliquer sur le lien de paiement, puis `Vérifier le paiement`.
  - Tests unitaires / mocks: pour éviter appels réels, mocker `requests.post` / `requests.get` (ex: `requests-mock` ou `unittest.mock`) dans `payment_service.py`.

- Schéma DB (tables clés et migration runtime)
  - Tables principales observées:
    - `adherents` (colonnes: `id, nom, prenom, telephone, email, statut, type_abonnement, date_inscription, date_fin_abonnement, methode_paiement, statut_paiement, montant_paye, date_dernier_paiement, commentaires, date_creation, date_maj`)
    - `seances` (colonnes: `id, jour_semaine, type_seance, heure_debut, heure_fin, capacite_max, coach, description, statut, date_creation`)
    - `inscriptions` (colonnes: `id, adherent_id, seance_id, date_inscription, statut, presence`)
    - `paiements` (créée par `enregistrer_paiement`, colonnes: `reference, montant, methode, statut, date_creation`)
  - Pattern de migration utilisé: `PRAGMA table_info(table)` puis `ALTER TABLE ADD COLUMN` si manquant (voir `init_db()` dans `app_new.py`).
  - Bonnes pratiques spécifiques au projet: utiliser `conn.rollback()` sur exception, committer explicitement, garder les modifications de schéma minimales et idempotentes.

- Déploiement & callbacks
  - Les callbacks et URLs publiques doivent être configurées avec `CALLBACK_URL` et les clés `WAVE_CALLBACK_URL` / `ORANGE_MONEY_CALLBACK_URL` dans l'environnement.
  - En production: exposer des endpoints HTTPS publics et vérifier les signatures/webhook tokens fournis par les fournisseurs.
  - Tests locaux: utiliser `ngrok` pour exposer votre instance Streamlit lors de tests de callback:
    ```bash
    ngrok http 8501
    ```
  - Ne pas hardcoder les secrets; utilisez un gestionnaire de secrets ou variables d'environnement déployées par CI/CD.

- Exemples de code rapides
  - Ajouter un provider (template):
    ```py
    # dans payment_service.py
    @classmethod
    def process_myprovider_payment(cls, amount, phone, description=""):
        config = PAYMENT_CONFIG['myprovider']
        ref = cls.generate_payment_reference('MP')
        # envoyer requête, générer QR si besoin
        return {'success': True, 'reference': ref, 'payment_url': 'https://...'}
    # et dans process_payment: ajouter un cas `elif payment_method=='myprovider'`.
    ```
  - Test rapide sans UI:
    ```bash
    python - <<'PY'
    from payment_service import PaymentService
    print(PaymentService.process_cash_payment(1000, 'test'))
    PY
    ```

Notes finales
- Les changements qui touchent aux paiements ou notifications nécessitent une validation manuelle (clés, endpoints, templates). Si vous voulez, j'ajoute un petit ensemble de tests unitaires et un exemple `.env.example`.

