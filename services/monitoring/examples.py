#!/usr/bin/env python3
"""
Examples for the monitoring service.

Run with: python services/monitoring/examples.py
"""

import os
import sys

# Add parent to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


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
    jobs = monitor.audit_project("thordata")

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
        "*/5 * * * *",  # Every 5 minutes
        "0 * * * *",  # Hourly
        "0 0 * * *",  # Daily at midnight
        "0 0 * * 0",  # Weekly on Sunday
        "0 0 1 * *",  # Monthly on 1st
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
