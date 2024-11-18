# Claude Code Quality Hooks

This directory contains quality control hooks that run automatically during Claude Code operations.

## 🎯 What Are Hooks?

Hooks are scripts that Claude Code runs at specific points (before commits, after file writes, etc.) to ensure code quality and prevent errors.

## 📁 Files

### `hooks.json`
Configuration file that tells Claude Code which hooks to run and when.

### `quality-gate.sh` (BLOCKING)
**Runs before git commits** - Blocks commits if checks fail.

**Checks:**
1. ✅ Python syntax validation
2. ✅ Security checks (no hardcoded credentials, no .env commits)
3. ⚠️  Code quality hints (print statements, TODOs)
4. ✅ Automated tests for modified services

**Exit codes:**
- `0` = All checks passed, commit allowed
- `1` = Checks failed, commit blocked

### `hint-best-practices.sh` (NON-BLOCKING)
**Runs after Write/Edit tools** - Provides guidance without blocking.

**Hints:**
- 💡 Missing error handling (try/except)
- 💡 Missing docstrings
- 💡 Missing type hints
- 💡 Using print() instead of logging
- 💡 Manual pagination (use `fetch_all()`)
- 💡 Using `len(query())` (use `count()`)
- 💡 Using `len(query()) > 0` (use `exists()`)

## 🚀 How to Use

### Enable Hooks (Already Done)
Hooks are configured in `.claude/hooks.json` and automatically run.

### Test Hooks Manually

```bash
# Test quality gate
./.claude/hooks/quality-gate.sh "git commit -m 'test'"

# Test best practices hints
./.claude/hooks/hint-best-practices.sh "Write" '{"file_path": "services/supabase/api.py"}'
```

### Disable Hooks Temporarily

Edit `.claude/hooks.json` and set `"enabled": false`:

```json
{
  "hooks": {
    "user-prompt-submit": {
      "enabled": false,  // <-- Disable here
      ...
    }
  }
}
```

### Bypass Hooks (Emergency)

If hooks are incorrectly blocking:

```bash
# Remove pass file
rm /tmp/agent-pre-commit-pass

# Or disable in hooks.json
```

## 📊 Hook Flow

### Block-at-Submit Hook (Primary Quality Control)

```
Claude writes code
    ↓
Claude: "git commit -m 'Add feature'"
    ↓
quality-gate.sh runs
    ↓
┌─────────────────┐
│ Check 1: Syntax │ ─── ❌ Fail → Block commit, show error
└─────────────────┘        │
    ↓ ✅ Pass              │
┌─────────────────┐        │
│ Check 2: Security│ ─── ❌ Fail → Block commit
└─────────────────┘        │
    ↓ ✅ Pass              │
┌─────────────────┐        │
│ Check 3: Tests  │ ─── ❌ Fail → Block commit, show test output
└─────────────────┘
    ↓ ✅ Pass

Commit allowed! ✓
```

### Hint Hook (Non-blocking Guidance)

```
Claude: Write tool called
    ↓
File written successfully
    ↓
hint-best-practices.sh runs
    ↓
Shows helpful tips:
💡 Consider adding error handling
💡 Missing docstrings
💡 Use api.count() instead of len(query())
    ↓
Continues (doesn't block)
```

## 🎓 Best Practices

### 1. Keep Hooks Fast
- Hooks run on every commit/write
- Avoid expensive operations
- Cache results when possible

### 2. Clear Error Messages
- Tell Claude HOW to fix the issue
- Provide examples
- Link to relevant docs

### 3. Balance Blocking vs Hints
- **Block:** Syntax errors, security issues, failing tests
- **Hint:** Style suggestions, optimization tips, best practices

### 4. Test Your Hooks
```bash
# Test blocking behavior
./quality-gate.sh "git commit -m 'test'"

# Expected: Exit 1 if checks fail, Exit 0 if pass
```

## 🔧 Customization

### Add New Check to Quality Gate

Edit `quality-gate.sh`:

```bash
# ═══════════════════════════════════════════════════
# 5. YOUR NEW CHECK
# ═══════════════════════════════════════════════════
echo ""
echo "▶ Step 5/5: Your check..."

# Your check logic here
if [ some_condition ]; then
  echo "❌ BLOCKED: Your error message"
  exit 1  # Blocks commit
fi

echo "  ✅ Your check passed"
```

### Add New Hint

Edit `hint-best-practices.sh`:

```bash
# ═══════════════════════════════════════════════════
# HINT X: Your Hint
# ═══════════════════════════════════════════════════
if grep -q "pattern" "$file_path"; then
  echo ""
  echo "💡 HINT: Your suggestion"
  echo "   File: $file_path"
  echo "   Tip: How to improve"
fi
```

## 📚 Examples

### Example 1: Blocked Commit (Syntax Error)

```
Claude: git commit -m "Add new feature"

Hook Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 API Toolkit Quality Gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▶ Step 1/4: Checking Python syntax...
  ❌ Syntax error in services/supabase/api.py

❌ BLOCKED: Fix Python syntax errors before committing

Result: Commit blocked ❌
Claude must fix syntax error and try again
```

### Example 2: Hint (Non-blocking)

```
Claude: [Writes new API method]

Hook Output:
💡 HINT: Consider adding error handling
   File: services/smartlead/api.py
   Detected: Network operations without try/except
   Tip: Wrap API calls in try/except blocks

Result: Continues normally ✓
Claude receives hint but can proceed
```

### Example 3: All Checks Pass

```
Claude: git commit -m "Add fetch_all method"

Hook Output:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 API Toolkit Quality Gate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▶ Step 1/4: Checking Python syntax...
  ✅ All Python files have valid syntax

▶ Step 2/4: Security checks...
  ✅ No security issues detected

▶ Step 3/4: Code quality hints...
  ✅ Quality hints complete

▶ Step 4/4: Running tests...
  🧪 Service files modified, running relevant tests...
     Testing supabase...
  ✅ All service tests passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALL QUALITY CHECKS PASSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commit allowed ✓

Result: Commit succeeds ✅
```

## 🆘 Troubleshooting

### Hook Not Running
```bash
# Check if hooks.json exists
cat .claude/hooks.json

# Check hook is executable
ls -l .claude/hooks/*.sh

# Make executable if needed
chmod +x .claude/hooks/*.sh
```

### Hook Always Blocks
```bash
# Test hook manually
bash -x .claude/hooks/quality-gate.sh "git commit -m 'test'"

# Check for logic errors
# Look for unexpected exit 1
```

### Hook Slows Down Workflow
```bash
# Profile hook execution
time .claude/hooks/quality-gate.sh "git commit -m 'test'"

# Optimize slow sections
# Consider skipping tests for minor changes
```

## 🔗 Resources

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude/docs/hooks)
- [Git Hooks Guide](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Bash Scripting Tutorial](https://www.shellscript.sh/)

## 💡 Tips

1. **Start Simple** - Add one check at a time
2. **Test Thoroughly** - Run hooks manually before committing
3. **Clear Messages** - Help Claude understand what went wrong
4. **Balance Speed** - Hooks should be fast (<5 seconds)
5. **Version Control** - Commit hooks.json so it persists

---

**Last Updated:** 2025-11-19
**API Toolkit v2.1**
