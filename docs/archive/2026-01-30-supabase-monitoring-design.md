# Supabase Monitoring System Design

*Created: 2026-01-30*

## Problem

Projects are running with pg_cron jobs and edge functions, but failures go unnoticed until discovered manually. Need visibility into all running jobs across 4 Supabase projects with alerting on failures.

## Projects to Monitor

- smoothed (lead gen)
- blingsting (CRM)
- scraping (web scraping)
- thordata (central hub + monitoring infrastructure)

## Architecture

**Central Hub: thordata**

All monitoring infrastructure lives here:
- `job_inventory` table - catalog of all jobs across all 4 projects
- `job_health_log` table - execution results collected from each project
- `check_job_health` edge function - runs on schedule, queries each project
- `send_alert` edge function - dispatches to Discord or Telegram based on criticality

**Data Flow:**
```
smoothed ──┐
blingsting ─┼──▶ thordata collects health data ──▶ alerts
scraping ──┤
thordata ──┘
```

**Access Method:**
- Uses `PostgresAPI` for direct Postgres access to query `pg_cron` tables
- Each project needs its `SUPABASE_POSTGRES_URL` in `.env`

## Data Model

### job_inventory

```sql
create table job_inventory (
  id uuid primary key default gen_random_uuid(),
  project_name text not null,  -- smoothed, blingsting, scraping, thordata
  job_type text check (job_type in ('pg_cron', 'edge_function')),
  job_name text not null,
  schedule text,  -- cron expression for pg_cron, null for edge functions
  description text,  -- what it does (manual annotation)
  success_criteria text,  -- how to know it worked (manual annotation)
  criticality text check (criticality in ('critical', 'important', 'low')),
  last_seen_at timestamptz,  -- updated by health check
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(project_name, job_type, job_name)
);
```

### job_health_log

```sql
create table job_health_log (
  id uuid primary key default gen_random_uuid(),
  job_inventory_id uuid references job_inventory(id),
  status text check (status in ('success', 'failed', 'missed')),
  error_message text,
  run_at timestamptz,
  collected_at timestamptz default now()
);
```

### alert_config

```sql
create table alert_config (
  id uuid primary key default gen_random_uuid(),
  channel text not null,  -- 'discord' or 'telegram'
  criticality text check (criticality in ('critical', 'important', 'low', 'all')),
  webhook_url text,  -- for discord
  bot_token text,  -- for telegram
  chat_id text,  -- for telegram
  enabled boolean default true
);
```

## Audit/Discovery Process

### Step 1: Query pg_cron from each project

```sql
SELECT
  jobname as job_name,
  schedule,
  command,
  active
FROM cron.job
ORDER BY jobname;
```

Recent execution history:

```sql
SELECT
  jobname,
  status,
  return_message,
  start_time,
  end_time
FROM cron.job_run_details
WHERE start_time > now() - interval '7 days'
ORDER BY start_time DESC;
```

### Step 2: List edge functions via Management API

```bash
curl https://api.supabase.com/v1/projects/{project_id}/functions \
  -H "Authorization: Bearer {SUPABASE_ACCESS_TOKEN}"
```

Requires Supabase access token from dashboard > Account > Access Tokens.

### Step 3: Consolidate into job_inventory

Script pulls from all 4 projects and inserts/updates rows in thordata's `job_inventory` table.

## Health Checks & Alerting

### Health Check Logic (runs every 15 minutes)

1. For each project, query `cron.job_run_details` for jobs in inventory
2. Compare last run time against expected schedule
3. Flag issues:
   - `failed` - last run status != 'succeeded'
   - `missed` - job hasn't run within expected window
4. Log to `job_health_log`
5. If status changed to failed/missed → trigger alert

### Alert Routing

| Criticality | Channel |
|-------------|---------|
| critical | Telegram |
| important | Discord |
| low | Discord |

### Dead Man's Switch

For a job scheduled `0 * * * *` (hourly), if no run in last 90 minutes → alert as `missed`. Buffer accounts for timing variance.

## Implementation in API Toolkit

**Location:** `services/monitoring/`

```
services/monitoring/
├── api.py              # MonitoringAPI class - main interface
├── discovery.py        # Functions to audit pg_cron and edge functions
├── health_check.py     # Health check logic (also deployed as edge function)
├── alerts.py           # Discord and Telegram alert senders
├── queries.py          # SQL queries for pg_cron tables
└── README.md           # Setup instructions
```

### Usage

```python
from api_toolkit.services.monitoring.api import MonitoringAPI

monitor = MonitoringAPI()

# Phase 1: Discover all jobs across projects
monitor.audit_all_projects()  # Populates job_inventory

# View what was found
jobs = monitor.list_jobs()  # Returns all discovered jobs

# Annotate a job
monitor.update_job('job-uuid',
    description="Syncs leads from Smartlead to Supabase",
    criticality="important"
)

# Phase 2: Run health check
monitor.check_health()  # Queries all projects, logs results, sends alerts
```

### Deployment

- `health_check.py` logic deployed as edge function to thordata
- pg_cron job in thordata calls it every 15 minutes

## Environment Variables Required

```bash
# Postgres URLs for direct access (pg_cron queries)
SUPABASE_POSTGRES_URL=postgresql://...    # smoothed
SUPABASE_POSTGRES_URL_2=postgresql://...  # blingsting
SUPABASE_POSTGRES_URL_3=postgresql://...  # scraping
SUPABASE_POSTGRES_URL_4=postgresql://...  # thordata

# Supabase Management API (for edge function discovery)
SUPABASE_ACCESS_TOKEN=sbp_...

# Alert destinations
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=...
```

## Implementation Phases

### Phase 1: Inventory Audit
- [ ] Add Postgres URLs for all 4 projects to .env
- [ ] Create `job_inventory` table in thordata
- [ ] Build discovery script for pg_cron jobs
- [ ] Get Supabase access token for Management API
- [ ] Build discovery for edge functions
- [ ] Run full audit across all projects
- [ ] Manual pass to annotate jobs with description/criticality

### Phase 2: Health Checks & Alerting
- [ ] Create `job_health_log` table in thordata
- [ ] Create `alert_config` table in thordata
- [ ] Set up Discord webhook
- [ ] Set up Telegram bot
- [ ] Build health check function
- [ ] Build alert dispatch function
- [ ] Deploy health check as edge function
- [ ] Set up pg_cron to run health check every 15 minutes
- [ ] Test with intentional failure

### Phase 3: Error Analysis (Future)
- Langfuse integration for deeper trace analysis
- See: `error_analysis/langfuse_integration_idea.md`
