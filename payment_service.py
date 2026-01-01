import os
import json
import requests
import qrcode
from datetime import datetime, timedelta
from config import PAYMENT_CONFIG, PATHS
from notifications import NotificationService

class PaymentService:
    @staticmethod
    def generate_payment_reference(prefix='PAY'):
        """Génère une référence de paiement unique"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}-{timestamp}"

    @staticmethod
    def generate_qr_code(data, filename=None):
        """Génère un QR code à partir des données fournies"""
        if not filename:
            filename = f"qr_{int(datetime.now().timestamp())}.png"
        
        qr_path = os.path.join(PATHS['qrcodes'], filename)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_path)
        
        return qr_path

    @classmethod
    def process_orange_money_payment(cls, amount, phone_number, description=""):
        """Traite un paiement via Orange Money"""
        config = PAYMENT_CONFIG['orange_money']
        reference = cls.generate_payment_reference('OM')
        
        # URL et données pour l'API Orange Money
        url = "https://api.orange.com/orange-money-webpay/dev/v1/webpayment"
        
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "merchant_key": config['merchant_code'],
            "currency": "XOF",
            "order_id": reference,
            "amount": amount,
            "return_url": config['callback_url'],
            "cancel_url": config['callback_url'],
            "notif_url": config['callback_url'],
            "lang": "fr",
            "reference": description
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            payment_data = response.json()
            
            # Générer le QR code pour le paiement
            qr_data = f"om://send?amount={amount}&tel={config['phone_number']}&reference={reference}"
            qr_path = cls.generate_qr_code(qr_data, f"orange_money_{reference}.png")
            
            return {
                'success': True,
                'reference': reference,
                'payment_url': payment_data.get('payment_url'),
                'qr_code': qr_path,
                'method': 'orange_money'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'orange_money'
            }

    @classmethod
    def process_wave_payment(cls, amount, phone_number, description=""):
        """Traite un paiement via Wave"""
        config = PAYMENT_CONFIG['wave']
        reference = cls.generate_payment_reference('WV')
        
        # URL et données pour l'API Wave
        url = "https://api.wave.com/v1/checkout/sessions"
        
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "amount": amount,
            "currency": "XOF",
            "error_url": config['callback_url'],
            "success_url": config['callback_url'],
            "client_reference": reference,
            "business_name": "ISBISPORTCLUB",
            "business_logo": "https://isbisportclub.com/logo.png"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            payment_data = response.json()
            
            # Générer le QR code pour le paiement
            qr_data = f"wave://pay?amount={amount}&business_id={config['business_id']}&reference={reference}"
            qr_path = cls.generate_qr_code(qr_data, f"wave_{reference}.png")
            
            return {
                'success': True,
                'reference': reference,
                'payment_url': payment_data.get('checkout_url'),
                'qr_code': qr_path,
                'method': 'wave'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'wave'
            }

    @classmethod
    def process_cash_payment(cls, amount, description=""):
        """Traite un paiement en espèces"""
        reference = cls.generate_payment_reference('CSH')
        
        return {
            'success': True,
            'reference': reference,
            'method': 'cash',
            'instructions': 'Veuvez-vous présenter à la réception pour effectuer le paiement en espèces.'
        }

    @classmethod
    def process_payment(cls, amount, payment_method, customer_info, description=""):
        """
        Traite un paiement en fonction de la méthode choisie
        
        Args:
            amount (float): Montant à payer
            payment_method (str): Méthode de paiement ('orange_money', 'wave', 'cash')
            customer_info (dict): Informations du client
            description (str): Description du paiement
            
        Returns:
            dict: Résultat du paiement
        """
        payment_method = payment_method.lower()
        
        if payment_method == 'orange_money':
            result = cls.process_orange_money_payment(
                amount=amount,
                phone_number=customer_info.get('phone'),
                description=description
            )
        elif payment_method == 'wave':
            result = cls.process_wave_payment(
                amount=amount,
                phone_number=customer_info.get('phone'),
                description=description
            )
        elif payment_method == 'cash':
            result = cls.process_cash_payment(
                amount=amount,
                description=description
            )
        else:
            return {
                'success': False,
                'error': 'Méthode de paiement non supportée',
                'method': payment_method
            }
        
        # Si le paiement est réussi, envoyer une notification
        if result.get('success'):
            payment_data = {
                'reference': result['reference'],
                'amount': amount,
                'currency': 'XOF',
                'method': payment_method,
                'date': datetime.now().isoformat(),
                'status': 'completed' if payment_method == 'cash' else 'pending',
                'description': description
            }
            
            # Envoyer la confirmation de paiement
            NotificationService.send_payment_confirmation(
                payment_data=payment_data,
                member_data=customer_info,
                qr_code_path=result.get('qr_code')
            )
        
        return result

    @classmethod
    def get_payment_status(cls, reference, method):
        """Vérifie le statut d'un paiement"""
        # Implémentez la logique pour vérifier le statut d'un paiement
        # Cette méthode dépendra de l'API de paiement utilisée
        pass
