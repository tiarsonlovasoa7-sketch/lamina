# Lamina - Gestion des audiences
# Point d'entree : configuration, navigation et orchestration des pages.
import streamlit as st
from dotenv import load_dotenv

from database import RendezVous, init_db, trouver_compte
from services.auth import logout
from services.db import get_db
from ui.components import afficher_chargement, afficher_ecran_intro, show_notification
from ui.pages import page_dashboard, page_gestion_equipe, page_historique, page_planning, page_saisie, page_validation
from ui.personal import interface_personnel
from ui.team import interface_equipe
from utils import libelle_role

load_dotenv()
init_db()

# Configuration de la page Streamlit pour une utilisation adaptee aux mobiles et ordinateurs
st.set_page_config(page_title="Lamina", layout="wide")

# PWA : metas et manifest injectees dans <head> pour rendre l'application installable
st.markdown(
    """
    <script>
    (function () {
        function ajouter(relation, href) {
            var l = document.createElement("link");
            l.rel = relation;
            l.href = href;
            document.head.appendChild(l);
        }
        function ajouterMeta(nom, contenu) {
            var m = document.createElement("meta");
            m.name = nom;
            m.content = contenu;
            document.head.appendChild(m);
        }
        ajouter("manifest", "/static/manifest.webmanifest");
        ajouter("icon", "/static/icone-192.png");
        ajouter("apple-touch-icon", "/static/icone-180.png");
        ajouterMeta("theme-color", "#C0392B");
        ajouterMeta("mobile-web-app-capable", "yes");
        ajouterMeta("apple-mobile-web-app-capable", "yes");
        ajouterMeta("apple-mobile-web-app-status-bar-style", "black-translucent");
        ajouterMeta("apple-mobile-web-app-title", "Lamina");
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

# Chargeur plein ecran declenche au clic. Les scripts ne s'executent pas dans st.markdown,
# on passe donc par st.iframe (script + acces meme-origine autorises) qui rejoint le DOM
# principal de l'application via window.parent.document.
st.iframe(
    """
    <div style="position:relative;width:0;height:0;overflow:hidden"></div>
    <script>
    (function () {
        try {
            var doc = window.parent.document;
            if (doc.__laminaLoaderJs) { return; }
            doc.__laminaLoaderJs = true;

            var voile = null;
            var enAttente = false;
            var minuteur = null;

            function creerVoile() {
                var v = doc.createElement("div");
                v.className = "lamina-voile-js";
                v.innerHTML = '<div class="lamina-nom-js">Lamina</div><div class="lamina-spin-js"></div><div class="lamina-texte-js">Veuillez patienter</div>';
                doc.body.appendChild(v);
                return v;
            }

            function montrer() {
                if (!voile) voile = creerVoile();
                appliquerThemeVoile();
                voile.classList.add("actif");
                enAttente = true;
                clearTimeout(minuteur);
                minuteur = setTimeout(masquer, 8000);
            }

            function masquer() {
                if (voile) voile.classList.remove("actif");
                enAttente = false;
                clearTimeout(minuteur);
            }

            function themeSombre() {
                var attr = doc.documentElement.getAttribute && doc.documentElement.getAttribute("data-theme");
                if (attr === "dark") return true;
                if (attr === "light") return false;
                var corpAttr = doc.body.getAttribute && doc.body.getAttribute("data-theme");
                if (corpAttr === "dark") return true;
                if (corpAttr === "light") return false;
                try {
                    var bg = getComputedStyle(doc.body).backgroundColor;
                    var m = /rgba?\\(\\s*(\\d+)[,\\s]+(\\d+)[,\\s]+(\\d+)/.exec(bg);
                    if (m) {
                        var l = 0.299 * Number(m[1]) + 0.587 * Number(m[2]) + 0.114 * Number(m[3]);
                        return l < 128;
                    }
                } catch (e) {}
                return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
            }

            function appliquerThemeVoile() {
                if (!voile) return;
                voile.classList.remove("theme-sombre");
                voile.classList.remove("theme-clair");
                voile.classList.add(themeSombre() ? "theme-sombre" : "theme-clair");
            }

            function appliquerThemeIntro() {
                var intro = doc.querySelector(".lamina-intro");
                if (!intro) return;
                intro.classList.remove("theme-sombre");
                intro.classList.remove("theme-clair");
                intro.classList.add(themeSombre() ? "theme-sombre" : "theme-clair");
            }

            function estTelechargement(el) {
                var tid = el.getAttribute("data-testid") || "";
                return tid.toLowerCase().indexOf("download") !== -1;
            }

            function estCosmetique(el) {
                if (el.closest) {
                    var anc = el.closest('[data-testid*="SidebarCollapseButton"], [data-testid*="SidebarExpandButton"], [data-testid*="stExpandSidebarButton"], [data-testid*="stSidebarCollapseButton"], [data-testid*="SidebarCollapse"]');
                    if (anc) return true;
                }
                var tid = el.getAttribute("data-testid") || "";
                if (tid.indexOf("SidebarCollapse") !== -1) return true;
                if (tid.indexOf("ExpandSidebarButton") !== -1) return true;
                if (tid.indexOf("stPopover") !== -1) return true;
                if (tid.indexOf("stMainMenu") !== -1) return true;
                if ((el.getAttribute && el.getAttribute("aria-label") === "Close") ||
                    (el.closest && el.closest('[data-testid="stToast"], [data-testid="stAlert"]'))) {
                    return true;
                }
                return false;
            }

            function estDansSidebar(el) {
                if (!el.closest) return false;
                return !!el.closest('[data-testid="stSidebar"]');
            }

            function estDansPopover(el) {
                if (!el.closest) return false;
                return !!el.closest('[data-testid="stPopover"]');
            }

            function estMobile() {
                return doc.documentElement.clientWidth <= 700;
            }

            function replierSidebar() {
                var barre = doc.querySelector('[data-testid="stSidebar"]');
                if (!barre) return;
                if (barre.getAttribute("aria-expanded") !== "true") return;
                var collapse = doc.querySelector('[data-testid="stSidebarCollapseButton"] button, button[data-testid="stSidebarCollapseButton"]');
                if (collapse) {
                    collapse.click();
                    return;
                }
                var cible = doc.querySelector('[data-testid="stMain"]') || doc.querySelector('[data-testid="stApp"]') || doc.body;
                if (cible) {
                    cible.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true }));
                }
            }

            var iconesEnLigne = ["arrow_back", "swap_horiz", "house"];

            var ICONES_FILTRES = {
                "search": "\\ue8b6",
                "calendar_month": "\\uebcc",
            };

            function appliquerIcônesFiltres() {
                // Icône de recherche sur les champs dont le placeholder commence par "Rechercher"
                var textes = doc.querySelectorAll('div[data-testid="stTextInput"]');
                for (var i = 0; i < textes.length; i++) {
                    var input = textes[i].querySelector('input');
                    if (!input) continue;
                    var ph = (input.getAttribute("placeholder") || "").toLowerCase();
                    if (ph.indexOf("rechercher") !== 0) continue;
                    if (textes[i].querySelector(".lamina-icone-recherche")) continue;
                    textes[i].classList.add("lamina-filtre-champ");
                    var span = doc.createElement("span");
                    span.className = "lamina-icone-recherche lamina-icone";
                    span.textContent = ICONES_FILTRES["search"];
                    textes[i].appendChild(span);
                    if (window.getComputedStyle(input).paddingLeft === "0px" || parseFloat(window.getComputedStyle(input).paddingLeft) < 40) {
                        input.style.paddingLeft = "2.5rem";
                    }
                }
                // Icône de calendrier sur le filtre de période (date range)
                var dates = doc.querySelectorAll('div[data-testid="stDateInput"]');
                for (var j = 0; j < dates.length; j++) {
                    if (dates[j].querySelector(".lamina-icone-calendrier")) continue;
                    // L'icône est centrée dans la boîte de saisie (et non le widget, qui contient le libellé)
                    var conteneur = dates[j].querySelector('[data-testid="stDateInputField"]') || dates[j];
                    conteneur.classList.add("lamina-filtre-champ");
                    var span2 = doc.createElement("span");
                    span2.className = "lamina-icone-calendrier lamina-icone";
                    span2.textContent = ICONES_FILTRES["calendar_month"];
                    conteneur.appendChild(span2);
                }
            }

            function appliquerClassesBoutons() {
                var boutons = doc.querySelectorAll('div[data-testid="stButton"] button');
                for (var i = 0; i < boutons.length; i++) {
                    var icone = boutons[i].querySelector('[data-testid="stIconMaterial"]');
                    var nom = icone ? (icone.textContent || "").trim() : "";
                    if (iconesEnLigne.indexOf(nom) !== -1) {
                        boutons[i].classList.add("lamina-bouton-ligne");
                    } else {
                        boutons[i].classList.remove("lamina-bouton-ligne");
                    }
                }
            }

            var conteneur = doc.querySelector('[data-testid="stMain"]');
            var minuteurClasses = null;

            function appliquerClassesDelaye() {
                clearTimeout(minuteurClasses);
                minuteurClasses = setTimeout(appliquerClassesBoutons, 150);
            }

            function surveiller() {
                if (!conteneur) return;
                if (window.MutationObserver) {
                    var obs = new MutationObserver(function (mutations) {
                        appliquerClassesDelaye();
                        appliquerIcônesFiltres();
                        appliquerThemeIntro();
                        if (!enAttente) return;
                        for (var i = 0; i < mutations.length; i++) {
                            if (voile && voile.contains(mutations[i].target)) continue;
                            masquer();
                            return;
                        }
                    });
                    obs.observe(conteneur, { childList: true, subtree: true, characterData: true });
                }
                appliquerClassesBoutons();
                appliquerIcônesFiltres();
                appliquerThemeIntro();
            }

            doc.addEventListener("click", function (evt) {
                var el = evt.target && evt.target.closest("button");
                if (!el) return;
                if (estCosmetique(el)) return;
                if (estDansSidebar(el)) {
                    montrer();
                    if (estMobile()) {
                        replierSidebar();
                    }
                    return;
                }
                if (estDansPopover(el)) return;
                montrer();
                if (estTelechargement(el)) {
                    setTimeout(masquer, 1500);
                }
            }, true);

            doc.addEventListener("click", function (evt) {
                if (!estMobile()) return;
                var el = evt.target && evt.target.closest ?
                    (evt.target.closest('[data-testid="stSidebar"]') ||
                     evt.target.closest('[data-testid="stPopover"]') ||
                     evt.target.closest('button[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"]') ||
                     evt.target.closest('[data-testid="stToast"], [data-testid="stAlert"]')) :
                    null;
                if (el) return;
                replierSidebar();
            }, true);

            doc.addEventListener("keydown", function (evt) {
                if (evt.key !== "Enter") return;
                var el = evt.target && evt.target.closest("input, textarea");
                if (el) montrer();
            }, true);

            surveiller();
        } catch (e) {}
    })();
    </script>
    """,
    height=5,
)

# Style global : titres rouges, ombre et elevation au toucher, navigation arrondie
st.markdown(
    """
    <style>
    h1, h2, h3 {
        color: #C0392B !important;
    }
    .titre-bienvenue {
        color: #9AA0A6 !important;
        font-weight: 400 !important;
    }
    .lamina-nom {
        color: #C0392B !important;
        font-weight: 700 !important;
    }
    .lamina-titre-appli {
        color: #C0392B !important;
        font-weight: 700 !important;
    }
    .titre-mode {
        color: #2563EB !important;
    }
    @keyframes lamina-cascade {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div {
        animation: lamina-cascade 0.55s ease-out backwards;
    }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.08s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.16s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.24s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.32s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(6) { animation-delay: 0.4s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(7) { animation-delay: 0.48s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(8) { animation-delay: 0.56s; }
    section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:nth-child(n+9) { animation-delay: 0.64s; }
    @media (prefers-reduced-motion: reduce) {
        section[data-testid="stMain"] [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div {
            animation: none !important;
        }
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        color: #2563EB !important;
    }
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stNumberInput"] div[data-baseweb="input"],
    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-testid="stDateInput"] div[data-baseweb="input"],
    div[data-testid="stTimeInput"] div[data-baseweb="input"] {
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }

    /* Icônes de recherche et de période sur les barres de filtres */
    .lamina-filtre-champ {
        position: relative;
    }
    .lamina-icone {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        left: 0.8rem;
        color: #2563EB;
        font-size: 1.3rem;
        line-height: 1;
        pointer-events: none;
        z-index: 5;
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif;
    }
    .lamina-icone-calendrier {
        color: #2563EB;
    }
    /* Alignement : recherche et période sur la même ligne, mêmes dimensions */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stDateInput"])
        div[data-testid="stTextInput"] input {
        min-height: 2.65rem !important;
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stDateInput"])
        div[data-testid="stDateInput"] div[data-baseweb="input"] {
        min-height: 2.65rem !important;
        display: flex;
        align-items: center;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stDateInput"])
        div[data-testid="stDateInput"] input {
        padding-left: 2.5rem !important;
    }
    /* Dégagement du texte du champ de début de période pour ne pas recouvrir l'icône calendrier */
    div[data-testid="stDateInput"] div[data-range-field="start"] {
        padding-left: 2.2rem !important;
    }
    div[data-testid="stDateInput"] div[data-range-field="start"] [role="group"] {
        margin-left: 1rem !important;
    }
    /* Dégagement du texte pour un champ date simple (avec libellé), icône centrée dans la boîte */
    div[data-testid="stDateInput"]:not(:has(div[data-range-field])) div[data-testid="stDateInputField"] [role="group"] {
        margin-left: 2.5rem !important;
    }
    div[data-testid="stButton"] button:hover,
    div[data-testid="stButton"] button:active,
    div[data-testid="stButton"] button:focus-visible,
    div[data-testid="stFormSubmitButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:active,
    div[data-testid="stFormSubmitButton"] button:focus-visible {
        box-shadow: 0 4px 14px rgba(49, 56, 65, 0.28);
        transform: translateY(-2px);
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTimeInput"] div[data-baseweb="input"]:focus-within {
        box-shadow: 0 4px 14px rgba(49, 56, 65, 0.28);
    }
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stDownloadButton"] button,
    button[data-testid="stPopoverButton"] {
        justify-content: flex-start !important;
        text-align: left !important;
    }
    button[data-testid="stPopoverButton"] div[aria-hidden="true"] {
        display: none !important;
    }
    button[data-testid="stPopoverButton"] {
        width: 3.5rem !important;
        min-width: 3.5rem !important;
        height: 3.5rem !important;
        padding: 0 !important;
        justify-content: center !important;
    }
    [data-testid="stPopoverBody"] div[data-testid="stButton"] button {
        min-height: 3.5rem !important;
        font-size: 1rem !important;
    }
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stPopover"]) > [data-testid="stColumn"]:last-child {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stPopoverBody"] div[data-testid="stButton"] button [data-has-shortcut] {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.5rem !important;
        text-align: left !important;
    }
    [data-testid="stPopoverBody"] div[data-testid="stButton"] button {
        justify-content: flex-start !important;
    }
    @media (max-width: 700px) {
        [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stPopover"]) {
            flex-wrap: nowrap !important;
        }
        [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stPopover"]) > [data-testid="stColumn"]:first-child {
            flex: 1 1 0% !important;
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [data-testid="stPopover"]) > [data-testid="stColumn"]:last-child {
            flex: 0 0 3.5rem !important;
            min-width: 3.5rem !important;
        }
        button[data-testid="stPopoverButton"] {
            width: 3rem !important;
            min-width: 3rem !important;
            height: 3rem !important;
        }
        [data-testid="stPopoverBody"] div[data-testid="stButton"] button {
            min-height: 3rem !important;
        }
    }
    /* Icônes au-dessus du texte (hors sidebar, form-submit et boutons "Retour/Changer de compte/Changer d'entreprise") */
    div[data-testid="stButton"] button [data-has-shortcut] {
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem !important;
        text-align: center !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button [data-has-shortcut],
    div[data-testid="stFormSubmitButton"] button [data-has-shortcut] {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.5rem !important;
        text-align: left !important;
    }
    div[data-testid="stButton"] button.lamina-bouton-ligne [data-has-shortcut] {
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 0.5rem !important;
        text-align: left !important;
    }
    div[data-testid="stButton"] button.lamina-bouton-ligne {
        justify-content: flex-start !important;
    }
    div[data-testid="stButton"] button {
        justify-content: center !important;
    }
    section[data-testid="stSidebar"] {
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
        border: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stContainer"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        justify-content: flex-start !important;
        border-radius: 16px;
        border: none !important;
    }
    section[data-testid="stSidebar"] h1 {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        margin: 0.1rem 0 0.35rem 0 !important;
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stContainer"] {
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        min-height: 2.1rem !important;
        font-size: 0.9rem !important;
        line-height: 1.15 !important;
        border-radius: 14px;
    }
    section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {
        font-size: 0.78rem !important;
        margin-bottom: 0.1rem !important;
        opacity: 0.9;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1rem !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] {
        background: #C0392B !important;
        border-color: #C0392B !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover,
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:focus-visible {
        background: #A93226 !important;
        border-color: #A93226 !important;
        box-shadow: 0 4px 14px rgba(192, 57, 43, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background: #15803D !important;
        border-color: #15803D !important;
        color: #FFFFFF !important;
    }
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover,
    button[data-testid="stBaseButton-primaryFormSubmit"]:focus-visible {
        background: #166534 !important;
        border-color: #166534 !important;
        box-shadow: 0 4px 14px rgba(21, 128, 61, 0.42) !important;
        transform: translateY(-2px) !important;
    }
    .lamina-voile-js {
        position: fixed;
        inset: 0;
        z-index: 999998;
        display: none !important;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1.25rem;
        pointer-events: none;
        background: rgba(247, 246, 242, 0.97);
        backdrop-filter: blur(4px);
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    .lamina-voile-js.actif {
        display: flex !important;
    }
    .lamina-nom-js {
        color: #C0392B;
        font-size: 40px;
        font-weight: 700;
        letter-spacing: 2px;
        font-family: "Menlo", "Consolas", monospace;
    }
    .lamina-spin-js {
        width: 46px;
        height: 46px;
        border: 4px solid rgba(192, 57, 43, 0.18);
        border-top-color: #C0392B;
        border-right-color: #C0392B;
        border-radius: 50%;
        box-shadow: 0 0 14px rgba(192, 57, 43, 0.25);
        animation: lamina-spin 0.8s linear infinite;
    }
    .lamina-texte-js {
        color: #4B5563;
        font-size: 1.05rem;
        font-weight: 500;
        letter-spacing: 0.01em;
        text-align: center;
        white-space: nowrap;
    }

    /* ------- Adaptation du Voile au Mode Sombre (Theme #171B21 & #C0392B) ------- */
    .lamina-voile-js.theme-clair {
        background: rgba(247, 246, 242, 0.97) !important;
        backdrop-filter: blur(4px) !important;
    }
    .lamina-voile-js.theme-clair .lamina-nom-js {
        color: #C0392B !important;
        text-shadow: none !important;
    }
    .lamina-voile-js.theme-clair .lamina-spin-js {
        border-color: rgba(192, 57, 43, 0.18) !important;
        border-top-color: #C0392B !important;
        border-right-color: #C0392B !important;
        box-shadow: 0 0 14px rgba(192, 57, 43, 0.25) !important;
    }
    .lamina-voile-js.theme-clair .lamina-texte-js {
        color: #4B5563 !important;
    }
    .lamina-voile-js.theme-sombre,
    [data-theme="dark"] .lamina-voile-js,
    body.dark-theme .lamina-voile-js {
        background: rgba(23, 27, 33, 0.97) !important;
        backdrop-filter: blur(6px) !important;
    }
    .lamina-voile-js.theme-sombre .lamina-nom-js,
    [data-theme="dark"] .lamina-voile-js .lamina-nom-js {
        color: #C0392B !important;
        text-shadow: 0 0 14px rgba(192, 57, 43, 0.45) !important;
    }
    .lamina-voile-js.theme-sombre .lamina-spin-js,
    [data-theme="dark"] .lamina-voile-js .lamina-spin-js {
        border-color: rgba(192, 57, 43, 0.22) !important;
        border-top-color: #C0392B !important;
        border-right-color: #C0392B !important;
        box-shadow: 0 0 18px rgba(192, 57, 43, 0.38) !important;
    }
    .lamina-voile-js.theme-sombre .lamina-texte-js,
    [data-theme="dark"] .lamina-voile-js .lamina-texte-js {
        color: #9AA0A6 !important;
    }

    .lamina-loader {
        position: fixed;
        inset: 0;
        z-index: 999999;
        background: rgba(247, 246, 242, 0.96);
        pointer-events: none;
    }
    [data-theme="dark"] .lamina-loader,
    body.dark-theme .lamina-loader {
        background: rgba(23, 27, 33, 0.97) !important;
    }

    @media (prefers-color-scheme: dark) {
        .lamina-voile-js:not(.theme-clair) {
            background: rgba(23, 27, 33, 0.97);
            backdrop-filter: blur(6px);
        }
        .lamina-voile-js:not(.theme-clair) .lamina-nom-js {
            color: #C0392B;
            text-shadow: 0 0 14px rgba(192, 57, 43, 0.45);
        }
        .lamina-voile-js:not(.theme-clair) .lamina-spin-js {
            border-color: rgba(192, 57, 43, 0.22);
            border-top-color: #C0392B;
            border-right-color: #C0392B;
            box-shadow: 0 0 18px rgba(192, 57, 43, 0.38);
        }
        .lamina-voile-js:not(.theme-clair) .lamina-texte-js {
            color: #9AA0A6;
        }
        .lamina-loader:not(.theme-clair) {
            background: rgba(23, 27, 33, 0.97);
        }
    }

    @keyframes lamina-spin {
        to { transform: rotate(360deg); }
    }
    /* ------- Adaptation mobile ------- */
    @media (max-width: 700px) {
        section[data-testid="stMain"] [data-testid="stMainBlockContainer"] {
            padding: 0.6rem 0.9rem 2.5rem !important;
        }
        section[data-testid="stMain"] [data-testid="stVerticalBlock"] {
            gap: 0.55rem !important;
        }
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stDownloadButton"] button {
            min-height: 3rem !important;
            padding: 0.5rem 0.85rem !important;
            font-size: 1rem !important;
            line-height: 1.25 !important;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-testid="stTimeInput"] div[data-baseweb="input"],
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 2.9rem !important;
        }
        [data-testid="stColumn"] {
            flex: 1 1 100% !important;
            max-width: 100% !important;
        }
        section[data-testid="stMain"] h1 {
            font-size: 1.5rem !important;
        }
        section[data-testid="stMain"] h3 {
            font-size: 1.05rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialisation de l etat de session de l application
if "mode" not in st.session_state:
    st.session_state.mode = None
if "user" not in st.session_state:
    st.session_state.user = None
if "tenant_db" not in st.session_state:
    st.session_state.tenant_db = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Tableau de bord"
if "just_logged_in" not in st.session_state:
    st.session_state.just_logged_in = False
if "editing_rdv_id" not in st.session_state:
    st.session_state.editing_rdv_id = None
if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

if "flash_msg" not in st.session_state:
    st.session_state.flash_msg = None
if "flash_type" not in st.session_state:
    st.session_state.flash_type = "success"

# Affiche l indicateur de chargement
if st.session_state.pop("_page_chargement", False):
    pass

# Ecran de lancement unique : "Lamina" s'ecrit au clavier au tout debut de session
if st.session_state.get("intro_jouee") is None:
    st.session_state.intro_jouee = True
    afficher_ecran_intro()

# Affichage des messages flash en attente
if st.session_state.flash_msg:
    show_notification(st.session_state.flash_msg, st.session_state.flash_type)
    st.session_state.flash_msg = None

# Ecran de bienvenue avec le choix du mode d utilisation
if st.session_state.user is None and st.session_state.mode is None:
    st.markdown("""
        <style>
        [data-testid="stMain"] [data-testid="stButton"] {
            display: flex;
            justify-content: center;
        }
        [data-testid="stMain"] [data-testid="stButton"] button,
        [data-testid="stMain"] .stButton button,
        [data-testid="stMain"] button[data-testid^="stBaseButton-"] {
            min-height: 4.5rem !important;
            width: min(22rem, 90%) !important;
            padding: 0.7rem 1.1rem !important;
            text-align: center !important;
            cursor: pointer !important;
        }
        [data-testid="stMain"] button p {
            flex: 0 0 100% !important;
            max-width: 100% !important;
            display: block !important;
            white-space: normal !important;
        }
        [data-testid="stMain"] button p:first-of-type {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            line-height: 1.25 !important;
            margin: 0 0 0.3rem 0 !important;
        }
        [data-testid="stMain"] button p:last-of-type {
            font-size: 0.95rem !important;
            line-height: 1.3 !important;
            margin: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    st.markdown('<h1 class="titre-bienvenue" style="text-align:center;">Bienvenue sur l\'application <span class="lamina-nom">Lamina</span></h1>', unsafe_allow_html=True)
    st.caption("Choisissez votre mode d'utilisation", text_alignment="center")

    st.space("medium")

    col_gauche, col_milieu, col_droite = st.columns([1, 2, 1])

    with col_milieu:
        if st.button(":blue[**Mode personnel**]\n\nGérer votre propre programme", key="mode_personnel", icon=":material/person:", width="stretch", type="primary"):
            st.session_state.mode = "personnel"
            st.session_state.tenant_db = None
            st.session_state.perso_selection_nom = None
            st.session_state.perso_selection_chemin = None
            afficher_chargement()

        st.space("small")

        if st.button(":blue[**Mode équipe**]\n\nAvec plusieurs personnes selon votre entreprise", key="mode_equipe", icon=":material/apartment:", width="stretch"):
            st.session_state.mode = "equipe"
            st.session_state.tenant_db = None
            st.session_state.equipe_selection_chemin = None
            st.session_state.equipe_selection_nom = None
            st.session_state.equipe_selection_membre = None
            st.session_state.equipe_selection_libelle = None
            afficher_chargement()

    st.stop()

# Interface pour les utilisateurs non connectes selon le mode choisi
if st.session_state.user is None:
    st.markdown('<h1 class="lamina-titre-appli" style="text-align:center;">Lamina</h1>', unsafe_allow_html=True)
    if st.session_state.mode == "personnel":
        st.caption("Espace personnel : une seule personne, ses rendez-vous", text_alignment="center")
        interface_personnel()
    elif st.session_state.mode == "equipe":
        st.caption("Espace équipe : un Responsable et des Assistant(e)s", text_alignment="center")
        interface_equipe()
    st.stop()

# Interface pour les utilisateurs authentifies
if st.session_state.user is not None:
    user = st.session_state.user
    db = get_db()

    try:
        # Recuperation des statistiques globales
        nb_en_attente = db.query(RendezVous).filter(RendezVous.statut == "En attente").count()

        # Barre latérale d informations et de navigation
        st.sidebar.title("Lamina")
        st.sidebar.space("small")
        with st.sidebar.container():
            st.write(f"**{user['nom']}**")
            if user['role'] == "Personnel":
                st.caption("Mode personnel")
            else:
                compte_actif = trouver_compte(chemin_db=st.session_state.get("tenant_db")) if st.session_state.get("tenant_db") else None
                if compte_actif:
                    st.caption(f"Entreprise : {compte_actif.nom}")
                st.caption(f"Rôle : {libelle_role(user['role'])}")
            if user['role'] == "Directeur" and nb_en_attente > 0:
                st.markdown(f":orange[{nb_en_attente} demande(s) en attente]")

        st.sidebar.divider()
        st.sidebar.subheader("Navigation")

        # Dynamic navigation options based on user role, avec libelles de taille stable
        label_saisie_rdv = "Nouvelle demande de RDV"
        if user['role'] in ("Directeur", "Personnel"):
            label_saisie_rdv = "Ajouter un rendez-vous"

        if user['role'] == "Directeur":
            nav_options = [
                ("Tableau de bord", "Tableau de bord", ":material/dashboard:"),
                ("Saisir une demande", label_saisie_rdv, ":material/event_note:"),
                ("Validation des Audiences", "Validation des Audiences", ":material/fact_check:"),
                ("Planning et Briefs", "Planning et Briefs", ":material/calendar_month:"),
                ("Historique et Exports", "Historique et Exports", ":material/history:"),
                ("Gérer l'équipe", "Gérer l'équipe", ":material/group:")
            ]
        else:
            nav_options = [
                ("Tableau de bord", "Tableau de bord", ":material/dashboard:"),
                ("Saisir une demande", label_saisie_rdv, ":material/event_note:"),
                ("Planning et Briefs", "Planning et Briefs", ":material/calendar_month:"),
                ("Historique et Exports", "Historique et Exports", ":material/history:")
            ]

        # Verification de la cle de navigation valide
        valid_keys = [item[0] for item in nav_options]
        if st.session_state.current_page not in valid_keys:
            st.session_state.current_page = "Tableau de bord"

        # Rendu des boutons de navigation avec animation au changement d onglet
        for page_key, label, icone in nav_options:
            is_active = (st.session_state.current_page == page_key)
            btn_type = "primary" if is_active else "secondary"
            if st.sidebar.button(label, key=f"nav_{page_key}", type=btn_type, icon=icone, width="stretch"):
                if st.session_state.current_page != page_key:
                    st.session_state.current_page = page_key
                st.session_state.editing_rdv_id = None
                afficher_chargement()

        # Bouton de deconnexion dans son propre espace, ecarte en bas de la barre laterale
        st.sidebar.space("large")
        if st.sidebar.button("Se déconnecter", icon=":material/logout:", width="stretch", type="tertiary", key="btn_deconnexion"):
            st.session_state.flash_msg = "Déconnexion effectuée avec succès."
            st.session_state.flash_type = "success"
            logout()
            db.close()
            afficher_chargement()

        # Affichage des notifications d accueil a la premiere connexion
        if st.session_state.just_logged_in:
            if user['role'] == "Directeur":
                if nb_en_attente > 0:
                    show_notification(f"Connexion établie. Vous avez {nb_en_attente} demande(s) en attente.")
                else:
                    show_notification("Connexion établie. Aucune nouvelle demande en attente.")
            elif user['role'] == "Personnel":
                show_notification("Bienvenue en mode personnel. Vous gérez directement vos rendez-vous.")
            else:
                show_notification("Connexion établie. Espace assistant(e) opérationnel.")
            st.session_state.just_logged_in = False

        menu = st.session_state.current_page

        # Dispatcher vers la page demandee
        if menu == "Tableau de bord":
            page_dashboard(user, db)

        elif menu == "Saisir une demande":
            page_saisie(user, db)

        elif menu == "Validation des Audiences" and user['role'] == "Directeur":
            page_validation(user, db)

        elif menu == "Gérer l'équipe" and user['role'] == "Directeur":
            page_gestion_equipe(user, db)

        elif menu == "Planning et Briefs":
            page_planning(user, db)

        elif menu == "Historique et Exports":
            page_historique(user, db)

    finally:
        db.close()