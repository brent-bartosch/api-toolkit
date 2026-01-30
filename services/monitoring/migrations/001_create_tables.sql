-- Monitoring system tables for thordata
-- Run with: PostgresAPI('thordata').run_migration('services/monitoring/migrations/001_create_tables.sql')

-- Job inventory: catalog of all jobs across all projects
CREATE TABLE IF NOT EXISTS job_inventory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name text NOT NULL,
    job_type text CHECK (job_type IN ('pg_cron', 'edge_function')),
    job_name text NOT NULL,
    job_id bigint,  -- pg_cron jobid
    schedule text,
    expected_interval_minutes int,
    description text,
    success_criteria text,
    criticality text CHECK (criticality IN ('critical', 'important', 'low')),
    last_seen_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(project_name, job_type, job_name)
);

-- Job health log: execution results from health checks
CREATE TABLE IF NOT EXISTS job_health_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job_inventory_id uuid REFERENCES job_inventory(id),
    project_name text NOT NULL,
    job_name text NOT NULL,
    status text CHECK (status IN ('success', 'failed', 'missed', 'unknown')),
    error_message text,
    last_run_at timestamptz,
    collected_at timestamptz DEFAULT now()
);

-- Alert configuration: where to send alerts
CREATE TABLE IF NOT EXISTS alert_config (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel text NOT NULL,  -- 'discord' or 'telegram'
    criticality text CHECK (criticality IN ('critical', 'important', 'low', 'all')),
    webhook_url text,  -- for discord
    bot_token text,  -- for telegram
    chat_id text,  -- for telegram
    enabled boolean DEFAULT true,
    created_at timestamptz DEFAULT now()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_job_inventory_project ON job_inventory(project_name);
CREATE INDEX IF NOT EXISTS idx_job_health_log_job ON job_health_log(job_inventory_id);
CREATE INDEX IF NOT EXISTS idx_job_health_log_collected ON job_health_log(collected_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for job_inventory
DROP TRIGGER IF EXISTS job_inventory_updated_at ON job_inventory;
CREATE TRIGGER job_inventory_updated_at
    BEFORE UPDATE ON job_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
