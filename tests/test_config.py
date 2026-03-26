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


def test_channel_configs_structure():
    import channel_ai
    assert "default" in channel_ai.CHANNEL_CONFIGS
    cfg = channel_ai.CHANNEL_CONFIGS["default"]
    assert "system_prompt" in cfg
    assert "language" in cfg
    assert "channel_id" in cfg
    assert "sources" in cfg


def test_channel_configs_from_env():
    import json
    os.environ["CHANNEL_CONFIGS"] = json.dumps({
        "test_ch": {
            "channel_id": 123,
            "system_prompt": "test",
            "language": "en",
            "search_topics": [],
        }
    })
    import importlib
    import channel_ai
    importlib.reload(channel_ai)
    assert "test_ch" in channel_ai.CHANNEL_CONFIGS
    assert channel_ai.CHANNEL_CONFIGS["test_ch"]["channel_id"] == 123
    assert "sources" in channel_ai.CHANNEL_CONFIGS["test_ch"]
    del os.environ["CHANNEL_CONFIGS"]
    importlib.reload(channel_ai)


def test_run_all_channels_exists():
    import channel_ai
    assert hasattr(channel_ai, "run_all_channels")


def test_exclusions_list():
    import channel_ai
    assert isinstance(channel_ai.EXCLUSIONS, list)
    assert len(channel_ai.EXCLUSIONS) > 0


def test_image_dimensions():
    import channel_ai
    assert 0 < channel_ai.IMAGE_WIDTH <= 2048
    assert 0 < channel_ai.IMAGE_HEIGHT <= 2048
