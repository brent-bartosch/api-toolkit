# Code Execution MCP Server

**Following Anthropic's pattern for efficient large-scale data processing**

## 🎯 The Problem This Solves

Traditional MCP servers have two major issues:

1. **Context Overload**: Loading all tool definitions upfront (90,000-150,000 tokens)
2. **Token Waste**: Large datasets returned to Claude consume massive tokens

## ✨ Anthropic's Solution (Implemented Here)

Instead of returning large datasets to Claude, **execute Python code in a sandbox** that:
- Queries and processes data locally
- Returns only final results (summary/analysis)
- Saves 90-95% of tokens on large dataset operations

### Example: The Difference

**Traditional MCP** (~50,000 tokens):
```
Claude: query_supabase('project1', 'leads')
→ Returns 1000 leads = 50,000 tokens
Claude: [Processes in conversation]
```

**Code Execution MCP** (~500 tokens):
```python
# Code executes in sandbox
api = SupabaseAPI('project1')
leads = api.query('leads', limit=1000)

# Process here (NO tokens used for intermediate data!)
high_value = [l for l in leads if l.get('score', 0) > 90]
analysis = {
    'total': len(leads),
    'high_value_count': len(high_value),
    'avg_score': sum(l['score'] for l in leads) / len(leads),
    'top_10': high_value[:10]
}

print(analysis)  # Only this small summary returned
```

**Result**: 500 tokens instead of 50,000 (99% reduction!)

## 🚀 Features

### 1. **Code Execution** (`execute_python`)
Execute Python with full API toolkit access:
- SupabaseAPI for all 3 projects
- QueryBuilder for complex queries
- Standard libraries (json, datetime, collections, etc.)
- Secure sandbox environment

### 2. **Progressive Tool Discovery**
Load tool documentation on-demand, not upfront:
- `discover_services` - List available services (minimal)
- `get_service_info` - Get details at 3 levels (basic/standard/full)
- `get_quick_start` - Minimal working example
- `search_tools` - Find tools by keyword
- `get_code_examples` - Get specific examples

### 3. **Token Optimization**
- **Tool definitions**: ~2,000 tokens (vs 150,000 traditional)
- **Data processing**: 0 tokens (happens in sandbox)
- **Results only**: 100-1,000 tokens (vs 10,000-100,000)

## 📦 Installation

### 1. Install Dependencies

```bash
cd /path/to/api-toolkit/mcp-server-code-exec
pip install -r requirements.txt
```

### 2. Configure Claude Code

Add to `~/.config/claude/mcp.json`:

```json
{
  "mcpServers": {
    "api-toolkit-code-exec": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server-code-exec/server.py"]
    }
  }
}
```

### 3. Restart Claude Code

### 4. Verify

```
You: "What MCP servers are available?"
Claude: [Should show api-toolkit-code-exec]

You: "Discover available services"
Claude: [Calls discover_services, shows supabase, smartlead, etc.]
```

## 🎓 Usage Patterns

### Pattern 1: Progressive Discovery

```
User: "What services are available?"
Claude: [Calls discover_services]
Result: {services: ['supabase', 'smartlead', 'metabase', ...]}

User: "Tell me about supabase"
Claude: [Calls get_service_info('supabase', 'basic')]
Result: {files: ['api.py', 'query_helpers.py', ...]}

User: "Show me supabase methods"
Claude: [Calls get_service_info('supabase', 'standard')]
Result: {class: 'SupabaseAPI', methods: ['query', 'discover', ...]}

User: "Give me a quick example"
Claude: [Calls get_quick_start('supabase')]
Result: [Working code snippet]
```

### Pattern 2: Simple Data Query

```
User: "Get 10 leads from project1 database"
Claude: [Calls execute_python]
Code:
api = SupabaseAPI('project1')
leads = api.query('leads', limit=10)
print(f"Found {len(leads)} leads")
for lead in leads[:5]:
    print(f"  - {lead.get('email')}: score {lead.get('score')}")

Output: [5 leads shown]
```

### Pattern 3: Large Dataset Analysis

```
User: "Analyze all leads in smoothed and show me score distribution"
Claude: [Calls execute_python]
Code:
api = SupabaseAPI('project1')

# Query large dataset
leads = api.query('leads', limit=10000)
print(f"Analyzing {len(leads)} leads...")

# Process in sandbox (NO tokens for this!)
from collections import Counter
scores = [l.get('score', 0) for l in leads]

analysis = {
    'total_leads': len(leads),
    'avg_score': sum(scores) / len(scores),
    'score_distribution': {
        '0-50': len([s for s in scores if s < 50]),
        '50-70': len([s for s in scores if 50 <= s < 70]),
        '70-90': len([s for s in scores if 70 <= s < 90]),
        '90-100': len([s for s in scores if s >= 90])
    },
    'top_10_leads': sorted(leads, key=lambda x: x.get('score', 0), reverse=True)[:10]
}

print(json.dumps(analysis, indent=2))

Output: [Summary only - maybe 1000 tokens vs 50,000!]
```

### Pattern 4: Complex Multi-Step Operations

```python
# Query multiple tables and join
api = SupabaseAPI('project1')

# Get brands
brands = api.query('brands', filters={'status': 'eq.active'})
brand_dict = {b['id']: b for b in brands}

# Get leads for those brands
leads = api.query('leads', limit=5000)

# Join and analyze (all in sandbox - no tokens!)
lead_by_brand = {}
for lead in leads:
    brand_id = lead.get('brand_id')
    if brand_id in brand_dict:
        brand_name = brand_dict[brand_id]['name']
        if brand_name not in lead_by_brand:
            lead_by_brand[brand_name] = []
        lead_by_brand[brand_name].append(lead)

# Return summary
summary = {
    brand: {
        'total_leads': len(leads),
        'avg_score': sum(l.get('score', 0) for l in leads) / len(leads),
        'high_quality': len([l for l in leads if l.get('score', 0) > 80])
    }
    for brand, leads in lead_by_brand.items()
}

print(json.dumps(summary, indent=2))
```

### Pattern 5: Call Deno Edge Functions

```python
# Invoke serverless function with data processing
api = SupabaseAPI('project1')

# Get leads that need processing
leads = api.query('leads', filters={'status': 'eq.pending'}, limit=100)

results = []
for lead in leads[:10]:  # Process 10 at a time
    result = api.invoke_function('process-lead', {
        'lead_id': lead['id'],
        'action': 'verify_email'
    })
    results.append(result)

# Summarize results
summary = {
    'processed': len(results),
    'verified': len([r for r in results if r.get('verified')]),
    'failed': len([r for r in results if r.get('error')])
}

print(json.dumps(summary, indent=2))
```

## 🔒 Security

The sandbox provides:
- **Limited built-ins**: Only safe functions (no eval, exec, file I/O)
- **Timeout**: 60 second max execution time
- **Output limit**: 100KB max output size
- **No system access**: Cannot access filesystem, network (except via API toolkit)
- **Safe imports only**: Restricted to whitelisted modules

## 📊 Token Comparison

| Operation | Traditional MCP | Code Execution | Savings |
|-----------|-----------------|----------------|---------|
| **Tool Definitions** | 150,000 | 2,000 | 98.7% |
| **Query 1000 rows** | 50,000 | 500 | 99% |
| **Complex analysis** | 75,000 | 1,000 | 98.7% |
| **Multi-table join** | 100,000 | 1,500 | 98.5% |

## 🎯 When to Use Each Approach

### Use Code Execution MCP When:
- ✅ Processing > 100 rows
- ✅ Multiple queries/joins needed
- ✅ Complex data transformations
- ✅ Statistical analysis
- ✅ Large dataset operations

### Use Direct Tools MCP When:
- ✅ Simple queries (< 100 rows)
- ✅ Single operations
- ✅ Metadata queries
- ✅ Discovery/exploration

### Use Slash Commands When:
- ✅ Learning syntax
- ✅ Exploring capabilities
- ✅ Getting examples

## 🛠️ Available Tools

| Tool | Description | Tokens |
|------|-------------|--------|
| `execute_python` | Run Python code in sandbox | ~400 |
| `discover_services` | List services (minimal) | ~200 |
| `get_service_info` | Service details (3 levels) | 200-1000 |
| `get_quick_start` | Working code example | ~300 |
| `search_tools` | Search by keyword | ~200 |
| `get_code_examples` | Get examples | ~500 |

**Total**: ~2,000 tokens (vs 150,000 for traditional)

## 🔄 Workflow Example

Real-world workflow combining all features:

```
1. Discovery
   User: "What can I do with leads?"
   → discover_services()
   → get_service_info('supabase', 'basic')
   → get_quick_start('supabase')

2. Exploration
   Code:
   api = SupabaseAPI('project1')
   info = api.discover('leads')
   print(json.dumps(info, indent=2))

3. Analysis
   Code:
   leads = api.query('leads', limit=5000)
   # Complex analysis here...
   print(summary)

4. Action
   Code:
   for lead in high_value_leads:
       api.invoke_function('send-email', {'lead_id': lead['id']})
```

## 📚 Examples Directory

See `/examples/` for complete working examples:
- `simple_query.py` - Basic querying
- `large_dataset.py` - Processing 10k+ rows
- `multi_table.py` - Joining multiple tables
- `edge_functions.py` - Using Deno functions
- `rpc_functions.py` - PostgreSQL functions

## 🆘 Troubleshooting

### "Module not found"
Run from correct directory:
```bash
cd /path/to/api-toolkit
python mcp-server-code-exec/server.py
```

### "Code execution failed"
Check available imports:
```python
# Available in sandbox:
SupabaseAPI, QueryBuilder
json, datetime, collections, re, math, statistics
```

### "Connection error"
Verify environment:
```bash
python test-env-loading.py
```

## 🎉 Benefits Summary

1. **98.7% token reduction** on tool definitions
2. **99% token reduction** on large dataset operations
3. **Progressive disclosure** - load only what you need
4. **Data processing in sandbox** - no intermediate token cost
5. **Complex operations** - loops, joins, transformations
6. **Secure execution** - sandboxed environment

---

**This is the recommended approach for working with large datasets or complex operations.**

For simple queries, use the direct tools MCP (`mcp-server/`).
For documentation, use slash commands (`.claude/commands/`).
For everything else, use this code execution MCP! 🚀
