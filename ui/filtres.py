# Filtres de recherche et de periode pour les listes de l application
import unicodedata

import streamlit as st


def _normaliser(texte):
    """Normalise un texte : minuscules et retrait des accents pour une recherche tolérante."""
    chaine = unicodedata.normalize("NFD", texte or "")
    return "".join(c for c in chaine if unicodedata.category(c) != "Mn").lower()


def texte_contient(texte, reference) -> bool:
    """Vrai si reference contient texte (insensible a la casse et aux accents)."""
    return _normaliser(texte) in _normaliser(reference)


def zone_recherche(cle, placeholder="Rechercher...", label="Recherche"):
    """Barre de recherche libre renvoyant le texte saisi."""
    return st.text_input(
        label,
        key=cle,
        placeholder=placeholder,
        label_visibility="collapsed",
    )


def plage_dates(cle, label="Période"):
    """Filtre par periode : retourne (date_debut, date_fin) ou (None, None)."""
    selection = st.date_input(
        label,
        value=(),
        key=cle,
    )
    if not selection:
        return None, None
    valeurs = selection if isinstance(selection, (list, tuple)) else (selection,)
    if len(valeurs) < 2:
        return None, None
    debut, fin = valeurs[0], valeurs[1]
    if hasattr(debut, "date"):
        debut = debut.date()
    if hasattr(fin, "date"):
        fin = fin.date()
    return (debut or None), (fin or None)


def barre_recherche_et_dates(cle_prefixe, placeholder="Rechercher un titre, intervenant ou organisme..."):
    """Barre combinee : recherche libre + periode, renvoyant (texte, date_debut, date_fin)."""
    col_recherche, col_dates = st.columns([3, 2])
    with col_recherche:
        texte = zone_recherche(f"{cle_prefixe}_recherche", placeholder=placeholder)
    with col_dates:
        date_debut, date_fin = plage_dates(f"{cle_prefixe}_dates")
    return texte, date_debut, date_fin


def filtrer_rdv(rdvs, texte, date_debut, date_fin):
    """Filtre une liste de rendez-vous par texte libre et par periode."""
    sortie = []
    for rdv in rdvs:
        if texte:
            champs = [
                rdv.titre, rdv.intervenant, rdv.organisme,
                rdv.email_intervenant, rdv.telephone, rdv.contexte_notes,
            ]
            if not any(texte_contient(texte, c) for c in champs):
                continue
        if date_debut and rdv.date_heure.date() < date_debut:
            continue
        if date_fin and rdv.date_heure.date() > date_fin:
            continue
        sortie.append(rdv)
    return sortie


def filtrer_objets(objets, attributs, texte):
    """Filtre une liste d objets par texte libre sur plusieurs attributs."""
    if not texte:
        return list(objets)
    return [o for o in objets if any(texte_contient(texte, getattr(o, a, None)) for a in attributs)]