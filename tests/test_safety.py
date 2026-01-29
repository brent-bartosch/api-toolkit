#!/usr/bin/env python3
"""
Test Suite for SQL Safety Classification Module

Tests for the safety.py module that classifies SQL statements
into SAFE, CAUTIOUS, or DESTRUCTIVE tiers.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase.safety import (
    SafetyTier,
    SafetyError,
    classify_sql,
    check_safety,
)


class TestSafetyClassification(unittest.TestCase):
    """Test cases for SQL safety classification"""

    # ============= SAFE SQL TESTS =============

    def test_create_table_is_safe(self):
        """CREATE TABLE should be classified as SAFE"""
        sql = "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_create_index_is_safe(self):
        """CREATE INDEX should be classified as SAFE"""
        sql = "CREATE INDEX idx_users_email ON users(email)"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_alter_add_column_is_safe(self):
        """ALTER TABLE ADD COLUMN should be classified as SAFE"""
        sql = "ALTER TABLE users ADD COLUMN age INTEGER"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_alter_rename_is_safe(self):
        """ALTER TABLE RENAME should be classified as SAFE"""
        sql = "ALTER TABLE users RENAME COLUMN name TO full_name"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_select_is_safe(self):
        """SELECT statements should be classified as SAFE"""
        sql = "SELECT * FROM users WHERE active = true"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_insert_is_safe(self):
        """INSERT statements should be classified as SAFE"""
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_update_with_where_is_safe(self):
        """UPDATE with WHERE clause should be classified as SAFE"""
        sql = "UPDATE users SET active = false WHERE id = 123"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_comment_on_is_safe(self):
        """COMMENT ON should be classified as SAFE"""
        sql = "COMMENT ON TABLE users IS 'User accounts'"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_create_type_is_safe(self):
        """CREATE TYPE should be classified as SAFE"""
        sql = "CREATE TYPE status_enum AS ENUM ('active', 'inactive')"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_create_extension_is_safe(self):
        """CREATE EXTENSION should be classified as SAFE"""
        sql = "CREATE EXTENSION IF NOT EXISTS pgcrypto"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_create_function_is_safe(self):
        """CREATE FUNCTION should be classified as SAFE"""
        sql = "CREATE FUNCTION add(a INTEGER, b INTEGER) RETURNS INTEGER AS $$ SELECT a + b; $$ LANGUAGE SQL"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    # ============= CAUTIOUS SQL TESTS =============

    def test_truncate_is_cautious(self):
        """TRUNCATE should be classified as CAUTIOUS"""
        sql = "TRUNCATE TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    def test_alter_drop_column_is_cautious(self):
        """ALTER TABLE DROP COLUMN should be classified as CAUTIOUS"""
        sql = "ALTER TABLE users DROP COLUMN age"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    def test_delete_with_where_is_cautious(self):
        """DELETE with WHERE clause should be classified as CAUTIOUS"""
        sql = "DELETE FROM users WHERE status = 'inactive'"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    def test_update_without_where_is_cautious(self):
        """UPDATE without WHERE clause should be classified as CAUTIOUS"""
        sql = "UPDATE users SET active = false"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    # ============= DESTRUCTIVE SQL TESTS =============

    def test_drop_table_is_destructive(self):
        """DROP TABLE should be classified as DESTRUCTIVE"""
        sql = "DROP TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_table_if_exists_is_destructive(self):
        """DROP TABLE IF EXISTS should be classified as DESTRUCTIVE"""
        sql = "DROP TABLE IF EXISTS users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_delete_without_where_is_destructive(self):
        """DELETE without WHERE clause should be classified as DESTRUCTIVE"""
        sql = "DELETE FROM users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_database_is_destructive(self):
        """DROP DATABASE should be classified as DESTRUCTIVE"""
        sql = "DROP DATABASE mydb"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_schema_is_destructive(self):
        """DROP SCHEMA should be classified as DESTRUCTIVE"""
        sql = "DROP SCHEMA public CASCADE"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_function_is_destructive(self):
        """DROP FUNCTION should be classified as DESTRUCTIVE"""
        sql = "DROP FUNCTION my_function"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_type_is_destructive(self):
        """DROP TYPE should be classified as DESTRUCTIVE"""
        sql = "DROP TYPE status_enum"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_drop_index_is_destructive(self):
        """DROP INDEX should be classified as DESTRUCTIVE"""
        sql = "DROP INDEX idx_users_email"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_alter_drop_constraint_is_destructive(self):
        """ALTER TABLE DROP CONSTRAINT should be classified as DESTRUCTIVE"""
        sql = "ALTER TABLE users DROP CONSTRAINT users_pkey"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    # ============= EDGE CASES =============

    def test_case_insensitive(self):
        """Classification should be case-insensitive"""
        sql_lower = "drop table users"
        sql_upper = "DROP TABLE USERS"
        sql_mixed = "DrOp TaBlE users"

        self.assertEqual(classify_sql(sql_lower), SafetyTier.DESTRUCTIVE)
        self.assertEqual(classify_sql(sql_upper), SafetyTier.DESTRUCTIVE)
        self.assertEqual(classify_sql(sql_mixed), SafetyTier.DESTRUCTIVE)

    def test_multiline_sql(self):
        """Classification should handle multiline SQL"""
        sql = """
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_multiline_destructive_sql(self):
        """Classification should handle multiline destructive SQL"""
        sql = """
            DROP
            TABLE
            users
        """
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_sql_with_comments(self):
        """Classification should handle SQL with comments"""
        sql = "-- This drops the table\nDROP TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_unknown_sql_defaults_to_cautious(self):
        """Unknown SQL should default to CAUTIOUS for safety"""
        sql = "VACUUM ANALYZE users"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    # ============= MULTI-STATEMENT SQL TESTS =============

    def test_multi_statement_detects_destructive(self):
        """Multi-statement SQL with DROP should be DESTRUCTIVE"""
        sql = "SELECT * FROM users; DROP TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_multi_statement_detects_destructive_first(self):
        """Multi-statement SQL with DROP first should be DESTRUCTIVE"""
        sql = "DROP TABLE users; SELECT * FROM users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_multi_statement_detects_destructive_middle(self):
        """Multi-statement SQL with DROP in middle should be DESTRUCTIVE"""
        sql = "SELECT * FROM users; DROP TABLE users; SELECT 1"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_multi_statement_safe_only(self):
        """Multi-statement SQL with only SAFE statements should be SAFE"""
        sql = "SELECT * FROM users; SELECT * FROM orders"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)

    def test_multi_statement_cautious_highest(self):
        """Multi-statement SQL with CAUTIOUS as highest tier"""
        sql = "SELECT * FROM users; TRUNCATE TABLE temp"
        self.assertEqual(classify_sql(sql), SafetyTier.CAUTIOUS)

    # ============= BLOCK COMMENT BYPASS TESTS =============

    def test_block_comment_before_drop(self):
        """Block comment before DROP should still be DESTRUCTIVE"""
        sql = "/* comment */ DROP TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_block_comment_multiline(self):
        """Multiline block comment before DROP should still be DESTRUCTIVE"""
        sql = """/* this is a
        multiline comment */
        DROP TABLE users"""
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_block_comment_nested_text(self):
        """Block comment with nested text should be removed"""
        sql = "/* SELECT * FROM safe */ DROP TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_block_comment_multiple(self):
        """Multiple block comments should all be removed"""
        sql = "/* comment1 */ DROP /* comment2 */ TABLE users"
        self.assertEqual(classify_sql(sql), SafetyTier.DESTRUCTIVE)

    def test_block_comment_with_safe_sql(self):
        """Block comment with SAFE SQL should be SAFE"""
        sql = "/* just a comment */ SELECT * FROM users"
        self.assertEqual(classify_sql(sql), SafetyTier.SAFE)


class TestSafetyError(unittest.TestCase):
    """Test cases for SafetyError exception"""

    def test_safety_error_has_tier(self):
        """SafetyError should have a tier attribute"""
        error = SafetyError(
            tier=SafetyTier.DESTRUCTIVE,
            sql="DROP TABLE users",
            message="Blocked destructive SQL",
        )
        self.assertEqual(error.tier, SafetyTier.DESTRUCTIVE)
        self.assertEqual(error.sql, "DROP TABLE users")
        self.assertIn("Blocked", str(error))

    def test_safety_error_str_representation(self):
        """SafetyError should have meaningful string representation"""
        error = SafetyError(
            tier=SafetyTier.CAUTIOUS,
            sql="TRUNCATE users",
            message="Requires confirmation",
        )
        self.assertIn("Requires confirmation", str(error))
        self.assertIn("CAUTIOUS", str(error))


class TestCheckSafety(unittest.TestCase):
    """Test cases for check_safety function"""

    def test_safe_sql_passes_without_confirmation(self):
        """SAFE SQL should pass without any confirmation"""
        sql = "SELECT * FROM users"
        # Should not raise
        check_safety(sql)

    def test_cautious_sql_blocked_without_confirmation(self):
        """CAUTIOUS SQL should be blocked without confirmation"""
        sql = "TRUNCATE TABLE users"
        with self.assertRaises(SafetyError) as context:
            check_safety(sql)
        self.assertEqual(context.exception.tier, SafetyTier.CAUTIOUS)

    def test_cautious_sql_passes_with_confirm(self):
        """CAUTIOUS SQL should pass with confirm=True"""
        sql = "TRUNCATE TABLE users"
        # Should not raise
        check_safety(sql, confirm=True)

    def test_destructive_sql_blocked_without_override(self):
        """DESTRUCTIVE SQL should be blocked even with confirm=True"""
        sql = "DROP TABLE users"
        with self.assertRaises(SafetyError) as context:
            check_safety(sql, confirm=True)
        self.assertEqual(context.exception.tier, SafetyTier.DESTRUCTIVE)

    def test_destructive_sql_passes_with_override(self):
        """DESTRUCTIVE SQL should pass with i_know_what_im_doing=True"""
        sql = "DROP TABLE users"
        # Should not raise
        check_safety(sql, i_know_what_im_doing=True)

    def test_safe_sql_returns_tier(self):
        """check_safety should return the tier on success"""
        sql = "SELECT * FROM users"
        result = check_safety(sql)
        self.assertEqual(result, SafetyTier.SAFE)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
