# API Toolkit MCP Server

**Lightweight MCP server (~500 tokens) for direct tool calling with API toolkit.**

**Services:** Supabase (7 tools) + Shopify (5 tools) = 12 total tools

## 🎯 Problem Solved

Instead of Claude generating Python code that you have to execute, the MCP server enables **direct tool calling**:

### Before (Slash Commands)
```
User: "Get high-scoring leads"
Claude: [Generates Python code]
User: [Has to run the Python code]
```

### After (MCP Server)
```
User: "Get high-scoring leads"
Claude: [Directly calls: query_supabase('project1', 'leads', {'score': 'gte.80'})]
Result: [Data returned immediately]
```

## 📊 Token Comparison

| Approach | Context Tokens | Tool Calling? |
|----------|----------------|---------------|
| Bad MCP (docs in tools) | 90,000 | ✅ Yes |
| Slash commands | 1,000 | ❌ No |
| **This MCP Server** | **~500** | **✅ Yes** |

**Note:** ~300 tokens for Supabase tools only, ~500 with Shopify tools added

## 🚀 Installation

### 1. Install MCP Dependencies

```bash
cd /path/to/api-toolkit/mcp-server
pip install -r requirements.txt
```

### 2. Configure Claude Code

Add to your Claude Code MCP configuration (`~/.config/claude/mcp.json` or project `.claude/mcp.json`):

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}",
        "SUPABASE_URL_2": "${SUPABASE_URL_2}",
        "SUPABASE_SERVICE_ROLE_KEY_2": "${SUPABASE_SERVICE_ROLE_KEY_2}",
        "SUPABASE_URL_3": "${SUPABASE_URL_3}",
        "SUPABASE_SERVICE_ROLE_KEY_3": "${SUPABASE_SERVICE_ROLE_KEY_3}"
      }
    }
  }
}
```

### 3. Test the Server

```bash
# Test Supabase tools directly
python tools/supabase_tools.py

# Test the MCP server (requires MCP protocol client)
python server.py
```

## 🛠️ Available Tools

### Supabase (7 tools)

**Read/Write access to 3 Supabase projects**

1. **query_supabase** - Query tables with filters
   ```python
   query_supabase(
       project='project1',
       table='leads',
       filters={'score': 'gte.80'},
       limit=20
   )
   ```

2. **supabase_discover** - List tables or get schema
   ```python
   # List all tables
   supabase_discover(project='project1')

   # Get table schema
   supabase_discover(project='project1', table='leads')
   ```

3. **supabase_raw_query** - Execute raw SQL
   ```python
   supabase_raw_query(
       project='project1',
       sql='SELECT * FROM leads WHERE score > 80 LIMIT 10'
   )
   ```

4. **supabase_insert** - Insert records
   ```python
   supabase_insert(
       project='project1',
       table='leads',
       data={'email': 'test@example.com', 'score': 85}
   )
   ```

5. **supabase_update** - Update records
   ```python
   supabase_update(
       project='project1',
       table='leads',
       filters={'id': 'eq.123'},
       data={'status': 'contacted'}
   )
   ```

6. **supabase_rpc** - Call PostgreSQL functions
   ```python
   supabase_rpc(
       project='project1',
       function_name='calculate_score',
       params={'lead_id': 123}
   )
   ```

7. **supabase_invoke_function** - Call Deno Edge Functions
   ```python
   supabase_invoke_function(
       project='project1',
       function_name='process-lead',
       body={'lead_id': 123, 'action': 'verify'},
       method='POST'
   )
   ```

## 📋 Projects Available

### Supabase Projects

| Project | Description | Common Tables |
|---------|-------------|---------------|
| **smoothed** | Lead Generation | brands, leads, scraping_results |
| **blingsting** | CRM System | customers, orders, products |
| **scraping** | Web Project 3 | scrape_guide, scrape_results, scrape_queue |

### Shopify (5 tools)

1. **get_shopify_products** - List products with filters
   ```python
   get_shopify_products(
       status='active',           # active, draft, archived
       vendor='Nike',
       product_type='Sneakers',
       limit=50
   )
   ```

2. **get_shopify_product** - Get single product by ID
   ```python
   get_shopify_product(
       product_id=1234567890,
       fields='id,title,variants,vendor'  # Optional
   )
   ```

3. **get_shopify_orders** - List orders with filters
   ```python
   get_shopify_orders(
       status='any',              # open, closed, cancelled, any
       financial_status='paid',   # authorized, pending, paid, etc.
       fulfillment_status='shipped',
       created_at_min='2024-01-01T00:00:00Z',
       limit=50
   )
   ```

4. **get_shopify_order** - Get single order by ID
   ```python
   get_shopify_order(
       order_id=1234567890,
       fields='id,order_number,total_price,customer'  # Optional
   )
   ```

5. **shopify_discover** - Test connection and show available resources
   ```python
   shopify_discover()
   # Returns store info and available tools
   ```

## 🎓 Usage Examples

### Example 1: Query with Discovery

```
User: "Show me the schema for the leads table in smoothed"
Claude: [Calls supabase_discover('project1', 'leads')]
Result: {columns: [...], sample_data: [...]}

User: "Get leads with score over 80"
Claude: [Calls query_supabase('project1', 'leads', {'score': 'gte.80'})]
Result: [10 leads returned]
```

### Example 2: Complex Query

```
User: "Get high-scoring leads from smoothed, ordered by score"
Claude: [Calls query_supabase('project1', 'leads', {
    'score': 'gte.80',
    'status': 'eq.new'
}, order='-score', limit=20)]
Result: [20 leads returned, ordered by score desc]
```

### Example 3: Call Edge Function

```
User: "Process lead 123 with the verify action"
Claude: [Calls supabase_invoke_function('project1', 'process-lead', {
    'lead_id': 123,
    'action': 'verify'
})]
Result: {success: true, verified: true}
```

### Example 4: Call PostgreSQL Function

```
User: "Calculate score for lead 123"
Claude: [Calls supabase_rpc('project1', 'calculate_score', {
    'lead_id': 123
})]
Result: {score: 85, factors: {...}}
```

### Example 5: Query Shopify Products

```
User: "Show me active products from Shopify"
Claude: [Calls shopify_discover() first]
Result: {store: "sellblingsting.myshopify.com", ...}

Claude: [Calls get_shopify_products(status='active', limit=10)]
Result: [10 active products returned]
```

### Example 6: Get Recent Shopify Orders

```
User: "Get paid orders from the last week"
Claude: [Calls get_shopify_orders({
    'status': 'any',
    'financial_status': 'paid',
    'created_at_min': '2024-11-28T00:00:00Z',
    'limit': 20
})]
Result: [20 paid orders returned]
```

## 🔄 Response Format

All tools return consistent format:

```json
{
  "success": true,
  "data": [...],
  "error": null,
  "metadata": {
    "rows": 10,
    "project": "project1",
    "table": "leads"
  }
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "error": "Table 'users' not found",
  "suggestion": "Use supabase_discover('project1') to see available tables"
}
```

## 🎯 Best Practices

### 1. Always Discover First

```
User: "I need to query the leads table"
Claude: [Calls supabase_discover('project1', 'leads') first]
Claude: "I see the leads table has these columns: [...]. What would you like to query?"
```

### 2. Use Filters Properly

Filters use Supabase PostgREST format:

```python
filters = {
    'score': 'gte.80',        # score >= 80
    'status': 'eq.new',       # status = 'new'
    'email': 'like.%@gmail%'  # email contains @gmail
}
```

### 3. Combine with Slash Commands

The MCP server is for **operations**, slash commands are for **documentation**:

```
User: /supabase
Claude: [Loads filter syntax, examples]

User: "Get high-scoring leads"
Claude: [Uses query_supabase tool with correct filter syntax]
```

## 🆚 MCP Server vs Slash Commands

| Feature | MCP Server | Slash Commands |
|---------|------------|----------------|
| **Tool Calling** | ✅ Direct | ❌ Python code |
| **Tokens** | ~300 | ~1,000 |
| **Speed** | Fast | Slower |
| **Documentation** | Minimal | Detailed |
| **Use For** | Operations | Learning |

**Recommendation:** Use **both**!
- MCP server for actual work (queries, updates)
- Slash commands when you need docs (/supabase for filter syntax)

## 🔧 Troubleshooting

### "MCP server not found"

Check your MCP configuration:
```bash
cat ~/.config/claude/mcp.json
# or
cat .claude/mcp.json
```

Verify the path is correct:
```bash
ls -la /path/to/api-toolkit/mcp-server/server.py
```

### "Environment variables not loaded"

The MCP server loads from:
1. Environment variables in MCP config
2. `.env` file in project root
3. `.env` file in api-toolkit directory

Test environment loading:
```bash
python /path/to/api-toolkit/test-env-loading.py
```

### "Connection failed"

Test connection directly:
```bash
cd /path/to/api-toolkit
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
print('Connected!' if api.test_connection() else 'Failed')
"
```

### "Tool not working"

Test tools directly:
```bash
cd /path/to/api-toolkit/mcp-server
python tools/supabase_tools.py
```

## 📈 Future Services

Coming soon:
- Smartlead (email campaigns)
- Metabase (analytics)
- Render (deployments)
- BrightData (web scraping)

Each service will add ~5-7 tools, keeping total tokens under 500.

## 🎓 Learning Path

1. **Start with discovery**: Use `supabase_discover()` to explore
2. **Query with tools**: Use `query_supabase()` for data
3. **Complex operations**: Use `supabase_raw_query()` or `supabase_rpc()`
4. **Edge functions**: Use `supabase_invoke_function()` for serverless
5. **Refer to docs**: Use `/supabase` slash command for detailed help

## 📚 Related Documentation

- **Server design**: `design.md` - Architecture and token optimization
- **API toolkit**: `../CLAUDE.md` - General guidance
- **Slash commands**: `../.claude/commands/supabase.md` - Detailed docs
- **Quick reference**: `../QUICK_REFERENCE.md` - Quick reference card

---

**Remember:** The MCP server is optimized for **tool calling** (~300 tokens). Use slash commands for **documentation** (~1000 tokens, only when needed).
