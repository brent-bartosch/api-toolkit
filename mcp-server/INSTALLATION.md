# MCP Server Installation Guide

## Quick Install (5 Minutes)

### Step 1: Install Dependencies

```bash
cd /path/to/api-toolkit/mcp-server
pip install -r requirements.txt
```

### Step 2: Test the Tools

```bash
# From api-toolkit root directory
cd /path/to/api-toolkit
python mcp-server/tools/supabase_tools.py
```

You should see:
```
Testing Supabase tools...
1. Testing supabase_discover...
Success: True
Tables found: X

2. Testing query_supabase...
Success: True
Rows returned: 2
```

### Step 3: Configure for Claude Code

#### Option A: Global Configuration (All Projects)

Edit `~/.config/claude/mcp.json` (create if doesn't exist):

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"]
    }
  }
}
```

#### Option B: Project-Specific Configuration

In your project, create `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"]
    }
  }
}
```

### Step 4: Restart Claude Code

Close and reopen Claude Code for MCP configuration to take effect.

### Step 5: Verify in Claude Code

In a new Claude Code conversation, check if tools are available:

```
You: "List available MCP tools"
Claude: [Should show api-toolkit tools including query_supabase, supabase_discover, etc.]
```

## Environment Variables

The MCP server needs Supabase credentials. It loads from:

1. Project `.env` file (recommended)
2. api-toolkit `.env` file
3. System environment variables

### Option 1: Project .env (Recommended)

In your project root:
```bash
# .env
SUPABASE_URL=https://your-project-1.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here

# Additional projects
SUPABASE_URL_2=https://your-project-2.supabase.co
SUPABASE_SERVICE_ROLE_KEY_2=your-key-2

SUPABASE_URL_3=https://your-project-3.supabase.co
SUPABASE_SERVICE_ROLE_KEY_3=your-key-3
```

### Option 2: MCP Config with Env Vars

In your MCP config, explicitly pass environment variables:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"],
      "env": {
        "SUPABASE_URL": "https://your-project-1.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "your-actual-key-here",
        "SUPABASE_URL_2": "https://your-project-2.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY_2": "your-key-2",
        "SUPABASE_URL_3": "https://your-project-3.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY_3": "your-key-3"
      }
    }
  }
}
```

## Testing

### Test 1: Direct Tool Test

```bash
cd /path/to/api-toolkit
python mcp-server/tools/supabase_tools.py
```

Should show successful tests for discover and query.

### Test 2: Connection Test

```bash
python -c "
from services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
print('✅ Connected!' if api.test_connection() else '❌ Failed')
"
```

### Test 3: MCP Server Running

```bash
# This will start the server (needs MCP client to actually test)
python mcp-server/server.py
```

The server should start without errors. Press Ctrl+C to stop.

### Test 4: In Claude Code

Open Claude Code and try:

```
You: "Use supabase_discover to show me tables in project1 project"
Claude: [Should call the tool and return tables]

You: "Query the leads table, limit 5"
Claude: [Should call query_supabase and return results]
```

## Troubleshooting

### Problem: "Module not found"

```bash
# Ensure you're running from correct directory
cd /path/to/api-toolkit

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall requirements
pip install -r mcp-server/requirements.txt
```

### Problem: "MCP server not showing in Claude Code"

1. Check MCP config exists:
   ```bash
   cat ~/.config/claude/mcp.json
   # or
   cat .claude/mcp.json
   ```

2. Verify path is absolute:
   ```json
   "args": ["/path/to/api-toolkit/mcp-server/server.py"]
   ```

3. Restart Claude Code completely

4. Check Claude Code logs for errors

### Problem: "Connection failed"

```bash
# Check environment variables
python /path/to/api-toolkit/test-env-loading.py

# Test Supabase connection directly
python -c "
from services.supabase.api import SupabaseAPI
for project in ['project1', 'project2', 'project3']:
    api = SupabaseAPI(project)
    status = '✅' if api.test_connection() else '❌'
    print(f'{status} {project}')
"
```

### Problem: "Tools not available in Claude Code"

Check if MCP server is actually registered:

1. In Claude Code, check bottom status bar for MCP indicator
2. Try: "What MCP servers are available?"
3. If api-toolkit doesn't show, check MCP config path is correct

## Advanced Configuration

### Multiple MCP Servers

You can run multiple MCP servers alongside api-toolkit:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    }
  }
}
```

### Custom Python Environment

If you use a virtual environment:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"]
    }
  }
}
```

### Debug Mode

Add environment variable for verbose logging:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"],
      "env": {
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

## Verification Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Direct tool test passes (`python mcp-server/tools/supabase_tools.py`)
- [ ] Connection test passes (all 3 projects connect)
- [ ] MCP config file created in correct location
- [ ] Absolute paths used in MCP config
- [ ] Claude Code restarted after config changes
- [ ] Tools visible in Claude Code
- [ ] Tools work when called

## Next Steps

Once installed:

1. **Try discovery**: "Show me tables in smoothed"
2. **Try queries**: "Get leads with score > 80"
3. **Try functions**: "Call the calculate_score function"
4. **Combine with slash commands**: Use `/supabase` for documentation

## Getting Help

If you're stuck:

1. Check tool tests work: `python mcp-server/tools/supabase_tools.py`
2. Verify environment: `python test-env-loading.py`
3. Check MCP config: `cat ~/.config/claude/mcp.json`
4. Look at server design: Read `mcp-server/design.md`
5. Review API toolkit docs: Read `CLAUDE.md`

---

**Remember:** The MCP server (~300 tokens) is for **tool calling**. Use slash commands (~1000 tokens) for **documentation**.
