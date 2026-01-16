import streamlit as st
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

# Credentials sécurisés (depuis .env)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def hash_password(password):
    """Hash le mot de passe avec SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    """Vérifie les identifiants"""
    return (username == ADMIN_USERNAME and 
            password == ADMIN_PASSWORD)

def init_auth_session():
    """Initialise l'état d'authentification"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None

def show_login_page():
    """Affiche la page de login"""
    st.set_page_config(
        page_title="ISBISPORTCLUB - Connexion",
        page_icon="🏋️",
        layout="centered"
    )
    
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 40px;
            border-radius: 10px;
            background-color: #f0f2f6;
        }
        h1 { 
            color: #1a4d2e;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("🏋️ ISBISPORTCLUB")
    st.markdown("### Gestion du Club Sportif")
    st.markdown("---")
    
    with st.form("login_form"):
        st.markdown("#### Connexion Gérant")
        username = st.text_input(
            "Nom d'utilisateur",
            placeholder="Entrez votre identifiant",
            help="Fourni par l'administrateur"
        )
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Entrez votre mot de passe",
            help="Fourni par l'administrateur"
        )
        
        submitted = st.form_submit_button(
            "🔓 Se connecter",
            use_container_width=True
        )
        
        if submitted:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Connexion réussie !")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    **Contact Support** :
    - 📧 Email : isbisportclub@gmail.com
    - 📱 Téléphone : +221 76 455 4434
    """)

def require_login(func):
    """Décorateur pour protéger les pages"""
    def wrapper():
        init_auth_session()
        if not st.session_state.authenticated:
            show_login_page()
            st.stop()
        return func()
    return wrapper

def logout():
    """Déconnecte l'utilisateur"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()
