# 🌊 Guide d'Intégration Wave pour ISBISPORTCLUB

## 📋 Vue d'ensemble

Ce guide explique comment intégrer les paiements Wave dans votre application ISBISPORTCLUB pour recevoir des notifications automatiques après chaque paiement.

## 🔧 Prérequis

1. **Compte Wave Business** actif
2. **Clé API Wave** (obtenir depuis le portail Wave Business)
3. **URL de votre application** Streamlit Cloud

## ⚙️ Configuration

### 1. Obtenir vos clés Wave

1. Connectez-vous à votre [portail Wave Business](https://business.wave.com)
2. Allez dans **Paramètres** → **API**
3. Générez une nouvelle clé API
4. Copiez la clé API et le secret webhook

### 2. Configurer les variables d'environnement

Dans votre fichier `.env`:

```bash
WAVE_API_KEY=wave_sn_prod_VOTRE_CLÉ_API
WAVE_WEBHOOK_SECRET=VOTRE_SECRET_WEBHOOK
```

### 3. Mettre à jour le code

Dans `webhook_wave.py`, remplacez les valeurs par défaut:

```python
WAVE_API_KEY = "wave_sn_prod_VOTRE_CLÉ_API"
WAVE_WEBHOOK_SECRET = "VOTRE_SECRET_WEBHOOK"
```

## 🌐 Configuration du Webhook

### 1. Enregistrer le webhook

Dans votre portail Wave Business:

1. Allez dans **Webhooks** → **Ajouter un webhook**
2. **URL du webhook**: `https://votre-app.streamlit.app/webhook/wave`
3. **Événements à souscrire**:
   - ✅ `checkout.session.completed`
   - ✅ `checkout.session.payment_failed`
   - ✅ `merchant.payment_received`
   - ✅ `test.test_event` (pour les tests)

### 2. Configurer la sécurité

- **Secret**: Utilisez le secret généré par Wave
- **IP autorisées**: Ajoutez les IPs de Streamlit Cloud si nécessaire

## 🚀 Déploiement

### 1. Mettre à jour les dépendances

```bash
pip install -r requirements.txt
```

### 2. Pousser les modifications

```bash
git add .
git commit -m "Intégration des paiements Wave"
git push origin main
```

### 3. Redéployer sur Streamlit Cloud

L'application se redéploiera automatiquement après le push.

## 🧪 Tests

### 1. Tester le webhook

1. Dans le portail Wave Business, cliquez sur **Tester** à côté de votre webhook
2. Vérifiez que vous recevez une notification de test dans l'application

### 2. Test de paiement

1. Créez un nouvel adhérent dans l'application
2. Sélectionnez **Wave** comme méthode de paiement
3. Cliquez sur le bouton **Payer avec Wave 🌊**
4. Complétez le paiement via l'application Wave
5. Vérifiez que:
   - ✅ Le statut de l'adhérent passe à "Actif"
   - ✅ Une notification apparaît dans la barre latérale
   - ✅ Le paiement est enregistré dans la base de données

## 📊 Fonctionnalités intégrées

### ✅ Paiements automatiques
- Création de sessions de paiement Wave
- Redirection vers l'application Wave
- Gestion des callbacks de succès/échec

### ✅ Notifications en temps réel
- Notifications dans l'interface Streamlit
- Mises à jour automatiques du statut des adhérents
- Historique des paiements

### ✅ Sécurité
- Vérification des signatures de webhooks
- Validation des transactions
- Protection contre les fraudes

## 🔍 Dépannage

### Erreurs courantes

1. **"Signature invalide"**
   - Vérifiez que le secret webhook est correct
   - Assurez-vous que l'URL du webhook est accessible

2. **"Échec de la création de session"**
   - Vérifiez votre clé API
   - Assurez-vous que le montant est valide (en XOF)

3. **"Webhook non reçu"**
   - Vérifiez que l'URL est correcte
   - Assurez-vous que le portail Wave peut accéder à votre application

### Logs

Les erreurs sont enregistrées dans les logs de Streamlit Cloud:
1. Allez dans votre application Streamlit Cloud
2. Cliquez sur **Manage app**
3. Allez dans l'onglet **Logs**

## 📞 Support

- **Documentation Wave**: https://docs.wave.com
- **Support Wave**: support@wave.com
- **Issues du projet**: Signalez tout problème dans les issues GitHub

## 🔄 Mises à jour

Pour mettre à jour l'intégration:
1. Mettez à jour le code si nécessaire
2. Testez en environnement local
3. Déployez sur Streamlit Cloud

---

**🎉 Votre application ISBISPORTCLUB est maintenant prête à accepter les paiements Wave !**
