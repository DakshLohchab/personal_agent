from datetime import datetime, timedelta, timezone
from uuid import uuid4

from services.memory.service import MemoryService


class Repository:
    def __init__(self, records):
        self.records = records

    def list_valid(self, user_id, filters):
        return self.records


def test_retrieval_excludes_expired_and_inactive_memory() -> None:
    now = datetime.now(timezone.utc)
    records = [
        {
            "id": uuid4(),
            "status": "active",
            "memory_type": "preference",
            "content": "prefers train travel",
            "provenance_type": "user_input",
            "expires_at": None,
            "structured_data": {},
        },
        {
            "id": uuid4(),
            "status": "active",
            "memory_type": "preference",
            "content": "prefers train travel",
            "provenance_type": "user_input",
            "expires_at": now - timedelta(seconds=1),
            "structured_data": {},
        },
    ]
    result = MemoryService(Repository(records)).retrieve_relevant_memories(
        "user", "train travel"
    )
    assert len(result) == 1
    assert result[0].content == "prefers train travel"
