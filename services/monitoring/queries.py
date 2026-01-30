#!/usr/bin/env python3
"""
SQL queries for monitoring pg_cron jobs.

These queries work with the cron schema in Supabase/PostgreSQL.
"""

# Get all cron jobs
GET_CRON_JOBS = """
SELECT
    jobid,
    jobname as job_name,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active
FROM cron.job
ORDER BY jobname
"""

# Get recent cron execution history (last 7 days)
GET_CRON_HISTORY = """
SELECT
    runid,
    jobid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
WHERE start_time > now() - interval '7 days'
ORDER BY start_time DESC
"""

# Get history for a specific job
GET_JOB_HISTORY = """
SELECT
    runid,
    status,
    return_message,
    start_time,
    end_time,
    end_time - start_time as duration
FROM cron.job_run_details
WHERE jobid = %s
ORDER BY start_time DESC
LIMIT %s
"""

# Get last successful run for a job
GET_LAST_SUCCESS = """
SELECT
    start_time,
    end_time,
    return_message
FROM cron.job_run_details
WHERE jobid = %s AND status = 'succeeded'
ORDER BY start_time DESC
LIMIT 1
"""


def is_valid_sql(query: str) -> bool:
    """
    Basic validation that a string looks like SQL.

    Args:
        query: SQL query string

    Returns:
        True if it appears to be valid SQL
    """
    normalized = query.strip().upper()
    valid_starts = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP")
    return any(normalized.startswith(start) for start in valid_starts)
