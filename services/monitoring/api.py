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
        print(
            f"Audit complete. Found {total_jobs} jobs across {len(PROJECTS)} projects."
        )

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
            Health check results with summary
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
