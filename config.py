import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
SQLITE_DATABASE_PATH = PROJECT_DIR / "instance" / "compatibilitymatch.db"


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "compatibilitymatch-dev-key")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{SQLITE_DATABASE_PATH.as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LLM_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    # Keep this key outside the database and source control. Required to encrypt
    # API keys entered by admins and to decrypt them at runtime.
    GEMINI_ENCRYPTION_KEY = os.getenv("GEMINI_ENCRYPTION_KEY", "").strip()
    LLM_BASE_URL = os.getenv(
        "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
    ).rstrip("/")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite")
    # Standard paid-tier prices for Gemini 3.1 Flash-Lite. Free-tier keys
    # incur no token charge; override these values when using another model.
    LLM_INPUT_COST_PER_1M = float(os.getenv("LLM_INPUT_COST_PER_1M", "0.25"))
    LLM_OUTPUT_COST_PER_1M = float(os.getenv("LLM_OUTPUT_COST_PER_1M", "1.50"))
    SCORING_VERSION = "cm-score-v2"
    ALERT_ON_TRACK = 0.90
    ALERT_NEEDS_ATTENTION = 0.70
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "25"))
    LLM_RETRY_ATTEMPTS = int(os.getenv("LLM_RETRY_ATTEMPTS", "2"))
