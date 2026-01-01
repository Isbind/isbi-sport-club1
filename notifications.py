import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from config import EMAIL_CONFIG, PATHS, NOTIFICATION_CONFIG, APP_CONFIG

# Configuration de l'environnement Jinja2 pour les templates
env = Environment(loader=FileSystemLoader(PATHS['templates']))

class NotificationService:
    @staticmethod
    def send_email(recipient_email, template_name, context=None, subject=None, attachments=None):
        """
        Envoie un email basé sur un template
        
        Args:
            recipient_email (str): Adresse email du destinataire
            template_name (str): Nom du template à utiliser
            context (dict): Données à passer au template
            subject (str, optional): Sujet de l'email
            attachments (list, optional): Liste des chemins des fichiers à joindre
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if context is None:
            context = {}
            
        # Ajout des configurations au contexte
        context.update({
            'site_name': APP_CONFIG['site_name'],
            'support_email': EMAIL_CONFIG['support_email'],
            'current_year': datetime.now().year
        })
        
        # Chargement du template
        try:
            template = env.get_template(template_name)
            html_content = template.render(**context)
        except Exception as e:
            print(f"Erreur lors du chargement du template {template_name}: {str(e)}")
            return False
        
        # Création du message
        msg = MIMEMultipart('related')
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject or NOTIFICATION_CONFIG.get(template_name, {}).get('subject', 'Notification')
        
        # Ajout du contenu HTML
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Gestion des pièces jointes
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    with open(attachment, 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-ID', f'<{os.path.basename(attachment)}>')
                        msg.attach(img)
        
        # Envoi de l'email
        try:
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email à {recipient_email}: {str(e)}")
            return False
    
    @classmethod
    def send_new_member_notification(cls, member_data):
        """Envoie une notification pour un nouvel adhérent"""
        return cls.send_email(
            recipient_email=EMAIL_CONFIG['email'],
            template_name='emails/new_member.html',
            context={'member': member_data},
            subject=f"Nouvel adhérent : {member_data.get('first_name', '')} {member_data.get('last_name', '')}"
        )
    
    @classmethod
    def send_payment_confirmation(cls, payment_data, member_data, qr_code_path=None):
        """Envoie une confirmation de paiement"""
        attachments = [qr_code_path] if qr_code_path and os.path.exists(qr_code_path) else None
        
        return cls.send_email(
            recipient_email=member_data.get('email'),
            template_name='emails/payment_received.html',
            context={
                'member': member_data,
                'payment': payment_data,
                'support_phone': '+221 76 455 44 34'
            },
            subject=f"Confirmation de paiement - {payment_data.get('reference', '')}",
            attachments=attachments
        )
    
    @classmethod
    def send_subscription_reminder(cls, member_data, subscription_data, renew_url, unsubscribe_url):
        """Envoie un rappel de renouvellement d'abonnement"""
        return cls.send_email(
            recipient_email=member_data.get('email'),
            template_name='emails/subscription_reminder.html',
            context={
                'member': member_data,
                'subscription': subscription_data,
                'renew_url': renew_url,
                'unsubscribe_url': unsubscribe_url,
                'support_phone': '+221 76 455 44 34'
            },
            subject=f"Rappel : Votre abonnement se termine bientôt"
        )
