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

- Hourly job (60 min) -> alert after 90 minutes
- Daily job (1440 min) -> alert after 36 hours
- Every 5 min job -> alert after 7.5 minutes

## API Reference

### MonitoringAPI

The main entry point for all monitoring operations.

```python
from api_toolkit.services.monitoring import MonitoringAPI

monitor = MonitoringAPI(
    central_project='thordata',  # Where inventory is stored
    alert_sender=None,           # Optional custom AlertSender
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `quick_start()` | Overview and discover jobs |
| `audit_all_projects()` | Discover jobs across all projects |
| `audit_project(project)` | Discover jobs in one project |
| `list_jobs(project=None)` | List discovered jobs |
| `get_job_history(project, job_name=None)` | Get execution history |
| `check_health(project=None)` | Run health checks and alert |
| `test_connection()` | Test database connectivity |

### Utility Functions

```python
from api_toolkit.services.monitoring import (
    parse_cron_schedule,     # Parse cron expressions
    discover_cron_jobs,      # Discover jobs in a project
    discover_cron_history,   # Get job history
    check_job_status,        # Check individual job health
)
```

## Examples

Run the examples script:

```bash
# Parse cron schedules (no database needed)
python services/monitoring/examples.py schedules

# Quick start (requires database)
python services/monitoring/examples.py quick_start

# Audit a single project
python services/monitoring/examples.py audit

# Run health check
python services/monitoring/examples.py health
```
