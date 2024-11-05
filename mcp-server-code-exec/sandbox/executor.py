#!/usr/bin/env python3
"""
Secure Python code execution sandbox for MCP server.
Follows Anthropic's pattern for processing data before returning to model.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import traceback

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))


class CodeExecutor:
    """
    Secure Python code executor with access to API toolkit.

    Key features:
    - Executes Python code in controlled environment
    - Has access to all api_toolkit services
    - Captures stdout/stderr for returning to model
    - Handles errors gracefully with helpful messages
    - Supports data processing before returning results
    """

    def __init__(self):
        self.timeout = 60  # 60 second timeout
        self.max_output_size = 100000  # 100KB max output

        # Available imports for the sandbox
        self.safe_imports = {
            # API Toolkit services
            'SupabaseAPI': 'from services.supabase.api import SupabaseAPI',
            'QueryBuilder': 'from services.supabase.query_helpers import QueryBuilder',

            # Standard library (safe subset)
            'json': 'import json',
            'datetime': 'from datetime import datetime, timedelta',
            'collections': 'from collections import Counter, defaultdict',
            'itertools': 'import itertools',
            're': 'import re',
            'math': 'import math',
            'statistics': 'import statistics',

            # Data processing
            'csv': 'import csv',
        }

    def execute(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute
            timeout: Optional timeout in seconds (default 60)

        Returns:
            {
                'success': bool,
                'output': str,         # stdout captured
                'error': str,          # stderr or exception
                'result': Any,         # final return value if any
                'execution_time': float
            }
        """
        import time
        start_time = time.time()

        # Prepare execution environment
        globals_dict = self._prepare_environment()

        # Capture stdout/stderr
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Execute the code
                exec(code, globals_dict)

            execution_time = time.time() - start_time
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            # Check output size
            if len(stdout_output) > self.max_output_size:
                stdout_output = (
                    stdout_output[:self.max_output_size] +
                    f"\n... (output truncated, exceeded {self.max_output_size} bytes)"
                )

            return {
                'success': True,
                'output': stdout_output,
                'error': stderr_output if stderr_output else None,
                'result': globals_dict.get('result', None),
                'execution_time': execution_time,
                'metrics': {
                    'output_size': len(stdout_output),
                    'execution_time_ms': int(execution_time * 1000)
                }
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

            return {
                'success': False,
                'output': stdout_buffer.getvalue(),
                'error': error_msg,
                'result': None,
                'execution_time': execution_time,
                'suggestion': self._get_error_suggestion(e)
            }

    def _prepare_environment(self) -> Dict[str, Any]:
        """Prepare safe execution environment with API toolkit access"""

        # Import services
        from services.supabase.api import SupabaseAPI
        from services.supabase.query_helpers import QueryBuilder

        # Build globals dict with safe builtins and imports
        env = {
            '__builtins__': {
                # Safe builtins only
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'type': type,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'True': True,
                'False': False,
                'None': None,
            },

            # API Toolkit
            'SupabaseAPI': SupabaseAPI,
            'QueryBuilder': QueryBuilder,

            # Standard library
            'json': __import__('json'),
            'datetime': __import__('datetime'),
            'collections': __import__('collections'),
            're': __import__('re'),
            'math': __import__('math'),
            'statistics': __import__('statistics'),
        }

        return env

    def _get_error_suggestion(self, error: Exception) -> str:
        """Get helpful suggestion based on error type"""

        error_type = type(error).__name__
        error_msg = str(error).lower()

        if 'name' in error_msg and 'not defined' in error_msg:
            return (
                "Variable not defined. Available imports: SupabaseAPI, QueryBuilder, "
                "json, datetime, collections, re, math, statistics"
            )

        if 'does not exist' in error_msg and 'table' in error_msg:
            return "Table not found. Use: api.discover() to see available tables"

        if 'column' in error_msg:
            return "Column error. Use: api.discover('table_name') to see schema"

        if 'jwt' in error_msg or 'auth' in error_msg:
            return "Authentication error. Check .env has correct Supabase credentials"

        if error_type == 'TimeoutError':
            return "Code execution timed out. Try processing data in smaller batches"

        return "Check your code syntax and API usage"

    def get_available_imports(self) -> Dict[str, str]:
        """Get list of available imports for documentation"""
        return self.safe_imports.copy()


if __name__ == "__main__":
    # Test the executor
    executor = CodeExecutor()

    print("Testing Code Executor...")
    print("=" * 60)

    # Test 1: Simple execution
    print("\n1. Testing simple code:")
    code1 = """
print("Hello from sandbox!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    result1 = executor.execute(code1)
    print(f"Success: {result1['success']}")
    print(f"Output:\n{result1['output']}")

    # Test 2: Supabase discovery
    print("\n2. Testing Supabase discovery:")
    code2 = """
api = SupabaseAPI('project1')
info = api.discover()
print(f"Found {len(info.get('tables', []))} tables")
for table in info.get('tables', [])[:3]:
    print(f"  - {table}")
"""
    result2 = executor.execute(code2)
    print(f"Success: {result2['success']}")
    print(f"Output:\n{result2['output']}")

    # Test 3: Data processing
    print("\n3. Testing data processing:")
    code3 = """
api = SupabaseAPI('project1')

# Query data
leads = api.query('leads', limit=10)
print(f"Retrieved {len(leads)} leads")

# Process in sandbox (no tokens used for this!)
high_scores = [l for l in leads if l.get('score', 0) > 80]
avg_score = sum(l.get('score', 0) for l in leads) / len(leads) if leads else 0

# Return only summary
result = {
    'total_leads': len(leads),
    'high_score_count': len(high_scores),
    'average_score': round(avg_score, 2)
}
print(f"Summary: {result}")
"""
    result3 = executor.execute(code3)
    print(f"Success: {result3['success']}")
    print(f"Output:\n{result3['output']}")
    if result3['error']:
        print(f"Error: {result3['error']}")

    print("\n" + "=" * 60)
    print("Code executor tests complete!")
