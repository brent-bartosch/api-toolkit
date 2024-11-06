# API Toolkit Slash Commands for Claude Code

## 🎯 Problem Solved

Every time you start a new Claude Code conversation, you had to:
- ❌ Re-explain the API toolkit exists
- ❌ Wait for Claude to discover the files
- ❌ Watch Claude try to recreate existing code
- ❌ Waste tokens loading full documentation

## ✨ Solution: Service-Specific Slash Commands

Pre-configured commands that instantly load the right context for each API service.

## 📋 Available Commands

### Quick Reference Table

| Command | Tokens | Speed | Use When |
|---------|--------|-------|----------|
| `/api-toolkit` | ~800 | ⚡ Fast | Check installation, get overview |
| `/supabase` | ~1000 | ⚡ Fast | Database work (3 projects available) |
| `/smartlead` | ~900 | ⚡ Fast | Email campaigns, webhooks |
| `/metabase` | ~850 | ⚡ Fast | Analytics, BI, SQL queries |
| `/render` | ~800 | ⚡ Fast | Cloud deployments, env vars |
| `/brightdata` | ~850 | ⚡ Fast | Web scraping, proxies |

Compare to:
- Loading full README: ~5,000 tokens
- Loading all docs: ~10,000 tokens
- MCP servers: 90,000+ tokens ❌

## 🚀 Quick Start

### Scenario 1: Starting Fresh

```bash
# You open Claude Code in a project
# You type:
/api-toolkit

# Claude responds:
# "✅ Checking installation..."
# "✅ API toolkit found at api-toolkit/"
# "Available services: supabase, smartlead, metabase, render, brightdata"
# "Which service do you need help with?"

# You type:
/supabase

# Claude responds:
# "✅ Reviewing Supabase service..."
# "SupabaseAPI available with 3 projects: smoothed, blingsting, scraping"
# "Key methods: .quick_start(), .query(), .raw_query(), QueryBuilder"
# "What would you like to query?"
```

### Scenario 2: Direct to Service

```bash
# You know you need Supabase, skip the overview
/supabase

# Claude loads Supabase context immediately
# Ready to help with queries
```

### Scenario 3: Installation Check

```bash
# Working in a new project, not sure if toolkit is installed
/api-toolkit

# Claude checks and either:
# ✅ "Toolkit installed, which service?"
# OR
# ❌ "Toolkit not found. Install with: /path/to/api-toolkit/install.sh"
```

## 📖 Command Details

### `/api-toolkit` - General Overview

**What it does:**
1. Checks if toolkit is installed (`ls -la api-toolkit/`)
2. Lists all available services
3. Explains the architecture
4. Shows installation command if needed
5. Directs you to service-specific commands

**When to use:**
- First time in a project
- Not sure if toolkit is installed
- Want to see all available services
- Need installation help

**Token cost:** ~800 tokens

---

### `/supabase` - Database Operations

**What it does:**
1. Checks installation
2. Reviews `services/supabase/api.py`
3. Reviews `services/supabase/query_helpers.py`
4. Loads Supabase sections from QUICK_REFERENCE.md
5. Summarizes available methods and 3 projects

**Key information loaded:**
- SupabaseAPI initialization
- Discovery methods (quick_start, discover, explore)
- Query methods (query, raw_query, get_schema)
- QueryBuilder pattern
- Three projects: smoothed, blingsting, scraping
- Environment variable requirements

**When to use:**
- Need to query Supabase databases
- Want to explore schema
- Building complex queries
- Working with any of the 3 projects

**Token cost:** ~1000 tokens

---

### `/smartlead` - Email Campaigns

**What it does:**
1. Checks installation
2. Reviews `services/smartlead/api.py`
3. Reviews `services/smartlead/webhooks.py`
4. Loads webhook handler patterns
5. Summarizes campaign management

**Key information loaded:**
- SmartleadAPI initialization
- Campaign creation and management
- Lead addition and tracking
- Analytics and reporting
- Webhook event handling

**When to use:**
- Creating email campaigns
- Managing leads
- Setting up webhooks
- Analyzing campaign performance

**Token cost:** ~900 tokens

---

### `/metabase` - Analytics & BI

**What it does:**
1. Checks installation
2. Reviews `services/metabase/api.py`
3. Loads query and export patterns
4. Summarizes dashboard management

**Key information loaded:**
- MetabaseAPI initialization (API key or session)
- SQL query execution
- Saved card/question queries
- Export functionality (CSV, JSON, XLSX)
- Dashboard creation and management

**When to use:**
- Running analytics queries
- Exporting data
- Creating dashboards
- Working with saved questions

**Token cost:** ~850 tokens

---

### `/render` - Cloud Deployments

**What it does:**
1. Checks installation
2. Reviews `services/render/api.py`
3. Loads deployment management patterns
4. Summarizes service and database operations

**Key information loaded:**
- RenderAPI initialization
- Service listing and management
- Deploy triggering and monitoring
- Environment variable management
- Database operations

**When to use:**
- Deploying services
- Managing environment variables
- Checking deploy status
- Working with Render databases

**Token cost:** ~800 tokens

---

### `/brightdata` - Web Project 3

**What it does:**
1. Checks installation
2. Reviews `services/brightdata/api.py`
3. Reviews `services/brightdata/web_unlocker.py`
4. Loads scraping patterns

**Key information loaded:**
- BrightDataAPI initialization
- Project 3 Browser usage
- Web Unlocker for anti-bot bypass
- SERP API for search results
- Proxy management

**When to use:**
- Web scraping projects
- Bypassing anti-bot protections
- Fetching search results
- Managing proxies

**Token cost:** ~850 tokens

## 🎓 Best Practices

### 1. Start Every Conversation with a Slash Command

Instead of typing:
> "I need to query the Supabase project1 database for leads with high scores"

Type:
```bash
/supabase
```

Then say:
> "Query project1 database for leads with score > 80"

**Why:** Claude already knows about SupabaseAPI, QueryBuilder, and the project1 project.

---

### 2. Use Service-Specific Commands

Don't use `/api-toolkit` unless you need the overview. Go directly to what you need:

```bash
/supabase      # For database work
/smartlead     # For email campaigns
/metabase      # For analytics
```

**Why:** Loads less context, saves tokens, faster response.

---

### 3. Trust the Installation Check

Every command checks if toolkit is installed. If Claude says it's installed, it is. Don't ask again.

**Claude will tell you:**
- ✅ "Toolkit installed at api-toolkit/"
- OR
- ❌ "Toolkit not found. Install?"

---

### 4. Let Claude Review the Files

The commands instruct Claude to read specific files. Let it do this before asking your question.

**Good flow:**
```
You: /supabase
Claude: [reviews files, loads context]
You: Get high-scoring leads
Claude: [uses QueryBuilder from reviewed files]
```

**Poor flow:**
```
You: /supabase how do I query leads?
Claude: [might answer before reviewing files]
```

---

### 5. Use Commands in Other Projects

These slash commands work across all projects that have the toolkit installed:

```bash
# Project A
cd ~/projects/crm-system
/supabase

# Project B
cd ~/projects/analytics-dashboard
/metabase

# Project C
cd ~/projects/email-automation
/smartlead
```

Each command checks the local project's installation.

## 📦 Installation in Your Projects

For these commands to work in other projects:

### Option 1: Copy to Each Project (Recommended)

```bash
# In your project directory
mkdir -p .claude/commands

# Copy the commands you need
cp /path/to/api-toolkit/.claude/commands/supabase.md .claude/commands/
cp /path/to/api-toolkit/.claude/commands/api-toolkit.md .claude/commands/

# Now /supabase works in this project!
```

### Option 2: Symlink (Advanced)

```bash
# In your project directory
ln -s /path/to/api-toolkit/.claude/commands .claude/commands

# All commands available, auto-update when api-toolkit updates
```

### Option 3: Use from Home CLAUDE.md

Add to your `~/CLAUDE.md`:

```markdown
## API Toolkit Slash Commands

Available in projects with api-toolkit:
- `/supabase` - Database operations
- `/smartlead` - Email campaigns
- `/metabase` - Analytics
- `/render` - Deployments
- `/brightdata` - Web scraping

Commands located at: `/path/to/api-toolkit/.claude/commands/`
```

## 🔧 Customizing Commands

### Add Project-Specific Context

Edit the command file to add your common queries:

```markdown
<!-- In .claude/commands/supabase.md -->

## Your Common Queries

**Get active leads:**
```python
api = SupabaseAPI('project1')
leads = api.query('leads', filters={'status': 'eq.active', 'score': 'gte.80'})
```

**Export customers:**
```python
api = SupabaseAPI('project2')
customers = api.query('customers', order='-created_at', limit=100)
```
\`\`\`

### Add Environment Reminders

```markdown
## Project-Specific Environment

For THIS project, you need:
\`\`\`bash
SUPABASE_URL=https://your-specific-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here
\`\`\`
```

## 📊 Token Usage Comparison

### Traditional Approach
```
User: "I need to query Supabase for high-scoring leads"
Claude: "Let me check what's available..." [explores files: 5000 tokens]
Claude: "I'll write a query function..." [writes new code]
User: "No, use the existing toolkit!"
Claude: "Oh, let me check the toolkit..." [more exploration: 3000 tokens]
Total: 8000+ tokens, duplicate code written
```

### With Slash Commands
```
User: /supabase
Claude: [loads 1000 tokens of focused context]
User: "Get high-scoring leads"
Claude: [uses QueryBuilder from loaded context]
Total: 1000 tokens, uses existing code
```

**Savings:** 87% fewer tokens, no duplicate code, faster results.

## 🎯 Real-World Examples

### Example 1: Database Query

**Without command:**
```
User: I need to query the smoothed Supabase for leads with score over 85
Claude: Let me explore your codebase...
[10 file reads, 4000 tokens]
Claude: I'll create a query function...
[Writes new code instead of using SupabaseAPI]
```

**With command:**
```
User: /supabase
Claude: [Loads SupabaseAPI context, 1000 tokens]
User: Query smoothed for leads score > 85
Claude: ```python
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.supabase.query_helpers import QueryBuilder

api = SupabaseAPI('project1')
query = QueryBuilder('leads').where('score', '>', 85)
leads = query.execute(api)
```
[Uses existing code correctly]
```

### Example 2: Email Campaign

**Without command:**
```
User: Create a Smartlead campaign
Claude: Do you have a Smartlead integration?
User: Yes, check the api-toolkit
Claude: [Explores, reads files, 5000 tokens]
Claude: Here's how to call the API...
[Writes requests.post() instead of using SmartleadAPI]
```

**With command:**
```
User: /smartlead
Claude: [Loads SmartleadAPI context, 900 tokens]
User: Create campaign "Q1 Outreach"
Claude: ```python
from api_toolkit.services.smartlead.api import SmartleadAPI

api = SmartleadAPI()
campaign = api.create_campaign('Q1 Outreach', client_id=1)
```
[Uses existing SmartleadAPI]
```

## 🆘 Troubleshooting

### "Command not found"

**Problem:** `/supabase` returns "command not found"

**Solution:**
```bash
# Check if commands directory exists
ls -la .claude/commands/

# If not, copy commands from api-toolkit
mkdir -p .claude/commands
cp /path/to/api-toolkit/.claude/commands/*.md .claude/commands/
```

---

### "Toolkit not installed"

**Problem:** Command says toolkit not installed but you're sure it is

**Solution:**
```bash
# Verify installation
ls -la api-toolkit/

# If it's a symlink, check it's valid
ls -la api-toolkit/toolkit.py

# Re-run installation if needed
/path/to/api-toolkit/install.sh
```

---

### "Claude still writing new code"

**Problem:** Even after using `/supabase`, Claude writes new query functions

**Cause:** Command instructions weren't followed

**Solution:**
1. Check the command file has "USE EXISTING CODE" instructions
2. Be explicit: "Use the existing SupabaseAPI class"
3. Remind: "Don't write new code, use api-toolkit"

---

### "Too much context loaded"

**Problem:** Command loads too many files, uses too many tokens

**Solution:**
Edit the command file to be more selective:
```markdown
**Files to Review:**
- `api-toolkit/services/supabase/api.py` - Main class only
<!-- Remove unnecessary files -->
```

## 🔮 Future Enhancements

Planned improvements:

1. **Auto-discovery** - Commands auto-detect which services project uses
2. **Smart caching** - Remember loaded context across conversations
3. **Usage analytics** - Track which services are used most
4. **Context trimming** - Load only the methods you typically use
5. **Project templates** - Pre-configured command sets for project types

## 📚 Related Documentation

- `.claude/commands/README.md` - Command structure and maintenance
- `CLAUDE.md` - General Claude Code guidance for this repository
- `QUICK_REFERENCE.md` - Quick reference card for all services
- `README.md` - Full API toolkit documentation

---

**Remember:** These slash commands are designed to make your conversation with Claude more efficient. Use them at the start of every conversation to avoid repeating yourself!
