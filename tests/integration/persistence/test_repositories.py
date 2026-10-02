from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from packages.ports.auth import AuthPrincipal


def test_profile_goal_constraint_and_commitment_crud(user_context) -> None:
    principal = user_context.principal
    with user_context.unit_of_work() as unit_of_work:
        profile = unit_of_work.profiles.get(principal.user_id)
        goal = unit_of_work.goals.create(
            principal.user_id,
            {"name": "Emergency fund", "target_value": Decimal("10000.25"), "unit": "USD"},
        )
        constraint = unit_of_work.constraints.create(
            principal.user_id,
            {"name": "Cash floor", "metric": "minimum_cash", "limit_value": Decimal("500")},
        )
        commitment = unit_of_work.commitments.create(
            principal.user_id,
            {
                "name": "Rent",
                "monthly_cost": Decimal("1200.50"),
                "monthly_hours": Decimal("0"),
                "start_month": 1,
            },
        )
        assert profile["auth_subject"] == principal.auth_subject
        assert unit_of_work.goals.get(principal.user_id, goal["id"])["target_value"] == Decimal(
            "10000.25"
        )
        updated_goal = unit_of_work.goals.update(
            principal.user_id, goal["id"], {"name": "Emergency reserve"}
        )
        assert updated_goal["name"] == "Emergency reserve"
        assert unit_of_work.goals.list_for_user(principal.user_id)[0]["id"] == goal["id"]
        assert unit_of_work.constraints.get(principal.user_id, constraint["id"])
        assert unit_of_work.commitments.get(principal.user_id, commitment["id"])
        assert unit_of_work.goals.delete(principal.user_id, goal["id"])
        assert unit_of_work.constraints.delete(principal.user_id, constraint["id"])
        assert unit_of_work.commitments.delete(principal.user_id, commitment["id"])


def test_scenario_versions_and_parent_child_branches(user_context) -> None:
    user_id = user_context.principal.user_id
    with user_context.unit_of_work() as unit_of_work:
        scenario = unit_of_work.scenarios.create(user_id, {"name": "Move"})
        version = unit_of_work.scenarios.add_version(
            user_id,
            scenario["id"],
            {"cash": "1000.00"},
            {"id": "move", "deltas": {"cash": "-100"}},
        )
        parent = unit_of_work.scenarios.create_branch(
            user_id,
            scenario["id"],
            version["id"],
            "Move base",
            {"cash": "-100"},
        )
        child = unit_of_work.scenarios.create_branch(
            user_id,
            scenario["id"],
            version["id"],
            "Furnished move",
            {"cash": "-500"},
            parent_branch_id=parent["id"],
        )
        assert unit_of_work.scenarios.get_version(user_id, scenario["id"], version["id"])
        assert child["parent_branch_id"] == parent["id"]
        branch_ids = [
            branch["id"]
            for branch in unit_of_work.scenarios.list_branches(user_id, scenario["id"])
        ]
        assert branch_ids == [
            parent["id"],
            child["id"],
        ]


def test_duplicate_scenario_version_is_rejected(user_context) -> None:
    user_id = user_context.principal.user_id
    with user_context.unit_of_work() as unit_of_work:
        scenario = unit_of_work.scenarios.create(user_id, {"name": "Move"})
        unit_of_work.scenarios.add_version(user_id, scenario["id"], {}, {}, version_number=1)

    with pytest.raises(IntegrityError):
        with user_context.unit_of_work() as unit_of_work:
            unit_of_work.scenarios.add_version(
                user_id, scenario["id"], {}, {}, version_number=1
            )

    with user_context.unit_of_work() as unit_of_work:
        assert len(unit_of_work.scenarios.list_for_user(user_id)) == 1


def test_research_sources_evidence_and_assumption_provenance(user_context) -> None:
    user_id = user_context.principal.user_id
    with user_context.unit_of_work() as unit_of_work:
        query = unit_of_work.research.create_query(
            user_id, {"query": "average rent", "provider": "manual"}
        )
        source = unit_of_work.research.create_source(
            user_id,
            query["id"],
            {
                "url": "https://example.test/rent",
                "retrieved_at": datetime.now(UTC),
                "metadata_json": {"kind": "test"},
            },
        )
        evidence = unit_of_work.evidence.create(
            user_id,
            {
                "research_source_id": source["id"],
                "claim_text": "Rent median",
                "evidence_text": "Median rent is 1200",
            },
        )
        assumption = unit_of_work.assumptions.create(
            user_id,
            {
                "key": "monthly_rent",
                "value": "1200",
                "source_type": "research",
                "evidence_id": evidence["id"],
            },
        )
        assert unit_of_work.research.get_query(user_id, query["id"])
        assert len(unit_of_work.research.list_queries(user_id)) == 1
        assert unit_of_work.research.list_sources(user_id, query["id"])[0]["id"] == source["id"]
        assert unit_of_work.evidence.get(user_id, evidence["id"])
        assert assumption["evidence_id"] == evidence["id"]
        with pytest.raises(ValueError, match="require evidence_id"):
            unit_of_work.assumptions.create(
                user_id,
                {"key": "rent", "value": "1200", "source_type": "research"},
            )


def test_runs_memories_files_documents_and_embeddings(user_context) -> None:
    user_id = user_context.principal.user_id
    with user_context.unit_of_work() as unit_of_work:
        evidence = unit_of_work.evidence.create(
            user_id, {"claim_text": "Claim", "evidence_text": "Evidence"}
        )
        run = unit_of_work.runs.create(
            user_id,
            {
                "engine_version": "0.1.0",
                "schema_version": "0.1.0",
                "seed": 42,
                "input_snapshot": {"cash": "100"},
                "result_snapshot": {"ending_cash": "110"},
            },
        )
        memory = unit_of_work.memories.create(
            user_id, {"memory_type": "preference", "content": "Prefers quiet spaces"}
        )
        file = unit_of_work.files.create(
            user_id, {"original_name": "notes.txt", "media_type": "text/plain"}
        )
        document = unit_of_work.documents.create(
            user_id, {"file_id": file["id"], "title": "Notes", "content": "A note"}
        )
        chunk = unit_of_work.documents.create_chunk(
            user_id, document["id"], {"chunk_index": 0, "content": "A note"}
        )
        memory_embedding = unit_of_work.embeddings.create(
            user_id,
            {
                "memory_id": memory["id"],
                "model_name": "test-model",
                "dimensions": 2,
                "embedding": [1.0, 0.0],
            },
        )
        unit_of_work.embeddings.create(
            user_id,
            {
                "document_chunk_id": chunk["id"],
                "model_name": "test-model",
                "dimensions": 2,
                "embedding": [0.0, 1.0],
            },
        )
        unit_of_work.embeddings.create(
            user_id,
            {
                "evidence_id": evidence["id"],
                "model_name": "test-model",
                "dimensions": 2,
                "embedding": [-1.0, 0.0],
            },
        )
        results = unit_of_work.embeddings.exact_cosine_search(user_id, [1.0, 0.0])
        assert run["seed"] == 42
        assert unit_of_work.runs.get(user_id, run["id"])
        assert unit_of_work.memories.get(user_id, memory["id"])
        assert unit_of_work.files.get(user_id, file["id"])
        assert unit_of_work.documents.get(user_id, document["id"])
        assert unit_of_work.documents.list_chunks(user_id, document["id"])[0]["id"] == chunk[
            "id"
        ]
        assert results[0]["id"] == memory_embedding["id"]
        assert results[0]["cosine_distance"] == pytest.approx(0.0)


def test_user_ownership_isolation_and_transaction_rollback(user_context) -> None:
    owner_id = user_context.principal.user_id
    other_principal = AuthPrincipal(uuid4(), f"other-{uuid4()}", "fake")
    with user_context.unit_of_work(other_principal) as unit_of_work:
        unit_of_work.profiles.create(other_principal)
    with user_context.unit_of_work() as unit_of_work:
        goal = unit_of_work.goals.create(owner_id, {"name": "Private goal"})
        assert unit_of_work.goals.get(owner_id, goal["id"])

    with user_context.unit_of_work(other_principal) as unit_of_work:
        assert unit_of_work.goals.get(other_principal.user_id, goal["id"]) is None
        assert unit_of_work.goals.list_for_user(other_principal.user_id) == []
        assert not unit_of_work.goals.delete(other_principal.user_id, goal["id"])
    with user_context.unit_of_work() as unit_of_work:
        with pytest.raises(PermissionError, match="authenticated user"):
            unit_of_work.goals.get(other_principal.user_id, goal["id"])

    with pytest.raises(RuntimeError, match="rollback test"):
        with user_context.unit_of_work() as unit_of_work:
            rolled_back = unit_of_work.goals.create(owner_id, {"name": "Rolled back"})
            raise RuntimeError("rollback test")
    with user_context.unit_of_work() as unit_of_work:
        assert unit_of_work.goals.get(owner_id, rolled_back["id"]) is None


def test_related_rows_cannot_cross_user_ownership(user_context) -> None:
    owner_id = user_context.principal.user_id
    other_principal = AuthPrincipal(uuid4(), f"relations-{uuid4()}", "fake")
    with user_context.unit_of_work(other_principal) as unit_of_work:
        unit_of_work.profiles.create(other_principal)
    with user_context.unit_of_work() as unit_of_work:
        scenario = unit_of_work.scenarios.create(owner_id, {"name": "Private"})
        file_record = unit_of_work.files.create(owner_id, {"original_name": "private.txt"})
        query = unit_of_work.research.create_query(
            owner_id, {"query": "private", "provider": "manual"}
        )
        source = unit_of_work.research.create_source(
            owner_id,
            query["id"],
            {"url": "https://example.test/private", "retrieved_at": datetime.now(UTC)},
        )

    with user_context.unit_of_work(other_principal) as unit_of_work:
        with pytest.raises(ValueError, match="scenario does not belong"):
            unit_of_work.assumptions.create(
                other_principal.user_id,
                {"key": "x", "value": 1, "source_type": "manual", "scenario_id": scenario["id"]},
            )
        with pytest.raises(ValueError, match="scenario does not belong"):
            unit_of_work.runs.create(
                other_principal.user_id,
                {
                    "scenario_id": scenario["id"],
                    "engine_version": "0.1.0",
                    "schema_version": "0.1.0",
                    "input_snapshot": {},
                    "result_snapshot": {},
                },
            )
        with pytest.raises(ValueError, match="research source does not belong"):
            unit_of_work.evidence.create(
                other_principal.user_id,
                {
                    "research_source_id": source["id"],
                    "claim_text": "claim",
                    "evidence_text": "text",
                },
            )
        with pytest.raises(ValueError, match="file does not belong"):
            unit_of_work.documents.create(
                other_principal.user_id,
                {"file_id": file_record["id"], "title": "private", "content": "text"},
            )


def test_database_rejects_research_assumption_without_evidence(user_context) -> None:
    user_id = user_context.principal.user_id
    with pytest.raises(IntegrityError):
        with user_context.engine.begin() as connection:
            connection.execute(
                text(
                    """INSERT INTO assumptions (id, user_id, key, value, source_type)
                    VALUES (gen_random_uuid(), :user_id, 'rent', '1200'::jsonb, 'research')"""
                ),
                {"user_id": str(user_id)},
            )


def test_database_rejects_embedding_without_exactly_one_owner(user_context) -> None:
    with pytest.raises(IntegrityError):
        with user_context.engine.begin() as connection:
            connection.execute(
                text(
                    """INSERT INTO embeddings (id, user_id, model_name, dimensions)
                    VALUES (:id, :user_id, 'test-model', 2)"""
                ),
                {"id": str(uuid4()), "user_id": str(user_context.principal.user_id)},
            )