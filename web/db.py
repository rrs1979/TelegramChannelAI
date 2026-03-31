"""SQLite storage for the web dashboard."""

import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager

from web.config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db_conn():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist and apply schema migrations."""
    with db_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                title TEXT DEFAULT '',
                subscribers INTEGER DEFAULT 0,
                added_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT DEFAULT 'running',
                posts_scanned INTEGER DEFAULT 0,
                posts_published INTEGER DEFAULT 0,
                errors TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                original_text TEXT NOT NULL,
                rewritten_text TEXT,
                image_prompt TEXT,
                poll_data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS published (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_msg_id INTEGER,
                text TEXT NOT NULL,
                source TEXT,
                published_at TEXT DEFAULT (datetime('now'))
            );
        """)

        # add analytics columns to pipeline_runs if missing
        cols = [r[1] for r in conn.execute("PRAGMA table_info(pipeline_runs)").fetchall()]
        if "posts_generated" not in cols:
            conn.execute("ALTER TABLE pipeline_runs ADD COLUMN posts_generated INTEGER DEFAULT 0")
        if "cost_usd" not in cols:
            conn.execute("ALTER TABLE pipeline_runs ADD COLUMN cost_usd REAL DEFAULT 0.0")
        if "duration_ms" not in cols:
            conn.execute("ALTER TABLE pipeline_runs ADD COLUMN duration_ms INTEGER DEFAULT 0")

    seed_published()
    seed_pipeline_runs()


# --- sources ---

def get_sources():
    with db_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM sources ORDER BY added_at DESC"
        ).fetchall()]


def add_source(username, title="", subscribers=0):
    username = username.lstrip("@").strip()
    if not username:
        return None
    with db_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO sources (username, title, subscribers) VALUES (?, ?, ?)",
                (username, title, subscribers)
            )
            return username
        except sqlite3.IntegrityError:
            return None


def remove_source(source_id: int):
    with db_conn() as conn:
        conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))


def toggle_source(source_id):
    with db_conn() as conn:
        conn.execute(
            "UPDATE sources SET is_active = NOT is_active WHERE id = ?",
            (source_id,)
        )


# --- pipeline runs ---

def start_run():
    now = datetime.now(timezone.utc).isoformat()
    with db_conn() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_runs (started_at) VALUES (?)", (now,)
        )
        return cur.lastrowid


def finish_run(run_id, posts_scanned=0, posts_published=0, status="completed", errors=""):
    now = datetime.now(timezone.utc).isoformat()
    with db_conn() as conn:
        conn.execute(
            """UPDATE pipeline_runs
               SET finished_at=?, status=?, posts_scanned=?, posts_published=?, errors=?
               WHERE id=?""",
            (now, status, posts_scanned, posts_published, errors, run_id)
        )


def get_last_run():
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_runs(limit=20):
    with db_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]


# --- queue ---

def add_to_queue(source, original_text, rewritten_text=None, image_prompt=None, poll_data=None):
    with db_conn() as conn:
        conn.execute(
            """INSERT INTO queue (source, original_text, rewritten_text, image_prompt, poll_data)
               VALUES (?, ?, ?, ?, ?)""",
            (source, original_text, rewritten_text, image_prompt, poll_data)
        )


def get_queue(status="pending"):
    with db_conn() as conn:
        if status == "all":
            return [dict(r) for r in conn.execute(
                "SELECT * FROM queue ORDER BY created_at DESC"
            ).fetchall()]
        return [dict(r) for r in conn.execute(
            "SELECT * FROM queue WHERE status = ? ORDER BY created_at DESC",
            (status,)
        ).fetchall()]


def update_queue_status(queue_id, status):
    now = datetime.now(timezone.utc).isoformat()
    with db_conn() as conn:
        conn.execute(
            "UPDATE queue SET status = ?, reviewed_at = ? WHERE id = ?",
            (status, now, queue_id)
        )


# --- published ---

def get_published(limit=100):
    with db_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM published ORDER BY published_at DESC LIMIT ?", (limit,)
        ).fetchall()]


def seed_published():
    """Insert a few sample posts if table is empty (for dev/demo)."""
    with db_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM published").fetchone()[0]
        if count > 0:
            return

        samples = [
            (1001, "5 underrated Python libraries every backend dev should know about. "
             "Thread below with code examples and real benchmarks.",
             "python_weekly", "2026-03-20 14:30:00"),
            (1002, "The market is shifting. Here's what 3 months of tracking crypto "
             "sentiment on Telegram taught me about predicting price moves.",
             "crypto_signals", "2026-03-19 09:15:00"),
            (1003, "New AI image generators compared: Flux vs SDXL vs Midjourney v6. "
             "Quality, speed, and cost breakdown with sample outputs.",
             "tech_news_daily", "2026-03-18 18:45:00"),
        ]
        conn.executemany(
            "INSERT INTO published (telegram_msg_id, text, source, published_at) VALUES (?, ?, ?, ?)",
            samples,
        )


# --- stats ---

def get_stats():
    with db_conn() as conn:
        total_published = conn.execute("SELECT COUNT(*) FROM published").fetchone()[0]
        total_sources = conn.execute("SELECT COUNT(*) FROM sources WHERE is_active = 1").fetchone()[0]
        queue_size = conn.execute("SELECT COUNT(*) FROM queue WHERE status = 'pending'").fetchone()[0]
        total_runs = conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0]

        last_run = get_last_run()

        return {
            "total_published": total_published,
            "total_sources": total_sources,
            "queue_size": queue_size,
            "total_runs": total_runs,
            "last_run": last_run,
        }


# --- analytics ---

def get_analytics():
    """Return daily pipeline stats for charts."""
    with db_conn() as conn:
        rows = conn.execute("""
            SELECT
                date(started_at) as day,
                COUNT(*) as runs,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(COALESCE(posts_generated, posts_scanned)) as generated,
                SUM(posts_published) as published,
                ROUND(SUM(COALESCE(cost_usd, 0)), 2) as cost,
                AVG(COALESCE(duration_ms, 0)) as avg_duration
            FROM pipeline_runs
            WHERE started_at IS NOT NULL
            GROUP BY date(started_at)
            ORDER BY day DESC
            LIMIT 30
        """).fetchall()

        days = [dict(r) for r in rows]
        days.reverse()  # oldest first for charts

        # totals for the doughnut
        totals = conn.execute("""
            SELECT
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running
            FROM pipeline_runs
        """).fetchone()

        return {
            "daily": days,
            "totals": {
                "completed": totals[0] or 0,
                "failed": totals[1] or 0,
                "running": totals[2] or 0,
            },
        }


def seed_pipeline_runs():
    """Insert sample pipeline runs for the last 14 days if table is mostly empty."""
    with db_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0]
        if count > 5:
            return

        import random
        from datetime import timedelta

        base = datetime(2026, 3, 10, tzinfo=timezone.utc)
        samples = []
        for day_offset in range(14):
            day = base + timedelta(days=day_offset)
            # 1-3 runs per day
            for run_idx in range(random.randint(1, 3)):
                hour = 8 + run_idx * 4 + random.randint(0, 2)
                started = day.replace(hour=hour, minute=random.randint(0, 59))

                status = random.choices(["completed", "failed"], weights=[85, 15])[0]
                generated = random.randint(3, 12)
                published = random.randint(1, generated) if status == "completed" else 0
                cost = round(random.uniform(0.01, 0.04) * generated, 3)
                duration = random.randint(12000, 90000)

                finished = started + timedelta(milliseconds=duration)

                samples.append((
                    started.isoformat(),
                    finished.isoformat(),
                    status,
                    generated,  # posts_scanned
                    published,
                    "" if status == "completed" else "Timeout on source @tech_daily",
                    generated,
                    cost,
                    duration,
                ))

        conn.executemany(
            """INSERT INTO pipeline_runs
               (started_at, finished_at, status, posts_scanned, posts_published, errors,
                posts_generated, cost_usd, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            samples,
        )
