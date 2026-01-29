#!/usr/bin/env python3
"""Tests for PostgresAPI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock, mock_open
from services.supabase.postgres import PostgresAPI
from services.supabase.safety import SafetyError, SafetyTier


class TestPostgresAPIInit:
    """Test PostgresAPI initialization."""

    def test_init_with_project_name(self):
        """Test initialization with project name looks up env var."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            assert api.project == "smoothed"

    def test_init_with_direct_url(self):
        """Test initialization with direct URL bypasses env lookup."""
        api = PostgresAPI("smoothed", url="postgres://user:pass@localhost:5432/db")
        assert api.connection_url == "postgres://user:pass@localhost:5432/db"

    def test_init_raises_without_url(self):
        """Test initialization raises error when no URL available."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="No Postgres URL"):
                PostgresAPI("smoothed")

    def test_init_with_project_alias(self):
        """Test project aliases like project1, project2 map correctly."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL_2": "postgres://user:pass@localhost:5432/db2"},
        ):
            api = PostgresAPI("blingsting")
            assert api.project == "blingsting"
            assert "db2" in api.connection_url


class TestPostgresAPISafety:
    """Test safety classification integration."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API with mocked connection."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            # Mock the connection
            api._conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = None
            api._conn.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            return api

    def test_safe_sql_executes(self, mock_api):
        """Test that SAFE SQL executes without confirmation."""
        mock_api.execute("CREATE TABLE test (id int)")
        # Should not raise - verification is that we got here

    def test_cautious_sql_requires_confirm(self, mock_api):
        """Test that CAUTIOUS SQL requires confirm=True."""
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("TRUNCATE users")
        assert "confirm=True" in str(exc.value)

    def test_cautious_sql_with_confirm_executes(self, mock_api):
        """Test that CAUTIOUS SQL with confirm=True executes."""
        mock_api.execute("TRUNCATE users", confirm=True)
        # Should not raise

    def test_destructive_sql_blocked(self, mock_api):
        """Test that DESTRUCTIVE SQL is blocked without override."""
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("DROP TABLE users")
        assert "i_know_what_im_doing" in str(exc.value)

    def test_destructive_sql_with_override(self, mock_api):
        """Test that DESTRUCTIVE SQL with override executes."""
        mock_api.execute("DROP TABLE users", i_know_what_im_doing=True)
        # Should not raise

    def test_delete_without_where_is_destructive(self, mock_api):
        """Test that DELETE without WHERE is DESTRUCTIVE."""
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("DELETE FROM users")
        assert exc.value.tier == SafetyTier.DESTRUCTIVE

    def test_delete_with_where_is_cautious(self, mock_api):
        """Test that DELETE with WHERE is CAUTIOUS."""
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("DELETE FROM users WHERE id = 1")
        assert exc.value.tier == SafetyTier.CAUTIOUS


class TestPostgresAPIDryRun:
    """Test dry-run mode."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for dry run tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            return api

    def test_dry_run_does_not_execute(self, mock_api, capsys):
        """Test that dry_run=True does not execute SQL."""
        mock_api.execute("CREATE TABLE test (id int)", dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        mock_api._conn.cursor.assert_not_called()

    def test_dry_run_shows_tier(self, mock_api, capsys):
        """Test that dry run shows the safety tier."""
        mock_api.execute("DROP TABLE users", dry_run=True, i_know_what_im_doing=True)
        captured = capsys.readouterr()
        assert "DESTRUCTIVE" in captured.out

    def test_dry_run_still_requires_safety_override(self, mock_api):
        """Test that dry run still enforces safety checks."""
        with pytest.raises(SafetyError):
            mock_api.execute("DROP TABLE users", dry_run=True)


class TestPostgresAPIQuery:
    """Test query method."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for query tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
            mock_cursor.description = [("id",), ("name",)]
            api._conn.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            return api

    def test_query_returns_results(self, mock_api):
        """Test that query returns results from SELECT."""
        results = mock_api.query("SELECT * FROM users")
        assert len(results) == 1
        assert results[0]["id"] == 1

    def test_query_only_allows_select(self, mock_api):
        """Test that query method only allows SELECT statements."""
        with pytest.raises(ValueError, match="SELECT"):
            mock_api.query("DELETE FROM users")


class TestPostgresAPIHelpers:
    """Test helper methods."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for helper method tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            return api

    def test_table_exists_true(self, mock_api):
        """Test table_exists returns True when table exists."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"exists": True}
        mock_api._conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        assert mock_api.table_exists("users") is True

    def test_table_exists_false(self, mock_api):
        """Test table_exists returns False when table doesn't exist."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"exists": False}
        mock_api._conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        assert mock_api.table_exists("nonexistent") is False

    def test_get_schema_returns_columns(self, mock_api):
        """Test get_schema returns column information."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "text", "is_nullable": "YES"},
        ]
        mock_api._conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        schema = mock_api.get_schema("users")
        assert len(schema) == 2
        assert schema[0]["column_name"] == "id"


class TestPostgresAPITransaction:
    """Test transaction context manager."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for transaction tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = None
            api._conn.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            return api

    def test_transaction_commits_on_success(self, mock_api):
        """Test that transaction commits on successful completion."""
        with mock_api.transaction():
            mock_api.execute("CREATE TABLE test (id int)")
        mock_api._conn.commit.assert_called()

    def test_transaction_rollbacks_on_error(self, mock_api):
        """Test that transaction rollbacks on error."""
        mock_api._conn.cursor.return_value.__enter__.return_value.execute.side_effect = Exception(
            "DB error"
        )
        with pytest.raises(Exception):
            with mock_api.transaction():
                mock_api.execute("CREATE TABLE test (id int)")
        mock_api._conn.rollback.assert_called()


class TestPostgresAPIMigrations:
    """Test migration methods."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for migration tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = None
            api._conn.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            return api

    def test_run_migration_from_file(self, mock_api):
        """Test running a migration from a file."""
        sql_content = "CREATE TABLE test (id int);"
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=sql_content):
                mock_api.run_migration("/path/to/migration.sql")
        # Should have executed the SQL

    def test_run_migration_file_not_found(self, mock_api):
        """Test run_migration raises error for missing file."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                mock_api.run_migration("/path/to/nonexistent.sql")

    def test_run_migrations_from_dir_orders_files(self, mock_api):
        """Test that migrations are run in alphabetical order."""
        mock_files = [
            Path("/migrations/002_second.sql"),
            Path("/migrations/001_first.sql"),
            Path("/migrations/003_third.sql"),
        ]
        with patch("pathlib.Path.glob", return_value=mock_files):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="SELECT 1;")):
                    with patch.object(mock_api, "run_migration") as mock_run:
                        mock_api.run_migrations_from_dir("/migrations")

        # Verify files were called in sorted order
        calls = mock_run.call_args_list
        assert "001_first" in str(calls[0])
        assert "002_second" in str(calls[1])
        assert "003_third" in str(calls[2])


class TestPostgresAPIContextManager:
    """Test context manager support."""

    def test_context_manager_closes_connection(self):
        """Test that context manager closes connection on exit."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            with patch("psycopg2.connect") as mock_connect:
                mock_conn = MagicMock()
                mock_connect.return_value = mock_conn

                with PostgresAPI("smoothed") as api:
                    api._get_connection()  # Force connection creation

                mock_conn.close.assert_called_once()


class TestPostgresAPIAuditLog:
    """Test audit logging."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock API for audit log tests."""
        with patch.dict(
            "os.environ",
            {"SUPABASE_POSTGRES_URL": "postgres://user:pass@localhost:5432/db"},
        ):
            api = PostgresAPI("smoothed")
            api._conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = None
            api._conn.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            api._conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            return api

    def test_audit_log_written_for_ddl(self, mock_api, tmp_path):
        """Test that DDL operations are logged."""
        log_file = tmp_path / "ddl_audit.log"
        with patch.object(mock_api, "_audit_log_path", log_file):
            mock_api.execute("CREATE TABLE test (id int)")

        # Verify log was written
        assert log_file.exists()
        content = log_file.read_text()
        assert "CREATE TABLE" in content
        assert "SAFE" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
