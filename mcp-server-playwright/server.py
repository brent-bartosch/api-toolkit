#!/usr/bin/env python3
"""
Playwright Curated MCP Server
Token-efficient MCP server exposing 8 Playwright tools (~2K tokens).
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from browser_manager import BrowserManager
from tools import PlaywrightTools


class PlaywrightMCPServer:
    """Lightweight MCP server for Playwright browser automation."""

    def __init__(self):
        self.server = Server("playwright")
        self.manager = BrowserManager()
        self.tools = PlaywrightTools(self.manager)
        self._setup_handlers()

    def _setup_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="browser_navigate",
                    description="Navigate to a URL. Returns page title and status.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to",
                            }
                        },
                        "required": ["url"],
                    },
                ),
                Tool(
                    name="browser_screenshot",
                    description="Take screenshot, save to disk. Returns file path (use Read tool to view).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Optional file path. Auto-generated if omitted.",
                            },
                            "full_page": {
                                "type": "boolean",
                                "description": "Capture full scrollable page (default false)",
                                "default": False,
                            },
                        },
                    },
                ),
                Tool(
                    name="browser_click",
                    description="Click an element. Supports CSS selectors and text= selectors.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": 'CSS or text selector (e.g., "#btn", "text=Sign In")',
                            }
                        },
                        "required": ["selector"],
                    },
                ),
                Tool(
                    name="browser_type",
                    description="Type text into an input field.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the input",
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type",
                            },
                        },
                        "required": ["selector", "text"],
                    },
                ),
                Tool(
                    name="browser_select",
                    description="Select a dropdown option by value.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the select element",
                            },
                            "value": {
                                "type": "string",
                                "description": "Option value to select",
                            },
                        },
                        "required": ["selector", "value"],
                    },
                ),
                Tool(
                    name="browser_snapshot",
                    description="Get page accessibility tree as text. Good for understanding page structure without a screenshot.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "max_lines": {
                                "type": "integer",
                                "description": "Max lines to return (default 200)",
                                "default": 200,
                            }
                        },
                    },
                ),
                Tool(
                    name="browser_evaluate",
                    description="Run JavaScript on the page. Returns result (truncated to 2000 chars).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "JavaScript to evaluate",
                            }
                        },
                        "required": ["script"],
                    },
                ),
                Tool(
                    name="browser_close",
                    description="Close the browser session.",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            dispatch = {
                "browser_navigate": lambda args: self.tools.navigate(args["url"]),
                "browser_screenshot": lambda args: self.tools.screenshot(
                    path=args.get("path"), full_page=args.get("full_page", False)
                ),
                "browser_click": lambda args: self.tools.click(args["selector"]),
                "browser_type": lambda args: self.tools.type_text(
                    args["selector"], args["text"]
                ),
                "browser_select": lambda args: self.tools.select(
                    args["selector"], args["value"]
                ),
                "browser_snapshot": lambda args: self.tools.snapshot(
                    max_lines=args.get("max_lines")
                ),
                "browser_evaluate": lambda args: self.tools.evaluate(args["script"]),
                "browser_close": lambda args: self.tools.close(),
            }

            if name not in dispatch:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            try:
                result = await dispatch[name](arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"success": False, "error": str(e)}),
                    )
                ]

    async def run(self):
        """Run the MCP server via stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def cleanup(self):
        """Clean up browser on shutdown."""
        await self.manager.close()


def main():
    server = PlaywrightMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        asyncio.run(server.cleanup())


if __name__ == "__main__":
    main()
