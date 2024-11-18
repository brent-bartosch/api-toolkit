#!/bin/bash

# Best Practices Hints (Non-blocking)
# Provides gentle guidance after Write/Edit tool calls

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Only run for Write/Edit tools
if [[ "$TOOL_NAME" != "Write" ]] && [[ "$TOOL_NAME" != "Edit" ]]; then
  exit 0
fi

# Extract file path from tool args
file_path=$(echo "$TOOL_ARGS" | grep -oE '/[^"]+\.py' | head -1)

if [ -z "$file_path" ] || [ ! -f "$file_path" ]; then
  exit 0
fi

# ═══════════════════════════════════════════════════
# HINT 1: Error Handling
# ═══════════════════════════════════════════════════
if ! grep -q "try:" "$file_path" && ! grep -q "except" "$file_path"; then
  # Check if file has network calls or file operations
  if grep -qE '(requests\.|open\(|SupabaseAPI|MetabaseAPI)' "$file_path"; then
    echo ""
    echo "💡 HINT: Consider adding error handling"
    echo "   File: $file_path"
    echo "   Detected: Network/file operations without try/except"
    echo "   Tip: Wrap API calls in try/except blocks"
  fi
fi

# ═══════════════════════════════════════════════════
# HINT 2: Docstrings
# ═══════════════════════════════════════════════════
if grep -qE '^def |^class ' "$file_path"; then
  # Count functions/classes vs docstrings
  func_count=$(grep -cE '^def |^class ' "$file_path" || echo "0")
  docstring_count=$(grep -cE '""".*"""' "$file_path" || echo "0")

  if [ "$func_count" -gt "$docstring_count" ]; then
    echo ""
    echo "💡 HINT: Some functions/classes may need docstrings"
    echo "   File: $file_path"
    echo "   Functions/Classes: $func_count, Docstrings: $docstring_count"
  fi
fi

# ═══════════════════════════════════════════════════
# HINT 3: Type Hints
# ═══════════════════════════════════════════════════
if grep -qE '^def ' "$file_path"; then
  # Check if functions have type hints
  funcs_without_types=$(grep -E '^def [^(]+\([^)]*\):' "$file_path" | grep -v ' -> ' | wc -l || echo "0")

  if [ "$funcs_without_types" -gt 0 ]; then
    echo ""
    echo "💡 HINT: Consider adding type hints to functions"
    echo "   File: $file_path"
    echo "   Functions without return types: $funcs_without_types"
    echo "   Example: def query(table: str) -> List[Dict]:"
  fi
fi

# ═══════════════════════════════════════════════════
# HINT 4: Logging vs Print
# ═══════════════════════════════════════════════════
if grep -qE '^\s+print\(' "$file_path" && ! grep -q "import logging" "$file_path"; then
  print_count=$(grep -cE '^\s+print\(' "$file_path" || echo "0")

  if [ "$print_count" -gt 2 ]; then
    echo ""
    echo "💡 HINT: Consider using logging instead of print()"
    echo "   File: $file_path"
    echo "   Print statements: $print_count"
    echo "   Tip: import logging; logger = logging.getLogger(__name__)"
  fi
fi

# ═══════════════════════════════════════════════════
# HINT 5: API Toolkit Patterns
# ═══════════════════════════════════════════════════

# Check for manual pagination (should use fetch_all)
if grep -qE 'offset.*limit|while.*query' "$file_path"; then
  if ! grep -q "fetch_all" "$file_path"; then
    echo ""
    echo "💡 HINT: Manual pagination detected"
    echo "   File: $file_path"
    echo "   Tip: Use api.fetch_all() for automatic pagination"
  fi
fi

# Check for len(query(...)) (should use count)
if grep -qE 'len\(.*\.query\(' "$file_path"; then
  echo ""
  echo "💡 HINT: Consider using api.count() instead of len(api.query())"
  echo "   File: $file_path"
  echo "   Benefit: 10-100x faster for large datasets"
fi

# Check for query checking existence (should use exists)
if grep -qE 'if.*len\(.*\.query\(.*\)\s*>\s*0' "$file_path"; then
  echo ""
  echo "💡 HINT: Consider using api.exists() for existence checks"
  echo "   File: $file_path"
  echo "   Example: if api.exists('table', filters): ..."
fi

# All hints are non-blocking
exit 0
