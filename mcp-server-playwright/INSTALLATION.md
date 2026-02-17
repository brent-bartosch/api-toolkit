# Playwright MCP Server -- Installation

## Prerequisites

```bash
pip install playwright mcp
playwright install chromium
```

## Claude Code Setup

Add to your project's `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "python",
      "args": ["/Users/brentbartosch/Development/api-toolkit/mcp-server-playwright/server.py"],
      "env": {}
    }
  }
}
```

Or add globally at `~/.claude.json`.

## Verify

Restart Claude Code. You should see 8 `browser_*` tools available.

## Screenshot Directory

Screenshots are saved to `.playwright/screenshots/` in your working directory.
Add to `.gitignore`:

```
.playwright/
```
