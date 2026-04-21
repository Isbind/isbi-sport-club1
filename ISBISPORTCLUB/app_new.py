import streamlit as st
from datetime import datetime, timedelta
import os
import uuid
import json
import pandas as pd
import numpy as np
import io
import sqlite3
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
from webhook_wave import creer_session_paiement_wave, afficher_notifications

# Constantes
TYPES_ABONNEMENT = [
    "Mensuel (15,000 XOF)",
    "Mensuel (20,000 XOF)",
    "Trimestriel (40,000 XOF)",
    "Annuel (120,000 XOF)",
    "Séance unique (1,000 XOF)",
    "Séance unique (2,000 XOF)"
]

STATUTS = ["Actif", "Inactif", "En attente"]

METHODES_PAIEMENT = ["Espèces", "Orange Money", "Wave", "Virement bancaire"]

# Configuration de la page - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="ISBISPORTCLUB - Gestion",
    page_icon="🏋️",
    layout="wide"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
        .main { background-color: #ffffff; }
        h1 { 
            color: #1a4d2e;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 10px;
        }
        .stButton>button {
            background-color: #4a9d5e;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            border: none;
        }
        [data-testid="stSidebar"] {
            background-color: #1a4d2e;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Fonctions de base de données
def init_db():
    """Initialise la base de données et retourne une connexion"""
    conn = sqlite3.connect('isbisport.db')
    c = conn.cursor()
    
    # Table des adhérents
    c.execute('''
        CREATE TABLE IF NOT EXISTS adherents (
            id TEXT PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            telephone TEXT NOT NULL,
            email TEXT,
            statut TEXT NOT NULL,
            type_abonnement TEXT NOT NULL,
            date_inscription DATE NOT NULL,
            date_fin_abonnement DATE NOT NULL,
            methode_paiement TEXT NOT NULL,
            statut_paiement TEXT NOT NULL,
            montant_paye FLOAT DEFAULT 0,
            date_dernier_paiement DATE,
            commentaires TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_maj TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Vérification et ajout des colonnes manquantes si nécessaire
    c.execute("PRAGMA table_info(adherents)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'montant_paye' not in columns:
        c.execute('ALTER TABLE adherents ADD COLUMN montant_paye FLOAT DEFAULT 0')
    if 'date_dernier_paiement' not in columns:
        c.execute('ALTER TABLE adherents ADD COLUMN date_dernier_paiement DATE')
    if 'commentaires' not in columns:
        c.execute('ALTER TABLE adherents ADD COLUMN commentaires TEXT')
    
    # Table des séances
    c.execute('''
        CREATE TABLE IF NOT EXISTS seances (
            id TEXT PRIMARY KEY,
            jour_semaine TEXT NOT NULL,
            type_seance TEXT NOT NULL,
            heure_debut TEXT NOT NULL,
            heure_fin TEXT NOT NULL,
            capacite_max INTEGER NOT NULL,
            coach TEXT,
            description TEXT,
            statut TEXT DEFAULT 'active',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des inscriptions
    c.execute('''
        CREATE TABLE IF NOT EXISTS inscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adherent_id TEXT NOT NULL,
            seance_id INTEGER NOT NULL,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'confirmée',
            FOREIGN KEY (adherent_id) REFERENCES adherents (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    # Table des paiements
    c.execute('''
        CREATE TABLE IF NOT EXISTS paiements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adherent_id TEXT NOT NULL,
            montant DECIMAL(10, 2) NOT NULL,
            date_paiement DATE NOT NULL,
            methode_paiement TEXT NOT NULL,
            reference TEXT,
            statut TEXT DEFAULT 'en_attente',
            type_paiement TEXT NOT NULL,  -- 'abonnement', 'seance', 'autre'
            details TEXT,
            facture_generee BOOLEAN DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (adherent_id) REFERENCES adherents (id)
        )
    ''')
    
    # Table des réservations
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adherent_id TEXT NOT NULL,
            seance_id INTEGER NOT NULL,
            date_reservation DATE NOT NULL,
            statut TEXT DEFAULT 'confirmée',  -- confirmée, annulée, terminée
            notification_envoyee BOOLEAN DEFAULT 0,
            rappel_envoye BOOLEAN DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (adherent_id) REFERENCES adherents (id),
            FOREIGN KEY (seance_id) REFERENCES seances (id)
        )
    ''')
    
    conn.commit()
    return conn

def get_adherents(conn, filtre_nom="", filtre_statut="", filtre_abonnement=""):
    """Récupère les adhérents avec filtres optionnels"""
    query = """
        SELECT 
            id, nom, prenom, telephone, email, statut,
            type_abonnement, date_inscription, date_fin_abonnement,
            methode_paiement, statut_paiement, montant_paye,
            date_dernier_paiement, commentaires
        FROM adherents
        WHERE 1=1
    """
    params = []
    
    if filtre_nom:
        query += " AND (nom LIKE ? OR prenom LIKE ?)"
        params.extend([f"%{filtre_nom}%", f"%{filtre_nom}%"])
    
    if filtre_statut:
        query += " AND statut = ?"
        params.append(filtre_statut)
        
    if filtre_abonnement:
        query += " AND type_abonnement LIKE ?"
        params.append(f"%{filtre_abonnement}%")
    
    query += " ORDER BY nom, prenom"
    
    return pd.read_sql_query(query, conn, params=params if params else None)

def ajouter_adherent(conn, adherent):
    """Ajoute un nouvel adhérent à la base de données"""
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO adherents (
                id, nom, prenom, telephone, email, statut,
                type_abonnement, date_inscription, date_fin_abonnement,
                methode_paiement, statut_paiement, montant_paye,
                date_dernier_paiement, commentaires
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adherent['id'],
            adherent['nom'].upper(),
            adherent['prenom'].capitalize(),
            adherent['telephone'],
            adherent.get('email', ''),
            adherent.get('statut', 'Actif'),
            adherent['type_abonnement'],
            adherent['date_inscription'],
            adherent['date_fin_abonnement'],
            adherent.get('methode_paiement', 'Espèces'),
            adherent.get('statut_paiement', 'Payé'),
            adherent.get('montant_paye', 0),
            adherent.get('date_dernier_paiement', None),
            adherent.get('commentaires', '')
        ))
        conn.commit()
        return True, "Adhérent ajouté avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de l'ajout de l'adhérent : {str(e)}"

def mettre_a_jour_adherent(conn, adherent_id, updates):
    """Met à jour les informations d'un adhérent"""
    if not updates:
        return True, "Aucune mise à jour nécessaire"
    
    c = conn.cursor()
    try:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        updates['date_maj'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        params = list(updates.values())
        params.append(adherent_id)
        
        c.execute(f"""
            UPDATE adherents 
            SET {set_clause}, date_maj = ?
            WHERE id = ?
        """, params)
        
        conn.commit()
        return True, "Adhérent mis à jour avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la mise à jour : {str(e)}"

def supprimer_adherent(conn, adherent_id):
    """Supprime un adhérent de la base de données"""
    c = conn.cursor()
    try:
        # Vérifier si l'adhérent a des inscriptions
        c.execute("SELECT COUNT(*) FROM inscriptions WHERE adherent_id = ?", (adherent_id,))
        if c.fetchone()[0] > 0:
            return False, "Impossible de supprimer : l'adhérent a des inscriptions en cours."
            
        c.execute("DELETE FROM adherents WHERE id = ?", (adherent_id,))
        conn.commit()
        return True, "Adhérent supprimé avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la suppression : {str(e)}"

def init_seances_par_defaut(conn):
    """Initialise les séances par défaut si elles n'existent pas"""
    c = conn.cursor()
    
    # Vérifier s'il y a déjà des séances
    c.execute("SELECT COUNT(*) FROM seances")
    if c.fetchone()[0] > 0:
        return 0  # Des séances existent déjà
    
    # Définition des séances par défaut
    seances_par_defaut = [
        {
            'jour_semaine': 'Lundi',
            'type_seance': 'AEROMIX',
            'heure_debut': '20:00',
            'heure_fin': '21:00',
            'capacite_max': 20,
            'coach': 'Ndiaye',
            'description': 'Séance de remise en forme complète avec des mouvements aérobiques dynamiques.'
        },
        {
            'jour_semaine': 'Mardi',
            'type_seance': 'STEP',
            'heure_debut': '20:00',
            'heure_fin': '21:00',
            'capacite_max': 15,
            'coach': 'Ndiaye',
            'description': 'Cours de step pour travailler le cardio et la coordination.'
        },
        {
            'jour_semaine': 'Mercredi',
            'type_seance': 'GYM AVEC BATTONS',
            'heure_debut': '20:00',
            'heure_fin': '21:00',
            'capacite_max': 20,
            'coach': 'Ndiaye',
            'description': 'Renforcement musculaire avec des bâtons pour une meilleure posture et tonification.'
        },
        {
            'jour_semaine': 'Jeudi',
            'type_seance': 'GYM ALTER AVEC BODY ATTACK',
            'heure_debut': '20:00',
            'heure_fin': '21:30',
            'capacite_max': 25,
            'coach': 'Ndiaye',
            'description': 'Séance intensive combinant renforcement musculaire et exercices cardiovasculaires.'
        },
        {
            'jour_semaine': 'Vendredi',
            'type_seance': 'BODY COMBAT',
            'heure_debut': '20:00',
            'heure_fin': '21:30',
            'capacite_max': 20,
            'coach': 'Ndiaye',
            'description': 'Cours inspiré des arts martiaux pour se défouler et se dépenser.'
        }
    ]
    
    # Ajouter les séances à la base de données
    for seance in seances_par_defaut:
        c.execute('''
            INSERT INTO seances (id, jour_semaine, type_seance, heure_debut, heure_fin, 
                              capacite_max, coach, description, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ''', (
            str(uuid.uuid4()),
            seance['jour_semaine'],
            seance['type_seance'],
            seance['heure_debut'],
            seance['heure_fin'],
            seance['capacite_max'],
            seance['coach'],
            seance['description']
        ))
    
    conn.commit()
    return len(seances_par_defaut)

def get_seances(conn, jour_semaine=None):
    """Récupère les séances, éventuellement filtrées par jour"""
    query = '''
        SELECT s.*, 
               (SELECT COUNT(*) FROM inscriptions i WHERE i.seance_id = s.id) as nb_inscrits,
               (s.capacite_max - (SELECT COUNT(*) FROM inscriptions i WHERE i.seance_id = s.id)) as places_restantes
        FROM seances s
        WHERE s.statut = 'active'
    '''
    params = ()
    
    if jour_semaine:
        query += " AND s.jour_semaine = ?"
        params = (jour_semaine,)
    
    query += """
        ORDER BY
            CASE s.jour_semaine
                WHEN 'Lundi' THEN 1
                WHEN 'Mardi' THEN 2
                WHEN 'Mercredi' THEN 3
                WHEN 'Jeudi' THEN 4
                WHEN 'Vendredi' THEN 5
                WHEN 'Samedi' THEN 6
                WHEN 'Dimanche' THEN 7
            END,
            s.heure_debut
    """.strip()
    
    return pd.read_sql_query(query, conn, params=params)

def get_adherents(conn, filtre_nom="", filtre_statut="", filtre_abonnement=""):
    """Récupère les adhérents avec filtres optionnels"""
    query = """
        SELECT 
            id, nom, prenom, telephone, email, statut,
            type_abonnement, date_inscription, date_fin_abonnement,
            methode_paiement, statut_paiement, montant_paye,
            date_dernier_paiement, commentaires
        FROM adherents
        WHERE 1=1
    """
    params = []
    
    if filtre_nom:
        query += " AND (nom LIKE ? OR prenom LIKE ?)"
        params.extend([f"%{filtre_nom}%", f"%{filtre_nom}%"])
        
    if filtre_statut:
        query += " AND statut = ?"
        params.append(filtre_statut)
        
    if filtre_abonnement:
        query += " AND type_abonnement LIKE ?"
        params.append(f"%{filtre_abonnement}%")
    
    query += " ORDER BY nom, prenom"
    
    return pd.read_sql_query(query, conn, params=params if params else None)

def ajouter_adherent(conn, adherent):
    """Ajoute un nouvel adhérent à la base de données"""
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO adherents (
                id, nom, prenom, telephone, email, statut,
                type_abonnement, date_inscription, date_fin_abonnement,
                methode_paiement, statut_paiement
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            adherent['id'],
            adherent['nom'].upper(),
            adherent['prenom'].capitalize(),
            adherent['telephone'],
            adherent.get('email', ''),
            adherent.get('statut', 'Actif'),
            adherent['type_abonnement'],
            adherent['date_inscription'],
            adherent['date_fin_abonnement'],
            adherent.get('methode_paiement', 'Espèces'),
            adherent.get('statut_paiement', 'Payé')
        ))
        conn.commit()
        return True, "Adhérent ajouté avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de l'ajout de l'adhérent : {str(e)}"

def mettre_a_jour_adherent(conn, adherent_id, updates):
    """Met à jour les informations d'un adhérent"""
    if not updates:
        return True, "Aucune mise à jour nécessaire"
    
    c = conn.cursor()
    try:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        params = list(updates.values())
        params.append(adherent_id)
        
        c.execute(f"""
            UPDATE adherents 
            SET {set_clause}
            WHERE id = ?
        """, params)
        
        conn.commit()
        return True, "Adhérent mis à jour avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la mise à jour : {str(e)}"

def supprimer_adherent(conn, adherent_id):
    """Supprime un adhérent de la base de données"""
    c = conn.cursor()
    try:
        c.execute("DELETE FROM adherents WHERE id = ?", (adherent_id,))
        conn.commit()
        return True, "Adhérent supprimé avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la suppression : {str(e)}"

def afficher_onglet_adherents(conn):
    st.header("👥 Gestion des adhérents")
    
    # Création des onglets
    tab1, tab2, tab3 = st.tabs(["📋 Liste des adhérents", "➕ Ajouter un adhérent", "📤 Importer des adhérents"])
    
    with tab1:
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            filtre_nom = st.text_input("Rechercher par nom ou prénom", "")
        with col2:
            filtre_statut = st.selectbox("Filtrer par statut", [""] + STATUTS)
        with col3:
            filtre_abonnement = st.selectbox(
                "Filtrer par type d'abonnement",
                [""] + TYPES_ABONNEMENT
            )
        
        # Bouton pour réinitialiser les filtres
        if st.button("Réinitialiser les filtres"):
            filtre_nom = ""
            filtre_statut = ""
            filtre_abonnement = ""
            st.rerun()
        
        # Récupération des adhérents avec filtres
        df_adherents = get_adherents(conn, filtre_nom, filtre_statut, filtre_abonnement)
        
        # Affichage du tableau des adhérents
        if not df_adherents.empty:
            # Formatage des colonnes
            df_display = df_adherents.copy()
            df_display['date_inscription'] = pd.to_datetime(df_display['date_inscription']).dt.strftime('%d/%m/%Y')
            df_display['date_fin_abonnement'] = pd.to_datetime(df_display['date_fin_abonnement']).dt.strftime('%d/%m/%Y')
            
            # Afficher le tableau avec des colonnes sélectionnées
            st.dataframe(
                df_display[['nom', 'prenom', 'telephone', 'email', 'statut', 'type_abonnement', 'date_fin_abonnement']],
                column_config={
                    "nom": "Nom",
                    "prenom": "Prénom",
                    "telephone": "Téléphone",
                    "email": "Email",
                    "statut": "Statut",
                    "type_abonnement": "Type d'abonnement",
                    "date_fin_abonnement": "Fin d'abonnement"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Statistiques rapides
            st.subheader("📊 Statistiques")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total adhérents", len(df_adherents))
            with col2:
                st.metric("Actifs", len(df_adherents[df_adherents['statut'] == 'Actif']))
            with col3:
                st.metric("Abonnements expirant ce mois", 
                         len(df_adherents[pd.to_datetime(df_adherents['date_fin_abonnement']).dt.month == pd.Timestamp.now().month]))
        else:
            st.info("Aucun adhérent trouvé avec ces critères.")
    
    with tab2:
        st.subheader("Nouvel adhérent")
        st.markdown("---")
        
        with st.form("form_adherent", clear_on_submit=True):
            # Section d'information
            st.markdown("### Informations personnelles")
            
            # Première ligne
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom *", key="nom_input", placeholder="Entrez le nom")
                prenom = st.text_input("Prénom *", key="prenom_input", placeholder="Entrez le prénom")
                telephone = st.text_input("Téléphone *", key="tel_input", placeholder="771234567")
            
            with col2:
                email = st.text_input("Email", key="email_input", placeholder="exemple@domaine.com")
                
                statut = st.selectbox(
                    "Statut *",
                    STATUTS,
                    key="statut_select"
                )
                
                type_abonnement = st.selectbox(
                    "Type d'abonnement *",
                    TYPES_ABONNEMENT,
                    key="abonnement_select"
                )
                
                # Calcul du montant et de la date de fin
                date_aujourdhui = datetime.now().date()
                montant = 0
                
                if "Mensuel (15,000 XOF)" in type_abonnement:
                    montant = 15000
                    date_fin = date_aujourdhui + timedelta(days=30)
                elif "Mensuel (20,000 XOF)" in type_abonnement:
                    montant = 20000
                    date_fin = date_aujourdhui + timedelta(days=30)
                elif "Trimestriel" in type_abonnement:
                    montant = 40000
                    date_fin = date_aujourdhui + timedelta(weeks=12)  # 3 mois
                elif "Annuel" in type_abonnement:
                    montant = 120000
                    date_fin = date_aujourdhui + timedelta(weeks=52)  # 1 an
                else:  # Séance unique
                    montant = 1000 if "1,000" in type_abonnement else 2000
                    date_fin = date_aujourdhui
                
                # Affichage du montant et de la date de fin
                st.write(f"<div style='background-color: #f0f8ff; padding: 10px; border-radius: 5px;'>"
                        f"<strong>Montant à payer :</strong> {montant:,} XOF<br>"
                        f"<strong>Date de fin d'abonnement :</strong> {date_fin.strftime('%d/%m/%Y')}"
                        "</div>", 
                        unsafe_allow_html=True)
                
                # Champ caché pour la date de fin
                date_fin_input = st.date_input(
                    "Date de fin d'abonnement *", 
                    value=date_fin,
                    min_value=date_aujourdhui,
                    key="date_input",
                    disabled=False,
                    help="Date de fin automatiquement calculee selon le type d abonnement"
                )
                
                # Section de paiement
                st.markdown("---")
                st.subheader("💳 Paiement")
                
                # Sélection de la méthode de paiement
                methode_paiement = st.radio(
                    "Méthode de paiement *",
                    METHODES_PAIEMENT,
                    horizontal=True,
                    key="methode_paiement_radio"
                )
                
                statut_paiement = st.selectbox(
                    "Statut du paiement *",
                    ["Payé", "En attente", "Annulé"],
                    key="statut_paiement_select"
                )
                
                montant_paye = st.number_input(
                    "Montant payé (XOF) *",
                    min_value=0.0,
                    value=float(montant),
                    step=1000.0,
                    key="montant_paye_input"
                )
                
                commentaires = st.text_area("Commentaires", key="commentaires_area")
            
            # Bouton de soumission
            submitted = st.form_submit_button("Enregistrer l'adhérent")
            
            if submitted:
                # Validation des champs obligatoires
                if not nom or not prenom or not telephone or not type_abonnement:
                    st.error("Veuillez remplir tous les champs obligatoires (*).")
                else:
                    # Si paiement par Wave, créer une session de paiement
                    if methode_paiement == "Wave":
                        client_reference = f"adherent_{uuid.uuid4().hex[:8]}"
                        paiement_result = creer_session_paiement_wave(
                            montant=montant,
                            description=f"Abonnement {type_abonnement} - {nom} {prenom}",
                            client_reference=client_reference
                        )
                        
                        if paiement_result['success']:
                            st.success("🌊 Redirection vers le paiement Wave...")
                            st.markdown(f"""
                            <div style="text-align: center; padding: 20px;">
                                <h3>🌊 Payer avec Wave</h3>
                                <p>Cliquez sur le bouton ci-dessous pour finaliser votre paiement</p>
                                <a href="{paiement_result['payment_url']}" target="_blank">
                                    <button style="background-color: #00D4AA; color: white; padding: 12px 24px; 
                                                   border: none; border-radius: 8px; font-size: 16px; 
                                                   cursor: pointer; text-decoration: none;">
                                        Payer avec Wave 🌊
                                    </button>
                                </a>
                                <p><small>Reference: {client_reference}</small></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Enregistrer l'adhérent avec statut "en attente"
                            nouvel_adherent = {
                                'id': str(uuid.uuid4()),
                                'nom': nom.upper(),
                                'prenom': prenom.capitalize(),
                                'telephone': telephone,
                                'email': email,
                                'statut': 'En attente',
                                'type_abonnement': type_abonnement,
                                'date_inscription': date_aujourdhui.strftime('%Y-%m-%d'),
                                'date_fin_abonnement': date_fin_input.strftime('%Y-%m-%d'),
                                'methode_paiement': methode_paiement,
                                'statut_paiement': 'En attente',
                                'montant_paye': 0,
                                'date_dernier_paiement': None,
                                'commentaires': f"En attente de paiement Wave - Ref: {client_reference}"
                            }
                        else:
                            st.error(f"❌ Erreur lors de la création du paiement Wave: {paiement_result['error']}")
                            return
                    else:
                        # Pour les autres méthodes de paiement
                        nouvel_adherent = {
                            'id': str(uuid.uuid4()),
                            'nom': nom.upper(),
                            'prenom': prenom.capitalize(),
                            'telephone': telephone,
                            'email': email,
                            'statut': statut,
                            'type_abonnement': type_abonnement,
                            'date_inscription': date_aujourdhui.strftime('%Y-%m-%d'),
                            'date_fin_abonnement': date_fin_input.strftime('%Y-%m-%d'),
                            'methode_paiement': methode_paiement,
                            'statut_paiement': statut_paiement,
                            'montant_paye': montant_paye,
                            'date_dernier_paiement': date_aujourdhui.strftime('%Y-%m-%d'),
                        'commentaires': commentaires
                    }
                    
                    # Ajout de l'adhérent
                    success, message = ajouter_adherent(conn, nouvel_adherent)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
    
    with tab3:
        st.subheader("Importer des adhérents")
        st.markdown("---")
        
        st.info("💡 Téléchargez un fichier Excel (.xlsx) contenant la liste des adhérents. "
               "Assurez-vous que le fichier contient les colonnes suivantes : "
               "Nom, Prénom, Téléphone, Email, Type d'abonnement, Statut, Méthode de paiement, Montant payé.")
        
        fichier = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])
        
        if fichier is not None:
            try:
                # Lire le fichier Excel
                df_import = pd.read_excel(fichier)
                
                # Aperçu des données
                st.subheader("Aperçu des données à importer")
                st.dataframe(df_import.head())
                
                # Bouton de confirmation d'importation
                if st.button("Confirmer l'importation"):
                    # Traitement des données et insertion dans la base de données
                    succes = 0
                    echecs = 0
                    
                    for _, row in df_import.iterrows():
                        try:
                            # Conversion des données
                            adherent = {
                                'id': str(uuid.uuid4()),
                                'nom': str(row.get('Nom', '')).strip(),
                                'prenom': str(row.get('Prénom', '')).strip(),
                                'telephone': str(row.get('Téléphone', '')).strip(),
                                'email': str(row.get('Email', '')).strip(),
                                'statut': str(row.get('Statut', 'Actif')).strip(),
                                'type_abonnement': str(row.get("Type d'abonnement", '')).strip(),
                                'date_inscription': datetime.now().strftime('%Y-%m-%d'),
                                'date_fin_abonnement': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),  # Par défaut 1 mois
                                'methode_paiement': str(row.get('Méthode de paiement', 'Espèces')).strip(),
                                'statut_paiement': 'Payé',
                                'montant_paye': float(row.get('Montant payé', 0)),
                                'date_dernier_paiement': datetime.now().strftime('%Y-%m-%d'),
                                'commentaires': 'Importé depuis fichier Excel'
                            }
                            
                            # Validation des champs obligatoires
                            if adherent['nom'] and adherent['prenom'] and adherent['telephone']:
                                ajouter_adherent(conn, adherent)
                                succes += 1
                            else:
                                echecs += 1
                        except Exception as e:
                            echecs += 1
                            continue
                    
                    st.success(f"Importation terminée : {succes} adhérent(s) importé(s) avec succès, {echecs} échec(s).")
                    
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {str(e)}")

def get_seances_par_jour(conn, jour):
    """Récupère les séances pour un jour donné"""
    try:
        return pd.read_sql_query(
            "SELECT * FROM seances WHERE jour_semaine = ? ORDER BY heure_debut", 
            conn, 
            params=(jour,)
        )
    except Exception as e:
        st.error(f"Erreur lors de la récupération des séances : {str(e)}")
        return pd.DataFrame()

def enregistrer_paiement(conn, adherent_id, montant, methode_paiement, type_paiement, reference=None, details=None):
    """Enregistre un nouveau paiement"""
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO paiements (adherent_id, montant, date_paiement, methode_paiement, 
                                 reference, type_paiement, details, statut)
            VALUES (?, ?, DATE('now'), ?, ?, ?, ?, 'completé')
        ''', (adherent_id, montant, methode_paiement, reference, type_paiement, details))
        
        # Mise à jour du statut de paiement de l'adhérent
        c.execute('''
            UPDATE adherents 
            SET statut_paiement = 'à jour',
                date_dernier_paiement = DATE('now'),
                montant_paye = ?,
                date_maj = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (montant, adherent_id))
        
        conn.commit()
        return True, "Paiement enregistré avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de l'enregistrement du paiement : {str(e)}"

def creer_reservation(conn, adherent_id, seance_id, date_reservation):
    """Crée une nouvelle réservation"""
    try:
        # Vérifier les places disponibles
        c = conn.cursor()
        c.execute('SELECT places_restantes, capacite_max FROM seances WHERE id = ?', (seance_id,))
        places = c.fetchone()
        
        if not places or places[0] <= 0:
            return False, "Plus de places disponibles pour cette séance"
        
        # Créer la réservation
        c.execute('''
            INSERT INTO reservations (adherent_id, seance_id, date_reservation, statut)
            VALUES (?, ?, ?, 'confirmée')
        ''', (adherent_id, seance_id, date_reservation))
        
        # Mettre à jour le nombre de places restantes
        c.execute('''
            UPDATE seances 
            SET places_restantes = places_restantes - 1
            WHERE id = ?
        ''', (seance_id,))
        
        conn.commit()
        return True, "Réservation effectuée avec succès"
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la création de la réservation : {str(e)}"

def envoyer_notification(conn, adherent_id, message, type_notification='email'):
    """Envoie une notification à l'adhérent"""
    try:
        # Récupérer les informations de contact de l'adhérent
        adherent = pd.read_sql_query(
            'SELECT email, telephone FROM adherents WHERE id = ?', 
            conn, 
            params=(adherent_id,)
        ).iloc[0]
        
        if type_notification == 'email' and adherent['email']:
            # Logique d'envoi d'email
            print(f"Email envoyé à {adherent['email']}: {message}")
        elif type_notification == 'whatsapp' and adherent['telephone']:
            # Logique d'envoi WhatsApp
            print(f"Message WhatsApp envoyé à {adherent['telephone']}: {message}")
            
        return True, "Notification envoyée avec succès"
    except Exception as e:
        return False, f"Erreur lors de l'envoi de la notification : {str(e)}"

def generer_facture(conn, paiement_id):
    """Génère une facture pour un paiement"""
    try:
        # Récupérer les informations du paiement et de l'adhérent
        facture = pd.read_sql_query('''
            SELECT p.*, a.nom, a.prenom, a.email, a.telephone
            FROM paiements p
            JOIN adherents a ON p.adherent_id = a.id
            WHERE p.id = ?
        ''', conn, params=(paiement_id,)).iloc[0]
        
        # Ici, vous pouvez ajouter la logique pour générer un PDF
        # Par exemple, en utilisant reportlab ou weasyprint
        
        # Mettre à jour le statut de la facture
        c = conn.cursor()
        c.execute('''
            UPDATE paiements 
            SET facture_generee = 1
            WHERE id = ?
        ''', (paiement_id,))
        conn.commit()
        
        return True, f"facture_{paiement_id}.pdf"
    except Exception as e:
        return False, f"Erreur lors de la génération de la facture : {str(e)}"

# Initialisation de la base de données
conn = init_db()

# Initialisation des séances par défaut (si nécessaire)
if 'seances_initialisees' not in st.session_state:
    nb_seances = init_seances_par_defaut(conn)
    if nb_seances > 0:
        st.toast(f"✅ {nb_seances} séances par défaut ont été créées", icon="✅")
    st.session_state.seances_initialisees = True

# Options pour les menus déroulants
TYPES_ABONNEMENT = [
    "Mensuel (15,000 XOF)",
    "Mensuel (20,000 XOF)",
    "Trimestriel (40,000 XOF)",
    "Annuel (120,000 XOF)",
    "Séance unique (1,000 XOF)",
    "Séance unique (2,000 XOF)"
]

STATUTS = ["Actif", "Inactif", "En attente"]
METHODES_PAIEMENT = ["Espèces", "Orange Money", "Wave", "Virement bancaire"]

# Barre latérale avec le menu
with st.sidebar:
    st.title("ISBISPORTCLUB")
    menu_options = ["🏠 Tableau de bord", "👥 Adhérents", "📅 Planning", "💳 Paiements"]
    selected = option_menu(
        menu_title=None,
        options=menu_options,
        icons=None,
        default_index=0
    )

# Contenu principal
if selected == "🏠 Tableau de bord":
    st.title("Tableau de Bord")
    
    # Statistiques
    st.subheader("Statistiques")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Adhérents", len(get_adherents(conn)))
        
    with col2:
        seances_du_jour = get_seances(conn, datetime.now().strftime('%A'))
        st.metric("Séances Aujourd'hui", len(seances_du_jour))
        
    with col3:
        st.metric("Inscriptions du jour", 0)  # À implémenter
    
    # Prochaines séances
    st.subheader("Prochaines séances")
    prochaines_seances = get_seances(conn).head(3)
    if not prochaines_seances.empty:
        for _, seance in prochaines_seances.iterrows():
            with st.container():
                cols = st.columns([1, 3, 1])
                with cols[0]:
                    st.write(f"**{seance['jour_semaine']}**\n{seance['heure_debut']}-{seance['heure_fin']}")
                with cols[1]:
                    st.write(f"**{seance['type_seance']}**")
                    st.caption(seance['description'])
                with cols[2]:
                    st.metric("Places", f"{seance['places_restantes']}/{seance['capacite_max']}")
                st.divider()
    else:
        st.info("Aucune séance à venir")

elif selected == "👥 Adhérents":
    afficher_onglet_adherents(conn)

elif selected == "� Paiements":
    st.title("Gestion des Paiements")
    
    # Création des onglets
    tab_paiements, tab_factures, tab_rapports = st.tabs(["📝 Enregistrer un paiement", "📄 Factures", "📊 Rapports"])
    
    with tab_paiements:
        st.subheader("Nouveau paiement")
        with st.form("form_paiement"):
            # Sélection de l'adhérent
            df_adherents = get_adherents(conn)
            adherents_list = [f"{row['prenom']} {row['nom']} ({row['id']})" for _, row in df_adherents.iterrows()]
            selected_adherent = st.selectbox("Sélectionnez un adhérent", adherents_list)
            
            # Détails du paiement
            col1, col2 = st.columns(2)
            with col1:
                montant = st.number_input("Montant (€)", min_value=0.0, step=0.01, format="%.2f")
                type_paiement = st.selectbox("Type de paiement", ["Abonnement mensuel", "Séance unique", "Autre"])
            with col2:
                methode_paiement = st.selectbox("Méthode de paiement", ["Espèces", "Carte bancaire", "Virement", "Chèque"])
                reference = st.text_input("Référence (optionnel)")
            
            details = st.text_area("Détails supplémentaires (optionnel)")
            
            if st.form_submit_button("Enregistrer le paiement"):
                if selected_adherent and montant > 0:
                    # Extraire l'ID de l'adhérent
                    adherent_id = selected_adherent.split('(')[-1].rstrip(')')
                    
                    # Enregistrer le paiement
                    success, message = enregistrer_paiement(
                        conn, adherent_id, montant, methode_paiement, 
                        type_paiement, reference, details
                    )
                    
                    if success:
                        st.success(message)
                        # Générer la facture
                        facture_success, facture_path = generer_facture(conn, conn.cursor().lastrowid)
                        if facture_success:
                            st.success(f"Facture générée : {facture_path}")
                        # Envoyer une notification
                        envoyer_notification(
                            conn, adherent_id,
                            f"Paiement de {montant}€ enregistré. Merci pour votre confiance !",
                            'email'
                        )
                    else:
                        st.error(message)
    
    with tab_factures:
        st.subheader("Historique des factures")
        # Afficher l'historique des paiements
        df_paiements = pd.read_sql_query('''
            SELECT p.id, a.nom, a.prenom, p.montant, p.date_paiement, 
                   p.methode_paiement, p.type_paiement, p.facture_generee
            FROM paiements p
            JOIN adherents a ON p.adherent_id = a.id
            ORDER BY p.date_paiement DESC
            LIMIT 50
        ''', conn)
        
        if not df_paiements.empty:
            st.dataframe(
                df_paiements,
                column_config={
                    "id": "N°",
                    "nom": "Nom",
                    "prenom": "Prénom",
                    "montant": st.column_config.NumberColumn("Montant", format="%.2f €"),
                    "date_paiement": "Date",
                    "methode_paiement": "Méthode",
                    "type_paiement": "Type",
                    "facture_generee": "Facture"
                },
                use_container_width=True
            )
        else:
            st.info("Aucun paiement enregistré pour le moment.")
    
    with tab_rapports:
        st.subheader("Rapports financiers")
        
        # Sélection de la période
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date de début", value=datetime.now().replace(day=1))
        with col2:
            date_fin = st.date_input("Date de fin")
        
        if st.button("Générer le rapport"):
            # Récupérer les données pour la période sélectionnée
            df_rapport = pd.read_sql_query('''
                SELECT 
                    strftime('%Y-%m', date_paiement) as mois,
                    type_paiement,
                    methode_paiement,
                    SUM(montant) as total
                FROM paiements
                WHERE date_paiement BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', date_paiement), type_paiement, methode_paiement
                ORDER BY mois DESC, type_paiement
            ''', conn, params=(date_debut, date_fin))
            
            if not df_rapport.empty:
                # Afficher un tableau récapitulatif
                st.write("### Récapitulatif des paiements")
                st.dataframe(
                    df_rapport.pivot_table(
                        index=['mois', 'type_paiement'],
                        columns='methode_paiement',
                        values='total',
                        aggfunc='sum',
                        fill_value=0
                    ).style.format("{:.2f} €"),
                    use_container_width=True
                )
                
                # Afficher un graphique
                st.write("### Répartition des paiements par type")
                fig, ax = plt.subplots()
                df_rapport.groupby('type_paiement')['total'].sum().plot.pie(
                    autopct='%1.1f%%',
                    startangle=90,
                    ax=ax
                )
                ax.set_ylabel('')
                st.pyplot(fig)
            else:
                st.info("Aucune donnée disponible pour la période sélectionnée.")
    
    # Création des onglets
    tab_planning, tab_ajout = st.tabs(["📅 Planning des séances", "➕ Ajouter une séance"])
    
    with tab_planning:
        # Sélection du jour
        jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        jour = st.selectbox("Sélectionnez un jour", jours_semaine, index=datetime.now().weekday() % 7)
    
    with tab_ajout:
        # Formulaire d'ajout de séance
        with st.form("form_seance"):
            st.markdown("### Ajouter une nouvelle séance")
            
            # Champs du formulaire
            type_seance = st.selectbox("Type de séance", ["Fitness", "Musculation", "Cardio", "Yoga", "Aeromix"])
            jour_seance = st.selectbox("Jour de la semaine", jours_semaine, index=datetime.now().weekday() % 7)
            heure_debut = st.time_input("Heure de début", value=datetime.strptime("19:00", "%H:%M").time())
            heure_fin = st.time_input("Heure de fin", value=datetime.strptime("20:00", "%H:%M").time())
            capacite_max = st.number_input("Capacité maximale", min_value=1, value=20)
            coach = st.text_input("Nom du coach (optionnel)")
            
            submitted = st.form_submit_button("Ajouter la séance")
            if submitted:
                try:
                    # Ajouter la logique d'ajout de la séance ici
                    st.success(f"Séance de {type_seance} ajoutée avec succès le {jour_seance} !")
                except Exception as e:
                    st.error(f"Erreur lors de l'ajout de la séance : {str(e)}")
    
    # Récupération des séances pour le jour sélectionné
    seances_du_jour = get_seances_par_jour(conn, jour)
    
    if not seances_du_jour.empty:
        st.subheader(f"Séances du {jour}")
        
        for _, seance in seances_du_jour.iterrows():
            with st.container():
                cols = st.columns([1, 3, 1, 1])
                with cols[0]:
                    st.markdown(f"**{seance['heure_debut']} - {seance['heure_fin']}**")
                with cols[1]:
                    st.markdown(f"**{seance['type_seance']}**")
                    st.caption(f"{seance.get('coach', 'Sans coach')}")
                with cols[2]:
                    st.metric("Places", f"{seance.get('places_restantes', '?')}/{seance.get('capacite_max', '?')}")
                with cols[3]:
                    places_restantes = seance.get('places_restantes', 0)
                    if places_restantes is not None and places_restantes > 0:
                        # Utilisation d'un bouton standard avec une clé unique
                        if st.button("S'inscrire", key=f"btn_inscription_{seance.get('id', '')}"):
                            # Logique d'inscription
                            st.success(f"Inscription à {seance.get('type_seance', 'cette séance')} confirmée !")
                            st.balloons()
                    else:
                        st.error("Complet")
    else:
        st.info(f"Aucune séance prévue le {jour}")
    
    # Suppression de la section redondante
        
        # Formulaire d'ajout de séance
        with st.form("form_seance"):
            st.markdown("### Ajouter une nouvelle séance")
            
            col1, col2 = st.columns(2)
            with col1:
                jour_semaine = st.selectbox("Jour de la semaine", 
                                          ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'])
                heure_debut = st.time_input("Heure de début", value=datetime.strptime("20:00", "%H:%M").time())
                type_seance = st.text_input("Type de séance")
            
            with col2:
                duree = st.slider("Durée (minutes)", 30, 120, 60, 15)
                heure_fin = (datetime.combine(datetime.today(), heure_debut) + timedelta(minutes=duree)).time()
                st.write(f"Heure de fin : {heure_fin.strftime('%H:%M')}")
                capacite = st.number_input("Capacité maximale", min_value=1, max_value=50, value=15)
                coach = st.text_input("Coach (optionnel)")
            
            description = st.text_area("Description (optionnel)")
            
            if st.form_submit_button("Ajouter la séance"):
                seance = {
                    'jour_semaine': jour_semaine,
                    'type_seance': type_seance,
                    'heure_debut': heure_debut.strftime('%H:%M'),
                    'heure_fin': heure_fin.strftime('%H:%M'),
                    'capacite_max': capacite,
                    'coach': coach if coach else None,
                    'description': description if description else None
                }
                
                c = conn.cursor()
                c.execute('''
                    INSERT INTO seances (id, jour_semaine, type_seance, heure_debut, heure_fin, 
                                      capacite_max, coach, description, statut)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
                ''', (
                    str(uuid.uuid4()),
                    seance['jour_semaine'],
                    seance['type_seance'],
                    seance['heure_debut'],
                    seance['heure_fin'],
                    seance['capacite_max'],
                    seance['coach'],
                    seance['description']
                ))
                conn.commit()
                st.success("Séance ajoutée avec succès !")
                st.experimental_rerun()
        
        # Liste des séances existantes
        st.markdown("### Séances existantes")
        seances = get_seances(conn)
        
        if not seances.empty:
            for _, seance in seances.iterrows():
                with st.expander(f"{seance['type_seance']} - {seance['jour_semaine']} {seance['heure_debut']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Heure :** {seance['heure_debut']} - {seance['heure_fin']}")
                        st.write(f"**Type :** {seance['type_seance']}")
                        st.write(f"**Coach :** {seance['coach'] or 'Non spécifié'}")
                        st.write(f"**Capacité :** {seance['nb_inscrits']}/{seance['capacite_max']} places")
                        
                    with col2:
                        if seance['description']:
                            st.write("**Description :**")
                            st.write(seance['description'])
                        
                        if st.button("Supprimer", key=f"del_{seance['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM seances WHERE id = ?", (seance['id'],))
                            conn.commit()
                            st.experimental_rerun()
        else:
            st.info("Aucune séance n'a été créée pour le moment.")

def afficher_onglet_adherents(conn):
    st.header("👥 Gestion des adhérents")
    
    # Création des onglets
    tab1, tab2, tab3 = st.tabs(["📋 Liste des adhérents", "➕ Ajouter un adhérent", "📤 Importer des adhérents"])
    
    with tab1:
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            filtre_nom = st.text_input("Rechercher par nom ou prénom", "")
        with col2:
            filtre_statut = st.selectbox("Filtrer par statut", [""] + STATUTS)
        with col3:
            filtre_abonnement = st.selectbox(
                "Filtrer par type d'abonnement",
                [""] + TYPES_ABONNEMENT
            )
        
        # Bouton pour réinitialiser les filtres
        if st.button("Réinitialiser les filtres"):
            filtre_nom = ""
            filtre_statut = ""
            filtre_abonnement = ""
            st.rerun()
        
        # Récupération des adhérents avec filtres
        df_adherents = get_adherents(conn, filtre_nom, filtre_statut, filtre_abonnement)
        
        # Affichage du tableau des adhérents
        if not df_adherents.empty:
            # Formatage des colonnes
            df_display = df_adherents.copy()
            df_display['date_inscription'] = pd.to_datetime(df_display['date_inscription']).dt.strftime('%d/%m/%Y')
            df_display['date_fin_abonnement'] = pd.to_datetime(df_display['date_fin_abonnement']).dt.strftime('%d/%m/%Y')
            
            # Afficher le tableau avec des colonnes sélectionnées
            st.dataframe(
                df_display[['nom', 'prenom', 'telephone', 'email', 'statut', 'type_abonnement', 'date_fin_abonnement']],
                column_config={
                    "nom": "Nom",
                    "prenom": "Prénom",
                    "telephone": "Téléphone",
                    "email": "Email",
                    "statut": "Statut",
                    "type_abonnement": "Type d'abonnement",
                    "date_fin_abonnement": "Fin d'abonnement"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Statistiques rapides
            st.subheader("📊 Statistiques")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total adhérents", len(df_adherents))
            with col2:
                st.metric("Actifs", len(df_adherents[df_adherents['statut'] == 'Actif']))
            with col3:
                st.metric("Abonnements expirant ce mois", 
                         len(df_adherents[pd.to_datetime(df_adherents['date_fin_abonnement']).dt.month == pd.Timestamp.now().month]))
        else:
            st.info("Aucun adhérent trouvé avec ces critères.")
    
    with tab2:
        st.subheader("Nouvel adhérent")
        st.markdown("---")
        
        with st.form("form_adherent", clear_on_submit=True):
            # Section d'information
            st.markdown("### Informations personnelles")
            
            # Première ligne
            col1, col2 = st.columns(2)
            
            with col1:
                nom = st.text_input("Nom *", key="nom_input", placeholder="Entrez le nom")
                prenom = st.text_input("Prénom *", key="prenom_input", placeholder="Entrez le prénom")
                telephone = st.text_input("Téléphone *", key="tel_input", placeholder="771234567")
            
            with col2:
                email = st.text_input("Email", key="email_input", placeholder="exemple@domaine.com")
                
                statut = st.selectbox(
                    "Statut *",
                    STATUTS,
                    key="statut_select"
                )
                
                type_abonnement = st.selectbox(
                    "Type d'abonnement *",
                    TYPES_ABONNEMENT,
                    key="abonnement_select"
                )
                
                # Calcul du montant et de la date de fin
                date_aujourdhui = datetime.now().date()
                montant = 0
                
                if "Mensuel (15,000 XOF)" in type_abonnement:
                    montant = 15000
                    date_fin = date_aujourdhui + timedelta(days=30)
                elif "Mensuel (20,000 XOF)" in type_abonnement:
                    montant = 20000
                    date_fin = date_aujourdhui + timedelta(days=30)
                elif "Trimestriel" in type_abonnement:
                    montant = 40000
                    date_fin = date_aujourdhui + timedelta(weeks=12)  # 3 mois
                elif "Annuel" in type_abonnement:
                    montant = 120000
                    date_fin = date_aujourdhui + timedelta(weeks=52)  # 1 an
                else:  # Séance unique
                    montant = 1000 if "1,000" in type_abonnement else 2000
                    date_fin = date_aujourdhui
                
                # Affichage du montant et de la date de fin
                st.write(f"<div style='background-color: #f0f8ff; padding: 10px; border-radius: 5px;'>"
                        f"<strong>Montant à payer :</strong> {montant:,} XOF<br>"
                        f"<strong>Date de fin d'abonnement :</strong> {date_fin.strftime('%d/%m/%Y')}"
                        "</div>", 
                        unsafe_allow_html=True)
                
                # Champ caché pour la date de fin
                date_fin_input = st.date_input(
                    "Date de fin d'abonnement *", 
                    value=date_fin,
                    min_value=date_aujourdhui,
                    key="date_input",
                    disabled=False,
                    help="Date de fin automatiquement calculee selon le type d abonnement"
                )
                
                # Section de paiement
                st.markdown("---")
                st.subheader("💳 Paiement")
                
                # Sélection de la méthode de paiement
                methode_paiement = st.radio(
                    "Méthode de paiement *",
                    METHODES_PAIEMENT,
                    horizontal=True,
                    key="methode_paiement_radio"
                )
                
                statut_paiement = st.selectbox(
                    "Statut du paiement *",
                    ["Payé", "En attente", "Annulé"],
                    key="statut_paiement_select"
                )
                
                montant_paye = st.number_input(
                    "Montant payé (XOF) *",
                    min_value=0.0,
                    value=float(montant),
                    step=1000.0,
                    key="montant_paye_input"
                )
                
                commentaires = st.text_area("Commentaires", key="commentaires_area")
            
            # Bouton de soumission
            submitted = st.form_submit_button("Enregistrer l'adhérent")
            
            if submitted:
                # Validation des champs obligatoires
                if not nom or not prenom or not telephone or not type_abonnement:
                    st.error("Veuillez remplir tous les champs obligatoires (*).")
                else:
                    # Création du dictionnaire adhérent
                    nouvel_adherent = {
                        'id': str(uuid.uuid4()),
                        'nom': nom,
                        'prenom': prenom,
                        'telephone': telephone,
                        'email': email,
                        'statut': statut,
                        'type_abonnement': type_abonnement,
                        'date_inscription': date_aujourdhui.strftime('%Y-%m-%d'),
                        'date_fin_abonnement': date_fin_input.strftime('%Y-%m-%d'),
                        'methode_paiement': methode_paiement,
                        'statut_paiement': statut_paiement,
                        'montant_paye': montant_paye,
                        'date_dernier_paiement': date_aujourdhui.strftime('%Y-%m-%d'),
                        'commentaires': commentaires
                    }
                    
                    # Ajout de l'adhérent
                    success, message = ajouter_adherent(conn, nouvel_adherent)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
    
    with tab3:
        st.subheader("Importer des adhérents")
        st.markdown("---")
        
        st.info("💡 Téléchargez un fichier Excel (.xlsx) contenant la liste des adhérents. "
               "Assurez-vous que le fichier contient les colonnes suivantes : "
               "Nom, Prénom, Téléphone, Email, Type d'abonnement, Statut, Méthode de paiement, Montant payé.")
        
        fichier = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])
        
        if fichier is not None:
            try:
                # Lire le fichier Excel
                df_import = pd.read_excel(fichier)
                
                # Aperçu des données
                st.subheader("Aperçu des données à importer")
                st.dataframe(df_import.head())
                
                # Bouton de confirmation d'importation
                if st.button("Confirmer l'importation"):
                    # Traitement des données et insertion dans la base de données
                    succes = 0
                    echecs = 0
                    
                    for _, row in df_import.iterrows():
                        try:
                            # Conversion des données
                            adherent = {
                                'id': str(uuid.uuid4()),
                                'nom': str(row.get('Nom', '')).strip(),
                                'prenom': str(row.get('Prénom', '')).strip(),
                                'telephone': str(row.get('Téléphone', '')).strip(),
                                'email': str(row.get('Email', '')).strip(),
                                'statut': str(row.get('Statut', 'Actif')).strip(),
                                'type_abonnement': str(row.get("Type d'abonnement", '')).strip(),
                                'date_inscription': datetime.now().strftime('%Y-%m-%d'),
                                'date_fin_abonnement': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),  # Par défaut 1 mois
                                'methode_paiement': str(row.get('Méthode de paiement', 'Espèces')).strip(),
                                'statut_paiement': 'Payé',
                                'montant_paye': float(row.get('Montant payé', 0)),
                                'date_dernier_paiement': datetime.now().strftime('%Y-%m-%d'),
                                'commentaires': 'Importé depuis fichier Excel'
                            }
                            
                            # Validation des champs obligatoires
                            if adherent['nom'] and adherent['prenom'] and adherent['telephone']:
                                ajouter_adherent(conn, adherent)
                                succes += 1
                            else:
                                echecs += 1
                        except Exception as e:
                            echecs += 1
                            continue
                    
                    st.success(f"Importation terminée : {succes} adhérent(s) importé(s) avec succès, {echecs} échec(s).")
                    
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {str(e)}")

# Fermer la connexion à la base de données à la fin
try:
    conn.close()
except:
    pass

# Point d'entrée principal pour Streamlit
cd /Users/issandoye/CascadeProjects/windsurf-project
echo "from ISBISPORTCLUB.app_new import main\n\nif __name__ == \"__main__\":\n    main()" > streamlit_app.py

def main():
    # Votre code principal ici
    pass
if __name__ == "__main__":
    main()
 from ISBISPORTCLUB.app_new import main
if __name__ == "__main__":
    main()
       
