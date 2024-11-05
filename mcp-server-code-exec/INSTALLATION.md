# Code Execution MCP Server - Installation Guide

**Following Anthropic's pattern for efficient data processing**

## Quick Install (5 Minutes)

### Step 1: Install Dependencies

```bash
cd /path/to/api-toolkit/mcp-server-code-exec
pip install -r requirements.txt
```

Dependencies:
- `mcp>=0.9.0` - MCP protocol
- `python-dotenv>=1.0.0` - Environment loading
- `requests>=2.31.0` - HTTP client
- `RestrictedPython>=6.0` - Secure sandbox

### Step 2: Test the Components

```bash
# Test code executor
cd /path/to/api-toolkit
python mcp-server-code-exec/sandbox/executor.py

# Test discovery system
python mcp-server-code-exec/tools/discovery.py
```

You should see:
```
Testing Code Executor...
1. Testing simple code: ✓
2. Testing Supabase discovery: ✓
3. Testing data processing: ✓

Testing Tool Discovery System...
1. Available services: supabase, smartlead, ...
```

### Step 3: Configure Claude Code

#### Option A: Global Configuration

Edit `~/.config/claude/mcp.json`:

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

#### Option B: Project-Specific

Create `.claude/mcp.json` in your project:

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

### Step 4: Restart Claude Code

Close and reopen Claude Code completely for the MCP config to take effect.

### Step 5: Verify Installation

Open Claude Code and try:

```
You: "What MCP servers are available?"
Claude: [Should list api-toolkit-code-exec]

You: "Discover available services"
Claude: [Should call discover_services and show: supabase, smartlead, metabase, ...]

You: "Show me a quick example for supabase"
Claude: [Should call get_quick_start and return working code]
```

## Environment Configuration

The server uses the same environment as the API toolkit:

1. Project `.env` (recommended)
2. Toolkit `.env`
3. System environment variables

Test your environment:
```bash
python test-env-loading.py
```

Should show:
```
✅ Loaded from: /path/to/project/.env
✅ SUPABASE_URL (smoothed): configured
✅ SUPABASE_URL_2 (blingsting): configured
✅ SUPABASE_URL_3 (scraping): configured
```

## Testing

### Test 1: Discovery

```
You: "Discover available services"

Expected: List of services (supabase, smartlead, etc.)
```

### Test 2: Simple Code Execution

```
You: "Run this Python code: print('Hello from sandbox!')"

Expected: Hello from sandbox!
```

### Test 3: Supabase Query

```
You: "Execute Python code to query project1 database for 5 leads"

Expected: Claude writes code like:
api = SupabaseAPI('project1')
leads = api.query('leads', limit=5)
print(f"Found {len(leads)} leads")

Result: Shows 5 leads
```

### Test 4: Data Processing

```
You: "Analyze 100 leads from smoothed and show me score distribution"

Expected: Claude processes data in sandbox and returns summary
```

## Combining with Other Approaches

You can run multiple MCP servers:

```json
{
  "mcpServers": {
    "api-toolkit": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server/server.py"]
    },
    "api-toolkit-code-exec": {
      "command": "python",
      "args": ["/path/to/api-toolkit/mcp-server-code-exec/server.py"]
    }
  }
}
```

Then choose the right approach:
- **api-toolkit**: Simple queries (<100 rows)
- **api-toolkit-code-exec**: Complex operations (>100 rows)

## Troubleshooting

### "MCP server not found"

Check config file exists:
```bash
cat ~/.config/claude/mcp.json
# or
cat .claude/mcp.json
```

Verify path is absolute:
```bash
ls -la /path/to/api-toolkit/mcp-server-code-exec/server.py
```

### "Module not found" errors

Ensure running from toolkit root:
```bash
cd /path/to/api-toolkit
python mcp-server-code-exec/server.py
```

Check Python path:
```python
python -c "import sys; print('\n'.join(sys.path))"
```

### "Code execution failed"

Test executor directly:
```bash
python mcp-server-code-exec/sandbox/executor.py
```

Common issues:
- Missing `services` directory in path
- Missing `.env` file with Supabase credentials
- Import errors (check available imports in sandbox)

### "Connection to Supabase failed"

Test connection:
```bash
python -c "
from services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
print('✅' if api.test_connection() else '❌')
"
```

If fails:
```bash
# Check environment
python test-env-loading.py

# Verify .env file
cat .env | grep SUPABASE_URL
```

### "Tools not showing in Claude Code"

1. Restart Claude Code completely
2. Check logs for MCP errors
3. Verify server starts without errors:
   ```bash
   python mcp-server-code-exec/server.py
   # Should start without errors (Ctrl+C to stop)
   ```

## Advanced Configuration

### Custom Python Environment

If using virtual environment:

```json
{
  "mcpServers": {
    "api-toolkit-code-exec": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/mcp-server-code-exec/server.py"]
    }
  }
}
```

### Execution Timeout

Modify `sandbox/executor.py`:

```python
class CodeExecutor:
    def __init__(self):
        self.timeout = 120  # Increase to 2 minutes
        self.max_output_size = 200000  # 200KB
```

### Debug Mode

Add logging to server.py:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

The sandbox is secure but not impenetrable:

1. **Limited builtins**: No `eval`, `exec`, `open`, `__import__`
2. **Timeout**: 60 second max execution
3. **Output limit**: 100KB max
4. **No filesystem**: Cannot read/write files
5. **API only**: Network access only through API toolkit

For production use, consider:
- Running in Docker container
- Using resource limits (memory, CPU)
- Monitoring execution logs
- Rate limiting requests

## Verification Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Executor test passes (`python sandbox/executor.py`)
- [ ] Discovery test passes (`python tools/discovery.py`)
- [ ] MCP config file created
- [ ] Absolute paths used in config
- [ ] Claude Code restarted
- [ ] Tools visible in Claude Code (`discover_services` works)
- [ ] Code execution works (simple print test)
- [ ] Supabase query works (query project1 database)

## Performance Tips

1. **Progressive disclosure**: Start with `discover_services`, then `get_service_info('basic')`, only load 'full' if needed

2. **Process in sandbox**: Do complex operations in code, return only summary

3. **Batch operations**: Process multiple items in one code execution

4. **Cache results**: Store intermediate results in variables

## Next Steps

Once installed:

1. **Try discovery**:
   ```
   "What services are available?"
   "Show me supabase methods"
   "Give me a quick start example"
   ```

2. **Execute simple code**:
   ```
   "Print hello world in Python"
   ```

3. **Query database**:
   ```
   "Get 10 leads from project1 database"
   ```

4. **Process data**:
   ```
   "Analyze 1000 leads and show score distribution"
   ```

## Getting Help

If stuck:

1. Test components individually (executor, discovery)
2. Check environment (`test-env-loading.py`)
3. Verify MCP config (absolute paths)
4. Review logs for errors
5. See `README.md` for usage patterns
6. Check `mcp-server-code-exec/examples/` for working code

---

**Remember**: This approach is optimized for large datasets and complex operations. For simple queries, consider using the direct tools MCP (`mcp-server/`).
