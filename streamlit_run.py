import os
import sys

# Point d'entree unique pour les plateformes d'hebergement
# (Streamlit Cloud, Hugging Face, Fly.io, Render, etc.)

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        os.path.join(os.path.dirname(__file__), "app.py"),
        "--server.port",
        os.getenv("PORT", "8501"),
        "--server.address",
        "0.0.0.0",
    ]
    from streamlit.web import cli as stcli
    raise SystemExit(stcli.main())