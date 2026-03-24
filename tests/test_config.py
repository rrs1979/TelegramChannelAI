"""Tests for configuration and module structure."""
import os

os.environ.setdefault("TELEGRAM_API_ID", "0")
os.environ.setdefault("TELEGRAM_API_HASH", "test")
os.environ.setdefault("POLLINATIONS_API_KEY", "test")


def test_channel_ai_imports():
    import channel_ai
    assert hasattr(channel_ai, "run_cycle")
    assert hasattr(channel_ai, "ai_call")
    assert hasattr(channel_ai, "generate_image")


def test_web_app_imports():
    from web.app import app
    assert app is not None


def test_channel_prompts_structure():
    import channel_ai
    assert "default" in channel_ai.CHANNEL_PROMPTS
    prompt = channel_ai.CHANNEL_PROMPTS["default"]
    assert "system_prompt" in prompt
    assert "language" in prompt


def test_exclusions_list():
    import channel_ai
    assert isinstance(channel_ai.EXCLUSIONS, list)
    assert len(channel_ai.EXCLUSIONS) > 0


def test_image_dimensions():
    import channel_ai
    assert 0 < channel_ai.IMAGE_WIDTH <= 2048
    assert 0 < channel_ai.IMAGE_HEIGHT <= 2048
