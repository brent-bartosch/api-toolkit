# API Toolkit - LLM/Agent Usage Improvements

**Date:** 2025-11-18
**Based on:** Real-world usage session with Claude Code
**Status:** Recommendations for implementation

---

## Executive Summary

During a multi-hour session working with the Faire lead generation project, several UX pain points emerged when using the API toolkit. **None of these are Supabase limitations** - they're all toolkit design decisions that can be improved to make LLM/agent usage smoother.

**Impact:** These changes would have saved ~20-30 minutes of debugging and trial-and-error during the session.

---

## Issue #1: Hidden 1,000 Row Limit

### Problem

**Location:** `services/supabase/api.py` line 418

```python
# Current code
def query(self, table, limit=None, ...):
    # ... other code ...
    limit = min(limit, 1000)  # Silently caps at 1,000 rows
```

**What happened:**
- LLM tried to fetch 8,225 brands
- Got only 1,000 rows back
- No error, no warning
- Took 3+ attempts to figure out what was happening
- LLM had to manually implement pagination

**Why it's confusing:**
- Supabase itself has NO 1,000 row limit
- Limit is a toolkit safety feature (good intent!)
- But it's undocumented and silent

### Solution

Make the limit **configurable** and **visible**:

```python
# In services/supabase/api.py

class SupabaseAPI:
    def __init__(self, project='default', max_row_limit=1000):
        """
        Initialize Supabase API client.

        Args:
            project: Project name ('project1', 'project2', 'project3')
            max_row_limit: Maximum rows to return in a single query (default: 1000)
                          Set to None for unlimited (use with caution!)
        """
        self.project = project
        self.max_row_limit = max_row_limit
        # ... rest of init ...

    def query(self, table, select='*', filters=None, limit=None, offset=None, order_by=None):
        """
        Query a table with optional filters.

        Args:
            limit: Max rows to return. If exceeds max_row_limit, will be capped with a warning.

        Returns:
            List of records (NOT {'data': [...]})
        """
        # Check if limit exceeds max
        if self.max_row_limit and limit and limit > self.max_row_limit:
            print(f"⚠️  WARNING: Requested {limit:,} rows, but max_row_limit is {self.max_row_limit:,}")
            print(f"    Results will be capped. Consider using fetch_all() for large datasets.")
            limit = self.max_row_limit
        elif self.max_row_limit and not limit:
            limit = self.max_row_limit

        # ... rest of query logic ...
```

### Usage Examples

```python
# Option 1: Use default limit (1,000 rows)
api = SupabaseAPI('project1')
brands = api.query('brands')  # Gets 1,000 max, WITH WARNING if more exist

# Option 2: Increase limit for this instance
api = SupabaseAPI('project1', max_row_limit=10000)
brands = api.query('brands')  # Gets up to 10,000 rows

# Option 3: Disable limit (use with caution!)
api = SupabaseAPI('project1', max_row_limit=None)
brands = api.query('brands')  # Gets ALL rows (could be millions!)

# Option 4: Use new fetch_all() method (see Issue #2)
api = SupabaseAPI('project1')
brands = api.fetch_all('brands')  # Auto-paginates, gets all 8,225 rows
```

---

## Issue #2: No Built-in Pagination Helper

### Problem

**What happened:**
- LLM needed all 8,225 brands
- Hit the 1,000 row limit
- Had to manually write pagination code:
  ```python
  def fetch_all_sql(query, description):
      all_data = []
      offset = 0
      page_size = 1000
      while True:
          paginated_query = f"{query} LIMIT {page_size} OFFSET {offset}"
          batch = api.raw_query(paginated_query)
          if not batch or len(batch) < page_size:
              break
          all_data.extend(batch)
          offset += page_size
      return all_data
  ```

**Why it's a problem:**
- Common use case (fetch all records from a table)
- Every LLM/user has to reinvent this wheel
- Easy to get wrong (forgot to check `len(batch) < page_size`, infinite loops, etc.)

### Solution

Add a `fetch_all()` method to `SupabaseAPI`:

```python
# In services/supabase/api.py

class SupabaseAPI:
    # ... existing methods ...

    def fetch_all(self, table, select='*', filters=None, order_by=None, verbose=True):
        """
        Fetch ALL records from a table using automatic pagination.

        This method bypasses max_row_limit and fetches the entire dataset
        using efficient pagination under the hood.

        Args:
            table: Table name
            select: Columns to select (default: all)
            filters: Dict of filters (e.g., {'state': 'CA'})
            order_by: Column to sort by (e.g., 'created_at')
            verbose: Print progress updates (default: True)

        Returns:
            List of ALL records from the table

        Example:
            api = SupabaseAPI('project1')
            all_brands = api.fetch_all('brands')  # Gets all 8,225 brands
            ca_brands = api.fetch_all('brands', filters={'state': 'CA'})

        Warning:
            This can return LARGE datasets. Use filters to narrow results when possible.
        """
        all_data = []
        offset = 0
        page_size = 1000

        if verbose:
            print(f"📥 Fetching all records from '{table}'...")

        while True:
            # Build query using Supabase client's .range() method
            query = self.supabase.table(table).select(select)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    # Support filter syntax like 'status.eq.active'
                    if '.' in key:
                        parts = key.split('.')
                        col = parts[0]
                        op = parts[1] if len(parts) > 1 else 'eq'
                        query = query.filter(col, op, value)
                    else:
                        query = query.filter(key, 'eq', value)

            # Apply ordering
            if order_by:
                if order_by.startswith('-'):
                    query = query.order(order_by[1:], desc=True)
                else:
                    query = query.order(order_by)

            # Fetch page using .range()
            try:
                result = query.range(offset, offset + page_size - 1).execute()
            except Exception as e:
                print(f"❌ Error fetching data: {e}")
                break

            # Check if we got data
            if not result.data:
                break

            all_data.extend(result.data)

            # Progress update
            if verbose and len(all_data) % 5000 == 0:
                print(f"   ... fetched {len(all_data):,} records so far")

            # Check if we're done (got less than page_size)
            if len(result.data) < page_size:
                break

            offset += page_size

        if verbose:
            print(f"✅ Fetched {len(all_data):,} total records from '{table}'")

        return all_data
```

### Usage Examples

```python
# Simple: Get all records
api = SupabaseAPI('project1')
all_brands = api.fetch_all('brands')
# Output:
# 📥 Fetching all records from 'brands'...
# ✅ Fetched 8,225 total records from 'brands'

# With filters
ca_brands = api.fetch_all('brands', filters={'state': 'CA'})

# With ordering
recent_brands = api.fetch_all('brands', order_by='-created_at')

# Select specific columns
brand_names = api.fetch_all('brands', select='token, name')

# Silent mode
all_brands = api.fetch_all('brands', verbose=False)
```

---

## Issue #3: Unclear When to Use SQL vs Methods

### Problem

**What happened:**
- LLM wasn't sure when to use `api.query()` vs `api.raw_query()`
- Defaulted to SQL because it was more familiar
- Missed out on benefits of typed methods

**Why it's confusing:**
- Both work for simple queries
- No clear guidance in docs
- Each has different trade-offs

### Solution

Add a decision guide to `QUICK_REFERENCE.md`:

```markdown
# Quick Reference - API Toolkit

## When to Use What

### Use `api.query()` when:
✅ Simple filters (1-3 conditions)
✅ Need type safety and autocomplete
✅ Working with < 1,000 rows
✅ Standard CRUD operations

**Example:**
```python
api = SupabaseAPI('project1')

# Simple filter
ca_brands = api.query('brands', filters={'state': 'CA'}, limit=100)

# Multiple filters
active_ca = api.query('brands',
                     filters={'state': 'CA', 'status': 'active'},
                     order_by='name')
```

### Use `api.fetch_all()` when:
✅ Need ALL records from a table
✅ Dataset might be > 1,000 rows
✅ Want automatic pagination
✅ Simple queries with optional filters

**Example:**
```python
# Get everything
all_brands = api.fetch_all('brands')

# With filters
ca_brands = api.fetch_all('brands', filters={'state': 'CA'})

# Specific columns only
brand_tokens = api.fetch_all('brands', select='token, name')
```

### Use `api.raw_query()` when:
✅ Complex JOINs across multiple tables
✅ CTEs (WITH clauses) or window functions
✅ Custom aggregations (GROUP BY, COUNT, AVG, etc.)
✅ Need full PostgreSQL features
✅ Performance optimization (indexes, EXPLAIN)

**Example:**
```python
# Complex aggregation
stats = api.raw_query("""
    SELECT
        state,
        COUNT(*) as total_brands,
        AVG(product_count) as avg_products,
        SUM(followers) as total_followers
    FROM brands
    WHERE status = 'active'
    GROUP BY state
    ORDER BY total_followers DESC
    LIMIT 10
""")

# JOIN across tables
enriched = api.raw_query("""
    SELECT
        b.name,
        b.state,
        i.followers,
        w.emails
    FROM brands b
    LEFT JOIN instagram_profiles i ON b.token = i.brand_token
    LEFT JOIN brand_website_contacts w ON b.token = w.brand_token
    WHERE b.state = 'CA'
    ORDER BY i.followers DESC
    LIMIT 100
""")

# CTE with window functions
ranked = api.raw_query("""
    WITH ranked_brands AS (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY state ORDER BY followers DESC) as state_rank
        FROM brands
    )
    SELECT * FROM ranked_brands WHERE state_rank <= 10
""")
```

### Use `api.discover()` when:
✅ Exploring a new database
✅ Checking table schema before querying
✅ LLM needs to understand available data

**Example:**
```python
# Explore all tables
api.discover()

# Explore specific table
api.discover('brands')  # Shows columns, types, sample data
```

## Token Cost Comparison

| Method | Approx Tokens | Best For |
|--------|---------------|----------|
| `api.query()` | ~500 | Simple queries |
| `api.fetch_all()` | ~600 | Get all records |
| `api.raw_query()` | ~600 | Complex SQL |
| `api.discover()` | ~800 | Schema exploration |
| MCP Servers | ~90,000 ❌ | (Avoid - 180x more expensive!) |
```

---

## Issue #4: Better Error Messages

### Problem

**Current behavior:**
```python
api = SupabaseAPI('project1')
brands = api.query('brands', limit=10000)
# Silently returns 1,000 rows
```

**What LLM expected:**
- Either get 10,000 rows
- OR get an error/warning explaining the limit

### Solution

Add informative warnings:

```python
# In api.py query() method

if self.max_row_limit and limit and limit > self.max_row_limit:
    print(f"⚠️  WARNING: Requested {limit:,} rows, but max_row_limit is {self.max_row_limit:,}")
    print(f"    Results will be capped at {self.max_row_limit:,}.")
    print(f"    💡 TIP: Use api.fetch_all('{table}') to get all records via pagination")
    limit = self.max_row_limit
```

**Output:**
```
⚠️  WARNING: Requested 10,000 rows, but max_row_limit is 1,000
    Results will be capped at 1,000.
    💡 TIP: Use api.fetch_all('brands') to get all records via pagination
```

---

## Implementation Checklist

### Code Changes

- [ ] **api.py** - Add `max_row_limit` parameter to `__init__()`
- [ ] **api.py** - Add warning in `query()` when limit exceeds max
- [ ] **api.py** - Add `fetch_all()` method with pagination
- [ ] **api.py** - Update docstrings with examples

### Documentation Updates

- [ ] **QUICK_REFERENCE.md** - Add "When to Use What" section
- [ ] **QUICK_REFERENCE.md** - Add `fetch_all()` examples
- [ ] **QUICK_REFERENCE.md** - Add token cost comparison
- [ ] **README.md** - Update intro to mention `fetch_all()`
- [ ] **CHANGELOG.md** - Document v2.1 changes

### Testing

- [ ] Test `max_row_limit` parameter works
- [ ] Test `fetch_all()` with small dataset (< 1,000 rows)
- [ ] Test `fetch_all()` with large dataset (> 5,000 rows)
- [ ] Test warning message displays correctly
- [ ] Test `fetch_all()` with filters
- [ ] Test `fetch_all()` with ordering

---

## Example: Before vs After

### Before (Current State)

```python
# LLM has to figure out pagination manually
api = SupabaseAPI('project1')

# Tries to get all brands
brands = api.query('brands', limit=10000)
print(f"Got {len(brands)} brands")  # Output: Got 1000 brands (⚠️ WRONG!)

# LLM realizes something is wrong, has to implement pagination:
def fetch_all_manually():
    all_data = []
    offset = 0
    while True:
        batch = api.raw_query(f"SELECT * FROM brands LIMIT 1000 OFFSET {offset}")
        if not batch:
            break
        all_data.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return all_data

brands = fetch_all_manually()
print(f"Got {len(brands)} brands")  # Output: Got 8225 brands ✅
```

**Time wasted:** ~15-20 minutes debugging + implementing pagination

### After (With Improvements)

```python
# Option 1: Use fetch_all() (recommended)
api = SupabaseAPI('project1')
brands = api.fetch_all('brands')
# Output:
# 📥 Fetching all records from 'brands'...
# ✅ Fetched 8,225 total records from 'brands'
print(f"Got {len(brands)} brands")  # Got 8225 brands ✅

# Option 2: Increase limit with warning
api = SupabaseAPI('project1')
brands = api.query('brands', limit=10000)
# Output:
# ⚠️  WARNING: Requested 10,000 rows, but max_row_limit is 1,000
#     Results will be capped at 1,000.
#     💡 TIP: Use api.fetch_all('brands') to get all records via pagination
print(f"Got {len(brands)} brands")  # Got 1000 brands (but NOW I KNOW why!)

# Option 3: Configure higher limit
api = SupabaseAPI('project1', max_row_limit=10000)
brands = api.query('brands')  # Gets up to 10,000 rows
```

**Time saved:** ~15-20 minutes

---

## Additional Nice-to-Haves

### 1. Add `count()` Helper

```python
def count(self, table, filters=None):
    """
    Get count of records in a table.

    Example:
        total_brands = api.count('brands')
        ca_brands = api.count('brands', filters={'state': 'CA'})
    """
    query = self.supabase.table(table).select('*', count='exact')

    if filters:
        for key, value in filters.items():
            query = query.filter(key, 'eq', value)

    result = query.execute()
    return result.count
```

### 2. Add `exists()` Helper

```python
def exists(self, table, filters):
    """
    Check if any records match filters.

    Example:
        if api.exists('brands', {'name': 'Nike'}):
            print("Nike exists!")
    """
    result = self.query(table, filters=filters, limit=1)
    return len(result) > 0
```

### 3. Add Progress Callback to `fetch_all()`

```python
def fetch_all(self, table, ..., progress_callback=None):
    """
    Args:
        progress_callback: Function called with (current_count, total_count)
    """
    while True:
        # ... fetch logic ...

        if progress_callback:
            # Estimate total (could query count first)
            progress_callback(len(all_data), estimated_total)
```

---

## Summary

These improvements would make the API toolkit significantly more LLM-friendly:

1. **Configurable limits** - No more silent truncation
2. **Built-in pagination** - Common use case becomes one-liner
3. **Clear guidance** - LLMs know when to use which method
4. **Better errors** - Informative warnings guide LLMs to solutions

**Estimated implementation time:** 2-3 hours
**Estimated time saved per LLM session:** 15-30 minutes
**ROI:** Very high

---

## Contact

For questions or implementation help, reference this document from the session on 2025-11-18 working on the Faire lead generation website consolidation task.
