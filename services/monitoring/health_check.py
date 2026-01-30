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
    if expected_interval and is_job_overdue(
        last_run, expected_interval, buffer_percent
    ):
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
        from services.monitoring.discovery import (
            discover_cron_jobs,
            discover_cron_history,
        )

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

            results.append(
                {
                    "job_name": job_name,
                    "job_id": job_id,
                    "project": project,
                    "status": status.value,
                    "last_status": last_status,
                    "last_run": last_run.isoformat() if last_run else None,
                    "error_message": error_message,
                    "expected_interval_minutes": expected_interval,
                }
            )

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
