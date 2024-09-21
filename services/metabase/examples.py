#!/usr/bin/env python3
"""
Metabase API Examples

Demonstrates common patterns for working with Metabase analytics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.metabase.api import MetabaseAPI
import json
from datetime import datetime, timedelta

def example_basic_connection():
    """Example: Basic connection and authentication"""
    print("\n" + "="*50)
    print("EXAMPLE: Basic Connection")
    print("="*50)

    # Method 1: Using API Key (recommended)
    api = MetabaseAPI(api_key='mb_your_api_key_here')

    # Method 2: Using session authentication
    api = MetabaseAPI()
    # api.login('admin@example.com', 'password')

    # Test connection
    if api.test_connection():
        print("✅ Connected to Metabase")
    else:
        print("❌ Connection failed")

    return api

def example_explore_databases():
    """Example: Explore available databases and tables"""
    print("\n" + "="*50)
    print("EXAMPLE: Explore Databases")
    print("="*50)

    api = MetabaseAPI()

    # List all databases
    databases = api.list_databases()
    print(f"Found {len(databases)} databases:")

    for db in databases[:3]:
        print(f"\nDatabase: {db['name']} (ID: {db['id']})")

        # Get metadata for each database
        try:
            metadata = api.get_database_metadata(db['id'])
            tables = metadata.get('tables', [])
            print(f"  Tables: {len(tables)}")

            for table in tables[:3]:
                print(f"    - {table['name']} ({len(table.get('fields', []))} fields)")
        except Exception as e:
            print(f"  Could not get metadata: {e}")

def example_run_queries():
    """Example: Run SQL queries"""
    print("\n" + "="*50)
    print("EXAMPLE: Running Queries")
    print("="*50)

    api = MetabaseAPI()

    # Assuming database_id=1 (adjust for your setup)
    database_id = 1

    # Simple query
    query = "SELECT * FROM orders LIMIT 5"
    print(f"\nRunning query: {query}")

    try:
        results = api.run_query(query, database_id)

        # Extract data from results
        rows = results.get('data', {}).get('rows', [])
        cols = results.get('data', {}).get('cols', [])

        print(f"Returned {len(rows)} rows with {len(cols)} columns")

        # Display column names
        if cols:
            col_names = [col.get('name', 'unknown') for col in cols]
            print(f"Columns: {', '.join(col_names)}")

        # Display first row
        if rows:
            print(f"First row: {rows[0]}")
    except Exception as e:
        print(f"Query failed: {e}")

    # Parameterized query example
    print("\n" + "-"*30)
    print("Parameterized Query Example:")

    query_with_params = """
    SELECT * FROM orders
    WHERE created_at > {{start_date}}
    LIMIT 10
    """

    parameters = [{
        "type": "date",
        "target": ["variable", ["template-tag", "start_date"]],
        "value": "2024-01-01"
    }]

    print(f"Query with parameter: start_date = 2024-01-01")
    # Results would be: api.run_query(query_with_params, database_id, parameters)

def example_manage_cards():
    """Example: Create and manage cards (saved questions)"""
    print("\n" + "="*50)
    print("EXAMPLE: Managing Cards/Questions")
    print("="*50)

    api = MetabaseAPI()

    # List existing cards
    cards = api.list_cards()
    print(f"Found {len(cards)} existing cards")

    if cards:
        # Display first few cards
        for card in cards[:3]:
            print(f"  - {card['name']} (ID: {card['id']})")

        # Get details of first card
        card_id = cards[0]['id']
        card_details = api.get_card(card_id)
        print(f"\nCard '{card_details['name']}' details:")
        print(f"  - Database: {card_details.get('database_id')}")
        print(f"  - Collection: {card_details.get('collection_id')}")
        print(f"  - Created: {card_details.get('created_at')}")

    # Example: Create a new card
    print("\n" + "-"*30)
    print("Creating a new card (example):")

    new_card_example = """
    # Create a card with SQL query
    card = api.create_card(
        name="Monthly Sales Report",
        query="SELECT DATE_TRUNC('month', created_at) as month, SUM(total) as revenue FROM orders GROUP BY 1",
        database_id=1,
        description="Monthly revenue summary",
        visualization_settings={
            "display": "line",
            "line.interpolate": "linear"
        }
    )
    """
    print(new_card_example)

def example_dashboards():
    """Example: Work with dashboards"""
    print("\n" + "="*50)
    print("EXAMPLE: Managing Dashboards")
    print("="*50)

    api = MetabaseAPI()

    # List dashboards
    dashboards = api.list_dashboards()
    print(f"Found {len(dashboards)} dashboards")

    for dash in dashboards[:3]:
        print(f"  - {dash['name']} (ID: {dash['id']})")

    if dashboards:
        # Get dashboard details
        dash_id = dashboards[0]['id']
        dashboard = api.get_dashboard(dash_id)

        print(f"\nDashboard '{dashboard['name']}' details:")
        print(f"  - Cards: {len(dashboard.get('dashcards', []))}")
        print(f"  - Collection: {dashboard.get('collection_id')}")

        # List cards in dashboard
        for dashcard in dashboard.get('dashcards', [])[:3]:
            card = dashcard.get('card', {})
            print(f"    • {card.get('name', 'Unknown')} (position: {dashcard.get('row', 0)},{dashcard.get('col', 0)})")

    # Example: Create dashboard and add cards
    print("\n" + "-"*30)
    print("Creating dashboard example:")

    dashboard_example = """
    # Create a new dashboard
    dashboard = api.create_dashboard(
        name="Executive Summary",
        description="High-level business metrics",
        collection_id=1  # Root collection
    )

    # Add cards to dashboard
    api.add_card_to_dashboard(
        dashboard_id=dashboard['id'],
        card_id=123,  # Your card ID
        row=0, col=0,
        size_x=6, size_y=4
    )
    """
    print(dashboard_example)

def example_collections():
    """Example: Organize content with collections"""
    print("\n" + "="*50)
    print("EXAMPLE: Working with Collections")
    print("="*50)

    api = MetabaseAPI()

    # List collections
    collections = api.list_collections()
    print(f"Found {len(collections)} collections")

    for coll in collections[:5]:
        print(f"  - {coll.get('name', 'Unknown')} (ID: {coll.get('id')})")
        if coll.get('description'):
            print(f"    Description: {coll['description']}")

    # Example: Create nested collections
    print("\n" + "-"*30)
    print("Creating collection structure example:")

    collection_example = """
    # Create parent collection
    parent = api.create_collection(
        name="Analytics Reports",
        description="All analytical reports"
    )

    # Create child collections
    sales = api.create_collection(
        name="Sales Analytics",
        description="Sales team reports",
        parent_id=parent['id']
    )

    marketing = api.create_collection(
        name="Marketing Analytics",
        description="Marketing team reports",
        parent_id=parent['id']
    )
    """
    print(collection_example)

def example_export_data():
    """Example: Export data in different formats"""
    print("\n" + "="*50)
    print("EXAMPLE: Exporting Data")
    print("="*50)

    api = MetabaseAPI()

    # List cards to find one to export
    cards = api.list_cards()

    if cards:
        card_id = cards[0]['id']
        card_name = cards[0]['name']

        print(f"Exporting card: '{card_name}' (ID: {card_id})")

        # Export as JSON
        print("\n1. Export as JSON:")
        try:
            json_data = api.export_card(card_id, format='json')
            print(f"   Exported {len(json_data.get('data', {}).get('rows', []))} rows")
        except Exception as e:
            print(f"   Export failed: {e}")

        # Export examples for other formats
        print("\n2. Export as CSV:")
        print("   csv_data = api.export_card(card_id, format='csv')")

        print("\n3. Export as Excel:")
        print("   xlsx_data = api.export_card(card_id, format='xlsx')")

        print("\n4. Export with parameters:")
        print("""   data = api.export_card(
       card_id,
       format='csv',
       parameters={'date_range': 'last30days'}
   )""")
    else:
        print("No cards available to export")

def example_discovery_pattern():
    """Example: Discover and explore pattern"""
    print("\n" + "="*50)
    print("EXAMPLE: Discovery Pattern")
    print("="*50)

    api = MetabaseAPI()

    # Use the discover method
    print("Discovering databases...")
    info = api.discover()

    print(f"\nFound {len(info.get('databases', []))} databases:")
    for db in info.get('databases', []):
        print(f"  • {db['name']} (ID: {db['id']})")
        print(f"    Engine: {db.get('engine', 'unknown')}")
        print(f"    Sample: {db.get('is_sample', False)}")

    # Discover specific database
    if info.get('databases'):
        db_id = info['databases'][0]['id']
        print(f"\nExploring database ID {db_id}...")

        db_info = api.discover(db_id)
        print(f"Database: {db_info['database']}")
        print(f"Tables: {len(db_info.get('tables', []))}")

        for table in db_info.get('tables', [])[:3]:
            print(f"  • {table['name']}")
            print(f"    Fields: {table['fields']}")
            if table.get('description'):
                print(f"    Description: {table['description']}")

def example_error_handling():
    """Example: Proper error handling"""
    print("\n" + "="*50)
    print("EXAMPLE: Error Handling")
    print("="*50)

    api = MetabaseAPI()

    # Handle authentication errors
    try:
        api_bad = MetabaseAPI(api_key='invalid_key')
        api_bad.list_databases()
    except Exception as e:
        print(f"❌ Authentication error handled: {e}")

    # Handle missing resources
    try:
        card = api.get_card(999999)  # Non-existent card
    except Exception as e:
        print(f"❌ Resource not found handled: {e}")

    # Handle invalid queries
    try:
        results = api.run_query("INVALID SQL QUERY", database_id=1)
    except Exception as e:
        print(f"❌ Query error handled: {e}")

    print("\n✅ All errors handled gracefully")

# ============= MAIN EXECUTION =============

if __name__ == "__main__":
    if len(sys.argv) > 1:
        example_name = sys.argv[1]

        examples = {
            'basic': example_basic_connection,
            'databases': example_explore_databases,
            'queries': example_run_queries,
            'cards': example_manage_cards,
            'dashboards': example_dashboards,
            'collections': example_collections,
            'export': example_export_data,
            'discover': example_discovery_pattern,
            'errors': example_error_handling
        }

        if example_name in examples:
            examples[example_name]()
        else:
            print(f"Unknown example: {example_name}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        print("Metabase API Examples")
        print("="*40)
        print("\nUsage: python examples.py [example_name]")
        print("\nAvailable examples:")
        print("  basic       - Basic connection and auth")
        print("  databases   - Explore databases and tables")
        print("  queries     - Run SQL queries")
        print("  cards       - Manage cards/questions")
        print("  dashboards  - Work with dashboards")
        print("  collections - Organize with collections")
        print("  export      - Export data formats")
        print("  discover    - Discovery pattern")
        print("  errors      - Error handling")
        print("\nRunning all examples...")

        # Run all examples
        example_basic_connection()
        example_explore_databases()
        example_run_queries()
        example_manage_cards()
        example_dashboards()
        example_collections()
        example_export_data()
        example_discovery_pattern()
        example_error_handling()