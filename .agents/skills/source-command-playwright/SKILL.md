---
name: "source-command-playwright"
description: "Load Playwright MCP context for browser automation"
---

# source-command-playwright

Use this skill when the user asks to run the migrated source command `playwright`.

## Command Template

# Playwright MCP -- Quick Reference

8 tools available via MCP for visual + interactive frontend work:

| Tool | Example |
|------|---------|
| `browser_navigate` | `{"url": "https://staging.example.com"}` |
| `browser_screenshot` | `{}` or `{"full_page": true}` |
| `browser_click` | `{"selector": "#submit-btn"}` or `{"selector": "text=Sign In"}` |
| `browser_type` | `{"selector": "input[name='email']", "text": "test@example.com"}` |
| `browser_select` | `{"selector": "#country", "value": "US"}` |
| `browser_snapshot` | `{"max_lines": 100}` |
| `browser_evaluate` | `{"script": "document.querySelectorAll('.item').length"}` |
| `browser_close` | `{}` |

**Workflow**: Navigate -> Screenshot -> View with Read tool -> Interact -> Screenshot again

**Screenshots**: Saved to `.playwright/screenshots/`, auto-cleaned after 24h. Use Read tool to view.

**Selectors**: CSS (`#id`, `.class`, `input[name='x']`) or text (`text=Click Me`).
