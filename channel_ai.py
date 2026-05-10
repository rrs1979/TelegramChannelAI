"""
TelegramChannelAI — Automated Telegram channel management via Pollinations.ai

Scans news sources, rewrites content, generates images, publishes to Telegram.
Uses Pollinations.ai as unified backend for text generation, fact-checking, and images.

Author: Roman Rebrov (github.com/rrs1979)
License: MIT
"""

import asyncio
import hashlib
import json
import os
import re
import random
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════

POLLINATIONS_KEY = os.getenv("POLLINATIONS_API_KEY", "")
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION", "")

# Source channels to monitor (default set, overridable per channel config).
# Override with DEFAULT_SOURCES env var (comma-separated).
_sources_env = os.getenv("DEFAULT_SOURCES", "")
DEFAULT_SOURCES = (
    [s.strip() for s in _sources_env.split(",") if s.strip()]
    if _sources_env
    else [
        "truexanewsua", "u_now", "voynareal", "UaOnlii",
        "oko_ua", "novynu_ukraina", "DeepStateUA", "TCH_channel",
        "uniannet", "suspilnenews", "ukrpravda_news", "censor_net",
    ]
)

# Per-channel configs: each key maps to a target channel with its own personality.
# Override via CHANNEL_CONFIGS env var (JSON) or fall back to CHANNEL_ID env var.
_DEFAULT_PROMPT = {
    "channel_id": int(os.getenv("CHANNEL_ID", "0")),
    "system_prompt": "You are a news channel editor. Rewrite the news in an engaging style.\n"
                     "Format: HTML for Telegram. Include fact-check section. 200-300 words.",
    "language": "en",
    "search_topics": ["breaking news", "politics"],
    "sources": DEFAULT_SOURCES,
}


def _load_channel_configs():
    raw = os.getenv("CHANNEL_CONFIGS", "")
    if raw:
        try:
            configs = json.loads(raw)
            for cfg in configs.values():
                cfg.setdefault("sources", DEFAULT_SOURCES)
            return configs
        except (json.JSONDecodeError, AttributeError):
            pass
    return {"default": _DEFAULT_PROMPT}


CHANNEL_CONFIGS = _load_channel_configs()

# Topics to skip
EXCLUSIONS = [
    "military positions", "coordinates",
    "casualties with details", "prisoner lists",
]

SCAN_HOURS = int(os.getenv("SCAN_HOURS", 2))
DEDUP_HOURS = int(os.getenv("DEDUP_HOURS", 48))
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", 768))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", 432))

# ═══════════════════════════════════════════
# AI CALLS (via Pollinations.ai)
# ═══════════════════════════════════════════

HEADERS = {
    "Authorization": f"Bearer {POLLINATIONS_KEY}",
    "Content-Type": "application/json",
}


async def ai_call(session, model, system, user, max_tokens=1200):
    """Call any AI model via Pollinations OpenAI-compatible API."""
    try:
        async with session.post(
            "https://gen.pollinations.ai/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    return None
    except Exception as e:
        print(f"  AI error ({model}): {e}")
    return None


async def generate_image(prompt, vpn_proxy=None):
    """Generate image via Pollinations Flux model."""
    encoded = urllib.parse.quote(prompt[:500])
    seed = random.randint(1, 999999)
    url = (
        f"https://gen.pollinations.ai/image/{encoded}"
        f"?model=flux&width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        f"&seed={seed}&nologo=true"
    )
    path = Path(tempfile.gettempdir()) / f"channel_ai_{seed}.jpg"

    connector = None
    if vpn_proxy:
        try:
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(vpn_proxy)
        except ImportError:
            pass

    try:
        async with aiohttp.ClientSession(connector=connector) as s:
            async with s.get(
                url,
                headers={"Authorization": f"Bearer {POLLINATIONS_KEY}"},
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                if r.status == 200 and "image" in r.headers.get("content-type", ""):
                    data = await r.read()
                    # Pollinations sometimes returns a tiny placeholder on timeout;
                    # real generated images are always well above 3 KB.
                    if len(data) > 3000:
                        path.write_bytes(data)
                        return str(path)
    except Exception as e:
        print(f"  Image error: {e}")
    return None


# ═══════════════════════════════════════════
# TELEGRAM SCANNER
# ═══════════════════════════════════════════

async def scan_sources(client, channels, hours=SCAN_HOURS):
    """Scan source channels for recent posts."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    posts = []

    for username in channels:
        try:
            entity = await client.get_entity(f"@{username}")
            async for msg in client.iter_messages(entity, limit=5):
                if msg.text and len(msg.text) > 80 and msg.date and msg.date > since:
                    posts.append({
                        "text": msg.text[:500],
                        "source": f"@{username}",
                        "source_username": username,
                        "msg_id": msg.id,
                        "views": msg.views or 0,
                    })
        except Exception:
            pass
        await asyncio.sleep(0.5)

    posts.sort(key=lambda p: p["views"], reverse=True)
    return posts


# ═══════════════════════════════════════════
# DEDUPLICATION
# ═══════════════════════════════════════════

_published_hashes = set()
HASH_FILE = Path("published_hashes.json")


def load_hashes():
    global _published_hashes
    if HASH_FILE.exists():
        try:
            data = json.loads(HASH_FILE.read_text())
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=DEDUP_HOURS)).isoformat()
            _published_hashes = {h for h, ts in data.items() if ts > cutoff}
        except Exception:
            _published_hashes = set()


def save_hashes():
    now = datetime.now(timezone.utc).isoformat()
    data = {h: now for h in _published_hashes}
    HASH_FILE.write_text(json.dumps(data))


def is_duplicate(text):
    # Only hash first 100 chars — headlines are enough to catch reposts,
    # and body text often varies between sources covering the same story.
    h = hashlib.md5(text[:100].lower().encode()).hexdigest()
    if h in _published_hashes:
        return True
    _published_hashes.add(h)
    return False


# ═══════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════

async def process_post(session, post, prompt_config):
    """Full pipeline for a single post: factcheck → rewrite → humanize → image."""

    # 1. Fact-check via Perplexity
    factcheck = await ai_call(
        session, "perplexity-fast",
        "Fact-checker. Verify this news: find official sources, media confirmations, URLs. Brief.",
        f"Verify:\n{post['text'][:400]}",
        500,
    )

    # 2. Build source link
    source_link = post.get("source", "")
    msg_link = ""
    if post.get("msg_id") and post.get("source_username"):
        msg_link = f"https://t.me/{post['source_username']}/{post['msg_id']}"
        source_link = f"{post['source']} | {msg_link}"

    # 3. Rewrite in channel style
    rewritten = await ai_call(
        session, "claude",
        prompt_config["system_prompt"],
        f"Rewrite:\n{post['text']}\n\nSource: {source_link}\n\nFact-check:\n{factcheck or 'none'}",
        1500,
    )
    if not rewritten:
        return None

    # Check exclusions
    if rewritten.strip().upper().startswith("SKIP"):
        print(f"  Skipped (exclusion): {post['text'][:50]}...")
        return None

    # 4. Humanize — make it sound natural
    humanized = await ai_call(
        session, "openai",
        "Humanize this text. Keep HTML formatting. Replace formal language with conversational. "
        "Vary sentence length. Remove excess emoji (max 2). Don't add new facts. Output ONLY the text.",
        rewritten,
        1500,
    )
    if humanized and len(humanized) > 100:
        rewritten = humanized

    # 5. Extract URLs from factcheck
    if factcheck:
        urls = re.findall(r"https?://[^\s\)\"<>]+", factcheck)
        real_urls = [u for u in urls if len(u.split("/")) > 3]
        if real_urls and not any(u in rewritten for u in real_urls[:2]):
            rewritten += "\n\n" + "\n".join(f"🔗 {u}" for u in real_urls[:3])

    if msg_link and msg_link not in rewritten:
        rewritten += f"\n📢 {msg_link}"

    # 6. Generate image prompt
    img_prompt = await ai_call(
        session, "claude-fast",
        "Generate Flux AI image prompt. English, max 50 words. Cinematic, 4k. NO text. Output ONLY prompt.",
        rewritten[:300],
        80,
    )

    # 7. Generate poll question
    poll_data = await ai_call(
        session, "claude-fast",
        'Create a Telegram poll. JSON only, no markdown:\n'
        '{"question":"short question about the news","answers":["option 1","option 2","option 3"]}',
        rewritten[:300],
        200,
    )

    return {
        "text": rewritten,
        "image_prompt": img_prompt,
        "poll_data": poll_data,
        "source": post.get("source", ""),
    }


# ═══════════════════════════════════════════
# PUBLISHER
# ═══════════════════════════════════════════

async def publish_post(client, channel_entity, result):
    """Publish a processed post to Telegram channel."""
    from telethon.tl.types import (
        ReactionEmoji, InputMediaPoll, Poll, PollAnswer, TextWithEntities,
    )
    from telethon.tl.functions.messages import SendReactionRequest

    text = result["text"]

    # Generate image if prompt exists
    img_path = None
    if result.get("image_prompt"):
        img_path = await generate_image(result["image_prompt"])

    # Send post
    if img_path and os.path.exists(img_path):
        if len(text) <= 1024:
            msg = await client.send_file(channel_entity, img_path, caption=text, parse_mode="html")
        else:
            await client.send_file(channel_entity, img_path)
            msg = await client.send_message(channel_entity, text, parse_mode="html")
        os.unlink(img_path)
    else:
        msg = await client.send_message(channel_entity, text, parse_mode="html")

    # Add reaction
    try:
        await client(SendReactionRequest(
            peer=channel_entity, msg_id=msg.id,
            reaction=[ReactionEmoji(emoticon="\U0001f44d")],
        ))
    except Exception:
        pass

    # Send poll
    if result.get("poll_data"):
        try:
            raw = result["poll_data"].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            pd = json.loads(raw)
            poll_q = pd.get("question", "What do you think?")[:255]
            answers = pd.get("answers", ["Yes", "No", "Not sure"])[:3]

            await client.send_message(
                channel_entity,
                file=InputMediaPoll(poll=Poll(
                    id=0,
                    question=TextWithEntities(text=poll_q, entities=[]),
                    answers=[
                        PollAnswer(
                            text=TextWithEntities(text=a[:100], entities=[]),
                            option=str(i).encode(),
                        )
                        for i, a in enumerate(answers)
                    ],
                )),
            )
        except Exception:
            pass

    return msg.id


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

async def run_cycle(channel_key="default", max_posts=3):
    """Run one full pipeline cycle for a single channel config."""
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.types import PeerChannel

    if not POLLINATIONS_KEY:
        print("ERROR: POLLINATIONS_API_KEY not set")
        return

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH or not TELEGRAM_SESSION:
        print("ERROR: Telegram credentials not set")
        return

    channel_cfg = CHANNEL_CONFIGS.get(channel_key)
    if not channel_cfg:
        print(f"ERROR: unknown channel config '{channel_key}'")
        return

    channel_id = channel_cfg.get("channel_id", 0)
    sources = channel_cfg.get("sources", DEFAULT_SOURCES)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting pipeline for '{channel_key}'...")
    load_hashes()

    client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("ERROR: Telegram session expired")
        return

    print(f"  Scanning {len(sources)} channels...")
    t0 = time.time()
    posts = await scan_sources(client, sources)
    print(f"  Found {len(posts)} posts ({time.time()-t0:.1f}s)")

    if not posts:
        await client.disconnect()
        return

    unique = [p for p in posts if not is_duplicate(p["text"])]
    selected = unique[:max_posts]
    print(f"  Selected {len(selected)} (filtered {len(posts)-len(unique)} duplicates)")

    if not selected:
        save_hashes()
        await client.disconnect()
        return

    results = []
    async with aiohttp.ClientSession() as session:
        for i, post in enumerate(selected):
            print(f"  [{i+1}/{len(selected)}] Processing: {post['text'][:50]}...")
            t1 = time.time()
            result = await process_post(session, post, channel_cfg)
            if result:
                results.append(result)
                print(f"    Done ({time.time()-t1:.1f}s)")
            await asyncio.sleep(2)

    if results and channel_id:
        channel_entity = await client.get_entity(PeerChannel(channel_id))
        for result in results:
            msg_id = await publish_post(client, channel_entity, result)
            print(f"  Published to '{channel_key}': msg_id={msg_id}")
            await asyncio.sleep(5)

    await client.disconnect()
    save_hashes()

    print(f"  Pipeline complete for '{channel_key}': {len(results)} posts published")
    return results


async def run_all_channels(max_posts=3):
    """Run the pipeline for every configured channel sequentially."""
    all_results = {}
    for key in CHANNEL_CONFIGS:
        all_results[key] = await run_cycle(channel_key=key, max_posts=max_posts)
    return all_results


if __name__ == "__main__":
    asyncio.run(run_all_channels())
