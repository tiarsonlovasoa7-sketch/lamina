# Lamina - Gestion des audiences
# Point d'entree : configuration, navigation et orchestration des pages.
import streamlit as st
from dotenv import load_dotenv

from database import RendezVous, init_db, trouver_compte
from services.auth import logout
from services.db import get_db
from ui.components import afficher_chargement, afficher_ecran_intro, show_notification
from ui.pages import page_dashboard, page_gestion_equipe, page_historique, page_planning, page_saisie, page_validation
from ui.personal import interface_personnel
from ui.team import interface_equipe
from utils import libelle_role

load_dotenv()
init_db()

# Configuration de la page Streamlit pour une utilisation adaptee aux mobiles et ordinateurs
st.set_page_config(page_title="Lamina", layout="wide")

# PWA : metas et manifest injectees dans <head> pour rendre l'application installable
st.markdown(
    """
    <script>
    (function () {
        function ajouter(relation, href) {
            var l = document.createElement("link");
            l.rel = relation;
            l.href = href;
            document.head.appendChild(l);
        }
        function ajouterMeta(nom, contenu) {
            var m = document.createElement("meta");
            m.name = nom;
            m.content = contenu;
            document.head.appendChild(m);
        }
        ajouter("manifest", "/static/manifest.webmanifest");
        ajouter("icon", "/static/icone-192.png");
        ajouter("apple-touch-icon", "/static/icone-180.png");
        ajouterMeta("theme-color", "#C0392B");
        ajouterMeta("mobile-web-app-capable", "yes");
        ajouterMeta("apple-mobile-web-app-capable", "yes");
        ajouterMeta("apple-mobile-web-app-status-bar-style", "black-translucent");
        ajouterMeta("apple-mobile-web-app-title", "Lamina");
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Style global : titres rouges, ombre et elevation au toucher, navigation arrondie
st.markdown(
    """
    <style>
    h1, h2, h3 {
        color: #C0392B !important;
    }
    .titre-bienvenue {
        color: #9AA0A6 !important;
        font-weight: 400 !important;
    }
    .lamina-nom {
        color: #C0392B !important;
        font-weight: 700 !important;
    }
    .lamina-titre-appli {
        color: #C0392B !important;
        font-weight: 700 !important;
    }
    .titre-mode {
        color: #2563EB !important;
    }
    @keyframes lamina-cascade {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div {
        animation: lamina-cascade 0.55s ease-out backwards;
    }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.08s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.16s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.24s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.32s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(6) { animation-delay: 0.4s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(7) { animation-delay: 0.48s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(8) { animation-delay: 0.56s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(n+9) { animation-delay: 0.64s; }
    @media (prefers-reduced-motion: reduce) {
        section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div {
            animation: none !important;
        }
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        color: #2563EB !important;
    }
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] div[data-baseweb="input"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stDateInput"] div[data-baseweb="input"],
    div[data-testid="stTimeInput"] div[data-baseweb="input"] {
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stButton"] button:active,
    div[data-testid="stButton"] button:focus-visible,
    div[data-testid="stFormSubmitButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:active,
    div[data-testid="stFormSubmitButton"] button:focus-visible {
        box-shadow: 0 4px 14px rgba(49, 56, 65, 0.28);
        transform: translateY(-2px);
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTimeInput"] div[data-baseweb="input"]:focus-within {
        box-shadow: 0 4px 14px rgba(49, 56, 65, 0.28);
    }
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stDownloadButton"] button,
    button[data-testid="stPopoverButton"] {
        justify-content: flex-start !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] {
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
        border: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stContainer"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        border-radius: 16px;
        border: none !important;
    }
    section[data-testid="stSidebar"] h1 {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        margin: 0.1rem 0 0.35rem 0 !important;
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stContainer"] {
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        min-height: 2.1rem !important;
        font-size: 0.9rem !important;
        line-height: 1.15 !important;
        border-radius: 14px;
    }
    section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {
        font-size: 0.78rem !important;
        margin-bottom: 0.1rem !important;
        opacity: 0.9;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1rem !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] {
        background: #C0392B !important;
        border-color: #C0392B !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover,
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:focus-visible {
        background: #A93226 !important;
        border-color: #A93226 !important;
        box-shadow: 0 4px 14px rgba(192, 57, 43, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: #15803D !important;
        border-color: #15803D !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    button[data-testid="stBaseButton-primaryFormSubmit"]:focus-visible {
        background: #166534 !important;
        border-color: #166534 !important;
        box-shadow: 0 4px 14px rgba(21, 128, 61, 0.42) !important;
        transform: translateY(-2px) !important;
    }
    .lamina-intro {
        position: fixed;
        inset: 0;
        z-index: 1000000;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #171B21;
        animation: lamina-intro-out 0.6s ease-in-out 1.5s forwards;
        pointer-events: none;
    }
    .lamina-intro .intro-nom {
        color: #C0392B;
        font-size: 52px;
        font-weight: 700;
        letter-spacing: 2px;
        font-family: "Menlo", "Consolas", monospace;
        overflow: hidden;
        white-space: nowrap;
        border-right: 3px solid #C0392B;
        width: 0;
        animation: lamina-typing 1.2s steps(12, end) 0.15s forwards, lamina-caret 0.7s step-end infinite;
    }
    @keyframes lamina-typing {
        from { width: 0; }
        to { width: 6.2ch; }
    }
    @keyframes lamina-caret {
        0%, 100% { border-color: transparent; }
        50% { border-color: #C0392B; }
    }
    @keyframes lamina-intro-out {
        0% { opacity: 1; }
        100% { opacity: 0; visibility: hidden; }
    }
    .lamina-loader {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.5rem;
        pointer-events: none;
        background: rgba(247, 246, 242, 0.94);
        background: light-dark(rgba(247, 246, 242, 0.94), rgba(23, 27, 33, 0.94));
        animation: lamina-voile 1.4s ease forwards;
    }
    .lamina-loader::before {
        content: "Veuillez patienter s'il vous plaît";
        color: #4B5563;
        color: light-dark(#4B5563, #C7CDD6);
        font-size: 1.05rem;
        font-weight: 500;
        letter-spacing: 0.01em;
        text-align: center;
        white-space: nowrap;
        animation: lamina-fade-up 0.35s ease 0.05s forwards;
    }
    .lamina-loader::after {
        content: "";
        width: 46px;
        height: 46px;
        border: 4px solid rgba(192, 57, 43, 0.18);
        border-top-color: #C0392B;
        border-right-color: #C0392B;
        border-radius: 50%;
        box-shadow: 0 0 14px rgba(192, 57, 43, 0.25);
        animation: lamina-spin 0.8s linear infinite, lamina-fade-in 0.35s ease 0.12s backwards;
    }
    @keyframes lamina-spin {
        to { transform: rotate(360deg); }
    }
    @keyframes lamina-fade-in {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    @keyframes lamina-fade-up {
        0% { opacity: 0; transform: translateY(6px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes lamina-voile {
        0% { opacity: 1; }
        65% { opacity: 1; }
        100% { opacity: 0; visibility: hidden; }
    }
    @media (prefers-reduced-motion: reduce) {
        .lamina-loader {
            animation-duration: 0.001s !important;
            animation-fill-mode: forwards !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }
    }
    /* ------- Adaptation mobile ------- */
    @media (max-width: 700px) {
        section[data-testid="stMain"] [data-testid="stMainBlockContainer"] {
            padding: 0.6rem 0.9rem 2.5rem !important;
        }
        section[data-testid="stMain"] [data-testid="stVerticalBlock"] {
            gap: 0.55rem !important;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button {
            min-height: 3rem !important;
            padding: 0.5rem 0.85rem !important;
            font-size: 1rem !important;
            line-height: 1.25 !important;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-testid="stTimeInput"] div[data-baseweb="input"],
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 2.9rem !important;
        }
        [data-testid="stColumn"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
        }
        section[data-testid="stMain"] h1 {
            font-size: 1.5rem !important;
        }
        section[data-testid="stMain"] h3 {
            font-size: 1.05rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialisation de l etat de session de l application
if "mode" not in st.session_state:
    st.session_state.mode = None
if "user" not in st.session_state:
    st.session_state.user = None
if "tenant_db" not in st.session_state:
    st.session_state.tenant_db = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Tableau de bord"
if "just_logged_in" not in st.session_state:
    st.session_state.just_logged_in = False
if "editing_rdv_id" not in st.session_state:
    st.session_state.editing_rdv_id = None
if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

if "flash_msg" not in st.session_state:
    st.session_state.flash_msg = None
if "flash_type" not in st.session_state:
    st.session_state.flash_type = "success"

# Affiche l indicateur de chargement au debut de la nouvelle page lors d un changement de page ou onglet
if st.session_state.pop("_page_chargement", False):
    st.markdown('<div class="lamina-loader" id="laminaLoader"></div>', unsafe_allow_html=True)

# Ecran de lancement unique : "Lamina" s'ecrit au clavier au tout debut de session
if st.session_state.get("intro_jouee") is None:
    st.session_state.intro_jouee = True
    afficher_ecran_intro()

# Affichage des messages flash en attente
if st.session_state.flash_msg:
    show_notification(st.session_state.flash_msg, st.session_state.flash_type)
    st.session_state.flash_msg = None

# Ecran de bienvenue avec le choix du mode d utilisation
if st.session_state.user is None and st.session_state.mode is None:
    st.markdown("""
        <style>
        [data-testid="stMain"] [data-testid="stButton"] {
            display: flex;
            justify-content: center;
        }
        [data-testid="stMain"] [data-testid="stButton"] button,
        [data-testid="stMain"] .stButton button,
        [data-testid="stMain"] button[data-testid^="stBaseButton-"] {
            min-height: 4.5rem !important;
            width: min(22rem, 90%) !important;
            padding: 0.7rem 1.1rem !important;
            text-align: center !important;
            cursor: pointer !important;
        }
        [data-testid="stMain"] button p {
            flex: 0 0 100% !important;
            max-width: 100% !important;
            display: block !important;
            white-space: normal !important;
        }
        [data-testid="stMain"] button p:first-of-type {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            line-height: 1.25 !important;
            margin: 0 0 0.3rem 0 !important;
        }
        [data-testid="stMain"] button p:last-of-type {
            font-size: 0.95rem !important;
            line-height: 1.3 !important;
            margin: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    st.markdown('<h1 class="titre-bienvenue" style="text-align:center;">Bienvenue sur l\'application <span class="lamina-nom">Lamina</span></h1>', unsafe_allow_html=True)
    st.caption("Choisissez votre mode d'utilisation", text_alignment="center")

    st.space("medium")

    col_gauche, col_milieu, col_droite = st.columns([1, 2, 1])

    with col_milieu:
        if st.button(":blue[**Mode personnel**]\n\nGérer votre propre programme", key="mode_personnel", icon=":material/person:", width="stretch", type="primary"):
            st.session_state.mode = "personnel"
            afficher_chargement()

        st.space("small")

        if st.button(":blue[**Mode équipe**]\n\nAvec plusieurs personnes selon votre entreprise", key="mode_equipe", icon=":material/apartment:", width="stretch"):
            st.session_state.mode = "equipe"
            afficher_chargement()

    st.stop()

# Interface pour les utilisateurs non connectes selon le mode choisi
if st.session_state.user is None:
    st.markdown('<h1 class="lamina-titre-appli" style="text-align:center;">Lamina</h1>', unsafe_allow_html=True)
    if st.session_state.mode == "personnel":
        st.caption("Espace personnel : une seule personne, ses rendez-vous", text_alignment="center")
        interface_personnel()
    elif st.session_state.mode == "equipe":
        st.caption("Espace équipe : un Responsable et des Assistant(e)s", text_alignment="center")
        interface_equipe()
    st.stop()

# Interface pour les utilisateurs authentifies
if st.session_state.user is not None:
    user = st.session_state.user
    db = get_db()

    try:
        # Recuperation des statistiques globales
        nb_en_attente = db.query(RendezVous).filter(RendezVous.statut == "En attente").count()

        # Barre latérale d informations et de navigation
        st.sidebar.title("Lamina")
        st.sidebar.space("small")
        with st.sidebar.container():
            st.write(f"**{user['nom']}**")
            if user['role'] == "Personnel":
                st.caption("Mode personnel")
            else:
                compte_actif = trouver_compte(chemin_db=st.session_state.get("tenant_db")) if st.session_state.get("tenant_db") else None
                if compte_actif:
                    st.caption(f"Entreprise : {compte_actif.nom}")
                st.caption(f"Rôle : {libelle_role(user['role'])}")
            if user['role'] == "Directeur" and nb_en_attente > 0:
                st.markdown(f":orange[{nb_en_attente} demande(s) en attente]")

        st.sidebar.divider()
        st.sidebar.subheader("Navigation")

        # Dynamic navigation options based on user role, avec libelles de taille stable
        label_saisie_rdv = "Nouvelle demande de RDV"
        if user['role'] in ("Directeur", "Personnel"):
            label_saisie_rdv = "Ajouter un rendez-vous"

        if user['role'] == "Directeur":
            nav_options = [
                ("Tableau de bord", "Tableau de bord", ":material/dashboard:"),
                ("Saisir une demande", label_saisie_rdv, ":material/event_note:"),
                ("Validation des Audiences", "Validation des Audiences", ":material/fact_check:"),
                ("Planning et Briefs", "Planning et Briefs", ":material/calendar_month:"),
                ("Historique et Exports", "Historique et Exports", ":material/history:"),
                ("Gérer l'équipe", "Gérer l'équipe", ":material/group:")
            ]
        else:
            nav_options = [
                ("Tableau de bord", "Tableau de bord", ":material/dashboard:"),
                ("Saisir une demande", label_saisie_rdv, ":material/event_note:"),
                ("Planning et Briefs", "Planning et Briefs", ":material/calendar_month:"),
                ("Historique et Exports", "Historique et Exports", ":material/history:")
            ]

        # Verification de la cle de navigation valide
        valid_keys = [item[0] for item in nav_options]
        if st.session_state.current_page not in valid_keys:
            st.session_state.current_page = "Tableau de bord"

        # Rendu des boutons de navigation avec animation au changement d onglet
        for page_key, label, icone in nav_options:
            is_active = (st.session_state.current_page == page_key)
            btn_type = "primary" if is_active else "secondary"
            if st.sidebar.button(label, key=f"nav_{page_key}", type=btn_type, icon=icone, width="stretch"):
                if st.session_state.current_page != page_key:
                    st.session_state.current_page = page_key
                st.session_state.editing_rdv_id = None
                afficher_chargement()

        # Bouton de deconnexion dans son propre espace, ecarte en bas de la barre laterale
        st.sidebar.space("large")
        if st.sidebar.button("Se déconnecter", icon=":material/logout:", width="stretch", type="tertiary", key="btn_deconnexion"):
            st.session_state.flash_msg = "Déconnexion effectuée avec succès."
            st.session_state.flash_type = "success"
            logout()
            db.close()
            afficher_chargement()

        # Affichage des notifications d accueil a la premiere connexion
        if st.session_state.just_logged_in:
            if user['role'] == "Directeur":
                if nb_en_attente > 0:
                    show_notification(f"Connexion établie. Vous avez {nb_en_attente} demande(s) en attente.")
                else:
                    show_notification("Connexion établie. Aucune nouvelle demande en attente.")
            elif user['role'] == "Personnel":
                show_notification("Bienvenue en mode personnel. Vous gérez directement vos rendez-vous.")
            else:
                show_notification("Connexion établie. Espace assistant(e) opérationnel.")
            st.session_state.just_logged_in = False

        menu = st.session_state.current_page

        # Dispatcher vers la page demandee
        if menu == "Tableau de bord":
            page_dashboard(user, db)

        elif menu == "Saisir une demande":
            page_saisie(user, db)

        elif menu == "Validation des Audiences" and user['role'] == "Directeur":
            page_validation(user, db)

        elif menu == "Gérer l'équipe" and user['role'] == "Directeur":
            page_gestion_equipe(user, db)

        elif menu == "Planning et Briefs":
            page_planning(user, db)

        elif menu == "Historique et Exports":
            page_historique(user, db)

    finally:
        db.close()