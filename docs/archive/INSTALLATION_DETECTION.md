# API Toolkit Installation Detection

## Problem Solved

Claude Code was repeatedly trying to install or setup the API Toolkit even when it was already installed in projects. This wasted time and caused confusion.

## Solution: Multi-Layer Detection System

### 1. **Marker Files** (Primary Detection)
When `install.sh` runs, it creates a `.toolkit-installed` marker file that contains:
- Installation type (symlink, copy, or python_package)
- Installation date
- Source and project paths
- Version information

**Location of marker file:**
- Symlink/Copy installation: `api-toolkit/.toolkit-installed`
- Python package installation: `.toolkit-installed` (in project root)

### 2. **Updated Documentation Headers**
All key documentation files now start with prominent installation check instructions:

**Files updated:**
- [README.md](README.md) - Added "Check Installation Status First" section at top
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Updated "CLAUDE: READ THIS FIRST" with explicit checks
- `~/CLAUDE.md` - Added "INSTALLATION CHECK - DO THIS FIRST" section

### 3. **Detection Commands for Claude Code**

**Primary check (use this first):**
```bash
# Check for toolkit directory OR marker file
ls -la api-toolkit/ 2>/dev/null || ls -la .toolkit-installed 2>/dev/null
```

**What the output means:**
- ✅ **Sees files/symlink**: Toolkit IS installed → Use it directly
- ❌ **"No such file"**: Toolkit NOT installed → Run install.sh

**Secondary verification:**
```bash
# Read marker file to see installation details
cat api-toolkit/.toolkit-installed 2>/dev/null || cat .toolkit-installed 2>/dev/null
```

## Instructions for Claude Code

When you start working in a new project:

1. **FIRST**: Check if toolkit exists
   ```bash
   ls -la api-toolkit/ || ls -la .toolkit-installed
   ```

2. **IF EXISTS**: Skip directly to usage
   - Do NOT run install.sh
   - Do NOT create new setup scripts
   - Do NOT write new connection code
   - Just import and use: `from api_toolkit.services.supabase.api import SupabaseAPI`

3. **IF NOT EXISTS**: Install it
   ```bash
   /path/to/api-toolkit/install.sh
   ```

## Key Documentation Files (All Updated)

1. **[README.md](README.md)** - Main documentation with installation check at top
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick start guide with check-first workflow
3. **`~/CLAUDE.md`** - Global Claude configuration with prominent warning

## Benefits

- ✅ **No repeated installations** - Clear detection prevents redundant setup
- ✅ **Faster onboarding** - Claude Code immediately knows toolkit status
- ✅ **Less confusion** - Documentation clearly states "check first, install second"
- ✅ **Persistent markers** - `.toolkit-installed` files track installation state
- ✅ **Multi-method detection** - Works with symlinks, copies, and Python packages

## Maintenance

The `.toolkit-installed` marker files are:
- Created automatically by install.sh
- Should NOT be deleted (contains important metadata)
- Safe to commit to git (helps team members know toolkit is in use)
- Human-readable for troubleshooting

## Testing the Solution

```bash
# Test in a new conversation:
# 1. cd to a project with api-toolkit
cd /path/to/project

# 2. Run the check
ls -la api-toolkit/

# 3. You should see output (symlink or directory)
# This means: SKIP installation, use directly!

# 4. Verify marker file
cat api-toolkit/.toolkit-installed
# Should show installation metadata
```

---

**Last updated:** 2025-10-02
**Version:** 2.0
