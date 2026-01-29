# Safe DDL Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add direct Postgres connection support with safety classification for DDL operations.

**Architecture:** Create `PostgresAPI` class alongside existing `SupabaseAPI`. PostgresAPI connects directly to Postgres for DDL/schema operations while SupabaseAPI continues handling REST-based queries. Safety classification in separate module prevents destructive operations without explicit confirmation.

**Tech Stack:** Python, psycopg2-binary, existing BaseAPI patterns

---

## Task 1: Add psycopg2-binary Dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add the dependency**

Add to `requirements.txt`:
```
psycopg2-binary>=2.9.9
```

**Step 2: Install and verify**

Run: `pip install psycopg2-binary`
Expected: Successfully installed psycopg2-binary

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add psycopg2-binary for direct Postgres access"
```

---

## Task 2: Create Safety Classification Module

**Files:**
- Create: `services/supabase/safety.py`
- Test: `tests/test_safety.py`

**Step 1: Write the failing tests**

Create `tests/test_safety.py`:
```python
#!/usr/bin/env python3
"""Tests for SQL safety classification."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from services.supabase.safety import classify_sql, SafetyTier, SafetyError


class TestSafetyClassification:
    """Test SQL classification into safety tiers."""

    def test_create_table_is_safe(self):
        tier = classify_sql("CREATE TABLE users (id uuid PRIMARY KEY)")
        assert tier == SafetyTier.SAFE

    def test_create_index_is_safe(self):
        tier = classify_sql("CREATE INDEX idx_users_email ON users(email)")
        assert tier == SafetyTier.SAFE

    def test_alter_add_column_is_safe(self):
        tier = classify_sql("ALTER TABLE users ADD COLUMN phone text")
        assert tier == SafetyTier.SAFE

    def test_alter_rename_is_safe(self):
        tier = classify_sql("ALTER TABLE users RENAME COLUMN name TO full_name")
        assert tier == SafetyTier.SAFE

    def test_truncate_is_cautious(self):
        tier = classify_sql("TRUNCATE users")
        assert tier == SafetyTier.CAUTIOUS

    def test_alter_drop_column_is_cautious(self):
        tier = classify_sql("ALTER TABLE users DROP COLUMN phone")
        assert tier == SafetyTier.CAUTIOUS

    def test_delete_with_where_is_cautious(self):
        tier = classify_sql("DELETE FROM users WHERE id = 123")
        assert tier == SafetyTier.CAUTIOUS

    def test_drop_table_is_destructive(self):
        tier = classify_sql("DROP TABLE users")
        assert tier == SafetyTier.DESTRUCTIVE

    def test_drop_table_if_exists_is_destructive(self):
        tier = classify_sql("DROP TABLE IF EXISTS users")
        assert tier == SafetyTier.DESTRUCTIVE

    def test_delete_without_where_is_destructive(self):
        tier = classify_sql("DELETE FROM users")
        assert tier == SafetyTier.DESTRUCTIVE

    def test_select_is_safe(self):
        tier = classify_sql("SELECT * FROM users")
        assert tier == SafetyTier.SAFE

    def test_case_insensitive(self):
        tier = classify_sql("drop table USERS")
        assert tier == SafetyTier.DESTRUCTIVE

    def test_multiline_sql(self):
        sql = """
        CREATE TABLE campaigns (
            id uuid PRIMARY KEY,
            name text NOT NULL
        )
        """
        tier = classify_sql(sql)
        assert tier == SafetyTier.SAFE


class TestSafetyError:
    """Test SafetyError exception."""

    def test_safety_error_has_tier(self):
        err = SafetyError("Blocked", SafetyTier.DESTRUCTIVE, "DROP TABLE x")
        assert err.tier == SafetyTier.DESTRUCTIVE
        assert err.sql == "DROP TABLE x"
        assert "Blocked" in str(err)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_safety.py -v`
Expected: FAIL with "No module named 'services.supabase.safety'"

**Step 3: Write minimal implementation**

Create `services/supabase/safety.py`:
```python
#!/usr/bin/env python3
"""
SQL Safety Classification

Classifies SQL statements into safety tiers:
- SAFE: CREATE, ALTER ADD, SELECT - execute immediately
- CAUTIOUS: TRUNCATE, ALTER DROP COLUMN, DELETE with WHERE - require confirm=True
- DESTRUCTIVE: DROP TABLE, DELETE without WHERE - require i_know_what_im_doing=True
"""

import re
from enum import Enum
from typing import Optional


class SafetyTier(Enum):
    """Classification tiers for SQL statements."""
    SAFE = "safe"
    CAUTIOUS = "cautious"
    DESTRUCTIVE = "destructive"


class SafetyError(Exception):
    """Raised when SQL is blocked by safety classification."""

    def __init__(self, message: str, tier: SafetyTier, sql: str):
        self.tier = tier
        self.sql = sql
        self.message = message
        super().__init__(f"{message} [Tier: {tier.value}] SQL: {sql[:100]}...")


# Pattern definitions
SAFE_PATTERNS = [
    r'^\s*CREATE\s+TABLE',
    r'^\s*CREATE\s+INDEX',
    r'^\s*CREATE\s+UNIQUE\s+INDEX',
    r'^\s*CREATE\s+TYPE',
    r'^\s*CREATE\s+EXTENSION',
    r'^\s*CREATE\s+FUNCTION',
    r'^\s*CREATE\s+OR\s+REPLACE\s+FUNCTION',
    r'^\s*ALTER\s+TABLE\s+\w+\s+ADD',
    r'^\s*ALTER\s+TABLE\s+\w+\s+RENAME',
    r'^\s*COMMENT\s+ON',
    r'^\s*SELECT\b',
    r'^\s*INSERT\s+INTO',
    r'^\s*UPDATE\s+\w+\s+SET',
]

CAUTIOUS_PATTERNS = [
    r'^\s*ALTER\s+TABLE\s+\w+\s+DROP\s+COLUMN',
    r'^\s*TRUNCATE',
    r'^\s*DELETE\s+FROM\s+\w+\s+WHERE',
]

DESTRUCTIVE_PATTERNS = [
    r'^\s*DROP\s+TABLE',
    r'^\s*DROP\s+DATABASE',
    r'^\s*DROP\s+SCHEMA',
    r'^\s*DROP\s+FUNCTION',
    r'^\s*DROP\s+TYPE',
    r'^\s*DROP\s+INDEX',
    r'^\s*DELETE\s+FROM\s+\w+\s*$',  # DELETE without WHERE
    r'^\s*DELETE\s+FROM\s+\w+\s*;?\s*$',  # DELETE without WHERE (with optional semicolon)
    r'^\s*ALTER\s+TABLE\s+\w+\s+DROP\s+CONSTRAINT',
]


def classify_sql(sql: str) -> SafetyTier:
    """
    Classify SQL statement into a safety tier.

    Args:
        sql: SQL statement to classify

    Returns:
        SafetyTier indicating the classification
    """
    # Normalize: strip whitespace and handle multiline
    sql_normalized = ' '.join(sql.split())

    # Check destructive first (most restrictive)
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.match(pattern, sql_normalized, re.IGNORECASE):
            return SafetyTier.DESTRUCTIVE

    # Check cautious
    for pattern in CAUTIOUS_PATTERNS:
        if re.match(pattern, sql_normalized, re.IGNORECASE):
            return SafetyTier.CAUTIOUS

    # Check safe patterns
    for pattern in SAFE_PATTERNS:
        if re.match(pattern, sql_normalized, re.IGNORECASE):
            return SafetyTier.SAFE

    # Default: treat unknown SQL as cautious (conservative approach)
    return SafetyTier.CAUTIOUS


def check_safety(sql: str, confirm: bool = False,
                 i_know_what_im_doing: bool = False) -> None:
    """
    Check if SQL is allowed to execute based on safety tier.

    Args:
        sql: SQL statement to check
        confirm: If True, allows CAUTIOUS operations
        i_know_what_im_doing: If True, allows DESTRUCTIVE operations

    Raises:
        SafetyError: If operation is not allowed
    """
    tier = classify_sql(sql)

    if tier == SafetyTier.DESTRUCTIVE and not i_know_what_im_doing:
        raise SafetyError(
            "Destructive operation blocked. Use i_know_what_im_doing=True to override.",
            tier,
            sql
        )

    if tier == SafetyTier.CAUTIOUS and not confirm and not i_know_what_im_doing:
        raise SafetyError(
            "This operation requires confirm=True.",
            tier,
            sql
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_safety.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/supabase/safety.py tests/test_safety.py
git commit -m "feat: add SQL safety classification module"
```

---

## Task 3: Create PostgresAPI Core Class

**Files:**
- Create: `services/supabase/postgres.py`
- Test: `tests/test_postgres.py`

**Step 1: Write the failing tests for initialization**

Create `tests/test_postgres.py`:
```python
#!/usr/bin/env python3
"""Tests for PostgresAPI."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock
from services.supabase.postgres import PostgresAPI
from services.supabase.safety import SafetyError, SafetyTier


class TestPostgresAPIInit:
    """Test PostgresAPI initialization."""

    def test_init_with_project_name(self):
        with patch.dict('os.environ', {
            'SUPABASE_POSTGRES_URL': 'postgres://user:pass@localhost:5432/db'
        }):
            api = PostgresAPI('project1')
            assert api.project == 'project1'

    def test_init_with_direct_url(self):
        api = PostgresAPI('project1', url='postgres://user:pass@localhost:5432/db')
        assert api.connection_url == 'postgres://user:pass@localhost:5432/db'

    def test_init_raises_without_url(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="No Postgres URL"):
                PostgresAPI('project1')


class TestPostgresAPISafety:
    """Test safety classification integration."""

    @pytest.fixture
    def mock_api(self):
        with patch.dict('os.environ', {
            'SUPABASE_POSTGRES_URL': 'postgres://user:pass@localhost:5432/db'
        }):
            api = PostgresAPI('project1')
            api._conn = MagicMock()
            api._conn.cursor.return_value.__enter__ = MagicMock()
            api._conn.cursor.return_value.__exit__ = MagicMock()
            return api

    def test_safe_sql_executes(self, mock_api):
        mock_api._conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        mock_api.execute("CREATE TABLE test (id int)")
        # Should not raise

    def test_cautious_sql_requires_confirm(self, mock_api):
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("TRUNCATE users")
        assert "confirm=True" in str(exc.value)

    def test_cautious_sql_with_confirm_executes(self, mock_api):
        mock_api._conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        mock_api.execute("TRUNCATE users", confirm=True)
        # Should not raise

    def test_destructive_sql_blocked(self, mock_api):
        with pytest.raises(SafetyError) as exc:
            mock_api.execute("DROP TABLE users")
        assert "i_know_what_im_doing" in str(exc.value)

    def test_destructive_sql_with_override(self, mock_api):
        mock_api._conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []
        mock_api.execute("DROP TABLE users", i_know_what_im_doing=True)
        # Should not raise


class TestPostgresAPIDryRun:
    """Test dry-run mode."""

    @pytest.fixture
    def mock_api(self):
        with patch.dict('os.environ', {
            'SUPABASE_POSTGRES_URL': 'postgres://user:pass@localhost:5432/db'
        }):
            api = PostgresAPI('project1')
            api._conn = MagicMock()
            return api

    def test_dry_run_does_not_execute(self, mock_api, capsys):
        mock_api.execute("CREATE TABLE test (id int)", dry_run=True)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        mock_api._conn.cursor.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_postgres.py -v`
Expected: FAIL with "No module named 'services.supabase.postgres'"

**Step 3: Write minimal implementation**

Create `services/supabase/postgres.py`:
```python
#!/usr/bin/env python3
"""
PostgresAPI - Direct Postgres connection for DDL operations.

Use this for schema changes (CREATE TABLE, ALTER, etc.) while using
SupabaseAPI for regular queries via REST API.

Safety tiers:
- SAFE: CREATE, ALTER ADD - execute immediately
- CAUTIOUS: TRUNCATE, DROP COLUMN - require confirm=True
- DESTRUCTIVE: DROP TABLE - require i_know_what_im_doing=True
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

from services.supabase.safety import classify_sql, check_safety, SafetyTier, SafetyError


# Project configurations for Postgres URLs
POSTGRES_PROJECTS = {
    'project1': {
        'url_env': 'SUPABASE_POSTGRES_URL',
        'description': 'Project 1 - Primary database'
    },
    'project2': {
        'url_env': 'SUPABASE_POSTGRES_URL_2',
        'description': 'Project 2 - Secondary database'
    },
    'project3': {
        'url_env': 'SUPABASE_POSTGRES_URL_3',
        'description': 'Project 3 - Tertiary database'
    },
    # Aliases
    'smoothed': 'project1',
    'blingsting': 'project2',
    'scraping': 'project3',
}

# Audit log location
AUDIT_LOG_PATH = Path.home() / '.api-toolkit' / 'ddl_audit.log'


class PostgresAPI:
    """
    Direct Postgres connection for DDL operations.

    Use this alongside SupabaseAPI:
    - PostgresAPI: Schema changes (CREATE TABLE, ALTER, migrations)
    - SupabaseAPI: Data queries and CRUD via REST API

    Safety features:
    - SQL classification into SAFE/CAUTIOUS/DESTRUCTIVE tiers
    - Automatic transaction wrapping
    - Audit logging of all DDL operations
    - Dry-run mode for testing

    Examples:
        db = PostgresAPI('smoothed')

        # Safe operations - execute immediately
        db.execute("CREATE TABLE users (id uuid PRIMARY KEY)")

        # Cautious operations - require confirmation
        db.execute("TRUNCATE test_data", confirm=True)

        # Destructive operations - require explicit override
        db.execute("DROP TABLE old_backup", i_know_what_im_doing=True)

        # Dry-run mode
        db.execute("CREATE TABLE test (id int)", dry_run=True)
    """

    def __init__(self, project: str = 'project1', url: Optional[str] = None):
        """
        Initialize Postgres connection.

        Args:
            project: Project name ('project1', 'project2', 'project3') or aliases
            url: Optional direct Postgres connection URL
        """
        # Resolve aliases
        if project in POSTGRES_PROJECTS and isinstance(POSTGRES_PROJECTS[project], str):
            project = POSTGRES_PROJECTS[project]

        self.project = project

        # Get connection URL
        if url:
            self.connection_url = url
        elif project in POSTGRES_PROJECTS and isinstance(POSTGRES_PROJECTS[project], dict):
            config = POSTGRES_PROJECTS[project]
            self.connection_url = os.getenv(config['url_env'])
            self.project_description = config.get('description', '')
        else:
            self.connection_url = os.getenv('SUPABASE_POSTGRES_URL')
            self.project_description = f'Custom project: {project}'

        if not self.connection_url:
            raise ValueError(
                f"No Postgres URL found for project '{project}'. "
                f"Set {POSTGRES_PROJECTS.get(project, {}).get('url_env', 'SUPABASE_POSTGRES_URL')} in .env"
            )

        self._conn = None
        self._ensure_audit_dir()

    def _ensure_audit_dir(self):
        """Ensure audit log directory exists."""
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.connection_url)
            self._conn.autocommit = False
        return self._conn

    def _audit_log(self, sql: str, tier: SafetyTier, override_used: bool = False):
        """Log DDL operation to audit file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        override_str = " | override=True" if override_used else ""
        log_line = f"{timestamp} | {self.project} | {tier.value.upper()} | {sql[:200]}{override_str}\n"

        try:
            with open(AUDIT_LOG_PATH, 'a') as f:
                f.write(log_line)
        except Exception:
            pass  # Silently fail audit logging

    def execute(self, sql: str, confirm: bool = False,
                i_know_what_im_doing: bool = False,
                dry_run: bool = False) -> Optional[List[Dict]]:
        """
        Execute SQL with safety checks.

        Args:
            sql: SQL statement to execute
            confirm: Required for CAUTIOUS operations (TRUNCATE, DROP COLUMN)
            i_know_what_im_doing: Required for DESTRUCTIVE operations (DROP TABLE)
            dry_run: If True, show what would happen without executing

        Returns:
            Query results if any, None otherwise

        Raises:
            SafetyError: If operation is blocked by safety tier
        """
        tier = classify_sql(sql)

        if dry_run:
            print(f"[DRY RUN] Would execute: {sql[:100]}...")
            print(f"Classification: {tier.value.upper()}")
            if tier == SafetyTier.CAUTIOUS:
                print("Note: Would require confirm=True")
            elif tier == SafetyTier.DESTRUCTIVE:
                print("Note: Would require i_know_what_im_doing=True")
            print("No changes made.")
            return None

        # Check safety before executing
        check_safety(sql, confirm=confirm, i_know_what_im_doing=i_know_what_im_doing)

        # Log the operation
        self._audit_log(sql, tier, override_used=i_know_what_im_doing)

        # Execute with transaction
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)

                # Try to fetch results (for SELECT or RETURNING)
                try:
                    results = cur.fetchall()
                    conn.commit()
                    return [dict(row) for row in results]
                except psycopg2.ProgrammingError:
                    # No results to fetch (DDL statement)
                    conn.commit()
                    return None

        except Exception as e:
            conn.rollback()
            raise

    def query(self, sql: str) -> List[Dict]:
        """
        Execute SELECT query and return results.

        Args:
            sql: SELECT statement

        Returns:
            List of dicts with query results
        """
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (table_name,))
            return cur.fetchone()[0]

    def get_schema(self, table_name: str) -> List[Dict]:
        """Get table schema information."""
        sql = """
            SELECT
                column_name as name,
                data_type as type,
                is_nullable as nullable,
                column_default as default_value
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position
        """
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (table_name,))
            return [dict(row) for row in cur.fetchall()]

    def run_migration(self, file_path: str) -> None:
        """
        Run a SQL migration file.

        Args:
            file_path: Path to .sql file
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Migration file not found: {file_path}")

        sql = path.read_text()

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for statement in statements:
            tier = classify_sql(statement)
            if tier == SafetyTier.DESTRUCTIVE:
                print(f"Skipping destructive statement: {statement[:50]}...")
                print("Use execute() with i_know_what_im_doing=True for destructive operations")
                continue
            self.execute(statement, confirm=True)

        print(f"Migration complete: {file_path}")

    def run_migrations_from_dir(self, dir_path: str) -> None:
        """
        Run all .sql files in a directory in sorted order.

        Args:
            dir_path: Path to directory containing .sql files
        """
        path = Path(dir_path)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        sql_files = sorted(path.glob('*.sql'))

        for sql_file in sql_files:
            print(f"Running: {sql_file.name}")
            self.run_migration(str(sql_file))

    def transaction(self):
        """
        Context manager for explicit transaction control.

        Example:
            with db.transaction() as tx:
                tx.execute("CREATE TABLE a (...)")
                tx.execute("CREATE TABLE b (...)")
                # All succeed together or all rollback
        """
        return _TransactionContext(self)

    def close(self):
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class _TransactionContext:
    """Context manager for explicit transactions."""

    def __init__(self, api: PostgresAPI):
        self.api = api
        self.conn = None

    def __enter__(self):
        self.conn = self.api._get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
        else:
            self.conn.commit()

    def execute(self, sql: str, confirm: bool = False,
                i_know_what_im_doing: bool = False) -> Optional[List[Dict]]:
        """Execute SQL within the transaction."""
        tier = classify_sql(sql)
        check_safety(sql, confirm=confirm, i_know_what_im_doing=i_know_what_im_doing)
        self.api._audit_log(sql, tier, override_used=i_know_what_im_doing)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            try:
                return [dict(row) for row in cur.fetchall()]
            except psycopg2.ProgrammingError:
                return None


# Re-export SafetyError for convenience
__all__ = ['PostgresAPI', 'SafetyError', 'SafetyTier']
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_postgres.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/supabase/postgres.py tests/test_postgres.py
git commit -m "feat: add PostgresAPI with safety classification"
```

---

## Task 4: Update Configuration for Postgres URLs

**Files:**
- Modify: `core/config.py`
- Modify: `.env.example`

**Step 1: Update config.py**

Add to `core/config.py` in the SERVICES dict, update the supabase entry:
```python
'supabase': {
    'projects': {
        'project1': 'your-project-1-ref',
        'project2': 'your-project-2-ref',
        'project3': 'your-project-3-ref'
    },
    'env_vars': [
        'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_POSTGRES_URL',  # NEW: Direct Postgres access
        'SUPABASE_URL_2', 'SUPABASE_SERVICE_ROLE_KEY_2',
        'SUPABASE_POSTGRES_URL_2',
        'SUPABASE_URL_3', 'SUPABASE_SERVICE_ROLE_KEY_3',
        'SUPABASE_POSTGRES_URL_3',
    ],
    'token_cost': 600
},
```

**Step 2: Update .env.example**

Add to `.env.example`:
```bash
# Direct Postgres connections (for DDL/migrations)
# Get from: Supabase Dashboard → Settings → Database → Connection string
SUPABASE_POSTGRES_URL=postgres://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SUPABASE_POSTGRES_URL_2=postgres://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SUPABASE_POSTGRES_URL_3=postgres://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

**Step 3: Commit**

```bash
git add core/config.py .env.example
git commit -m "feat: add Postgres URL configuration"
```

---

## Task 5: Add Integration Tests

**Files:**
- Create: `tests/test_postgres_integration.py`

**Step 1: Write integration tests**

Create `tests/test_postgres_integration.py`:
```python
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
    not os.getenv('SUPABASE_POSTGRES_URL'),
    reason="SUPABASE_POSTGRES_URL not set"
)


class TestPostgresIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def db(self):
        api = PostgresAPI('project1')
        yield api
        api.close()

    def test_connection(self, db):
        """Test that we can connect."""
        result = db.query("SELECT 1 as test")
        assert result[0]['test'] == 1

    def test_table_exists(self, db):
        """Test table_exists method."""
        # This table should exist in any Supabase project
        # Adjust table name based on your project
        exists = db.table_exists('_test_safe_ddl_nonexistent_xyz')
        assert exists is False

    def test_create_and_drop_table(self, db):
        """Test creating and dropping a table."""
        table_name = '_test_safe_ddl_temp'

        # Clean up if exists from previous failed test
        if db.table_exists(table_name):
            db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)

        # Create table (SAFE)
        db.execute(f"CREATE TABLE {table_name} (id serial PRIMARY KEY, name text)")
        assert db.table_exists(table_name)

        # Get schema
        schema = db.get_schema(table_name)
        assert len(schema) == 2
        assert schema[0]['name'] == 'id'

        # Drop table (DESTRUCTIVE - requires override)
        db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)
        assert not db.table_exists(table_name)

    def test_transaction_rollback(self, db):
        """Test that failed transactions roll back."""
        table_name = '_test_safe_ddl_rollback'

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
        table_name = '_test_safe_ddl_dryrun'

        # Clean up
        if db.table_exists(table_name):
            db.execute(f"DROP TABLE {table_name}", i_know_what_im_doing=True)

        # Dry run
        db.execute(f"CREATE TABLE {table_name} (id int)", dry_run=True)

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert not db.table_exists(table_name)
```

**Step 2: Run integration tests**

Run: `pytest tests/test_postgres_integration.py -v`
Expected: PASS (or SKIP if no Postgres URL configured)

**Step 3: Commit**

```bash
git add tests/test_postgres_integration.py
git commit -m "test: add PostgresAPI integration tests"
```

---

## Task 6: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `services/supabase/README.md`

**Step 1: Add section to README.md**

Add after the Supabase examples section:
```markdown
### Direct Postgres Access (DDL Operations)

For schema changes that the REST API can't handle:

```python
from api_toolkit.services.supabase.postgres import PostgresAPI

db = PostgresAPI('smoothed')

# Safe operations - execute immediately
db.execute("CREATE TABLE users (id uuid PRIMARY KEY, email text)")
db.execute("ALTER TABLE users ADD COLUMN phone text")

# Cautious operations - require confirmation
db.execute("TRUNCATE test_data", confirm=True)

# Destructive operations - blocked by default
db.execute("DROP TABLE users")  # Raises SafetyError
db.execute("DROP TABLE users", i_know_what_im_doing=True)  # Works

# Dry-run mode
db.execute("CREATE TABLE test (id int)", dry_run=True)

# Run migration files
db.run_migration('migrations/001_init.sql')
```

**Safety tiers:**
| Tier | Operations | Behavior |
|------|------------|----------|
| SAFE | CREATE, ALTER ADD, SELECT | Execute immediately |
| CAUTIOUS | TRUNCATE, ALTER DROP COLUMN | Require `confirm=True` |
| DESTRUCTIVE | DROP TABLE, DELETE without WHERE | Require `i_know_what_im_doing=True` |
```

**Step 2: Update CLAUDE.md**

Add to the Supabase section in CLAUDE.md:
```markdown
### Direct Postgres Access (NEW)

For DDL operations the REST API can't handle:

```python
from api_toolkit.services.supabase.postgres import PostgresAPI

db = PostgresAPI('smoothed')

# CREATE is safe - runs immediately
db.execute("CREATE TABLE campaigns (id uuid PRIMARY KEY)")

# DROP requires explicit override
db.execute("DROP TABLE old_data", i_know_what_im_doing=True)

# Dry run to preview
db.execute("ALTER TABLE users ADD COLUMN phone text", dry_run=True)
```

Requires `SUPABASE_POSTGRES_URL` in .env (get from Supabase Dashboard → Settings → Database).
```

**Step 3: Commit**

```bash
git add README.md CLAUDE.md services/supabase/README.md
git commit -m "docs: add PostgresAPI documentation"
```

---

## Task 7: Final Verification and Cleanup

**Files:**
- All modified files

**Step 1: Run all tests**

Run: `pytest tests/test_safety.py tests/test_postgres.py -v`
Expected: All tests PASS

**Step 2: Run linting (if available)**

Run: `python -m py_compile services/supabase/safety.py services/supabase/postgres.py`
Expected: No syntax errors

**Step 3: Test CLI usage**

Run: `python -c "from services.supabase.postgres import PostgresAPI; print('Import OK')"`
Expected: "Import OK"

**Step 4: Final commit**

```bash
git status
# Ensure no uncommitted changes
```

---

## Summary

| Task | Files | Tests | Commits |
|------|-------|-------|---------|
| 1. Dependency | requirements.txt | - | 1 |
| 2. Safety module | safety.py, test_safety.py | 14 tests | 1 |
| 3. PostgresAPI | postgres.py, test_postgres.py | 9 tests | 1 |
| 4. Configuration | config.py, .env.example | - | 1 |
| 5. Integration tests | test_postgres_integration.py | 5 tests | 1 |
| 6. Documentation | README, CLAUDE.md | - | 1 |
| 7. Verification | - | All | - |

**Total: 28 tests, 6 commits**
