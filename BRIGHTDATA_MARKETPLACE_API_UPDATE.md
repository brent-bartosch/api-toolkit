# BrightData API Toolkit - Marketplace Dataset Feature Addition

## Overview
This document contains instructions for adding BrightData Marketplace Dataset API functionality to the existing BrightData API toolkit located at `/path/to/api-toolkit/services/brightdata/`.

## Background
The current BrightData API implementation supports web scraping, proxies, and SERP API but lacks the Marketplace Dataset API functionality needed to programmatically query and filter datasets (like Google Maps locations) before purchasing/downloading.

## Required Updates

### 1. Update `api.py` - Add Marketplace Methods

Add the following methods to the `BrightDataAPI` class in `/path/to/api-toolkit/services/brightdata/api.py`:

```python
# Add after line 599 (after collect_social_posts method)

def get_dataset_list(self) -> Dict[str, Any]:
    """
    Get list of available marketplace datasets.

    Returns:
        List of datasets with IDs and descriptions
    """
    try:
        response = self.session.get(
            f'{self.base_url}/api/datasets/get-dataset-list',
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response.raise_for_status()
        return {
            'success': True,
            'datasets': response.json()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
    """
    Get metadata for a specific dataset including available fields.

    Args:
        dataset_id: Dataset ID (e.g., 'gd_lw8kc4s7r2' for Google Maps)

    Returns:
        Dataset schema and filterable fields
    """
    try:
        response = self.session.get(
            f'{self.base_url}/api/datasets/get-dataset-metadata',
            params={'dataset_id': dataset_id},
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response.raise_for_status()
        return {
            'success': True,
            'metadata': response.json()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def filter_marketplace_dataset(self, dataset_id: str,
                              filters: Dict[str, Any],
                              format: str = 'json',
                              limit: Optional[int] = None,
                              sample: bool = True) -> Dict[str, Any]:
    """
    Filter marketplace dataset with specific criteria.

    Args:
        dataset_id: Dataset ID (e.g., 'gd_lw8kc4s7r2' for Google Maps)
        filters: Filter criteria dictionary
        format: Output format ('json' or 'csv')
        limit: Maximum records to return
        sample: If True, returns sample data; if False, creates snapshot for download

    Returns:
        Filtered dataset or snapshot information

    Example filters for Google Maps:
        {
            'country': 'United States',
            'category': {'$regex': 'beauty|gun'},
            'name': {'$nin': ['Sally Beauty', 'Ulta', 'Sephora']},
            'chain': False,  # If field exists
            'review_count': {'$lt': 500}
        }
    """
    try:
        payload = {
            'dataset_id': dataset_id,
            'filters': filters,
            'format': format
        }

        if limit:
            payload['limit'] = limit

        if not sample:
            payload['deliver'] = True  # Create snapshot for full download

        response = self.session.post(
            f'{self.base_url}/api/datasets/filter-dataset',
            json=payload,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response.raise_for_status()

        result = response.json()

        if sample:
            return {
                'success': True,
                'data': result.get('data', []),
                'count': result.get('count', 0),
                'sample': True
            }
        else:
            return {
                'success': True,
                'snapshot_id': result.get('snapshot_id'),
                'status': result.get('status'),
                'sample': False,
                'message': 'Snapshot created. Use get_snapshot_status() to check progress.'
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def filter_dataset_with_exclusion_list(self, dataset_id: str,
                                       inclusion_filters: Dict[str, Any],
                                       exclusion_list: List[str],
                                       exclusion_field: str = 'name') -> Dict[str, Any]:
    """
    Filter dataset with inclusion criteria and exclusion list.

    Args:
        dataset_id: Dataset ID
        inclusion_filters: What to include
        exclusion_list: List of values to exclude
        exclusion_field: Field to apply exclusion list to

    Returns:
        Filtered results
    """
    # Combine inclusion and exclusion filters
    filters = inclusion_filters.copy()
    filters[exclusion_field] = {'$nin': exclusion_list}

    return self.filter_marketplace_dataset(dataset_id, filters)

def get_snapshot_status(self, snapshot_id: str) -> Dict[str, Any]:
    """
    Check status of a dataset snapshot.

    Args:
        snapshot_id: Snapshot ID from filter_marketplace_dataset()

    Returns:
        Snapshot status and download information
    """
    try:
        response = self.session.get(
            f'{self.base_url}/api/datasets/get-snapshot-meta',
            params={'snapshot_id': snapshot_id},
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        response.raise_for_status()
        return {
            'success': True,
            'snapshot': response.json()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def download_snapshot(self, snapshot_id: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Download a completed snapshot.

    Args:
        snapshot_id: Snapshot ID
        output_path: Where to save the file (optional)

    Returns:
        Download status
    """
    try:
        response = self.session.get(
            f'{self.base_url}/api/datasets/download-the-file-by-snapshot_id',
            params={'snapshot_id': snapshot_id},
            headers={'Authorization': f'Bearer {self.api_key}'},
            stream=True
        )
        response.raise_for_status()

        if output_path:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return {
                'success': True,
                'saved_to': output_path
            }
        else:
            return {
                'success': True,
                'data': response.content
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Known dataset IDs (add as class variables near line 90)
MARKETPLACE_DATASETS = {
    'google_maps': 'gd_lw8kc4s7r2',
    'google_search': 'gd_l7q7zkf5kq7vz7164',
    'linkedin_companies': 'gd_l3q4sjf9p5ld7zj72',
    'amazon_products': 'gd_l1g5kqf3j4h2k8j92'
}
```

### 2. Add Chain Exclusion Lists

Create a new file `/path/to/api-toolkit/services/brightdata/chain_lists.py`:

```python
"""
Chain store lists for filtering marketplace datasets
"""

BEAUTY_CHAINS = [
    # Major Beauty Chains
    'Sally Beauty', 'Sally Beauty Supply', 'Ulta', 'Ulta Beauty',
    'Sephora', 'CosmoProf', 'Beauty Brands', 'Harmon Face Values',
    "Ricky's NYC", 'Beauty 360', 'Bluemercury', 'Trade Secret',
    'Beauty First', 'Perfumania', 'The Body Shop', 'Lush Cosmetics',
    'Bath & Body Works', "Victoria's Secret", 'Yankee Candle',

    # Department Stores with Beauty Sections
    'CVS', 'CVS Pharmacy', 'Walgreens', 'Rite Aid', 'Duane Reade',
    'Target', 'Walmart', 'Macy\'s', 'Nordstrom', 'JCPenney',
    'Kohl\'s', 'Dillard\'s', 'Lord & Taylor', 'Bloomingdale\'s'
]

GUN_CHAINS = [
    "Sportsman's Warehouse", 'Bass Pro Shops', "Cabela's",
    "Dick's Sporting Goods", 'Field & Stream', 'Big 5 Sporting Goods',
    'Gander Mountain', 'Gander Outdoors', 'Scheels',
    'Academy Sports + Outdoors', "Dunham's Sports", 'Turner\'s Outdoorsman',
    'Fin Feather Fur Outfitters', 'Guns & Ammo', 'Range USA',
    'Shoot Point Blank', 'The Range 702', 'Gun World'
]

def get_exclusion_list(category: str) -> list:
    """
    Get chain exclusion list for a category.

    Args:
        category: 'beauty', 'gun', or 'all'

    Returns:
        List of chain names to exclude
    """
    if category.lower() == 'beauty':
        return BEAUTY_CHAINS
    elif category.lower() == 'gun':
        return GUN_CHAINS
    elif category.lower() == 'all':
        return BEAUTY_CHAINS + GUN_CHAINS
    else:
        return []
```

### 3. Update `examples.py`

Add these examples to `/path/to/api-toolkit/services/brightdata/examples.py` (after line 350):

```python
def marketplace_dataset_examples():
    """Marketplace dataset filtering examples"""
    print("\n=== Marketplace Dataset Examples ===\n")

    api = BrightDataAPI()

    # Import chain lists
    from services.brightdata.chain_lists import get_exclusion_list

    # 1. List available datasets
    print("📊 Available Datasets:")
    datasets = api.get_dataset_list()
    if datasets['success']:
        for dataset in datasets.get('datasets', [])[:5]:
            print(f"  - {dataset.get('name')}: {dataset.get('id')}")

    # 2. Get Google Maps dataset metadata
    print("\n🗺️ Google Maps Dataset Schema:")
    metadata = api.get_dataset_metadata('gd_lw8kc4s7r2')
    if metadata['success']:
        fields = metadata.get('metadata', {}).get('fields', [])
        print(f"  Available fields: {', '.join(fields[:10])}")

    # 3. Filter beauty and gun stores (excluding chains)
    print("\n🔍 Filtering Beauty & Gun Stores (Independent Only):")

    filters = {
        'country': 'United States',
        'category': {'$regex': 'beauty|gun|firearm|salon|cosmetic'},
        'name': {'$nin': get_exclusion_list('all')},
        'review_count': {'$lt': 500}  # Chains typically have more reviews
    }

    # Get sample data first
    sample_result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=filters,
        limit=10,
        sample=True
    )

    if sample_result['success']:
        print(f"  ✅ Found {sample_result['count']} matching locations")
        print(f"  📍 Sample results:")
        for location in sample_result.get('data', [])[:5]:
            name = location.get('name', 'Unknown')
            category = location.get('category', 'Unknown')
            city = location.get('city', 'Unknown')
            print(f"    - {name} ({category}) in {city}")

    # 4. Create full dataset snapshot
    print("\n💾 Creating Full Dataset Snapshot:")

    full_result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=filters,
        sample=False  # This creates a snapshot for download
    )

    if full_result['success']:
        snapshot_id = full_result.get('snapshot_id')
        print(f"  ✅ Snapshot created: {snapshot_id}")
        print(f"  📊 Status: {full_result.get('status')}")
        print(f"  💡 Use api.get_snapshot_status('{snapshot_id}') to check progress")


def smart_filtering_example():
    """Advanced filtering with business logic"""
    print("\n=== Smart Filtering Example ===\n")

    from services.brightdata.chain_lists import BEAUTY_CHAINS, GUN_CHAINS

    api = BrightDataAPI()

    # Multi-stage filtering approach
    print("🎯 Multi-Stage Filtering Strategy:\n")

    # Stage 1: Basic filtering
    print("Stage 1: Apply basic filters")
    basic_filters = {
        'country': 'United States',
        'state': {'$in': ['Texas', 'California', 'Florida', 'New York']},
        'category': {'$regex': 'beauty|salon|cosmetic|gun|firearm|sporting'}
    }

    # Stage 2: Exclude known chains
    print("Stage 2: Exclude known chains")
    basic_filters['name'] = {
        '$nin': BEAUTY_CHAINS + GUN_CHAINS,
        '$not': {'$regex': '(#\\d+|store \\d+|location \\d+)'}  # Store numbers
    }

    # Stage 3: Business indicators
    print("Stage 3: Filter by business indicators")
    basic_filters.update({
        'review_count': {'$gte': 10, '$lte': 500},  # Active but not massive chains
        'rating': {'$gte': 3.5},  # Quality businesses
        'price_range': {'$in': ['$', '$$', '$$$']},  # Not luxury/exclusive
        'permanently_closed': False
    })

    # Test the filters
    result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=basic_filters,
        limit=100,
        sample=True
    )

    if result['success']:
        print(f"\n✅ Filtering Results:")
        print(f"  Total matches: {result.get('count', 0)}")

        # Analyze the sample
        data = result.get('data', [])
        categories = {}
        states = {}

        for item in data:
            cat = item.get('category', 'Unknown')
            state = item.get('state', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
            states[state] = states.get(state, 0) + 1

        print(f"\n  Category Distribution:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {cat}: {count}")

        print(f"\n  State Distribution:")
        for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {state}: {count}")
```

### 4. Update CLI Interface

Add to the CLI section of `api.py` (around line 690):

```python
elif command == "datasets":
    # List marketplace datasets
    datasets = api.get_dataset_list()
    if datasets['success']:
        print("📊 Available Marketplace Datasets:")
        for ds in datasets.get('datasets', []):
            print(f"  - {ds.get('name')}: {ds.get('id')}")

elif command == "filter" and len(sys.argv) > 2:
    # Quick filter for beauty/gun stores
    from services.brightdata.chain_lists import get_exclusion_list

    dataset_id = 'gd_lw8kc4s7r2'  # Google Maps
    category = sys.argv[2]  # 'beauty' or 'gun'

    filters = {
        'country': 'United States',
        'category': {'$regex': category},
        'name': {'$nin': get_exclusion_list(category)}
    }

    result = api.filter_marketplace_dataset(
        dataset_id=dataset_id,
        filters=filters,
        limit=10,
        sample=True
    )

    if result['success']:
        print(f"✅ Found {result['count']} {category} locations")
        for item in result.get('data', [])[:5]:
            print(f"  - {item.get('name')} in {item.get('city')}, {item.get('state')}")
```

### 5. Update `README.md`

Add this section to `/path/to/api-toolkit/services/brightdata/README.md`:

```markdown
## Marketplace Datasets

Access and filter BrightData's marketplace datasets programmatically.

### Quick Start
```python
from services.brightdata.api import BrightDataAPI
from services.brightdata.chain_lists import get_exclusion_list

api = BrightDataAPI()

# Filter Google Maps for independent beauty/gun stores
filters = {
    'country': 'United States',
    'category': {'$regex': 'beauty|gun'},
    'name': {'$nin': get_exclusion_list('all')},
    'review_count': {'$lt': 500}
}

result = api.filter_marketplace_dataset(
    dataset_id='gd_lw8kc4s7r2',  # Google Maps
    filters=filters,
    limit=100,
    sample=True
)

print(f"Found {result['count']} independent businesses")
```

### Available Datasets
- Google Maps: `gd_lw8kc4s7r2`
- Google Search: `gd_l7q7zkf5kq7vz7164`
- LinkedIn Companies: `gd_l3q4sjf9p5ld7zj72`
- Amazon Products: `gd_l1g5kqf3j4h2k8j92`

### Filter Operators
- `$eq`: Equals
- `$ne`: Not equals
- `$in`: In array
- `$nin`: Not in array
- `$regex`: Regex match
- `$gt`, `$gte`, `$lt`, `$lte`: Comparison
- `$exists`: Field exists
```

## Testing

After implementing these changes, test with:

```bash
# Test from the API toolkit directory
cd /path/to/api-toolkit

# List datasets
python services/brightdata/api.py datasets

# Quick filter test
python services/brightdata/api.py filter beauty

# Run examples
python services/brightdata/examples.py marketplace

# Python script test
python -c "
from services.brightdata.api import BrightDataAPI
api = BrightDataAPI()
result = api.get_dataset_metadata('gd_lw8kc4s7r2')
print('Success:', result.get('success'))
"
```

## Environment Variables Required

Make sure these are set in your `.env` file:
```bash
BRIGHTDATA_API_KEY=your_api_key_here
BRIGHTDATA_CUSTOMER_ID=your_customer_id
BRIGHTDATA_ZONE=your_zone_name
```

## Notes for Implementation

1. The actual dataset IDs and field names may vary - use `get_dataset_metadata()` to discover the exact field names
2. Some filter operators might not be supported - check BrightData's documentation
3. Rate limits apply - implement appropriate delays for large requests
4. Snapshots for large datasets take time to generate - implement polling with `get_snapshot_status()`

## Cost Considerations

- Sampling is free/cheap - use `sample=True` for testing
- Full dataset downloads incur costs - use specific filters to minimize data
- Check your BrightData account for specific pricing

This completes the marketplace dataset functionality for the BrightData API toolkit.