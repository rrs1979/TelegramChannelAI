"""
Example: Crypto/finance channel configuration.
"""

CHANNEL_PROMPTS = {
    "crypto_signals": {
        "system_prompt": """You are a crypto market analyst.
Data-driven, concise, actionable insights.
Include: asset context, key numbers, analysis, risk (1-5).
Format: HTML for Telegram. 150-250 words. English.
Do NOT give financial advice. Always add disclaimer.""",
        "language": "en",
        "search_topics": ["Bitcoin", "Ethereum", "DeFi", "crypto regulation"],
    }
}

SOURCE_CHANNELS = ["CoinDesk", "Cointelegraph", "WuBlockchain"]
EXCLUSIONS = ["pump and dump", "guaranteed returns"]
