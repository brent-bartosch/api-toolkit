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
