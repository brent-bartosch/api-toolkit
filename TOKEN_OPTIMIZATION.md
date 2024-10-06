# Token Optimization Strategy

## Problem
We've added comprehensive documentation which is great for reference but could bloat Claude Code's context on every conversation start.

## Solution: Layered Documentation

### Layer 1: ALWAYS LOAD (Essential - ~1500 tokens)
**Files Claude Code reads on every conversation:**
- `README.md` - Quick start, essential commands
- `QUICK_REFERENCE.md` - Fast lookup reference
- `.api-toolkit-config.md` - Project-specific config (if exists)

**What they contain:**
- Installation check commands
- Project config check
- Service status (✅/⚪)
- Essential code examples
- Links to deeper docs (not the docs themselves)

### Layer 2: LOAD ON DEMAND (Reference - ~3000 tokens)
**Files Claude Code reads ONLY when needed:**
- `PROJECT_CONFIG_GUIDE.md` - When setting up config
- `INSTALLATION_DETECTION.md` - When troubleshooting install
- `FILTER_SYNTAX.md` - When writing complex queries
- Service-specific docs (`services/*/README.md`)

**When to load:**
- User explicitly asks
- Error suggests need
- Tool references guide

### Layer 3: NEVER AUTO-LOAD (History - ~2000 tokens)
**Files for humans, excluded via .claudeignore:**
- `CHANGELOG.md` - Version history
- `IMPROVEMENTS_SUMMARY.md` - Evolution story
- `COMPLETE_SOLUTION_SUMMARY.md` - Technical deep-dive
- `QUICK_START_FLOWCHART.md` - Visual reference
- Test reports and guides

**Access:**
- Read only when user asks "what changed?"
- Excluded from automatic context loading

## Token Budget Comparison

### Before Optimization (Hypothetical bloat):
```
README.md                        ~2000 tokens
QUICK_REFERENCE.md               ~1000 tokens
CHANGELOG.md                     ~1500 tokens (bloat!)
IMPROVEMENTS_SUMMARY.md          ~2000 tokens (bloat!)
PROJECT_CONFIG_GUIDE.md          ~2500 tokens (bloat!)
COMPLETE_SOLUTION_SUMMARY.md    ~2500 tokens (bloat!)
INSTALLATION_DETECTION.md        ~800 tokens (bloat!)
QUICK_START_FLOWCHART.md        ~1200 tokens (bloat!)
─────────────────────────────────────────────
Total: ~13,500 tokens (TOO MUCH!)
```

### After Optimization (With .claudeignore):
```
README.md                        ~2000 tokens ✅
QUICK_REFERENCE.md               ~1000 tokens ✅
.api-toolkit-config.md           ~500 tokens ✅ (if exists)
─────────────────────────────────────────────
Total: ~3,500 tokens (PERFECT!)

Other docs available but not auto-loaded
```

## .claudeignore Strategy

Exclude from auto-loading:
```
CHANGELOG.md
IMPROVEMENTS_SUMMARY.md
COMPLETE_SOLUTION_SUMMARY.md
PROJECT_CONFIG_GUIDE.md
INSTALLATION_DETECTION.md
QUICK_START_FLOWCHART.md
tests/
```

## Smart References

Instead of embedding full guides, use pointers:

**In README.md:**
```markdown
# For complete project config guide:
# See PROJECT_CONFIG_GUIDE.md

# For troubleshooting installation:
# See INSTALLATION_DETECTION.md
```

Claude Code can read these files IF NEEDED, but won't load automatically.

## Best Practices

### Do:
✅ Keep README.md and QUICK_REFERENCE.md lean
✅ Use .claudeignore for historical/reference docs
✅ Link to detailed guides instead of embedding
✅ Maintain project-specific `.api-toolkit-config.md` (tiny, high-value)

### Don't:
❌ Auto-load changelog/history files
❌ Embed full guides in quick reference
❌ Duplicate information across files
❌ Load test reports automatically

## Maintenance

When adding new documentation:

1. **Ask**: Does Claude Code need this EVERY conversation?
   - Yes → README.md or QUICK_REFERENCE.md
   - No → Separate file + add to .claudeignore

2. **Check token cost**: Run `wc -l` on file
   - <100 lines → Probably OK to auto-load
   - >200 lines → Should be on-demand only

3. **Test**: Start new conversation, check context usage
   - Goal: <5,000 tokens for all auto-loaded docs

## Current Status

✅ `.claudeignore` created
✅ Historical docs excluded
✅ Essential docs remain lean
✅ Token budget: ~3,500 tokens (was ~500, still efficient!)

The small increase from 500→3,500 tokens is justified because:
- Installation detection instructions (prevents 10 min wasted)
- Project config checks (preserves context)
- Still 180x better than MCP servers (90,000 tokens)!

---

**Target**: Keep auto-loaded docs under 5,000 tokens total
**Current**: ~3,500 tokens (70% of budget, room to grow)
