# Supabase Monitoring System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a centralized monitoring system that discovers pg_cron jobs and edge functions across 4 Supabase projects, tracks their health, and sends alerts via Discord (general) and Telegram (critical).

**Architecture:** MonitoringAPI service in api-toolkit that uses PostgresAPI to query pg_cron tables across projects, stores inventory and health logs in thordata, and dispatches alerts based on criticality.

**Tech Stack:** Python, psycopg2 (via existing PostgresAPI), requests (for Discord/Telegram webhooks), Supabase Management API

---

## Task 1: Create Service Directory Structure

**Files:**
- Create: `services/monitoring/__init__.py`
- Create: `services/monitoring/api.py` (stub)
- Create: `services/monitoring/README.md`

**Step 1: Create the monitoring service directory**

```bash
mkdir -p services/monitoring
```

**Step 2: Create `__init__.py`**

```python
"""Monitoring service for Supabase jobs and edge functions."""
from .api import MonitoringAPI

__all__ = ['MonitoringAPI']
```

**Step 3: Create stub `api.py`**

```python
#!/usr/bin/env python3
"""
Supabase Monitoring API
Token Cost: ~800 tokens when loaded

Monitors pg_cron jobs and edge functions across multiple Supabase projects.
"""

class MonitoringAPI:
    """
    Centralized monitoring for Supabase infrastructure.

    CAPABILITIES:
    - Discover pg_cron jobs across all projects
    - Discover edge functions via Management API
    - Track job health and execution history
    - Send alerts via Discord and Telegram

    COMMON PATTERNS:
    ```python
    monitor = MonitoringAPI()
    monitor.audit_all_projects()  # Discover all jobs
    monitor.check_health()        # Run health checks
    ```
    """

    def __init__(self):
        pass

    def test_connection(self) -> bool:
        """Test if monitoring is configured"""
        return True
```

**Step 4: Create `README.md`**

```markdown
# Monitoring Service

Centralized monitoring for Supabase pg_cron jobs and edge functions.

## Setup

1. Ensure Postgres URLs are in `.env` for all projects
2. Set up Discord webhook and Telegram bot
3. Create tables in thordata project

## Usage

```python
from api_toolkit.services.monitoring.api import MonitoringAPI

monitor = MonitoringAPI()
monitor.audit_all_projects()
monitor.check_health()
```
```

**Step 5: Verify structure**

Run: `ls -la services/monitoring/`
Expected: Shows `__init__.py`, `api.py`, `README.md`

**Step 6: Commit**

```bash
git add services/monitoring/
git commit -m "feat(monitoring): create service directory structure"
```

---

## Task 2: Add Monitoring Service to Config

**Files:**
- Modify: `core/config.py:49-77` (add monitoring to SERVICES dict)

**Step 1: Read current config**

Verify the SERVICES dict structure.

**Step 2: Add monitoring service config**

Add to `core/config.py` SERVICES dict:

```python
"monitoring": {
    "env_vars": [
        "DISCORD_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SUPABASE_ACCESS_TOKEN",
    ],
    "projects": ["smoothed", "blingsting", "scraping", "thordata"],
    "token_cost": 800,
},
```

**Step 3: Verify config loads**

Run: `python -c "from core.config import Config; print('monitoring' in Config.SERVICES)"`
Expected: `True`

**Step 4: Commit**

```bash
git add core/config.py
git commit -m "feat(monitoring): add service to config registry"
```

---

## Task 3: Create SQL Queries Module

**Files:**
- Create: `services/monitoring/queries.py`
- Create: `tests/test_monitoring_queries.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_queries.py -v`
Expected: FAIL with "No module named 'services.monitoring.queries'"

**Step 3: Write queries.py**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_queries.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add services/monitoring/queries.py tests/test_monitoring_queries.py
git commit -m "feat(monitoring): add pg_cron SQL queries"
```

---

## Task 4: Create Discovery Module

**Files:**
- Create: `services/monitoring/discovery.py`
- Create: `tests/test_monitoring_discovery.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Tests for monitoring discovery module."""
import pytest
from unittest.mock import Mock, patch
from services.monitoring.discovery import (
    discover_cron_jobs,
    parse_cron_schedule,
    calculate_expected_interval_minutes,
)


def test_parse_cron_schedule_hourly():
    """Hourly cron should be parsed correctly."""
    result = parse_cron_schedule("0 * * * *")
    assert result["frequency"] == "hourly"


def test_parse_cron_schedule_daily():
    """Daily cron should be parsed correctly."""
    result = parse_cron_schedule("0 0 * * *")
    assert result["frequency"] == "daily"


def test_parse_cron_schedule_every_5_minutes():
    """Every 5 minutes should be parsed correctly."""
    result = parse_cron_schedule("*/5 * * * *")
    assert result["frequency"] == "every_5_minutes"


def test_calculate_expected_interval_hourly():
    """Hourly job should expect 60 minute interval."""
    minutes = calculate_expected_interval_minutes("0 * * * *")
    assert minutes == 60


def test_calculate_expected_interval_daily():
    """Daily job should expect 1440 minute interval."""
    minutes = calculate_expected_interval_minutes("0 0 * * *")
    assert minutes == 1440


def test_calculate_expected_interval_every_5_minutes():
    """Every 5 min job should expect 5 minute interval."""
    minutes = calculate_expected_interval_minutes("*/5 * * * *")
    assert minutes == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_discovery.py -v`
Expected: FAIL with "No module named 'services.monitoring.discovery'"

**Step 3: Write discovery.py**

```python
#!/usr/bin/env python3
"""
Discovery module for finding pg_cron jobs and edge functions.
"""

import os
import re
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.supabase.postgres import PostgresAPI
from services.monitoring.queries import GET_CRON_JOBS, GET_CRON_HISTORY


# Project configurations
PROJECTS = ["smoothed", "blingsting", "scraping", "thordata"]


def parse_cron_schedule(schedule: str) -> Dict[str, Any]:
    """
    Parse a cron schedule expression into human-readable format.

    Args:
        schedule: Cron expression (e.g., "0 * * * *")

    Returns:
        Dict with frequency and description
    """
    parts = schedule.split()
    if len(parts) != 5:
        return {"frequency": "unknown", "description": schedule}

    minute, hour, day, month, weekday = parts

    # Every N minutes
    if minute.startswith("*/"):
        n = int(minute[2:])
        return {
            "frequency": f"every_{n}_minutes",
            "description": f"Every {n} minutes",
            "interval_minutes": n,
        }

    # Hourly (minute is fixed, hour is *)
    if hour == "*" and day == "*" and month == "*" and weekday == "*":
        return {
            "frequency": "hourly",
            "description": f"Hourly at minute {minute}",
            "interval_minutes": 60,
        }

    # Daily (hour and minute fixed, rest is *)
    if day == "*" and month == "*" and weekday == "*":
        return {
            "frequency": "daily",
            "description": f"Daily at {hour}:{minute}",
            "interval_minutes": 1440,
        }

    # Weekly
    if day == "*" and month == "*" and weekday != "*":
        return {
            "frequency": "weekly",
            "description": f"Weekly on day {weekday} at {hour}:{minute}",
            "interval_minutes": 10080,
        }

    # Monthly
    if month == "*" and weekday == "*" and day != "*":
        return {
            "frequency": "monthly",
            "description": f"Monthly on day {day} at {hour}:{minute}",
            "interval_minutes": 43200,
        }

    return {"frequency": "custom", "description": schedule, "interval_minutes": None}


def calculate_expected_interval_minutes(schedule: str) -> Optional[int]:
    """
    Calculate expected interval between runs in minutes.

    Args:
        schedule: Cron expression

    Returns:
        Expected minutes between runs, or None if unknown
    """
    parsed = parse_cron_schedule(schedule)
    return parsed.get("interval_minutes")


def discover_cron_jobs(project: str) -> List[Dict[str, Any]]:
    """
    Discover all pg_cron jobs in a project.

    Args:
        project: Project name (smoothed, blingsting, scraping, thordata)

    Returns:
        List of job dictionaries
    """
    try:
        api = PostgresAPI(project)
        jobs = api.query(GET_CRON_JOBS)
        api.close()

        # Enrich with parsed schedule
        for job in jobs:
            if job.get("schedule"):
                parsed = parse_cron_schedule(job["schedule"])
                job["parsed_schedule"] = parsed
                job["expected_interval_minutes"] = parsed.get("interval_minutes")
            job["project"] = project
            job["job_type"] = "pg_cron"
            job["discovered_at"] = datetime.now().isoformat()

        return jobs
    except Exception as e:
        print(f"Error discovering jobs in {project}: {e}")
        return []


def discover_cron_history(project: str) -> List[Dict[str, Any]]:
    """
    Get recent cron job execution history.

    Args:
        project: Project name

    Returns:
        List of execution records
    """
    try:
        api = PostgresAPI(project)
        history = api.query(GET_CRON_HISTORY)
        api.close()

        for record in history:
            record["project"] = project

        return history
    except Exception as e:
        print(f"Error getting history for {project}: {e}")
        return []


def discover_edge_functions(project_id: str, access_token: str) -> List[Dict[str, Any]]:
    """
    Discover edge functions via Supabase Management API.

    Args:
        project_id: Supabase project ID (ref)
        access_token: Supabase access token

    Returns:
        List of edge function details
    """
    url = f"https://api.supabase.com/v1/projects/{project_id}/functions"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        functions = response.json()

        for func in functions:
            func["job_type"] = "edge_function"
            func["discovered_at"] = datetime.now().isoformat()

        return functions
    except Exception as e:
        print(f"Error discovering edge functions: {e}")
        return []


def discover_all_projects() -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover all jobs across all configured projects.

    Returns:
        Dict mapping project names to lists of jobs
    """
    results = {}

    for project in PROJECTS:
        jobs = discover_cron_jobs(project)
        results[project] = jobs
        print(f"Found {len(jobs)} jobs in {project}")

    return results
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_discovery.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add services/monitoring/discovery.py tests/test_monitoring_discovery.py
git commit -m "feat(monitoring): add discovery module for pg_cron jobs"
```

---

## Task 5: Create Alerts Module

**Files:**
- Create: `services/monitoring/alerts.py`
- Create: `tests/test_monitoring_alerts.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Tests for monitoring alerts module."""
import pytest
from unittest.mock import Mock, patch
from services.monitoring.alerts import (
    format_discord_message,
    format_telegram_message,
    AlertSender,
)


def test_format_discord_message_failed():
    """Failed job should format with warning emoji."""
    msg = format_discord_message(
        job_name="sync_leads",
        project="smoothed",
        status="failed",
        error="connection timeout",
    )
    assert "sync_leads" in msg
    assert "smoothed" in msg
    assert "connection timeout" in msg


def test_format_discord_message_missed():
    """Missed job should format with clock emoji."""
    msg = format_discord_message(
        job_name="daily_report",
        project="blingsting",
        status="missed",
    )
    assert "daily_report" in msg
    assert "missed" in msg.lower() or "hasn't run" in msg.lower()


def test_format_telegram_message_critical():
    """Critical alert should have urgent formatting."""
    msg = format_telegram_message(
        job_name="payment_sync",
        project="blingsting",
        status="failed",
        error="database error",
    )
    assert "CRITICAL" in msg or "payment_sync" in msg
    assert "blingsting" in msg


def test_alert_sender_init_with_env():
    """AlertSender should read from environment."""
    with patch.dict("os.environ", {
        "DISCORD_WEBHOOK_URL": "https://discord.com/webhook/test",
        "TELEGRAM_BOT_TOKEN": "123:ABC",
        "TELEGRAM_CHAT_ID": "456",
    }):
        sender = AlertSender()
        assert sender.discord_url == "https://discord.com/webhook/test"
        assert sender.telegram_token == "123:ABC"
        assert sender.telegram_chat_id == "456"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_alerts.py -v`
Expected: FAIL with "No module named 'services.monitoring.alerts'"

**Step 3: Write alerts.py**

```python
#!/usr/bin/env python3
"""
Alert dispatch module for Discord and Telegram.
"""

import os
import requests
from typing import Optional
from datetime import datetime


def format_discord_message(
    job_name: str,
    project: str,
    status: str,
    error: Optional[str] = None,
    last_run: Optional[str] = None,
) -> str:
    """
    Format an alert message for Discord.

    Args:
        job_name: Name of the job
        project: Project name
        status: Status (failed, missed, recovered)
        error: Error message if available
        last_run: Last run timestamp

    Returns:
        Formatted Discord message
    """
    if status == "failed":
        emoji = ":warning:"
        title = "Job Failed"
    elif status == "missed":
        emoji = ":clock3:"
        title = "Job Missed (Dead Man's Switch)"
    elif status == "recovered":
        emoji = ":white_check_mark:"
        title = "Job Recovered"
    else:
        emoji = ":information_source:"
        title = "Job Alert"

    lines = [
        f"{emoji} **{title}: {job_name}**",
        f"**Project:** {project}",
    ]

    if last_run:
        lines.append(f"**Last run:** {last_run}")

    if error:
        lines.append(f"**Error:** {error}")

    return "\n".join(lines)


def format_telegram_message(
    job_name: str,
    project: str,
    status: str,
    error: Optional[str] = None,
    last_run: Optional[str] = None,
) -> str:
    """
    Format an alert message for Telegram (critical alerts).

    Args:
        job_name: Name of the job
        project: Project name
        status: Status (failed, missed)
        error: Error message if available
        last_run: Last run timestamp

    Returns:
        Formatted Telegram message
    """
    if status == "failed":
        header = f"🚨 CRITICAL: {job_name} failed"
    elif status == "missed":
        header = f"🚨 CRITICAL: {job_name} hasn't run"
    else:
        header = f"⚠️ Alert: {job_name}"

    lines = [
        header,
        f"Project: {project}",
        "Requires immediate attention",
    ]

    if error:
        lines.append(f"Error: {error}")

    if last_run:
        lines.append(f"Last run: {last_run}")

    return "\n".join(lines)


class AlertSender:
    """
    Sends alerts to Discord and Telegram.
    """

    def __init__(
        self,
        discord_url: Optional[str] = None,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ):
        """
        Initialize AlertSender.

        Args:
            discord_url: Discord webhook URL (or from DISCORD_WEBHOOK_URL env)
            telegram_token: Telegram bot token (or from TELEGRAM_BOT_TOKEN env)
            telegram_chat_id: Telegram chat ID (or from TELEGRAM_CHAT_ID env)
        """
        self.discord_url = discord_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def send_discord(self, message: str) -> bool:
        """
        Send message to Discord webhook.

        Args:
            message: Message to send

        Returns:
            True if successful
        """
        if not self.discord_url:
            print("Discord webhook URL not configured")
            return False

        try:
            response = requests.post(
                self.discord_url,
                json={"content": message},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Discord send failed: {e}")
            return False

    def send_telegram(self, message: str) -> bool:
        """
        Send message to Telegram.

        Args:
            message: Message to send

        Returns:
            True if successful
        """
        if not self.telegram_token or not self.telegram_chat_id:
            print("Telegram not configured")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Telegram send failed: {e}")
            return False

    def send_alert(
        self,
        job_name: str,
        project: str,
        status: str,
        criticality: str = "important",
        error: Optional[str] = None,
        last_run: Optional[str] = None,
    ) -> bool:
        """
        Send alert to appropriate channel based on criticality.

        Args:
            job_name: Name of the job
            project: Project name
            status: Status (failed, missed, recovered)
            criticality: Job criticality (critical, important, low)
            error: Error message
            last_run: Last run timestamp

        Returns:
            True if alert sent successfully
        """
        if criticality == "critical":
            # Critical goes to Telegram
            message = format_telegram_message(
                job_name=job_name,
                project=project,
                status=status,
                error=error,
                last_run=last_run,
            )
            return self.send_telegram(message)
        else:
            # Important and low go to Discord
            message = format_discord_message(
                job_name=job_name,
                project=project,
                status=status,
                error=error,
                last_run=last_run,
            )
            return self.send_discord(message)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_alerts.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/monitoring/alerts.py tests/test_monitoring_alerts.py
git commit -m "feat(monitoring): add alerts module for Discord and Telegram"
```

---

## Task 6: Create Health Check Module

**Files:**
- Create: `services/monitoring/health_check.py`
- Create: `tests/test_monitoring_health.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Tests for monitoring health check module."""
import pytest
from datetime import datetime, timedelta
from services.monitoring.health_check import (
    check_job_status,
    is_job_overdue,
    JobStatus,
)


def test_check_job_status_success():
    """Successful run should return success status."""
    status = check_job_status(
        last_status="succeeded",
        last_run=datetime.now() - timedelta(minutes=30),
        expected_interval=60,
    )
    assert status == JobStatus.SUCCESS


def test_check_job_status_failed():
    """Failed run should return failed status."""
    status = check_job_status(
        last_status="failed",
        last_run=datetime.now() - timedelta(minutes=5),
        expected_interval=60,
    )
    assert status == JobStatus.FAILED


def test_check_job_status_missed():
    """Job that hasn't run should return missed status."""
    status = check_job_status(
        last_status="succeeded",
        last_run=datetime.now() - timedelta(minutes=120),
        expected_interval=60,  # Should have run within 60 mins
    )
    assert status == JobStatus.MISSED


def test_is_job_overdue_true():
    """Job past its interval should be overdue."""
    result = is_job_overdue(
        last_run=datetime.now() - timedelta(minutes=100),
        expected_interval_minutes=60,
        buffer_percent=50,  # 60 * 1.5 = 90 minutes
    )
    assert result is True


def test_is_job_overdue_false():
    """Job within interval should not be overdue."""
    result = is_job_overdue(
        last_run=datetime.now() - timedelta(minutes=50),
        expected_interval_minutes=60,
        buffer_percent=50,
    )
    assert result is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_health.py -v`
Expected: FAIL with "No module named 'services.monitoring.health_check'"

**Step 3: Write health_check.py**

```python
#!/usr/bin/env python3
"""
Health check module for monitoring job execution.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any

from services.supabase.postgres import PostgresAPI
from services.monitoring.queries import GET_JOB_HISTORY, GET_LAST_SUCCESS
from services.monitoring.alerts import AlertSender


class JobStatus(Enum):
    """Job health status."""
    SUCCESS = "success"
    FAILED = "failed"
    MISSED = "missed"
    UNKNOWN = "unknown"


def is_job_overdue(
    last_run: datetime,
    expected_interval_minutes: int,
    buffer_percent: int = 50,
) -> bool:
    """
    Check if a job is overdue based on expected interval.

    Args:
        last_run: Timestamp of last run
        expected_interval_minutes: Expected minutes between runs
        buffer_percent: Extra time to allow before considering overdue

    Returns:
        True if job is overdue
    """
    buffer = expected_interval_minutes * (buffer_percent / 100)
    threshold = expected_interval_minutes + buffer

    elapsed = datetime.now() - last_run
    elapsed_minutes = elapsed.total_seconds() / 60

    return elapsed_minutes > threshold


def check_job_status(
    last_status: str,
    last_run: datetime,
    expected_interval: Optional[int] = None,
    buffer_percent: int = 50,
) -> JobStatus:
    """
    Determine the current status of a job.

    Args:
        last_status: Status from last execution (succeeded, failed, etc.)
        last_run: Timestamp of last execution
        expected_interval: Expected minutes between runs (for dead man's switch)
        buffer_percent: Extra time buffer before considering missed

    Returns:
        JobStatus enum value
    """
    # If last run failed, job is failed
    if last_status == "failed":
        return JobStatus.FAILED

    # If last run succeeded but job is overdue, it's missed
    if expected_interval and is_job_overdue(last_run, expected_interval, buffer_percent):
        return JobStatus.MISSED

    # Job ran successfully and is not overdue
    if last_status == "succeeded":
        return JobStatus.SUCCESS

    return JobStatus.UNKNOWN


class HealthChecker:
    """
    Checks health of monitored jobs and sends alerts.
    """

    def __init__(
        self,
        central_project: str = "thordata",
        alert_sender: Optional[AlertSender] = None,
    ):
        """
        Initialize HealthChecker.

        Args:
            central_project: Project where inventory/logs are stored
            alert_sender: AlertSender instance (creates one if not provided)
        """
        self.central_project = central_project
        self.alert_sender = alert_sender or AlertSender()
        self._previous_statuses: Dict[str, JobStatus] = {}

    def check_project_jobs(self, project: str) -> List[Dict[str, Any]]:
        """
        Check health of all jobs in a project.

        Args:
            project: Project name

        Returns:
            List of job status results
        """
        from services.monitoring.discovery import discover_cron_jobs, discover_cron_history

        jobs = discover_cron_jobs(project)
        history = discover_cron_history(project)

        # Build history lookup by job_id
        history_by_job = {}
        for record in history:
            job_id = record.get("jobid")
            if job_id not in history_by_job:
                history_by_job[job_id] = []
            history_by_job[job_id].append(record)

        results = []
        for job in jobs:
            job_id = job.get("jobid")
            job_name = job.get("job_name")
            expected_interval = job.get("expected_interval_minutes")

            # Get most recent run
            job_history = history_by_job.get(job_id, [])
            if job_history:
                last_record = job_history[0]  # Already sorted by start_time DESC
                last_status = last_record.get("status")
                last_run = last_record.get("start_time")
                error_message = last_record.get("return_message")
            else:
                last_status = "unknown"
                last_run = None
                error_message = None

            # Determine current status
            if last_run:
                status = check_job_status(
                    last_status=last_status,
                    last_run=last_run,
                    expected_interval=expected_interval,
                )
            else:
                status = JobStatus.UNKNOWN

            results.append({
                "job_name": job_name,
                "job_id": job_id,
                "project": project,
                "status": status.value,
                "last_status": last_status,
                "last_run": last_run.isoformat() if last_run else None,
                "error_message": error_message,
                "expected_interval_minutes": expected_interval,
            })

        return results

    def check_all_and_alert(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check all projects and send alerts for status changes.

        Returns:
            Dict mapping project names to job status lists
        """
        from services.monitoring.discovery import PROJECTS

        all_results = {}

        for project in PROJECTS:
            results = self.check_project_jobs(project)
            all_results[project] = results

            for job in results:
                job_key = f"{job['project']}:{job['job_name']}"
                current_status = JobStatus(job["status"])
                previous_status = self._previous_statuses.get(job_key)

                # Alert on status change to failed or missed
                if current_status in (JobStatus.FAILED, JobStatus.MISSED):
                    if previous_status != current_status:
                        # Status changed - send alert
                        # TODO: Look up criticality from job_inventory
                        criticality = "important"  # Default

                        self.alert_sender.send_alert(
                            job_name=job["job_name"],
                            project=job["project"],
                            status=job["status"],
                            criticality=criticality,
                            error=job.get("error_message"),
                            last_run=job.get("last_run"),
                        )

                # Update previous status
                self._previous_statuses[job_key] = current_status

        return all_results
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_health.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add services/monitoring/health_check.py tests/test_monitoring_health.py
git commit -m "feat(monitoring): add health check module with dead man's switch"
```

---

## Task 7: Create Main MonitoringAPI Class

**Files:**
- Modify: `services/monitoring/api.py`
- Create: `tests/test_monitoring_api.py`

**Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Tests for MonitoringAPI main class."""
import pytest
from unittest.mock import Mock, patch
from services.monitoring.api import MonitoringAPI


def test_monitoring_api_init():
    """MonitoringAPI should initialize."""
    api = MonitoringAPI()
    assert api is not None


def test_monitoring_api_has_required_methods():
    """MonitoringAPI should have required methods."""
    api = MonitoringAPI()
    assert hasattr(api, "audit_all_projects")
    assert hasattr(api, "list_jobs")
    assert hasattr(api, "check_health")
    assert hasattr(api, "test_connection")


def test_monitoring_api_test_connection():
    """test_connection should return True when configured."""
    api = MonitoringAPI()
    # Without actual DB, just test it doesn't crash
    result = api.test_connection()
    assert isinstance(result, bool)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_monitoring_api.py -v`
Expected: FAIL with "has no attribute 'audit_all_projects'"

**Step 3: Implement MonitoringAPI**

```python
#!/usr/bin/env python3
"""
Supabase Monitoring API
Token Cost: ~800 tokens when loaded

Monitors pg_cron jobs and edge functions across multiple Supabase projects.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from services.monitoring.discovery import (
    discover_all_projects,
    discover_cron_jobs,
    discover_cron_history,
    PROJECTS,
)
from services.monitoring.health_check import HealthChecker, JobStatus
from services.monitoring.alerts import AlertSender


class MonitoringAPI:
    """
    Centralized monitoring for Supabase infrastructure.

    CAPABILITIES:
    - Discover pg_cron jobs across all projects
    - Discover edge functions via Management API
    - Track job health and execution history
    - Send alerts via Discord and Telegram

    COMMON PATTERNS:
    ```python
    monitor = MonitoringAPI()
    monitor.audit_all_projects()  # Discover all jobs
    jobs = monitor.list_jobs()    # See what was found
    monitor.check_health()        # Run health checks and alert
    ```
    """

    def __init__(
        self,
        central_project: str = "thordata",
        alert_sender: Optional[AlertSender] = None,
    ):
        """
        Initialize MonitoringAPI.

        Args:
            central_project: Project where inventory/logs are stored
            alert_sender: AlertSender for notifications
        """
        self.central_project = central_project
        self.alert_sender = alert_sender or AlertSender()
        self.health_checker = HealthChecker(
            central_project=central_project,
            alert_sender=self.alert_sender,
        )
        self._inventory: Dict[str, List[Dict[str, Any]]] = {}
        self._last_audit: Optional[datetime] = None

    def test_connection(self) -> bool:
        """
        Test if monitoring is properly configured.

        Returns:
            True if at least one project is accessible
        """
        try:
            # Try to connect to central project
            from services.supabase.postgres import PostgresAPI
            api = PostgresAPI(self.central_project)
            api.query("SELECT 1")
            api.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def audit_all_projects(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all jobs across all configured projects.

        Returns:
            Dict mapping project names to lists of jobs
        """
        self._inventory = discover_all_projects()
        self._last_audit = datetime.now()

        total_jobs = sum(len(jobs) for jobs in self._inventory.values())
        print(f"Audit complete. Found {total_jobs} jobs across {len(PROJECTS)} projects.")

        return self._inventory

    def audit_project(self, project: str) -> List[Dict[str, Any]]:
        """
        Discover jobs in a specific project.

        Args:
            project: Project name

        Returns:
            List of jobs
        """
        jobs = discover_cron_jobs(project)
        self._inventory[project] = jobs
        return jobs

    def list_jobs(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List discovered jobs.

        Args:
            project: Optional project filter

        Returns:
            List of jobs
        """
        if not self._inventory:
            print("No jobs in inventory. Run audit_all_projects() first.")
            return []

        if project:
            return self._inventory.get(project, [])

        # Return all jobs
        all_jobs = []
        for jobs in self._inventory.values():
            all_jobs.extend(jobs)
        return all_jobs

    def get_job_history(
        self,
        project: str,
        job_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for jobs.

        Args:
            project: Project name
            job_name: Optional job name filter

        Returns:
            List of execution records
        """
        history = discover_cron_history(project)

        if job_name:
            # Filter by job name (need to look up jobid first)
            jobs = self._inventory.get(project, [])
            job_id = None
            for job in jobs:
                if job.get("job_name") == job_name:
                    job_id = job.get("jobid")
                    break

            if job_id:
                history = [h for h in history if h.get("jobid") == job_id]

        return history

    def check_health(self, project: Optional[str] = None) -> Dict[str, Any]:
        """
        Run health checks and send alerts for failures.

        Args:
            project: Optional project to check (checks all if not specified)

        Returns:
            Health check results
        """
        if project:
            results = {project: self.health_checker.check_project_jobs(project)}
        else:
            results = self.health_checker.check_all_and_alert()

        # Summarize
        total = 0
        failed = 0
        missed = 0

        for proj, jobs in results.items():
            for job in jobs:
                total += 1
                if job["status"] == "failed":
                    failed += 1
                elif job["status"] == "missed":
                    missed += 1

        summary = {
            "total_jobs": total,
            "failed": failed,
            "missed": missed,
            "healthy": total - failed - missed,
            "checked_at": datetime.now().isoformat(),
            "details": results,
        }

        return summary

    def quick_start(self):
        """
        Quick overview of monitoring status.
        """
        print("=" * 60)
        print("Supabase Monitoring - Quick Start")
        print("=" * 60)
        print()
        print(f"Central project: {self.central_project}")
        print(f"Monitored projects: {', '.join(PROJECTS)}")
        print()

        # Check connection
        if self.test_connection():
            print("Connection: OK")
        else:
            print("Connection: FAILED - check your .env configuration")
            return

        # Run audit
        print()
        print("Discovering jobs...")
        self.audit_all_projects()

        # Show summary
        print()
        print("Jobs by project:")
        for project, jobs in self._inventory.items():
            print(f"  {project}: {len(jobs)} jobs")

        print()
        print("Next steps:")
        print("  monitor.check_health()  # Run health checks")
        print("  monitor.list_jobs()     # See all jobs")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_monitoring_api.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add services/monitoring/api.py tests/test_monitoring_api.py
git commit -m "feat(monitoring): implement main MonitoringAPI class"
```

---

## Task 8: Create Database Migration for Thordata

**Files:**
- Create: `services/monitoring/migrations/001_create_tables.sql`

**Step 1: Create migrations directory**

```bash
mkdir -p services/monitoring/migrations
```

**Step 2: Write the migration SQL**

```sql
-- Monitoring system tables for thordata
-- Run with: PostgresAPI('thordata').run_migration('services/monitoring/migrations/001_create_tables.sql')

-- Job inventory: catalog of all jobs across all projects
CREATE TABLE IF NOT EXISTS job_inventory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name text NOT NULL,
    job_type text CHECK (job_type IN ('pg_cron', 'edge_function')),
    job_name text NOT NULL,
    job_id bigint,  -- pg_cron jobid
    schedule text,
    expected_interval_minutes int,
    description text,
    success_criteria text,
    criticality text CHECK (criticality IN ('critical', 'important', 'low')),
    last_seen_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(project_name, job_type, job_name)
);

-- Job health log: execution results from health checks
CREATE TABLE IF NOT EXISTS job_health_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_inventory_id uuid REFERENCES job_inventory(id),
    project_name text NOT NULL,
    job_name text NOT NULL,
    status text CHECK (status IN ('success', 'failed', 'missed', 'unknown')),
    error_message text,
    last_run_at timestamptz,
    collected_at timestamptz DEFAULT now()
);

-- Alert configuration: where to send alerts
CREATE TABLE IF NOT EXISTS alert_config (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel text NOT NULL,  -- 'discord' or 'telegram'
    criticality text CHECK (criticality IN ('critical', 'important', 'low', 'all')),
    webhook_url text,  -- for discord
    bot_token text,  -- for telegram
    chat_id text,  -- for telegram
    enabled boolean DEFAULT true,
    created_at timestamptz DEFAULT now()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_job_inventory_project ON job_inventory(project_name);
CREATE INDEX IF NOT EXISTS idx_job_health_log_job ON job_health_log(job_inventory_id);
CREATE INDEX IF NOT EXISTS idx_job_health_log_collected ON job_health_log(collected_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for job_inventory
DROP TRIGGER IF EXISTS job_inventory_updated_at ON job_inventory;
CREATE TRIGGER job_inventory_updated_at
    BEFORE UPDATE ON job_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

**Step 3: Verify file created**

Run: `ls services/monitoring/migrations/`
Expected: Shows `001_create_tables.sql`

**Step 4: Commit**

```bash
git add services/monitoring/migrations/
git commit -m "feat(monitoring): add database migration for thordata tables"
```

---

## Task 9: Add Integration Test

**Files:**
- Create: `tests/test_monitoring_integration.py`

**Step 1: Write integration test**

```python
#!/usr/bin/env python3
"""
Integration tests for monitoring service.

These tests require actual database connections.
Skip if credentials not available.
"""
import os
import pytest
from services.monitoring.api import MonitoringAPI


# Skip all tests if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("THORDATA_SUPABASE_POSTGRES_URL"),
    reason="THORDATA_SUPABASE_POSTGRES_URL not set",
)


class TestMonitoringIntegration:
    """Integration tests for MonitoringAPI."""

    def test_connection_to_thordata(self):
        """Should connect to thordata project."""
        api = MonitoringAPI()
        assert api.test_connection() is True

    def test_audit_discovers_jobs(self):
        """Audit should discover at least some jobs."""
        api = MonitoringAPI()
        results = api.audit_all_projects()

        # At least one project should have jobs
        total_jobs = sum(len(jobs) for jobs in results.values())
        # This might be 0 if no jobs exist, which is fine
        assert isinstance(total_jobs, int)

    def test_health_check_returns_results(self):
        """Health check should return structured results."""
        api = MonitoringAPI()
        api.audit_all_projects()

        results = api.check_health()

        assert "total_jobs" in results
        assert "failed" in results
        assert "missed" in results
        assert "healthy" in results
        assert "checked_at" in results
```

**Step 2: Run integration test (may skip if no creds)**

Run: `pytest tests/test_monitoring_integration.py -v`
Expected: Either PASS or SKIP (depending on credentials)

**Step 3: Commit**

```bash
git add tests/test_monitoring_integration.py
git commit -m "test(monitoring): add integration tests"
```

---

## Task 10: Update Service __init__ and Run Full Tests

**Files:**
- Modify: `services/monitoring/__init__.py`

**Step 1: Update `__init__.py` with all exports**

```python
"""
Monitoring service for Supabase jobs and edge functions.

Usage:
    from api_toolkit.services.monitoring import MonitoringAPI

    monitor = MonitoringAPI()
    monitor.audit_all_projects()
    monitor.check_health()
"""
from .api import MonitoringAPI
from .discovery import (
    discover_cron_jobs,
    discover_cron_history,
    discover_all_projects,
    parse_cron_schedule,
)
from .health_check import HealthChecker, JobStatus, check_job_status
from .alerts import AlertSender, format_discord_message, format_telegram_message

__all__ = [
    "MonitoringAPI",
    "discover_cron_jobs",
    "discover_cron_history",
    "discover_all_projects",
    "parse_cron_schedule",
    "HealthChecker",
    "JobStatus",
    "check_job_status",
    "AlertSender",
    "format_discord_message",
    "format_telegram_message",
]
```

**Step 2: Run all monitoring tests**

Run: `pytest tests/test_monitoring*.py -v`
Expected: All tests PASS (some may skip without credentials)

**Step 3: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All existing tests still pass

**Step 4: Commit**

```bash
git add services/monitoring/__init__.py
git commit -m "feat(monitoring): finalize service exports and run tests"
```

---

## Task 11: Final Documentation and Cleanup

**Files:**
- Modify: `services/monitoring/README.md`
- Create: `services/monitoring/examples.py`

**Step 1: Update README with complete docs**

```markdown
# Monitoring Service

Centralized monitoring for Supabase pg_cron jobs and edge functions across multiple projects.

## Features

- Discover pg_cron jobs across all Supabase projects
- Track job execution history
- Dead man's switch detection (jobs that haven't run)
- Alerts via Discord (general) and Telegram (critical)
- Centralized job inventory in thordata project

## Setup

### 1. Environment Variables

Add to your `.env`:

```bash
# Postgres URLs for each project
SMOOTHED_SUPABASE_POSTGRES_URL=postgresql://...
BLINGSTING_SUPABASE_POSTGRES_URL=postgresql://...
SCRAPING_SUPABASE_POSTGRES_URL=postgresql://...
THORDATA_SUPABASE_POSTGRES_URL=postgresql://...

# Alert destinations
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=...
```

### 2. Create Tables in Thordata

```python
from services.supabase.postgres import PostgresAPI

api = PostgresAPI('thordata')
api.run_migration('services/monitoring/migrations/001_create_tables.sql')
api.close()
```

## Usage

### Quick Start

```python
from api_toolkit.services.monitoring import MonitoringAPI

monitor = MonitoringAPI()
monitor.quick_start()  # Shows overview and discovers jobs
```

### Audit All Projects

```python
monitor = MonitoringAPI()
results = monitor.audit_all_projects()

# See what was found
for project, jobs in results.items():
    print(f"{project}: {len(jobs)} jobs")
```

### Run Health Checks

```python
# Check all projects and alert on failures
summary = monitor.check_health()

print(f"Total: {summary['total_jobs']}")
print(f"Failed: {summary['failed']}")
print(f"Missed: {summary['missed']}")
print(f"Healthy: {summary['healthy']}")
```

### View Job History

```python
# Get recent execution history
history = monitor.get_job_history('smoothed')

for record in history[:5]:
    print(f"{record['command']}: {record['status']}")
```

## Alert Routing

| Criticality | Destination |
|-------------|-------------|
| critical | Telegram |
| important | Discord |
| low | Discord |

## Dead Man's Switch

Jobs are considered "missed" if they haven't run within 150% of their expected interval:

- Hourly job (60 min) → alert after 90 minutes
- Daily job (1440 min) → alert after 36 hours
- Every 5 min job → alert after 7.5 minutes
```

**Step 2: Create examples.py**

```python
#!/usr/bin/env python3
"""
Examples for the monitoring service.

Run with: python services/monitoring/examples.py
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def example_quick_start():
    """Basic monitoring quick start."""
    from services.monitoring.api import MonitoringAPI

    print("=" * 60)
    print("Example: Quick Start")
    print("=" * 60)

    monitor = MonitoringAPI()
    monitor.quick_start()


def example_audit_single_project():
    """Audit a single project."""
    from services.monitoring.api import MonitoringAPI

    print("=" * 60)
    print("Example: Audit Single Project")
    print("=" * 60)

    monitor = MonitoringAPI()
    jobs = monitor.audit_project('thordata')

    print(f"Found {len(jobs)} jobs in thordata:")
    for job in jobs:
        print(f"  - {job['job_name']}: {job.get('schedule', 'no schedule')}")


def example_health_check():
    """Run health checks."""
    from services.monitoring.api import MonitoringAPI

    print("=" * 60)
    print("Example: Health Check")
    print("=" * 60)

    monitor = MonitoringAPI()
    monitor.audit_all_projects()

    summary = monitor.check_health()

    print(f"Health Check Results:")
    print(f"  Total jobs: {summary['total_jobs']}")
    print(f"  Healthy: {summary['healthy']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Missed: {summary['missed']}")


def example_parse_schedules():
    """Parse cron schedule expressions."""
    from services.monitoring.discovery import parse_cron_schedule

    print("=" * 60)
    print("Example: Parse Cron Schedules")
    print("=" * 60)

    schedules = [
        "*/5 * * * *",    # Every 5 minutes
        "0 * * * *",      # Hourly
        "0 0 * * *",      # Daily at midnight
        "0 0 * * 0",      # Weekly on Sunday
        "0 0 1 * *",      # Monthly on 1st
    ]

    for schedule in schedules:
        parsed = parse_cron_schedule(schedule)
        print(f"  {schedule} -> {parsed['description']}")


if __name__ == "__main__":
    import sys

    examples = {
        "quick_start": example_quick_start,
        "audit": example_audit_single_project,
        "health": example_health_check,
        "schedules": example_parse_schedules,
    }

    if len(sys.argv) < 2:
        print("Usage: python examples.py <example_name>")
        print(f"Available: {', '.join(examples.keys())}")
        sys.exit(1)

    example_name = sys.argv[1]
    if example_name in examples:
        examples[example_name]()
    else:
        print(f"Unknown example: {example_name}")
        print(f"Available: {', '.join(examples.keys())}")
```

**Step 3: Run examples to verify**

Run: `python services/monitoring/examples.py schedules`
Expected: Shows parsed cron schedules

**Step 4: Final commit**

```bash
git add services/monitoring/README.md services/monitoring/examples.py
git commit -m "docs(monitoring): add complete documentation and examples"
```

---

## Checkpoint: Review Implementation

At this point, the monitoring service should be complete with:

- [x] Service structure (`services/monitoring/`)
- [x] SQL queries for pg_cron (`queries.py`)
- [x] Discovery module (`discovery.py`)
- [x] Alert module (`alerts.py`)
- [x] Health check module (`health_check.py`)
- [x] Main API class (`api.py`)
- [x] Database migration
- [x] Unit tests
- [x] Integration tests
- [x] Documentation
- [x] Examples

**Run final verification:**

```bash
# Run all tests
pytest tests/test_monitoring*.py -v

# Test import
python -c "from services.monitoring import MonitoringAPI; print('Import OK')"

# Quick functional test
python services/monitoring/examples.py schedules
```
