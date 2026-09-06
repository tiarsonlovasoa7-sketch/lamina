# Dialogues de confirmation et callbacks associes
import streamlit as st

from database import Compte, SessionLocal, Utilisateur, creer_session_sur, supprimer_compte
from ui.components import afficher_chargement, show_notification


def _fermer_menu_fixer_action(cle_menu, type_action, action):
    """Ferme un popover menu et fixe l'action (appele depuis on_click)."""
    if cle_menu:
        st.session_state[cle_menu] = False
    if type_action == "perso":
        st.session_state.perso_action = action
    else:
        st.session_state.action_membre = action


def _annuler_action_perso():
    st.session_state.perso_action = None


def _annuler_action_membre():
    st.session_state.action_membre = None


@st.dialog("Supprimer l'espace personnel", width="small", icon=":material/person_remove:", on_dismiss=_annuler_action_perso)
def dialog_supprimer_compte_perso(compte_id, compte_nom):
    st.markdown(
        f"<p style='text-align:center;color:#6b7280;font-size:1.05rem;font-weight:500;'>"
        f"Cette action supprimera définitivement l'espace personnel « {compte_nom} » et toutes ses données.</p>",
        unsafe_allow_html=True
    )
    col_conf, col_annul = st.columns(2)
    with col_conf:
        if st.button("Confirmer la suppression", key=f"perso_conf_del_{compte_id}", icon=":material/delete_forever:", type="secondary", width="stretch"):
            with st.spinner("Suppression du compte..."):
                _, erreur = supprimer_compte(compte_id)
            if erreur:
                show_notification(f"Erreur lors de la suppression : {erreur}", type_notif="error")
            else:
                st.session_state.perso_action = None
                st.session_state.flash_msg = f"Espace personnel {compte_nom} supprimé."
                st.session_state.flash_type = "success"
                afficher_chargement()
    with col_annul:
        if st.button("Annuler", key=f"perso_annuler_del_{compte_id}", icon=":material/close:", width="stretch"):
            st.session_state.perso_action = None
            afficher_chargement()


@st.dialog("Supprimer le compte de l'équipe", width="small", icon=":material/person_remove:", on_dismiss=_annuler_action_membre)
def dialog_supprimer_membre(membre_id, nom_complet):
    tenant_db = st.session_state.get("tenant_db")
    tdb = creer_session_sur(tenant_db) if tenant_db else SessionLocal()
    try:
        membre = tdb.query(Utilisateur).filter(Utilisateur.id == membre_id).first()
        if membre is None:
            st.markdown(
                "<p style='text-align:center;color:#6b7280;font-size:1.05rem;font-weight:500;'>"
                "Ce membre n'existe plus.</p>",
                unsafe_allow_html=True
            )
            if st.button("Fermer", icon=":material/close:", width="stretch"):
                st.session_state.action_membre = None
                afficher_chargement()
        else:
            st.markdown(
                f"<p style='text-align:center;color:#6b7280;font-size:1.05rem;font-weight:500;'>"
                f"Cette action supprimera définitivement le compte de {nom_complet} de l'équipe.</p>",
                unsafe_allow_html=True
            )
            col_conf, col_annul = st.columns(2)
            with col_conf:
                if st.button("Confirmer la suppression", key=f"conf_del_{membre_id}", icon=":material/delete_forever:", type="secondary", width="stretch"):
                    with st.spinner("Suppression du compte..."):
                        tdb.delete(membre)
                        tdb.commit()
                    st.session_state.action_membre = None
                    st.session_state.flash_msg = f"Compte {nom_complet} supprimé de l'équipe."
                    st.session_state.flash_type = "success"
                    afficher_chargement()
            with col_annul:
                if st.button("Annuler", key=f"annuler_del_{membre_id}", icon=":material/close:", width="stretch"):
                    st.session_state.action_membre = None
                    afficher_chargement()
    finally:
        tdb.close()