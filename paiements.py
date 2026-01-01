import os
import streamlit as st
import requests
from datetime import datetime
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class PaiementManager:
    def __init__(self):
        self.wave_api_key = os.getenv('WAVE_API_KEY')
        self.orange_money_api_key = os.getenv('ORANGE_MONEY_API_KEY')
        self.callback_url = os.getenv('CALLBACK_URL', 'https://votresite.com/callback')
    
    def initier_paiement_wave(self, montant, reference, telephone, description):
        """
        Initialise un paiement via Wave
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.wave_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'amount': str(montant),
                'currency': 'XOF',
                'error_url': f'{self.callback_url}/erreur',
                'success_url': f'{self.callback_url}/success',
                'client_reference': reference,
                'customer_phone_number': telephone,
                'description': description
            }
            
            response = requests.post(
                'https://api.wave.com/v1/checkout/sessions',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                return response.json()['checkout_url']
            else:
                st.error(f"Erreur lors de l'initialisation du paiement Wave: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Erreur: {str(e)}")
            return None
    
    def initier_paiement_orange_money(self, montant, reference, telephone):
        """
        Initialise un paiement via Orange Money Sénégal
        """
        try:
            # Pour Orange Money, vous devez utiliser l'API officielle d'Orange Money Sénégal
            # Ceci est un exemple et nécessite une configuration avec les identifiants Orange Money
            headers = {
                'Authorization': f'Bearer {self.orange_money_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'merchant_key': os.getenv('ORANGE_MERCHANT_KEY'),
                'currency': 'XOF',
                'order_id': reference,
                'amount': str(montant),
                'return_url': f'{self.callback_url}/success',
                'cancel_url': f'{self.callback_url}/cancel',
                'notif_url': f'{self.callback_url}/notif',
                'lang': 'fr',
                'reference': reference,
                'customer_phone': telephone
            }
            
            response = requests.post(
                'https://api.orange.com/orange-money-webpay/senegal/v1/webpayment',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                return response.json()['payment_url']
            else:
                st.error(f"Erreur lors de l'initialisation du paiement Orange Money: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Erreur: {str(e)}")
            return None
    
    def verifier_statut_paiement(self, reference, methode):
        """
        Vérifie le statut d'un paiement
        """
        try:
            if methode.lower() == 'wave':
                headers = {'Authorization': f'Bearer {self.wave_api_key}'}
                response = requests.get(
                    f'https://api.wave.com/v1/checkout/sessions/{reference}',
                    headers=headers
                )
                if response.status_code == 200:
                    return response.json()['status']
                    
            elif methode.lower() == 'orange':
                headers = {'Authorization': f'Bearer {self.orange_money_api_key}'}
                response = requests.get(
                    f'https://api.orange.com/orange-money-webpay/senegal/v1/transaction/{reference}',
                    headers=headers
                )
                if response.status_code == 200:
                    return response.json()['status']
                    
            return None
            
        except Exception as e:
            st.error(f"Erreur lors de la vérification du paiement: {str(e)}")
            return None

def afficher_boutons_paiement(montant, reference, telephone, description):
    """
    Affiche les boutons de paiement dans l'interface Streamlit
    """
    st.subheader("Paiement en ligne")
    st.write(f"Montant à payer : {montant:,} XOF".replace(',', ' '))
    
    paiement_manager = PaiementManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Payer avec Wave"):
            url_paiement = paiement_manager.initier_paiement_wave(
                montant, reference, telephone, description
            )
            if url_paiement:
                st.session_state['en_attente_paiement'] = True
                st.session_state['url_paiement'] = url_paiement
                st.session_state['reference_paiement'] = reference
                st.session_state['methode_paiement'] = 'wave'
    
    with col2:
        if st.button("Payer avec Orange Money"):
            url_paiement = paiement_manager.initier_paiement_orange_money(
                montant, reference, telephone
            )
            if url_paiement:
                st.session_state['en_attente_paiement'] = True
                st.session_state['url_paiement'] = url_paiement
                st.session_state['reference_paiement'] = reference
                st.session_state['methode_paiement'] = 'orange'
    
    # Afficher le lien de paiement si disponible
    if st.session_state.get('en_attente_paiement', False):
        st.warning("Paiement en attente...")
        st.markdown(f"[Cliquez ici pour finaliser le paiement]({st.session_state['url_paiement']})")
        
        # Vérifier le statut du paiement
        if st.button("Vérifier le paiement"):
            statut = paiement_manager.verifier_statut_paiement(
                st.session_state['reference_paiement'],
                st.session_state['methode_paiement']
            )
            
            if statut == 'paid':
                st.success("Paiement confirmé ! Merci pour votre règlement.")
                # Enregistrer le paiement dans la base de données
                enregistrer_paiement(
                    reference=st.session_state['reference_paiement'],
                    montant=montant,
                    methode=st.session_state['methode_paiement'],
                    statut='payé'
                )
                # Réinitialiser l'état
                del st.session_state['en_attente_paiement']
            elif statut in ['pending', 'processing']:
                st.warning("Paiement en cours de traitement...")
            else:
                st.error("Paiement non reçu ou échoué. Veuillez réessayer.")

def enregistrer_paiement(reference, montant, methode, statut):
    """
    Enregistre le paiement dans la base de données
    """
    try:
        conn = sqlite3.connect('isbisportclub.db')
        c = conn.cursor()
        
        # Créer la table si elle n'existe pas
        c.execute('''
            CREATE TABLE IF NOT EXISTS paiements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE,
                montant REAL,
                methode TEXT,
                statut TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insérer le paiement
        c.execute('''
            INSERT INTO paiements (reference, montant, methode, statut)
            VALUES (?, ?, ?, ?)
        ''', (reference, montant, methode, statut))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement du paiement: {str(e)}")
        return False
