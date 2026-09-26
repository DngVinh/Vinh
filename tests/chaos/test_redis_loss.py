import pytest
from unittest.mock import MagicMock


class MockTruthStore:
    def __init__(self):
        self.records = {"ticket_001": {"status": "SUBMITTED", "truth_verified": True}}

    def get(self, key: str):
        return self.records.get(key)


class CacheAsideManager:
    def __init__(self, truth_store: MockTruthStore, redis_client):
        self.truth_store = truth_store
        self.redis_client = redis_client

    def get_ticket(self, ticket_id: str):
        # Try cache first
        try:
            val = self.redis_client.get(f"ticket:{ticket_id}")
            if val is not None:
                return val
        except Exception:
            # Graceful degradation on redis loss: fallback to database truth
            pass

        # Fetch from PostgreSQL truth
        return self.truth_store.get(ticket_id)


def test_redis_loss_graceful_degradation_to_truth():
    # AC-01: When Redis is lost/offline, read falls back to database truth without error
    truth = MockTruthStore()
    mock_redis = MagicMock()
    mock_redis.get.side_effect = ConnectionError("Redis server connection dropped (Chaos simulated)")

    cache_manager = CacheAsideManager(truth_store=truth, redis_client=mock_redis)

    # Must return truth despite Redis failure
    ticket = cache_manager.get_ticket("ticket_001")
    assert ticket is not None
    assert ticket["status"] == "SUBMITTED"
    assert ticket["truth_verified"] is True


def test_redis_available_reads_from_cache():
    # AC-02: When Redis is healthy, reads return cached copy
    truth = MockTruthStore()
    mock_redis = MagicMock()
    mock_redis.get.return_value = {"status": "SUBMITTED", "from_cache": True}

    cache_manager = CacheAsideManager(truth_store=truth, redis_client=mock_redis)
    ticket = cache_manager.get_ticket("ticket_001")
    assert ticket["from_cache"] is True
