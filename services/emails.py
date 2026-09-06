# Envoi d'e-mails SMTP et templates centralises
import os
import smtplib
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils import clean_str, format_id


def _getenv(name, default=""):
    """Lit une variable d'environnement, puis les secrets Streamlit Cloud en secours."""
    valeur = os.getenv(name)
    if valeur:
        return valeur
    try:
        import streamlit as st

        return st.secrets.get(name, default)
    except Exception:
        return default


def envoyer_email_auto(destinataire, sujet, corps_html):
    """Envoi automatique d'un e-mail via SMTP."""
    smtp_host = _getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_getenv("SMTP_PORT", "587"))
    smtp_email = _getenv("SMTP_EMAIL")
    smtp_password = _getenv("SMTP_PASSWORD")

    if not smtp_email or not smtp_password:
        return False, "Configuration SMTP absente."

    clean_dest = clean_str(destinataire).lower()
    if not clean_dest or "@" not in clean_dest:
        return False, "Adresse e-mail invalide."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"] = f"Lamina <{smtp_email}>"
        msg["To"] = clean_dest

        msg.attach(MIMEText(corps_html, "html", "utf-8"))
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, clean_dest, msg.as_string())
        server.quit()
        return True, "Message envoyé."
    except Exception as e:
        return False, str(e)


# Templates d'e-mails centralises (construction du sujet + du corps HTML)
def _salutation_html(intervenant):
    return f"<p>Bonjour {html.escape(str(intervenant))},</p>"


def template_rdv_planifie(rdv, objet):
    sujet = f"Confirmation d'audience {format_id(rdv.id)} : {objet}"
    corps = (
        "<h3>Audience planifiée</h3>"
        f"{_salutation_html(rdv.intervenant)}"
        f"<p>Un rendez-vous a été planifié pour vous le "
        f"{rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}.</p>"
    )
    return sujet, corps


def template_rdv_accepte(rdv):
    sujet = f"Confirmation d'audience {format_id(rdv.id)} : {rdv.titre}"
    corps = (
        "<h3>Audience acceptée</h3>"
        f"{_salutation_html(rdv.intervenant)}"
        f"<p>Votre demande d'audience a été acceptée pour le "
        f"{rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}.</p>"
    )
    return sujet, corps


def template_rdv_refuse(rdv):
    sujet = f"Annulation de demande d'audience {format_id(rdv.id)}"
    corps = (
        "<h3>Audience annulée</h3>"
        f"{_salutation_html(rdv.intervenant)}"
        "<p>Votre demande d'audience a été annulée.</p>"
    )
    return sujet, corps


def template_code_reset(code):
    sujet = "Lamina - Code de réinitialisation de mot de passe"
    corps = (
        "<h3>Réinitialisation de mot de passe</h3>"
        f"<p>Voici votre code de vérification sécurisé : <b>{code}</b></p>"
        "<p>Ce code est valable pendant 15 minutes.</p>"
    )
    return sujet, corps