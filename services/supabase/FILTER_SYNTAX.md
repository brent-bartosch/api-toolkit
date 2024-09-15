# 🔍 Supabase Filter Syntax - Complete Reference

## ⚡ Quick Reference (Copy & Paste)

```python
# ALWAYS START WITH DISCOVERY
api = SupabaseAPI('project1')
api.quick_start()  # Shows everything in 5 seconds!

# BASIC FILTERS
filters = {
    'age': 'gte.18',              # age >= 18
    'status': 'eq.active',        # status = 'active'
    'email': 'ilike.%gmail%',     # email ILIKE '%gmail%' (case-insensitive)
    'deleted_at': 'is.null',      # deleted_at IS NULL
    'role': 'in.(admin,user)',    # role IN ('admin', 'user')
}

# QUERY WITH FILTERS
results = api.query('users', filters=filters)
# Returns LIST directly, NOT {'data': [...]}
for user in results:  # NOT results['data']
    print(user['email'])
```

## 📊 Complete Filter Operations

| Operation | Filter Syntax | SQL Equivalent | Example |
|-----------|--------------|----------------|---------|
| **EQUALITY** |
| Equals | `eq.value` | `= value` | `{'status': 'eq.active'}` |
| Not equals | `neq.value` | `!= value` | `{'status': 'neq.deleted'}` |
| **COMPARISON** |
| Greater than | `gt.value` | `> value` | `{'age': 'gt.18'}` |
| Greater or equal | `gte.value` | `>= value` | `{'score': 'gte.80'}` |
| Less than | `lt.value` | `< value` | `{'price': 'lt.100'}` |
| Less or equal | `lte.value` | `<= value` | `{'stock': 'lte.10'}` |
| **PATTERN MATCHING** |
| Like (case-sensitive) | `like.pattern` | `LIKE pattern` | `{'email': 'like.%@gmail.com'}` |
| ILike (case-insensitive) | `ilike.pattern` | `ILIKE pattern` | `{'name': 'ilike.%john%'}` |
| **NULL CHECKS** |
| Is null | `is.null` | `IS NULL` | `{'deleted': 'is.null'}` |
| Is not null | `not.is.null` | `IS NOT NULL` | `{'email': 'not.is.null'}` |
| **BOOLEAN** |
| Is true | `is.true` | `IS TRUE` | `{'active': 'is.true'}` |
| Is false | `is.false` | `IS FALSE` | `{'verified': 'is.false'}` |
| **ARRAYS** |
| In array | `in.(val1,val2)` | `IN (val1, val2)` | `{'status': 'in.(new,pending)'}` |
| Not in array | `not.in.(val1,val2)` | `NOT IN (val1, val2)` | `{'role': 'not.in.(banned,suspended)'}` |
| **RANGES** |
| Range (inclusive) | `gte.start&lte.end` | `BETWEEN start AND end` | Multiple filters needed |
| **TEXT SEARCH** |
| Full text search | `fts.query` | `@@ to_tsquery` | `{'document': 'fts.python tutorial'}` |
| Phrase search | `plfts.query` | `@@ plainto_tsquery` | `{'content': 'plfts.exact phrase'}` |
| **JSON/JSONB** |
| JSON contains | `cs.{json}` | `@> json` | `{'metadata': 'cs.{"type":"premium"}'}` |
| JSON contained by | `cd.{json}` | `<@ json` | `{'tags': 'cd.["a","b","c"]'}` |

## 💡 Common Patterns

### Pattern 1: Finding Records with Partial Text Match
```python
# Find all emails containing 'gmail'
results = api.query('users', filters={
    'email': 'ilike.%gmail%'  # Case-insensitive contains
})

# Find names starting with 'John'
results = api.query('users', filters={
    'name': 'ilike.John%'
})

# Find URLs ending with '.com'
results = api.query('sites', filters={
    'url': 'like.%.com'
})
```

### Pattern 2: Combining Multiple Filters
```python
# All filters are AND'ed together
results = api.query('products', filters={
    'price': 'gte.10',        # price >= 10
    'price': 'lte.100',       # AND price <= 100 (Note: overwrites!)
    'category': 'eq.electronics',  # AND category = 'electronics'
    'in_stock': 'is.true'     # AND in_stock IS TRUE
})

# For complex OR conditions, use raw_query()
results = api.raw_query("""
    SELECT * FROM products 
    WHERE (price >= 10 AND price <= 100)
    OR category = 'sale'
    LIMIT 100
""")
```

### Pattern 3: Null and Boolean Checks
```python
# Find records with no deletion date
active = api.query('records', filters={
    'deleted_at': 'is.null'
})

# Find verified users
verified = api.query('users', filters={
    'email_verified': 'is.true',
    'phone_verified': 'is.true'
})

# Find incomplete profiles
incomplete = api.query('profiles', filters={
    'bio': 'is.null',
    'avatar': 'is.null'
})
```

### Pattern 4: Working with Arrays and Lists
```python
# Find records with specific statuses
results = api.query('orders', filters={
    'status': 'in.(pending,processing,shipped)'
})

# Exclude certain roles
results = api.query('users', filters={
    'role': 'not.in.(banned,suspended,deleted)'
})

# Multiple conditions
results = api.query('products', filters={
    'category': 'in.(electronics,computers)',
    'brand': 'not.in.(unknown,generic)'
})
```

### Pattern 5: Date and Time Filters
```python
from datetime import datetime, timedelta

# Records from last 30 days
thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
results = api.query('events', filters={
    'created_at': f'gte.{thirty_days_ago}'
})

# Records from specific date range
results = api.query('orders', filters={
    'order_date': 'gte.2024-01-01',
    'order_date': 'lte.2024-12-31'  # Note: overwrites previous!
})

# Better approach for date ranges with raw_query
results = api.raw_query("""
    SELECT * FROM orders 
    WHERE order_date >= '2024-01-01' 
    AND order_date <= '2024-12-31'
    LIMIT 1000
""")
```

## 🚨 Common Gotchas

### 1. **Filter Overwriting**
```python
# ❌ WRONG - Second filter overwrites first!
filters = {
    'price': 'gte.10',
    'price': 'lte.100'  # This overwrites 'gte.10'!
}

# ✅ CORRECT - Use raw_query for ranges
results = api.raw_query(
    "SELECT * FROM products WHERE price BETWEEN 10 AND 100"
)
```

### 2. **Pattern Matching Wildcards**
```python
# ❌ WRONG - Missing wildcards
filters = {'email': 'ilike.gmail'}  # Won't match anything

# ✅ CORRECT - Include % wildcards
filters = {'email': 'ilike.%gmail%'}  # Matches *gmail*
```

### 3. **Null Checking Syntax**
```python
# ❌ WRONG
filters = {'deleted': 'null'}      # Doesn't work
filters = {'deleted': 'eq.null'}   # Doesn't work

# ✅ CORRECT
filters = {'deleted': 'is.null'}   # Correct syntax
filters = {'deleted': 'not.is.null'}  # For NOT NULL
```

### 4. **IN Array Syntax**
```python
# ❌ WRONG
filters = {'status': 'in.active,pending'}  # Missing parentheses
filters = {'status': 'in.(active, pending)'}  # No spaces!

# ✅ CORRECT
filters = {'status': 'in.(active,pending)'}  # No spaces between values
```

### 5. **Case Sensitivity**
```python
# ❌ Case-sensitive (might miss records)
filters = {'name': 'like.%John%'}  # Won't match 'john'

# ✅ Case-insensitive
filters = {'name': 'ilike.%john%'}  # Matches 'John', 'JOHN', 'john'
```

## 🔧 Advanced Techniques

### Using QueryBuilder Instead
```python
from api_toolkit.services.supabase.query_helpers import QueryBuilder

# Cleaner syntax, no filter formatting needed
query = (QueryBuilder('users')
    .where('age', '>=', 18)
    .where('status', '=', 'active')
    .contains('email', 'gmail')  # Automatically adds wildcards
    .is_null('deleted_at')
    .in_array('role', ['admin', 'moderator'])
    .order('created_at', desc=True)
    .limit(100))

results = query.execute(api)
```

### Complex Queries with Raw SQL
```python
# When filters aren't enough, use raw SQL
results = api.raw_query("""
    SELECT u.*, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.created_at >= '2024-01-01'
    AND (u.status = 'active' OR u.status = 'premium')
    GROUP BY u.id
    HAVING COUNT(o.id) > 5
    ORDER BY order_count DESC
    LIMIT 100
""")
```

## 📋 Quick Diagnostic

```python
# If filters aren't working, debug like this:

# 1. Check column names
info = api.discover('your_table')
print("Available columns:", info['column_names'])

# 2. Check data types
for col in info['columns']:
    print(f"{col['name']}: {col['type']}")

# 3. Try without filters first
all_records = api.query('your_table', limit=5)
print("Sample data:", all_records)

# 4. Add filters one by one
test1 = api.query('your_table', filters={'col1': 'eq.value'})
print(f"With filter 1: {len(test1)} results")

test2 = api.query('your_table', filters={
    'col1': 'eq.value',
    'col2': 'gte.10'
})
print(f"With filters 1+2: {len(test2)} results")
```

## 🎯 Best Practices

1. **Always discover first**: Use `api.quick_start()` or `api.discover('table')`
2. **Start simple**: Test with one filter before adding more
3. **Use ilike for text**: Case-insensitive is usually what you want
4. **Check for nulls**: Many queries fail due to unexpected NULL values
5. **Use raw_query for complex logic**: Don't fight with filter syntax for OR conditions
6. **Verify column names**: Most errors are typos in column names
7. **Test with limits**: Always use `limit=10` when testing filters

## 🆘 When All Else Fails

```python
# The nuclear option - see everything
api = SupabaseAPI('project1')

# 1. Start fresh with quick_start
api.quick_start()

# 2. Discover the specific table
info = api.discover('your_table')
print(json.dumps(info, indent=2))

# 3. Use raw SQL for exact control
results = api.raw_query("SELECT * FROM your_table LIMIT 10")

# 4. Check the error message carefully
try:
    api.query('table', filters={'bad': 'filter'})
except Exception as e:
    print(f"Error details: {e}")
    # Often shows the exact column name issue
```

---
Remember: Filters are powerful but filter syntax can be tricky. When in doubt, use `api.discover()` and start with simple queries!