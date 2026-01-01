# Déploiement de l'application ISBISPORTCLUB

## Option 1 : Déploiement sur Streamlit Cloud (Gratuit)

1. Créez un compte sur [Streamlit Cloud](https://streamlit.io/cloud)
2. Connectez votre compte GitHub
3. Créez une nouvelle application et sélectionnez votre dépôt
4. Spécifiez le fichier principal : `app.py`
5. Ajoutez les variables d'environnement :
   - `ADMIN_USERNAME`=votre_identifiant
   - `ADMIN_PASSWORD`=votre_mot_de_passe
6. Cliquez sur "Deploy"

## Option 2 : Déploiement sur un VPS (Plus de contrôle)

1. Connectez-vous à votre serveur via SSH
2. Installez les dépendances :
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv
   ```
3. Clonez le dépôt :
   ```bash
   git clone [URL_DU_REPO]
   cd ISBISPORTCLUB
   ```
4. Créez un environnement virtuel :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
5. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
6. Installez gunicorn :
   ```bash
   pip install gunicorn
   ```
7. Créez un service systemd pour exécuter l'application :
   ```bash
   sudo nano /etc/systemd/system/isbisportclub.service
   ```
   
   Ajoutez ce contenu (adaptez les chemins) :
   ```ini
   [Unit]
   Description=ISBISPORTCLUB Web Application
   After=network.target

   [Service]
   WorkingDirectory=/chemin/vers/ISBISPORTCLUB
   ExecStart=/chemin/vers/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   User=www-data
   Group=www-data
   Restart=always
   Environment="PATH=/chemin/vers/venv/bin"

   [Install]
   WantedBy=multi-user.target
   ```

8. Activez et démarrez le service :
   ```bash
   sudo systemctl enable isbisportclub
   sudo systemctl start isbisportclub
   ```

## Accès sécurisé avec Nginx (Recommandé)

1. Installez Nginx :
   ```bash
   sudo apt install nginx
   ```

2. Créez un fichier de configuration :
   ```bash
   sudo nano /etc/nginx/sites-available/isbisportclub
   ```

   Ajoutez cette configuration (remplacez `votre_domaine.com` par votre domaine) :
   ```nginx
   server {
       listen 80;
       server_name votre_domaine.com www.votre_domaine.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

3. Activez le site :
   ```bash
   sudo ln -s /etc/nginx/sites-available/isbisportclub /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Sécurité

1. **Mettez à jour le mot de passe par défaut** dans `config.yaml`
2. Activez HTTPS avec Let's Encrypt :
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d votre_domaine.com -d www.votre_domaine.com
   ```
3. Configurez le renouvellement automatique :
   ```bash
   sudo certbot renew --dry-run
   ```

## Accès à distance

Une fois déployé, vous pourrez accéder à votre application depuis n'importe où via :
- L'URL fournie par Streamlit Cloud (option 1)
- Votre nom de domaine (option 2)

**Identifiants par défaut :**
- Utilisateur : admin
- Mot de passe : admin123

**Important :** Changez ces identifiants immédiatement après la première connexion !
