# API Toolkit MCP Server Design

## Goal

Create a lightweight MCP server (~300 tokens) that enables direct tool calling while avoiding context bloat.

## Design Principles

1. **Minimal Tool Definitions** - Brief descriptions only (1-2 sentences)
2. **No Schema Documentation** - Don't include table schemas in tool descriptions
3. **Discovery Tools** - Let Claude query for schema when needed
4. **Defer to Slash Commands** - For detailed docs, use `/supabase` etc.
5. **Core Operations Only** - ~10-15 essential tools, not full API coverage

## Tool Inventory

### Supabase (5 tools)

```typescript
query_supabase(project: string, table: string, filters?: object, select?: string, limit?: number)
// Brief: Query Supabase table with optional filters

supabase_discover(project: string, table?: string)
// Brief: List tables or get schema for specific table

supabase_raw_query(project: string, sql: string)
// Brief: Execute raw SQL query (SELECT only)

supabase_insert(project: string, table: string, data: object)
// Brief: Insert record into table

supabase_update(project: string, table: string, id: string, data: object)
// Brief: Update record by ID
```

### Smartlead (4 tools)

```typescript
smartlead_create_campaign(name: string, client_id: number, settings?: object)
// Brief: Create new email campaign

smartlead_add_leads(campaign_id: string, leads: array)
// Brief: Add leads to campaign

smartlead_get_analytics(campaign_id: string)
// Brief: Get campaign performance metrics

smartlead_list_campaigns()
// Brief: List all campaigns
```

### Metabase (3 tools)

```typescript
metabase_run_query(sql: string, database_id: number, parameters?: array)
// Brief: Execute SQL query

metabase_query_card(card_id: number, parameters?: object)
// Brief: Query saved question/card

metabase_export_card(card_id: number, format: string)
// Brief: Export card data (csv, json, xlsx)
```

### Render (2 tools)

```typescript
render_trigger_deploy(service_id: string)
// Brief: Trigger manual deployment

render_update_env_var(service_id: string, key: string, value: string)
// Brief: Update environment variable
```

### BrightData (2 tools)

```typescript
brightdata_web_unlocker(url: string, method?: string)
// Brief: Fetch URL bypassing anti-bot

brightdata_serp_search(query: string, engine: string, country?: string)
// Brief: Get search engine results
```

**Total: 16 tools, ~300 tokens**

## Tool Response Format

All tools return consistent format:

```json
{
  "success": true,
  "data": [...],
  "error": null,
  "metadata": {
    "rows": 10,
    "took_ms": 145
  }
}
```

## Error Handling

When tool fails, response includes helpful context:

```json
{
  "success": false,
  "data": null,
  "error": "Table 'users' not found. Available tables: leads, brands, scraping_results",
  "suggestion": "Use supabase_discover('project1') to see all tables"
}
```

## Interaction with Slash Commands

**Tools** = Direct operations (query, create, update)
**Slash Commands** = Documentation (schemas, filters, examples)

**Example workflow:**
```
User: "Get high-scoring leads from Supabase"

Claude: [Calls query_supabase('project1', 'leads', {score: 'gte.80'})]
Result: [10 leads returned]

User: "What filters can I use?"
Claude: Uses /supabase slash command to load filter documentation
```

## Token Budget

| Component | Tokens | Purpose |
|-----------|--------|---------|
| Tool definitions | ~300 | MCP server protocol |
| Slash commands | ~1000 | Loaded only when needed |
| Full docs | ~5000 | Rarely needed |
| **Total (typical)** | **~300** | **Just tool definitions!** |

Compare to:
- Poor MCP design: 90,000 tokens (all docs in tool descriptions)
- Current slash commands: 1,000 tokens (but requires Python code)
- **This design: 300 tokens with direct tool calling ✨**

## Implementation

### MCP Server Structure

```
mcp-server/
├── server.py           # MCP protocol implementation
├── tools/
│   ├── supabase.py    # Supabase tool implementations
│   ├── smartlead.py   # Smartlead tool implementations
│   ├── metabase.py    # Metabase tool implementations
│   ├── render.py      # Render tool implementations
│   └── brightdata.py  # BrightData tool implementations
├── config.py          # Configuration
└── README.md          # Setup instructions
```

### Server Entry Point

```python
# server.py
from mcp.server import Server
from tools import supabase, smartlead, metabase, render, brightdata

server = Server("api-toolkit")

# Register tools
server.register_tools([
    *supabase.get_tools(),
    *smartlead.get_tools(),
    *metabase.get_tools(),
    *render.get_tools(),
    *brightdata.get_tools()
])

if __name__ == "__main__":
    server.run()
```

### Tool Implementation Example

```python
# tools/supabase.py
from api_toolkit.services.supabase.api import SupabaseAPI

@tool
def query_supabase(project: str, table: str, filters: dict = None,
                   select: str = None, limit: int = 100):
    """Query Supabase table with optional filters"""
    try:
        api = SupabaseAPI(project)
        results = api.query(table, filters=filters, select=select, limit=limit)

        return {
            "success": True,
            "data": results,
            "error": None,
            "metadata": {"rows": len(results)}
        }
    except Exception as e:
        # Helpful error with suggestions
        available_tables = api.explore() if hasattr(api, 'explore') else []

        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": f"Use supabase_discover('{project}') to see available tables"
        }
```

## Configuration

MCP server config for Claude Code (`.claude/mcp.json`):

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_SERVICE_ROLE_KEY": "${SUPABASE_SERVICE_ROLE_KEY}",
        "SMARTLEAD_API_KEY": "${SMARTLEAD_API_KEY}"
      }
    }
  }
}
```

## Benefits

✅ **True tool calling** - No Python code generation
✅ **Minimal tokens** - ~300 tokens vs 90,000
✅ **Fast** - Direct API calls, no intermediary
✅ **Discovery** - `supabase_discover()` for schema when needed
✅ **Slash commands** - Still available for detailed docs
✅ **Consistent** - All tools return same format
✅ **Helpful errors** - Include suggestions for fixing

## Migration Path

1. **Phase 1**: Implement MCP server with core tools
2. **Phase 2**: Test token usage vs slash commands
3. **Phase 3**: Keep slash commands for documentation fallback
4. **Phase 4**: Update project setup to offer MCP or slash commands

Users can choose:
- **MCP server** = Direct tool calling (~300 tokens)
- **Slash commands** = More control, Python code (~1000 tokens)
- **Both** = Best of both worlds
