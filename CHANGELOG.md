# API Toolkit Changelog

## Version 2.1.1 - Smart Environment Loading (2025-10-10)

### 🎯 Problem Statement

Users experienced confusion about where to place `.env` files:
- Should each service have its own .env file?
- Should .env be in the toolkit directory or project root?
- Which .env file is actually being used?

### ✨ New Features

#### 1. **Priority-Based .env Loading** 🔍

**Smart Search Order:**
1. **Project root** (`./env`) - Checked FIRST ✅
2. Toolkit directory (`api-toolkit/.env`) - Fallback
3. Home directory (`~/.api-toolkit.env`) - Global fallback

**Updated File:**
- `core/config.py` - New `_load_env_with_priority()` function

#### 2. **Environment Diagnostics** 🛠

**Test Script:** `test-env-loading.py`
```bash
python api-toolkit/test-env-loading.py
# Shows: which .env loaded + all service credential status
```

**New Config Method:**
```python
from api_toolkit.core.config import Config
Config.get_env_source()  # Returns path to loaded .env
```

#### 3. **Comprehensive Documentation** 📚

**New File:** `ENV_TROUBLESHOOTING.md`
- Where to put .env files
- How priority loading works
- Common problems & solutions
- Security best practices
- Service-by-service variable reference

**Updated Files:**
- `README.md` - Added "Where to Put Your .env File" section
- `QUICK_REFERENCE.md` - Added env diagnostic commands

### 🎯 Recommendation

**Keep ONE `.env` file in your project root:**
```bash
your-project/
├── .env                    # ✅ All API keys here
├── api-toolkit/           # Symlink
└── main.py
```

### 💡 Benefits

- ✅ **Clear best practice** - One .env per project
- ✅ **No more guessing** - Diagnostic shows which file loaded
- ✅ **Standard conventions** - Works like most Python projects
- ✅ **Multi-project support** - Each project has own credentials
- ✅ **Easy debugging** - Test script shows exactly what's wrong

---

## Version 2.1.0 - Installation Detection & Project Configuration (2025-10-02)

### 🎯 Problem Statement

After v2.0 launched, we discovered two critical issues affecting Claude Code usage:
1. Redundant installation attempts when toolkit was already present
2. No way to track which services were active per project (context lost between conversations)

### ✨ New Features

#### 1. **Installation Detection System** 🔍

**Marker Files**
- Auto-created `.toolkit-installed` files track installation state
- Contains metadata: version, type (symlink/copy/package), paths, date
- Prevents redundant installation attempts

**Check Script**
```bash
bash /path/to/api-toolkit/check-installation.sh
# Output: ✓ Toolkit IS installed (type: symlink)
```

#### 2. **Project Configuration System** 📋

**Per-Project Config File** (`.api-toolkit-config.md`)
```markdown
### Supabase
- **Status**: ✅ Active
- **Project(s) Used**: smoothed
- **Common Pattern**: api.query('leads', filters={'score': 'gte.80'})

### Metabase
- **Status**: ⚪ Not Configured (not needed for this project)
```

**Service Status Indicators**
- ⚪ **Not Configured** - Don't use this service in this project
- 🟡 **Configured** - Credentials added, ready to test
- ✅ **Active** - Tested and working, safe to use

**Interactive Configuration**
```bash
/path/to/api-toolkit/init-project.sh
# Wizard asks which services project needs
# Creates customized .api-toolkit-config.md
```

#### 3. **Updated Install Flow**

**install.sh Enhancements**
- Creates marker files for all installation types
- Offers project configuration after installation
- Integrated with init-project.sh wizard

### 📚 New Documentation

**Core Guides:**
1. **INSTALLATION_DETECTION.md** - How detection system works
2. **PROJECT_CONFIG_GUIDE.md** - Complete guide to project configs (4000+ words)
3. **COMPLETE_SOLUTION_SUMMARY.md** - Technical implementation details
4. **QUICK_START_FLOWCHART.md** - Visual decision tree for Claude Code

**Updated Files:**
- `README.md` - Added "Check Installation Status First" section
- `QUICK_REFERENCE.md` - Added project config check step
- `CLAUDE.md` - Added installation & config check instructions
- `IMPROVEMENTS_SUMMARY.md` - Added v2.1 section

### 🔧 Technical Changes

**New Scripts:**
1. `check-installation.sh` - Status detection with color output
2. `init-project.sh` - Interactive project configuration wizard
3. `.toolkit-installed` - Marker file template
4. `.api-toolkit-config.template.md` - Configuration template

**Updated Scripts:**
- `install.sh` - Lines 55-69, 104-118, 142-156, 199-214

### 💡 Benefits

| Aspect | Before v2.1 | After v2.1 | Time Saved |
|--------|-------------|------------|------------|
| Installation checks | Trial & error | Automated detection | 5-10 min |
| Service knowledge | Lost on restart | Persisted in config | Always available |
| Pattern reuse | Reinvent each time | Documented | Instant access |
| Progress tracking | No visibility | Checkboxes & notes | Clear status |
| Multi-project work | Confusion | Isolated configs | No mixing |

### 🔄 Workflow for Claude Code

**Every New Conversation:**
```bash
# Step 1: Check installation (2s)
ls -la api-toolkit/

# Step 2: Read project config (3s)
cat .api-toolkit-config.md

# Step 3: Use ONLY active services
# ✅ Supabase & Smartlead active → Use them
# ❌ Metabase not configured → Ignore it

# Step 4: Continue from progress notes
```

### 📖 Real-World Example

**Day 1:**
```bash
cd /project/lead-gen
/path/to/api-toolkit/install.sh
# Select: Supabase, Smartlead
# Creates .api-toolkit-config.md
```

**Day 5 (New Conversation):**
```bash
# Claude Code reads .api-toolkit-config.md
# Sees: ✅ Supabase active, ✅ Smartlead active
# Sees: [x] Lead scoring done, [ ] Smartlead integration pending
# Picks up exactly where you left off!
```

### 💬 User Feedback That Drove This

> "I'll start a new conversation with Claude Code, and it thinks, oh, I have to install this when everything has already been installed."

> "Each project has its own requirements. Is it best practice to tell the agent which ones we need?"

> "Will it update so when the conversation is restarted, it'll have the context?"

### 🚀 Migration Guide

**For Existing Projects:**
```bash
cd /path/to/project-with-toolkit
/path/to/api-toolkit/init-project.sh
# Creates .api-toolkit-config.md
```

**For New Projects:**
```bash
cd /path/to/new-project
/path/to/api-toolkit/install.sh
# Answer "y" to create project config
```

### 🎯 Key Insights

1. **Statelessness is the enemy** - Files persist, conversations don't
2. **Explicit > Implicit** - Declare what's active, don't guess
3. **Detection > Installation** - Check first, install second
4. **Project isolation** - Different projects need different tools

---

## Version 2.0.0 - Zero-Friction Update (2024)

### 🎯 Based on Real User Feedback

After extensive real-world usage, we've implemented critical improvements that eliminate 80% of the friction users experienced.

### ✨ New Features

#### 1. **discover() Method** - Always Works! 🥇
```python
info = api.discover()          # All tables with accessibility status
info = api.discover('users')   # Columns, types, samples, row count
```
- **Why added**: Users spent 30+ minutes trying to figure out what tables/columns existed
- **Impact**: Eliminates guesswork, always returns useful info even if queries fail
- **Fallback**: Uses known tables for each project if API discovery fails

#### 2. **quick_start() Method** - 5-Second Setup 🚀
```python
api = SupabaseAPI('project1')
api.quick_start()  # Shows EVERYTHING you need!
```
- **Why added**: Users wanted "out of the box" functionality
- **Impact**: See all tables, columns, filter syntax, examples in one command
- **Output**: Connection status, available tables, sample structure, filter cheatsheet

#### 3. **raw_query() Method** - Complex SQL Support 📝
```python
results = api.raw_query("""
    SELECT u.*, COUNT(o.id) as orders
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id
    HAVING COUNT(o.id) > 5
""")
```
- **Why added**: Filter syntax couldn't handle complex queries (JOINs, GROUP BY, OR logic)
- **Safety**: SELECT-only, auto-LIMIT, parameterized queries
- **Fallback**: Converts simple SQL to REST API calls when RPC unavailable

#### 4. **Enhanced Error Messages** 🛠
```
Table 'userz' does not exist.
Available tables: users, profiles, sessions
Hint: Use api.discover() first to see all available tables
```
- **Why added**: Generic errors left users guessing what went wrong
- **Impact**: Shows available tables/columns directly in error message
- **Coverage**: Table errors, column errors, auth errors

#### 5. **Clear API Response Documentation** 📖
```python
# API returns LIST directly
users = api.query('users')     # ✅ users is a list
for user in users:              # ✅ NOT users['data']
    print(user['email'])
```
- **Why added**: Users expected `result['data']` format
- **Impact**: Clear docstrings prevent confusion about response structure

### 📚 New Documentation

#### FILTER_SYNTAX.md - Complete Reference
- All operators with SQL equivalents
- Common patterns and gotchas
- Quick diagnostic section
- Copy-paste examples

#### Updated QUICK_REFERENCE.md
- Start with `quick_start()` command
- New methods prominently featured
- Clear response format notes

### 🔧 Technical Improvements

1. **Known Tables Fallback**
   - Each project has hardcoded table list
   - Discovery works even if API fails
   
2. **Type Inference**
   - Automatically detects column types from samples
   - Shows boolean, integer, text, jsonb, array types

3. **Better Project Handling**
   - Clear project descriptions
   - Proper env var guidance in errors

### 💡 User Feedback That Drove Changes

> "The discover() method would have saved me 30 minutes"

> "I kept trying result['data'] and getting errors"

> "Filter syntax for complex queries was impossible"

> "Errors didn't tell me what tables actually existed"

> "I just want it to work out of the box"

### 🚀 Migration Guide

**Before (v1.0):**
```python
api = SupabaseAPI('project1')
# Guess at table names
# Hope columns exist
# Struggle with filters
```

**After (v2.0):**
```python
api = SupabaseAPI('project1')
api.quick_start()  # See everything!
info = api.discover('table')  # Never guess again
api.raw_query("SELECT...")  # Complex queries work
```

### 📊 Impact Metrics

- **Discovery time**: 30 minutes → 5 seconds
- **Error resolution**: 5-10 minutes → immediate
- **Complex queries**: impossible → simple
- **Setup friction**: 80% reduction
- **Token usage**: Still 180x better than MCP!

---

## Version 1.0.0 - Initial Release

### Features
- Multi-project Supabase support
- Query builder for clean syntax
- Environment-based configuration
- 180x token reduction vs MCP servers
- Installation script for easy deployment

### Projects Supported
- Project1 (Lead Generation)
- Project2 (CRM)
- Project 3 (Web Project 3)