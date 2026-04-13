# TelegramChannelAI

[![Powered by Pollinations.ai](https://img.shields.io/badge/Powered%20by-Pollinations.ai-green?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDIgMC04LTMuNTgtOC04czMuNTgtOCA4LTggOCAzLjU4IDggOC0zLjU4IDgtOCA4eiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://pollinations.ai)
[![GitHub stars](https://img.shields.io/github/stars/rrs1979/TelegramChannelAI?style=flat)](https://github.com/rrs1979/TelegramChannelAI)

Automated Telegram channel management powered by [Pollinations.ai](https://pollinations.ai).

Scans news sources, rewrites content with AI, generates images, and publishes to Telegram channels — all automated.

## Features

- **Multi-source scanning** — monitors 40+ Telegram channels for trending news
- **Smart rewriting** — rewrites news in your channel's unique voice/style
- **Fact-checking** — verifies claims via Perplexity search before publishing
- **Image generation** — creates relevant images via Flux model
- **Humanization** — second-pass rewrite for natural, human-sounding language
- **Telegram publishing** — posts with images, polls, and reactions
- **Duplicate detection** — prevents republishing the same story
- **Exclusion filters** — skip sensitive topics (configurable)
- **Web dashboard** — manage sources, review queue, see published posts
- **Analytics** — pipeline performance charts (runs, costs, success rate)
- **Settings UI** — configure API keys and pipeline mode from the browser

## Screenshots

| Dashboard | Analytics |
|-----------|-----------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Analytics](docs/screenshots/analytics.png) |

| Queue | Settings |
|-------|----------|
| ![Queue](docs/screenshots/queue.png) | ![Settings](docs/screenshots/settings.png) |

## Architecture

```
News Sources (40+ channels)
        |
    [Scanner] ──── scans last 2h, finds trending (3+ channels = hot)
        |
    [Fact-checker] ── Perplexity search for confirmation + source URLs
        |
    [Rewriter] ──── rewrites in channel style + adds analysis
        |
    [Humanizer] ──── polishes text for natural, human-sounding language
        |
    [Image Gen] ──── Flux generates topic-relevant image (768x432)
        |
    [Publisher] ──── posts to Telegram with poll + reactions
```

## Quick Start

### Local development

```bash
git clone https://github.com/rrs1979/TelegramChannelAI.git
cd TelegramChannelAI

# create virtualenv (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# install deps
pip install -r requirements.txt

# configure
cp .env.example .env
# edit .env with your API keys (or configure later via Settings page)

# run the web dashboard
python -m web.app
# open http://localhost:5000

# run the pipeline directly (headless)
python channel_ai.py
```

### Docker

```bash
git clone https://github.com/rrs1979/TelegramChannelAI.git
cd TelegramChannelAI

cp .env.example .env
# edit .env

docker compose up --build
# dashboard at http://localhost:5000
```

The Docker setup runs the Flask dashboard on port 5000. SQLite data is persisted in a volume.

## Configuration

Create `.env` file (or use the Settings page in the dashboard):

```env
POLLINATIONS_API_KEY=your_pollinations_key
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION=your_session_string
CHANNEL_ID=your_channel_telegram_id
PIPELINE_INTERVAL=3600
PIPELINE_MODE=semi-auto
```

## Requirements

- Python 3.10+
- Pollinations.ai API key (free tier works)
- Telegram API credentials (from my.telegram.org)
- Active Telegram account with channel admin rights

## How It Works

1. **Scanner** connects to Telegram via Telethon and reads latest posts from configured source channels
2. **Deduplicator** checks if the story was already published (hash-based, 48h window)
3. **Fact-checker** sends the story to Perplexity for verification and source URLs
4. **Rewriter** rewrites in your channel's style via Pollinations
5. **Humanizer** polishes the text for natural, conversational language
6. **Image generator** creates a Flux image prompt and generates a 768x432 image
7. **Publisher** sends to Telegram channel with optional poll and reaction seeding

## Pollinations.ai Integration

This project uses Pollinations.ai as the unified AI backend:

- **Text generation**: multiple models via single API (rewriting, fact-checking, humanization)
- **Image generation**: Flux model for photorealistic images
- **Cost**: ~$0.01-0.02 per post (text + image + fact-check)

At ~10 posts/day, monthly cost is approximately $5-10.

## Customization

### Channel Style (System Prompt)

Edit `CHANNEL_PROMPTS` in `channel_ai.py` to define your channel's personality:

```python
CHANNEL_PROMPTS = {
    "my_channel": {
        "system_prompt": "You are the editor of a tech news channel...",
        "language": "en",
        "search_topics": ["AI news", "startup funding"],
    }
}
```

### Exclusion List

Configure topics to skip in `EXCLUSIONS`:

```python
EXCLUSIONS = [
    "military positions",
    "casualties",
    # Add your own...
]
```

## FAQ

**What's the difference between Auto and Semi-auto mode?**

- **Auto** — the pipeline scans, rewrites, and publishes directly to your channel. Fully hands-off.
- **Semi-auto** — posts go into a review queue first. You approve or reject each one from the dashboard before it gets published. Good for getting started or when you want editorial control.

Change the mode in Settings or set `PIPELINE_MODE=auto` / `PIPELINE_MODE=semi-auto` in `.env`.

**Can I use my own list of source channels?**

Yes. Set `DEFAULT_SOURCES` in `.env` with a comma-separated list of Telegram channel usernames (without the `@`):

```env
DEFAULT_SOURCES=truexanewsua,u_now,voynareal
```

This overrides the built-in default list. You can also manage sources from the dashboard UI.

**How often does the pipeline run, and can I change it?**

By default the pipeline runs every 60 minutes (`PIPELINE_INTERVAL=3600` in `.env`, value is in seconds). You can lower it for fast-moving topics or raise it for quieter channels:

```env
PIPELINE_INTERVAL=1800   # every 30 min
PIPELINE_INTERVAL=7200   # every 2 hours
```

You can also change this from the Settings page without restarting the app.

**How does duplicate detection work?**

The pipeline hashes each story's core text before publishing. If a hash already exists in the local store, the story is silently skipped. Hashes expire after 48 hours, so the same topic can be covered again if it stays relevant for several days. The hash file (`published_hashes.json`) is created automatically on first run — no setup needed.

## License

MIT License

## Credits

Built with [Pollinations.ai](https://pollinations.ai) — the unified AI API platform.
