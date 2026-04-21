import streamlit as st
import json
import hmac
import hashlib
from webhook_wave import traiter_webhook_wave

# Page pour gérer les webhooks Wave
def webhook_wave_handler():
    """Gère les webhooks entrants de Wave"""
    
    # Titre de la page
    st.set_page_config(page_title="Wave Webhook", page_icon="🌊", layout="centered")
    
    st.title("🌊 Webhook Wave")
    st.write("Point de terminaison pour les notifications de paiement Wave")
    
    # Récupérer les données de la requête
    if st.request.method == 'POST':
        try:
            # Récupérer le corps de la requête
            body = st.request.body.decode('utf-8')
            signature = st.request.headers.get('Wave-Signature')
            
            # Traiter le webhook
            result = traiter_webhook_wave(body, signature)
            
            if result['status'] == 'success':
                st.success("✅ Webhook traité avec succès")
                st.json(result)
            else:
                st.error(f"❌ Erreur lors du traitement: {result['message']}")
                
        except Exception as e:
            st.error(f"❌ Erreur serveur: {str(e)}")
    else:
        st.info("Cette page gère les webhooks POST de Wave")
        
        # Afficher les informations de configuration
        st.markdown("""
        ### Configuration requise:
        
        1. **URL du webhook**: `https://votre-app.streamlit.app/webhook/wave`
        2. **Événements à souscrire**:
           - `checkout.session.completed`
           - `checkout.session.payment_failed`
           - `merchant.payment_received`
        
        3. **Secret**: Configurez un secret dans votre portail Wave Business
        
        ### Test du webhook:
        Utilisez le bouton "Tester" dans votre portail Wave Business pour vérifier la configuration.
        """)

if __name__ == "__main__":
    webhook_wave_handler()
