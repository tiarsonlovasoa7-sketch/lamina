# Interfaces de connexion et de gestion du mode equipe
import streamlit as st

from database import Utilisateur, creer_compte, creer_session_sur, generer_chemin_base, hash_password, lister_comptes, lister_utilisateurs, trouver_compte
from services.auth import _verifier_ancien_mdp, confirmer_reset, envoyer_code_reset, login
from ui.components import afficher_chargement, section_title, show_notification, styler_champs_login
from ui.dialogs import _annuler_action_membre, _fermer_menu_fixer_action, dialog_supprimer_membre
from utils import clean_str, libelle_role, sanitize_text, validate_password_strength


@st.fragment
def _section_liste_membres():
    """Liste des membres de l'equipe + panneau d'action."""
    tenant_db = st.session_state.get("tenant_db")
    tdb = creer_session_sur(tenant_db) if tenant_db else None
    try:
        section_title("Membres de l'équipe")
        membres = tdb.query(Utilisateur).order_by(Utilisateur.role, Utilisateur.nom_complet).all()
        if not membres:
            st.info("Aucun membre pour le moment.")
        else:
            if "action_membre" not in st.session_state:
                st.session_state.action_membre = None
            for m in membres:
                with st.container(border=True):
                    col_info, col_menu = st.columns([3, 1])
                    with col_info:
                        st.write(f"**{m.nom_complet}** — {libelle_role(m.role)}")
                        st.caption(m.email)
                    with col_menu:
                        with st.popover("", icon=":material/more_vert:", key=f"menu_{m.id}", on_change="rerun", width="stretch"):
                            st.button("Modifier le mot de passe", key=f"action_mdp_{m.id}", icon=":material/password:", width="stretch",
                                      on_click=lambda mid=m.id, cmenu=f"menu_{m.id}", tdb2=st.session_state.get("tenant_db"): _fermer_menu_fixer_action(cmenu, "membre", ("mdp", mid, tdb2)))
                            if m.role != "Directeur":
                                st.write("")
                                st.button("Supprimer le compte", key=f"action_del_{m.id}", icon=":material/delete:", width="stretch",
                                          on_click=lambda mid=m.id, cmenu=f"menu_{m.id}", tdb2=st.session_state.get("tenant_db"): _fermer_menu_fixer_action(cmenu, "membre", ("del", mid, tdb2)))

            # Panneau d'action selon le menu choisi
            action = st.session_state.action_membre
            if action and len(action) == 3 and action[2] == tenant_db:
                act, mid, _ = action
                membre = tdb.query(Utilisateur).filter(Utilisateur.id == mid).first()
                if membre is None:
                    st.session_state.action_membre = None
                elif act == "mdp":
                    with st.container(border=True):
                        section_title(f"Modifier le mot de passe — {membre.nom_complet}")
                        with st.form(f"form_mdp_{mid}"):
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
                                elif not _verifier_ancien_mdp(tenant_db, membre.email, old_clean):
                                    show_notification("L'ancien mot de passe est incorrect.", type_notif="error")
                                else:
                                    is_strong, msg_strength = validate_password_strength(pass_clean)
                                    if not is_strong:
                                        show_notification(msg_strength, type_notif="error")
                                    else:
                                        membre.mot_de_passe_hash = hash_password(pass_clean)
                                        tdb.commit()
                                        st.session_state.action_membre = None
                                        st.session_state.flash_msg = f"Le mot de passe de {membre.nom_complet} a été modifié."
                                        st.session_state.flash_type = "success"
                                        afficher_chargement()
                        st.button("Annuler", key=f"annuler_mdp_{mid}", icon=":material/close:", on_click=_annuler_action_membre)
                elif act == "del":
                    dialog_supprimer_membre(mid, membre.nom_complet)
    finally:
        if tdb:
            tdb.close()


def interface_equipe():
    """Interface de connexion pour le mode equipe."""
    col_gauche, col_milieu, col_droite = st.columns([1, 1, 1])
    with col_milieu:
        if st.button("Retour au choix du mode", icon=":material/arrow_back:", width="stretch"):
            st.session_state.mode = None
            afficher_chargement()
    st.space("small")
    styler_champs_login()

    with st.columns([1, 3, 1])[1]:
        with st.container(border=True):
            tab_rejoindre, tab_creer, tab_reset = st.tabs(["Rejoindre une entreprise", "Créer une entreprise", "Mot de passe oublié"])

            # Rejoindre une entreprise existante
            with tab_rejoindre:
                section_title("Connexion à votre entreprise")
                st.write("Sélectionnez votre entreprise, puis votre compte au sein de cette entreprise.")

                # Activation de la selection (entreprise puis membre) depuis l annuaire
                if "equipe_selection_chemin" not in st.session_state:
                    st.session_state.equipe_selection_chemin = None
                    st.session_state.equipe_selection_nom = None
                    st.session_state.equipe_selection_membre = None

                if not st.session_state.equipe_selection_chemin:
                    comptes = lister_comptes(mode="equipe")
                    if not comptes:
                        st.info("Aucune entreprise créée pour le moment. Créez la vôtre dans l'onglet « Créer une entreprise ».")
                    else:
                        styler_champs_login()
                        for compte in comptes:
                            if st.button(compte.nom, key=f"equipe_{compte.id}", icon=":material/business:", width="stretch"):
                                st.session_state.equipe_selection_chemin = compte.chemin_db
                                st.session_state.equipe_selection_nom = compte.nom
                                st.session_state.equipe_selection_membre = None
                                afficher_chargement()
                elif not st.session_state.equipe_selection_membre:
                    entreprise_nom = st.session_state.equipe_selection_nom
                    entreprise_chemin = st.session_state.equipe_selection_chemin
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        if st.button("Changer d'entreprise", key="eq_retour_liste", icon=":material/house:", width="stretch"):
                            st.session_state.equipe_selection_chemin = None
                            st.session_state.equipe_selection_nom = None
                            st.session_state.equipe_selection_membre = None
                            afficher_chargement()
                    with col_info2:
                        st.caption(f"Entreprise sélectionnée : {entreprise_nom}")

                    membres = lister_utilisateurs(entreprise_chemin)
                    if not membres:
                        st.info("Aucun compte membre trouvé dans cette entreprise.")
                    else:
                        st.write("Choisissez votre compte :")
                        styler_champs_login()
                        for membre in membres:
                            if st.button(membre.nom_complet, key=f"membre_{entreprise_nom}_{membre.id}", icon=":material/person:", width="stretch"):
                                st.session_state.equipe_selection_membre = membre.nom_complet
                                st.session_state.equipe_selection_libelle = membre.nom_complet
                                afficher_chargement()
                else:
                    entreprise_nom = st.session_state.equipe_selection_nom
                    entreprise_chemin = st.session_state.equipe_selection_chemin
                    membre_libelle = st.session_state.get("equipe_selection_libelle", st.session_state.equipe_selection_membre)
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        if st.button("Changer de compte", key="eq_retour_membre", icon=":material/swap_horiz:", width="stretch"):
                            st.session_state.equipe_selection_membre = None
                            st.session_state.equipe_selection_libelle = None
                            afficher_chargement()
                    with col_info2:
                        st.caption(f"Compte : {membre_libelle} ({entreprise_nom})")

                    styler_champs_login()
                    with st.form("login_equipe_mdp"):
                        email_input = st.text_input("Adresse e-mail", placeholder="Entrez votre e-mail")
                        password_input = st.text_input("Mot de passe", type="password", placeholder="Saisissez votre mot de passe")
                        btn_join = st.form_submit_button("Se connecter", type="primary", icon=":material/login:")
                        if btn_join:
                            email_clean = clean_str(email_input).lower()
                            if not email_clean or not clean_str(password_input):
                                show_notification("Veuillez remplir votre e-mail et votre mot de passe.", type_notif="error")
                            else:
                                st.session_state.tenant_db = entreprise_chemin
                                with st.spinner("Vérification sécurisée des identifiants..."):
                                    succes, message = login(email_clean, password_input)
                                if succes:
                                    st.session_state.equipe_selection_chemin = None
                                    st.session_state.equipe_selection_nom = None
                                    st.session_state.equipe_selection_membre = None
                                    st.session_state.equipe_selection_libelle = None
                                    st.session_state.flash_msg = f"Connexion réussie. Bienvenue dans l'entreprise {entreprise_nom}."
                                    st.session_state.flash_type = "success"
                                    afficher_chargement()
                                else:
                                    show_notification(f"Échec de connexion : {message}", type_notif="error")

            # Creation d une entreprise et du compte Responsable
            with tab_creer:
                section_title("Créer votre entreprise")
                with st.form("create_company_form"):
                    nom_entreprise = st.text_input("Nom de l'entreprise", placeholder="Entrez le nom de l'entreprise")
                    nom = st.text_input("Nom du Responsable", placeholder="Entrez votre nom de famille")
                    prenom = st.text_input("Prénom du Responsable", placeholder="Entrez votre prénom")
                    email_reg = st.text_input("Adresse e-mail du Responsable", placeholder="Entrez votre e-mail")
                    pass_reg = st.text_input("Mot de passe (8 caractères min)", type="password", placeholder="Saisissez votre mot de passe")
                    pass_confirm = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmez votre mot de passe")

                    if st.form_submit_button("Créer l'entreprise et mon compte", icon=":material/apartment:"):
                        entreprise_clean = clean_str(nom_entreprise)
                        email_clean = clean_str(email_reg).lower()
                        pass_clean = clean_str(pass_reg)
                        nom_clean = sanitize_text(nom)
                        prenom_clean = sanitize_text(prenom)

                        if not entreprise_clean or not nom_clean or not prenom_clean or not email_clean or not pass_clean:
                            show_notification("Veuillez remplir tous les champs.", type_notif="error")
                        elif pass_clean != clean_str(pass_confirm):
                            show_notification("Les mots de passe ne correspondent pas.", type_notif="error")
                        else:
                            is_strong, msg_strength = validate_password_strength(pass_clean)
                            if not is_strong:
                                show_notification(msg_strength, type_notif="error")
                            elif trouver_compte(mode="equipe", nom=entreprise_clean):
                                show_notification("Une entreprise avec ce nom existe déjà.", type_notif="error")
                            elif trouver_compte(mode="equipe", email=email_clean):
                                show_notification("Cet e-mail est déjà utilisé comme identifiant d'entreprise.", type_notif="error")
                            else:
                                with st.spinner("Création de l'entreprise et du compte Responsable..."):
                                    nom_complet = f"{nom_clean} {prenom_clean}"
                                    chemin = generer_chemin_base(entreprise_clean)
                                    compte, erreur = creer_compte("equipe", entreprise_clean, chemin, email=email_clean)
                                    if erreur:
                                        show_notification(f"Erreur lors de la création : {erreur}", type_notif="error")
                                    else:
                                        tdb = creer_session_sur(chemin)
                                        try:
                                            tdb.add(Utilisateur(
                                                nom_complet=nom_complet,
                                                email=email_clean,
                                                mot_de_passe_hash=hash_password(pass_clean),
                                                role="Directeur"
                                            ))
                                            tdb.commit()
                                            responsable_db = tdb.query(Utilisateur).filter(Utilisateur.email == email_clean).first()
                                        finally:
                                            tdb.close()
                                        st.session_state.tenant_db = compte["chemin_db"]
                                        st.session_state.user = {
                                            "id": responsable_db.id if responsable_db else None,
                                            "nom": nom_complet,
                                            "email": email_clean,
                                            "role": "Directeur"
                                        }
                                        st.session_state.just_logged_in = True
                                        st.session_state.current_page = "Tableau de bord"
                                        st.session_state.flash_msg = f"Entreprise « {entreprise_clean} » créée avec succès. Vous en êtes le Responsable."
                                        st.session_state.flash_type = "success"
                                        afficher_chargement()

            # Reinitialisation du mot de passe au sein d une entreprise
            with tab_reset:
                section_title("Réinitialiser le mot de passe")
                with st.form("reset_request_equipe"):
                    entreprise_reset = st.text_input("Nom de l'entreprise", placeholder="Entrez le nom de l'entreprise")
                    email_reset_input = st.text_input("Adresse e-mail de votre compte", value=st.session_state.reset_email, placeholder="Entrez votre e-mail")
                    btn_send_code = st.form_submit_button("Envoyer le code de vérification", icon=":material/send:")

                    if btn_send_code:
                        entreprise_clean = clean_str(entreprise_reset).lower()
                        clean_mail = clean_str(email_reset_input).lower()
                        if not entreprise_clean or not clean_mail:
                            show_notification("Veuillez saisir le nom de l'entreprise et votre e-mail.", type_notif="error")
                        else:
                            compte = trouver_compte(mode="equipe", nom=entreprise_clean)
                            if not compte:
                                show_notification("Entreprise introuvable.", type_notif="error")
                            else:
                                st.session_state.tenant_db = compte.chemin_db
                                msg, typ = envoyer_code_reset(clean_mail)
                                show_notification(msg, type_notif=typ)

                st.space("small")
                with st.form("reset_confirm_equipe"):
                    code_saisi = st.text_input("Code de vérification", placeholder="Entrez votre code à 6 chiffres")
                    new_pass = st.text_input("Nouveau mot de passe", type="password", placeholder="Saisissez votre nouveau mot de passe")
                    new_pass_conf = st.text_input("Confirmer le nouveau mot de passe", type="password", placeholder="Confirmez votre nouveau mot de passe")
                    btn_confirm_reset = st.form_submit_button("Valider le nouveau mot de passe", icon=":material/save:")

                    if btn_confirm_reset:
                        msg, typ = confirmer_reset(code_saisi, new_pass, new_pass_conf)
                        show_notification(msg, type_notif=typ)