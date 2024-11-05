#!/usr/bin/env python3
"""
Supabase MCP Tools - Lightweight tool definitions
Includes support for queries, functions, RPC, and Deno edge functions
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import from services directory
from services.supabase.api import SupabaseAPI
from services.supabase.query_helpers import QueryBuilder


def query_supabase(project: str, table: str, filters: dict = None,
                   select: str = None, order: str = None, limit: int = 100) -> dict:
    """
    Query a Supabase table with optional filters.

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        table: Table name
        filters: Optional filters dict (e.g., {'score': 'gte.80'})
        select: Optional columns to select (comma-separated)
        order: Optional column to order by (prefix with - for desc)
        limit: Max rows to return (default 100)

    Returns:
        {success: bool, data: list, error: str, metadata: dict}
    """
    try:
        api = SupabaseAPI(project)

        # Build parameters
        params = {'limit': limit}
        if filters:
            params['filters'] = filters
        if select:
            params['select'] = select
        if order:
            params['order'] = order

        results = api.query(table, **params)

        return {
            "success": True,
            "data": results,
            "error": None,
            "metadata": {
                "rows": len(results),
                "project": project,
                "table": table
            }
        }

    except Exception as e:
        error_msg = str(e)
        suggestion = f"Try using supabase_discover('{project}') to see available tables"

        if "does not exist" in error_msg.lower():
            suggestion = f"Table '{table}' not found. Use supabase_discover('{project}') to list tables"
        elif "column" in error_msg.lower():
            suggestion = f"Column issue. Use supabase_discover('{project}', '{table}') to see schema"

        return {
            "success": False,
            "data": None,
            "error": error_msg,
            "suggestion": suggestion
        }


def supabase_discover(project: str, table: str = None) -> dict:
    """
    Discover tables or get schema for a specific table.

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        table: Optional table name to get schema for

    Returns:
        {success: bool, data: dict, error: str}
    """
    try:
        api = SupabaseAPI(project)

        if table:
            # Get schema for specific table
            schema = api.get_schema(table)

            # Get sample data
            sample = api.query(table, limit=2)

            return {
                "success": True,
                "data": {
                    "table": table,
                    "columns": schema,
                    "sample_data": sample
                },
                "error": None,
                "metadata": {
                    "project": project,
                    "column_count": len(schema)
                }
            }
        else:
            # List all tables with row counts
            info = api.discover()

            return {
                "success": True,
                "data": info,
                "error": None,
                "metadata": {
                    "project": project,
                    "table_count": len(info.get('tables', []))
                }
            }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check project name is valid: smoothed, blingsting, or scraping"
        }


def supabase_raw_query(project: str, sql: str) -> dict:
    """
    Execute raw SQL query (SELECT only, auto-limited to 1000 rows).

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        sql: SQL query string (SELECT statements only)

    Returns:
        {success: bool, data: list, error: str}
    """
    try:
        api = SupabaseAPI(project)
        results = api.raw_query(sql)

        return {
            "success": True,
            "data": results,
            "error": None,
            "metadata": {
                "rows": len(results),
                "project": project
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Only SELECT queries are supported. Ensure SQL syntax is valid."
        }


def supabase_insert(project: str, table: str, data: dict) -> dict:
    """
    Insert a record into a Supabase table.

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        table: Table name
        data: Dictionary of column: value pairs to insert

    Returns:
        {success: bool, data: dict, error: str}
    """
    try:
        api = SupabaseAPI(project)
        result = api.insert(table, data)

        return {
            "success": True,
            "data": result,
            "error": None,
            "metadata": {
                "project": project,
                "table": table,
                "inserted": True
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": f"Check schema with supabase_discover('{project}', '{table}')"
        }


def supabase_update(project: str, table: str, filters: dict, data: dict) -> dict:
    """
    Update records in a Supabase table.

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        table: Table name
        filters: Filter dict to identify records (e.g., {'id': 'eq.123'})
        data: Dictionary of column: value pairs to update

    Returns:
        {success: bool, data: dict, error: str}
    """
    try:
        api = SupabaseAPI(project)
        result = api.update(table, filters, data)

        return {
            "success": True,
            "data": result,
            "error": None,
            "metadata": {
                "project": project,
                "table": table,
                "updated": True
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Ensure filters identify specific records to update"
        }


def supabase_rpc(project: str, function_name: str, params: dict = None) -> dict:
    """
    Call a PostgreSQL function via Supabase RPC.

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        function_name: Name of the PostgreSQL function
        params: Optional parameters to pass to the function

    Returns:
        {success: bool, data: any, error: str}
    """
    try:
        api = SupabaseAPI(project)
        result = api.rpc(function_name, params or {})

        return {
            "success": True,
            "data": result,
            "error": None,
            "metadata": {
                "project": project,
                "function": function_name
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": f"Check function '{function_name}' exists and parameter types match"
        }


def supabase_invoke_function(project: str, function_name: str,
                             body: dict = None, method: str = "POST") -> dict:
    """
    Invoke a Supabase Edge Function (Deno serverless function).

    Args:
        project: Project name (smoothed, blingsting, or scraping)
        function_name: Name of the edge function
        body: Optional request body to send
        method: HTTP method (default POST)

    Returns:
        {success: bool, data: any, error: str}
    """
    try:
        api = SupabaseAPI(project)
        result = api.invoke_function(function_name, body or {}, method=method)

        return {
            "success": True,
            "data": result,
            "error": None,
            "metadata": {
                "project": project,
                "function": function_name,
                "method": method
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": f"Check edge function '{function_name}' is deployed and accessible"
        }


# Tool registry for MCP
SUPABASE_TOOLS = [
    {
        "name": "query_supabase",
        "description": "Query a Supabase table with optional filters",
        "function": query_supabase
    },
    {
        "name": "supabase_discover",
        "description": "List tables or get schema for specific table",
        "function": supabase_discover
    },
    {
        "name": "supabase_raw_query",
        "description": "Execute raw SQL query (SELECT only)",
        "function": supabase_raw_query
    },
    {
        "name": "supabase_insert",
        "description": "Insert record into table",
        "function": supabase_insert
    },
    {
        "name": "supabase_update",
        "description": "Update records in table",
        "function": supabase_update
    },
    {
        "name": "supabase_rpc",
        "description": "Call PostgreSQL function via RPC",
        "function": supabase_rpc
    },
    {
        "name": "supabase_invoke_function",
        "description": "Invoke Supabase Edge Function (Deno serverless)",
        "function": supabase_invoke_function
    }
]


if __name__ == "__main__":
    # Test the tools
    print("Testing Supabase tools...")

    # Test discover
    print("\n1. Testing supabase_discover...")
    result = supabase_discover('project1')
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Tables found: {result['metadata']['table_count']}")

    # Test query
    print("\n2. Testing query_supabase...")
    result = query_supabase('project1', 'leads', limit=2)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Rows returned: {result['metadata']['rows']}")
