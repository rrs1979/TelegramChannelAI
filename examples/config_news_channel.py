"""
Example: Ukrainian news channel configuration.
"""

CHANNEL_PROMPTS = {
    "ua_news_channel": {
        "system_prompt": """You are the editor of a Ukrainian news channel.
Your style: sharp, analytical, slightly ironic.
Always include:
- A catchy headline (bold)
- 2-3 paragraph analysis
- Original source link
- Your editorial take at the end

Format: HTML for Telegram. 200-300 words. Language: Ukrainian.""",
        "language": "uk",
        "search_topics": [
            "Ukraine news", "economy Ukraine", "energy prices Europe",
            "EU policy", "tech startups Ukraine",
        ],
    }
}

SOURCE_CHANNELS = [
    "truexanewsua", "u_now", "UaOnlii", "TCH_channel",
    "uniannet", "suspilnenews", "ukrpravda_news", "censor_net",
]

EXCLUSIONS = ["military positions", "coordinates", "casualties with details"]
