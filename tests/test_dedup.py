"""Tests for duplicate detection logic."""
import os
import tempfile

os.environ.setdefault("TELEGRAM_API_ID", "0")
os.environ.setdefault("TELEGRAM_API_HASH", "test")
os.environ.setdefault("POLLINATIONS_API_KEY", "test")

from channel_ai import is_duplicate


class TestDeduplication:
    def setup_method(self):
        import channel_ai
        channel_ai._seen_hashes = set()
        channel_ai._hash_file = tempfile.mktemp(suffix=".json")

    def test_first_message_not_duplicate(self):
        assert is_duplicate("Breaking: new policy announced") is False

    def test_same_message_is_duplicate(self):
        text = "Breaking: new policy announced today"
        is_duplicate(text)
        assert is_duplicate(text) is True

    def test_different_messages_not_duplicate(self):
        is_duplicate("First news story")
        assert is_duplicate("Completely different story") is False

    def test_empty_message(self):
        result = is_duplicate("")
        assert isinstance(result, bool)
