# Project-Specific Configuration Guide

## Problem This Solves

Different projects need different services from the API Toolkit. Previously, Claude Code had no way to know which services were relevant for a specific project, leading to:
- Confusion about which services to use
- Attempts to configure unnecessary services
- Loss of context between conversation restarts
- No tracking of project-specific patterns

## Solution: `.api-toolkit-config.md` per Project

Each project that uses the API Toolkit should have its own **`.api-toolkit-config.md`** file that:
1. ✅ **Declares which services are active** for this project
2. 📝 **Documents project-specific patterns** and common queries
3. 🔄 **Persists across conversation restarts** (Claude Code reads it each time)
4. 📊 **Tracks progress** on integrations and tasks
5. 🎯 **Provides context** about what the project does

---

## Quick Start

### For New Projects

When installing the toolkit, you'll be prompted to configure services:

```bash
cd /path/to/your/project
/path/to/api-toolkit/install.sh
# Answer "y" to create project configuration
# Select which services you need
```

### For Existing Installations

Add configuration to a project that already has the toolkit:

```bash
cd /path/to/your/project
/path/to/api-toolkit/init-project.sh
```

---

## The Configuration File

### Location
- **File**: `.api-toolkit-config.md` (in project root)
- **Visibility**: Should be committed to git (helps team members)
- **Format**: Markdown (human and LLM readable)

### Structure

```markdown
# API Toolkit Configuration for [Your Project]

## Active Services for This Project

### Supabase
- **Status**: ✅ Active
- **Project(s) Used**: smoothed
- **Tables/Features**:
  - [x] leads - Main lead tracking
  - [x] brands - Brand information
- **Notes**: Using for lead generation pipeline

### Metabase
- **Status**: ⚪ Not Configured
```

### Service Status Indicators

| Status | Meaning | When to Use |
|--------|---------|-------------|
| ⚪ **Not Configured** | Service not needed for this project | Default for unused services |
| 🟡 **Configured** | Service set up but not fully tested | Initial configuration phase |
| ✅ **Active** | Service tested and working | Production use |

---

## How Claude Code Uses This

### On Conversation Start

1. Claude Code opens your project
2. Reads `.api-toolkit-config.md` (if present)
3. Understands which services are available
4. Uses only the active services
5. References project-specific patterns documented in the file

### During Work

- **Before using a service**: Checks if it's marked as ✅ Active
- **When documenting patterns**: Updates the config file with new patterns
- **On completing tasks**: Updates progress tracking section
- **On errors**: Adds troubleshooting notes

### On Conversation Restart

- Reads updated config file
- Sees what was completed previously
- Continues from where you left off
- No need to re-explain which services are active

---

## Workflow: Service Lifecycle

### 1. Initial Setup (⚪ → 🟡)

```bash
# Install toolkit
/path/to/api-toolkit/install.sh

# Configure project (select Supabase)
# Creates .api-toolkit-config.md with Supabase marked as 🟡 Configured
```

Edit `.api-toolkit-config.md`:
```markdown
### Supabase
- **Status**: 🟡 Configured
- **Project(s) Used**: smoothed
- **Environment Variables Required**:
  - [x] SUPABASE_URL
  - [x] SUPABASE_SERVICE_ROLE_KEY
```

### 2. Testing & Activation (🟡 → ✅)

Tell Claude Code:
> "Test the Supabase connection and mark it as active in the config"

Claude will:
```python
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
if api.test_connection():
    # Updates config file
    # Changes status to ✅ Active
```

### 3. Documentation & Iteration

As you work, Claude Code updates the config with:
- Common query patterns you use frequently
- Integration points between services
- Troubleshooting notes for issues encountered
- Progress on tasks and features

### 4. Adding New Services

Later, you need Metabase:
```bash
# Edit .api-toolkit-config.md manually or run:
/path/to/api-toolkit/init-project.sh
```

Tell Claude Code:
> "I need to add Metabase. Update the config and test the connection."

---

## Example: Multi-Project Setup

### Project 1: Lead Generation Tool

**`.api-toolkit-config.md`:**
```markdown
## Active Services for This Project

### Supabase
- **Status**: ✅ Active
- **Project(s) Used**: smoothed
- **Common Pattern**:
  ```python
  # Get hot leads for outreach
  api = SupabaseAPI('project1')
  leads = api.query('leads',
      filters={'score': 'gte.80', 'status': 'eq.new'},
      limit=50
  )
  ```

### Smartlead
- **Status**: ✅ Active
- **Usage**: Push leads to email campaigns

### Metabase
- **Status**: ⚪ Not Configured

### Others
- All other services: ⚪ Not Configured
```

### Project 2: E-commerce Dashboard

**`.api-toolkit-config.md`:**
```markdown
## Active Services for This Project

### Supabase
- **Status**: ✅ Active
- **Project(s) Used**: blingsting
- **Tables**: customers, orders, products

### Shopify
- **Status**: ✅ Active
- **Usage**: Sync orders and inventory

### Metabase
- **Status**: ✅ Active
- **Dashboards**:
  - Dashboard 42: Sales Overview
  - Dashboard 89: Inventory Status

### Others
- Smartlead: ⚪ Not Configured (not needed)
- BrightData: ⚪ Not Configured (not needed)
```

---

## Best Practices

### 1. Update as You Go
```markdown
# ✅ GOOD - Keep it current
After implementing feature → Update config with pattern
After fixing bug → Add troubleshooting note
After completing task → Check it off

# ❌ BAD - Let it get stale
Config says "Not Configured" but you've been using it
Config shows old patterns that no longer work
```

### 2. Be Specific
```markdown
# ✅ GOOD - Actionable details
### Supabase
- **Tables**: leads (for new prospects), brands (company info)
- **Pattern**: Always filter by score >= 80 for quality leads

# ❌ BAD - Too vague
### Supabase
- **Status**: Active
- Uses some tables
```

### 3. Document Gotchas
```markdown
### Troubleshooting & Notes

#### Supabase Query Timeouts
- Large table queries need LIMIT
- Use pagination for exports
- Index on 'created_at' column

#### Metabase Connection
- Uses session auth (expires every 24h)
- Re-login if getting 401 errors
```

### 4. Track Integration Points
```markdown
### Integration Points
- **Supabase → Smartlead**: New leads auto-added to campaigns
- **Shopify → Supabase**: Orders synced every 15 minutes
- **Metabase**: Reads from Supabase (read-only connection)
```

---

## Commands Reference

```bash
# Create initial project config
/path/to/api-toolkit/init-project.sh

# View current config
cat .api-toolkit-config.md

# Edit config
code .api-toolkit-config.md  # or vim, nano, etc.

# Test services listed in config
python api-toolkit/toolkit.py supabase test
python api-toolkit/toolkit.py metabase test

# Check which services are active
grep "Status\*\*: ✅" .api-toolkit-config.md
```

---

## For Claude Code: Reading the Config

When you start in a new project:

```python
# 1. Check for config file
import os
config_exists = os.path.exists('.api-toolkit-config.md')

# 2. If present, read it to understand project
if config_exists:
    with open('.api-toolkit-config.md', 'r') as f:
        config = f.read()

    # 3. Extract active services
    active_services = []
    if '✅ Active' in config:
        # Parse which services are active
        # Use ONLY those services
        pass

# 4. Only use active services
# Example: If Supabase is ✅ Active, use it
# If Metabase is ⚪ Not Configured, don't try to use it
```

**Key Rule**:
- ✅ Active → Safe to use
- 🟡 Configured → May need testing
- ⚪ Not Configured → DON'T USE

---

## Benefits Summary

| Benefit | Without Config | With Config |
|---------|---------------|-------------|
| **Service Discovery** | Trial and error | Explicitly declared |
| **Context Persistence** | Lost on restart | Maintained in file |
| **Pattern Reuse** | Reinvent each time | Documented & reusable |
| **Team Collaboration** | Undocumented setup | Clear configuration |
| **Progress Tracking** | No visibility | Checkboxes & notes |

---

## Migration Guide

### Adding Config to Existing Projects

If you have projects with the toolkit but no config file:

```bash
# Navigate to each project
cd /path/to/project-with-toolkit

# Run initialization
/path/to/api-toolkit/init-project.sh

# Follow prompts to document current setup

# Commit the new config file
git add .api-toolkit-config.md
git commit -m "docs: Add API toolkit configuration"
```

---

## FAQ

**Q: Do I need a config file?**
A: Not required, but highly recommended for any serious project. Saves time and prevents confusion.

**Q: Can I have multiple config files?**
A: One per project. Each project root should have its own `.api-toolkit-config.md`.

**Q: Should I commit this to git?**
A: Yes! It helps your team (and future you) understand the project setup.

**Q: What if I need to add a service later?**
A: Edit `.api-toolkit-config.md` manually or re-run `init-project.sh`.

**Q: How do I mark a service as active?**
A: Change the status line from `⚪ Not Configured` or `🟡 Configured` to `✅ Active`.

**Q: Can Claude Code update this file?**
A: Yes! Ask Claude to document patterns or update status, and it will edit the config file.

---

*Last updated: 2025-10-02*
