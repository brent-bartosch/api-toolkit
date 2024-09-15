#!/usr/bin/env python3
"""
Supabase Table Documentation
Known table structures and common queries for each project.
"""

# ============= PROJECT: SMOOTHED (Lead Gen) =============
SMOOTHED_TABLES = {
    'brands': {
        'description': 'Brand/company information',
        'key_columns': ['id', 'name', 'domain', 'industry', 'status'],
        'common_filters': {
            'active': {'status': 'eq.active'},
            'by_industry': lambda ind: {'industry': f'eq.{ind}'},
            'has_website': {'domain': 'not.is.null'}
        },
        'sample_queries': [
            "api.query('brands', filters={'status': 'eq.active'})",
            "api.query('brands', filters={'industry': 'eq.fashion'}, limit=10)",
        ]
    },
    'scraping_results': {
        'description': 'Web scraping results and data',
        'key_columns': ['id', 'url', 'data', 'scraped_at', 'status'],
        'common_filters': {
            'successful': {'status': 'eq.success'},
            'recent': lambda days: {'scraped_at': f'gte.{days}'},
            'by_domain': lambda domain: {'url': f'like.%{domain}%'}
        },
        'sample_queries': [
            "api.query('scraping_results', filters={'status': 'eq.success'}, order='-scraped_at')",
        ]
    },
    'leads': {
        'description': 'Potential customer leads',
        'key_columns': ['id', 'email', 'company', 'name', 'score', 'status'],
        'common_filters': {
            'qualified': {'score': 'gte.70'},
            'uncontacted': {'status': 'eq.new'},
            'hot_leads': {'score': 'gte.90', 'status': 'eq.new'}
        },
        'sample_queries': [
            "api.query('leads', filters={'score': 'gte.80'}, order='-score')",
        ]
    }
}

# ============= PROJECT: BLINGSTING (CRM) =============
BLINGSTING_TABLES = {
    'customers': {
        'description': 'Customer profiles and information',
        'key_columns': ['id', 'email', 'name', 'phone', 'created_at', 'status'],
        'common_filters': {
            'active': {'status': 'eq.active'},
            'by_email': lambda email: {'email': f'eq.{email}'},
            'recent': {'created_at': 'gte.2024-01-01'}
        },
        'sample_queries': [
            "api.query('customers', filters={'status': 'eq.active'})",
            "api.get_by_id('customers', 'cust_123')",
        ]
    },
    'orders': {
        'description': 'Customer orders and transactions',
        'key_columns': ['id', 'customer_id', 'total', 'status', 'created_at'],
        'common_filters': {
            'pending': {'status': 'eq.pending'},
            'completed': {'status': 'eq.completed'},
            'high_value': {'total': 'gte.1000'},
            'by_customer': lambda cid: {'customer_id': f'eq.{cid}'}
        },
        'sample_queries': [
            "api.query('orders', filters={'status': 'eq.pending'}, order='-created_at')",
            "api.query('orders', filters={'customer_id': 'eq.cust_123'})",
        ]
    },
    'products': {
        'description': 'Product catalog',
        'key_columns': ['id', 'sku', 'name', 'price', 'inventory', 'category'],
        'common_filters': {
            'in_stock': {'inventory': 'gt.0'},
            'by_category': lambda cat: {'category': f'eq.{cat}'},
            'price_range': lambda min, max: {'price': f'gte.{min}', 'price': f'lte.{max}'}
        },
        'sample_queries': [
            "api.query('products', filters={'inventory': 'gt.0'}, order='name')",
        ]
    }
}

# ============= PROJECT: SCRAPING (Web Project 3) =============
SCRAPING_TABLES = {
    'scrape_guide': {
        'description': 'Project 3 configuration and targets',
        'key_columns': ['id', 'url', 'selector', 'frequency', 'priority', 'category_display_name'],
        'common_filters': {
            'high_priority': {'priority': 'gte.8'},
            'active': {'active': 'eq.true'},
            'by_category': lambda cat: {'category_display_name': f'eq.{cat}'}
        },
        'sample_queries': [
            "api.query('scrape_guide', filters={'priority': 'gte.8'})",
            "api.query('scrape_guide', filters={'active': 'eq.true'}, limit=10)",
        ]
    },
    'scrape_results': {
        'description': 'Results from scraping operations',
        'key_columns': ['id', 'guide_id', 'data', 'extracted_at', 'status'],
        'common_filters': {
            'successful': {'status': 'eq.success'},
            'failed': {'status': 'eq.failed'},
            'recent': lambda hours: {'extracted_at': f'gte.{hours}'}
        },
        'sample_queries': [
            "api.query('scrape_results', filters={'status': 'eq.success'}, order='-extracted_at')",
        ]
    },
    'scrape_queue': {
        'description': 'Queue of pending scrape jobs',
        'key_columns': ['id', 'url', 'priority', 'scheduled_for', 'status'],
        'common_filters': {
            'pending': {'status': 'eq.pending'},
            'ready': {'scheduled_for': 'lte.now()'},
            'high_priority': {'priority': 'gte.9'}
        },
        'sample_queries': [
            "api.query('scrape_queue', filters={'status': 'eq.pending'}, order='priority')",
        ]
    }
}

# ============= HELPER FUNCTIONS =============

def get_table_info(project: str, table: str) -> dict:
    """Get documentation for a specific table"""
    project_tables = {
        'project1': SMOOTHED_TABLES,
        'project2': BLINGSTING_TABLES,
        'project3': SCRAPING_TABLES
    }
    
    tables = project_tables.get(project, {})
    return tables.get(table, {
        'description': f'Table {table} - documentation not available',
        'key_columns': [],
        'common_filters': {},
        'sample_queries': [f"api.query('{table}')"]
    })


def list_project_tables(project: str) -> list:
    """List all documented tables for a project"""
    project_tables = {
        'project1': SMOOTHED_TABLES,
        'project2': BLINGSTING_TABLES,
        'project3': SCRAPING_TABLES
    }
    
    tables = project_tables.get(project, {})
    return list(tables.keys())


def generate_query(project: str, table: str, filter_type: str = None) -> str:
    """Generate a sample query for a table"""
    info = get_table_info(project, table)
    
    if filter_type and filter_type in info.get('common_filters', {}):
        filter_def = info['common_filters'][filter_type]
        if callable(filter_def):
            # It's a lambda, show example usage
            return f"# Requires parameter\napi.query('{table}', filters={filter_type}_value)"
        else:
            return f"api.query('{table}', filters={filter_def})"
    
    # Return first sample query or basic query
    if info.get('sample_queries'):
        return info['sample_queries'][0]
    return f"api.query('{table}')"


# ============= CLI HELPER =============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Table Documentation Helper")
        print("=" * 50)
        print("\nUsage:")
        print("  python table_docs.py list [project]     # List tables")
        print("  python table_docs.py info [project] [table]  # Get table info")
        print("  python table_docs.py query [project] [table] [filter]  # Generate query")
        print("\nProjects: smoothed, blingsting, scraping")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list" and len(sys.argv) > 2:
        project = sys.argv[2]
        tables = list_project_tables(project)
        print(f"\nTables in {project}:")
        for table in tables:
            info = get_table_info(project, table)
            print(f"  - {table}: {info.get('description', 'No description')}")
    
    elif command == "info" and len(sys.argv) > 3:
        project = sys.argv[2]
        table = sys.argv[3]
        info = get_table_info(project, table)
        
        print(f"\nTable: {table}")
        print(f"Project: {project}")
        print(f"Description: {info.get('description', 'N/A')}")
        print(f"\nKey Columns:")
        for col in info.get('key_columns', []):
            print(f"  - {col}")
        print(f"\nCommon Filters:")
        for name, filter_def in info.get('common_filters', {}).items():
            print(f"  - {name}: {filter_def if not callable(filter_def) else 'dynamic'}")
        print(f"\nSample Queries:")
        for query in info.get('sample_queries', []):
            print(f"  {query}")
    
    elif command == "query" and len(sys.argv) > 3:
        project = sys.argv[2]
        table = sys.argv[3]
        filter_type = sys.argv[4] if len(sys.argv) > 4 else None
        
        query = generate_query(project, table, filter_type)
        print(f"\nGenerated query:")
        print(query)
    
    else:
        print(f"Unknown command: {command}")