# Playwright Curated MCP Server

Token-efficient Playwright MCP server (~2K tokens) for visual + interactive frontend development.

## Tools (8)

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Load a URL |
| `browser_screenshot` | Capture page to disk (returns file path) |
| `browser_click` | Click element (CSS/text selector) |
| `browser_type` | Type into input field |
| `browser_select` | Select dropdown option |
| `browser_snapshot` | Get accessibility tree as text |
| `browser_evaluate` | Run JavaScript |
| `browser_close` | Close browser session |

## Token Comparison

| Approach | Tool Schema Tokens |
|----------|--------------------|
| Stock Playwright MCP (34 tools) | ~20,000 |
| **This server (8 tools)** | **~2,000** |

## Usage

Navigate to a page, take a screenshot, then use Read tool to view it:

1. `browser_navigate` with your staging URL
2. `browser_screenshot` to capture the page
3. View the screenshot file with Read tool
4. `browser_click` / `browser_type` to interact
5. `browser_screenshot` again to verify changes

Screenshots are saved to `.playwright/screenshots/` and auto-cleaned after 24 hours.

## Setup

See `INSTALLATION.md`.
