# MCP Server Configuration — Systemic Architecture

## What This Is

`mcp-servers/` is the **canonical source of truth** for MCP server configurations across all agent tools. Define servers once in `manifest.json`, run `sync.py` to propagate.

## Architecture (Refined for Token Efficiency)

```
manifest.json (source of truth)
       │
       ├── Hermes (~/.hermes/config.yaml)
       │   └── 12 of 23 Playwright tools via tools.include filter
       │       Built-in browser toolset: DISABLED
       │       Token cost: ~2,532 tokens
       │
       ├── Claude Code (project-level .claude/mcp.json)
       │   └── All 23 Playwright tools (no per-tool filter available)
       │       Only loads when working in api-toolkit project
       │       Token cost: ~4,577 tokens (project-scoped only)
       │
       └── Codex (~/.codex/config.toml)
           └── NO Playwright MCP — uses browser@openai-bundled + chrome@openai-bundled
               Token cost: 0 (no Playwright overhead)
```

## Token Cost Summary

| Tool | Before | After | Savings |
|------|--------|-------|---------|
| **Hermes** | ~6,577 (7 built-in + 23 MCP) | ~2,532 (12 MCP only) | ~4,045 tokens (61%) |
| **Claude Code** | ~4,577 (global, every session) | ~4,577 (project-level only) | Global sessions: 100% |
| **Codex** | ~4,577 + browser plugins | 0 + browser plugins | ~4,577 tokens |

## The 12 Essential Playwright Tools (Hermes)

| Tool | Tokens | Why Kept |
|------|--------|----------|
| `browser_navigate` | 103 | Core — can't do anything without this |
| `browser_navigate_back` | 86 | Cheap, useful for multi-page flows |
| `browser_click` | 252 | Core interaction |
| `browser_type` | 246 | Core input |
| `browser_snapshot` | 232 | How agents "see" the page (accessibility tree) |
| `browser_tabs` | 174 | Multi-tab — unique capability |
| `browser_file_upload` | 131 | File uploads — unique capability |
| `browser_fill_form` | 305 | Batch form fill — saves multiple type calls |
| `browser_evaluate` | 227 | JS execution — covers scroll, hover, press_key, resize, select_option, console |
| `browser_network_requests` | 226 | Network inspection — unique capability |
| `browser_take_screenshot` | 404 | Visual debugging |
| `browser_wait_for` | 146 | Wait for elements — prevents race conditions |

**Total: ~2,532 tokens**

### 11 Tools Dropped (covered by `browser_evaluate` or niche)

| Dropped Tool | Tokens | Replacement |
|-------------|--------|--------------|
| `browser_close` | 78 | Session closes on restart |
| `browser_resize` | 129 | `browser_evaluate: window.resizeTo()` |
| `browser_console_messages` | 226 | `browser_evaluate: console.log capture` |
| `browser_handle_dialog` | 132 | Niche — alerts auto-dismiss |
| `browser_press_key` | 118 | `browser_evaluate: dispatchEvent(new KeyboardEvent(...))` |
| `browser_hover` | 154 | `browser_evaluate: element.dispatchEvent(new MouseEvent('mouseover'))` |
| `browser_select_option` | 202 | `browser_evaluate: element.value = 'X'` |
| `browser_drag` | 239 | Niche — can use JS if needed |
| `browser_drop` | 284 | Niche — can use JS if needed |
| `browser_network_request` | 244 | Detail view — `browser_network_requests` covers list |
| `browser_run_code_unsafe` | 229 | `browser_evaluate` covers JS execution |

## Shared Persistent Browser Profile

All tools point to the same persistent profile at `~/.hermes/browser-profiles/playwright`:
- **Hermes** and **Claude Code** share login sessions
- **Codex** uses its own browser plugins (separate profile) — doesn't share sessions with Playwright
- Log in to a browser-only destination once → Hermes and Claude Code both see the authenticated session

## Usage

```bash
# Sync all servers to all tools
python mcp-servers/sync.py

# Sync only Playwright to Hermes
python mcp-servers/sync.py --server playwright --tool hermes

# Dry run
python mcp-servers/sync.py --dry-run
```

## After Syncing

| Tool | Action Required |
|------|----------------|
| **Hermes** | `/reset` or relaunch — 12 Playwright tools load |
| **Claude Code** | Restart — loads project-level `.claude/mcp.json` (only in api-toolkit) |
| **Codex** | N/A — no Playwright MCP configured |
