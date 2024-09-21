#!/usr/bin/env python3
"""
Metabase API Client
Token Cost: ~600 tokens when loaded

Provides access to Metabase analytics platform for:
- Running queries and retrieving data
- Managing dashboards and questions
- Accessing collections and datasets
- Exporting data in various formats
"""

import os
import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.base_api import BaseAPI, APIError

class MetabaseAPI(BaseAPI):
    """
    Metabase API wrapper for analytics and business intelligence operations.

    CAPABILITIES:
    - Execute queries (native SQL and MBQL)
    - Manage questions/cards and dashboards
    - Access collections and datasets
    - Export data (CSV, JSON, XLSX)
    - Database metadata exploration

    AUTHENTICATION:
    - API Key (recommended for automation)
    - Session tokens (14-day expiry)

    COMMON PATTERNS:
    ```python
    # Using API Key (recommended)
    api = MetabaseAPI(api_key='mb_your_api_key')

    # Using session authentication
    api = MetabaseAPI()
    api.login('user@example.com', 'password')

    # Query data
    results = api.query_card(123)  # Query saved question
    results = api.run_query('SELECT * FROM users LIMIT 10', database_id=1)
    ```

    RATE LIMITS:
    - Login requests are rate-limited
    - Cache session tokens (14-day validity)
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize Metabase API client.

        Args:
            api_key: API key for authentication (mb_...)
            base_url: Metabase instance URL (e.g., http://localhost:3000)
            username: Username for session auth
            password: Password for session auth
        """
        self.api_key = api_key or os.getenv('METABASE_API_KEY')
        self.base_url = (base_url or os.getenv('METABASE_URL', 'http://localhost:3000')).rstrip('/')
        self.username = username or os.getenv('METABASE_USERNAME')
        self.password = password or os.getenv('METABASE_PASSWORD')
        self.session_token = None
        self.session_expiry = None

        super().__init__(
            api_key=self.api_key,
            base_url=f"{self.base_url}/api",
            requests_per_second=10
        )

        # Auto-login if credentials provided but no API key
        if not self.api_key and self.username and self.password:
            self.login()

    def _setup_auth(self):
        """Setup authentication headers"""
        if self.api_key:
            self.session.headers.update({
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            })
        elif self.session_token:
            self.session.headers.update({
                'X-Metabase-Session': self.session_token,
                'Content-Type': 'application/json'
            })

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> Dict:
        """
        Login with username/password to get session token.

        Args:
            username: User email/username
            password: User password

        Returns:
            Session information including token

        Example:
            api.login('admin@example.com', 'password')
        """
        username = username or self.username
        password = password or self.password

        if not username or not password:
            raise APIError("Username and password required for login")

        response = self._make_request('POST', 'session', data={
            'username': username,
            'password': password
        })

        self.session_token = response.get('id')
        # Sessions last 14 days by default
        self.session_expiry = datetime.now() + timedelta(days=14)
        self._setup_auth()

        return response

    def logout(self) -> bool:
        """Logout and invalidate session token"""
        if self.session_token:
            try:
                self._make_request('DELETE', 'session')
                self.session_token = None
                self.session_expiry = None
                return True
            except:
                return False
        return True

    # ============= DATABASE OPERATIONS =============

    def list_databases(self) -> List[Dict]:
        """
        List all available databases.

        Returns:
            List of database configurations
        """
        return self._make_request('GET', 'database')

    def get_database(self, database_id: int) -> Dict:
        """
        Get database details and metadata.

        Args:
            database_id: Database ID

        Returns:
            Database configuration and metadata
        """
        return self._make_request('GET', f'database/{database_id}')

    def get_database_metadata(self, database_id: int) -> Dict:
        """
        Get detailed database metadata including tables and fields.

        Args:
            database_id: Database ID

        Returns:
            Complete database schema information
        """
        return self._make_request('GET', f'database/{database_id}/metadata')

    # ============= QUERY OPERATIONS =============

    def run_query(self,
                  query: str,
                  database_id: int,
                  parameters: Optional[List[Dict]] = None) -> Dict:
        """
        Execute a native SQL query.

        Args:
            query: SQL query string
            database_id: Database to run query against
            parameters: Query parameters (for parameterized queries)

        Returns:
            Query results with data and metadata

        Example:
            results = api.run_query(
                "SELECT * FROM users WHERE created_at > ?",
                database_id=1,
                parameters=[{"type": "date", "value": "2024-01-01"}]
            )
        """
        payload = {
            'database': database_id,
            'native': {
                'query': query
            },
            'type': 'native'
        }

        if parameters:
            payload['native']['template-tags'] = parameters

        return self._make_request('POST', 'dataset', data=payload)

    def query_card(self, card_id: int, parameters: Optional[Dict] = None) -> Dict:
        """
        Execute a saved question/card.

        Args:
            card_id: Card/Question ID
            parameters: Parameters for the card

        Returns:
            Query results
        """
        endpoint = f'card/{card_id}/query'
        if parameters:
            return self._make_request('POST', endpoint, data={'parameters': parameters})
        return self._make_request('POST', endpoint)

    # ============= CARD/QUESTION OPERATIONS =============

    def list_cards(self, collection_id: Optional[int] = None) -> List[Dict]:
        """
        List all cards/questions, optionally filtered by collection.

        Args:
            collection_id: Filter by collection ID

        Returns:
            List of cards/questions
        """
        params = {}
        if collection_id is not None:
            params['collection'] = collection_id
        return self._make_request('GET', 'card', params=params)

    def get_card(self, card_id: int) -> Dict:
        """
        Get card/question details.

        Args:
            card_id: Card ID

        Returns:
            Card configuration and query
        """
        return self._make_request('GET', f'card/{card_id}')

    def create_card(self,
                    name: str,
                    query: Union[str, Dict],
                    database_id: int,
                    collection_id: Optional[int] = None,
                    description: Optional[str] = None,
                    visualization_settings: Optional[Dict] = None) -> Dict:
        """
        Create a new card/question.

        Args:
            name: Card name
            query: SQL string or MBQL query dict
            database_id: Database ID
            collection_id: Collection to save in
            description: Card description
            visualization_settings: Chart/viz configuration

        Returns:
            Created card details
        """
        data = {
            'name': name,
            'database_id': database_id,
            'dataset_query': {
                'database': database_id
            }
        }

        # Handle native SQL vs MBQL
        if isinstance(query, str):
            data['dataset_query']['type'] = 'native'
            data['dataset_query']['native'] = {'query': query}
        else:
            data['dataset_query']['type'] = 'query'
            data['dataset_query']['query'] = query

        if collection_id:
            data['collection_id'] = collection_id
        if description:
            data['description'] = description
        if visualization_settings:
            data['visualization_settings'] = visualization_settings

        return self._make_request('POST', 'card', data=data)

    def update_card(self, card_id: int, updates: Dict) -> Dict:
        """
        Update an existing card.

        Args:
            card_id: Card ID
            updates: Fields to update

        Returns:
            Updated card details
        """
        return self._make_request('PUT', f'card/{card_id}', data=updates)

    def delete_card(self, card_id: int) -> bool:
        """
        Delete a card/question.

        Args:
            card_id: Card ID

        Returns:
            True if successful
        """
        self._make_request('DELETE', f'card/{card_id}')
        return True

    # ============= DASHBOARD OPERATIONS =============

    def list_dashboards(self, collection_id: Optional[int] = None) -> List[Dict]:
        """
        List all dashboards.

        Args:
            collection_id: Filter by collection

        Returns:
            List of dashboards
        """
        params = {}
        if collection_id is not None:
            params['collection'] = collection_id
        return self._make_request('GET', 'dashboard', params=params)

    def get_dashboard(self, dashboard_id: int) -> Dict:
        """
        Get dashboard details including cards.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dashboard configuration and cards
        """
        return self._make_request('GET', f'dashboard/{dashboard_id}')

    def create_dashboard(self,
                        name: str,
                        description: Optional[str] = None,
                        collection_id: Optional[int] = None) -> Dict:
        """
        Create a new dashboard.

        Args:
            name: Dashboard name
            description: Dashboard description
            collection_id: Collection to save in

        Returns:
            Created dashboard details
        """
        data = {'name': name}
        if description:
            data['description'] = description
        if collection_id:
            data['collection_id'] = collection_id

        return self._make_request('POST', 'dashboard', data=data)

    def add_card_to_dashboard(self,
                             dashboard_id: int,
                             card_id: int,
                             row: int = 0,
                             col: int = 0,
                             size_x: int = 4,
                             size_y: int = 3) -> Dict:
        """
        Add a card to a dashboard.

        Args:
            dashboard_id: Dashboard ID
            card_id: Card ID to add
            row: Grid row position
            col: Grid column position
            size_x: Width in grid units
            size_y: Height in grid units

        Returns:
            Dashboard card configuration
        """
        data = {
            'cardId': card_id,
            'row': row,
            'col': col,
            'size_x': size_x,
            'size_y': size_y
        }
        return self._make_request('POST', f'dashboard/{dashboard_id}/cards', data=data)

    # ============= COLLECTION OPERATIONS =============

    def list_collections(self) -> List[Dict]:
        """List all collections"""
        return self._make_request('GET', 'collection')

    def get_collection(self, collection_id: int) -> Dict:
        """Get collection details"""
        return self._make_request('GET', f'collection/{collection_id}')

    def create_collection(self,
                         name: str,
                         description: Optional[str] = None,
                         parent_id: Optional[int] = None) -> Dict:
        """
        Create a new collection.

        Args:
            name: Collection name
            description: Collection description
            parent_id: Parent collection ID (for nesting)

        Returns:
            Created collection details
        """
        data = {'name': name}
        if description:
            data['description'] = description
        if parent_id:
            data['parent_id'] = parent_id

        return self._make_request('POST', 'collection', data=data)

    # ============= DATA EXPORT =============

    def export_card(self,
                   card_id: int,
                   format: str = 'json',
                   parameters: Optional[Dict] = None) -> Union[Dict, bytes]:
        """
        Export card data in various formats.

        Args:
            card_id: Card ID
            format: Export format (json, csv, xlsx)
            parameters: Card parameters

        Returns:
            Data in requested format
        """
        endpoint = f'card/{card_id}/query/{format}'

        # Set appropriate headers for non-JSON formats
        headers = None
        if format in ['csv', 'xlsx']:
            headers = {'Accept': f'application/{format}'}

        if parameters:
            return self._make_request('POST', endpoint,
                                    data={'parameters': parameters},
                                    headers=headers)
        return self._make_request('POST', endpoint, headers=headers)

    # ============= HELPER METHODS =============

    def discover(self, database_id: Optional[int] = None) -> Dict:
        """
        Discover available databases and their tables.

        Args:
            database_id: Specific database to explore

        Returns:
            Database and table information
        """
        if database_id:
            metadata = self.get_database_metadata(database_id)
            return {
                'database': metadata.get('name', f'Database {database_id}'),
                'tables': [
                    {
                        'name': table['name'],
                        'schema': table.get('schema'),
                        'fields': len(table.get('fields', [])),
                        'description': table.get('description')
                    }
                    for table in metadata.get('tables', [])
                ]
            }
        else:
            databases = self.list_databases()
            return {
                'databases': [
                    {
                        'id': db['id'],
                        'name': db['name'],
                        'engine': db.get('engine'),
                        'is_sample': db.get('is_sample', False)
                    }
                    for db in databases.get('data', databases) if isinstance(databases, (dict, list))
                ]
            }

    def quick_start(self) -> None:
        """
        Display quick start information for Metabase API.
        """
        print("🚀 Metabase API Quick Start")
        print("=" * 50)

        # Test connection
        try:
            if self.test_connection():
                print("✅ Connected to Metabase")
            else:
                print("❌ Connection failed - check credentials")
                return
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return

        # Show databases
        try:
            info = self.discover()
            print(f"\n📊 Available Databases: {len(info.get('databases', []))}")
            for db in info.get('databases', [])[:5]:
                print(f"  - {db['name']} (ID: {db['id']}, Engine: {db.get('engine', 'unknown')})")
        except Exception as e:
            print(f"Could not list databases: {e}")

        print("\n📝 Common Operations:")
        print("  # List databases")
        print("  databases = api.list_databases()")
        print("\n  # Run a query")
        print("  results = api.run_query('SELECT * FROM table LIMIT 10', database_id=1)")
        print("\n  # Query a saved card")
        print("  data = api.query_card(card_id=123)")
        print("\n  # Export data")
        print("  csv_data = api.export_card(card_id=123, format='csv')")

    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # Try to get user info or database list
            if self.api_key or self.session_token:
                self._make_request('GET', 'user/current')
                return True
            else:
                # Try to access public endpoint
                self._make_request('GET', 'database')
                return True
        except Exception as e:
            # If unauthorized, connection works but needs auth
            if '401' in str(e) or 'Unauthorized' in str(e):
                return True
            return False


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys

    api = MetabaseAPI()

    if len(sys.argv) < 2:
        print("Metabase API CLI")
        print("=" * 40)
        print("Usage:")
        print("  python api.py test              # Test connection")
        print("  python api.py quick_start        # Show quick start info")
        print("  python api.py discover           # List databases")
        print("  python api.py discover [db_id]   # Show database tables")
        print("  python api.py databases          # List all databases")
        print("  python api.py cards              # List all cards")
        print("  python api.py dashboards         # List all dashboards")
        print("  python api.py query [db_id] 'SQL'  # Run SQL query")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "test":
            if api.test_connection():
                print("✅ Connection successful")
            else:
                print("❌ Connection failed")

        elif command == "quick_start":
            api.quick_start()

        elif command == "discover":
            if len(sys.argv) > 2:
                info = api.discover(int(sys.argv[2]))
                print(f"Database: {info['database']}")
                print(f"Tables ({len(info['tables'])}):")
                for table in info['tables']:
                    print(f"  - {table['name']} ({table['fields']} fields)")
            else:
                info = api.discover()
                print(f"Databases ({len(info['databases'])}):")
                for db in info['databases']:
                    print(f"  - {db['name']} (ID: {db['id']}, Engine: {db['engine']})")

        elif command == "databases":
            databases = api.list_databases()
            print(f"Found {len(databases)} databases:")
            for db in databases:
                print(f"  - {db['name']} (ID: {db['id']})")

        elif command == "cards":
            cards = api.list_cards()
            print(f"Found {len(cards)} cards:")
            for card in cards[:10]:
                print(f"  - {card['name']} (ID: {card['id']})")

        elif command == "dashboards":
            dashboards = api.list_dashboards()
            print(f"Found {len(dashboards)} dashboards:")
            for dash in dashboards[:10]:
                print(f"  - {dash['name']} (ID: {dash['id']})")

        elif command == "query" and len(sys.argv) > 3:
            db_id = int(sys.argv[2])
            query = sys.argv[3]
            results = api.run_query(query, db_id)
            print(f"Query returned {len(results.get('data', {}).get('rows', []))} rows")
            print(json.dumps(results, indent=2))

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)