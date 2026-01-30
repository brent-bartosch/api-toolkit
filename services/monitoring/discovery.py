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
