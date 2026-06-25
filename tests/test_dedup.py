"""Tests for duplicate detection logic."""
import os

os.environ.setdefault("TELEGRAM_API_ID", "0")
os.environ.setdefault("TELEGRAM_API_HASH", "test")
os.environ.setdefault("POLLINATIONS_API_KEY", "test")

from channel_ai import is_duplicate


class TestDeduplication:
    def setup_method(self):
        import channel_ai
        channel_ai._published_hashes = set()
        channel_ai._hash_tokens = {}
        channel_ai.NEAR_DUP_THRESHOLD = 0.7  # deterministic for near-dup tests

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

    def test_reworded_same_story_is_near_duplicate(self):
        # Same story, different channel wording/order — exact md5 misses it,
        # fuzzy near-dup (Jaccard) should catch it.
        is_duplicate("Bitcoin price surges past one hundred thousand dollars")
        assert is_duplicate("Bitcoin surges past one hundred thousand dollars today") is True

    def test_different_topic_not_near_duplicate(self):
        is_duplicate("Bitcoin price surges past one hundred thousand dollars")
        assert is_duplicate("Local football team wins the championship final") is False

    def test_threshold_zero_disables_near_dup(self):
        import channel_ai
        channel_ai.NEAR_DUP_THRESHOLD = 0  # disable fuzzy → only exact md5
        is_duplicate("Bitcoin price surges past one hundred thousand dollars")
        # reworded headline is NOT an exact match → not flagged when fuzzy off
        assert is_duplicate("Bitcoin surges past one hundred thousand dollars today") is False
