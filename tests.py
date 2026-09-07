# Tests de l application Lamina : parcours multi-comptes et interfaces des rôles
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit.testing.v1 import AppTest

import database

# Identifiant unique par execution pour eviter les collisions d annuaire
UID = f"{os.getpid()}{int(time.time())}"


# --- Aides de navigation AppTest ---

def ouvrir_app():
    at = AppTest.from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"))
    return at.run(timeout=60)

def bouton_par_label(at, label):
    for b in at.button:
        if b.label == label:
            return b
    return None

def bouton_contenant(at, extrait):
    for b in at.button:
        if extrait in b.label:
            return b
    return None

def contient_dans(at, valeur):
    """Vrai si un texte des elements markdown/caption contient la valeur."""
    tous = textes_markdown(at) + textes_capture(at)
    return any(valeur in t for t in tous)

def titres(at):
    return [t.value for t in at.title]

def textes_markdown(at):
    return [m.value for m in at.markdown]

def textes_capture(at):
    return [c.value for c in at.caption]

def libelles_boutons(at):
    return [b.label for b in at.button]


# --- Tests ---

def test_bienvenue():
    at = ouvrir_app()
    assert "Choisissez votre mode d'utilisation" in textes_capture(at)
    assert bouton_contenant(at, "Mode personnel") is not None
    assert bouton_contenant(at, "Mode équipe") is not None
    assert at.exception == []
    print("OK test_bienvenue")

def test_creation_espace_personnel():
    at = ouvrir_app()
    bouton_contenant(at, "Mode personnel").click().run()

    # Remplissage du formulaire de creation (onglet "Créer mon espace")
    email_perso = f"marie.perso.{UID}@example.com"
    at.text_input(key="perso_reg_nom").set_value("Durand")
    at.text_input(key="perso_reg_prenom").set_value("Marie")
    at.text_input(key="perso_reg_email").set_value(email_perso)
    at.text_input(key="perso_reg_mdp").set_value("mdp2026perso")
    at.text_input(key="perso_reg_mdp_conf").set_value("mdp2026perso")
    bouton_par_label(at, "Créer mon espace").click().run()

    # Connexion automatique : tableau de bord personnel
    assert "Pilotage et indicateurs clés" in titres(at)
    assert "Mode personnel" in textes_capture(at)
    assert at.exception == []
    print("OK test_creation_espace_personnel")

def test_creation_entreprise():
    at = ouvrir_app()
    bouton_contenant(at, "Mode équipe").click().run()

    entreprise = f"Technova{UID}"
    email_responsable = f"responsable.{UID}@technova.com"
    at.text_input(key="equipe_create_entreprise").set_value(entreprise)
    at.text_input(key="equipe_create_nom").set_value("Martin")
    at.text_input(key="equipe_create_prenom").set_value("Paul")
    at.text_input(key="equipe_create_email").set_value(email_responsable)
    at.text_input(key="equipe_create_mdp").set_value("mdp2026equipe")
    at.text_input(key="equipe_create_mdp_conf").set_value("mdp2026equipe")
    bouton_par_label(at, "Créer l'entreprise et mon compte").click().run()

    # Connexion automatique : tableau de bord Responsable
    assert "Pilotage et indicateurs clés" in titres(at)
    assert f"Entreprise : {entreprise}" in textes_capture(at)
    assert bouton_par_label(at, "Gérer l'équipe") is not None
    assert at.exception == []
    print("OK test_creation_entreprise")

def test_reconnexion_personnel():
    at = ouvrir_app()
    bouton_contenant(at, "Mode personnel").click().run()

    email_perso = f"marie2.perso.{UID}@example.com"
    at.text_input(key="perso_reg_nom").set_value("Durand")
    at.text_input(key="perso_reg_prenom").set_value("Marie")
    at.text_input(key="perso_reg_email").set_value(email_perso)
    at.text_input(key="perso_reg_mdp").set_value("mdp2026perso")
    at.text_input(key="perso_reg_mdp_conf").set_value("mdp2026perso")
    bouton_par_label(at, "Créer mon espace").click().run()

    # Deconnexion puis reconnexion avec le meme compte (clic sur le nom, puis email + mot de passe)
    bouton_par_label(at, "Se déconnecter").click().run()
    bouton_contenant(at, "Mode personnel").click().run()
    bouton_contenant(at, "Durand Marie").click().run()
    at.text_input(key="perso_login_email").set_value(email_perso)
    at.text_input(key="perso_login_mdp").set_value("mdp2026perso")
    bouton_par_label(at, "Se connecter").click().run()

    # Tableau de bord personnel a nouveau
    assert "Pilotage et indicateurs clés" in titres(at)
    assert at.exception == []
    print("OK test_reconnexion_personnel")

def test_gestion_equipe_et_role_assistant():
    at = ouvrir_app()
    bouton_contenant(at, "Mode équipe").click().run()

    entreprise = f"BatiPro{UID}"
    email_responsable = f"responsable.{UID}@batipro.com"
    at.text_input(key="equipe_create_entreprise").set_value(entreprise)
    at.text_input(key="equipe_create_nom").set_value("Martin")
    at.text_input(key="equipe_create_prenom").set_value("Paul")
    at.text_input(key="equipe_create_email").set_value(email_responsable)
    at.text_input(key="equipe_create_mdp").set_value("mdp2026equipe")
    at.text_input(key="equipe_create_mdp_conf").set_value("mdp2026equipe")
    bouton_par_label(at, "Créer l'entreprise et mon compte").click().run()

    # Ajout d'un(e) assistant(e) depuis la page Gestion de l'équipe
    bouton_par_label(at, "Gérer l'équipe").click().run()
    assert "Gestion de l'équipe" in titres(at)

    email_assistant = f"sophie.{UID}@batipro.com"
    at.text_input(key="membre_add_nom").set_value("Sophie Leroux")
    at.text_input(key="membre_add_email").set_value(email_assistant)
    at.text_input(key="membre_add_mdp").set_value("mdpassist2026")
    at.text_input(key="membre_add_mdp_conf").set_value("mdpassist2026")
    bouton_par_label(at, "Ajouter l'assistant(e)").click().run()

    # L'assistant(e) apparait dans la liste de l'equipe
    assert contient_dans(at, "Sophie Leroux")
    assert at.exception == []

    # Deconnexion du Responsable, puis connexion de l'assistant(e)
    bouton_par_label(at, "Se déconnecter").click().run()
    bouton_contenant(at, "Mode équipe").click().run()
    bouton_contenant(at, entreprise).click().run()
    bouton_contenant(at, "Sophie Leroux").click().run()
    at.text_input(key="equipe_login_email").set_value(email_assistant)
    at.text_input(key="equipe_login_mdp").set_value("mdpassist2026")
    bouton_par_label(at, "Se connecter").click().run()

    # L'assistant(e) accede au tableau de bord sans la gestion d'equipe
    assert "Pilotage et indicateurs clés" in titres(at)
    assert bouton_par_label(at, "Gérer l'équipe") is None
    assert bouton_par_label(at, "Nouvelle demande de RDV") is not None
    assert at.exception == []
    print("OK test_gestion_equipe_et_role_assistant")

def test_annuaire_comptes():
    # Nettoyage d un eventuel compte precedent cree lors d une execution precedente
    database.init_db()
    email_a = f"alice.{UID}@example.com"
    email_b = f"bob.{UID}@example.com"
    compte = database.trouver_compte(mode="personnel", nom=None, email=email_a)
    if compte:
        db = database.SessionLocal()
        try:
            db.delete(db.query(database.Compte).get(compte.id))
            db.commit()
        finally:
            db.close()

    # Creation d un compte personnel avec sa propre base
    chemin = database.generer_chemin_base(email_a)
    compte, erreur = database.creer_compte("personnel", "Alice Test", chemin, email=email_a)
    assert erreur is None
    assert compte is not None
    assert compte["chemin_db"] == chemin

    # Recherche insensible a la casse sur l'email
    retrouve = database.trouver_compte(mode="personnel", email=email_a.upper())
    assert retrouve is not None
    assert retrouve.chemin_db == chemin

    # La base du compte est bien creee et isolee
    session_a = database.creer_session_sur(chemin)
    try:
        session_a.add(database.Utilisateur(
            nom_complet="Alice Test",
            email=email_a,
            mot_de_passe_hash=database.hash_password("mdp2026"),
            role="Personnel"
        ))
        session_a.commit()
        assert session_a.query(database.Utilisateur).count() == 1
    finally:
        session_a.close()

    # Un second compte personnel est isole : utilisateurs vides
    chemin_b = database.generer_chemin_base(email_b)
    compte_b, erreur_b = database.creer_compte("personnel", "Bob Test", chemin_b, email=email_b)
    assert erreur_b is None
    assert compte_b["chemin_db"] == chemin_b
    session_b = database.creer_session_sur(chemin_b)
    try:
        assert session_b.query(database.Utilisateur).count() == 0
    finally:
        session_b.close()

    # Creation d une entreprise et recherche par nom insensible a la casse
    nom_ent = f"Technova{UID}"
    compte_ent, err_ent = database.creer_compte(
        "equipe",
        nom_ent,
        database.generer_chemin_base(nom_ent),
        email=f"ct.{UID}@technova.com",
    )
    assert err_ent is None
    assert compte_ent["nom"] == nom_ent
    assert database.trouver_compte(mode="equipe", nom=nom_ent.lower()) is not None
    assert database.trouver_compte(mode="equipe", nom="inconnue") is None
    print("OK test_annuaire_comptes")

def test_generation_pdf_caracteres_speciaux():
    from datetime import datetime
    from database import RendezVous
    from services.pdf import generer_pdf_brief

    rdv_test = RendezVous(
        id=99,
        titre="Audience d'évaluation & projet <alpha>",
        intervenant="M. l'Inspecteur & Mme. D'Artois",
        email_intervenant="inspecteur@example.com",
        telephone="0102030405",
        organisme="Ministère & Cie <Paris>",
        priorite="Haute",
        date_heure=datetime.now(),
        duree_minutes=45,
        contexte_notes="Note avec caractères spéciaux : & < > ' et retour à la ligne\nSeconde ligne."
    )
    pdf_buf = generer_pdf_brief(rdv_test)
    data = pdf_buf.getvalue()
    assert len(data) > 0
    assert data.startswith(b"%PDF")
    print("OK test_generation_pdf_caracteres_speciaux")

def test_reset_securite_et_isolation_modes():
    from services.auth import _verifier_ancien_mdp, logout
    import streamlit as st

    st.session_state.tenant_db = "fake_path.db"
    logout()
    assert st.session_state.tenant_db is None
    assert st.session_state.user is None

    # Test verification ancien mdp sans fallback non securise
    res = _verifier_ancien_mdp("non_existent_db.db", "unknown@test.com", "wrongpass")
    assert res is False
    print("OK test_reset_securite_et_isolation_modes")

def test_filtres_recherche_et_dates():
    from datetime import datetime
    from ui.filtres import filtrer_objets, filtrer_rdv, texte_contient
    from database import RendezVous

    assert texte_contient("ministere", "Ministère & Cie") is True
    assert texte_contient("alpha", "Béta") is False

    rdvs = [
        RendezVous(id=1, titre="Audience Ministère", intervenant="M. Alpha", organisme="Ministère", date_heure=datetime(2026, 9, 1, 9, 0), statut="Confirme"),
        RendezVous(id=2, titre="Réunion interne", intervenant="Mme Beta", organisme="Préfecture", date_heure=datetime(2026, 9, 3, 10, 0), statut="En attente"),
        RendezVous(id=3, titre="Point presse", intervenant="M. Alpha", organisme="Mairie", date_heure=datetime(2026, 9, 10, 14, 0), statut="Confirme"),
    ]
    # Recherche libre sur titre/intervenant/organisme (accents tolérés)
    assert [r.id for r in filtrer_rdv(rdvs, "ministère", None, None)] == [1]
    assert [r.id for r in filtrer_rdv(rdvs, "alpha", None, None)] == [1, 3]
    # Borne basse de periode uniquement
    assert [r.id for r in filtrer_rdv(rdvs, "", datetime(2026, 9, 3).date(), None)] == [2, 3]
    # Bornes basse et haute
    assert [r.id for r in filtrer_rdv(rdvs, "", datetime(2026, 9, 1).date(), datetime(2026, 9, 3).date())] == [1, 2]
    # Aucun filtre : tout est conservé
    assert len(filtrer_rdv(rdvs, "", None, None)) == 3

    class Personne:
        def __init__(self, nom, mail):
            self.nom = nom
            self.mail = mail

    personnes = [Personne("Durand Marie", "marie@x.fr"), Personne("Leroux Sophie", "sophie@x.fr")]
    assert [p.nom for p in filtrer_objets(personnes, ["nom", "mail"], "leroux")] == ["Leroux Sophie"]
    assert [p.nom for p in filtrer_objets(personnes, ["nom", "mail"], "MARIE")] == ["Durand Marie"]
    assert [p.nom for p in filtrer_objets(personnes, ["nom", "mail"], "")] == ["Durand Marie", "Leroux Sophie"]
    print("OK test_filtres_recherche_et_dates")

if __name__ == "__main__":
    test_bienvenue()
    test_creation_espace_personnel()
    test_creation_entreprise()
    test_reconnexion_personnel()
    test_gestion_equipe_et_role_assistant()
    test_annuaire_comptes()
    test_generation_pdf_caracteres_speciaux()
    test_reset_securite_et_isolation_modes()
    test_filtres_recherche_et_dates()
    print("Tous les tests sont passés.")