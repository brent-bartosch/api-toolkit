# API Toolkit Slash Commands

This directory contains custom Claude Code slash commands for quickly loading API toolkit context into new conversations.

## Why These Commands Exist

When starting a new conversation with Claude Code, the API toolkit context isn't automatically loaded. These commands:

1. **Check installation** - Verify toolkit is installed in current project
2. **Load service context** - Efficiently load only the relevant service files
3. **Prevent duplication** - Remind Claude to USE existing code, not recreate it
4. **Minimize tokens** - Load only what's needed for the specific service

## Available Commands

### General Commands

| Command | Description |
|---------|-------------|
| `/api-toolkit` | Check installation, get overview of all services |

### Service-Specific Commands

| Command | Service | Use For |
|---------|---------|---------|
| `/supabase` | Supabase | Database queries, schema discovery, 3 projects |
| `/smartlead` | Smartlead | Email campaigns, lead management, webhooks |
| `/metabase` | Metabase | Analytics, SQL queries, dashboards, exports |
| `/render` | Render | Cloud deployments, env vars, service management |
| `/brightdata` | BrightData | Web scraping, proxies, SERP API |

## How to Use

### Starting a New Conversation

When you open a new Claude Code conversation and need to work with an API:

```bash
# General check
/api-toolkit

# Or go directly to the service you need
/supabase
/smartlead
/metabase
```

### What the Commands Do

Each command:
1. Checks if `api-toolkit/` is installed in current project
2. Lists the key files to review for that service
3. Summarizes available methods and patterns
4. Loads minimal, focused context (not full docs)
5. Instructs Claude to USE existing code, not rewrite

### Example Workflow

```bash
# You: I need to query some Supabase data
> /supabase

# Claude checks installation, reviews files, then:
# "✅ API toolkit installed. SupabaseAPI available with 3 projects.
# What would you like to query?"

# You: Get leads with score > 80
# Claude uses existing api.query() method, doesn't write new code
```

## Command Structure

Each command file contains:

1. **Description** (YAML frontmatter) - Shows in command list
2. **Critical Instructions** - Check installation, use existing code
3. **Files to Review** - Specific service files to read
4. **Key Methods** - Quick reference of available methods
5. **Common Workflow** - Copy-paste examples
6. **Environment Requirements** - What .env vars are needed
7. **Task** - What Claude should do next

## Creating New Service Commands

To add a command for a new service:

```bash
# Copy template
cp .claude/commands/supabase.md .claude/commands/newservice.md

# Edit the file:
# 1. Update description in frontmatter
# 2. Change service name throughout
# 3. List correct files to review
# 4. Document key methods
# 5. Add example workflow
# 6. Specify environment variables
```

## Benefits

### For Users
- ✅ **Fast context loading** - Get Claude up to speed in seconds
- ✅ **No repetition** - Don't re-explain the toolkit every conversation
- ✅ **Consistent patterns** - Claude uses the established patterns
- ✅ **Token efficient** - Load only relevant service context

### For Claude
- ✅ **Clear instructions** - Know to check installation first
- ✅ **Focused scope** - Only read relevant files
- ✅ **Prevent mistakes** - Don't recreate existing code
- ✅ **Quick reference** - Methods and patterns readily available

## Installation Check Pattern

Every command starts with:

```bash
ls -la api-toolkit/
```

**If toolkit exists:**
- ✅ Read service files
- ✅ Use existing code
- ✅ DO NOT write new implementations

**If toolkit doesn't exist:**
- Offer to install: `/path/to/api-toolkit/install.sh`
- Help set up .env file
- Then proceed with task

## Token Optimization

These commands are designed for minimal token usage:

| Approach | Token Cost | Speed |
|----------|------------|-------|
| Load full README.md | ~5000 tokens | Slow |
| Load full docs | ~10000 tokens | Very slow |
| **Service slash command** | **~500-1000 tokens** | **Fast ✨** |
| Load MCP servers | 90,000+ tokens | Extremely slow ❌ |

## Maintenance

When you update a service:

1. Update the service files (`api.py`, `examples.py`, etc.)
2. Update the corresponding slash command if methods change
3. Keep commands focused - list only commonly-used methods
4. Update `QUICK_REFERENCE.md` with new patterns

## Related Files

- `/path/to/api-toolkit/CLAUDE.md` - General Claude Code guidance
- `/path/to/api-toolkit/QUICK_REFERENCE.md` - Quick reference card
- `/path/to/api-toolkit/README.md` - Full documentation
- Project-specific: `.api-toolkit-config.md` - Per-project configuration

---

**Remember:** These commands help Claude understand what's already built. Always prefer USING existing code over WRITING new code.
