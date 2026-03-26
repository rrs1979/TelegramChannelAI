"""
Example: Ukrainian news channel configuration.

Set CHANNEL_CONFIGS env var to this JSON (minified) to use multi-channel mode.
"""

CHANNEL_CONFIGS = {
    "ua_news_channel": {
        "channel_id": 0,
        "system_prompt": "You are the editor of a Ukrainian news channel.\n"
                         "Your style: sharp, analytical, slightly ironic.\n"
                         "Always include:\n"
                         "- A catchy headline (bold)\n"
                         "- 2-3 paragraph analysis\n"
                         "- Original source link\n"
                         "- Your editorial take at the end\n\n"
                         "Format: HTML for Telegram. 200-300 words. Language: Ukrainian.",
        "language": "uk",
        "search_topics": [
            "Ukraine news", "economy Ukraine", "energy prices Europe",
            "EU policy", "tech startups Ukraine",
        ],
        "sources": [
            "truexanewsua", "u_now", "UaOnlii", "TCH_channel",
            "uniannet", "suspilnenews", "ukrpravda_news", "censor_net",
        ],
    }
}

EXCLUSIONS = ["military positions", "coordinates", "casualties with details"]
