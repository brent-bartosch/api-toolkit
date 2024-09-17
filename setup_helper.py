#!/usr/bin/env python3
"""
Out-of-the-Box Setup Helper
Makes the API toolkit work immediately in any project
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
import json


class ToolkitSetupHelper:
    """
    Ensures API toolkit works immediately when installed in a project.
    No manual configuration needed.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.toolkit_path = self.project_path / "api-toolkit"
        
    def quick_check(self) -> Dict[str, bool]:
        """
        Quick diagnostic - what's working out of the box?
        """
        checks = {
            'toolkit_found': False,
            'env_configured': False,
            'imports_work': False,
            'supabase_connected': False,
            'schema_discoverable': False
        }
        
        # 1. Is toolkit installed?
        if self.toolkit_path.exists() or Path('/path/to/api-toolkit').exists():
            checks['toolkit_found'] = True
            
        # 2. Is environment configured?
        env_locations = [
            self.project_path / '.env',
            self.toolkit_path / '.env',
            Path('/path/to/api-toolkit/.env')
        ]
        
        for env_path in env_locations:
            if env_path.exists():
                checks['env_configured'] = True
                break
        
        # 3. Can we import?
        try:
            # Add to path if needed
            if not checks['toolkit_found']:
                sys.path.insert(0, '/path/to/api-toolkit')
            else:
                sys.path.insert(0, str(self.toolkit_path))
                
            from services.supabase.api import SupabaseAPI
            checks['imports_work'] = True
            
            # 4. Can we connect?
            try:
                api = SupabaseAPI('project1')
                if api.test_connection():
                    checks['supabase_connected'] = True
                    
                    # 5. Can we discover schema?
                    try:
                        # Just check if method exists and doesn't crash
                        api.explore  # Check method exists
                        checks['schema_discoverable'] = True
                    except:
                        pass
            except:
                pass
                
        except ImportError:
            pass
            
        return checks
    
    def generate_quickstart(self) -> str:
        """
        Generate a quickstart.py file for immediate use
        """
        quickstart_code = '''#!/usr/bin/env python3
"""
API Toolkit Quickstart
This file is auto-generated to work immediately in your project.
"""

import sys
from pathlib import Path

# Auto-detect toolkit location
toolkit_paths = [
    Path('api-toolkit'),
    Path('/path/to/api-toolkit')
]

for path in toolkit_paths:
    if path.exists():
        sys.path.insert(0, str(path))
        break

# Now you can use the toolkit!
from services.supabase.api import SupabaseAPI
from services.supabase.query_helpers import QueryBuilder

def explore_database(project='project1'):
    """Explore what's available in the database"""
    try:
        api = SupabaseAPI(project)
        
        if not api.test_connection():
            print(f"❌ Could not connect to {project}")
            print("   Check your .env file has the right keys")
            return None
            
        print(f"✅ Connected to {project}!")
        print("\\nExploring database...")
        api.explore()
        
        return api
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def quick_query_example(api, table_name):
    """Show a quick query example"""
    print(f"\\nSample query for {table_name}:")
    
    # Get schema first
    schema = api.get_schema(table_name)
    print(f"Columns: {[col['column'] for col in schema]}")
    
    # Query with limit
    results = api.query(table_name, limit=3)
    print(f"Found {len(results)} records (limited to 3)")
    
    if results:
        print(f"Sample record keys: {list(results[0].keys())}")
    
    return results

def query_builder_example(api, table_name):
    """Show QueryBuilder usage"""
    print(f"\\nUsing QueryBuilder for {table_name}:")
    
    query = (QueryBuilder(table_name)
             .select('*')
             .limit(5))
    
    results = query.execute(api)
    print(f"QueryBuilder returned {len(results)} records")
    return results

if __name__ == "__main__":
    print("🚀 API Toolkit Quickstart")
    print("=" * 50)
    
    # Choose project
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else 'project1'
    
    # Explore database
    api = explore_database(project)
    
    if api:
        # Show example queries
        print("\\n" + "=" * 50)
        print("Example Queries:")
        
        # You can change this to any table in your project
        sample_tables = {
            'project1': 'leads',
            'project2': 'customers',
            'project3': 'scrape_guide'
        }
        
        table = sample_tables.get(project, 'users')
        
        try:
            quick_query_example(api, table)
            query_builder_example(api, table)
        except Exception as e:
            print(f"Could not query {table}: {e}")
            print("Try a different table name")
    
    print("\\n✨ Quickstart complete!")
    print("\\nNext steps:")
    print("1. Check the schema with: api.get_schema('table_name')")
    print("2. Use QueryBuilder for complex queries")
    print("3. Read services/supabase/examples.py for more patterns")
'''
        
        quickstart_file = self.project_path / 'api_toolkit_quickstart.py'
        with open(quickstart_file, 'w') as f:
            f.write(quickstart_code)
            
        os.chmod(quickstart_file, 0o755)  # Make executable
        
        return str(quickstart_file)
    
    def generate_env_template(self) -> str:
        """
        Generate .env template if missing
        """
        env_template = '''# API Toolkit Environment Variables
# Generated template - fill in your actual values

# Supabase Project 1: Project1 (Lead Gen)
SUPABASE_URL=https://your-project-1.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here

# Supabase Project 2: Project2 (CRM)
SUPABASE_URL_2=https://your-project-2.supabase.co
SUPABASE_SERVICE_ROLE_KEY_2=your-key-here

# Supabase Project 3: Project 3
SUPABASE_URL_3=https://your-project-3.supabase.co
SUPABASE_SERVICE_ROLE_KEY_3=your-key-here
'''
        
        env_file = self.project_path / '.env.toolkit-template'
        with open(env_file, 'w') as f:
            f.write(env_template)
            
        return str(env_file)
    
    def setup_out_of_box(self) -> None:
        """
        Make everything work out of the box
        """
        print("🔧 Setting up API Toolkit for out-of-box usage...")
        
        # 1. Run diagnostic
        checks = self.quick_check()
        
        print("\n📊 Diagnostic Results:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
        
        # 2. Generate helpers if needed
        if not all(checks.values()):
            print("\n📝 Generating helper files...")
            
            # Generate quickstart
            quickstart = self.generate_quickstart()
            print(f"  ✓ Created {quickstart}")
            
            # Generate env template if needed
            if not checks['env_configured']:
                env_template = self.generate_env_template()
                print(f"  ✓ Created {env_template}")
                print("  ⚠️  Fill in your API keys in .env file")
        
        # 3. Generate type hints file
        self.generate_type_hints()
        
        print("\n✅ Setup complete!")
        
        if all(checks.values()):
            print("\n🎉 Everything works out of the box!")
            print("Try: python api_toolkit_quickstart.py")
        else:
            print("\n⚠️  Some configuration needed:")
            if not checks['env_configured']:
                print("  1. Copy .env.toolkit-template to .env")
                print("  2. Add your API keys")
            if not checks['toolkit_found']:
                print("  3. Run: /path/to/api-toolkit/install.sh")
    
    def generate_type_hints(self) -> None:
        """
        Generate Python type hints for better IDE support
        """
        stubs_content = '''"""
API Toolkit Type Stubs
Auto-generated for IDE autocomplete support
"""

from typing import List, Dict, Any, Optional, Union

class SupabaseAPI:
    def __init__(self, project: str = 'project1', 
                 url: Optional[str] = None,
                 key: Optional[str] = None,
                 use_anon_key: bool = False): ...
    
    def query(self, table: str,
             select: str = "*",
             filters: Optional[Dict] = None,
             order: Optional[str] = None,
             limit: Optional[int] = None,
             offset: Optional[int] = None) -> List[Dict]: ...
    
    def get_by_id(self, table: str, id_value: Any, 
                  id_column: str = 'id') -> Optional[Dict]: ...
    
    def insert(self, table: str, 
               data: Union[Dict, List[Dict]],
               on_conflict: Optional[str] = None) -> Union[Dict, List[Dict]]: ...
    
    def update(self, table: str, data: Dict, 
               filters: Dict) -> List[Dict]: ...
    
    def delete(self, table: str, filters: Dict) -> List[Dict]: ...
    
    def rpc(self, function_name: str, 
            params: Optional[Dict] = None) -> Any: ...
    
    def explore(self, table: Optional[str] = None) -> None: ...
    
    def get_schema(self, table: str) -> List[Dict[str, Any]]: ...
    
    def count(self, table: str, 
              filters: Optional[Dict] = None) -> int: ...
    
    def test_connection(self) -> bool: ...

class QueryBuilder:
    def __init__(self, table: str): ...
    def select(self, *columns) -> 'QueryBuilder': ...
    def where(self, column: str, operator: str, value: Any) -> 'QueryBuilder': ...
    def equals(self, column: str, value: Any) -> 'QueryBuilder': ...
    def contains(self, column: str, value: str) -> 'QueryBuilder': ...
    def order(self, column: str, desc: bool = False) -> 'QueryBuilder': ...
    def limit(self, count: int) -> 'QueryBuilder': ...
    def offset(self, count: int) -> 'QueryBuilder': ...
    def build(self) -> Dict: ...
    def execute(self, api: SupabaseAPI) -> List[Dict]: ...
'''
        
        stubs_file = self.project_path / 'api_toolkit.pyi'
        with open(stubs_file, 'w') as f:
            f.write(stubs_content)


if __name__ == "__main__":
    import sys
    
    # Check command
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Just run diagnostic
        helper = ToolkitSetupHelper()
        checks = helper.quick_check()
        
        all_good = all(checks.values())
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check.replace('_', ' ').title()}")
        
        sys.exit(0 if all_good else 1)
    
    else:
        # Full setup
        helper = ToolkitSetupHelper()
        helper.setup_out_of_box()