"""Flask dashboard for TelegramChannelAI pipeline."""

import os
import sys
import logging
import threading
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request, redirect, url_for

# add parent dir so we can import channel_ai if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from web.config import SECRET_KEY, PORT, DEBUG
from web.db import (
    init_db, get_stats, get_sources, add_source, remove_source,
    toggle_source, get_queue, update_queue_status, get_last_run,
    get_runs, start_run, finish_run, add_to_queue, get_published,
    get_analytics,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- logging setup ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=1_000_000, backupCount=3
)
log_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
log_handler.setLevel(logging.INFO)

logger = logging.getLogger("channelai")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
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
    items = get_queue(status)
    return render_template("queue.html", items=items, current_status=status)


@app.route("/published")
def published_page():
    posts = get_published()
    return render_template("published.html", posts=posts)


@app.route("/analytics")
def analytics_page():
    data = get_analytics()
    return render_template("analytics.html", analytics=data)


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
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "username required"}), 400

    result = add_source(username, data.get("title", ""), data.get("subscribers", 0))
    if result is None:
        return jsonify({"error": "already exists or invalid"}), 409
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
        return jsonify({"error": "pipeline already running"}), 409

    run_id = start_run()

    logger.info(f"Pipeline run #{run_id} started")

    # run in background thread so we don't block the request
    def _run():
        try:
            import asyncio
            from channel_ai import run_cycle
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(run_cycle())
            published = len(results) if results else 0
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
    username = request.form.get("username", "").strip()
    if username:
        add_source(username)
    return redirect(url_for("sources_page"))


@app.route("/sources/<int:source_id>/delete", methods=["POST"])
def form_delete_source(source_id):
    remove_source(source_id)
    return redirect(url_for("sources_page"))


# ---------- run ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
