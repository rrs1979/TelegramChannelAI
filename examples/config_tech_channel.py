"""
Example: Tech/AI news channel configuration.
"""

CHANNEL_PROMPTS = {
    "tech_digest": {
        "system_prompt": """You are a tech journalist covering AI and startups.
Enthusiastic but skeptical, always asking 'so what?'
Include: what happened, why it matters, who benefits, hot take.
Format: HTML for Telegram. 200-300 words. English.""",
        "language": "en",
        "search_topics": ["AI models", "startup funding", "open source", "developer tools"],
    }
}

SOURCE_CHANNELS = ["techcrunch", "the_information", "hackernews_feed"]
EXCLUSIONS = ["sponsored content", "product placement"]
