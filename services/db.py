# Acces a la base de donnees du compte actif
import streamlit as st

from database import SessionLocal, creer_session_sur


def get_db():
    """Obtient une session de base de donnees du compte actif."""
    chemin_tenant = st.session_state.get("tenant_db")
    if chemin_tenant:
        return creer_session_sur(chemin_tenant)
    return SessionLocal()