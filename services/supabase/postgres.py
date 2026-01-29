#!/usr/bin/env python3
"""
PostgresAPI - Direct PostgreSQL connection for DDL operations.

Provides safe DDL execution with:
- Safety classification (SAFE, CAUTIOUS, DESTRUCTIVE)
- Dry-run mode for previewing operations
- Audit logging for all DDL operations
- Transaction support
- Migration file execution

Usage:
    from services.supabase.postgres import PostgresAPI

    # Connect to a project
    api = PostgresAPI('smoothed')

    # Execute safe DDL
    api.execute("CREATE TABLE users (id serial PRIMARY KEY)")

    # Execute cautious DDL (requires confirmation)
    api.execute("TRUNCATE users", confirm=True)

    # Execute destructive DDL (requires explicit override)
    api.execute("DROP TABLE users", i_know_what_im_doing=True)

    # Dry-run mode (shows what would happen)
    api.execute("DROP TABLE users", dry_run=True, i_know_what_im_doing=True)

    # Run migrations
    api.run_migrations_from_dir("./migrations")

    # Use as context manager
    with PostgresAPI('smoothed') as api:
        api.execute("CREATE TABLE test (id int)")
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Re-export safety classes for convenience
from services.supabase.safety import SafetyError, SafetyTier, check_safety, classify_sql

# Lazy import psycopg2 to avoid import errors when not installed
psycopg2 = None


def _get_psycopg2():
    """Lazy import psycopg2."""
    global psycopg2
    if psycopg2 is None:
        import psycopg2 as pg
        from psycopg2 import extras

        psycopg2 = pg
        psycopg2.extras = extras
    return psycopg2


# =============================================================================
# Configuration
# =============================================================================

# Project name to environment variable mapping
# Format: PROJECTNAME_SUPABASE_POSTGRES_URL
POSTGRES_PROJECTS = {
    # Project 1: Smoothed Lead Gen
    "smoothed": "SMOOTHED_SUPABASE_POSTGRES_URL",
    "project1": "SMOOTHED_SUPABASE_POSTGRES_URL",
    # Project 2: Blingsting CRM
    "blingsting": "BLINGSTING_SUPABASE_POSTGRES_URL",
    "project2": "BLINGSTING_SUPABASE_POSTGRES_URL",
    # Project 3: Web Scraping
    "scraping": "SCRAPING_SUPABASE_POSTGRES_URL",
    "project3": "SCRAPING_SUPABASE_POSTGRES_URL",
    # Project 4: Thordata
    "thordata": "THORDATA_SUPABASE_POSTGRES_URL",
    "project4": "THORDATA_SUPABASE_POSTGRES_URL",
}

# Audit log location
AUDIT_LOG_DIR = Path.home() / ".api-toolkit"
AUDIT_LOG_PATH = AUDIT_LOG_DIR / "ddl_audit.log"


# =============================================================================
# Transaction Context Manager
# =============================================================================


class _TransactionContext:
    """Context manager for explicit transactions."""

    def __init__(self, api: "PostgresAPI"):
        self.api = api
        self._original_autocommit = None

    def __enter__(self):
        """Begin transaction."""
        conn = self.api._get_connection()
        self._original_autocommit = conn.autocommit
        conn.autocommit = False
        self.api._in_transaction = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        conn = self.api._conn
        self.api._in_transaction = False
        if exc_type is not None:
            conn.rollback()
        else:
            conn.commit()
        conn.autocommit = self._original_autocommit
        return False  # Don't suppress exceptions


# =============================================================================
# PostgresAPI Class
# =============================================================================


class PostgresAPI:
    """
    PostgreSQL API for safe DDL execution.

    Provides direct PostgreSQL access with safety classification,
    dry-run mode, audit logging, and transaction support.

    Attributes:
        project: The project name (smoothed, blingsting, scraping)
        connection_url: The PostgreSQL connection URL
    """

    def __init__(self, project: str, url: Optional[str] = None):
        """
        Initialize PostgresAPI.

        Args:
            project: Project name (smoothed, blingsting, scraping) or alias (project1, project2, project3)
            url: Optional direct connection URL. If not provided, looks up from environment.

        Raises:
            ValueError: If no Postgres URL is available for the project
        """
        self.project = project
        self._conn = None
        self._in_transaction = False
        self._audit_log_path = AUDIT_LOG_PATH

        if url:
            self.connection_url = url
        else:
            self.connection_url = self._resolve_connection_url(project)

    def _resolve_connection_url(self, project: str) -> str:
        """
        Resolve connection URL from environment variables.

        Args:
            project: Project name or alias

        Returns:
            PostgreSQL connection URL

        Raises:
            ValueError: If no URL found for project
        """
        # Get the env var name for this project
        env_var = POSTGRES_PROJECTS.get(project)

        if env_var:
            # Known project - use its specific env var
            url = os.environ.get(env_var)
            if url:
                return url
            raise ValueError(
                f"No Postgres URL found for project '{project}'. "
                f"Set {env_var} in your .env file."
            )
        else:
            # Unknown project - try generic patterns
            generic_patterns = [
                f"{project.upper()}_SUPABASE_POSTGRES_URL",
                f"{project.upper()}_POSTGRES_URL",
                "DATABASE_URL",
            ]
            for pattern in generic_patterns:
                url = os.environ.get(pattern)
                if url:
                    return url
            raise ValueError(
                f"Unknown project '{project}'. "
                f"Known projects: {', '.join(POSTGRES_PROJECTS.keys())}. "
                f"Or set {project.upper()}_SUPABASE_POSTGRES_URL in .env."
            )

    def _ensure_audit_dir(self) -> None:
        """Ensure the audit log directory exists."""
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self):
        """
        Get or create a database connection.

        Returns:
            psycopg2 connection object
        """
        if self._conn is None:
            pg = _get_psycopg2()
            self._conn = pg.connect(
                self.connection_url,
                cursor_factory=pg.extras.RealDictCursor,
            )
            self._conn.autocommit = False
        return self._conn

    def _audit_log(
        self,
        sql: str,
        tier: SafetyTier,
        override_used: bool = False,
        dry_run: bool = False,
    ) -> None:
        """
        Log DDL operation to audit file.

        Args:
            sql: The SQL statement executed
            tier: The safety tier classification
            override_used: Whether safety override was used
            dry_run: Whether this was a dry run
        """
        self._ensure_audit_dir()

        timestamp = datetime.now().isoformat()
        mode = "[DRY RUN]" if dry_run else "[EXECUTED]"
        override_note = " (override used)" if override_used else ""

        log_entry = (
            f"{timestamp} | {self.project} | {tier.value}{override_note} | {mode}\n"
            f"  SQL: {sql[:500]}{'...' if len(sql) > 500 else ''}\n"
            f"\n"
        )

        with open(self._audit_log_path, "a") as f:
            f.write(log_entry)

    def execute(
        self,
        sql: str,
        confirm: bool = False,
        i_know_what_im_doing: bool = False,
        dry_run: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL statement with safety checks.

        Args:
            sql: The SQL statement to execute
            confirm: If True, allows CAUTIOUS operations
            i_know_what_im_doing: If True, allows DESTRUCTIVE operations
            dry_run: If True, shows what would happen without executing

        Returns:
            List of result rows (empty for DDL statements)

        Raises:
            SafetyError: If safety checks fail
        """
        # Check safety (raises SafetyError if blocked)
        tier = check_safety(
            sql, confirm=confirm, i_know_what_im_doing=i_know_what_im_doing
        )

        # Determine if override was used
        override_used = (tier == SafetyTier.CAUTIOUS and confirm) or (
            tier == SafetyTier.DESTRUCTIVE and i_know_what_im_doing
        )

        # Handle dry run
        if dry_run:
            print(f"[DRY RUN] [{tier.value}] Would execute:")
            print(f"  {sql}")
            self._audit_log(sql, tier, override_used, dry_run=True)
            return []

        # Execute the SQL
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                # Try to fetch results (will fail for DDL, which is fine)
                if cursor.description:
                    results = cursor.fetchall()
                else:
                    results = []
            # Only commit if not inside a transaction context
            if not self._in_transaction:
                conn.commit()
        except Exception:
            conn.rollback()
            raise

        # Log the operation
        self._audit_log(sql, tier, override_used)

        return list(results)

    def query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute a SELECT query.

        This is a convenience method for read-only queries.
        It enforces that only SELECT statements are allowed.

        Args:
            sql: A SELECT statement

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If sql is not a SELECT statement
        """
        normalized = sql.strip().upper()
        if not normalized.startswith("SELECT"):
            raise ValueError(
                "query() only accepts SELECT statements. Use execute() for other operations."
            )

        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql)
            results = cursor.fetchall()
        return list(results)

    def table_exists(self, table_name: str, schema: str = "public") -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            True if table exists, False otherwise
        """
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            )
        """
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
            result = cursor.fetchone()
        return result["exists"] if result else False

    def get_schema(
        self, table_name: str, schema: str = "public"
    ) -> list[dict[str, Any]]:
        """
        Get column information for a table.

        Args:
            table_name: Name of the table
            schema: Schema name (default: public)

        Returns:
            List of column info dictionaries with keys:
            - column_name
            - data_type
            - is_nullable
            - column_default
        """
        sql = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position
        """
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
            results = cursor.fetchall()
        return list(results)

    def run_migration(self, file_path: str) -> None:
        """
        Run a migration from a SQL file.

        Args:
            file_path: Path to the .sql file

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Migration file not found: {file_path}")

        sql = path.read_text()
        self.execute(sql, confirm=True)

    def run_migrations_from_dir(self, dir_path: str) -> list[str]:
        """
        Run all .sql migrations in a directory in alphabetical order.

        Args:
            dir_path: Path to the migrations directory

        Returns:
            List of migration files that were executed
        """
        path = Path(dir_path)
        sql_files = sorted(path.glob("*.sql"))

        executed = []
        for sql_file in sql_files:
            self.run_migration(str(sql_file))
            executed.append(str(sql_file))

        return executed

    def transaction(self) -> _TransactionContext:
        """
        Create a transaction context manager.

        Usage:
            with api.transaction():
                api.execute("CREATE TABLE a ...")
                api.execute("CREATE TABLE b ...")
            # Both tables created, or neither if error

        Returns:
            Transaction context manager
        """
        return _TransactionContext(self)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "PostgresAPI":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - close connection."""
        self.close()
        return False  # Don't suppress exceptions


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    def print_usage():
        print("Usage: python postgres.py <project> <command> [args]")
        print()
        print("Projects: smoothed, blingsting, scraping")
        print()
        print("Commands:")
        print("  test                    Test connection")
        print("  tables                  List all tables")
        print("  schema <table>          Show table schema")
        print("  execute '<sql>'         Execute SQL (with safety checks)")
        print("  dry-run '<sql>'         Show what would happen")
        print()
        print("Examples:")
        print("  python postgres.py smoothed test")
        print("  python postgres.py smoothed tables")
        print("  python postgres.py smoothed schema users")
        print("  python postgres.py smoothed dry-run 'CREATE TABLE test (id int)'")

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(0)

    project = sys.argv[1]
    command = sys.argv[2]

    try:
        api = PostgresAPI(project)

        if command == "test":
            # Test connection
            conn = api._get_connection()
            print(f"Connected to {project}")
            api.close()

        elif command == "tables":
            # List tables
            results = api.query(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
            )
            print(f"Tables in {project}:")
            for row in results:
                print(f"  - {row['table_name']}")

        elif command == "schema":
            if len(sys.argv) < 4:
                print("Usage: python postgres.py <project> schema <table>")
                sys.exit(1)
            table = sys.argv[3]
            schema = api.get_schema(table)
            print(f"Schema for {table}:")
            for col in schema:
                nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                default = (
                    f" DEFAULT {col['column_default']}" if col["column_default"] else ""
                )
                print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")

        elif command == "execute":
            if len(sys.argv) < 4:
                print("Usage: python postgres.py <project> execute '<sql>'")
                sys.exit(1)
            sql = sys.argv[3]
            tier = classify_sql(sql)
            print(f"Safety tier: {tier.value}")
            if tier == SafetyTier.CAUTIOUS:
                confirm = input("This requires confirmation. Proceed? (y/N): ")
                if confirm.lower() != "y":
                    print("Aborted.")
                    sys.exit(0)
                api.execute(sql, confirm=True)
            elif tier == SafetyTier.DESTRUCTIVE:
                confirm = input("This is DESTRUCTIVE. Are you sure? (type 'yes'): ")
                if confirm != "yes":
                    print("Aborted.")
                    sys.exit(0)
                api.execute(sql, i_know_what_im_doing=True)
            else:
                api.execute(sql)
            print("Executed successfully.")

        elif command == "dry-run":
            if len(sys.argv) < 4:
                print("Usage: python postgres.py <project> dry-run '<sql>'")
                sys.exit(1)
            sql = sys.argv[3]
            tier = classify_sql(sql)
            # For dry-run, we still need the override flags to pass safety check
            if tier == SafetyTier.DESTRUCTIVE:
                api.execute(sql, dry_run=True, i_know_what_im_doing=True)
            elif tier == SafetyTier.CAUTIOUS:
                api.execute(sql, dry_run=True, confirm=True)
            else:
                api.execute(sql, dry_run=True)

        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except SafetyError as e:
        print(f"Safety Error: {e}")
        sys.exit(1)
