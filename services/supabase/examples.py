#!/usr/bin/env python3
"""
Supabase API Usage Examples
Complete examples for common operations across all projects.
"""

from services.supabase.api import SupabaseAPI
from services.supabase.query_helpers import QueryBuilder, CommonQueries
from services.supabase.table_docs import get_table_info

# ============= BASIC USAGE =============

def basic_examples():
    """Basic CRUD operations"""
    
    # Initialize for different projects
    api_smoothed = SupabaseAPI('project1')    # Lead gen
    api_crm = SupabaseAPI('project2')       # CRM data
    api_scraping = SupabaseAPI('project3')    # Web scraping
    
    # Simple query - get all records
    users = api_crm.query('customers')
    
    # Query with filters
    active_users = api_crm.query('customers', 
        filters={'status': 'eq.active'}
    )
    
    # Query with multiple conditions
    high_value_orders = api_crm.query('orders',
        filters={
            'status': 'eq.completed',
            'total': 'gte.1000'
        },
        order='-created_at',
        limit=10
    )
    
    # Get single record by ID
    customer = api_crm.get_by_id('customers', 'cust_123')
    
    # Insert new record
    new_lead = api_smoothed.insert('leads', {
        'email': 'prospect@example.com',
        'company': 'Example Corp',
        'score': 85,
        'status': 'new'
    })
    
    # Update existing record
    api_crm.update('customers', 
        {'status': 'premium'},
        {'id': 'eq.cust_123'}
    )
    
    # Delete records
    api_smoothed.delete('old_logs', 
        {'created_at': 'lt.2023-01-01'}
    )


# ============= QUERY BUILDER EXAMPLES =============

def query_builder_examples():
    """Using the QueryBuilder for cleaner syntax"""
    
    api = SupabaseAPI('project1')
    
    # Build complex query step by step
    query = (QueryBuilder('leads')
             .select('id', 'email', 'company', 'score')
             .where('score', '>=', 80)
             .where('status', '=', 'new')
             .contains('company', 'tech')
             .order('score', desc=True)
             .limit(20))
    
    # Execute the query
    hot_tech_leads = query.execute(api)
    
    # Pagination example
    page = 2
    per_page = 25
    
    paginated = (QueryBuilder('brands')
                 .select('name', 'domain', 'industry')
                 .where('status', '=', 'active')
                 .order('name')
                 .limit(per_page)
                 .offset((page - 1) * per_page))
    
    results = paginated.execute(api)
    
    return results


# ============= COMMON PATTERNS =============

def common_pattern_examples():
    """Using pre-built common patterns"""
    
    api = SupabaseAPI('project2')
    
    # Get recent records (last 7 days)
    params = CommonQueries.recent_records('orders', days=7)
    recent_orders = api.query('orders', **params)
    
    # Paginated results
    params = CommonQueries.paginated('customers', page=3, per_page=50)
    customers_page_3 = api.query('customers', **params)
    
    # Find by email
    params = CommonQueries.by_email('customers', 'john@example.com')
    customer = api.query('customers', **params)
    
    # Active records only
    params = CommonQueries.active_only('products')
    active_products = api.query('products', **params)
    
    return recent_orders


# ============= ADVANCED QUERIES =============

def advanced_examples():
    """Advanced query techniques"""
    
    api = SupabaseAPI('project3')
    
    # Query with relationships (foreign keys)
    # Assuming scrape_results has a guide_id that references scrape_guide
    results_with_guide = api.query('scrape_results',
        select='*, scrape_guide(url, category_display_name)',
        filters={'status': 'eq.success'},
        order='-extracted_at',
        limit=10
    )
    
    # Text search (case-insensitive)
    search_results = api.query('scrape_guide',
        filters={'url': 'ilike.%amazon%'},
        order='priority'
    )
    
    # Complex date filtering
    from datetime import datetime, timedelta
    
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    last_week = (datetime.now() - timedelta(days=7)).isoformat()
    
    recent_scrapes = api.query('scrape_results',
        filters={
            'extracted_at': f'gte.{last_week}',
            'extracted_at': f'lte.{yesterday}',
            'status': 'eq.success'
        }
    )
    
    # Using RPC for custom functions
    # Assuming you have a PostgreSQL function
    total_revenue = api.rpc('calculate_total_revenue', {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    })
    
    return results_with_guide


# ============= NEW v2.1 FEATURES =============

def v21_features_examples():
    """NEW in v2.1: Large dataset handling and helper methods"""

    api = SupabaseAPI('project1')

    # ===== 1. CONFIGURABLE ROW LIMITS =====

    # Default: 1,000 row limit (prevents accidental large loads)
    api_safe = SupabaseAPI('project1')  # max_row_limit=1000 by default

    # Custom limit for this instance
    api_custom = SupabaseAPI('project1', max_row_limit=500)

    # Unlimited (use with caution!)
    api_unlimited = SupabaseAPI('project1', max_row_limit=None)

    # Warning when limit exceeded
    try:
        # This will warn and cap at 1,000 rows
        brands = api.query('brands', limit=5000)
        # ⚠️  WARNING: Requested 5,000 rows, but max_row_limit is 1,000
        #     Results will be capped at 1,000.
        #     💡 TIP: Use api.fetch_all('brands') to get all records
    except Exception as e:
        print(f"Error: {e}")

    # ===== 2. FETCH_ALL - AUTO-PAGINATION =====

    # Get ALL records, even if 8,225 rows (automatically paginates)
    all_brands = api.fetch_all('brands')
    print(f"Fetched all {len(all_brands):,} brands")
    # Output:
    # 📥 Fetching all records from 'brands'...
    #    ... fetched 5,000 records so far
    # ✅ Fetched 8,225 total records from 'brands'

    # With filters
    ca_brands = api.fetch_all('brands', filters={'state': 'eq.CA'})
    print(f"CA brands: {len(ca_brands):,}")

    # Specific columns only (saves memory)
    brand_names = api.fetch_all('brands',
        select='token,name,state',
        filters={'status': 'eq.active'}
    )

    # Silent mode (no progress output)
    all_leads_silent = api.fetch_all('leads', verbose=False)

    # ===== 3. COUNT - FAST COUNTING =====

    # Count without fetching data (much faster!)
    total_brands = api.count('brands')
    print(f"Total brands: {total_brands:,}")

    # Count with filters
    active_brands = api.count('brands', filters={'status': 'eq.active'})
    ca_brands_count = api.count('brands', filters={'state': 'eq.CA'})
    high_score_leads = api.count('leads', filters={'score': 'gte.90'})

    print(f"Active: {active_brands:,}, CA: {ca_brands_count:,}, High score: {high_score_leads:,}")

    # Much faster than:
    # slow_count = len(api.query('brands'))  # ❌ Fetches all data!

    # ===== 4. EXISTS - QUICK CHECKS =====

    # Check if any records match (very fast, uses LIMIT 1)
    if api.exists('brands', {'name': 'eq.Nike'}):
        print("Nike exists in database!")

    # Existence check before insert
    email = 'john@example.com'
    if not api.exists('users', {'email': f'eq.{email}'}):
        # Safe to insert
        api.insert('users', {'email': email, 'name': 'John'})
        print(f"Created new user: {email}")
    else:
        print(f"User {email} already exists - skipping")

    # Check if any high-value leads
    if api.exists('leads', {'score': 'gte.95'}):
        print("We have premium leads!")

    # ===== 5. SAFE LARGE DATASET PATTERN =====

    # Always check size first before fetching
    total = api.count('leads', filters={'score': 'gte.80'})
    print(f"Found {total:,} leads matching criteria")

    # Decide approach based on size
    if total < 100:
        # Small dataset - fetch directly
        leads = api.query('leads', filters={'score': 'gte.80'})
        print(f"Small dataset: {len(leads)} rows")

    elif total < 10000:
        # Medium dataset - fetch all with progress
        leads = api.fetch_all('leads',
            filters={'score': 'gte.80'},
            verbose=True
        )
        print(f"Medium dataset: {len(leads):,} rows")

    else:
        # Large dataset - warn or process differently
        print(f"Large dataset ({total:,} rows)!")
        print("Consider:")
        print("  1. Add more filters to reduce size")
        print("  2. Process in batches")
        print("  3. Use raw_query() with aggregations")

        # Example: Process in batches
        batch_size = 1000
        for offset in range(0, min(total, 5000), batch_size):
            batch = api.query('leads',
                filters={'score': 'gte.80'},
                limit=batch_size,
                offset=offset
            )
            # Process this batch
            print(f"Processing batch: {len(batch)} leads")

    # ===== 6. PAGINATION INFO PATTERN =====

    # Get pagination details
    total = api.count('leads')
    page_size = 50
    total_pages = (total + page_size - 1) // page_size

    print(f"\nPagination Info:")
    print(f"  Total records: {total:,}")
    print(f"  Page size: {page_size}")
    print(f"  Total pages: {total_pages:,}")

    # Fetch specific page
    page_num = 1
    page_data = api.query('leads',
        limit=page_size,
        offset=(page_num - 1) * page_size
    )
    print(f"  Page {page_num}: {len(page_data)} records")

    # ===== 7. COMPARISON: OLD vs NEW =====

    print("\n=== Performance Comparison ===")

    # OLD WAY (pre-v2.1)
    # ❌ No warning, fetches all rows silently
    # ❌ Manual pagination code required
    # ❌ Slow existence checks: len(api.query(...)) > 0

    # NEW WAY (v2.1)
    # ✅ Configurable limits with warnings
    # ✅ Auto-pagination with fetch_all()
    # ✅ Fast count() and exists() helpers

    return {
        'all_brands_count': len(all_brands),
        'ca_brands_count': len(ca_brands),
        'total_brands': total_brands,
        'high_score_leads': high_score_leads
    }


# ============= BATCH OPERATIONS =============

def batch_operations():
    """Handling multiple records efficiently"""
    
    api = SupabaseAPI('project2')
    
    # Batch insert
    new_products = [
        {'name': 'Product A', 'price': 29.99, 'sku': 'SKU-001'},
        {'name': 'Product B', 'price': 49.99, 'sku': 'SKU-002'},
        {'name': 'Product C', 'price': 19.99, 'sku': 'SKU-003'},
    ]
    
    inserted = api.insert('products', new_products)
    
    # Upsert (insert or update on conflict)
    customer_updates = [
        {'email': 'john@example.com', 'status': 'premium'},
        {'email': 'jane@example.com', 'status': 'active'},
    ]
    
    upserted = api.insert('customers', 
        customer_updates, 
        on_conflict='email'  # Update if email exists
    )
    
    return inserted


# ============= ERROR HANDLING =============

def error_handling_examples():
    """Proper error handling patterns"""
    
    try:
        api = SupabaseAPI('project1')
        
        # Check connection first
        if not api.test_connection():
            print("Connection failed - check your .env configuration")
            return None
        
        # Wrap queries in try-catch
        try:
            data = api.query('nonexistent_table')
        except Exception as e:
            print(f"Query failed: {e}")
            # Fallback or alternative logic
            data = []
        
        # Validate before insert
        new_record = {'email': 'test@example.com'}
        
        if 'email' in new_record and '@' in new_record['email']:
            api.insert('leads', new_record)
        else:
            print("Invalid email format")
        
    except Exception as e:
        print(f"API initialization failed: {e}")
        print("Check your environment variables")


# ============= SCHEMA EXPLORATION =============

def explore_database():
    """Explore database schema and structure"""
    
    api = SupabaseAPI('project1')
    
    # List all tables
    tables = api.get_tables()
    print(f"Available tables: {tables}")
    
    # Get schema for a specific table
    schema = api.get_schema('leads')
    print("\nLeads table schema:")
    for col in schema:
        print(f"  {col['column']}: {col['type']}")
    
    # Get detailed table information
    info = api.describe_table('brands')
    print(f"\nBrands table:")
    print(f"  Rows: {info['row_count']}")
    print(f"  Columns: {len(info['columns'])}")
    
    # Interactive exploration
    api.explore()  # Lists all tables
    api.explore('leads')  # Details for specific table


# ============= PROJECT-SPECIFIC EXAMPLES =============

def smoothed_project_examples():
    """Examples specific to Project1 (Lead Gen) project"""
    
    api = SupabaseAPI('project1')
    
    # Find high-quality leads
    hot_leads = api.query('leads',
        filters={
            'score': 'gte.85',
            'status': 'eq.new'
        },
        order='-score',
        limit=20
    )
    
    # Get brands by industry
    fashion_brands = api.query('brands',
        filters={'industry': 'eq.fashion'},
        select='name,domain,status'
    )
    
    # Recent scraping results
    recent_scrapes = api.query('scraping_results',
        filters={'status': 'eq.success'},
        order='-scraped_at',
        limit=50
    )
    
    return hot_leads


def blingsting_project_examples():
    """Examples specific to Project2 (CRM) project"""
    
    api = SupabaseAPI('project2')
    
    # Get customer purchase history
    customer_orders = api.query('orders',
        filters={'customer_id': 'eq.cust_123'},
        order='-created_at'
    )
    
    # High-value customers
    vip_customers = api.query('customers',
        filters={'lifetime_value': 'gte.10000'},
        select='id,email,name,lifetime_value'
    )
    
    # Inventory check
    low_stock = api.query('products',
        filters={'inventory': 'lte.10'},
        order='inventory'
    )
    
    return customer_orders


def scraping_project_examples():
    """Examples specific to Project 3 project"""
    
    api = SupabaseAPI('project3')
    
    # High-priority scraping targets
    priority_targets = api.query('scrape_guide',
        filters={'priority': 'gte.9'},
        order='-priority'
    )
    
    # Failed scrapes for retry
    failed_scrapes = api.query('scrape_results',
        filters={'status': 'eq.failed'},
        select='id,guide_id,error_message',
        limit=20
    )
    
    # Project 3 queue status
    pending_jobs = api.count('scrape_queue', 
        filters={'status': 'eq.pending'}
    )
    print(f"Pending scrape jobs: {pending_jobs}")
    
    return priority_targets


# ============= MAIN DEMO =============

if __name__ == "__main__":
    import sys
    
    print("Supabase API Examples")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        examples = {
            'basic': basic_examples,
            'builder': query_builder_examples,
            'patterns': common_pattern_examples,
            'advanced': advanced_examples,
            'v21': v21_features_examples,
            'batch': batch_operations,
            'errors': error_handling_examples,
            'explore': explore_database,
            'project1': smoothed_project_examples,
            'project2': blingsting_project_examples,
            'project3': scraping_project_examples
        }
        
        if example in examples:
            print(f"\nRunning {example} examples...")
            result = examples[example]()
            if result:
                import json
                print(json.dumps(result[:2], indent=2))
        else:
            print(f"Unknown example: {example}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        print("\nUsage: python examples.py [example_type]")
        print("\nAvailable examples:")
        print("  basic      - Basic CRUD operations")
        print("  builder    - Query builder usage")
        print("  patterns   - Common query patterns")
        print("  advanced   - Advanced techniques")
        print("  v21        - 🆕 NEW v2.1 features (fetch_all, count, exists)")
        print("  batch      - Batch operations")
        print("  errors     - Error handling")
        print("  explore    - Database exploration")
        print("  smoothed   - Project1 project examples")
        print("  blingsting - Project2 project examples")
        print("  scraping   - Project 3 project examples")

        print("\nQuick tests:")
        print("  python examples.py v21       # Try new v2.1 features!")
        print("  python examples.py explore   # Explore database")