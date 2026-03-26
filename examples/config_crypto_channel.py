"""
Example: Crypto/finance channel configuration.

Set CHANNEL_CONFIGS env var to this JSON (minified) to use multi-channel mode.
"""

CHANNEL_CONFIGS = {
    "crypto_signals": {
        "channel_id": 0,
        "system_prompt": "You are a crypto market analyst.\n"
                         "Data-driven, concise, actionable insights.\n"
                         "Include: asset context, key numbers, analysis, risk (1-5).\n"
                         "Format: HTML for Telegram. 150-250 words. English.\n"
                         "Do NOT give financial advice. Always add disclaimer.",
        "language": "en",
        "search_topics": ["Bitcoin", "Ethereum", "DeFi", "crypto regulation"],
        "sources": ["CoinDesk", "Cointelegraph", "WuBlockchain"],
    }
}

EXCLUSIONS = ["pump and dump", "guaranteed returns"]
