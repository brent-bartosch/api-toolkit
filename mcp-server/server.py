#!/usr/bin/env python3
"""
API Toolkit MCP Server
Lightweight MCP server (~300 tokens) for direct tool calling
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory for api_toolkit imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import tool modules
from tools.supabase_tools import SUPABASE_TOOLS
from tools.shopify_tools import SHOPIFY_TOOLS


class APIToolkitServer:
    """Lightweight MCP server for API toolkit"""

    def __init__(self):
        self.server = Server("api-toolkit")
        self.tools = {}

        # Register all tools
        self._register_tools()

        # Setup handlers
        self._setup_handlers()

    def _register_tools(self):
        """Register all available tools"""
        # Register Supabase tools
        for tool in SUPABASE_TOOLS:
            self.tools[tool['name']] = tool['function']

        # Register Shopify tools
        for tool in SHOPIFY_TOOLS:
            self.tools[tool['name']] = tool['function']

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            tools = []

            # Supabase tools
            tools.extend([
                Tool(
                    name="query_supabase",
                    description="Query a Supabase table with optional filters. Projects: project1 (example), project2 (example), scraping (web scraping).",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name: smoothed, blingsting, or scraping",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "table": {
                                "type": "string",
                                "description": "Table name to query"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Optional filters (e.g., {'score': 'gte.80'})"
                            },
                            "select": {
                                "type": "string",
                                "description": "Optional columns to select (comma-separated)"
                            },
                            "order": {
                                "type": "string",
                                "description": "Optional column to order by (prefix with - for desc)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max rows to return (default 100)",
                                "default": 100
                            }
                        },
                        "required": ["project", "table"]
                    }
                ),
                Tool(
                    name="supabase_discover",
                    description="List all tables in a project or get schema for specific table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name: smoothed, blingsting, or scraping",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "table": {
                                "type": "string",
                                "description": "Optional table name to get schema for"
                            }
                        },
                        "required": ["project"]
                    }
                ),
                Tool(
                    name="supabase_raw_query",
                    description="Execute raw SQL query (SELECT only, auto-limited to 1000 rows)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project name",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "sql": {
                                "type": "string",
                                "description": "SQL query (SELECT only)"
                            }
                        },
                        "required": ["project", "sql"]
                    }
                ),
                Tool(
                    name="supabase_insert",
                    description="Insert a record into a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "table": {
                                "type": "string",
                                "description": "Table name"
                            },
                            "data": {
                                "type": "object",
                                "description": "Data to insert (column: value pairs)"
                            }
                        },
                        "required": ["project", "table", "data"]
                    }
                ),
                Tool(
                    name="supabase_update",
                    description="Update records in a Supabase table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "table": {
                                "type": "string",
                                "description": "Table name"
                            },
                            "filters": {
                                "type": "object",
                                "description": "Filters to identify records (e.g., {'id': 'eq.123'})"
                            },
                            "data": {
                                "type": "object",
                                "description": "Data to update (column: value pairs)"
                            }
                        },
                        "required": ["project", "table", "filters", "data"]
                    }
                ),
                Tool(
                    name="supabase_rpc",
                    description="Call a PostgreSQL function via Supabase RPC",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "function_name": {
                                "type": "string",
                                "description": "Name of the PostgreSQL function"
                            },
                            "params": {
                                "type": "object",
                                "description": "Optional parameters for the function"
                            }
                        },
                        "required": ["project", "function_name"]
                    }
                ),
                Tool(
                    name="supabase_invoke_function",
                    description="Invoke a Supabase Edge Function (Deno serverless function)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "enum": ["project1", "project2", "project3"]
                            },
                            "function_name": {
                                "type": "string",
                                "description": "Name of the edge function"
                            },
                            "body": {
                                "type": "object",
                                "description": "Optional request body"
                            },
                            "method": {
                                "type": "string",
                                "description": "HTTP method (default POST)",
                                "default": "POST"
                            }
                        },
                        "required": ["project", "function_name"]
                    }
                )
            ])

            # Shopify tools
            tools.extend([
                Tool(
                    name="get_shopify_products",
                    description="Get products from Shopify store with optional filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by status: active, draft, archived"
                            },
                            "vendor": {
                                "type": "string",
                                "description": "Filter by vendor name"
                            },
                            "product_type": {
                                "type": "string",
                                "description": "Filter by product type"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max products to return (default 50, max 250)",
                                "default": 50
                            }
                        }
                    }
                ),
                Tool(
                    name="get_shopify_product",
                    description="Get a single product by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "Shopify product ID"
                            },
                            "fields": {
                                "type": "string",
                                "description": "Optional comma-separated fields to return"
                            }
                        },
                        "required": ["product_id"]
                    }
                ),
                Tool(
                    name="get_shopify_orders",
                    description="Get orders from Shopify store with optional filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Order status: open, closed, cancelled, any"
                            },
                            "financial_status": {
                                "type": "string",
                                "description": "Payment status: authorized, pending, paid, etc."
                            },
                            "fulfillment_status": {
                                "type": "string",
                                "description": "Fulfillment status: shipped, partial, unshipped, any"
                            },
                            "created_at_min": {
                                "type": "string",
                                "description": "Minimum creation date (ISO 8601 format)"
                            },
                            "created_at_max": {
                                "type": "string",
                                "description": "Maximum creation date (ISO 8601 format)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max orders to return (default 50, max 250)",
                                "default": 50
                            }
                        }
                    }
                ),
                Tool(
                    name="get_shopify_order",
                    description="Get a single order by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "integer",
                                "description": "Shopify order ID"
                            },
                            "fields": {
                                "type": "string",
                                "description": "Optional comma-separated fields to return"
                            }
                        },
                        "required": ["order_id"]
                    }
                ),
                Tool(
                    name="shopify_discover",
                    description="Discover available Shopify resources and test connection",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ])

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Execute a tool"""

            if name not in self.tools:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]

            try:
                # Call the tool function
                result = self.tools[name](**arguments)

                # Format response
                import json
                response = json.dumps(result, indent=2)

                return [TextContent(
                    type="text",
                    text=response
                )]

            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "suggestion": "Check tool parameters and try again"
                    }, indent=2)
                )]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point"""
    server = APIToolkitServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
