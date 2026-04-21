import streamlit as st
import requests
import hmac
import hashlib
import json
from datetime import datetime
import sqlite3
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration Wave (à remplacer avec vos vraies clés)
WAVE_API_KEY = "wave_sn_prod_VOTRE_CLÉ_API"
WAVE_WEBHOOK_SECRET = "VOTRE_SECRET_WEBHOOK"

def verifier_signature_wave(payload, signature):
    """Vérifie la signature du webhook Wave"""
    if not signature:
        return False
    
    expected_signature = hmac.new(
        WAVE_WEBHOOK_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

def traiter_webhook_wave(request_data, signature):
    """Traite les événements webhook de Wave"""
    try:
        # Vérifier la signature
        if not verifier_signature_wave(request_data, signature):
            logger.error("Signature invalide")
            return {"status": "error", "message": "Signature invalide"}
        
        # Parser les données JSON
        event_data = json.loads(request_data)
        event_type = event_data.get('type')
        
        logger.info(f"Événement reçu: {event_type}")
        
        # Traiter selon le type d'événement
        if event_type == "checkout.session.completed":
            return traiter_paiement_reussi(event_data)
        elif event_type == "checkout.session.payment_failed":
            return traiter_paiement_echoue(event_data)
        elif event_type == "merchant.payment_received":
            return traiter_paiement_marchand(event_data)
        elif event_type == "test.test_event":
            return {"status": "success", "message": "Test reçu"}
        else:
            logger.info(f"Événement non traité: {event_type}")
            return {"status": "success", "message": f"Événement {event_type} reçu"}
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

def traiter_paiement_reussi(event_data):
    """Traite un paiement réussi"""
    try:
        payment_data = event_data.get('data', {})
        transaction_id = payment_data.get('transaction_id')
        montant = payment_data.get('amount')
        devise = payment_data.get('currency')
        client_reference = payment_data.get('client_reference')
        
        logger.info(f"Paiement réussi - Transaction: {transaction_id}, Montant: {montant} {devise}")
        
        # Connexion à la base de données
        conn = sqlite3.connect('isbisportclub.db')
        
        try:
            # Mettre à jour le statut du paiement dans la base de données
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE paiements 
                SET statut = 'confirmé',
                    reference = ?,
                    date_confirmation = ?
                WHERE reference = ? OR id = ?
            ''', (transaction_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                   client_reference, client_reference))
            
            conn.commit()
            
            # Envoyer notification au client
            envoyer_notification_paiement(montant, transaction_id, "succès")
            
            return {
                "status": "success", 
                "message": f"Paiement {montant} {devise} confirmé",
                "transaction_id": transaction_id
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement réussi: {str(e)}")
        return {"status": "error", "message": str(e)}

def traiter_paiement_echoue(event_data):
    """Traite un paiement échoué"""
    try:
        payment_data = event_data.get('data', {})
        payment_id = payment_data.get('id')
        error_info = payment_data.get('last_payment_error', {})
        
        logger.error(f"Paiement échoué - ID: {payment_id}, Erreur: {error_info}")
        
        # Mettre à jour le statut dans la base de données
        conn = sqlite3.connect('isbisportclub.db')
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE paiements 
                SET statut = 'échoué',
                    details = ?,
                    date_maj = ?
                WHERE reference = ? OR id = ?
            ''', (f"Erreur: {error_info.get('message', 'Inconnue')}", 
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   payment_id, payment_id))
            
            conn.commit()
            
            return {
                "status": "success", 
                "message": f"Paiement échoué enregistré",
                "payment_id": payment_id
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement échoué: {str(e)}")
        return {"status": "error", "message": str(e)}

def traiter_paiement_marchand(event_data):
    """Traite un paiement reçu par le marchand"""
    try:
        payment_data = event_data.get('data', {})
        transaction_id = payment_data.get('id')
        montant = payment_data.get('amount')
        sender_mobile = payment_data.get('sender_mobile')
        
        logger.info(f"Paiement marchand reçu - Transaction: {transaction_id}, Montant: {montant}, Expéditeur: {sender_mobile}")
        
        # Enregistrer le paiement dans la base de données
        conn = sqlite3.connect('isbisportclub.db')
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO paiements (reference, montant, methode_paiement, date_paiement, 
                                   statut, details, type_paiement)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, montant, 'Wave', datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   'confirmé', f"Payé par {sender_mobile}", 'direct'))
            
            conn.commit()
            
            # Envoyer notification
            envoyer_notification_paiement(montant, transaction_id, "réception")
            
            return {
                "status": "success", 
                "message": f"Paiement direct de {montant} XOF enregistré",
                "transaction_id": transaction_id
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du paiement marchand: {str(e)}")
        return {"status": "error", "message": str(e)}

def envoyer_notification_paiement(montant, transaction_id, statut):
    """Envoie une notification de paiement"""
    try:
        if statut == "succès":
            message = f"✅ Paiement de {montant} XOF confirmé (Ref: {transaction_id})"
        elif statut == "réception":
            message = f"💰 Paiement de {montant} XOF reçu (Ref: {transaction_id})"
        else:
            message = f"❌ Paiement échoué (Ref: {transaction_id})"
        
        # Afficher la notification dans l'application
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        st.session_state.notifications.append({
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': statut
        })
        
        logger.info(f"Notification envoyée: {message}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")

def creer_session_paiement_wave(montant, description, client_reference=None):
    """Crée une session de paiement Wave"""
    try:
        url = "https://api.wave.com/v1/checkout/sessions"
        headers = {
            "Authorization": f"Bearer {WAVE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": str(montant),
            "currency": "XOF",
            "error_callback_url": "https://votre-app.streamlit.app/webhook/wave",
            "success_callback_url": "https://votre-app.streamlit.app/paiement/succes",
            "client_reference": client_reference or f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        if description:
            payload["description"] = description
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            session_data = response.json()
            return {
                "success": True,
                "payment_url": session_data.get("payment_url"),
                "session_id": session_data.get("id")
            }
        else:
            return {
                "success": False,
                "error": response.text
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de la création de la session de paiement: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def afficher_notifications():
    """Affiche les notifications dans l'interface"""
    if 'notifications' in st.session_state and st.session_state.notifications:
        st.sidebar.markdown("### 📢 Notifications")
        
        # Afficher les 5 notifications les plus récentes
        notifications_recentes = st.session_state.notifications[-5:]
        
        for notification in reversed(notifications_recentes):
            if notification['type'] == 'succès':
                st.sidebar.success(notification['message'])
            elif notification['type'] == 'réception':
                st.sidebar.info(notification['message'])
            else:
                st.sidebar.error(notification['message'])
            
            st.sidebar.caption(f"🕐 {notification['timestamp']}")
            st.sidebar.markdown("---")
