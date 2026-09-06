#!/bin/bash
# Copie les fichiers PWA (manifest, icones, service worker) vers le dossier /static de Streamlit.
# Execute automatiquement par Streamlit Community Cloud avant le lancement de l'application.
set -e

SITE_STATIC=$(python -c "import streamlit, os; print(os.path.join(os.path.dirname(streamlit.__file__), 'static'))")
cp -f pwa/manifest.webmanifest pwa/sw.js pwa/icone-*.png "$SITE_STATIC/"
echo "Fichiers PWA copies vers $SITE_STATIC"