import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration loaded from environment variables."""

    # Secret key for cryptographic signing (itsdangerous and Flask sessions)
    SECRET_KEY = os.getenv("SECRET_KEY", "geoqr-insecure-dev-secret-key-change-in-prod-2026")

    # Anti-Proxy QR code rotation window in seconds (Strict 25s window)
    QR_TOKEN_MAX_AGE_SECONDS = int(os.getenv("QR_TOKEN_MAX_AGE_SECONDS", 25))

    # Path to Firebase service account credentials JSON file
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        str(BASE_DIR / "firebase" / "serviceAccountKey.json")
    )

    # Server environment
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")

    # Host and Port configuration
    HOST = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_RUN_PORT", 5000))
