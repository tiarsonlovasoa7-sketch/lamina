# Pages de l'espace authentifie
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from database import RendezVous, Utilisateur, hash_password
from services.emails import envoyer_email_auto, template_rdv_accepte, template_rdv_planifie, template_rdv_refuse
from services.pdf import generer_pdf_brief
from ui.components import afficher_chargement, badge_priorite, badge_statut, page_header, section_title, show_notification, stat_card
from ui.team import _section_liste_membres
from utils import clean_str, format_id, sanitize_text, validate_password_strength


def page_dashboard(user, db):
    """Tableau de bord avec les indicateurs cles de l'activite."""
    page_header("Pilotage et indicateurs clés", "Vue d'ensemble de l'activité des audiences")

    tous_rdvs = db.query(RendezVous).all()
    confirmes = [r for r in tous_rdvs if r.statut == "Confirme"]
    en_attente = [r for r in tous_rdvs if r.statut == "En attente"]
    refuses = [r for r in tous_rdvs if r.statut == "Refuse"]

    # Affichage des cartes d indicateurs de performance
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        stat_card("Total Demandes", len(tous_rdvs))
    with col2:
        stat_card("Audiences confirmées", len(confirmes))
    with col3:
        stat_card("En attente d'arbitrage", len(en_attente))
    with col4:
        stat_card("Demandes refusées", len(refuses))

    recent_reponses_confirmes = db.query(RendezVous).filter(RendezVous.statut == "Confirme").order_by(RendezVous.id.desc()).limit(3).all()
    recent_reponses_refuses = db.query(RendezVous).filter(RendezVous.statut == "Refuse").order_by(RendezVous.id.desc()).limit(3).all()

    if user['role'] == "Directeur":
        with st.container(border=True):
            if en_attente:
                st.warning(f"Notification Responsable : Vous avez {len(en_attente)} demande(s) d'audience en attente de décision.")
                if st.button("Accéder directement à la validation", icon=":material/fact_check:"):
                    st.session_state.current_page = "Validation des Audiences"
                    afficher_chargement()
            else:
                st.success("Aucune demande en attente. Toutes les audiences ont été arbitrées.")

    elif user['role'] == "Personnel":
        with st.container(border=True):
            if confirmes:
                st.info("Mode personnel : vos rendez-vous sont confirmés directement, sans validation.")
            else:
                st.success("Aucun rendez-vous pour le moment. Créez votre premier rendez-vous depuis le menu.")

    else:
        section_title("Derniers retours du Responsable")
        col_conf, col_ref = st.columns(2)

        with col_conf:
            with st.container(border=True):
                st.write("Dernières audiences confirmées")
                if recent_reponses_confirmes:
                    for r in recent_reponses_confirmes:
                        st.markdown(
                            f"{badge_statut(r.statut)} **{format_id(r.id)}** - {sanitize_text(r.titre)} "
                            f"({sanitize_text(r.intervenant)}) le {r.date_heure.strftime('%d/%m/%Y à %H:%M')}"
                        )
                else:
                    st.caption("Aucune confirmation récente.")

        with col_ref:
            with st.container(border=True):
                st.write("Dernières audiences refusées")
                if recent_reponses_refuses:
                    for r in recent_reponses_refuses:
                        st.markdown(
                            f"{badge_statut(r.statut)} **{format_id(r.id)}** - {sanitize_text(r.titre)} "
                            f"({sanitize_text(r.intervenant)})"
                        )
                else:
                    st.caption("Aucun refus récent.")


def page_saisie(user, db):
    """Saisie d'une nouvelle demande ou d'un rendez-vous."""
    titre_page = "Ajouter un rendez-vous" if user['role'] in ("Directeur", "Personnel") else "Saisir une nouvelle demande d'audience"
    soustitre_page = "Création directe d'un rendez-vous validé." if user['role'] in ("Directeur", "Personnel") else "Toute nouvelle demande sera transmise automatiquement au Responsable pour validation."

    page_header(titre_page, soustitre_page)

    with st.container(border=True):
        with st.form("form_rdv"):
            titre = st.text_input("Objet de la demande", placeholder="Entrez l'objet de la demande")
            col1, col2, col3 = st.columns(3)
            intervenant = col1.text_input("Nom et prénom de l'intervenant", placeholder="Entrez le nom de l'intervenant")
            email_intervenant = col2.text_input("Adresse e-mail de l'intervenant", placeholder="Entrez l'e-mail de l'intervenant")
            telephone = col3.text_input("Téléphone", placeholder="Entrez le numéro de téléphone")

            col4, col5, col6 = st.columns(3)
            organisme = col4.text_input("Organisme ou Service", placeholder="Entrez le nom de l'organisme")
            date_r = col5.date_input("Date souhaitée", datetime.now() + timedelta(days=1))
            heure_r = col6.time_input("Heure souhaitée", datetime.now().time())

            col7, col8 = st.columns(2)
            duree = col7.number_input("Durée (minutes)", min_value=15, max_value=240, value=30, step=15)
            priorite = col8.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=1)

            contexte = st.text_area("Notes de contexte et points clés", placeholder="Saisissez le contexte et les sujets à traiter")

            libelle_bouton = "Ajouter le rendez-vous" if user['role'] in ("Directeur", "Personnel") else "Envoyer la demande au Responsable"

            if st.form_submit_button(libelle_bouton, icon=":material/event:"):
                clean_email_int = clean_str(email_intervenant).lower()
                clean_titre = sanitize_text(titre)
                clean_intervenant = sanitize_text(intervenant)
                clean_organisme = sanitize_text(organisme)
                clean_telephone = sanitize_text(telephone)
                clean_contexte = sanitize_text(contexte)

                if not clean_titre or not clean_intervenant or not clean_email_int:
                    show_notification("Veuillez remplir l'objet, le nom et l'e-mail.", type_notif="error")
                else:
                    with st.spinner("Enregistrement sécurisé en cours..."):
                        statut_initial = "Confirme" if user['role'] in ("Directeur", "Personnel") else "En attente"

                        nouveau = RendezVous(
                            titre=clean_titre,
                            intervenant=clean_intervenant,
                            email_intervenant=clean_email_int,
                            telephone=clean_telephone,
                            organisme=clean_organisme,
                            priorite=priorite,
                            date_heure=datetime.combine(date_r, heure_r),
                            duree_minutes=duree,
                            contexte_notes=clean_contexte,
                            statut=statut_initial
                        )
                        db.add(nouveau)
                        db.commit()

                        if user['role'] in ("Directeur", "Personnel") and clean_email_int:
                            sujet, corps = template_rdv_planifie(nouveau, clean_titre)
                            ok_mail, err_mail = envoyer_email_auto(clean_email_int, sujet, corps)
                            if not ok_mail and err_mail != "Configuration SMTP absente.":
                                show_notification(f"Rendez-vous créé, mais l'envoi de l'e-mail a échoué : {err_mail}", type_notif="warning")

                    if user['role'] in ("Directeur", "Personnel"):
                        show_notification(f"Le rendez-vous {format_id(nouveau.id)} a été ajouté avec succès.")
                    else:
                        show_notification(f"La demande {format_id(nouveau.id)} a été envoyée au Responsable avec succès.")


def page_validation(user, db):
    """Arbitrage des demandes en attente pour le directeur."""
    page_header("Arbitrage et gestion des audiences", "Validez, modifiez ou refusez les demandes en attente")

    demandes = db.query(RendezVous).filter(RendezVous.statut == "En attente").order_by(RendezVous.date_heure).all()

    if not demandes:
        st.success("Aucune demande d'audience en attente de validation.")
    else:
        st.info(f"Vous avez {len(demandes)} demande(s) en attente d'arbitrage.")
        for rdv in demandes:
            with st.expander(f"{format_id(rdv.id)} | {rdv.titre} | {rdv.organisme} ({rdv.intervenant})", expanded=True):

                if st.session_state.editing_rdv_id == rdv.id:
                    section_title(f"Modification de la demande {format_id(rdv.id)}")
                    with st.form(key=f"edit_form_{rdv.id}"):
                        e_titre = st.text_input("Objet", value=rdv.titre)
                        c1, c2 = st.columns(2)
                        e_intervenant = c1.text_input("Intervenant", value=rdv.intervenant)
                        e_email = c2.text_input("Email", value=rdv.email_intervenant or "")

                        c3, c4 = st.columns(2)
                        e_date = c3.date_input("Date", value=rdv.date_heure.date())
                        e_heure = c4.time_input("Heure", value=rdv.date_heure.time())

                        c5, c6 = st.columns(2)
                        e_duree = c5.number_input("Durée (min)", value=rdv.duree_minutes, min_value=15, step=15)
                        e_priorite = c6.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(rdv.priorite))

                        e_contexte = st.text_area("Contexte et Notes", value=rdv.contexte_notes or "")

                        col_save, col_cancel = st.columns(2)
                        if col_save.form_submit_button("Enregistrer les modifications"):
                            with st.spinner("Enregistrement des modifications..."):
                                rdv.titre = sanitize_text(e_titre)
                                rdv.intervenant = sanitize_text(e_intervenant)
                                rdv.email_intervenant = clean_str(e_email).lower()
                                rdv.date_heure = datetime.combine(e_date, e_heure)
                                rdv.duree_minutes = e_duree
                                rdv.priorite = e_priorite
                                rdv.contexte_notes = sanitize_text(e_contexte)
                                db.commit()
                            st.session_state.editing_rdv_id = None
                            st.session_state.flash_msg = f"Modifications du rendez-vous {format_id(rdv.id)} enregistrées avec succès."
                            st.session_state.flash_type = "success"
                            st.rerun()
                        if col_cancel.form_submit_button("Annuler"):
                            st.session_state.editing_rdv_id = None
                            st.rerun()
                else:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"Identifiant : {format_id(rdv.id)}")
                        st.write(f"Date proposée : {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} ({rdv.duree_minutes} min)")
                        st.markdown(f"Priorité proposée : {badge_priorite(rdv.priorite)}")
                        st.write(f"E-mail intervenant : {rdv.email_intervenant or 'Non renseigné'}")
                        st.write(f"Contexte : {rdv.contexte_notes or 'Aucun'}")
                    with c2:
                        if st.button("Accepter l'audience", key=f"val_{rdv.id}", type="primary", icon=":material/check_circle:"):
                            with st.spinner("Validation et envoi de l'e-mail de confirmation..."):
                                rdv.statut = "Confirme"
                                db.commit()

                                if rdv.email_intervenant:
                                    sujet, corps = template_rdv_accepte(rdv)
                                    envoyer_email_auto(rdv.email_intervenant, sujet, corps)

                            st.session_state.flash_msg = f"Audience {format_id(rdv.id)} acceptée avec succès."
                            st.session_state.flash_type = "success"
                            st.rerun()

                        if st.button("Modifier le RDV", key=f"btn_edit_{rdv.id}", icon=":material/edit:"):
                            st.session_state.editing_rdv_id = rdv.id
                            st.rerun()

                        if st.button("Annuler le RDV", key=f"ref_{rdv.id}", icon=":material/cancel:"):
                            with st.spinner("Annulation du rendez-vous et notification..."):
                                rdv.statut = "Refuse"
                                db.commit()

                                if rdv.email_intervenant:
                                    sujet, corps = template_rdv_refuse(rdv)
                                    envoyer_email_auto(rdv.email_intervenant, sujet, corps)

                            st.session_state.flash_msg = f"Audience {format_id(rdv.id)} annulée avec succès."
                            st.session_state.flash_type = "error"
                            st.rerun()


def page_gestion_equipe(user, db):
    """Gestion de l'equipe pour le responsable."""
    page_header("Gestion de l'équipe", "Ajoutez ou retirez les comptes Assistant(e)s de votre entreprise")

    with st.container(border=True):
        section_title("Ajouter une Assistant(e)")
        with st.form("form_add_membre"):
            nom_membre = st.text_input("Nom et prénom de l'assistant(e)", placeholder="Entrez le nom complet")
            email_membre = st.text_input("Adresse e-mail", placeholder="Entrez l'e-mail de l'assistant(e)")
            pass_membre = st.text_input("Mot de passe (8 caractères min)", type="password", placeholder="Saisissez votre mot de passe")
            pass_membre_conf = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmez votre mot de passe")

            if st.form_submit_button("Ajouter l'assistant(e)", icon=":material/person_add:"):
                nom_clean = sanitize_text(nom_membre)
                email_clean = clean_str(email_membre).lower()
                pass_clean = clean_str(pass_membre)

                if not nom_clean or not email_clean or not pass_clean:
                    show_notification("Veuillez remplir tous les champs.", type_notif="error")
                elif pass_clean != clean_str(pass_membre_conf):
                    show_notification("Les mots de passe ne correspondent pas.", type_notif="error")
                else:
                    is_strong, msg_strength = validate_password_strength(pass_clean)
                    if not is_strong:
                        show_notification(msg_strength, type_notif="error")
                    elif db.query(Utilisateur).filter(Utilisateur.email == email_clean).first():
                        show_notification("Un compte existe déjà avec cet e-mail dans cette entreprise.", type_notif="error")
                    else:
                        with st.spinner("Ajout du compte assistant(e)..."):
                            db.add(Utilisateur(
                                nom_complet=nom_clean,
                                email=email_clean,
                                mot_de_passe_hash=hash_password(pass_clean),
                                role="Secretaire"
                            ))
                            db.commit()
                        st.session_state.flash_msg = f"Assistant(e) {nom_clean} ajouté(e) à l'équipe avec succès."
                        st.session_state.flash_type = "success"
                        st.rerun()

    st.space("medium")
    _section_liste_membres()


def page_planning(user, db):
    """Planning des audiences validees avec telechargement du brief PDF."""
    page_header("Planning des audiences validées", "Consultez les audiences confirmées et téléchargez leur brief")

    rdvs = db.query(RendezVous).filter(RendezVous.statut == "Confirme").order_by(RendezVous.date_heure).all()

    if not rdvs:
        st.info("Aucune audience confirmée au planning.")
    else:
        for rdv in rdvs:
            with st.expander(f"{format_id(rdv.id)} | {rdv.date_heure.strftime('%d/%m/%Y %H:%M')} | {rdv.titre} ({rdv.organisme})"):
                st.write(f"Intervenant : {rdv.intervenant} | Téléphone : {rdv.telephone or 'Non renseigné'}")
                st.write(f"Contexte : {rdv.contexte_notes or 'Aucun'}")

                with st.spinner("Génération du brief PDF en cours..."):
                    pdf_data = generer_pdf_brief(rdv)

                st.download_button(
                    label="Télécharger le Brief PDF",
                    data=pdf_data,
                    file_name=f"Brief_RDV_{format_id(rdv.id)}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{rdv.id}",
                    icon=":material/download:"
                )


def page_historique(user, db):
    """Historique general des demandes avec modification et export."""
    page_header("Historique général", "Retrouvez l'ensemble des demandes et leur statut")

    tous = db.query(RendezVous).order_by(RendezVous.date_heure.desc()).all()

    if st.session_state.editing_rdv_id is not None:
        rdv_edit = db.query(RendezVous).filter(RendezVous.id == st.session_state.editing_rdv_id).first()
        if rdv_edit:
            section_title(f"Modification de la demande {format_id(rdv_edit.id)}")
            with st.container(border=True):
                with st.form(key="form_edit_hist"):
                    e_titre = st.text_input("Objet", value=rdv_edit.titre)
                    c1, c2 = st.columns(2)
                    e_intervenant = c1.text_input("Intervenant", value=rdv_edit.intervenant)
                    e_email = c2.text_input("E-mail", value=rdv_edit.email_intervenant or "")

                    c3, c4 = st.columns(2)
                    e_date = c3.date_input("Date", value=rdv_edit.date_heure.date())
                    e_heure = c4.time_input("Heure", value=rdv_edit.date_heure.time())

                    c5, c6 = st.columns(2)
                    e_duree = c5.number_input("Durée (min)", value=rdv_edit.duree_minutes, min_value=15, step=15)
                    e_priorite = c6.selectbox("Priorité", ["Basse", "Moyenne", "Haute"], index=["Basse", "Moyenne", "Haute"].index(rdv_edit.priorite))

                    e_contexte = st.text_area("Contexte et Notes", value=rdv_edit.contexte_notes or "")

                    col_save, col_cancel = st.columns(2)
                    if col_save.form_submit_button("Enregistrer"):
                        with st.spinner("Mise à jour de la demande..."):
                            rdv_edit.titre = sanitize_text(e_titre)
                            rdv_edit.intervenant = sanitize_text(e_intervenant)
                            rdv_edit.email_intervenant = clean_str(e_email).lower()
                            rdv_edit.date_heure = datetime.combine(e_date, e_heure)
                            rdv_edit.duree_minutes = e_duree
                            rdv_edit.priorite = e_priorite
                            rdv_edit.contexte_notes = sanitize_text(e_contexte)
                            db.commit()
                        st.session_state.editing_rdv_id = None
                        st.session_state.flash_msg = f"Demande {format_id(rdv_edit.id)} mise à jour avec succès."
                        st.session_state.flash_type = "success"
                        st.rerun()
                    if col_cancel.form_submit_button("Annuler"):
                        st.session_state.editing_rdv_id = None
                        st.rerun()

    data = []
    for r in tous:
        data.append({
            "ID": format_id(r.id),
            "Objet": r.titre,
            "Intervenant": r.intervenant,
            "Organisme": r.organisme or "Non renseigné",
            "Priorite": r.priorite,
            "Date": r.date_heure.strftime('%d/%m/%Y %H:%M'),
            "Statut": r.statut
        })

    df_historique = pd.DataFrame(data)
    if not df_historique.empty:
        statuts_libelles = {"En attente": "En attente", "Confirme": "Confirmé", "Refuse": "Refusé"}
        df_historique["Statut"] = df_historique["Statut"].map(lambda s: statuts_libelles.get(s, s))

    st.dataframe(
        df_historique,
        hide_index=True,
        height=420,
        column_config={
            "ID": st.column_config.TextColumn("ID", width="small", pinned=True),
            "Priorite": st.column_config.SelectboxColumn(
                "Priorité",
                options=["Basse", "Moyenne", "Haute"],
                width="small",
            ),
            "Statut": st.column_config.SelectboxColumn(
                "Statut",
                options=["En attente", "Confirmé", "Refusé"],
                width="medium",
            ),
        },
    )

    st.space("medium")
    section_title("Action sur un enregistrement")
    col_sel, col_btn = st.columns([3, 1])
    rdv_options = {f"{format_id(r.id)} - {r.titre}": r.id for r in tous}
    if rdv_options:
        selected_label = col_sel.selectbox("Choisir une demande à modifier", list(rdv_options.keys()))
        if col_btn.button("Modifier cette demande"):
            st.session_state.editing_rdv_id = rdv_options[selected_label]
            st.rerun()