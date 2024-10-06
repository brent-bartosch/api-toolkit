# Quick Start Flowchart for Claude Code

## When Starting in ANY Project

```
┌─────────────────────────────────────────────────────────┐
│  NEW CONVERSATION STARTS IN A PROJECT                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  STEP 1: CHECK       │
          │  INSTALLATION        │
          └──────────┬───────────┘
                     │
          ls -la api-toolkit/
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌─────────┐           ┌─────────┐
    │ FOUND   │           │ NOT     │
    │ ✅      │           │ FOUND ❌│
    └────┬────┘           └────┬────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ INSTALL IT   │
         │              │ install.sh   │
         │              └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ CONFIGURE?   │
         │              │ (prompted)   │
         │              └──────┬───────┘
         │                     │
         └─────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  STEP 2: READ        │
          │  PROJECT CONFIG      │
          └──────────┬───────────┘
                     │
    cat .api-toolkit-config.md
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌─────────┐           ┌─────────┐
    │ FOUND   │           │ NOT     │
    │ ✅      │           │ FOUND ❌│
    └────┬────┘           └────┬────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ OFFER TO     │
         │              │ CREATE ONE   │
         │              └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ init-        │
         │              │ project.sh   │
         │              └──────┬───────┘
         │                     │
         └─────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  STEP 3: IDENTIFY    │
          │  ACTIVE SERVICES     │
          └──────────┬───────────┘
                     │
       Parse config for ✅ Active
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │ Active   │          │ Not      │
    │ Services │          │ Config   │
    └─────┬────┘          └─────┬────┘
          │                     │
          │ ✅ USE              │ ❌ IGNORE
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │ Supabase │          │ Metabase │
    │ Smartlead│          │ Klaviyo  │
    │ etc.     │          │ etc.     │
    └─────┬────┘          └──────────┘
          │
          ▼
    ┌──────────────────────┐
    │  STEP 4: START WORK  │
    └──────────┬───────────┘
               │
               ▼
    Use ONLY active services
    Document patterns in config
    Update progress as you work
```

---

## Decision Tree

```
START
  │
  ├─ Q: Is api-toolkit/ present?
  │   ├─ YES → Go to "Check Config"
  │   └─ NO  → Run install.sh → Go to "Check Config"
  │
  ├─ Check Config: Is .api-toolkit-config.md present?
  │   ├─ YES → Parse active services
  │   └─ NO  → Offer: init-project.sh or continue without
  │
  ├─ Parse Config: Which services are ✅ Active?
  │   ├─ Supabase ✅    → Import and use
  │   ├─ Metabase ⚪    → DO NOT USE
  │   ├─ Smartlead ✅   → Import and use
  │   └─ Others ⚪      → DO NOT USE
  │
  └─ Work: Use ONLY active services
      ├─ Document patterns → Update config
      ├─ Complete tasks → Check off in config
      └─ Add services → Change ⚪ to 🟡 to ✅
```

---

## Command Cheat Sheet

### Step 1: Installation Check
```bash
# Automated check (recommended)
bash /path/to/api-toolkit/check-installation.sh

# Manual check
ls -la api-toolkit/

# If not installed
/path/to/api-toolkit/install.sh
```

### Step 2: Config Check
```bash
# Check for config
cat .api-toolkit-config.md

# If not present
/path/to/api-toolkit/init-project.sh
```

### Step 3: Identify Active Services
```bash
# Show all active services
grep "Status\*\*: ✅" .api-toolkit-config.md

# Or read the whole config
cat .api-toolkit-config.md | less
```

### Step 4: Use Active Services
```python
# Example: If Supabase is ✅ Active
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
api.quick_start()

# Example: If Metabase is ✅ Active
from api_toolkit.services.metabase.api import MetabaseAPI
api = MetabaseAPI()
```

---

## Status Indicators Guide

### ⚪ Not Configured
- **Meaning**: Service not needed for this project
- **Action**: DO NOT attempt to use
- **Example**: Klaviyo in a web scraping project

### 🟡 Configured
- **Meaning**: Credentials added, not yet tested
- **Action**: Test before using
- **Example**: Just added Metabase keys to .env

### ✅ Active
- **Meaning**: Tested and working
- **Action**: Safe to use
- **Example**: Supabase connection verified

---

## Common Scenarios

### Scenario A: Brand New Project
```bash
cd /path/to/new-project
/path/to/api-toolkit/install.sh
# → Creates api-toolkit/
# → Prompts for project config
# → Creates .api-toolkit-config.md
# → Ready to use!
```

### Scenario B: Existing Project, New Conversation
```bash
# Claude Code starts
ls -la api-toolkit/           # ✅ Found
cat .api-toolkit-config.md    # ✅ Found
# Parse: Supabase ✅, Smartlead ✅, others ⚪
# USE: Only Supabase and Smartlead
```

### Scenario C: Need to Add Service
```bash
# Currently using: Supabase ✅
# Need to add: Metabase

# Edit config
code .api-toolkit-config.md
# Change Metabase from ⚪ to 🟡
# Add credentials to .env
# Test connection
python api-toolkit/toolkit.py metabase test
# If successful, change 🟡 to ✅
```

### Scenario D: No Config File
```bash
# Project has toolkit but no config
ls -la api-toolkit/           # ✅ Found
cat .api-toolkit-config.md    # ❌ Not found

# Create config
/path/to/api-toolkit/init-project.sh
# Or continue without config (not recommended)
```

---

## Red Flags 🚩

### DO NOT:
- ❌ Install toolkit if `api-toolkit/` exists
- ❌ Use services marked ⚪ Not Configured
- ❌ Assume all services are available
- ❌ Skip reading `.api-toolkit-config.md`
- ❌ Create new connection code if toolkit is installed

### ALWAYS:
- ✅ Check for installation first
- ✅ Read project config second
- ✅ Use only active services
- ✅ Update config as you work
- ✅ Document patterns you discover

---

## Quick Reference Card

**Format for Claude Code:**
```
NEW PROJECT? → Check installation → Check config → Use active only
TOOLKIT PRESENT? → Read config → Parse active services → Start work
NO CONFIG? → Offer to create → Or continue (sub-optimal)
ACTIVE SERVICE? → Use it → Document patterns → Update progress
NOT CONFIGURED? → DON'T USE → Suggest adding if needed
```

---

**Version**: 1.0
**Last Updated**: 2025-10-02
**Purpose**: Visual guide for Claude Code's startup sequence
