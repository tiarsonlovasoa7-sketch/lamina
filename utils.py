# Utilitaires partages : nettoyage de textes, securite des mots de passe, formatage
import html


def clean_str(valeur: str) -> str:
    """Nettoie et valide une chaine de caracteres."""
    return valeur.strip() if valeur else ""


def sanitize_text(valeur: str) -> str:
    """Nettoie et valide un texte pour le stockage."""
    return clean_str(valeur)


def validate_password_strength(password: str) -> tuple:
    """Verifie la complexite du mot de passe."""
    clean_pwd = clean_str(password)
    if len(clean_pwd) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    has_digit = any(char.isdigit() for char in clean_pwd)
    has_letter = any(char.isalpha() for char in clean_pwd)
    if not (has_digit and has_letter):
        return False, "Le mot de passe doit contenir des lettres et au moins un chiffre."
    return True, "Mot de passe conforme."


def format_id(item_id) -> str:
    """Formate les identifiants sous forme numerique propre."""
    return f"{item_id:04d}"


def libelle_role(role: str) -> str:
    """Affiche un libelle convivial pour un role."""
    return {"Directeur": "Responsable", "Secretaire": "Assistant(e)"}.get(role, role)