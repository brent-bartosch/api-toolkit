# MCP Server Overview

The API Toolkit provides two MCP server implementations for direct tool calling in Claude Code.

## Two Approaches

| Approach | Tokens | Best For | Directory |
|----------|--------|----------|-----------|
| **Direct Tools** | ~300 | Simple queries (<100 rows) | `mcp-server/` |
| **Code Execution** | ~2,000 | Large datasets, complex analysis | `mcp-server-code-exec/` |

## Direct Tools MCP (`mcp-server/`)

7 Supabase tools for direct database operations:
- `query_supabase` - Query tables with filters
- `supabase_discover` - List tables or get schema
- `supabase_raw_query` - Execute raw SQL
- `supabase_insert` / `supabase_update` - CRUD operations
- `supabase_rpc` - Call PostgreSQL functions
- `supabase_invoke_function` - Call Edge Functions

**Install:** See `mcp-server/INSTALLATION.md`

## Code Execution MCP (`mcp-server-code-exec/`)

Follows Anthropic's pattern: execute Python in sandbox, return only summaries.

6 tools:
- `execute_python` - Run Python with full API toolkit access
- `discover_services` / `get_service_info` - Progressive discovery
- `get_quick_start` / `get_code_examples` - Documentation on-demand
- `search_tools` - Find tools by keyword

**Use case:** Process 10,000 rows in sandbox (0 tokens), return 1,000 token summary.

**Install:** See `mcp-server-code-exec/INSTALLATION.md`

## Token Comparison

| Operation | Traditional MCP | Direct Tools | Code Execution |
|-----------|-----------------|--------------|----------------|
| Tool definitions | 90,000-150,000 | ~300 | ~2,000 |
| Query 1,000 rows | 50,000 | 50,000 | ~500 |
| Analyze 10,000 rows | 500,000+ | N/A | ~2,000 |

## Recommended Strategy

1. **Simple queries** → Direct Tools MCP
2. **Large datasets / analysis** → Code Execution MCP
3. **Learning / docs** → Slash commands (`/supabase`)

## Quick Setup

```bash
# Direct Tools
cd mcp-server && pip install -r requirements.txt

# Code Execution
cd mcp-server-code-exec && pip install -r requirements.txt
```

Configure in `~/.config/claude/mcp.json` - see installation docs in each directory.
