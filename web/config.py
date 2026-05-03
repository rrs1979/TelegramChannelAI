"""App configuration — reads from .env or falls back to defaults."""

import os
import secrets
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(ENV_PATH)

# server
PORT = int(os.getenv("PORT", 5000))
# default to off — we don't want the Werkzeug debugger exposed if FLASK_ENV is missing
DEBUG = os.getenv("FLASK_ENV", "production") == "development"
SECRET_KEY = os.getenv("FLASK_SECRET") or secrets.token_hex(32)

# database
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))

# pipeline
PIPELINE_INTERVAL = int(os.getenv("PIPELINE_INTERVAL", 3600))  # seconds between auto-runs


# --- settings helpers (read/write .env) ---

# keys we manage through the settings page
SETTINGS_KEYS = [
    "POLLINATIONS_API_KEY",
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "CHANNEL_ID",
    "CHANNEL_CONFIGS",
    "PIPELINE_INTERVAL",
    "PIPELINE_MODE",
]


def load_settings():
    """Read current settings from env (already loaded) with safe defaults."""
    return {
        "POLLINATIONS_API_KEY": os.getenv("POLLINATIONS_API_KEY", ""),
        "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID", ""),
        "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH", ""),
        "CHANNEL_ID": os.getenv("CHANNEL_ID", ""),
        "CHANNEL_CONFIGS": os.getenv("CHANNEL_CONFIGS", ""),
        "PIPELINE_INTERVAL": os.getenv("PIPELINE_INTERVAL", "3600"),
        "PIPELINE_MODE": os.getenv("PIPELINE_MODE", "semi-auto"),
    }


def save_settings(fields):
    """Merge fields into .env file, preserving unknown keys."""
    existing = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    existing[key.strip()] = val.strip()

    # update with new values (strip newlines to prevent .env injection)
    for key in SETTINGS_KEYS:
        if key in fields:
            clean = fields[key].replace("\n", "").replace("\r", "")
            existing[key] = clean
            os.environ[key] = clean  # update runtime too

    # create with 0600 from the start — plain open() respects umask, so on a default-umask server
    # the .env briefly sits world-readable between open() and the chmod() below
    fd = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        for key, val in existing.items():
            f.write(f"{key}={val}\n")

    # the mode arg above is ignored when the file already exists, so tighten any pre-existing
    # loose perms left over from before this fix landed
    try:
        os.chmod(ENV_PATH, 0o600)
    except OSError:
        pass
