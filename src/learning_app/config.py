from pathlib import Path
import os
import secrets

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY") or secrets.token_urlsafe(32)
    DATABASE = PROJECT_ROOT / "instance" / "learning.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
