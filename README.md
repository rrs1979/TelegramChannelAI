# TelegramChannelAI

Automated Telegram channel management powered by [Pollinations.ai](https://pollinations.ai).

Scans news sources, rewrites content with AI, generates images, and publishes to Telegram channels — all automated.

## Features

- **Multi-source scanning** — monitors 40+ Telegram channels for trending news
- **AI rewriting** — rewrites news in your channel's unique voice/style via Claude
- **Fact-checking** — verifies claims via Perplexity search before publishing
- **Image generation** — creates relevant images via Flux model
- **Humanization** — second-pass GPT rewrite to remove "AI-speak"
- **Telegram publishing** — posts with images, polls, and reactions
- **Duplicate detection** — prevents republishing the same story
- **Exclusion filters** — skip sensitive topics (configurable)

## Architecture

```
News Sources (40+ channels)
        |
    [Scanner] ──── scans last 2h, finds trending (3+ channels = hot)
        |
    [Fact-checker] ── Perplexity search for confirmation + source URLs
        |
    [Rewriter] ──── Claude rewrites in channel style + adds analysis
        |
    [Humanizer] ──── GPT removes AI artifacts, adds natural language
        |
    [Image Gen] ──── Flux generates topic-relevant image (768x432)
        |
    [Publisher] ──── posts to Telegram with poll + reactions
```

## Quick Start

```bash
# Clone
git clone https://github.com/rrs1979/TelegramChannelAI.git
cd TelegramChannelAI

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your keys

# Run
python channel_ai.py
```

## Configuration

Create `.env` file:

```env
POLLINATIONS_API_KEY=your_pollinations_key
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_SESSION=your_session_string
CHANNEL_ID=your_channel_telegram_id
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
4. **Rewriter** uses Claude (via Pollinations) to rewrite in your channel's style
5. **Humanizer** passes through GPT to remove AI patterns and add natural language
6. **Image generator** creates a Flux image prompt and generates a 768x432 image
7. **Publisher** sends to Telegram channel with optional poll and reaction seeding

## Pollinations.ai Integration

This project uses Pollinations.ai as the unified AI backend:

- **Text generation**: Claude, GPT, Perplexity — all via single API
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

## License

MIT License

## Credits

Built with [Pollinations.ai](https://pollinations.ai) — the unified AI API platform.
