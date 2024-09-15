#!/usr/bin/env python3
"""
Supabase Query Helpers
Provides common query patterns and builders for Supabase operations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class QueryBuilder:
    """Helper class to build Supabase queries more intuitively"""
    
    def __init__(self, table: str):
        self.table = table
        self.filters = {}
        self.select_cols = "*"
        self.order_by = None
        self.limit_count = None
        self.offset_count = None
    
    def select(self, *columns):
        """Select specific columns"""
        if columns:
            self.select_cols = ",".join(columns)
        return self
    
    def where(self, column: str, operator: str, value: Any):
        """Add a where clause"""
        op_map = {
            '=': 'eq',
            '==': 'eq',
            '!=': 'neq',
            '<>': 'neq',
            '>': 'gt',
            '>=': 'gte',
            '<': 'lt',
            '<=': 'lte',
            'like': 'like',
            'ilike': 'ilike',
            'is': 'is',
            'in': 'in'
        }
        
        op = op_map.get(operator, operator)
        self.filters[column] = f"{op}.{value}"
        return self
    
    def equals(self, column: str, value: Any):
        """Shorthand for equality"""
        return self.where(column, '=', value)
    
    def contains(self, column: str, value: str):
        """Search for substring (case-insensitive)"""
        return self.where(column, 'ilike', f'%{value}%')
    
    def between(self, column: str, start: Any, end: Any):
        """Between two values"""
        self.filters[column] = f"gte.{start}"
        self.filters[column] = f"lte.{end}"
        return self
    
    def order(self, column: str, desc: bool = False):
        """Order results"""
        self.order_by = f"-{column}" if desc else column
        return self
    
    def limit(self, count: int):
        """Limit results"""
        self.limit_count = count
        return self
    
    def offset(self, count: int):
        """Offset results"""
        self.offset_count = count
        return self
    
    def build(self) -> Dict:
        """Build the query parameters"""
        params = {
            'select': self.select_cols,
            'filters': self.filters if self.filters else None,
            'order': self.order_by,
            'limit': self.limit_count,
            'offset': self.offset_count
        }
        # Remove None values
        return {k: v for k, v in params.items() if v is not None}
    
    def execute(self, api):
        """Execute the query with the given API instance"""
        params = self.build()
        return api.query(self.table, **params)


class CommonQueries:
    """Common query patterns for Supabase"""
    
    @staticmethod
    def recent_records(table: str, days: int = 7, date_column: str = 'created_at') -> Dict:
        """Get records from the last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        return {
            'filters': {date_column: f'gte.{date_threshold}'},
            'order': f'-{date_column}'
        }
    
    @staticmethod
    def search_text(table: str, search_term: str, columns: List[str]) -> Dict:
        """Search multiple text columns"""
        # For Supabase, we need to use OR logic which requires RPC
        # This returns filters for a single column search
        filters = {}
        for col in columns[:1]:  # Simplified for now
            filters[col] = f'ilike.%{search_term}%'
        return {'filters': filters}
    
    @staticmethod
    def paginated(table: str, page: int = 1, per_page: int = 20) -> Dict:
        """Paginated query"""
        return {
            'limit': per_page,
            'offset': (page - 1) * per_page
        }
    
    @staticmethod
    def active_only(table: str, status_column: str = 'status') -> Dict:
        """Get only active records"""
        return {
            'filters': {status_column: 'eq.active'}
        }
    
    @staticmethod
    def by_email(table: str, email: str) -> Dict:
        """Find by email"""
        return {
            'filters': {'email': f'eq.{email}'},
            'limit': 1
        }
    
    @staticmethod
    def by_id(table: str, id_value: Any, id_column: str = 'id') -> Dict:
        """Find by ID"""
        return {
            'filters': {id_column: f'eq.{id_value}'},
            'limit': 1
        }


class TablePatterns:
    """Common patterns for specific table types"""
    
    @staticmethod
    def users_active_recent(days: int = 30) -> Dict:
        """Active users in last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        return {
            'filters': {
                'status': 'eq.active',
                'last_login': f'gte.{date_threshold}'
            },
            'order': '-last_login'
        }
    
    @staticmethod
    def orders_by_status(status: str) -> Dict:
        """Orders filtered by status"""
        return {
            'filters': {'status': f'eq.{status}'},
            'order': '-created_at'
        }
    
    @staticmethod
    def products_in_stock(min_quantity: int = 1) -> Dict:
        """Products with stock above threshold"""
        return {
            'filters': {
                'quantity': f'gte.{min_quantity}',
                'active': 'eq.true'
            },
            'order': 'name'
        }


# ============= USAGE EXAMPLES =============

def example_usage():
    """Examples of using query helpers"""
    from services.supabase.api import SupabaseAPI
    
    api = SupabaseAPI('project1')
    
    # Using QueryBuilder
    query = (QueryBuilder('users')
             .select('id', 'email', 'name')
             .where('status', '=', 'active')
             .where('created_at', '>=', '2024-01-01')
             .order('created_at', desc=True)
             .limit(10))
    
    results = query.execute(api)
    
    # Using CommonQueries
    params = CommonQueries.recent_records('logs', days=7)
    logs = api.query('logs', **params)
    
    # Using TablePatterns
    params = TablePatterns.users_active_recent(days=30)
    active_users = api.query('users', **params)
    
    return results


if __name__ == "__main__":
    # Demo the query builder
    print("Query Builder Examples:")
    print("=" * 50)
    
    # Example 1: Simple select
    q1 = QueryBuilder('users').select('id', 'email').limit(5)
    print(f"Simple select: {q1.build()}")
    
    # Example 2: With filters
    q2 = (QueryBuilder('orders')
          .where('status', '=', 'pending')
          .where('amount', '>', 100)
          .order('created_at', desc=True))
    print(f"With filters: {q2.build()}")
    
    # Example 3: Search
    q3 = QueryBuilder('products').contains('name', 'widget').limit(10)
    print(f"Search: {q3.build()}")
    
    print("\nCommon Query Patterns:")
    print("=" * 50)
    
    print(f"Recent records: {CommonQueries.recent_records('logs', days=3)}")
    print(f"Paginated: {CommonQueries.paginated('users', page=2, per_page=25)}")
    print(f"By email: {CommonQueries.by_email('users', 'test@example.com')}")