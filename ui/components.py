# Composants d'affichage reutilisables
import streamlit as st


def show_notification(message, type_notif="success"):
    """Affiche des notifications a l'utilisateur."""
    if type_notif == "error":
        st.error(message)
    elif type_notif == "warning":
        st.warning(message)
    else:
        st.toast(message)


def afficher_chargement():
    """Affiche l'indicateur de chargement lors d'un changement de page ou d'onglet."""
    st.session_state["_page_chargement"] = True
    st.rerun()


def page_header(titre, sous_titre=None):
    """Affiche un entete de page avec les composants natifs Streamlit."""
    st.title(titre, text_alignment="center")
    if sous_titre:
        st.caption(sous_titre, text_alignment="center")


def section_title(texte):
    """Affiche un sous-titre de section."""
    st.subheader(texte, text_alignment="center")


def badge_statut(statut):
    """Genere un texte colore representant un statut."""
    libelles = {
        "Confirme": "Confirmé",
        "En attente": "En attente",
        "Refuse": "Refusé"
    }
    couleurs = {
        "Confirme": "green",
        "En attente": "orange",
        "Refuse": "red"
    }
    couleur = couleurs.get(statut, "gray")
    libelle = libelles.get(statut, statut)
    return f":{couleur}[{libelle}]"


def badge_priorite(priorite):
    """Genere un texte colore representant une priorite."""
    mapping = {
        "Haute": "red",
        "Moyenne": "blue",
        "Basse": "gray"
    }
    couleur = mapping.get(priorite, "gray")
    return f":{couleur}[{priorite}]"


def stat_card(label, valeur):
    """Affiche une carte de statistique du tableau de bord."""
    with st.container(border=True):
        st.metric(label, valeur)


def styler_champs_login():
    """Colore les libelles de champs sur les ecrans de connexion."""
    st.markdown(
        """
        <style>
        [data-testid="stWidgetLabel"] {
            color: #2563EB !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def afficher_ecran_intro():
    """Affiche l'ecran de lancement : "Lamina" s'ecrit au clavier en 2 s, au theme de l'app."""
    st.markdown(
        """
        <style>
        .lamina-intro {
            position: fixed;
            inset: 0;
            z-index: 1000000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #F7F6F2;
            animation: lamina-intro-out 0.6s ease-in-out 1.4s forwards;
            pointer-events: none;
        }
        .lamina-intro.theme-sombre {
            background: #171B21;
        }
        .lamina-intro .intro-nom {
            color: #C0392B;
            font-size: 54px;
            font-weight: 700;
            letter-spacing: 2px;
            font-family: "Menlo", "Consolas", monospace;
            overflow: hidden;
            white-space: nowrap;
            border-right: 3px solid #C0392B;
            padding-right: 0.5ch;
            width: 0;
            animation: lamina-typing 1.2s steps(6, end) 0.1s forwards, lamina-caret 0.6s step-end 2 both;
        }
        @keyframes lamina-typing {
            from { width: 0; }
            to { width: 6.4ch; }
        }
        @keyframes lamina-caret {
            0%, 100% { border-color: transparent; }
            50% { border-color: #C0392B; }
        }
        @keyframes lamina-intro-out {
            0% { opacity: 1; }
            100% { opacity: 0; visibility: hidden; }
        }
        </style>
        <div class="lamina-intro">
            <div class="intro-nom">Lamina</div>
        </div>
        """,
        unsafe_allow_html=True
    )