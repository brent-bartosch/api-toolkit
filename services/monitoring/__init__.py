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
