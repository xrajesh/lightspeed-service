"""Unit tests for RedisCache class."""

from unittest.mock import patch

import pytest

from ols.app.models.config import RedisConfig
from ols.src.cache.redis_cache import RedisCache
from ols.utils import suid
from ols.src.cache.conversation import Conversation
from tests.mock_classes.redis import MockRedis


conversation_id = suid.get_suid()


@pytest.fixture
def cache():
    """Fixture with constucted and initialized Redis cache object."""
    # we don't want to connect to real Redis from unit tests
    # with patch("ols.src.cache.redis_cache.RedisCache.initialize_redis"):
    with patch("redis.StrictRedis", new=MockRedis):
        return RedisCache(RedisConfig({}))


def test_insert_or_append(cache):
    """Test the behavior of insert_or_append method."""
    assert cache.get("user1", conversation_id) is None
    cache.insert_or_append("user1", conversation_id, Conversation("User Message1","Assistant Message1"))
    assert cache.get("user1", conversation_id) == [Conversation("User Message1","Assistant Message1")]


def test_insert_or_append_existing_key(cache):
    """Test the behavior of insert_or_append method for existing item."""
    # conversation IDs are separated by users
    assert cache.get("user2", conversation_id) is None

    cache.insert_or_append("user2", conversation_id, Conversation("User Message1","Assistant Message1"))
    cache.insert_or_append("user2", conversation_id, Conversation("User Message2","Assistant Message2"))
    expected_messages=[]
    expected_messages.append(Conversation("User Message1", "Assistant Message1"))
    expected_messages.append(Conversation("User Message2", "Assistant Message2"))
    assert cache.get("user2", conversation_id) == expected_messages


def test_get_nonexistent_key(cache):
    """Test how non-existent items are handled by the cache."""
    assert cache.get("nonexistent_key", conversation_id) is None


def test_get_improper_user_id(cache):
    """Test how improper user ID is handled."""
    with pytest.raises(ValueError):
        assert cache.get("foo/bar", conversation_id) is None


def test_get_improper_conversation_id(cache):
    """Test how improper conversation ID is handled."""
    with pytest.raises(ValueError):
        assert cache.get("user1", "this-is-not-valid-uuid") is None


def test_singleton_pattern():
    """Test if in memory cache exists as one instance in memory."""
    cache1 = RedisCache(RedisConfig({}))
    cache2 = RedisCache(RedisConfig({}))
    assert cache1 is cache2
