from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from services.memory.service import MemoryPolicyError, MemoryService


class FakeMemoryRepository:
    def __init__(self, records):
        self.records = records

    def create(self, user_id, values):
        return {**values, "id": uuid4(), "user_id": user_id}

    def list_valid(self, user_id, memory_types=None):
        return [
            record
            for record in self.records
            if record["user_id"] == user_id
            and (memory_types is None or record["memory_type"] in memory_types)
            and record["status"] == "active"
        ]


def record(user_id, content, **overrides):
    return {
        "id": uuid4(),
        "user_id": user_id,
        "memory_type": "preference",
        "content": content,
        "structured_data": {},
        "provenance_type": "user_confirmed",
        "provenance_ref": None,
        "confidence": 1,
        "status": "active",
        "expires_at": None,
        "last_confirmed_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        **overrides,
    }


def test_new_memories_are_candidates_and_secrets_are_rejected():
    user_id = uuid4()
    service = MemoryService(FakeMemoryRepository([]))

    proposed = service.create_memory(
        user_id,
        {"memory_type": "preference", "content": "I prefer quiet hotels"},
    )

    assert proposed["status"] == "candidate"
    with pytest.raises(MemoryPolicyError):
        service.create_memory(
            user_id,
            {"memory_type": "preference", "content": "my password is secret"},
        )


def test_retrieval_excludes_expired_and_current_structured_values_win():
    user_id = uuid4()
    current = record(user_id, "temporary reserve", structured_data={"minimum_cash_reserve": 5000})
    expired = record(
        user_id,
        "old reserve",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    repository = FakeMemoryRepository([current, expired])
    service = MemoryService(repository)

    result = service.retrieve_relevant_memories(
        user_id,
        {"minimum_cash_reserve": 1000},
    )

    assert result == []
