#!/usr/bin/env python3
"""Tests for monitoring SQL queries."""
import pytest
from services.monitoring.queries import (
    GET_CRON_JOBS,
    GET_CRON_HISTORY,
    is_valid_sql,
)


def test_get_cron_jobs_query_is_valid_sql():
    """GET_CRON_JOBS should be valid SQL."""
    assert is_valid_sql(GET_CRON_JOBS)


def test_get_cron_history_query_is_valid_sql():
    """GET_CRON_HISTORY should be valid SQL."""
    assert is_valid_sql(GET_CRON_HISTORY)


def test_queries_are_select_only():
    """All queries should be SELECT statements."""
    assert GET_CRON_JOBS.strip().upper().startswith("SELECT")
    assert GET_CRON_HISTORY.strip().upper().startswith("SELECT")
