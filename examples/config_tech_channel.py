"""
Example: Tech/AI news channel configuration.

Set CHANNEL_CONFIGS env var to this JSON (minified) to use multi-channel mode.
"""

CHANNEL_CONFIGS = {
    "tech_digest": {
        "channel_id": 0,
        "system_prompt": "You are a tech journalist covering AI and startups.\n"
                         "Enthusiastic but skeptical, always asking 'so what?'\n"
                         "Include: what happened, why it matters, who benefits, hot take.\n"
                         "Format: HTML for Telegram. 200-300 words. English.",
        "language": "en",
        "search_topics": ["AI models", "startup funding", "open source", "developer tools"],
        "sources": ["techcrunch", "the_information", "hackernews_feed"],
    }
}

EXCLUSIONS = ["sponsored content", "product placement"]
