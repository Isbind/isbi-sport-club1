import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# Chemins des dossiers
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
TEMPLATES_DIR = BASE_DIR / 'templates'
QRCODES_DIR = BASE_DIR / 'static' / 'qrcodes'

# Créer les dossiers s'ils n'existent pas
for directory in [DATA_DIR, TEMPLATES_DIR, QRCODES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuration de l'application
APP_CONFIG = {
    'site_name': 'ISBISPORTCLUB',
    'admin_username': os.getenv('ADMIN_USERNAME', 'admin'),
    'admin_password': os.getenv('ADMIN_PASSWORD', 'admin123'),
    'db_url': os.getenv('DB_URL', 'sqlite:///isbisport.db'),
    'timezone': 'Africa/Dakar',
    'currency': 'XOF',
    'date_format': '%d/%m/%Y',
    'datetime_format': '%d/%m/%Y %H:%M',
    'support_phone': '+221764554434',
    'support_email': 'isbisportclub@gmail.com'
}

# Configuration email
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('ADMIN_EMAIL', 'isbisportclub@gmail.com'),
    'password': os.getenv('ADMIN_EMAIL_PASSWORD', ''),  # Mot de passe d'application Gmail
    'from_name': 'ISBISPORTCLUB',
    'reply_to': os.getenv('REPLY_TO_EMAIL', 'isbisportclub@gmail.com'),
    'support_email': os.getenv('SUPPORT_EMAIL', 'isbisportclub@gmail.com'),
    'use_tls': True
}

# Configuration des paiements
PAYMENT_CONFIG = {
    'orange_money': {
        'api_key': os.getenv('ORANGE_MONEY_API_KEY', ''),
        'merchant_code': os.getenv('ORANGE_MONEY_MERCHANT_CODE', ''),
        'merchant_key': os.getenv('ORANGE_MONEY_MERCHANT_KEY', ''),
        'phone_number': os.getenv('ORANGE_MONEY_PHONE', '221764554434'),
        'callback_url': os.getenv('ORANGE_MONEY_CALLBACK_URL', 'https://votresite.com/callback/orange-money')
    },
    'wave': {
        'api_key': os.getenv('WAVE_API_KEY', ''),
        'business_id': os.getenv('WAVE_BUSINESS_ID', ''),
        'callback_url': os.getenv('WAVE_CALLBACK_URL', 'https://votresite.com/callback/wave')
    },
    'cash': {
        'enabled': True,
        'instructions': 'Veuvez-vous présenter à la réception pour effectuer le paiement en espèces.'
    }
}

# Configuration des notifications
NOTIFICATION_CONFIG = {
    'new_member': {
        'subject': 'Nouvel adhérent enregistré',
        'template': 'emails/new_member.html',
        'enabled': True,
        'recipients': ['admin'],  # admin, member, both
        'tags': ['account', 'registration']
    },
    'payment_received': {
        'subject': 'Confirmation de paiement - {reference}',
        'template': 'emails/payment_received.html',
        'enabled': True,
        'recipients': ['member', 'admin'],
        'tags': ['payment', 'receipt']
    },
    'subscription_reminder': {
        'subject': 'Rappel : Votre abonnement se termine bientôt',
        'template': 'emails/subscription_reminder.html',
        'enabled': True,
        'days_before': [7, 3, 1],  # Jours avant l'expiration pour envoyer les rappels
        'recipients': ['member'],
        'tags': ['subscription', 'reminder']
    },
    'payment_reminder': {
        'subject': 'Paiement en attente - Rappel',
        'template': 'emails/payment_reminder.html',
        'enabled': True,
        'recipients': ['member'],
        'tags': ['payment', 'reminder']
    },
    'welcome': {
        'subject': 'Bienvenue chez ISBISPORTCLUB',
        'template': 'emails/welcome.html',
        'enabled': True,
        'recipients': ['member'],
        'tags': ['account', 'welcome']
    },
    'monthly_report': {
        'subject': 'Votre rapport mensuel ISBISPORTCLUB',
        'template': 'emails/monthly_report.html',
        'enabled': True,
        'schedule': '0 9 1 * *',  # Le 1er de chaque mois à 9h
        'recipients': ['member'],
        'tags': ['report', 'monthly']
    }
}

# Chemins des dossiers
PATHS = {
    'templates': os.path.join(os.path.dirname(__file__), 'templates'),
    'static': os.path.join(os.path.dirname(__file__), 'static'),
    'qrcodes': os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')
}

# Créer les dossiers nécessaires s'ils n'existent pas
os.makedirs(PATHS['qrcodes'], exist_ok=True)

# Configuration des types d'abonnement
SUBSCRIPTION_TYPES = [
    {
        'name': 'Mensuel (15,000 XOF)',
        'price': 15000,
        'duration_days': 30,
        'type': 'mensuel',
        'description': 'Accès illimité à la salle pendant 1 mois',
        'features': [
            'Accès 7j/7 de 6h à 23h',
            'Espace musculation et cardio',
            'Douches et vestiaires',
            '1 séance avec un coach offerte'
        ]
    },
    {
        'name': 'Mensuel (20,000 XOF)',
        'price': 20000,
        'duration_days': 30,
        'type': 'mensuel_premium',
        'description': 'Formule premium avec avantages exclusifs',
        'features': [
            'Tous les avantages du forfait mensuel',
            'Accès illimité aux cours collectifs',
            '2 séances avec un coach personnel',
            '1 analyse corporelle offerte'
        ]
    },
    {
        'name': 'Trimestriel (40,000 XOF)',
        'price': 40000,
        'duration_days': 90,
        'type': 'trimestriel',
        'description': 'Économisez avec un engagement de 3 mois',
        'features': [
            'Tous les avantages du forfait mensuel',
            'Économisez 11% par rapport au mensuel',
            '1 mois offert pour 3 mois payés',
            'Accès prioritaire aux nouveaux équipements'
        ]
    },
    {
        'name': 'Annuel (120,000 XOF)',
        'price': 120000,
        'duration_days': 365,
        'type': 'annuel',
        'description': 'La meilleure offre pour une année de sport',
        'features': [
            'Tous les avantages du forfait trimestriel',
            'Économisez 33% par rapport au mensuel',
            '3 mois offerts pour 12 mois payés',
            'Accès illimité à tous les cours',
            '1 mois d\'abonnement offert à un proche'
        ]
    },
    {
        'name': 'Séance unique (1,000 XOF)',
        'price': 1000,
        'duration_days': 1,
        'type': 'seance',
        'description': 'Pour essayer la salle sans engagement',
        'features': [
            'Accès à la salle pour une journée',
            'Espace musculation et cardio',
            'Utilisation des vestiaires et douches',
            'Accompagnement découverte offert'
        ]
    },
    {
        'name': 'Séance unique (2,000 XOF)',
        'price': 2000,
        'duration_days': 1,
        'type': 'seance_premium',
        'description': 'Séance découverte premium',
        'features': [
            'Tous les avantages de la séance simple',
            '1 séance de coaching personnalisée',
            'Bilan forme offert',
            'Boisson énergisante offerte'
        ]
    }
]

# Configuration des statuts
STATUS_CHOICES = [
    ('actif', 'Actif'),
    ('inactif', 'Inactif'),
    ('en_attente', 'En attente'),
    ('suspendu', 'Suspendu'),
    ('banni', 'Banni'),
    ('essai', 'Période d\'essai')
]

# Configuration des méthodes de paiement
PAYMENT_METHODS = [
    ('orange_money', 'Orange Money'),
    ('wave', 'Wave'),
    ('cash', 'Espèces'),
    ('cheque', 'Chèque'),
    ('virement', 'Virement bancaire'),
    ('carte', 'Carte bancaire')
]

# Configuration des statuts de paiement
PAYMENT_STATUS_CHOICES = [
    ('en_attente', 'En attente'),
    ('paye', 'Payé'),
    ('echec', 'Échec'),
    ('rembourse', 'Remboursé'),
    ('annule', 'Annulé'),
    ('en_controle', 'En contrôle')
]

# Configuration des rôles utilisateurs
USER_ROLES = [
    ('admin', 'Administrateur'),
    ('staff', 'Personnel'),
    ('member', 'Membre'),
    ('coach', 'Coach'),
    ('guest', 'Invité')
]

# Configuration des jours de la semaine
WEEKDAYS = [
    (0, 'Lundi'),
    (1, 'Mardi'),
    (2, 'Mercredi'),
    (3, 'Jeudi'),
    (4, 'Vendredi'),
    (5, 'Samedi'),
    (6, 'Dimanche')
]

# Configuration des créneaux horaires
TIME_SLOTS = [
    ('06:00', '06:00 - 07:00'),
    ('07:00', '07:00 - 08:00'),
    ('08:00', '08:00 - 09:00'),
    ('09:00', '09:00 - 10:00'),
    ('10:00', '10:00 - 11:00'),
    ('11:00', '11:00 - 12:00'),
    ('12:00', '12:00 - 13:00'),
    ('13:00', '13:00 - 14:00'),
    ('14:00', '14:00 - 15:00'),
    ('15:00', '15:00 - 16:00'),
    ('16:00', '16:00 - 17:00'),
    ('17:00', '17:00 - 18:00'),
    ('18:00', '18:00 - 19:00'),
    ('19:00', '19:00 - 20:00'),
    ('20:00', '20:00 - 21:00'),
    ('21:00', '21:00 - 22:00'),
    ('22:00', '22:00 - 23:00')
]
