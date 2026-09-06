# Lamina - Gestion des audiences

Application de gestion de rendez-vous et d'audiences, utilisable en
**mode personnel** (une personne gère son propre programme) ou en
**mode équipe** (un Responsable avec des Assistant(e)s), avec envoi
automatique d'e-mails et génération de briefs PDF.

- **Interface** : Streamlit (web + mobile/PWA installable)
- **Base de données** : SQLite multitenant (une base par compte)
- **Sécurité** : mots de passe hachés (PBKDF2), codes de réinitialisation
  valables 15 minutes, verrouillage temporaire après échecs répétés

## Démarrage local

```powershell
python -m venv env
env\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env   # configurer SMTP si besoin
env\Scripts\python -m streamlit run app.py
```

## Tests

```powershell
env\Scripts\python tests.py
```

## Déploiement sur Streamlit Community Cloud

1. Poussez le projet sur un dépôt GitHub.
2. Sur [streamlit.io/cloud](https://streamlit.io/cloud), cliquez sur
   **New app**, choisissez le dépôt, la branche `main` et le fichier
   `app.py`.
3. Ajoutez les secrets (onglet **Secrets**) :

```toml
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_EMAIL="votre@gmail.com"
SMTP_PASSWORD="mot de passe d'application"
```

Le déploiement exécute automatiquement `setup.sh`, qui copie les fichiers
PWA (`pwa/`) dans le dossier `/static` de Streamlit pour rendre l'application
installable sur téléphone.

> Note : le stockage SQLite n'est pas persistant sur le Cloud Community.
> Les données sont conservées tant que le serveur reste actif. Pour une
> utilisation durable, prévoyez une base distante (PostgreSQL).