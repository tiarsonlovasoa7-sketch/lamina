# Importation des modules pour la gestion de la base de donnees et la securite
import os
import hashlib
import hmac
import re
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

# Dossier contenant l annuaire et les bases de donnees de chaque compte
DOSSIER_BASES = "bases"

# Base de donnees de l annuaire des comptes (entreprises et espaces personnels)
DATABASE_URL = f"sqlite:///{DOSSIER_BASES}/annuaire.db"

# Creation du moteur SQLAlchemy de l annuaire
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Creation de la session de base de donnees de l annuaire
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Definition de la classe de base pour les modeles
Base = declarative_base()

# Fonction pour hacher un mot de passe avec PBKDF2 et un sel unique
def hash_password(password: str, salt: bytes = None) -> str:
    # Nettoyage de la chaine de caractere
    clean_pwd = password.strip() if password else ""
    
    # Generation d un sel aleatoire si aucun sel n est fourni
    if salt is None:
        salt = os.urandom(16)
        
    # Calcul du hachage PBKDF2 avec 100000 iterations
    key = hashlib.pbkdf2_hmac('sha256', clean_pwd.encode('utf-8'), salt, 100000)
    
    # Formatage de la chaine de hachage securisee
    return f"$pbkdf2${salt.hex()}${key.hex()}"

# Function to verify a reset code, supporting both hashed (PBKDF2) and legacy plain codes
def verifier_code_reset(code_saisi: str, code_stocke) -> bool:
    if not code_stocke:
        return False
    # Compatibilite avec les anciens codes stockes en clair
    if not str(code_stocke).startswith("$pbkdf2$"):
        return hmac.compare_digest(str(code_saisi).strip(), str(code_stocke))
    valide, _ = verify_password(code_saisi, code_stocke)
    return valide

# Function to verify a password and detect if an upgrade is required
def verify_password(password: str, stored_hash: str) -> tuple:
    # Nettoyage du mot de passe saisi
    clean_pwd = password.strip() if password else ""
    
    # Verification du format de hachage PBKDF2
    if stored_hash and stored_hash.startswith("$pbkdf2$"):
        try:
            # Extraction des parties du hachage
            _, algo, salt_hex, key_hex = stored_hash.split("$")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            
            # Calcul de la cle pour comparaison
            calculated_key = hashlib.pbkdf2_hmac('sha256', clean_pwd.encode('utf-8'), salt, 100000)
            
            # Comparaison constante en temps pour eviter les attaques temporelles
            is_valid = hmac.compare_digest(calculated_key, expected_key)
            return is_valid, False
        except Exception:
            return False, False
            
    # Traitement des anciens hachages SHA256 simples pour la compatibilite
    legacy_hash = hashlib.sha256(clean_pwd.encode('utf-8')).hexdigest()
    if hmac.compare_digest(legacy_hash, stored_hash):
        # Indique que le mot de passe est valide mais necessite une mise a jour vers PBKDF2
        return True, True
        
    # Retour par defaut si la verification echoue
    return False, False

# Modele de donnee pour enregistrer les comptes dans l annuaire
class Compte(Base):
    __tablename__ = "comptes"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String(20), nullable=False, index=True, default="equipe")
    nom = Column(String(150), nullable=False, index=True)
    email = Column(String(100), nullable=True, index=True)
    chemin_db = Column(String(300), nullable=False)
    cree_le = Column(DateTime, default=datetime.now)

# Modele de donnee pour les utilisateurs (une table par base de compte)
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    mot_de_passe_hash = Column(String(256), nullable=False)
    role = Column(String(50), default="Secretaire")
    code_reset = Column(String(20), nullable=True)
    code_reset_expire = Column(DateTime, nullable=True)

# Modele de donnee pour les rendez-vous (une table par base de compte)
class RendezVous(Base):
    __tablename__ = "rendezvous"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(200), nullable=False)
    intervenant = Column(String(100), nullable=False)
    email_intervenant = Column(String(100), nullable=True)
    telephone = Column(String(30), nullable=True)
    organisme = Column(String(100), nullable=True)
    priorite = Column(String(20), default="Moyenne")
    date_heure = Column(DateTime, nullable=False)
    duree_minutes = Column(Integer, default=30)
    contexte_notes = Column(Text, nullable=True)
    statut = Column(String(30), default="En attente")
    date_creation = Column(DateTime, default=datetime.now)

# Fonction pour generer un chemin de base de donnees libre pour un compte
def generer_chemin_base(nom: str) -> str:
    # Transformation du nom en identifiant de fichier sur
    slug = re.sub(r"[^a-z0-9]+", "-", (nom or "").lower().strip()).strip("-")
    if not slug:
        slug = uuid.uuid4().hex[:8]
    
    # Ajout d un suffixe aleatoire si le fichier existe deja
    chemin = f"{DOSSIER_BASES}/{slug}.db"
    if os.path.exists(chemin):
        chemin = f"{DOSSIER_BASES}/{slug}-{uuid.uuid4().hex[:6]}.db"
    return chemin

# Colonnes ajoutees apres la creation initiale du schema (echelonnable)
COLONNES_OPTIONNELLES = {
    "utilisateurs": [
        ("nom_complet", "VARCHAR(100)"),
        ("email", "VARCHAR(100)"),
        ("mot_de_passe_hash", "VARCHAR(256)"),
        ("role", "VARCHAR(50) DEFAULT 'Secretaire'"),
        ("code_reset", "VARCHAR(256)"),
        ("code_reset_expire", "DATETIME"),
    ],
    "rendezvous": [
        ("titre", "VARCHAR(200)"),
        ("intervenant", "VARCHAR(100)"),
        ("email_intervenant", "VARCHAR(100)"),
        ("telephone", "VARCHAR(30)"),
        ("organisme", "VARCHAR(100)"),
        ("priorite", "VARCHAR(20) DEFAULT 'Moyenne'"),
        ("date_heure", "DATETIME"),
        ("duree_minutes", "INTEGER DEFAULT 30"),
        ("contexte_notes", "TEXT"),
        ("statut", "VARCHAR(30) DEFAULT 'En attente'"),
        ("date_creation", "DATETIME"),
    ],
}

# Fonction d ajout des colonnes manquantes sur une base deja creee (migration legere)
def migrer_schema(moteur):
    with moteur.connect() as conn:
        for table, colonnes in COLONNES_OPTIONNELLES.items():
            existantes = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            for nom, type_sql in colonnes:
                if nom not in existantes:
                    conn.exec_driver_sql(
                        f"ALTER TABLE {table} ADD COLUMN {nom} {type_sql}"
                    )
                    print(f"[migration] colonne ajoutee : {table}.{nom}")

# Function to create a session towards a client database
def creer_session_sur(chemin_db: str):
    url = f"sqlite:///{chemin_db}"
    moteur = create_engine(url, connect_args={"check_same_thread": False})
    # Creation des tables du schema dans la base du compte
    Base.metadata.create_all(bind=moteur)
    # Ajout des colonnes manquantes pour les bases existantes
    migrer_schema(moteur)
    return sessionmaker(autocommit=False, autoflush=False, bind=moteur)()

# Fonction pour enregistrer un compte dans l annuaire
def creer_compte(mode, nom, chemin_db, email=None):
    db = SessionLocal()
    try:
        compte = Compte(mode=mode, nom=nom, email=email, chemin_db=chemin_db)
        db.add(compte)
        db.commit()
        # Valeurs capturees avant la fermeture de la session
        return {"id": compte.id, "mode": mode, "nom": nom, "email": email, "chemin_db": chemin_db}, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()

# Fonction pour rechercher un compte dans l annuaire selon differents criteres
def trouver_compte(mode=None, nom=None, email=None, chemin_db=None):
    db = SessionLocal()
    try:
        requete = db.query(Compte)
        if mode:
            requete = requete.filter(Compte.mode == mode)
        if nom:
            requete = requete.filter(func.lower(Compte.nom) == nom.strip().lower())
        if email:
            requete = requete.filter(func.lower(Compte.email) == email.strip().lower())
        if chemin_db:
            requete = requete.filter(Compte.chemin_db == chemin_db)
        return requete.first()
    finally:
        db.close()

# Fonction pour lister tous les comptes d un mode donne, tries du plus recent au plus ancien
def lister_comptes(mode=None):
    db = SessionLocal()
    try:
        requete = db.query(Compte)
        if mode:
            requete = requete.filter(Compte.mode == mode)
        return requete.order_by(Compte.cree_le.desc(), Compte.id.desc()).all()
    finally:
        db.close()

# Fonction pour supprimer un compte de l annuaire ainsi que sa base de donnees
def supprimer_compte(compte_id):
    db = SessionLocal()
    try:
        compte = db.get(Compte, compte_id)
        if not compte:
            return None, "Compte introuvable."
        chemin = compte.chemin_db
        nom = compte.nom
        db.delete(compte)
        db.commit()
        fichier_supprime = False
        if chemin and os.path.exists(chemin):
            try:
                os.remove(chemin)
                fichier_supprime = True
            except OSError:
                fichier_supprime = False
        return {"nom": nom, "chemin_db": chemin, "fichier_supprime": fichier_supprime}, None
    except Exception as e:
        db.rollback()
        return None, str(e)
    finally:
        db.close()

# Fonction pour lister les utilisateurs d un compte (base du compte)
def lister_utilisateurs(chemin_db):
    session = None
    try:
        session = creer_session_sur(chemin_db)
        return session.query(Utilisateur).order_by(Utilisateur.nom_complet.asc()).all()
    finally:
        if session:
            session.close()

# Fonction d initialisation de l annuaire des comptes
def init_db():
    os.makedirs(DOSSIER_BASES, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    migrer_schema(engine)