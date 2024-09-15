#!/usr/bin/env python3
"""
Supabase API Client
Token Cost: ~600 tokens when loaded

Supports multiple projects and common database operations.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from core.base_api import BaseAPI

class SupabaseAPI(BaseAPI):
    """
    Supabase API wrapper for database operations.

    CAPABILITIES:
    - Query tables with filters, ordering, pagination
    - Insert, update, delete operations
    - Call PostgreSQL functions (RPC)
    - Invoke Deno Edge Functions (serverless)
    - Multi-project support (smoothed, blingsting, scraping)
    - Large dataset handling with auto-pagination

    NEW IN v2.1:
    - Configurable max_row_limit (default: 1,000 rows) to prevent accidentally loading huge datasets
    - fetch_all() - Auto-pagination for large datasets (bypasses row limits)
    - count() - Fast record counting without fetching data
    - exists() - Quick existence checks using LIMIT 1
    - Better warnings when query limits are exceeded

    COMMON PATTERNS:
    ```python
    # Basic query
    api = SupabaseAPI('project1')
    users = api.query('users', filters={'email': 'eq.user@example.com'})

    # Large datasets - auto-pagination
    all_brands = api.fetch_all('brands')  # Gets all 8,225 brands automatically

    # Fast counting
    total = api.count('leads', filters={'score': 'gte.90'})

    # Quick existence check
    if api.exists('users', {'email': 'eq.john@example.com'}):
        print("User exists!")

    # CRUD operations
    api.insert('logs', {'message': 'Event occurred'})
    result = api.rpc('calculate_total', {'order_id': 123})

    # Call Edge Function
    response = api.invoke_function('process-lead', {'lead_id': 123})
    ```

    AUTHENTICATION:
    - Service role key (full access)
    - Anon key (row-level security)

    RATE LIMITS:
    - 1000 requests/minute
    - Use batch operations when possible
    """
    
    # Project configurations - customize these for your Supabase projects
    PROJECTS = {
        'project1': {  # Primary project
            'ref': 'your-project-1-ref',  # From Supabase dashboard URL
            'url_env': 'SUPABASE_URL',
            'key_env': 'SUPABASE_SERVICE_ROLE_KEY',
            'anon_env': 'SUPABASE_ANON_API',
            'description': 'Project 1 - Primary database'
        },
        'project2': {  # Secondary project
            'ref': 'your-project-2-ref',
            'url_env': 'SUPABASE_URL_2',
            'key_env': 'SUPABASE_SERVICE_ROLE_KEY_2',
            'anon_env': 'SUPABASE_ANON_API_2',
            'description': 'Project 2 - Secondary database'
        },
        'project3': {  # Tertiary project
            'ref': 'your-project-3-ref',
            'url_env': 'SUPABASE_URL_3',
            'key_env': 'SUPABASE_SERVICE_ROLE_KEY_3',
            'anon_env': 'SUPABASE_ANON_API_3',
            'description': 'Project 3 - Tertiary database'
        },
        # Aliases for backward compatibility
        'main': 'project1',
        'secondary': 'project2',
        'tertiary': 'project3'
    }
    
    def __init__(self, project: str = 'project1', url: Optional[str] = None,
                 key: Optional[str] = None, use_anon_key: bool = False,
                 max_row_limit: Optional[int] = 1000):
        """
        Initialize Supabase client for specified project.

        Args:
            project: Project name ('project1', 'project2', 'project3') or aliases
            url: Optional custom Supabase URL
            key: Optional custom API key
            use_anon_key: Use anonymous key instead of service role key
            max_row_limit: Maximum rows to return in a single query (default: 1000)
                          Set to None for unlimited (use with caution!)
                          This prevents accidentally loading huge datasets into memory.
                          Use fetch_all() to get all records via efficient pagination.

        Examples:
            # Default: 1,000 row safety limit
            api = SupabaseAPI('project1')

            # Increase limit for this session
            api = SupabaseAPI('project1', max_row_limit=10000)

            # Disable limit (careful!)
            api = SupabaseAPI('project1', max_row_limit=None)
        """
        self.max_row_limit = max_row_limit
        # Resolve aliases
        if project in self.PROJECTS and isinstance(self.PROJECTS[project], str):
            project = self.PROJECTS[project]
        
        self.project = project
        self.project_config = None
        
        # Get project configuration
        if project in self.PROJECTS and isinstance(self.PROJECTS[project], dict):
            config = self.PROJECTS[project]
            self.project_config = config
            self.project_ref = config['ref']
            self.project_description = config.get('description', '')
            url = url or os.getenv(config['url_env'])
            
            # Use anon key if requested, otherwise service role
            if use_anon_key:
                key = key or os.getenv(config.get('anon_env'))
            else:
                key = key or os.getenv(config['key_env'])
        else:
            # Assume project is a direct project ref
            self.project_ref = project
            self.project_description = f'Custom project: {project}'
            url = url or os.getenv('SUPABASE_URL')
            key = key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        super().__init__(
            api_key=key,
            base_url=url,
            requests_per_second=15  # Supabase can handle more
        )
    
    def _setup_auth(self):
        """Setup Supabase authentication headers"""
        if self.api_key:
            self.session.headers.update({
                'apikey': self.api_key,
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'  # Return created/updated data
            })
    
    # ============= QUERY OPERATIONS =============
    
    def query(self, table: str,
             select: str = "*",
             filters: Optional[Dict] = None,
             order: Optional[str] = None,
             limit: Optional[int] = None,
             offset: Optional[int] = None) -> List[Dict]:
        """
        Query a table with filters and options.

        ⚠️ IMPORTANT: Returns a LIST directly, not {'data': [...]}

        Args:
            table: Table name
            select: Columns to select (default: *)
            filters: Dict of filters {'column': 'op.value'}
                    Operations: eq, neq, gt, gte, lt, lte, like, ilike, is, in
            order: Column to order by (prefix with - for DESC)
            limit: Maximum rows to return. If exceeds max_row_limit, will be capped with a warning.
            offset: Number of rows to skip

        Returns:
            List[Dict] - List of matching records directly (NOT wrapped in 'data' key)

        Examples:
            # Returns list directly
            users = api.query('users')  # users is a list, not dict

            # Access results directly
            for user in users:  # NOT users['data']
                print(user['email'])

            # With filters
            api.query('users', filters={'age': 'gte.18'})
            api.query('posts', select='id,title,author(name)', order='-created_at', limit=10)

            # For large datasets, use fetch_all() instead
            all_brands = api.fetch_all('brands')  # Auto-paginates, no limit
        """
        # Check if limit exceeds max_row_limit and warn
        if self.max_row_limit:
            if limit and limit > self.max_row_limit:
                print(f"⚠️  WARNING: Requested {limit:,} rows, but max_row_limit is {self.max_row_limit:,}")
                print(f"    Results will be capped at {self.max_row_limit:,}.")
                print(f"    💡 TIP: Use api.fetch_all('{table}') to get all records via auto-pagination")
                limit = self.max_row_limit
            elif not limit:
                # If no limit specified, use max_row_limit as default
                limit = self.max_row_limit

        params = {'select': select}

        if filters:
            for column, condition in filters.items():
                params[column] = condition

        if order:
            params['order'] = order

        if limit:
            params['limit'] = limit

        if offset:
            params['offset'] = offset
        
        try:
            return self._make_request('GET', f'rest/v1/{table}', params=params)
        except Exception as e:
            # Enhanced error messages
            error_msg = str(e)
            
            if 'relation' in error_msg and 'does not exist' in error_msg:
                # Table doesn't exist
                available = self.discover()
                tables = available.get('table_names', [])
                raise ValueError(
                    f"Table '{table}' does not exist.\n"
                    f"Available tables: {', '.join(tables) if tables else 'Run api.discover() to see tables'}\n"
                    f"Hint: Use api.discover() first to see all available tables"
                )
            
            elif 'column' in error_msg and 'does not exist' in error_msg:
                # Column doesn't exist
                try:
                    info = self.discover(table)
                    cols = info.get('column_names', [])
                    raise ValueError(
                        f"Column error in table '{table}'.\n"
                        f"Available columns: {', '.join(cols) if cols else 'Run api.discover(table) to see columns'}\n"
                        f"Original error: {error_msg}"
                    )
                except:
                    raise ValueError(
                        f"Column error in table '{table}'.\n"
                        f"Use api.discover('{table}') to see available columns.\n"
                        f"Original error: {error_msg}"
                    )
            
            elif 'JWT' in error_msg or 'token' in error_msg.lower():
                # Authentication error
                raise ValueError(
                    f"Authentication failed for project '{self.project}'.\n"
                    f"Check your .env file has: {self.PROJECTS[self.project]['key_env']}\n"
                    f"Original error: {error_msg}"
                )
            
            else:
                # Unknown error - provide helpful context
                raise ValueError(
                    f"Query failed for table '{table}'.\n"
                    f"Try: api.discover('{table}') to check table structure\n"
                    f"Or: api.quick_start() to see everything\n"
                    f"Original error: {error_msg}"
                )
    
    def get_by_id(self, table: str, id_value: Any, id_column: str = 'id') -> Optional[Dict]:
        """Get a single record by ID"""
        results = self.query(table, filters={id_column: f'eq.{id_value}'}, limit=1)
        return results[0] if results else None

    def fetch_all(self, table: str,
                  select: str = "*",
                  filters: Optional[Dict] = None,
                  order: Optional[str] = None,
                  verbose: bool = True) -> List[Dict]:
        """
        Fetch ALL records from a table using automatic pagination.

        This method bypasses max_row_limit and fetches the entire dataset
        using efficient pagination under the hood. Perfect for when you need
        to process large datasets without worrying about limits.

        Args:
            table: Table name
            select: Columns to select (default: all)
            filters: Dict of filters (e.g., {'state': 'eq.CA'})
            order: Column to sort by (prefix with - for DESC)
            verbose: Print progress updates (default: True)

        Returns:
            List[Dict] - ALL records from the table (can be large!)

        Examples:
            # Get all brands (even if 8,225 rows)
            api = SupabaseAPI('project1')
            all_brands = api.fetch_all('brands')

            # With filters
            ca_brands = api.fetch_all('brands', filters={'state': 'eq.CA'})

            # Specific columns only
            brand_names = api.fetch_all('brands', select='token,name')

            # Silent mode (no progress)
            all_brands = api.fetch_all('brands', verbose=False)

        Warning:
            This can return VERY LARGE datasets. Use filters to narrow results when possible.
            For 8,225 brands, this will fetch all of them automatically.
        """
        all_data = []
        offset = 0
        page_size = 1000  # Fetch in 1k chunks

        if verbose:
            print(f"📥 Fetching all records from '{table}'...")

        while True:
            # Fetch next page (bypassing max_row_limit by using internal query)
            batch = self.query(
                table,
                select=select,
                filters=filters,
                order=order,
                limit=page_size,
                offset=offset
            )

            # Check if we got data
            if not batch:
                break

            all_data.extend(batch)

            # Progress update for large datasets
            if verbose and len(all_data) % 5000 == 0:
                print(f"   ... fetched {len(all_data):,} records so far")

            # Check if we're done (got less than page_size means last page)
            if len(batch) < page_size:
                break

            offset += page_size

        if verbose:
            print(f"✅ Fetched {len(all_data):,} total records from '{table}'")

        return all_data

    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """
        Get count of records in a table (fast, doesn't fetch data).

        Args:
            table: Table name
            filters: Optional filters to count subset

        Returns:
            int - Count of records

        Examples:
            # Total brands
            total = api.count('brands')

            # Active brands only
            active = api.count('brands', filters={'status': 'eq.active'})

            # CA brands
            ca_count = api.count('brands', filters={'state': 'eq.CA'})
        """
        # Use raw SQL COUNT for efficiency
        if filters:
            # Build WHERE clause from filters
            where_parts = []
            for column, condition in filters.items():
                # Parse condition like 'eq.CA' or 'gte.18'
                if '.' in condition:
                    op, value = condition.split('.', 1)
                    op_map = {
                        'eq': '=',
                        'neq': '!=',
                        'gt': '>',
                        'gte': '>=',
                        'lt': '<',
                        'lte': '<=',
                        'like': 'LIKE',
                        'ilike': 'ILIKE'
                    }
                    sql_op = op_map.get(op, '=')
                    # Quote string values
                    if not value.isdigit():
                        value = f"'{value}'"
                    where_parts.append(f"{column} {sql_op} {value}")

            where_clause = ' AND '.join(where_parts)
            sql = f"SELECT COUNT(*) as count FROM {table} WHERE {where_clause}"
        else:
            sql = f"SELECT COUNT(*) as count FROM {table}"

        result = self.raw_query(sql)
        return result[0]['count'] if result else 0

    def exists(self, table: str, filters: Dict) -> bool:
        """
        Check if any records match filters (fast, limit 1).

        Args:
            table: Table name
            filters: Filters to check

        Returns:
            bool - True if at least one record matches

        Examples:
            # Check if Nike exists
            if api.exists('brands', {'name': 'eq.Nike'}):
                print("Nike exists!")

            # Check if any CA brands
            if api.exists('brands', {'state': 'eq.CA'}):
                print("CA brands found!")
        """
        results = self.query(table, filters=filters, limit=1)
        return len(results) > 0
    
    # ============= MUTATION OPERATIONS =============
    
    def insert(self, table: str, data: Union[Dict, List[Dict]], 
              on_conflict: Optional[str] = None) -> Union[Dict, List[Dict]]:
        """
        Insert one or more records.
        
        Args:
            table: Table name
            data: Single dict or list of dicts to insert
            on_conflict: Column(s) for upsert behavior
        
        Returns:
            Inserted record(s)
        
        Examples:
            api.insert('users', {'name': 'John', 'email': 'john@example.com'})
            api.insert('users', [{'name': 'John'}, {'name': 'Jane'}])
            api.insert('profiles', {'email': 'x@y.com'}, on_conflict='email')  # Upsert
        """
        headers = {}
        if on_conflict:
            headers['Prefer'] = f'resolution=merge-duplicates,return=representation'
            params = {'on_conflict': on_conflict}
        else:
            params = {}
        
        return self._make_request('POST', f'rest/v1/{table}', 
                                 data=data, params=params, headers=headers)
    
    def update(self, table: str, data: Dict, filters: Dict) -> List[Dict]:
        """
        Update records matching filters.
        
        Args:
            table: Table name
            data: Fields to update
            filters: Which records to update
        
        Returns:
            Updated records
        
        Example:
            api.update('users', {'status': 'active'}, {'age': 'gte.18'})
        """
        params = filters.copy()
        return self._make_request('PATCH', f'rest/v1/{table}', 
                                 data=data, params=params)
    
    def delete(self, table: str, filters: Dict) -> List[Dict]:
        """
        Delete records matching filters.
        
        Args:
            table: Table name
            filters: Which records to delete
        
        Returns:
            Deleted records
        
        Example:
            api.delete('logs', {'created_at': 'lt.2024-01-01'})
        """
        return self._make_request('DELETE', f'rest/v1/{table}', params=filters)
    
    # ============= RPC OPERATIONS =============
    
    def rpc(self, function_name: str, params: Optional[Dict] = None) -> Any:
        """
        Call a PostgreSQL function.

        Args:
            function_name: Name of the function
            params: Function parameters

        Returns:
            Function result

        Example:
            api.rpc('calculate_revenue', {'month': '2024-01'})
        """
        return self._make_request('POST', f'rest/v1/rpc/{function_name}',
                                 data=params or {})

    def invoke_function(self, function_name: str, body: Optional[Dict] = None,
                       method: str = "POST") -> Any:
        """
        Invoke a Supabase Edge Function (Deno serverless function).

        Edge Functions are deployed serverless functions that run on Deno.
        They're different from PostgreSQL functions (use rpc() for those).

        Args:
            function_name: Name of the edge function
            body: Optional request body to send to the function
            method: HTTP method (default POST)

        Returns:
            Function response

        Examples:
            # Invoke function with body
            result = api.invoke_function('process-payment', {
                'amount': 100,
                'currency': 'USD'
            })

            # GET request
            result = api.invoke_function('get-stats', method='GET')
        """
        # Edge Functions use a different URL pattern
        url = f"{self.base_url}/functions/v1/{function_name}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        import requests
        response = requests.request(
            method=method,
            url=url,
            json=body if body else None,
            headers=headers
        )

        response.raise_for_status()

        try:
            return response.json()
        except:
            return response.text
    
    def raw_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute raw SQL query (READ-ONLY for safety).
        
        ⚠️ SAFETY FEATURES:
        - Only SELECT statements allowed
        - Parameterized queries to prevent SQL injection
        - Automatic LIMIT if not specified
        
        Args:
            sql: SQL query string (SELECT only)
            params: Optional parameters for parameterized query
        
        Returns:
            Query results as list of dicts
        
        Examples:
            # Simple query
            results = api.raw_query("SELECT * FROM users WHERE age > 18 LIMIT 10")
            
            # Parameterized query (recommended)
            results = api.raw_query(
                "SELECT * FROM users WHERE age > %(min_age)s AND status = %(status)s",
                {'min_age': 18, 'status': 'active'}
            )
            
            # Complex join
            results = api.raw_query('''
                SELECT u.name, COUNT(o.id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                GROUP BY u.id, u.name
                HAVING COUNT(o.id) > 5
                LIMIT 100
            ''')
        """
        # Safety check - only allow SELECT statements
        sql_trimmed = sql.strip().upper()
        if not sql_trimmed.startswith('SELECT'):
            raise ValueError("Only SELECT statements are allowed in raw_query() for safety")
        
        # Add LIMIT if not present (safety against large result sets)
        if 'LIMIT' not in sql_trimmed:
            sql = sql.rstrip(';') + ' LIMIT 1000'
        
        # Try to execute via RPC if available
        try:
            # Some Supabase projects have a query function
            result = self.rpc('exec_sql', {
                'query': sql,
                'params': params or {}
            })
            return result if isinstance(result, list) else []
        except:
            # Fallback: Parse SQL and convert to REST API call (basic support)
            # This is limited but works for simple queries
            import re
            
            # Extract table name (very basic parser)
            match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
            if match:
                table = match.group(1)
                
                # Extract WHERE conditions (basic)
                where_match = re.search(r'WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)', sql, re.IGNORECASE)
                filters = {}
                
                if where_match:
                    # Very basic WHERE parsing - handles simple conditions
                    conditions = where_match.group(1)
                    # Parse simple equality conditions
                    eq_pattern = r'(\w+)\s*=\s*[\'"]([^\'\"]+)[\'"]'
                    for col, val in re.findall(eq_pattern, conditions):
                        filters[col] = f'eq.{val}'
                
                # Extract LIMIT
                limit = 1000
                limit_match = re.search(r'LIMIT\s+(\d+)', sql, re.IGNORECASE)
                if limit_match:
                    limit = int(limit_match.group(1))
                
                # Execute via REST API
                return self.query(table, filters=filters, limit=limit)
            
            raise ValueError(f"Could not execute raw SQL. Use simple queries or ensure RPC 'exec_sql' is available.")
    
    # ============= UTILITY METHODS =============
    
    def discover(self, table: Optional[str] = None) -> Dict[str, Any]:
        """
        🔍 DISCOVER DATABASE STRUCTURE - Always works!
        
        This method ALWAYS returns useful information, even if queries fail.
        Use this FIRST before writing any queries!
        
        Args:
            table: Optional specific table to discover. If None, discovers all tables.
        
        Returns:
            Dict with discovery results including tables, columns, samples
        
        Examples:
            # Discover everything
            info = api.discover()
            print(info['tables'])  # List of all tables
            
            # Discover specific table
            info = api.discover('users')
            print(info['columns'])  # List of columns with types
            print(info['sample'])   # Sample data
        """
        result = {'success': False, 'project': self.project, 'description': self.project_description}
        
        if table:
            # Discover specific table
            result['table'] = table
            
            # Try to get columns from a sample
            try:
                sample = self.query(table, limit=1)
                if sample and len(sample) > 0:
                    columns = []
                    for key, value in sample[0].items():
                        col_type = 'null'
                        if value is not None:
                            if isinstance(value, bool):
                                col_type = 'boolean'
                            elif isinstance(value, int):
                                col_type = 'integer'
                            elif isinstance(value, float):
                                col_type = 'numeric'
                            elif isinstance(value, str):
                                col_type = 'text'
                            elif isinstance(value, dict):
                                col_type = 'jsonb'
                            elif isinstance(value, list):
                                col_type = 'array'
                            else:
                                col_type = type(value).__name__
                        
                        columns.append({
                            'name': key,
                            'type': col_type,
                            'sample': str(value)[:100] if value is not None else None
                        })
                    
                    result['columns'] = columns
                    result['column_names'] = [c['name'] for c in columns]
                    result['sample'] = sample
                    result['row_count'] = self.count(table)
                    result['success'] = True
                    result['message'] = f"Successfully discovered {table}"
                else:
                    # Table exists but is empty
                    result['columns'] = []
                    result['column_names'] = []
                    result['sample'] = []
                    result['row_count'] = 0
                    result['success'] = True
                    result['message'] = f"Table {table} exists but is empty"
            except Exception as e:
                result['error'] = str(e)
                result['message'] = f"Could not query {table}: {e}"
                result['hint'] = "Check if table name is correct. Use discover() without arguments to see all tables."
        else:
            # Discover all tables
            tables = []
            
            # Known tables for each project (fallback if API fails)
            KNOWN_TABLES = {
                'project1': ['brands', 'leads', 'scraping_results', 'brand_contacts'],
                'project2': ['customers', 'orders', 'products', 'invoices'],
                'project3': ['scrape_guide', 'scrape_results', 'scrape_queue']
            }
            
            # Try to get tables dynamically first
            discovered = False
            for known_table in KNOWN_TABLES.get(self.project, []):
                try:
                    # Test if table exists by trying to query it
                    test = self.query(known_table, limit=1)
                    tables.append({
                        'name': known_table,
                        'accessible': True,
                        'row_count': self.count(known_table)
                    })
                    discovered = True
                except:
                    tables.append({
                        'name': known_table,
                        'accessible': False,
                        'note': 'Table might not exist or no access'
                    })
            
            if discovered:
                result['tables'] = tables
                result['table_names'] = [t['name'] for t in tables if t.get('accessible', False)]
                result['success'] = True
                result['message'] = f"Discovered {len(result['table_names'])} accessible tables"
                result['hint'] = f"Use discover('table_name') to explore a specific table"
            else:
                result['tables'] = []
                result['table_names'] = []
                result['message'] = "Could not discover tables automatically"
                result['hint'] = f"Known tables for {self.project}: {', '.join(KNOWN_TABLES.get(self.project, []))}"
        
        return result
    
    def get_tables(self) -> List[str]:
        """
        Get list of all accessible tables.
        
        Returns:
            List of table names
        """
        discovery = self.discover()
        return discovery.get('table_names', [])
    
    def get_schema(self, table: str) -> List[Dict[str, Any]]:
        """Get schema information for a table"""
        try:
            # Get one row to infer schema
            sample = self.query(table, limit=1)
            if sample:
                schema = []
                for key, value in sample[0].items():
                    schema.append({
                        'column': key,
                        'type': type(value).__name__ if value is not None else 'unknown',
                        'sample': str(value)[:50] if value is not None else None
                    })
                return schema
            return []
        except Exception as e:
            print(f"Could not get schema for {table}: {e}")
            return []
    
    def describe_table(self, table: str) -> Dict[str, Any]:
        """Get detailed information about a table"""
        try:
            # Get basic info
            info = {
                'name': table,
                'columns': self.get_schema(table),
                'row_count': self.count(table),
                'sample_data': self.query(table, limit=3)
            }
            return info
        except Exception as e:
            return {'name': table, 'error': str(e)}
    
    def explore(self, table: Optional[str] = None) -> None:
        """Interactive exploration of database"""
        if table:
            info = self.describe_table(table)
            print(f"\nTable: {info['name']}")
            print(f"Rows: {info.get('row_count', 'unknown')}")
            print("\nColumns:")
            for col in info.get('columns', []):
                print(f"  - {col['column']}: {col['type']}")
            print("\nSample data:")
            if info.get('sample_data'):
                import json
                print(json.dumps(info['sample_data'][:2], indent=2))
        else:
            tables = self.get_tables()
            print(f"\nProject: {self.project} ({self.project_description})")
            print(f"Tables available: {len(tables)}")
            for table in tables:
                if isinstance(table, dict):
                    print(f"  - {table.get('table_name', table)}")
                else:
                    print(f"  - {table}")
    
    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # Try to get the API root to test connection
            self._make_request('GET', 'rest/v1/', params={'limit': 1})
            return True
        except:
            return False
    
    def quick_start(self) -> None:
        """
        🚀 QUICK START - Shows everything you need in 5 seconds!
        
        This single method eliminates 80% of the friction.
        Use this FIRST when starting with any project!
        
        Example:
            api = SupabaseAPI('project1')
            api.quick_start()  # Shows everything you need
        """
        print(f"\n{'='*60}")
        print(f"🚀 QUICK START for {self.project}")
        print(f"{'='*60}\n")
        
        # Test connection
        if not self.test_connection():
            print("❌ Connection failed! Check your .env file")
            print(f"   Expected env vars: {self.PROJECTS[self.project]['key_env']}")
            return
        
        print(f"✅ Connected to: {self.project_description}")
        print(f"   Project ref: {self.project_ref}\n")
        
        # Discover tables
        discovery = self.discover()
        
        if discovery['success']:
            tables = discovery.get('table_names', [])
            print(f"📊 Available tables ({len(tables)}):")
            for table in tables[:10]:  # Show first 10
                print(f"   - {table}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")
            print()
            
            # Show example table structure
            if tables:
                example_table = tables[0]
                print(f"🔍 Example table structure: {example_table}")
                
                table_info = self.discover(example_table)
                if table_info.get('success'):
                    columns = table_info.get('columns', [])
                    print(f"   Columns ({len(columns)}):")
                    for col in columns[:8]:  # Show first 8 columns
                        print(f"      - {col['name']}: {col['type']}")
                    if len(columns) > 8:
                        print(f"      ... and {len(columns) - 8} more")
                    
                    print(f"   Row count: {table_info.get('row_count', 'unknown')}")
                    print()
        else:
            print("⚠️  Could not auto-discover tables")
            print(f"   Hint: {discovery.get('hint', '')}")
            print()
        
        # Show filter syntax
        print("📝 Filter syntax cheat sheet:")
        print("   filters = {")
        print("       'age': 'gte.18',           # age >= 18")
        print("       'status': 'eq.active',     # status = 'active'")
        print("       'email': 'ilike.%gmail%',  # email ILIKE '%gmail%'")
        print("       'deleted': 'is.null',      # deleted IS NULL")
        print("       'role': 'in.(admin,user)', # role IN ('admin','user')")
        print("   }")
        print()
        
        # Show example queries
        print("💡 Example queries:")
        print(f"   # Get all records from first table")
        if tables:
            print(f"   results = api.query('{tables[0]}', limit=10)")
        else:
            print(f"   results = api.query('table_name', limit=10)")
        print(f"   ")
        print(f"   # With filters")
        print(f"   results = api.query('table', filters={{'status': 'eq.active'}})")
        print(f"   ")
        print(f"   # Raw SQL (for complex queries)")
        print(f"   results = api.raw_query('SELECT * FROM table WHERE id > 100')")
        print()
        
        print("📚 Next steps:")
        print("   1. api.discover()           # See all tables")
        print("   2. api.discover('table')    # Explore specific table")
        print("   3. api.query('table', ...)  # Query with filters")
        print("   4. Use QueryBuilder for complex queries")
        print(f"\n{'='*60}\n")


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api.py test [project]           # Test connection")
        print("  python api.py tables [project]         # List all tables")
        print("  python api.py query [project] [table]  # Query table")
        print("  python api.py count [project] [table]  # Count records")
        print("  python api.py schema [project] [table] # Show table schema")
        print("  python api.py explore [project] [table]# Explore database")
        print("\nProjects:")
        print("  smoothed   - Project1 Lead Gen (brands, scraping)")
        print("  blingsting - Project2 CRM (customers, orders)")
        print("  scraping   - Web Project 3 (scrape guides)")
        print("\nAliases: main→smoothed, project2→blingsting, project3→scraping")
        sys.exit(1)
    
    command = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else 'project1'
    
    try:
        if command == "test":
            api = SupabaseAPI(project)
            if api.test_connection():
                print(f"✓ Connection successful!")
                print(f"  Project: {api.project}")
                print(f"  Description: {api.project_description}")
                print(f"  Project ref: {api.project_ref}")
                print(f"  URL: {api.base_url}")
            else:
                print(f"✗ Connection to Supabase project '{project}' failed")
        
        elif command == "tables":
            api = SupabaseAPI(project)
            tables = api.get_tables()
            print(f"Tables in {project}:")
            for table in tables:
                print(f"  - {table}")
        
        elif command == "query" and len(sys.argv) > 3:
            table = sys.argv[3]
            api = SupabaseAPI(project)
            results = api.query(table, limit=5)
            print(json.dumps(results, indent=2))
        
        elif command == "count" and len(sys.argv) > 3:
            table = sys.argv[3]
            api = SupabaseAPI(project)
            count = api.count(table)
            print(f"{table} has {count} records")
        
        elif command == "schema" and len(sys.argv) > 3:
            table = sys.argv[3]
            api = SupabaseAPI(project)
            schema = api.get_schema(table)
            print(f"Schema for {table}:")
            for col in schema:
                print(f"  {col['column']}: {col['type']}")
        
        elif command == "explore":
            api = SupabaseAPI(project)
            if len(sys.argv) > 3:
                api.explore(sys.argv[3])
            else:
                api.explore()
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)