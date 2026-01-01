import streamlit as st
from datetime import datetime, timedelta
import os
import uuid
import json
import pandas as pd
import numpy as np
import io
from dotenv import load_dotenv
from payment_service import PaymentService
from notifications import NotificationService

# Configuration de la page - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="ISBISPORTCLUB - Gestion",
    page_icon="🏋️",
    layout="wide"
)

import pandas as pd
import os
from pathlib import Path
from streamlit_option_menu import option_menu
import yaml
from yaml.loader import SafeLoader
import sqlite3
import hashlib
from dotenv import load_dotenv
from paiements import afficher_boutons_paiement, enregistrer_paiement
import uuid

# Ajout de styles CSS personnalisés
st.markdown("""
    <style>
        /* Style général */
        .main {
            background-color: #ffffff;
        }
        
        /* Titre principal */
        h1 {
            color: #1a4d2e;  /* Vert foncé */
            border-bottom: 2px solid #e74c3c;  /* Rouge ISBISPORT */
            padding-bottom: 10px;
        }
        
        /* Cartes */
        .stCard {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #4a9d5e;  /* Vert ISBISPORT */
        }
        
        /* Boutons */
        .stButton>button {
            background-color: #4a9d5e;  /* Vert ISBISPORT */
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            border: none;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #3d824d;  /* Vert foncé au survol */
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Formulaire de connexion */
        .stForm {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #e0e0e0;
        }
        
        /* Barre latérale */
        [data-testid="stSidebar"] {
            background-color: #1a4d2e;  /* Vert foncé ISBISPORT */
            color: white;
        }
        
        [data-testid="stSidebar"] .stButton>button {
            width: 100%;
            margin: 5px 0;
            background-color: #e74c3c;  /* Rouge ISBISPORT */
            transition: all 0.3s ease;
        }
        
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: #c0392b;  /* Rouge foncé au survol */
            transform: translateY(-2px);
        }
        
        /* Tableaux */
        table {
            border-collapse: separate;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        th {
            background-color: #1a4d2e;  /* Vert foncé ISBISPORT */
            color: white;
            font-weight: 600;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f5e9;  /* Vert très clair au survol */
        }
        
        /* En-tête personnalisé */
        .header-box {
            background: linear-gradient(135deg, #1a4d2e 0%, #4a9d5e 100%);
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 25px;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .header-box h1 {
            color: white;
            border-bottom: 2px solid #e74c3c;  /* Rouge ISBISPORT */
            padding-bottom: 10px;
            margin-top: 0;
        }
    </style>
""", unsafe_allow_html=True)

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page (déjà définie au début du fichier)

# Initialisation de la base de données
def init_db():
    conn = sqlite3.connect('isbisportclub.db')
    c = conn.cursor()
    
    # Création des tables si elles n'existent pas
    c.execute('''
        CREATE TABLE IF NOT EXISTS adherents (
            id TEXT PRIMARY KEY,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            telephone TEXT,
            email TEXT,
            date_inscription TEXT,
            type_abonnement TEXT,
            date_fin_abonnement TEXT,
            statut TEXT,
            commentaires TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS seances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jour TEXT,
            horaire TEXT,
            activite TEXT,
            coach TEXT,
            salle TEXT,
            places_max INTEGER,
            inscrits INTEGER
        )
    ''')
    
    conn.commit()
    return conn

# Initialisation de la base de données
conn = init_db()

# Configuration de l'authentification simplifiée

# En-tête personnalisé
st.markdown("""
    <div class="header-box">
        <h1>ISBISPORTCLUB 🏋️</h1>
        <p style="margin: 0; font-size: 1.1em; opacity: 0.9;">Gestion de la salle de sport</p>
    </div>
""", unsafe_allow_html=True)

# Authentification simplifiée avec style
with st.sidebar:
    st.markdown("<div class='stForm'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #2c3e50; margin-bottom: 20px;'>Connexion</h3>", unsafe_allow_html=True)
    
    # Vérifier si l'utilisateur est déjà connecté
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", key="username")
            password = st.text_input("Mot de passe", type="password", key="password")
            submit_button = st.form_submit_button("Se connecter", type="primary")
            
            # Vérification des identifiants
            if submit_button:
                if username == 'admin' and password == 'admin123':
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    else:
        st.success("Connecté en tant qu'admin")
        if st.button("Se déconnecter", type="primary"):
            st.session_state.authenticated = False
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Vérifier l'état d'authentification
authentication_status = st.session_state.authenticated

# Menu de navigation
if authentication_status:
    with st.sidebar:
        st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
        selected = option_menu(
            menu_title=None,
            options=["🏠 Tableau de bord", "👥 Adhérents", "📅 Séances", "💳 Abonnements", "📊 Statistiques"],
            icons=None,
            default_index=0,
            key="main_menu"
        )
    
    # Contenu principal
    if selected == "🏠 Tableau de bord":
        st.title("Tableau de Bord")
        
        # Afficher des statistiques de base
        st.subheader("Statistiques")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Adhérents", len(get_adherents(conn)))
            
        with col2:
            # Compter les adhérents actifs
            st.metric("Adhérents Actifs", len(conn.execute("SELECT id FROM adherents WHERE statut = 'Actif'").fetchall()))
            
        with col3:
            # Séances du jour
            seances_du_jour = get_seances(conn, datetime.now().strftime('%A'))
            st.metric("Séances Aujourd'hui", len(seances_du_jour))
            
        with col4:
            # Inscriptions du jour
            inscriptions_du_jour = pd.read_sql_query("""
                SELECT COUNT(*) as count FROM inscriptions 
                WHERE date(date_inscription) = date('now')
            """, conn).iloc[0]['count']
            st.metric("Inscriptions Aujourd'hui", inscriptions_du_jour)
        
        # Graphique de fréquentation
        st.subheader("Fréquentation cette semaine")
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        
        # Récupérer les données de fréquentation
        frequentation = []
        for jour in jours_semaine:
            count = pd.read_sql_query("""
                SELECT COUNT(*) as count 
                FROM inscriptions i
                JOIN seances s ON i.seance_id = s.id
                WHERE s.jour_semaine = ?
                AND date(i.date_inscription) >= date('now', 'weekday 0', '-7 days')
                AND date(i.date_inscription) < date('now', 'weekday 0')
            """, conn, params=(jour,)).iloc[0]['count']
            frequentation.append(count)
        
        # Créer le graphique
        chart_data = pd.DataFrame({
            'Jour': jours_semaine,
            'Fréquentation': frequentation
        })
        st.bar_chart(chart_data.set_index('Jour'))
        
        # Prochaines séances
        st.subheader("Prochaines séances")
        prochaines_seances = pd.read_sql_query("""
            SELECT s.*, COUNT(i.id) as inscrits
            FROM seances s
            LEFT JOIN inscriptions i ON s.id = i.seance_id 
                AND date(i.date_inscription) = date('now')
            WHERE s.statut = 'active'
            GROUP BY s.id
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
            LIMIT 5
        """, conn)
        
        if not prochaines_seances.empty:
            for _, seance in prochaines_seances.iterrows():
                places_restantes = seance['capacite_max'] - seance['inscrits']
                with st.container():
                    cols = st.columns([1, 3, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{seance['jour_semaine']}**\n{seance['heure_debut']} - {seance['heure_fin']}")
                    with cols[1]:
                        st.markdown(f"**{seance['type_seance']}**")
                        st.caption(f"{seance['coach'] or 'Sans coach'}")
                    with cols[2]:
                        st.metric("Places", f"{places_restantes}/{seance['capacite_max']}")
                    with cols[3]:
                        if st.button("Voir", key=f"voir_{seance['id']}"):
                            st.session_state['selected_seance'] = seance['id']
                            st.experimental_rerun()
        else:
            st.info("Aucune séance à venir pour le moment.")
            
    elif selected == "📅 Planning":
        st.title("Gestion du Planning")
        
        # Onglets pour la gestion du planning
        tab_planning, tab_seances, tab_inscriptions = st.tabs(["📅 Planning Hebdomadaire", "➕ Gérer les Séances", "👥 Inscriptions"])
        
        with tab_planning:
            st.subheader("Planning Hebdomadaire")
            
            # Sélecteur de semaine
            semaine_actuelle = datetime.now().strftime("%Y-%m-%d")
            date_debut = st.date_input("Semaine du", 
                                     datetime.now(), 
                                     key="date_planning")
            
            # Afficher le planning pour chaque jour de la semaine
            jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            
            # Créer un conteneur pour chaque jour
            for jour in jours_semaine:
                with st.expander(f"{jour}", expanded=jour == datetime.now().strftime('%A')):
                    seances_jour = get_seances(conn, jour)
                    
                    if not seances_jour.empty:
                        for _, seance in seances_jour.iterrows():
                            places_restantes = seance['places_restantes']
                            
                            with st.container():
                                cols = st.columns([1, 3, 1, 1])
                                with cols[0]:
                                    st.markdown(f"**{seance['heure_debut']} - {seance['heure_fin']}**")
                                with cols[1]:
                                    st.markdown(f"**{seance['type_seance']}**")
                                    st.caption(f"{seance['coach'] or 'Sans coach'}")
                                with cols[2]:
                                    st.metric("Places", f"{places_restantes}/{seance['capacite_max']}")
                                with cols[3]:
                                    if st.button("S'inscrire", key=f"inscrire_{seance['id']}"):
                                        # Logique d'inscription
                                        if inscrire_adherent(conn, st.session_state.get('user_id'), seance['id']):
                                            st.success("Inscription réussie !")
                                        else:
                                            st.error("Impossible de vous inscrire à cette séance.")
                    else:
                        st.info(f"Aucune séance prévue le {jour}")
        
        with tab_seances:
            st.subheader("Gérer les Séances")
            
            # Formulaire d'ajout de séance
            with st.form("form_seance"):
                st.markdown("### Ajouter une nouvelle séance")
                
                col1, col2 = st.columns(2)
                with col1:
                    jour_semaine = st.selectbox("Jour de la semaine", 
                                              ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'])
                    heure_debut = st.time_input("Heure de début", value=datetime.strptime("09:00", "%H:%M").time())
                    type_seance = st.selectbox("Type de séance", 
                                            ["Cardio", "Musculation", "Cours collectif", "Yoga", "Pilates", "CrossFit"])
                
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
                        'heure_debut': heure_debut.strftime('%H:%M'),
                        'heure_fin': heure_fin.strftime('%H:%M'),
                        'type_seance': type_seance,
                        'capacite_max': capacite,
                        'coach': coach if coach else None,
                        'description': description if description else None
                    }
                    try:
                        ajouter_seance(conn, seance)
                        st.success("Séance ajoutée avec succès !")
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout de la séance : {str(e)}")
            
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
                            
                            # Boutons d'action
                            if st.button("Modifier", key=f"mod_{seance['id']}"):
                                st.session_state['editing_seance'] = seance['id']
                                
                            if st.button("Supprimer", key=f"del_{seance['id']}"):
                                supprimer_seance(conn, seance['id'])
                                st.experimental_rerun()
                            
                            if st.button("Voir les inscrits", key=f"view_{seance['id']}"):
                                st.session_state['selected_seance'] = seance['id']
                                st.experimental_rerun()
            else:
                st.info("Aucune séance n'a été créée pour le moment.")
        
        with tab_inscriptions:
            st.subheader("Gestion des Inscriptions")
            
            # Sélectionner une séance pour voir les inscriptions
            seances = get_seances(conn)
            if not seances.empty:
                seance_selectionnee = st.selectbox(
                    "Sélectionner une séance",
                    options=[f"{s['type_seance']} - {s['jour_semaine']} {s['heure_debut']}" for _, s in seances.iterrows()],
                    format_func=lambda x: x
                )
                
                # Récupérer l'ID de la séance sélectionnée
                seance_id = seances.iloc[seances.apply(
                    lambda x: f"{x['type_seance']} - {x['jour_semaine']} {x['heure_debut']}" == seance_selectionnee, 
                    axis=1
                )]['id'].values[0]
                
                # Afficher les inscriptions pour cette séance
                inscriptions = get_inscriptions_par_seance(conn, seance_id)
                
                if not inscriptions.empty:
                    st.write(f"**{len(inscriptions)} inscrit(s) sur {seances[seances['id'] == seance_id]['capacite_max'].values[0]} places**")
                    
                    # Afficher la liste des inscrits
                    for _, inscrit in inscriptions.iterrows():
                        with st.container():
                            cols = st.columns([3, 1, 1])
                            with cols[0]:
                                st.write(f"**{inscrit['prenom']} {inscrit['nom']}")
                                st.caption(f"Tél: {inscrit['telephone']} | Inscrit le: {inscrit['date_inscription']}")
                            
                            with cols[1]:
                                statut = st.selectbox(
                                    "Statut",
                                    ['confirmée', 'en attente', 'annulée'],
                                    index=['confirmée', 'en attente', 'annulée'].index(inscrit['statut']),
                                    key=f"statut_{inscrit['id']}",
                                    label_visibility="collapsed"
                                )
                                
                                # Mettre à jour le statut si modifié
                                if statut != inscrit['statut']:
                                    c = conn.cursor()
                                    c.execute("UPDATE inscriptions SET statut = ? WHERE id = ?", 
                                            (statut, inscrit['id']))
                                    conn.commit()
                                    st.experimental_rerun()
                            
                            with cols[2]:
                                presence = st.checkbox(
                                    "Présent",
                                    value=bool(inscrit['presence']),
                                    key=f"presence_{inscrit['id']}",
                                    label_visibility="collapsed"
                                )
                                
                                # Mettre à jour la présence si modifiée
                                if presence != bool(inscrit['presence']):
                                    c = conn.cursor()
                                    c.execute("UPDATE inscriptions SET presence = ? WHERE id = ?", 
                                            (1 if presence else 0, inscrit['id']))
                                    conn.commit()
                                    st.experimental_rerun()
                            
                            st.divider()
                    
                    # Bouton d'export des présences
                    if st.button("📥 Exporter la liste des présences"):
                        # Créer un DataFrame avec les informations à exporter
                        df_export = inscriptions[['nom', 'prenom', 'telephone', 'statut', 'presence']]
                        df_export['Présence'] = df_export['presence'].apply(lambda x: 'Oui' if x else 'Non')
                        df_export = df_export.drop('presence', axis=1)
                        
                        # Générer le fichier Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df_export.to_excel(writer, sheet_name='Liste des présences', index=False)
                            
                            # Formater le fichier Excel
                            workbook = writer.book
                            worksheet = writer.sheets['Liste des présences']
                            
                            # Ajouter un format pour les en-têtes
                            header_format = workbook.add_format({
                                'bold': True,
                                'text_wrap': True,
                                'valign': 'top',
                                'fg_color': '#4CAF50',
                                'color': 'white',
                                'border': 1
                            })
                            
                            # Écrire les en-têtes avec le format
                            for col_num, value in enumerate(df_export.columns.values):
                                worksheet.write(0, col_num, value, header_format)
                            
                            # Ajuster la largeur des colonnes
                            for i, col in enumerate(df_export.columns):
                                max_length = max(
                                    df_export[col].astype(str).apply(len).max(),
                                    len(str(col))
                                ) + 2
                                worksheet.set_column(i, i, max_length)
                        
                        # Télécharger le fichier
                        st.download_button(
                            label="Télécharger la liste des présences",
                            data=output.getvalue(),
                            file_name=f"presences_{seance_selectionnee.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.info("Aucune inscription pour cette séance.")
                    
                    # Formulaire d'inscription manuelle
                    st.markdown("### Inscrire un adhérent")
                    adherents = get_adherents(conn)
                    if not adherents.empty:
                        with st.form("form_inscription"):
                            adherent_id = st.selectbox(
                                "Sélectionner un adhérent",
                                options=adherents['id'],
                                format_func=lambda x: f"{adherents[adherents['id'] == x]['prenom'].values[0]} {adherents[adherents['id'] == x]['nom'].values[0]}"
                            )
                            
                            if st.form_submit_button("Inscrire"):
                                if inscrire_adherent(conn, adherent_id, seance_id):
                                    st.success("Adhérent inscrit avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Impossible d'inscrire cet adhérent à cette séance.")
                    else:
                        st.warning("Aucun adhérent n'est enregistré dans le système.")
        
    elif selected == "👥 Adhérents":
        st.title("Gestion des Adhérents")
        
        # Initialisation de la base de données pour les adhérents
        def init_seances_par_defaut(conn):
            """Initialise les séances par défaut si elles n'existent pas"""
            c = conn.cursor()
            
            # Vérifier si la table seances existe
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='seances'
            """)
            if not c.fetchone():
                return  # La table n'existe pas encore, on laissera init_adherents_db s'en occuper
            
            # Vérifier s'il y a déjà des séances
            c.execute("SELECT COUNT(*) FROM seances")
            if c.fetchone()[0] > 0:
                return  # Des séances existent déjà
            
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
                c.execute("""
                    INSERT INTO seances (id, jour_semaine, type_seance, heure_debut, heure_fin, 
                                      capacite_max, coach, description, statut, date_creation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', datetime('now'))
                """, (
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

        def init_adherents_db():
            conn = sqlite3.connect('isbisport.db')
            c = conn.cursor()
            
            # Créer la table des adhérents avec tous les champs nécessaires
            c.execute('''
                CREATE TABLE IF NOT EXISTS adherents (
                    id TEXT PRIMARY KEY,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    telephone TEXT,
                    email TEXT,
                    statut TEXT DEFAULT 'Actif',
                    type_abonnement TEXT,
                    date_inscription TEXT,
                    date_fin_abonnement TEXT,
                    montant_abonnement REAL,
                    methode_paiement TEXT,
                    statut_paiement TEXT DEFAULT 'en_attente',
                    reference_paiement TEXT,
                    date_paiement TEXT,
                    details_paiement TEXT,
                    commentaires TEXT,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    date_maj TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Créer un index sur les champs fréquemment utilisés pour les recherches
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_adherents_nom_prenom 
                ON adherents(nom, prenom)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_adherents_telephone 
                ON adherents(telephone)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_adherents_statut_paiement 
                ON adherents(statut_paiement)
            ''')
            
            # Créer la table des séances
            c.execute('''
                CREATE TABLE IF NOT EXISTS seances (
                    id TEXT PRIMARY KEY,
                    jour_semaine TEXT NOT NULL,
                    heure_debut TEXT NOT NULL,
                    heure_fin TEXT NOT NULL,
                    type_seance TEXT NOT NULL,
                    capacite_max INTEGER DEFAULT 15,
                    coach TEXT,
                    description TEXT,
                    statut TEXT DEFAULT 'active',
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Créer la table des inscriptions aux séances
            c.execute('''
                CREATE TABLE IF NOT EXISTS inscriptions (
                    id TEXT PRIMARY KEY,
                    adherent_id TEXT NOT NULL,
                    seance_id TEXT NOT NULL,
                    date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
                    statut TEXT DEFAULT 'confirmée',
                    presence BOOLEAN DEFAULT 0,
                    FOREIGN KEY (adherent_id) REFERENCES adherents (id),
                    FOREIGN KEY (seance_id) REFERENCES seances (id),
                    UNIQUE(adherent_id, seance_id, date_inscription)
                )
            ''')
            
            # Créer les index pour les performances
            c.execute('CREATE INDEX IF NOT EXISTS idx_seances_jour ON seances(jour_semaine, heure_debut)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_inscriptions_adherent ON inscriptions(adherent_id)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_inscriptions_seance ON inscriptions(seance_id)')
            
            conn.commit()
            return conn

        # Fonction pour ajouter un adhérent
        def ajouter_adherent(conn, adherent):
            c = conn.cursor()
            
            # Vérifier si la table existe déjà avec les anciennes colonnes
            c.execute('''PRAGMA table_info(adherents)''')
            columns = [column[1] for column in c.fetchall()]
            
            # Mettre à jour la structure de la table si nécessaire
            if 'id' not in columns:
                # Créer une nouvelle table avec la structure mise à jour
                c.execute('''
                    CREATE TABLE IF NOT EXISTS new_adherents (
                        id TEXT PRIMARY KEY,
                        nom TEXT NOT NULL,
                        prenom TEXT NOT NULL,
                        telephone TEXT,
                        email TEXT,
                        statut TEXT DEFAULT 'Actif',
                        type_abonnement TEXT,
                        date_inscription TEXT,
                        date_fin_abonnement TEXT,
                        montant_abonnement REAL,
                        methode_paiement TEXT,
                        statut_paiement TEXT DEFAULT 'en_attente',
                        reference_paiement TEXT,
                        date_paiement TEXT,
                        details_paiement TEXT
                    )
                ''')
                
                # Copier les données existantes
                c.execute('''
                    INSERT INTO new_adherents 
                    SELECT 
                        rowid as id,
                        nom,
                        prenom,
                        telephone,
                        email,
                        statut,
                        type_abonnement,
                        date('now') as date_inscription,
                        date_fin_abonnement,
                        CASE 
                            WHEN type_abonnement LIKE '%15,000%' THEN 15000
                            WHEN type_abonnement LIKE '%20,000%' THEN 20000
                            WHEN type_abonnement LIKE '%40,000%' THEN 40000
                            WHEN type_abonnement LIKE '%120,000%' THEN 120000
                            WHEN type_abonnement LIKE '%1,000%' THEN 1000
                            WHEN type_abonnement LIKE '%2,000%' THEN 2000
                            ELSE 0
                        END as montant_abonnement,
                        'Non spécifié' as methode_paiement,
                        'inconnu' as statut_paiement,
                        NULL as reference_paiement,
                        NULL as date_paiement,
                        NULL as details_paiement
                    FROM adherents
                ''')
                
                # Supprimer l'ancienne table et renommer la nouvelle
                c.execute('''DROP TABLE adherents''')
                c.execute('''ALTER TABLE new_adherents RENAME TO adherents''')
                conn.commit()
            
            # Insérer le nouvel adhérent
            c.execute('''
                INSERT INTO adherents (
                    id, nom, prenom, telephone, email, statut, type_abonnement, 
                    date_inscription, date_fin_abonnement, montant_abonnement,
                    methode_paiement, statut_paiement, reference_paiement, 
                    date_paiement, details_paiement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adherent.get('id', str(uuid.uuid4())),
                adherent['nom'],
                adherent['prenom'],
                adherent['telephone'],
                adherent.get('email', ''),
                adherent.get('statut', 'Actif'),
                adherent.get('type_abonnement', ''),
                adherent.get('date_inscription', datetime.now().strftime('%Y-%m-%d')),
                adherent.get('date_fin_abonnement', ''),
                adherent.get('montant_abonnement', 0),
                adherent.get('methode_paiement', 'Non spécifié'),
                adherent.get('statut_paiement', 'en_attente'),
                adherent.get('reference_paiement'),
                adherent.get('date_paiement'),
                json.dumps(adherent.get('details_paiement', {})) if isinstance(adherent.get('details_paiement'), dict) else adherent.get('details_paiement')
            ))
            conn.commit()

                                  capacite_max, coach, description, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (seance_id, seance['jour_semaine'], seance['heure_debut'], 
                 seance['heure_fin'], seance['type_seance'], seance.get('capacite_max', 15),
                 seance.get('coach'), seance.get('description'), seance.get('statut', 'active')))
            conn.commit()
            return seance_id
            
        def modifier_seance(conn, seance_id, updates):
            c = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values())
            values.append(seance_id)
            c.execute(f"UPDATE seances SET {set_clause} WHERE id = ?", values)
            conn.commit()
            
        def supprimer_seance(conn, seance_id):
            c = conn.cursor()
            c.execute("DELETE FROM seances WHERE id = ?", (seance_id,))
            conn.commit()
            
        def get_seances(conn, jour_semaine=None):
            query = """
                SELECT s.*, 
                       COUNT(i.id) as nb_inscrits,
                       s.capacite_max - COUNT(i.id) as places_restantes
                FROM seances s
                LEFT JOIN inscriptions i ON s.id = i.seance_id 
                    AND date(i.date_inscription) = date('now')
            """
            params = ()
            if jour_semaine:
                query += " WHERE s.jour_semaine = ?"
                params = (jour_semaine,)
                
            query += " GROUP BY s.id ORDER BY s.jour_semaine, s.heure_debut"
            return pd.read_sql_query(query, conn, params=params)
            
        # Fonctions pour la gestion des inscriptions
        def inscrire_adherent(conn, adherent_id, seance_id):
            c = conn.cursor()
            # Vérifier si l'adhérent est déjà inscrit
            c.execute("""
                SELECT id FROM inscriptions 
                WHERE adherent_id = ? AND seance_id = ? 
                AND date(date_inscription) = date('now')
            """, (adherent_id, seance_id))
            if c.fetchone():
                return False  # Déjà inscrit
                
            # Vérifier s'il reste des places
            c.execute("""
                SELECT s.capacite_max, COUNT(i.id) as nb_inscrits
                FROM seances s
                LEFT JOIN inscriptions i ON s.id = i.seance_id 
                    AND date(i.date_inscription) = date('now')
                WHERE s.id = ?
                GROUP BY s.id
            """, (seance_id,))
            result = c.fetchone()
            
            if result and result[1] >= result[0]:
                return False  # Plus de places disponibles
                
            # Effectuer l'inscription
            c.execute('''
                INSERT INTO inscriptions (id, adherent_id, seance_id, statut)
                VALUES (?, ?, ?, 'confirmée')
            ''', (str(uuid.uuid4()), adherent_id, seance_id))
            conn.commit()
            return True
            
        def desinscrire_adherent(conn, inscription_id):
            c = conn.cursor()
            c.execute("DELETE FROM inscriptions WHERE id = ?", (inscription_id,))
            conn.commit()
            
        def get_inscriptions_par_adherent(conn, adherent_id):
            return pd.read_sql_query('''
                SELECT i.*, s.jour_semaine, s.heure_debut, s.heure_fin, s.type_seance, s.coach
                FROM inscriptions i
                JOIN seances s ON i.seance_id = s.id
                WHERE i.adherent_id = ?
                ORDER BY s.jour_semaine, s.heure_debut
            ''', conn, params=(adherent_id,))
            
        def get_inscriptions_par_seance(conn, seance_id):
            return pd.read_sql_query('''
                SELECT i.*, a.nom, a.prenom, a.telephone
                FROM inscriptions i
                JOIN adherents a ON i.adherent_id = a.id
                WHERE i.seance_id = ?
                ORDER BY a.nom, a.prenom
            ''', conn, params=(seance_id,))

        # Initialisation de la base de données
        conn = init_adherents_db()
        
        # Initialisation des séances par défaut
        if 'seances_initialisees' not in st.session_state:
            nb_seances = init_seances_par_defaut(conn)
            if nb_seances and nb_seances > 0:
                st.toast(f"✅ {nb_seances} séances par défaut ont été créées", icon="✅")
            st.session_state.seances_initialisees = True

        # Onglets pour la gestion des adhérents
        tab1, tab2, tab3 = st.tabs(["📋 Liste des adhérents", "➕ Nouvel adhérent", "📤 Importer depuis Excel"])

        with tab1:
            st.subheader("Liste des adhérents")
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                statut_filter = st.selectbox(
                    "Filtrer par statut",
                    ["Tous", "Actif", "Inactif", "En attente"]
                )
            
            with col2:
                search_term = st.text_input("Rechercher un adhérent")
            
            # Récupération des données avec filtres
            query = "SELECT * FROM adherents WHERE 1=1"
            params = []
            
            if statut_filter != "Tous":
                query += " AND statut = ?"
                params.append(statut_filter)
                
            if search_term:
                query += " AND (nom LIKE ? OR prenom LIKE ? OR telephone LIKE ?)"
                search_term = f"%{search_term}%"
                params.extend([search_term, search_term, search_term])
            
            query += " ORDER BY nom, prenom"
            
            df_adherents = pd.read_sql(query, conn, params=params if params else None)
            
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
                st.subheader("Statistiques")
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
            
            # Test d'affichage
            st.write("🔍 Vérification de l'affichage - Ce message est-il visible ?")
            
            with st.form("form_adherent", clear_on_submit=True):
                # Section d'information
                st.markdown("### Informations personnelles")
                
                # Première ligne
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("Champ Nom :")
                    nom = st.text_input("Nom *", key="nom_input", placeholder="Entrez le nom")
                    st.write("Champ Prénom :")
                    prenom = st.text_input("Prénom *", key="prenom_input", placeholder="Entrez le prénom")
                    st.write("Champ Téléphone :")
                    telephone = st.text_input("Téléphone *", key="tel_input", placeholder="771234567")
                
                with col2:
                    st.write("Champ Email :")
                    email = st.text_input("Email", key="email_input", placeholder="exemple@domaine.com")
                    
                    st.write("Champ Statut :")
                    statut = st.selectbox(
                        "Statut *",
                        ["Actif", "Inactif", "En attente"],
                        key="statut_select"
                    )
                    
                    st.write("Type d'abonnement :")
                    abonnement_options = [
                        "Mensuel (15,000 XOF)",
                        "Mensuel (20,000 XOF)",
                        "Trimestriel (40,000 XOF)",
                        "Annuel (120,000 XOF)",
                        "Séance unique (1,000 XOF)",
                        "Séance unique (2,000 XOF)"
                    ]
                    abonnement_type = st.selectbox(
                        "Type d'abonnement *",
                        abonnement_options,
                        key="abonnement_select"
                    )
                    
                    # Calcul du montant et de la date de fin
                    date_aujourdhui = datetime.now().date()
                    montant = 0
                    
                    if "Mensuel (15,000 XOF)" in abonnement_type:
                        montant = 15000
                        date_fin = date_aujourdhui + timedelta(days=30)
                    elif "Mensuel (20,000 XOF)" in abonnement_type:
                        montant = 20000
                        date_fin = date_aujourdhui + timedelta(days=30)
                    elif "Trimestriel" in abonnement_type:
                        montant = 40000
                        date_fin = date_aujourdhui + timedelta(weeks=12)  # 3 mois
                    elif "Annuel" in abonnement_type:
                        montant = 120000
                        date_fin = date_aujourdhui + timedelta(weeks=52)  # 1 an
                    else:  # Séance unique
                        montant = 1000 if "1,000" in abonnement_type else 2000
                        date_fin = date_aujourdhui
                    
                    # Affichage du montant et de la date de fin
                    st.write(f"<div style='background-color: #f0f8ff; padding: 10px; border-radius: 5px;'>"
                            f"<strong>Montant à payer :</strong> {montant:,} XOF<br>"
                            f"<strong>Date de fin d'abonnement :</strong> {date_fin.strftime('%d/%m/%Y')}"
                            "</div>", 
                            unsafe_allow_html=True)
                    
                    # Champ caché pour la date de fin
                    date_fin = st.date_input(
                        "Date de fin d'abonnement *", 
                        value=date_fin,
                        min_value=date_aujourdhui,
                        key="date_input",
                        disabled=True,
                        label_visibility="collapsed"
                    )
                    
                    # Section de paiement
                    st.markdown("---")
                    st.subheader("Paiement")
                    
                    # Sélection de la méthode de paiement
                    from config import PAYMENT_METHODS
                    
                    # Styles CSS pour les boutons radio stylisés
                    st.markdown("""
                    <style>
                        /* Style général des options de paiement */
                        .stRadio > div {
                            display: flex;
                            gap: 10px;
                        }
                        
                        /* Style de chaque option */
                        .stRadio [role="radiogroup"] {
                            display: flex;
                            flex-wrap: wrap;
                            gap: 10px;
                        }
                        
                        .stRadio [role="radiogroup"] > label {
                            flex: 1;
                            min-width: 120px;
                            margin: 0 !important;
                            padding: 10px;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            text-align: center;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        }
                        
                        .stRadio [role="radiogroup"] > label:hover {
                            border-color: #4CAF50;
                            background-color: #f8f9fa;
                        }
                        
                        .stRadio [role="radiogroup"] > [data-baseweb="radio"] > div:first-child {
                            display: none;
                        }
                        
                        .stRadio [role="radiogroup"] > [data-baseweb="radio"] {
                            flex: 1;
                            margin: 0;
                        }
                        
                        .stRadio [role="radiogroup"] > [data-baseweb="radio"] > div:last-child {
                            width: 100%;
                            padding: 10px;
                            border: 2px solid #e0e0e0;
                            border-radius: 8px;
                            text-align: center;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        }
                        
                        .stRadio [role="radiogroup"] > [data-baseweb="radio"]:hover > div:last-child {
                            border-color: #4CAF50;
                            background-color: #f8f9fa;
                        }
                        
                        .stRadio [role="radiogroup"] > [data-baseweb="radio"][data-state*="selected"] > div:last-child {
                            border-color: #4CAF50;
                            background-color: #e8f5e9;
                            font-weight: bold;
                        }
                        
                        .payment-icon {
                            font-size: 24px;
                            display: block;
                            margin-bottom: 5px;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Options de paiement avec icônes
                    payment_options = [
                        {"label": "🟠 Orange Money", "value": "Orange Money"},
                        {"label": "🌊 Wave", "value": "Wave"},
                        {"label": "💵 Espèces", "value": "Espèces"}
                    ]
                    
                    # Créer des colonnes pour les options
                    cols = st.columns(3)
                    
                    # Afficher les options de paiement
                    for i, option in enumerate(payment_options):
                        with cols[i % 3]:
                            st.markdown(f"<div class='payment-option'>{option['label']}</div>", unsafe_allow_html=True)
                    
                    # Utiliser un selectbox caché pour la sélection
                    methode_paiement = st.radio(
                        "Sélectionnez une méthode de paiement",
                        [option["value"] for option in payment_options],
                        index=0,
                        format_func=lambda x: "",
                        label_visibility="collapsed",
                        horizontal=True,
                        key="payment_method_selector"
                    )
                    
                    # Afficher la méthode sélectionnée
                    selected_icon = ""
                    if methode_paiement == "Orange Money":
                        selected_icon = "🟠"
                    elif methode_paiement == "Wave":
                        selected_icon = "🌊"
                    else:
                        selected_icon = "💵"
                        
                    st.markdown(f"<div style='padding: 10px; background-color: #e8f5e9; border-radius: 5px; margin: 10px 0;'>"
                              f"Méthode sélectionnée : {selected_icon} <strong>{methode_paiement}</strong>"
                              f"</div>", unsafe_allow_html=True)
                    
                    # Informations supplémentaires selon la méthode de paiement
                    phone = ""
                    if methode_paiement in ["Orange Money", "Wave"]:
                        phone = st.text_input(
                            f"Numéro de téléphone {methode_paiement} *",
                            key=f"phone_{methode_paiement.lower().replace(' ', '_')}",
                            placeholder="Ex: 771234567"
                        )
                        
                        # Validation du format du numéro de téléphone
                        if phone:
                            # Supprimer les espaces et caractères non numériques
                            phone = ''.join(c for c in phone if c.isdigit())
                            # Vérifier que le numéro commence par 77, 76, 78, 70, 75 ou 33 et fait 9 chiffres
                            if not (phone.startswith(('77', '76', '78', '70', '75', '33')) and len(phone) == 9):
                                st.warning("⚠️ Le numéro de téléphone doit commencer par 77, 76, 78, 70, 75 ou 33 et contenir 9 chiffres.")
                                phone = ""
                    
                    # Bouton de soumission du formulaire
                    submitted = st.form_submit_button(
                        f"✅ Payer {montant:,} XOF et enregistrer l'adhérent",
                        type="primary",
                        help="Cliquez pour finaliser l'inscription et procéder au paiement"
                    )
                
                if submitted:
                    # Validation des champs obligatoires
                    if not all([nom, prenom, telephone, abonnement_type, date_fin]):
                        st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
                    else:
                        # Vérification du numéro de téléphone pour les paiements en ligne
                        if methode_paiement in ["Orange Money", "Wave"] and not phone:
                            st.error(f"❌ Veuillez entrer un numéro de téléphone pour le paiement par {methode_paiement}")
                        else:
                            # Création du dictionnaire adhérent
                            nouvel_adherent = {
                                'id': str(uuid.uuid4()),
                                'nom': nom.upper(),
                                'prenom': prenom.capitalize(),
                                'telephone': telephone,
                                'email': email,
                                'statut': statut,
                                'type_abonnement': abonnement_type,
                                'date_inscription': datetime.now().strftime('%Y-%m-%d'),
                                'date_fin_abonnement': date_fin.strftime('%Y-%m-%d'),
                                'montant_abonnement': montant,
                                'methode_paiement': methode_paiement,
                                'statut_paiement': 'en_attente'
                            }
                            
                            try:
                                # Traitement du paiement
                                payment_result = None
                                customer_info = {
                                    'first_name': prenom.capitalize(),
                                    'last_name': nom.upper(),
                                    'email': email,
                                    'phone': phone if methode_paiement in ["Orange Money", "Wave"] else telephone
                                }
                                
                                # Appel au service de paiement
                                payment_service = PaymentService()
                                payment_result = payment_service.process_payment(
                                    amount=montant,
                                    payment_method=methode_paiement.lower(),
                                    customer_info=customer_info,
                                    description=f"Abonnement {abonnement_type} - {prenom} {nom}"
                                )
                                
                                if payment_result and payment_result.get('success'):
                                    # Mise à jour des informations de paiement
                                    nouvel_adherent.update({
                                        'reference_paiement': payment_result.get('reference'),
                                        'statut_paiement': 'paye' if methode_paiement == 'Espèces' else 'en_attente',
                                        'date_paiement': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'details_paiement': json.dumps(payment_result)
                                    })
                                    
                                    # Ajout dans la base de données
                                    ajouter_adherent(conn, nouvel_adherent)
                                    
                                    # Envoi de la notification
                                    NotificationService.send_new_member_notification({
                                        'first_name': prenom.capitalize(),
                                        'last_name': nom.upper(),
                                        'email': email,
                                        'phone': telephone,
                                        'subscription_type': abonnement_type,
                                        'subscription_end_date': date_fin.strftime('%d/%m/%Y'),
                                        'payment_method': methode_paiement,
                                        'amount': f"{montant:,} XOF"
                                    })
                                    
                                    # Affichage du succès
                                    st.success("✅ Adhérent enregistré avec succès !")
                                    
                                    # Affichage des instructions de paiement si nécessaire
                                    if methode_paiement != 'Espèces':
                                        st.info(f"🔔 Un lien de paiement a été envoyé au numéro {phone}. "
                                               f"Veuillez compléter le paiement pour activer l'abonnement.")
                                    
                                    # Réinitialisation des champs
                                    st.rerun()
                                    
                                else:
                                    error_msg = payment_result.get('error', 'Erreur inconnue')
                                    st.error(f"❌ Échec du traitement du paiement : {error_msg}")
                                    
                            except Exception as e:
                                st.error(f"❌ Une erreur est survenue : {str(e)}")
                                if payment_result:
                                    st.json(payment_result)  # Afficher les détails de l'erreur
        
        def detecter_colonnes(df):
            """Détecte automatiquement les colonnes du fichier Excel"""
            colonnes_trouvees = {
                'nom': None,
                'prenom': None,
                'telephone': None,
                'email': None,
                'statut': None,
                'abonnement_type': None,
                'date_fin_abonnement': None
            }
            
            # Mapping des colonnes possibles
            mapping_possibilites = {
                'nom': ['nom', 'name', 'lastname', 'nom de famille'],
                'prenom': ['prenom', 'prénom', 'firstname', 'prenom et nom'],
                'telephone': ['telephone', 'téléphone', 'phone', 'tel', 'contact'],
                'email': ['email', 'e-mail', 'courriel', 'mail'],
                'statut': ['statut', 'status', 'etat', 'état'],
                'abonnement_type': ['abonnement', 'type abonnement', 'type_abonnement', 'forfait'],
                'date_fin_abonnement': ['date fin', 'fin abonnement', 'date expiration', 'expiration']
            }
            
            # Détection des colonnes
            colonnes_excel = [str(col).lower().strip() for col in df.columns]
            
            for champ, possibilites in mapping_possibilites.items():
                for p in possibilites:
                    if p in colonnes_excel:
                        idx = colonnes_excel.index(p)
                        colonnes_trouvees[champ] = df.columns[idx]
                        break
            
            # Détection intelligente supplémentaire
            for col in df.columns:
                col_lower = str(col).lower()
                # Si la colonne contient "@", c'est probablement un email
                if any('@' in str(x) for x in df[col].dropna().head()):
                    if not colonnes_trouvees['email']:
                        colonnes_trouvees['email'] = col
                # Si la colonne contient des numéros de téléphone
                elif any(isinstance(x, (int, float)) and len(str(int(x))) >= 8 for x in df[col].dropna().head() if pd.notna(x)):
                    if not colonnes_trouvees['telephone'] and 'date' not in col_lower:
                        colonnes_trouvees['telephone'] = col
                # Si la colonne contient des dates
                elif pd.api.types.is_datetime64_any_dtype(df[col]) or any('/' in str(x) or '-' in str(x) for x in df[col].dropna().head()):
                    if not colonnes_trouvees['date_fin_abonnement'] and 'date' in col_lower:
                        colonnes_trouvees['date_fin_abonnement'] = col
            
            return colonnes_trouvees

        with tab3:
            st.subheader("Importer des adhérents depuis Excel")
            st.info("Téléchargez votre fichier Excel. Le système essaiera de détecter automatiquement les colonnes.")
            
            uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx", "xls"])
            
            if uploaded_file is not None:
                try:
                    # Lire le fichier Excel
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
                    
                    # Aperçu des données
                    st.subheader("Aperçu des données détectées")
                    st.dataframe(df.head())
                    
                    # Détection automatique des colonnes
                    mapping_colonnes = detecter_colonnes(df)
                    
                    # Interface de mappage des colonnes
                    st.subheader("Correspondance des colonnes")
                    st.info("Vérifiez et ajustez la correspondance des colonnes si nécessaire")
                    
                    # Afficher les colonnes détectées
                    colonnes_disponibles = [""] + list(df.columns)
                    
                    # Créer des sélecteurs pour chaque champ
                    col1, col2 = st.columns(2)
                    with col1:
                        nom_col = st.selectbox("Colonne pour le Nom", 
                                            options=colonnes_disponibles,
                                            index=colonnes_disponibles.index(mapping_colonnes['nom']) if mapping_colonnes['nom'] in colonnes_disponibles else 0)
                        
                        prenom_col = st.selectbox("Colonne pour le Prénom", 
                                               options=colonnes_disponibles,
                                               index=colonnes_disponibles.index(mapping_colonnes['prenom']) if mapping_colonnes['prenom'] in colonnes_disponibles else 0)
                        
                        tel_col = st.selectbox("Colonne pour le Téléphone", 
                                            options=colonnes_disponibles,
                                            index=colonnes_disponibles.index(mapping_colonnes['telephone']) if mapping_colonnes['telephone'] in colonnes_disponibles else 0)
                        
                    with col2:
                        email_col = st.selectbox("Colonne pour l'Email", 
                                              options=colonnes_disponibles,
                                              index=colonnes_disponibles.index(mapping_colonnes['email']) if mapping_colonnes['email'] in colonnes_disponibles else 0)
                        
                        statut_col = st.selectbox("Colonne pour le Statut", 
                                               options=colonnes_disponibles,
                                               index=colonnes_disponibles.index(mapping_colonnes['statut']) if mapping_colonnes['statut'] in colonnes_disponibles else 0)
                        
                        abo_col = st.selectbox("Colonne pour le Type d'abonnement", 
                                            options=colonnes_disponibles,
                                            index=colonnes_disponibles.index(mapping_colonnes['abonnement_type']) if mapping_colonnes['abonnement_type'] in colonnes_disponibles else 0)
                        
                        date_col = st.selectbox("Colonne pour la Date de fin d'abonnement", 
                                             options=colonnes_disponibles,
                                             index=colonnes_disponibles.index(mapping_colonnes['date_fin_abonnement']) if mapping_colonnes['date_fin_abonnement'] in colonnes_disponibles else 0)
                    
                    # Vérifier les colonnes obligatoires
                    if not all([nom_col, prenom_col, tel_col]):
                        st.error("Les colonnes Nom, Prénom et Téléphone sont obligatoires")
                        st.stop()
                    else:
                        # Créer un nouveau DataFrame avec les colonnes mappées
                        data = {}
                        
                        # Mapper les colonnes avec les valeurs sélectionnées
                        if nom_col:
                            data['nom'] = df[nom_col].astype(str).str.upper()
                        if prenom_col:
                            data['prenom'] = df[prenom_col].astype(str).str.capitalize()
                        if tel_col:
                            data['telephone'] = df[tel_col].astype(str).str.strip()
                        if email_col:
                            data['email'] = df[email_col].astype(str).str.lower().str.strip()
                        if statut_col:
                            data['statut'] = df[statut_col].astype(str).str.capitalize()
                        if abo_col:
                            data['type_abonnement'] = df[abo_col].astype(str)  # Correction du nom de colonne
                        if date_col:
                            # Essayer de convertir en date
                            try:
                                data['date_fin_abonnement'] = pd.to_datetime(df[date_col], errors='coerce')
                            except:
                                data['date_fin_abonnement'] = None
                        
                        # Créer le DataFrame final
                        df = pd.DataFrame(data)
                        
                        # Remplir les valeurs manquantes
                        df['email'] = df.get('email', '')
                        df['statut'] = df.get('statut', 'Actif')
                        df['abonnement_type'] = df.get('abonnement_type', 'Non spécifié')
                        
                        # Convertir les dates si nécessaire
                        if 'date_fin_abonnement' in df.columns:
                            df['date_fin_abonnement'] = pd.to_datetime(df['date_fin_abonnement'], errors='coerce')
                        else:
                            df['date_fin_abonnement'] = pd.NaT
                        
                        # Afficher un aperçu des données transformées
                        st.subheader("Données à importer (après transformation)")
                        st.dataframe(df.head())
                        
                        # Bouton de confirmation d'importation
                        if st.button("Confirmer l'importation"):
                            try:
                                # Connexion à la base de données
                                conn = sqlite3.connect('isbisportclub.db')
                                c = conn.cursor()
                                
                                # Compter les adhérents avant l'importation
                                c.execute("SELECT COUNT(*) FROM adherents")
                                count_before = c.fetchone()[0]
                                
                                # Importer les données
                                for _, row in df.iterrows():
                                    try:
                                        # Générer un ID unique
                                        import uuid
                                        adherent_id = str(uuid.uuid4())
                                        
                                        c.execute('''
                                            INSERT INTO adherents 
                                            (id, nom, prenom, telephone, email, statut, type_abonnement, date_fin_abonnement, date_inscription)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'))
                                        ''', (
                                            adherent_id,
                                            str(row['nom']).upper() if pd.notna(row['nom']) else '',
                                            str(row['prenom']).capitalize() if pd.notna(row['prenom']) else '',
                                            str(row['telephone']) if pd.notna(row['telephone']) else '',
                                            str(row['email']) if pd.notna(row.get('email')) else '',
                                            str(row['statut']) if pd.notna(row.get('statut')) else 'Actif',
                                            str(row['type_abonnement']) if pd.notna(row.get('type_abonnement')) else 'Non spécifié',
                                            row['date_fin_abonnement'].strftime('%Y-%m-%d') if pd.notna(row.get('date_fin_abonnement')) else None
                                        ))
                                    except Exception as e:
                                        st.warning(f"Erreur lors de l'importation de {row['prenom']} {row['nom']}: {str(e)}")
                                
                                # Valider les modifications
                                conn.commit()
                                
                                # Compter les adhérents après l'importation
                                c.execute("SELECT COUNT(*) FROM adherents")
                                count_after = c.fetchone()[0]
                                
                                st.success(f"Importation réussie ! {count_after - count_before} nouveaux adhérents ont été ajoutés.")
                                
                            except Exception as e:
                                st.error(f"Une erreur est survenue lors de l'importation : {str(e)}")
                            finally:
                                if conn:
                                    conn.close()
                
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier Excel : {str(e)}")
        
        # Fermer la connexion à la base de données
        conn.close()
        
    elif selected == "📅 Séances":
        st.title("Planning des Séances")
        st.write("Gestion du planning et des inscriptions aux séances")
        
    elif selected == "💳 Abonnements":
        st.title("Gestion des Abonnements")
        st.write("Souscription et renouvellement des abonnements")
        
    elif selected == "📊 Statistiques":
        st.title("Statistiques et Rapports")
        st.write("Analyse des performances et statistiques d'utilisation")
        
        # Graphiques de statistiques
        st.subheader("Activité mensuelle")
        import numpy as np
        import pandas as pd
        
        # Données de démonstration
        data = pd.DataFrame({
            'Mois': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
            'Nouveaux adhérents': [15, 22, 18, 25, 30, 28],
            'Séances': [45, 52, 60, 65, 70, 75],
            'Revenus (x1000 XOF)': [1200, 1500, 1650, 1800, 2100, 2300]
        })
        
        # Graphique à barres
        st.bar_chart(data.set_index('Mois')[['Nouveaux adhérents', 'Séances']])
        
        # Graphique de revenus
        st.subheader("Évolution des revenus")
        st.line_chart(data.set_index('Mois')['Revenus (x1000 XOF)'])
        
        # Statistiques détaillées
        st.subheader("Détails mensuels")
        st.dataframe(data, use_container_width=True)
        with col4:
            st.metric("CA du mois", "4,250 €")
        
        # Graphiques et indicateurs
        st.subheader("Activité récente")
        # Ici vous pourriez ajouter des graphiques avec des données réelles
        
    elif selected == "Adhérents":
        st.title("👥 Gestion des adhérents")
        
        # Onglets pour la gestion des adhérents
        tab1, tab2 = st.tabs(["Liste des adhérents", "Nouvel adhérent"])
        
        with tab1:
            # Charger les données depuis la base de données
            df_adherents = pd.read_sql('SELECT * FROM adherents', conn)
            st.dataframe(df_adherents, use_container_width=True)
            
        with tab2:
            with st.form("nouvel_adherent"):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nom")
                    prenom = st.text_input("Prénom")
                    email = st.text_input("Email")
                with col2:
                    telephone = st.text_input("Téléphone")
                    type_abonnement = st.selectbox("Type d'abonnement", 
                                                 ["Mensuel", "Trimestriel", "Semestriel", "Annuel"])
                    date_inscription = st.date_input("Date d'inscription")
                
                if st.form_submit_button("Enregistrer"):
                    # Code pour enregistrer dans la base de données
                    st.success("Adhérent enregistré avec succès!")
    
    elif selected == "Séances":
        st.title("📅 Planning des séances")
        
        # Afficher le planning de la semaine
        df_seances = pd.read_sql('SELECT * FROM seances', conn)
        if df_seances.empty:
            # Si la table est vide, initialiser avec des données de démo
            df_seances = pd.DataFrame({
                'jour': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
                'horaire': ['18:00-19:30'] * 6,
                'activite': ['Fitness', 'Musculation', 'Yoga', 'CrossFit', 'HIIT', 'Cardio'],
                'coach': ['Jean D.', 'Marie L.', 'Sophie M.', 'Pierre D.', 'Karim B.', 'Emma T.'],
                'salle': ['Salle 1', 'Salle 2', 'Salle 1', 'Salle 3', 'Salle 2', 'Salle 1'],
                'places_max': [20, 15, 12, 10, 15, 20],
                'inscrits': [15, 10, 8, 8, 12, 18]
            })
            df_seances.to_sql('seances', conn, if_exists='replace', index=False)
        
        st.dataframe(df_seances, use_container_width=True)
    
    elif selected == "Abonnements":
        st.title("💳 Gestion des abonnements")
        
        # Types d'abonnements
        st.subheader("Formules d'abonnements")
        df_abonnements = pd.read_csv('abonnements/types_abonnements.csv')
        
        # Afficher les formules disponibles
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Formater l'affichage des prix
            df_abonnements['Prix (XOF)'] = df_abonnements['Prix (XOF)'].apply(lambda x: f"{int(x):,} XOF".replace(',', ' '))
            st.dataframe(df_abonnements, use_container_width=True)
        
        with col2:
            st.subheader("Souscrire à un abonnement")
            with st.form("souscription_abonnement"):
                type_abonnement = st.selectbox(
                    "Choisissez votre formule",
                    df_abonnements['Type'].tolist()
                )
                
                # Récupérer les détails de l'abonnement sélectionné
                abonnement = df_abonnements[df_abonnements['Type'] == type_abonnement].iloc[0]
                
                st.write(f"**Prix :** {abonnement['Prix (XOF)']}")
                st.write(f"**Durée :** {abonnement['Durée (mois)']} mois")
                
                telephone = st.text_input("Votre numéro de téléphone")
                
                if st.form_submit_button("Payer maintenant"):
                    if telephone:
                        # Générer une référence unique pour le paiement
                        reference = f"ABO-{str(uuid.uuid4())[:8].upper()}"
                        montant = int(abonnement['Prix (XOF)'])
                        
                        # Afficher les boutons de paiement
                        afficher_boutons_paiement(
                            montant=montant,
                            reference=reference,
                            telephone=telephone,
                            description=f"Abonnement {type_abonnement} - {abonnement['Durée (mois']} mois"
                        )
                    else:
                        st.error("Veuillez entrer votre numéro de téléphone")
    
    elif selected == "Statistiques":
        st.title("📊 Tableaux de bord")
        
        # Exemple de graphique (à remplacer par des données réelles)
        st.subheader("Fréquentation mensuelle")
        df_frequentation = pd.DataFrame({
            'Mois': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
            'Visites': [1200, 1500, 1800, 1600, 2000, 2200],
            'Nouveaux adhérents': [25, 30, 45, 35, 50, 55]
        })
        st.bar_chart(df_frequentation, x='Mois', y=['Visites', 'Nouveaux adhérents'])
    
    # Le bouton de déconnexion est maintenant géré plus haut dans le code

elif authentication_status is False:
    st.error('Nom d\'utilisateur ou mot de passe incorrect')
elif authentication_status is None:
    st.warning('Veuillez entrer vos identifiants')

# Pied de page
st.sidebar.markdown("---")
st.sidebar.info("ISBISPORTCLUB - Tous droits réservés © 2025")

# Pour exécuter l'application en local, utilisez la commande :
# streamlit run app.py
