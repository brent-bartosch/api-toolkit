#!/usr/bin/env python3
"""
Code Execution MCP Server for API Toolkit
Follows Anthropic's pattern for efficient large-scale data processing

Key Features:
- Execute Python code in sandbox (~2000 tokens vs 150k for traditional MCP)
- Progressive tool discovery (load docs on-demand)
- Process data before returning (huge token savings)
- Secure execution environment
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our components
from sandbox.executor import CodeExecutor
from tools.discovery import ToolDiscovery


class CodeExecutionMCPServer:
    """MCP server with code execution capabilities"""

    def __init__(self):
        self.server = Server("api-toolkit-code-exec")
        self.executor = CodeExecutor()
        self.discovery = ToolDiscovery()

        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools (progressive disclosure pattern)"""
            return [
                Tool(
                    name="execute_python",
                    description=(
                        "Execute Python code in sandbox with access to API toolkit. "
                        "Use this to query databases, process large datasets, and perform "
                        "complex operations. The code runs in a secure environment with "
                        "SupabaseAPI, QueryBuilder, and standard libraries available. "
                        "Process data in the sandbox before returning results to save tokens."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute"
                            },
                            "description": {
                                "type": "string",
                                "description": "Brief description of what the code does"
                            }
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="discover_services",
                    description=(
                        "List available API services (supabase, smartlead, metabase, etc). "
                        "Returns minimal metadata to keep token usage low. "
                        "Use get_service_info for detailed information about a specific service."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_service_info",
                    description=(
                        "Get detailed information about a specific service. "
                        "Detail levels: 'basic' (file list), 'standard' (methods), 'full' (docs). "
                        "Use progressive disclosure: start with basic, request more only if needed."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "description": "Service name (supabase, smartlead, metabase, etc)"
                            },
                            "detail_level": {
                                "type": "string",
                                "description": "Detail level: basic, standard, or full",
                                "enum": ["basic", "standard", "full"],
                                "default": "basic"
                            }
                        },
                        "required": ["service_name"]
                    }
                ),
                Tool(
                    name="get_quick_start",
                    description=(
                        "Get minimal working code example for a service. "
                        "Returns a quick start snippet you can adapt for your needs."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "description": "Service name"
                            }
                        },
                        "required": ["service_name"]
                    }
                ),
                Tool(
                    name="search_tools",
                    description=(
                        "Search for tools by keyword. "
                        "Returns matching services and their relevance scores."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results (default 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_code_examples",
                    description=(
                        "Get code examples for a service. "
                        "Optionally filter by example type."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_name": {
                                "type": "string",
                                "description": "Service name"
                            },
                            "example_type": {
                                "type": "string",
                                "description": "Optional filter (e.g., 'query', 'insert')"
                            }
                        },
                        "required": ["service_name"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Execute a tool"""

            try:
                if name == "execute_python":
                    result = self.executor.execute(arguments['code'])
                    return [TextContent(
                        type="text",
                        text=self._format_execution_result(result)
                    )]

                elif name == "discover_services":
                    services = self.discovery.list_services()
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            'services': services,
                            'count': len(services),
                            'usage_tip': 'Use get_service_info(service_name) for details'
                        }, indent=2)
                    )]

                elif name == "get_service_info":
                    service_name = arguments['service_name']
                    detail_level = arguments.get('detail_level', 'basic')
                    info = self.discovery.get_service_overview(service_name, detail_level)
                    return [TextContent(
                        type="text",
                        text=json.dumps(info, indent=2)
                    )]

                elif name == "get_quick_start":
                    quick_start = self.discovery.get_quick_start(arguments['service_name'])
                    return [TextContent(
                        type="text",
                        text=quick_start
                    )]

                elif name == "search_tools":
                    results = self.discovery.search_tools(
                        arguments['query'],
                        arguments.get('max_results', 10)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            'results': results,
                            'query': arguments['query']
                        }, indent=2)
                    )]

                elif name == "get_code_examples":
                    examples = self.discovery.get_code_examples(
                        arguments['service_name'],
                        arguments.get('example_type')
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(examples, indent=2)
                    )]

                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            'error': f"Unknown tool: {name}"
                        })
                    )]

            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        'error': str(e),
                        'tool': name,
                        'suggestion': 'Check tool parameters and try again'
                    }, indent=2)
                )]

    def _format_execution_result(self, result: dict) -> str:
        """Format code execution result for display"""

        if result['success']:
            output = f"""✅ Code executed successfully

Output:
{result['output']}

Execution time: {result['execution_time']:.2f}s
Output size: {result['metrics']['output_size']} bytes"""

            if result.get('error'):
                output += f"\n\nWarnings:\n{result['error']}"

            if result.get('result'):
                output += f"\n\nResult:\n{json.dumps(result['result'], indent=2)}"

            return output

        else:
            return f"""❌ Code execution failed

Error:
{result['error']}

Output (if any):
{result['output']}

Suggestion: {result.get('suggestion', 'Check code syntax')}

Execution time: {result['execution_time']:.2f}s"""

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
    server = CodeExecutionMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
