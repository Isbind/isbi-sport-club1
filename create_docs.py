import os
import shutil
from datetime import datetime

def create_text_documentation():
    """Crée une documentation au format texte"""
    # Créer le dossier de sortie
    os.makedirs('ISBISPORTCLUB_Documentation', exist_ok=True)
    
    # Chemin des fichiers
    output_file = 'ISBISPORTCLUB_Documentation/Guide_Utilisation_ISBISPORTCLUB.txt'
    
    # Contenu du fichier
    content = """
    ==================================================
    GUIDE D'UTILISATION - ISBISPORTCLUB
    ==================================================
    
    Date de génération: {}
    
    TABLE DES MATIÈRES
    =================
    1. Vue d'ensemble
    2. Installation
    3. Onglet Membres
    4. Onglet Abonnements
    5. Onglet Paiements
    6. Onglet Présences
    7. Tableau de Bord
    8. Conseils d'Utilisation
    9. Maintenance
    
    =================
    1. VUE D'ENSEMBLE
    =================
    Ce document fournit un guide complet pour l'utilisation du système de gestion ISBISPORTCLUB.
    
    =============
    2. INSTALLATION
    =============
    - Assurez-vous d'avoir Microsoft Excel installé
    - Ouvrez le fichier ISBISPORTCLUB_Suivi.xlsx
    - Activez les macros si nécessaire
    
    =================
    3. ONGLET MEMBRES
    =================
    - ID: Numéro unique d'identification
    - Nom/Prénom: Informations personnelles
    - Date d'inscription: Remplie automatiquement
    - Statut: Actif/Inactif/En attente
    
    =====================
    4. ONGLET ABONNEMENTS
    =====================
    - Type: Mensuel/Trimestriel/Annuel
    - Date début: Date de début de l'abonnement
    - Date fin: Calculée automatiquement
    - Statut: Actif/Expiré/Résilié
    
    ===================
    5. ONGLET PAIEMENTS
    ===================
    - Date: Date du paiement
    - Montant: Montant payé
    - Méthode: Espèces/Carte/Chèque
    - Statut: Payé/En attente/Annulé
    
    ===================
    6. ONGLET PRÉSENCES
    ===================
    - Date: Date de la séance
    - Heure: Heure d'arrivée/départ
    - Durée: Calculée automatiquement
    - Activité: Type de cours/séance
    
    =====================
    7. TABLEAU DE BORD
    =====================
    - Nombre de membres actifs
    - Revenus mensuels
    - Taux de fréquentation
    - Prochains renouvellements
    
    ==========================
    8. CONSEILS D'UTILISATION
    ==========================
    - Sauvegardez régulièrement vos données
    - Mettez à jour les statuts des abonnements
    - Utilisez les filtres pour faciliter la recherche
    
    ==============
    9. MAINTENANCE
    ==============
    - Vérifiez régulièrement les mises à jour
    - Faites des sauvegardes régulières
    - Contactez le support en cas de problème
    
    ====================
    CONTACT SUPPORT
    ====================
    Email: support@isbisportclub.com
    Téléphone: +33 X XX XX XX XX
    
    © {} ISBISPORTCLUB - Tous droits réservés
    """.format(datetime.now().strftime("%d/%m/%Y"), datetime.now().year)
    
    # Écrire le fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Documentation générée : {output_file}")
    
    # Créer une copie du fichier Excel s'il existe
    excel_source = 'ISBISPORTCLUB_Suivi.xlsx'
    if os.path.exists(excel_source):
        shutil.copy2(excel_source, 'ISBISPORTCLUB_Documentation/')
        print(f"Fichier Excel copié dans le dossier de documentation")
    
    # Créer une archive ZIP
    shutil.make_archive('ISBISPORTCLUB_Documentation', 'zip', 'ISBISPORTCLUB_Documentation')
    print("Archive ZIP créée : ISBISPORTCLUB_Documentation.zip")

if __name__ == "__main__":
    create_text_documentation()
