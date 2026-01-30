# Supabase Monitoring Audit System

## Problem

Projects are set up and running, but when they break there's no notification. Failures are discovered manually and retroactively.

## Goal

Create visibility into all running Supabase jobs and edge functions across projects, then build alerting on critical paths.

## Phase 1: Inventory Audit

### Data to collect

**From pg_cron (query programmatically):**
- Job name
- Schedule (cron expression)
- Command/function being called
- Active status

**From pg_cron.job_run_details:**
- Recent execution history
- Success/failure status
- Error messages

**From Supabase Management API:**
- Deployed edge functions per project
- (Invocation logs require dashboard or log drain setup)

**Manual annotation required:**
- Client/project name
- What the job does (plain english)
- Success criteria beyond "didn't throw"
- Criticality tier (critical / important / low)

### Output

A `job_inventory` table (can live in a central Supabase project) with schema:

```sql
create table job_inventory (
  id uuid primary key default gen_random_uuid(),
  project_id text not null,
  project_name text,
  job_type text check (job_type in ('pg_cron', 'edge_function', 'webhook')),
  job_name text not null,
  schedule text,
  description text,
  success_criteria text,
  criticality text check (criticality in ('critical', 'important', 'low')),
  alert_channel text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## Phase 2: Health Checks & Alerting

### For pg_cron jobs:
- Query `pg_cron.job_run_details` on a schedule
- Alert if last run status != 'succeeded'
- Alert if job hasn't run within expected window (dead man's switch)

### For edge functions:
- Options:
  - Log drain to central location + alert on error rates
  - Wrapper function that logs to a `function_executions` table
  - Health check endpoint per function that gets pinged

### Alert destinations:
- Slack webhook
- Discord webhook  
- Email via Resend/Postmark
- SMS for critical (Twilio)

---

## Phase 3: Error Analysis (Future - Langfuse territory)

Once alerting is in place, then set up trace collection for deeper pattern analysis. Not needed until Phase 1 and 2 are solid.

---

## Implementation Steps

1. [ ] Write query to pull pg_cron jobs from a single project
2. [ ] Test against one Supabase project
3. [ ] Create `job_inventory` table in central project
4. [ ] Script to pull from multiple projects and consolidate
5. [ ] Manual pass to annotate all jobs
6. [ ] Build alerting function that checks job health
7. [ ] Set up alert destinations
8. [ ] Create dead man's switch logic for scheduled jobs

---

## Supabase Projects to Audit

<!-- Add your project IDs/names here -->
- 
- 
- 

---

## Notes

- All infrastructure is Supabase edge functions and pg_cron (no n8n or external crons)
- Prefer building alerting within Supabase itself where possible