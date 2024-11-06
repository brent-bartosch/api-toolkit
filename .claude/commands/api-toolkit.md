---
description: Check API toolkit installation and load general context
---

# API Toolkit General Context

**FIRST: Check if toolkit is installed in this project**

Run this check immediately:
```bash
bash /path/to/api-toolkit/check-installation.sh
```

Or manually:
```bash
ls -la api-toolkit/
```

**If INSTALLED (you see output):**
- ✅ Toolkit is ready to use
- ✅ DO NOT run install.sh again
- ✅ DO NOT write new API integration code
- ✅ USE the existing services

**If NOT installed:**
- Offer to install it: `/path/to/api-toolkit/install.sh`

---

## What is the API Toolkit?

A lightweight, token-efficient alternative to MCP servers providing:
- **180x more efficient** than MCP (500-1000 tokens vs 90,000)
- Unified interface for multiple API services
- Built-in retry logic, rate limiting, error handling
- Discovery-first patterns to avoid errors

## Available Services

Review the appropriate command for the service you need:

| Service | Slash Command | Description |
|---------|---------------|-------------|
| **Supabase** | `/supabase` | Database operations (3 projects: smoothed, blingsting, scraping) |
| **Smartlead** | `/smartlead` | Cold email campaigns and webhooks |
| **Metabase** | `/metabase` | Analytics, BI, SQL queries |
| **Render** | `/render` | Cloud deployments |
| **BrightData** | `/brightdata` | Web scraping and proxies |
| **Context7** | `/context7` | Real-time API documentation |

## Quick Installation Check

After checking installation status:

**If installed, review:**
1. `api-toolkit/README.md` - General overview
2. `api-toolkit/QUICK_REFERENCE.md` - Quick reference card
3. `api-toolkit/CLAUDE.md` - This file (guidance for Claude Code)
4. Service-specific files in `api-toolkit/services/{name}/`

**If not installed:**
1. Ask if user wants to install it
2. Run: `/path/to/api-toolkit/install.sh`
3. Choose option 1 (symlink - recommended)
4. Help user create `.env` file with credentials

## Architecture Overview

```
api-toolkit/
├── core/
│   ├── base_api.py      # All services inherit from BaseAPI
│   ├── config.py        # Environment and configuration
│   └── documentation.py # Doc loading
├── services/
│   ├── supabase/        # Database operations
│   ├── smartlead/       # Email campaigns
│   ├── metabase/        # Analytics
│   ├── render/          # Deployments
│   ├── brightdata/      # Web scraping
│   └── context7/        # Documentation
├── toolkit.py           # CLI interface
└── tests/               # Test suite
```

## Environment Configuration

The toolkit loads `.env` with this priority:
1. **Project root** (`./env`) ← Put your .env here!
2. Toolkit directory (`api-toolkit/.env`)
3. Home directory (`~/.api-toolkit.env`)

Check which .env is loaded:
```bash
python api-toolkit/test-env-loading.py
```

## Common Commands

```bash
# List services
python api-toolkit/toolkit.py list

# Test connection
python api-toolkit/toolkit.py supabase test smoothed

# Check environment
python api-toolkit/toolkit.py supabase check

# Get help
python api-toolkit/toolkit.py --help
```

## Key Principle

**ALWAYS use existing toolkit code. DO NOT rewrite or duplicate functionality.**

If you need to work with a specific service, use the service-specific slash command:
- `/supabase` - For database work
- `/smartlead` - For email campaigns
- `/metabase` - For analytics
- etc.

**Your Task:**
1. Check installation status
2. Report what's available
3. Ask which service the user needs help with
4. Direct them to use the appropriate service-specific command
