"""Flask dashboard for TelegramChannelAI pipeline."""

import os
import re
import sys
import hmac
import time
import logging
import threading
from urllib.parse import urlsplit
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


# --- optional HTTP Basic Auth ---
# Set DASHBOARD_PASSWORD to lock the dashboard down. Left unset it stays open like
# before so existing localhost deploys don't suddenly break, but anything bound to
# 0.0.0.0 or exposed past nginx really wants this on — the settings page and the
# pipeline trigger are otherwise wide open to whoever can reach the port.
_AUTH_USER = os.getenv("DASHBOARD_USER", "admin")
_AUTH_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

# guessing the password was free: nothing throttled it and nothing logged it, so a
# script could hammer the login with a wordlist all night and the log would stay clean.
# five misses from one address now buy a 30s timeout, and each miss leaves a
# warning in the log so a brute-force run is at least visible after the fact.
_FAILED_LOGINS = {}  # ip -> (miss count, monotonic time of the last miss)
_LOCKOUT_MISSES = 5
_LOCKOUT_SECONDS = 30


@app.before_request
def require_auth():
    if not _AUTH_PASSWORD:
        return  # auth disabled
    if request.path == "/health":
        return  # keep uptime/load-balancer probes unauthenticated
    ip = request.remote_addr or "unknown"
    now = time.monotonic()
    misses, last_miss = _FAILED_LOGINS.get(ip, (0, 0.0))
    if now - last_miss > _LOCKOUT_SECONDS:
        misses = 0  # old misses age out, no need to serve a stale lockout
    if misses >= _LOCKOUT_MISSES:
        # locked out — don't even check the password, so a correct guess made
        # during the cooldown can't be told apart from another wrong one
        retry = max(1, int(_LOCKOUT_SECONDS - (now - last_miss)) + 1)
        return Response(
            "Too many failed logins, try again shortly", 429,
            {"Retry-After": str(retry)},
        )
    auth = request.authorization
    # compare_digest on both fields so a wrong username can't be timed apart from a wrong password
    if (auth and auth.type == "basic"
            and hmac.compare_digest(auth.username or "", _AUTH_USER)
            and hmac.compare_digest(auth.password or "", _AUTH_PASSWORD)):
        _FAILED_LOGINS.pop(ip, None)
        return
    if auth:
        # only count requests that actually carried credentials — the browser's
        # first bare request just hasn't seen the 401 challenge yet. and log the
        # ip but never the username: people paste passwords into that field.
        _FAILED_LOGINS[ip] = (misses + 1, now)
        logger.warning(f"Failed dashboard login from {ip} ({misses + 1} recent)")
        # sweep aged entries while we're here so an address-hopping scan
        # can't grow the table forever
        for stale in [k for k, (_, t) in _FAILED_LOGINS.items() if now - t > _LOCKOUT_SECONDS]:
            del _FAILED_LOGINS[stale]
    return Response(
        "Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="TelegramChannelAI dashboard"'},
    )


@app.before_request
def block_cross_site_writes():
    # basic auth rides along on every request the browser makes, including ones a
    # hostile page kicks off — a hidden <form> on some other site could rewrite the
    # settings, delete sources, or fire a pipeline run without ever seeing the
    # password. so anything state-changing has to look same-origin: browsers stamp
    # requests with Sec-Fetch-Site and Origin, and we bounce the ones marked
    # cross-site. curl and scripts send neither header, but they also carry no
    # ambient credentials, so they pass through untouched.
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    fetch_site = request.headers.get("Sec-Fetch-Site", "")
    if fetch_site and fetch_site not in ("same-origin", "none"):
        return jsonify({"error": "Cross-site requests are not allowed"}), 403
    origin = request.headers.get("Origin", "")
    if origin and urlsplit(origin).netloc != request.host:
        return jsonify({"error": "Cross-site requests are not allowed"}), 403


@app.after_request
def set_security_headers(resp):
    # the dashboard has no reason to ever be framed — DENY shuts the door on
    # clickjacking the settings form or the run-pipeline button. nosniff stops
    # the browser second-guessing our content types, and we don't want the
    # dashboard URL leaking to the tailwind CDN (or anywhere) in the Referer.
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    return resp


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
def not_found(_):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {e}")
    return jsonify({"error": "Something went wrong on our side. Try again in a moment, and if it keeps happening check the server logs."}), 500


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
    try:
        sources = get_sources()
    except Exception as e:
        logger.error(f"Sources load failed: {e}")
        sources = []
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
    try:
        posts = get_published()
    except Exception as e:
        logger.error(f"Published load failed: {e}")
        posts = []
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
        # api_id pattern is enforced on the form but a curl/devtools POST can still write
        # a non-numeric value to .env that Telethon then chokes on at the next login
        if fields["TELEGRAM_API_ID"] and not fields["TELEGRAM_API_ID"].isdigit():
            fields["TELEGRAM_API_ID"] = current.get("TELEGRAM_API_ID", "")
        # same story for channel_id — must be -100 followed by digits, or publishing breaks
        if fields["CHANNEL_ID"] and not re.fullmatch(r"-100[0-9]+", fields["CHANNEL_ID"]):
            fields["CHANNEL_ID"] = current.get("CHANNEL_ID", "")
        # and the hash — 32 hex chars; the form pattern catches it but a raw POST doesn't,
        # and a junk hash just makes Telethon fail to log in
        if fields["TELEGRAM_API_HASH"] and not re.fullmatch(r"[a-f0-9]{32}", fields["TELEGRAM_API_HASH"]):
            fields["TELEGRAM_API_HASH"] = current.get("TELEGRAM_API_HASH", "")

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
    # get_json() returns whatever the body parses to (list/str/number/null), not always an object,
    # so `or {}` only catches the falsy cases — a non-empty list/string body slips past and the
    # data.get() call below would raise AttributeError, swallowed into a misleading 500
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    username = data.get("username", "").strip().lstrip("@")
    if not username or not re.match(r'^[A-Za-z][A-Za-z0-9_]{3,30}$', username):
        return jsonify({"error": "That's not a valid Telegram handle. Use 4-31 letters, digits, or underscores, starting with a letter."}), 400

    subscribers = data.get("subscribers", 0)
    if not isinstance(subscribers, int) or subscribers < 0:
        subscribers = 0

    title = (data.get("title") or "").strip()[:128]
    result = add_source(username, title, subscribers)
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
    try:
        update_queue_status(item_id, "approved")
    except Exception as e:
        logger.error(f"Approve failed for queue item {item_id}: {e}")
        return jsonify({"error": "Couldn't update the item, try again in a moment"}), 500
    return jsonify({"ok": True})


@app.route("/api/queue/<int:item_id>/reject", methods=["POST"])
def api_reject(item_id):
    try:
        update_queue_status(item_id, "rejected")
    except Exception as e:
        logger.error(f"Reject failed for queue item {item_id}: {e}")
        return jsonify({"error": "Couldn't update the item, try again in a moment"}), 500
    return jsonify({"ok": True})


@app.route("/api/pipeline/run", methods=["POST"])
def api_run_pipeline():
    """Trigger pipeline run (async, returns immediately)."""
    last = get_last_run()
    if last and last.get("status") == "running":
        return jsonify({"error": "A pipeline run is already in progress. Refresh the page to see its status."}), 409

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
