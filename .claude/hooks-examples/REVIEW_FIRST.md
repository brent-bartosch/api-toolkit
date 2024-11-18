# ⚠️ Hooks Examples - Review Before Using

These are **example hook implementations** based on the recommendations from "6 Months of Hardcore Claude Code Use".

## 📁 What's Here

- **`quality-gate.sh`** - Blocking hook that runs before commits
  - Checks Python syntax
  - Checks for security issues (hardcoded credentials)
  - Runs tests for modified services
  - BLOCKS commits if checks fail

- **`hint-best-practices.sh`** - Non-blocking hint hook
  - Suggests error handling
  - Reminds about docstrings/type hints
  - Suggests API toolkit best practices
  - Runs after Write/Edit, doesn't block

- **`README.md`** - Full documentation on how hooks work

## 🚫 These Are NOT Active

These hooks are **disabled** and stored here for review only.

## ✅ To Activate (After Review)

If you decide to use them:

1. **Review the scripts** to understand what they do
2. **Test them manually**:
   ```bash
   ./quality-gate.sh "git commit -m 'test'"
   ```
3. **Create `.claude/hooks.json`** to enable them
4. **Move scripts** from `hooks-examples/` to `.claude/hooks/`

## 💡 Discussion Points

Before activating, consider:

1. **Do you want blocking hooks?** (prevent commits until tests pass)
2. **Which checks are most valuable?** (syntax, security, tests, style)
3. **Performance impact?** (hooks run on every commit/write)
4. **Custom checks needed?** (project-specific requirements)

## 📚 Resources

- [Hooks in Claude Code Documentation](https://docs.anthropic.com/claude/docs/hooks)
- Research summary: "6 Months of Hardcore Claude Code Use"
- Common patterns: Block at submit, hint at write

---

**Status:** Examples only, not active
**Created:** 2025-11-19
