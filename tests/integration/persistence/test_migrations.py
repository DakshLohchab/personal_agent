from alembic import command
from sqlalchemy import inspect, text

from tests.integration.persistence.conftest import _migration_config


def test_migration_upgrade_extension_tables_downgrade_and_reupgrade(postgres_engine) -> None:
    config = _migration_config(postgres_engine.url.render_as_string(hide_password=False))
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")

        expected = {
            "profiles",
            "goals",
            "constraints",
            "commitments",
            "scenarios",
            "scenario_versions",
            "scenario_branches",
            "assumptions",
            "research_queries",
            "research_sources",
            "evidence",
            "runs",
            "memories",
            "embeddings",
            "files",
            "documents",
            "document_chunks",
        }
        assert expected.issubset(set(inspect(postgres_engine).get_table_names()))
        with postgres_engine.connect() as connection:
            assert connection.scalar(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            ) == 1
            rls_tables = connection.execute(
                text(
                    """SELECT relname FROM pg_class
                    WHERE relrowsecurity AND relforcerowsecurity
                    AND relname IN ('profiles', 'goals', 'scenario_versions', 'research_sources')"""
                )
            ).scalars().all()
            assert set(rls_tables) == {
                "profiles",
                "goals",
                "scenario_versions",
                "research_sources",
            }
            policy_count = connection.scalar(
                text("SELECT count(*) FROM pg_policies WHERE schemaname = current_schema()")
            )
            assert policy_count >= 17

        command.downgrade(config, "base")
        assert not expected.intersection(set(inspect(postgres_engine).get_table_names()))
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        assert expected.issubset(set(inspect(postgres_engine).get_table_names()))
    finally:
        command.upgrade(config, "head")
