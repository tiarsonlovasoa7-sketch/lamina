# Authentification : connexion, deconnexion et reinitialisation du mot de passe
import secrets
from datetime import datetime, timedelta

import streamlit as st

from database import (Utilisateur, hash_password, verify_password, verifier_code_reset,
                      creer_session_sur, trouver_compte)
from services.db import get_db
from services.emails import envoyer_email_auto, template_code_reset
from utils import clean_str, validate_password_strength


def _verifier_ancien_mdp(chemin_db, email, ancien_mdp):
    """Verifie l'ancien mot de passe d'un utilisateur d'un compte."""
    tdb = None
    try:
        tdb = creer_session_sur(chemin_db)
        if not email:
            util = tdb.query(Utilisateur).first()
        else:
            util = tdb.query(Utilisateur).filter(Utilisateur.email == email).first()
        if util and util.mot_de_passe_hash:
            ok, _ = verify_password(ancien_mdp, util.mot_de_passe_hash)
            return ok
        return False
    except Exception:
        return False
    finally:
        if tdb:
            tdb.close()


def login(email_saisi, password_saisi):
    """Authentification avec protection contre le brute-force et migration de hachage."""
    email_clean = clean_str(email_saisi).lower()
    pass_clean = clean_str(password_saisi)

    # Verification de la limitation de tentatives de connexion
    if "failed_attempts" not in st.session_state:
        st.session_state.failed_attempts = 0
    if "lockout_time" not in st.session_state:
        st.session_state.lockout_time = None

    # Verification du blocage temporaire
    if st.session_state.lockout_time:
        if datetime.now() < st.session_state.lockout_time:
            temps_restant = int((st.session_state.lockout_time - datetime.now()).total_seconds())
            return False, f"Compte temporairement bloqué. Réessayez dans {temps_restant} secondes."
        else:
            st.session_state.lockout_time = None
            st.session_state.failed_attempts = 0

    db = get_db()
    try:
        # Recherche de l utilisateur en base
        user = db.query(Utilisateur).filter(Utilisateur.email == email_clean).first()

        if not user:
            st.session_state.failed_attempts += 1
            if st.session_state.failed_attempts >= 5:
                st.session_state.lockout_time = datetime.now() + timedelta(seconds=60)
            return False, "Adresse e-mail introuvable."

        # Verification du mot de passe avec support PBKDF2 et Sha256 ancien
        is_valid, needs_rehash = verify_password(pass_clean, user.mot_de_passe_hash)

        if is_valid:
            # Migration automatique des anciens mots de passe vers PBKDF2
            if needs_rehash:
                user.mot_de_passe_hash = hash_password(pass_clean)
                db.commit()

            # Reinitialisation du compteur d echecs
            st.session_state.failed_attempts = 0
            st.session_state.lockout_time = None

            # Stockage des informations de session utilisateur
            st.session_state.user = {
                "id": user.id,
                "nom": user.nom_complet,
                "email": user.email,
                "role": user.role
            }
            st.session_state.just_logged_in = True
            return True, "Connexion réussie."
        else:
            st.session_state.failed_attempts += 1
            if st.session_state.failed_attempts >= 5:
                st.session_state.lockout_time = datetime.now() + timedelta(seconds=60)
            return False, "Mot de passe incorrect."
    finally:
        db.close()


def logout():
    """Deconnexion reinitialisant la session."""
    st.session_state.user = None
    st.session_state.mode = None
    st.session_state.tenant_db = None
    st.session_state.current_page = "Tableau de bord"
    st.session_state.just_logged_in = False
    st.session_state.editing_rdv_id = None
    st.session_state.perso_selection_nom = None
    st.session_state.perso_selection_chemin = None
    st.session_state.equipe_selection_chemin = None
    st.session_state.equipe_selection_nom = None
    st.session_state.equipe_selection_membre = None
    st.session_state.equipe_selection_libelle = None
    st.session_state.perso_action = None
    st.session_state.action_membre = None
    st.session_state.equipe_action = None


def envoyer_code_reset(clean_mail, mode=None, entreprise=None):
    """Envoie un code de reinitialisation au compte proprietaire de l'e-mail.

    Les utilisateurs resident dans la base de donnees de leur compte, pas dans
    l'annuaire : on reperce d'abord le bon compte (par e-mail en mode personnel,
    par nom d'entreprise en mode equipe pour couvrir aussi les assistants),
    puis on ouvre sa base pour y chercher l'utilisateur.
    """
    compte_choisi = None
    if entreprise:
        compte_choisi = trouver_compte(mode="equipe", nom=clean_str(entreprise))
    elif mode:
        compte_choisi = trouver_compte(mode=mode, email=clean_mail)

    with st.spinner("Génération du code cryptographique sécurisé..."):
        if not compte_choisi:
            return "Aucun compte associé à cet e-mail.", "error"
        db = creer_session_sur(compte_choisi.chemin_db)
        try:
            user_to_reset = db.query(Utilisateur).filter(Utilisateur.email == clean_mail).first()
            if not user_to_reset:
                return "Aucun compte associé à cet e-mail.", "error"
            code_genere = f"{secrets.randbelow(900000) + 100000}"
            sujet, corps = template_code_reset(code_genere)
            ok, err = envoyer_email_auto(clean_mail, sujet, corps)
            if ok:
                user_to_reset.code_reset = hash_password(code_genere)
                user_to_reset.code_reset_expire = datetime.now() + timedelta(minutes=15)
                db.commit()
                st.session_state.reset_email = clean_mail
                st.session_state.reset_tenant_db = compte_choisi.chemin_db
                return "Code de vérification envoyé par e-mail avec succès.", "success"
            return f"Erreur d'envoi de l'e-mail : {err}", "error"
        finally:
            db.close()


def confirmer_reset(code_saisi, new_pass, new_pass_conf):
    """Valide la confirmation de reinitialisation du mot de passe."""
    clean_code = clean_str(code_saisi)
    clean_new_pass = clean_str(new_pass)
    clean_mail = clean_str(st.session_state.get("reset_email", "")).lower()

    if not clean_mail:
        return "Veuillez d'abord demander l'envoi d'un code ci-dessus.", "error"
    if not clean_code or not clean_new_pass:
        return "Veuillez remplir le code et le nouveau mot de passe.", "error"
    if clean_new_pass != clean_str(new_pass_conf):
        return "Les deux mots de passe ne correspondent pas.", "error"
    is_strong, msg_strength = validate_password_strength(clean_new_pass)
    if not is_strong:
        return msg_strength, "error"

    if st.session_state.get("reset_tenant_db"):
        st.session_state.tenant_db = st.session_state.reset_tenant_db

    with st.spinner("Mise à jour du mot de passe..."):
        db = get_db()
        try:
            user_to_update = db.query(Utilisateur).filter(Utilisateur.email == clean_mail).first()
            if not user_to_update:
                return "Compte introuvable.", "error"
            if not user_to_update.code_reset:
                return "Aucun code de réinitialisation actif. Veuillez demander un nouveau code.", "error"
            if user_to_update.code_reset_expire and user_to_update.code_reset_expire < datetime.now():
                return "Le code de vérification a expiré. Veuillez en demander un nouveau.", "error"
            if not verifier_code_reset(clean_code, user_to_update.code_reset):
                return "Code de vérification incorrect.", "error"
            user_to_update.mot_de_passe_hash = hash_password(clean_new_pass)
            user_to_update.code_reset = None
            user_to_update.code_reset_expire = None
            db.commit()
            return "Mot de passe réinitialisé avec succès. Vous pouvez vous connecter.", "success"
        finally:
            db.close()