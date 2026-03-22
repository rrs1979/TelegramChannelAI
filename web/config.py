"""App configuration — reads from .env or falls back to defaults."""

import os
from dotenv import load_dotenv

load_dotenv()

# server
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("FLASK_ENV", "development") == "development"
SECRET_KEY = os.getenv("FLASK_SECRET", "dev-key-change-me")

# database
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))

# pipeline
PIPELINE_INTERVAL = int(os.getenv("PIPELINE_INTERVAL", 3600))  # seconds between auto-runs
