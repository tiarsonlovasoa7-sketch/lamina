# Interfaces de connexion et de gestion du mode personnel
import streamlit as st

from database import Compte, SessionLocal, Utilisateur, creer_compte, creer_session_sur, generer_chemin_base, hash_password, lister_comptes, trouver_compte
from services.auth import _verifier_ancien_mdp, confirmer_reset, envoyer_code_reset, login
from ui.components import afficher_chargement, section_title, show_notification, styler_champs_login
from ui.dialogs import _annuler_action_perso, _fermer_menu_fixer_action, dialog_supprimer_compte_perso
from utils import clean_str, sanitize_text, validate_password_strength


@st.fragment
def _section_liste_comptes_perso():
    """Liste des espaces personnels + panneau d'action."""
    comptes = lister_comptes(mode="personnel")
    if not comptes:
        st.info("Aucun espace personnel créé pour le moment. Créez le vôtre dans l'onglet « Créer mon espace ».")
    else:
        styler_champs_login()
        if "perso_action" not in st.session_state:
            st.session_state.perso_action = None
        for compte in comptes:
            col_bouton, col_menu = st.columns([4, 1], vertical_alignment="center")
            with col_bouton:
                if st.button(f"{compte.nom}", key=f"perso_{compte.id}", icon=":material/account_circle:", width="stretch"):
                    st.session_state.perso_selection_nom = compte.nom
                    st.session_state.perso_selection_chemin = compte.chemin_db
                    afficher_chargement()
            with col_menu:
                with st.popover("", icon=":material/more_vert:", key=f"perso_menu_{compte.id}", on_change="rerun", width="stretch"):
                    st.button("Modifier le mot de passe", key=f"perso_action_mdp_{compte.id}", icon=":material/password:", width="stretch",
                              on_click=lambda cid=compte.id, cmenu=f"perso_menu_{compte.id}": _fermer_menu_fixer_action(cmenu, "perso", ("mdp", cid)))
                    st.button("Supprimer le compte", key=f"perso_action_del_{compte.id}", icon=":material/delete:", width="stretch",
                              on_click=lambda cid=compte.id, cmenu=f"perso_menu_{compte.id}": _fermer_menu_fixer_action(cmenu, "perso", ("del", cid)))

        # Panneau d'action du menu d'un espace personnel
        action = st.session_state.perso_action
        if action:
            act, cid = action
            session_dir = SessionLocal()
            try:
                compte_act = session_dir.query(Compte).filter(Compte.id == cid).first()
            finally:
                session_dir.close()
            if compte_act is None:
                st.session_state.perso_action = None
            elif act == "mdp":
                with st.container(border=True):
                    section_title(f"Modifier le mot de passe — {compte_act.nom}")
                    with st.form(f"perso_form_mdp_{cid}"):
                        ancien_mdp = st.text_input("Ancien mot de passe", type="password", placeholder="Saisissez l'ancien mot de passe")
                        nouveau_mdp = st.text_input("Nouveau mot de passe (8 caractères min)", type="password", placeholder="Saisissez le nouveau mot de passe")
                        nouveau_mdp_conf = st.text_input("Confirmer le nouveau mot de passe", type="password", placeholder="Confirmez le nouveau mot de passe")
                        btn_valider = st.form_submit_button("Valider le nouveau mot de passe", icon=":material/save:")
                        if btn_valider:
                            pass_clean = clean_str(nouveau_mdp)
                            old_clean = clean_str(ancien_mdp)
                            if not old_clean or not pass_clean or not clean_str(nouveau_mdp_conf):
                                show_notification("Veuillez remplir tous les champs.", type_notif="error")
                            elif pass_clean != clean_str(nouveau_mdp_conf):
                                show_notification("Les mots de passe ne correspondent pas.", type_notif="error")
                            elif not _verifier_ancien_mdp(compte_act.chemin_db, compte_act.email, old_clean):
                                show_notification("L'ancien mot de passe est incorrect.", type_notif="error")
                            else:
                                is_strong, msg_strength = validate_password_strength(pass_clean)
                                if not is_strong:
                                    show_notification(msg_strength, type_notif="error")
                                else:
                                    tdb = creer_session_sur(compte_act.chemin_db)
                                    try:
                                        util = tdb.query(Utilisateur).filter(Utilisateur.email == compte_act.email).first()
                                        if util is None:
                                            util = tdb.query(Utilisateur).first()
                                        if util:
                                            util.mot_de_passe_hash = hash_password(pass_clean)
                                            tdb.commit()
                                    finally:
                                        tdb.close()
                                    st.session_state.perso_action = None
                                    st.session_state.flash_msg = f"Le mot de passe de {compte_act.nom} a été modifié."
                                    st.session_state.flash_type = "success"
                                    afficher_chargement()
                    st.button("Annuler", key=f"perso_annuler_mdp_{cid}", icon=":material/close:",
                              on_click=_annuler_action_perso)
            elif act == "del":
                dialog_supprimer_compte_perso(cid, compte_act.nom)


def interface_personnel():
    """Interface de connexion pour le mode personnel."""
    col_gauche, col_milieu, col_droite = st.columns([1, 1, 1])
    with col_milieu:
        if st.button("Retour au choix du mode", icon=":material/arrow_back:", width="stretch"):
            st.session_state.mode = None
            afficher_chargement()
    st.space("small")
    styler_champs_login()

    with st.columns([1, 3, 1])[1]:
        with st.container(border=True):
            tab_connexion, tab_creation, tab_reset = st.tabs(["Connexion", "Créer mon espace", "Mot de passe oublié"])

            # Connexion a un espace personnel existant
            with tab_connexion:
                section_title("Accéder à votre espace")
                st.write("Sélectionnez votre espace personnel, puis saisissez votre e-mail et votre mot de passe.")

                # Activation du compte selectionne depuis l annuaire
                if "perso_selection_nom" not in st.session_state:
                    st.session_state.perso_selection_nom = None

                if not st.session_state.perso_selection_nom:
                    _section_liste_comptes_perso()
                else:
                    compte_nom = st.session_state.perso_selection_nom
                    compte_chemin = st.session_state.perso_selection_chemin
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        if st.button("Changer de compte", icon=":material/swap_horiz:", width="stretch"):
                            st.session_state.perso_selection_nom = None
                            st.session_state.perso_selection_chemin = None
                            afficher_chargement()
                    with col_info2:
                        st.caption(f"Compte sélectionné : {compte_nom}")

                    styler_champs_login()
                    with st.form("login_perso_mdp"):
                        email_input = st.text_input("Adresse e-mail", placeholder="Entrez votre e-mail")
                        password_input = st.text_input("Mot de passe", type="password", placeholder="Saisissez votre mot de passe")
                        btn_connexion = st.form_submit_button("Se connecter", type="primary", icon=":material/login:")
                        if btn_connexion:
                            email_clean = clean_str(email_input).lower()
                            if not email_clean or not clean_str(password_input):
                                show_notification("Veuillez remplir votre e-mail et votre mot de passe.", type_notif="error")
                            else:
                                st.session_state.tenant_db = compte_chemin
                                with st.spinner("Vérification sécurisée des identifiants..."):
                                    succes, message = login(email_clean, password_input)
                                if succes:
                                    st.session_state.perso_selection_nom = None
                                    st.session_state.perso_selection_chemin = None
                                    st.session_state.flash_msg = "Connexion réussie. Bienvenue dans votre espace personnel."
                                    st.session_state.flash_type = "success"
                                    afficher_chargement()
                                else:
                                    show_notification(f"Échec de connexion : {message}", type_notif="error")

            # Creation d un nouvel espace personnel avec sa propre base
            with tab_creation:
                section_title("Créer votre espace personnel")
                with st.form("register_form_perso"):
                    nom = st.text_input("Nom", placeholder="Entrez votre nom de famille")
                    prenom = st.text_input("Prénom", placeholder="Entrez votre prénom")
                    email_reg = st.text_input("Adresse e-mail", placeholder="Entrez votre e-mail")
                    pass_reg = st.text_input("Mot de passe (8 caractères min)", type="password", placeholder="Saisissez votre mot de passe")
                    pass_confirm = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmez votre mot de passe")

                    if st.form_submit_button("Créer mon espace", icon=":material/add_circle:"):
                        email_clean = clean_str(email_reg).lower()
                        pass_clean = clean_str(pass_reg)
                        nom_clean = sanitize_text(nom)
                        prenom_clean = sanitize_text(prenom)

                        if not nom_clean or not prenom_clean or not email_clean or not pass_clean:
                            show_notification("Veuillez remplir tous les champs.", type_notif="error")
                        elif pass_clean != clean_str(pass_confirm):
                            show_notification("Les mots de passe ne correspondent pas.", type_notif="error")
                        else:
                            is_strong, msg_strength = validate_password_strength(pass_clean)
                            if not is_strong:
                                show_notification(msg_strength, type_notif="error")
                            elif trouver_compte(mode="personnel", email=email_clean):
                                show_notification("Un espace personnel existe déjà avec cet e-mail.", type_notif="error")
                            else:
                                with st.spinner("Création de votre espace sécurisé..."):
                                    nom_complet = f"{nom_clean} {prenom_clean}"
                                    chemin = generer_chemin_base(email_clean)
                                    compte, erreur = creer_compte("personnel", nom_complet, chemin, email=email_clean)
                                    if erreur:
                                        show_notification(f"Erreur lors de la création : {erreur}", type_notif="error")
                                    else:
                                        tdb = creer_session_sur(chemin)
                                        try:
                                            tdb.add(Utilisateur(
                                                nom_complet=nom_complet,
                                                email=email_clean,
                                                mot_de_passe_hash=hash_password(pass_clean),
                                                role="Personnel"
                                            ))
                                            tdb.commit()
                                            utilisateur_db = tdb.query(Utilisateur).filter(Utilisateur.email == email_clean).first()
                                        finally:
                                            tdb.close()
                                        st.session_state.tenant_db = compte["chemin_db"]
                                        st.session_state.user = {
                                            "id": utilisateur_db.id if utilisateur_db else None,
                                            "nom": nom_complet,
                                            "email": email_clean,
                                            "role": "Personnel"
                                        }
                                        st.session_state.just_logged_in = True
                                        st.session_state.current_page = "Tableau de bord"
                                        st.session_state.flash_msg = "Espace personnel créé avec succès. Bienvenue !"
                                        st.session_state.flash_type = "success"
                                        afficher_chargement()

            # Reinitialisation du mot de passe personnel
            with tab_reset:
                section_title("Réinitialiser le mot de passe")
                with st.form("reset_request_perso"):
                    email_reset_input = st.text_input("Adresse e-mail de votre espace", value=st.session_state.reset_email, placeholder="Entrez votre e-mail")
                    btn_send_code = st.form_submit_button("Envoyer le code de vérification", icon=":material/send:")

                    if btn_send_code:
                        clean_mail = clean_str(email_reset_input).lower()
                        if not clean_mail:
                            show_notification("Veuillez saisir votre adresse e-mail.", type_notif="error")
                        else:
                            compte = trouver_compte(mode="personnel", email=clean_mail)
                            if not compte:
                                show_notification("Aucun espace personnel associé à cet e-mail.", type_notif="error")
                            else:
                                st.session_state.tenant_db = compte.chemin_db
                                msg, typ = envoyer_code_reset(clean_mail)
                                show_notification(msg, type_notif=typ)

                st.space("small")
                with st.form("reset_confirm_perso"):
                    code_saisi = st.text_input("Code de vérification", placeholder="Entrez votre code à 6 chiffres")
                    new_pass = st.text_input("Nouveau mot de passe", type="password", placeholder="Saisissez votre nouveau mot de passe")
                    new_pass_conf = st.text_input("Confirmer le nouveau mot de passe", type="password", placeholder="Confirmez votre nouveau mot de passe")
                    btn_confirm_reset = st.form_submit_button("Valider le nouveau mot de passe", icon=":material/save:")

                    if btn_confirm_reset:
                        msg, typ = confirmer_reset(code_saisi, new_pass, new_pass_conf)
                        show_notification(msg, type_notif=typ)