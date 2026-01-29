#!/usr/bin/env python3
"""
SQL Safety Classification Module

Classifies SQL statements into safety tiers:
- SAFE: Non-destructive operations (CREATE, SELECT, INSERT, UPDATE with WHERE)
- CAUTIOUS: Potentially dangerous (TRUNCATE, DELETE with WHERE, DROP COLUMN)
- DESTRUCTIVE: Irreversible data loss (DROP TABLE, DELETE without WHERE)

Usage:
    from services.supabase.safety import classify_sql, check_safety, SafetyTier

    # Classify a SQL statement
    tier = classify_sql("DROP TABLE users")
    # Returns: SafetyTier.DESTRUCTIVE

    # Check and potentially block unsafe SQL
    check_safety("TRUNCATE users")  # Raises SafetyError
    check_safety("TRUNCATE users", confirm=True)  # Passes

    # Override safety for destructive operations
    check_safety("DROP TABLE users", i_know_what_im_doing=True)  # Passes
"""

import re
from enum import Enum
from typing import Optional


class SafetyTier(Enum):
    """
    Safety classification tiers for SQL statements.

    SAFE: Operations that don't destroy existing data
    CAUTIOUS: Operations that may affect data but are recoverable/scoped
    DESTRUCTIVE: Operations that cause irreversible data loss
    """

    SAFE = "SAFE"
    CAUTIOUS = "CAUTIOUS"
    DESTRUCTIVE = "DESTRUCTIVE"


class SafetyError(Exception):
    """
    Exception raised when a SQL statement is blocked by safety checks.

    Attributes:
        tier: The SafetyTier that triggered the block
        sql: The SQL statement that was blocked
        message: Human-readable explanation
    """

    def __init__(self, tier: SafetyTier, sql: str, message: str):
        self.tier = tier
        self.sql = sql
        self.message = message
        super().__init__(f"[{tier.value}] {message}")

    def __str__(self) -> str:
        return f"[{self.tier.value}] {self.message}"


# =============================================================================
# Pattern Definitions
# =============================================================================

# SAFE_PATTERNS: Operations that don't destroy existing data
# Order matters - more specific patterns should come first
SAFE_PATTERNS = [
    # Schema creation (additive operations)
    r"^\s*CREATE\s+TABLE",
    r"^\s*CREATE\s+INDEX",
    r"^\s*CREATE\s+UNIQUE\s+INDEX",
    r"^\s*CREATE\s+TYPE",
    r"^\s*CREATE\s+EXTENSION",
    r"^\s*CREATE\s+FUNCTION",
    r"^\s*CREATE\s+OR\s+REPLACE\s+FUNCTION",
    r"^\s*CREATE\s+TRIGGER",
    r"^\s*CREATE\s+VIEW",
    r"^\s*CREATE\s+SCHEMA",
    r"^\s*CREATE\s+SEQUENCE",
    # Additive alterations
    r"^\s*ALTER\s+TABLE\s+\S+\s+ADD\s+COLUMN",
    r"^\s*ALTER\s+TABLE\s+\S+\s+ADD\s+CONSTRAINT",
    r"^\s*ALTER\s+TABLE\s+\S+\s+RENAME",
    r"^\s*ALTER\s+TABLE\s+\S+\s+ALTER\s+COLUMN\s+\S+\s+SET",
    # Documentation
    r"^\s*COMMENT\s+ON",
    # Read operations
    r"^\s*SELECT",
    # Write operations (scoped)
    r"^\s*INSERT\s+INTO",
    r"^\s*UPDATE\s+\S+\s+SET\s+.+\s+WHERE",  # UPDATE with WHERE
]

# CAUTIOUS_PATTERNS: Operations that may affect data but can be confirmed
CAUTIOUS_PATTERNS = [
    # Column removal (data loss but recoverable with backup)
    r"^\s*ALTER\s+TABLE\s+\S+\s+DROP\s+COLUMN",
    # Table truncation (data loss but table structure preserved)
    r"^\s*TRUNCATE",
    # Scoped deletion (has WHERE clause)
    r"^\s*DELETE\s+FROM\s+\S+\s+WHERE",
    # UPDATE without WHERE (affects all rows but can be rolled back)
    r"^\s*UPDATE\s+\S+\s+SET\s+(?!.*\bWHERE\b)",
]

# DESTRUCTIVE_PATTERNS: Operations that cause irreversible data loss
DESTRUCTIVE_PATTERNS = [
    # DROP operations (schema destruction)
    r"^\s*DROP\s+TABLE",
    r"^\s*DROP\s+DATABASE",
    r"^\s*DROP\s+SCHEMA",
    r"^\s*DROP\s+FUNCTION",
    r"^\s*DROP\s+TYPE",
    r"^\s*DROP\s+INDEX",
    r"^\s*DROP\s+TRIGGER",
    r"^\s*DROP\s+VIEW",
    r"^\s*DROP\s+SEQUENCE",
    r"^\s*DROP\s+EXTENSION",
    # Constraint removal
    r"^\s*ALTER\s+TABLE\s+\S+\s+DROP\s+CONSTRAINT",
    # Unscoped DELETE (no WHERE = delete all rows)
    r"^\s*DELETE\s+FROM\s+\S+\s*(?:;?\s*)?$",
]


# =============================================================================
# Classification Functions
# =============================================================================


def _normalize_sql(sql: str) -> str:
    """
    Normalize SQL for pattern matching.

    - Strip leading/trailing whitespace
    - Collapse multiple whitespace into single spaces
    - Convert to uppercase for case-insensitive matching
    - Remove SQL comments (single-line --)
    """
    # Remove single-line comments
    sql = re.sub(r"--[^\n]*", "", sql)

    # Collapse whitespace (including newlines) into single spaces
    sql = " ".join(sql.split())

    # Strip and uppercase
    return sql.strip().upper()


def classify_sql(sql: str) -> SafetyTier:
    """
    Classify a SQL statement into a safety tier.

    Args:
        sql: The SQL statement to classify

    Returns:
        SafetyTier.SAFE, SafetyTier.CAUTIOUS, or SafetyTier.DESTRUCTIVE

    Priority order:
        1. DESTRUCTIVE patterns checked first (most dangerous)
        2. CAUTIOUS patterns checked second
        3. SAFE patterns checked third
        4. Unknown SQL defaults to CAUTIOUS
    """
    normalized = _normalize_sql(sql)

    # Check DESTRUCTIVE patterns first (most dangerous)
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return SafetyTier.DESTRUCTIVE

    # Check CAUTIOUS patterns second
    for pattern in CAUTIOUS_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return SafetyTier.CAUTIOUS

    # Check SAFE patterns third
    for pattern in SAFE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return SafetyTier.SAFE

    # Default to CAUTIOUS for unknown SQL (fail-safe)
    return SafetyTier.CAUTIOUS


def check_safety(
    sql: str,
    confirm: bool = False,
    i_know_what_im_doing: bool = False,
) -> SafetyTier:
    """
    Check if a SQL statement is safe to execute.

    Args:
        sql: The SQL statement to check
        confirm: If True, allows CAUTIOUS operations to proceed
        i_know_what_im_doing: If True, allows DESTRUCTIVE operations to proceed

    Returns:
        The SafetyTier of the SQL statement if allowed

    Raises:
        SafetyError: If the SQL is blocked by safety checks

    Safety levels:
        - SAFE: Always allowed
        - CAUTIOUS: Requires confirm=True
        - DESTRUCTIVE: Requires i_know_what_im_doing=True
    """
    tier = classify_sql(sql)

    if tier == SafetyTier.SAFE:
        return tier

    if tier == SafetyTier.CAUTIOUS:
        if confirm or i_know_what_im_doing:
            return tier
        raise SafetyError(
            tier=tier,
            sql=sql,
            message=(
                "This SQL may affect multiple rows or remove data. "
                "Use confirm=True to proceed."
            ),
        )

    if tier == SafetyTier.DESTRUCTIVE:
        if i_know_what_im_doing:
            return tier
        raise SafetyError(
            tier=tier,
            sql=sql,
            message=(
                "This SQL will cause irreversible data loss. "
                "Use i_know_what_im_doing=True to proceed."
            ),
        )

    # Should never reach here, but just in case
    return tier


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python safety.py '<SQL statement>'")
        print("\nExamples:")
        print("  python safety.py 'CREATE TABLE users (id INT)'")
        print("  python safety.py 'DROP TABLE users'")
        print("  python safety.py 'DELETE FROM users WHERE id = 1'")
        sys.exit(0)

    sql = " ".join(sys.argv[1:])
    tier = classify_sql(sql)

    # Color output based on tier
    colors = {
        SafetyTier.SAFE: "\033[92m",  # Green
        SafetyTier.CAUTIOUS: "\033[93m",  # Yellow
        SafetyTier.DESTRUCTIVE: "\033[91m",  # Red
    }
    reset = "\033[0m"

    print(f"{colors[tier]}[{tier.value}]{reset} {sql[:50]}...")
    print(f"\nClassification: {tier.value}")

    if tier == SafetyTier.SAFE:
        print("This SQL is safe to execute.")
    elif tier == SafetyTier.CAUTIOUS:
        print("This SQL requires confirmation (confirm=True).")
    else:
        print("This SQL is destructive (requires i_know_what_im_doing=True).")
