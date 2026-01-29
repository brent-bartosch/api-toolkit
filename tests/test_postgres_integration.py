#!/usr/bin/env python3
"""
Integration tests for PostgresAPI.

These tests require a real Postgres connection.
Skip with: pytest tests/test_postgres_integration.py -v -k "not integration"
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from services.supabase.postgres import PostgresAPI
from services.supabase.safety import SafetyError


# Skip all tests if no Postgres URL configured
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_POSTGRES_URL"), reason="SUPABASE_POSTGRES_URL not set"
)


class TestPostgresIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def db(self):
        api = PostgresAPI("project1")
        yield api
        api.close()

    def test_connection(self, db):
        """Test that we can connect."""
        result = db.query("SELECT 1 as test")
        assert result[0]["test"] == 1

    def test_table_exists(self, db):
        """Test table_exists method."""
        exists = db.table_exists("_test_safe_ddl_nonexistent_xyz")
        assert exists is False

    def test_create_and_drop_table(self, db):
        """Test creating and dropping a table."""
        table_name = "_test_safe_ddl_temp"

        # Clean up if exists from previous failed test
        if db.table_exists(table_name):
            db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)

        # Create table (SAFE)
        db.execute(f"CREATE TABLE {table_name} (id serial PRIMARY KEY, name text)")
        assert db.table_exists(table_name)

        # Get schema
        schema = db.get_schema(table_name)
        assert len(schema) == 2
        assert schema[0]["name"] == "id"

        # Drop table (DESTRUCTIVE - requires override)
        db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)
        assert not db.table_exists(table_name)

    def test_transaction_rollback(self, db):
        """Test that failed transactions roll back."""
        table_name = "_test_safe_ddl_rollback"

        # Clean up
        if db.table_exists(table_name):
            db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)

        try:
            with db.transaction() as tx:
                tx.execute(f"CREATE TABLE {table_name} (id int)")
                # This should fail and rollback
                tx.execute("INVALID SQL SYNTAX HERE")
        except Exception:
            pass

        # Table should not exist due to rollback
        assert not db.table_exists(table_name)

    def test_dry_run_no_changes(self, db, capsys):
        """Test dry run doesn't make changes."""
        table_name = "_test_safe_ddl_dryrun"

        # Clean up
        if db.table_exists(table_name):
            db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)

        # Dry run
        db.execute(f"CREATE TABLE {table_name} (id int)", dry_run=True)

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert not db.table_exists(table_name)
