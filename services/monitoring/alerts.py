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
        header = f"CRITICAL: {job_name} failed"
    elif status == "missed":
        header = f"CRITICAL: {job_name} hasn't run"
    else:
        header = f"Alert: {job_name}"

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
