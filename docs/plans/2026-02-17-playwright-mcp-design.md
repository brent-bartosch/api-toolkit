# Playwright Curated MCP Proxy -- Design Document

**Date:** 2026-02-17
**Status:** Approved
**Goal:** Give Claude Code visual + interactive access to frontends via a token-efficient Playwright MCP server.

## Problem

The stock Playwright MCP (`@playwright/mcp`) loads ~20K tokens of tool schemas (34 tools) and generates ~114K tokens per session. This contradicts the API toolkit's philosophy of ~500-1000 tokens per service.

Claude Code needs to iterate on UI design and functionality by navigating to deployed staging/preview URLs, taking screenshots, clicking elements, and filling forms -- without exhausting the context window.

## Solution

A curated MCP server at `mcp-server-playwright/` that wraps Playwright directly (not the stock MCP), exposing 8 focused tools with minimal schemas. Screenshots saved to disk instead of returned inline. Estimated ~2-2.5K tokens for tool schemas (90% reduction from stock).

## Architecture

```
Claude Code  ──MCP protocol──>  mcp-server-playwright/server.py
                                        │
                                        ▼
                                 Playwright (headless Chromium)
                                        │
                                        ▼
                          Screenshots → .playwright/screenshots/
                          Snapshots  → Trimmed accessibility text (200 lines max)
```

### Key Principles

- 8 tools max (vs 34 in stock)
- Screenshots to disk, return file paths (zero inline image tokens)
- Minimal tool schemas (2-4 params each, short descriptions)
- Accessibility snapshots capped at 200 lines
- Single headless Chromium instance reused across calls
- Smart waits built into navigate/click (no separate wait tool)

## Tool Definitions

| # | Tool | Parameters | Returns |
|---|------|-----------|---------|
| 1 | `browser_navigate` | `url` (required) | Page title + status code |
| 2 | `browser_screenshot` | `path` (optional), `full_page` (bool) | File path to saved PNG |
| 3 | `browser_click` | `selector` (CSS/text) | Success + brief state change |
| 4 | `browser_type` | `selector`, `text` | Success confirmation |
| 5 | `browser_select` | `selector`, `value` | Success confirmation |
| 6 | `browser_snapshot` | `max_lines` (default 200) | Trimmed accessibility tree |
| 7 | `browser_evaluate` | `script` (JS string) | Return value (truncated 2000 chars) |
| 8 | `browser_close` | none | Confirmation |

### Selector Strategy

CSS selectors and text selectors (not accessibility refs). Claude already knows CSS. Examples:
- `"#submit-btn"` -- by ID
- `".nav-link"` -- by class
- `"text=Sign In"` -- by visible text
- `"input[name='email']"` -- by attribute

### Screenshot Strategy

- Saved to `.playwright/screenshots/` in the working directory
- Filename: `screenshot_YYYYMMDD_HHMMSS.png`
- Default viewport: 1280x720
- `full_page` option for scrollable content
- Auto-cleanup: screenshots older than 24 hours
- Claude views via Read tool (which supports images)

## Browser Lifecycle

- **Lazy launch**: Browser starts on first `browser_navigate`, not at MCP startup
- **Session persistence**: Browser stays alive across tool calls within a session
- **Auto-cleanup**: Browser closes when MCP server process exits
- **Smart waits**: Navigate waits for `networkidle`. Click waits for element actionable.
- **Timeout**: 30s per operation (configurable)

## File Structure

```
mcp-server-playwright/
├── server.py              # MCP server entry point
├── browser_manager.py     # Playwright browser lifecycle
├── tools.py               # Tool implementations
├── config.py              # Defaults (viewport, timeouts, dirs)
├── requirements.txt       # playwright, mcp
├── INSTALLATION.md        # Setup guide
└── README.md              # Usage docs
```

## Installation

### Claude Code Configuration

Add to `.claude/mcp.json`:
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

### Dependencies

```bash
pip install playwright mcp
playwright install chromium
```

## Slash Command

A `/playwright` slash command at `.claude/commands/playwright.md` providing usage context (~200-300 tokens) for Claude to reference when using the tools.

## Token Budget

| Component | Stock Playwright MCP | This Design |
|-----------|---------------------|-------------|
| Tool schemas | ~20,000 | ~2,000-2,500 |
| Per-screenshot | ~2,000-5,000 (inline) | 0 (disk) |
| Per-snapshot | ~500-5,000 | ~200-500 (capped) |
| Typical session | ~114,000 | ~5,000-10,000 |

## Target URLs

Primarily deployed staging/preview URLs (Render previews, Vercel, etc.). Full URL flexibility -- no hardcoded defaults.

## Out of Scope

- File upload tools
- Drag-and-drop
- Multi-tab management
- Vision/coordinate-based clicking
- PDF generation
- Testing assertions
- Network request monitoring
