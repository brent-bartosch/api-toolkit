#!/bin/bash

# API Toolkit Quality Gate
# Blocks commits until tests pass and code quality checks succeed

set -e  # Exit on any error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 API Toolkit Quality Gate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Only run for git commits
if ! echo "$@" | grep -q "git commit"; then
  echo "✓ Not a commit, skipping checks"
  exit 0
fi

# Change to toolkit directory
cd /path/to/api-toolkit

# ═══════════════════════════════════════════════════
# 1. PYTHON SYNTAX CHECK
# ═══════════════════════════════════════════════════
echo ""
echo "▶ Step 1/4: Checking Python syntax..."

python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -n "$python_files" ]; then
  syntax_errors=0
  while IFS= read -r file; do
    if [ -f "$file" ]; then
      python -m py_compile "$file" 2>&1
      if [ $? -ne 0 ]; then
        echo "  ❌ Syntax error in $file"
        syntax_errors=$((syntax_errors + 1))
      fi
    fi
  done <<< "$python_files"

  if [ $syntax_errors -gt 0 ]; then
    echo ""
    echo "❌ BLOCKED: Fix Python syntax errors before committing"
    exit 1
  fi
  echo "  ✅ All Python files have valid syntax"
else
  echo "  ⊘ No Python files changed"
fi

# ═══════════════════════════════════════════════════
# 2. SECURITY CHECKS
# ═══════════════════════════════════════════════════
echo ""
echo "▶ Step 2/4: Security checks..."

# Check for hardcoded credentials
if git diff --cached | grep -iE '(password|api_key|secret|token)\s*=\s*["\x27][^"x27${}]+["\x27]' | grep -v 'SUPABASE_SERVICE_ROLE_KEY\s*='; then
  echo ""
  echo "❌ BLOCKED: Possible hardcoded credentials detected!"
  echo "   Use environment variables instead (.env file)"
  exit 1
fi

# Check for .env file being committed
if git diff --cached --name-only | grep -q '\.env$' && ! git diff --cached --name-only | grep -q '\.env\.example$'; then
  echo ""
  echo "❌ BLOCKED: Attempting to commit .env file with secrets!"
  echo "   Remove .env from staging: git reset HEAD .env"
  exit 1
fi

echo "  ✅ No security issues detected"

# ═══════════════════════════════════════════════════
# 3. CODE QUALITY HINTS (Non-blocking)
# ═══════════════════════════════════════════════════
echo ""
echo "▶ Step 3/4: Code quality hints..."

# Check for print() statements (should use logging)
print_count=$(git diff --cached | grep -E '^\+.*print\(' | grep -v '# OK to print' | wc -l || true)
if [ "$print_count" -gt 0 ]; then
  echo "  ⚠️  Found $print_count print() statement(s) - consider using logging module"
  echo "     (Add '# OK to print' comment if intentional)"
fi

# Check for TODO/FIXME comments
todo_count=$(git diff --cached | grep -E '^\+.*(TODO|FIXME|XXX|HACK)' | wc -l || true)
if [ "$todo_count" -gt 0 ]; then
  echo "  💡 Found $todo_count TODO/FIXME comment(s) - track these as issues?"
fi

echo "  ✅ Quality hints complete"

# ═══════════════════════════════════════════════════
# 4. RUN TESTS (Critical - Blocks if fail)
# ═══════════════════════════════════════════════════
echo ""
echo "▶ Step 4/4: Running tests..."

# Check if any Python service files were modified
service_files=$(git diff --cached --name-only | grep -E 'services/.*\.py$' || true)

if [ -n "$service_files" ]; then
  echo "  🧪 Service files modified, running relevant tests..."

  # Run tests for modified services
  for file in $service_files; do
    service_name=$(echo "$file" | cut -d'/' -f2)
    test_file="tests/test_${service_name}.py"

    if [ -f "$test_file" ]; then
      echo "     Testing $service_name..."
      python -m pytest "$test_file" -v --tb=short 2>&1 | tee /tmp/api-toolkit-test-${service_name}.log

      if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ COMMIT BLOCKED: Tests failed for $service_name"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Fix the failing tests, then try again."
        echo "Test log: /tmp/api-toolkit-test-${service_name}.log"
        echo ""
        exit 1
      fi
    fi
  done

  echo "  ✅ All service tests passed"
else
  echo "  ⊘ No service files modified, skipping tests"
fi

# ═══════════════════════════════════════════════════
# ALL CHECKS PASSED
# ═══════════════════════════════════════════════════
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL QUALITY CHECKS PASSED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Commit allowed ✓"
echo ""

# Create pass file (optional, for compatibility)
touch /tmp/agent-pre-commit-pass

exit 0
