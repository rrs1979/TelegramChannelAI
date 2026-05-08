"""Flask dashboard for TelegramChannelAI pipeline."""

import os
import re
import sys
import logging
import threading
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request, redirect, url_for, Response

# add parent dir so we can import channel_ai if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from web.config import SECRET_KEY, PORT, DEBUG, load_settings, save_settings
from web.db import (
    init_db, get_stats, get_sources, add_source, remove_source,
    toggle_source, get_queue, update_queue_status, get_last_run,
    get_runs, start_run, finish_run, get_published,
    get_analytics,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.context_processor
def inject_last_run():
    try:
        lr = get_last_run()
    except Exception:
        lr = None
    return {"global_last_run": lr}

# --- logging setup ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_log_max_bytes = int(os.getenv("LOG_MAX_BYTES", 1_000_000))
_log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", 3))
log_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=_log_max_bytes, backupCount=_log_backup_count
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
log_handler.setLevel(logging.INFO)

logger = logging.getLogger("channelai")
_log_level = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO").upper()
logger.setLevel(getattr(logging, _log_level, logging.INFO))
logger.addHandler(log_handler)

# also log to console in dev mode
if DEBUG:
    logger.addHandler(logging.StreamHandler())

# init db on startup
init_db()
logger.info("App started, db initialized")


# ---------- error handlers ----------

@app.errorhandler(404)
def not_found(e):
    return render_template("base.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {e}")
    return jsonify({"error": "internal server error"}), 500


# ---------- health check ----------

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /\n", mimetype="text/plain")


# ---------- pages ----------

@app.route("/")
def dashboard():
    try:
        stats = get_stats()
        runs = get_runs(10)
    except Exception as e:
        logger.error(f"Dashboard load failed: {e}")
        stats = {"total_published": 0, "total_sources": 0, "queue_size": 0, "total_runs": 0, "last_run": None}
        runs = []
    return render_template("dashboard.html", stats=stats, runs=runs)


@app.route("/sources")
def sources_page():
    sources = get_sources()
    return render_template("sources.html", sources=sources)


@app.route("/queue")
def queue_page():
    status = request.args.get("status", "pending")
    if status not in ("pending", "approved", "rejected", "published"):
        status = "pending"
    try:
        items = get_queue(status)
    except Exception as e:
        logger.error(f"Queue load failed: {e}")
        items = []
    return render_template("queue.html", items=items, current_status=status)


@app.route("/published")
def published_page():
    posts = get_published()
    return render_template("published.html", posts=posts)


@app.route("/analytics")
def analytics_page():
    try:
        data = get_analytics()
    except Exception as e:
        logger.error(f"Analytics load failed: {e}")
        data = {"daily": [], "totals": {"completed": 0, "failed": 0, "running": 0}}
    return render_template("analytics.html", analytics=data)


def _mask(value):
    """Mask a secret so the raw value never reaches the browser."""
    if not value or len(value) < 6:
        return ""
    # cap the bullets at 12 so the mask doesn't leak the secret's actual length
    return value[:3] + "\u2022" * min(len(value) - 6, 12) + value[-3:]


# keys whose values should be masked in the settings form
_SECRET_FIELDS = ("POLLINATIONS_API_KEY", "TELEGRAM_API_HASH")


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        # validate pipeline interval is a positive integer
        raw_interval = request.form.get("pipeline_interval", "3600").strip()
        try:
            interval = int(raw_interval)
            if interval < 60 or interval > 86400:
                raise ValueError
        except (ValueError, TypeError):
            interval = 3600

        # validate pipeline mode against allowed values
        mode = request.form.get("pipeline_mode", "semi-auto").strip()
        if mode not in ("manual", "semi-auto", "auto"):
            mode = "semi-auto"

        current = load_settings()
        fields = {
            "POLLINATIONS_API_KEY": request.form.get("pollinations_key", "").strip(),
            "TELEGRAM_API_ID": request.form.get("telegram_api_id", "").strip(),
            "TELEGRAM_API_HASH": request.form.get("telegram_api_hash", "").strip(),
            "CHANNEL_ID": request.form.get("channel_id", "").strip(),
            "PIPELINE_INTERVAL": str(interval),
            "PIPELINE_MODE": mode,
        }
        # if a masked value was submitted unchanged, keep the original
        for key in _SECRET_FIELDS:
            if "\u2022" in fields.get(key, ""):
                fields[key] = current.get(key, "")

        save_settings(fields)
        logger.info("Settings updated")
        return redirect(url_for("settings_page"))

    settings = load_settings()
    for key in _SECRET_FIELDS:
        settings[key] = _mask(settings[key])
    return render_template("settings.html", settings=settings)


# ---------- API ----------

@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.route("/api/sources")
def api_sources():
    return jsonify(get_sources())


@app.route("/api/sources", methods=["POST"])
def api_add_source():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lstrip("@")
    if not username or not re.match(r'^[A-Za-z][A-Za-z0-9_]{3,30}$', username):
        return jsonify({"error": "Username must start with a letter and be 4-31 characters (letters, digits, underscores)"}), 400

    subscribers = data.get("subscribers", 0)
    if not isinstance(subscribers, int) or subscribers < 0:
        subscribers = 0

    result = add_source(username, data.get("title", ""), subscribers)
    if result is None:
        return jsonify({"error": "This channel is already in your sources list"}), 409
    logger.info(f"Source added: @{result}")
    return jsonify({"ok": True, "username": result}), 201


@app.route("/api/sources/<int:source_id>", methods=["DELETE"])
def api_remove_source(source_id):
    remove_source(source_id)
    return jsonify({"ok": True})


@app.route("/api/sources/<int:source_id>/toggle", methods=["POST"])
def api_toggle_source(source_id):
    toggle_source(source_id)
    return jsonify({"ok": True})


@app.route("/api/queue/<int:item_id>/approve", methods=["POST"])
def api_approve(item_id):
    update_queue_status(item_id, "approved")
    return jsonify({"ok": True})


@app.route("/api/queue/<int:item_id>/reject", methods=["POST"])
def api_reject(item_id):
    update_queue_status(item_id, "rejected")
    return jsonify({"ok": True})


@app.route("/api/pipeline/run", methods=["POST"])
def api_run_pipeline():
    """Trigger pipeline run (async, returns immediately)."""
    last = get_last_run()
    if last and last.get("status") == "running":
        return jsonify({"error": "Pipeline is already running, please wait for it to finish"}), 409

    run_id = start_run()

    logger.info(f"Pipeline run #{run_id} started")

    # run in background thread so we don't block the request
    def _run():
        try:
            import asyncio
            from channel_ai import run_all_channels
            loop = asyncio.new_event_loop()
            all_results = loop.run_until_complete(run_all_channels())
            published = sum(len(r) for r in (all_results or {}).values() if r)
            finish_run(run_id, posts_published=published, status="completed")
            logger.info(f"Pipeline run #{run_id} done, {published} posts published")
        except Exception as e:
            logger.error(f"Pipeline run #{run_id} failed: {e}")
            finish_run(run_id, status="failed", errors=str(e))

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return jsonify({"ok": True, "run_id": run_id})


# ---------- form actions (non-JS fallback) ----------

@app.route("/sources/add", methods=["POST"])
def form_add_source():
    username = request.form.get("username", "").strip().lstrip("@")
    if not username or not re.match(r'^[A-Za-z][A-Za-z0-9_]{3,30}$', username):
        return redirect(url_for("sources_page"))
    add_source(username)
    return redirect(url_for("sources_page"))


@app.route("/sources/<int:source_id>/delete", methods=["POST"])
def form_delete_source(source_id):
    remove_source(source_id)
    return redirect(url_for("sources_page"))


# ---------- run ----------

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=PORT, debug=DEBUG)
