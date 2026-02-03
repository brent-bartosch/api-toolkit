# API Toolkit Integration Guide

## 🚀 Quick Installation (From Any Project)

```bash
# Navigate to your project
cd /path/to/your/project

# Run the installer
/path/to/api-toolkit/install.sh
```

## Installation Options

### Option 1: Symbolic Link (Recommended)
- **Best for**: Active development
- **Pros**: Automatically gets updates, no duplication
- **Cons**: Requires source directory to remain in place

```bash
# Creates: ./api-toolkit -> /path/to/api-toolkit
ln -s /path/to/api-toolkit api-toolkit
```

### Option 2: Copy Files
- **Best for**: Production deployments
- **Pros**: Self-contained, can be committed to git
- **Cons**: Won't receive updates automatically

```bash
# Creates: ./api-toolkit (standalone copy)
cp -r /path/to/api-toolkit .
```

### Option 3: Python Package
- **Best for**: Import from anywhere
- **Pros**: Standard Python packaging, works from any directory
- **Cons**: Requires pip

```bash
# Install as editable package
pip install -e /path/to/api-toolkit
```

## Project Integration Patterns

### 1. Data Pipeline Project
```python
# data_pipeline.py
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.klaviyo.api import KlaviyoAPI

# Sync data from Supabase to Klaviyo
supabase = SupabaseAPI('project1')
klaviyo = KlaviyoAPI()

# Get customers from database
customers = supabase.query('customers', filters={'status': 'eq.active'})

# Update Klaviyo profiles
for customer in customers:
    klaviyo.update_profile(customer['email'], customer)
```

### 2. Web Project 3 Project
```python
# scraper.py
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.brightdata.api import BrightDataAPI

supabase = SupabaseAPI('project3')
scraper = BrightDataAPI()

# Get scraping targets
targets = supabase.query('scrape_guide', filters={'priority': 'gte.8'})

# Execute scraping
for target in targets:
    result = scraper.scrape(target['url'])
    supabase.insert('scrape_results', result)
```

### 3. E-commerce Integration
```python
# shopify_sync.py
from api_toolkit.services.shopify.api import ShopifyAPI
from api_toolkit.services.supabase.api import SupabaseAPI

shopify = ShopifyAPI()
db = SupabaseAPI('project2')

# Sync orders to database
orders = shopify.get_orders(status='fulfilled')
db.insert('orders', orders, on_conflict='order_id')
```

## Environment Configuration

### Per-Project .env
Each project can have its own `.env` file:

```bash
project1/
├── .env                    # Project-specific keys
├── api-toolkit/           # Symlink or copy
└── main.py

project2/
├── .env                    # Different keys
├── api-toolkit/           # Same toolkit
└── app.py
```

### Shared Configuration
Or use a central `.env` in the toolkit:

```bash
api-toolkit/
└── .env                    # Shared by all projects

project1/
├── api-toolkit -> ../api-toolkit
└── main.py                 # Uses shared .env

project2/
├── api-toolkit -> ../api-toolkit
└── app.py                  # Uses same shared .env
```

## Usage Examples

### CLI Usage (From Any Directory)
```bash
# If using symlink or copy
python api-toolkit/toolkit.py supabase test

# If installed as package
python -m api_toolkit.toolkit supabase test

# Direct script execution
python /path/to/api-toolkit/toolkit.py supabase test
```

### Python Import Patterns

#### With Symlink/Copy
```python
# Add to Python path
import sys
sys.path.insert(0, 'api-toolkit')

from services.supabase.api import SupabaseAPI
```

#### With Package Install
```python
# Direct import (no path manipulation needed)
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.klaviyo.api import KlaviyoAPI
```

#### Direct Path Import
```python
import sys
sys.path.insert(0, '/path/to/api-toolkit')

from services.supabase.api import SupabaseAPI
```

## Multi-Project Workflow

### Development Setup
```bash
~/Development/
├── api-toolkit/           # Master toolkit
├── project-a/
│   ├── api-toolkit -> ../api-toolkit
│   └── .env              # Project A keys
├── project-b/
│   ├── api-toolkit -> ../api-toolkit
│   └── .env              # Project B keys
└── project-c/
    ├── api-toolkit/      # Copied for production
    └── .env              # Project C keys
```

### CI/CD Integration
```yaml
# .github/workflows/deploy.yml
steps:
  - uses: actions/checkout@v2
  
  - name: Install API Toolkit
    run: |
      git clone https://github.com/yourusername/api-toolkit.git
      cd api-toolkit && pip install -r requirements.txt
  
  - name: Configure Environment
    run: |
      echo "SUPABASE_URL=${{ secrets.SUPABASE_URL }}" >> .env
      echo "SUPABASE_SERVICE_ROLE_KEY=${{ secrets.SUPABASE_KEY }}" >> .env
  
  - name: Run Integration
    run: python main.py
```

## Best Practices

### 1. Token Management
```python
# Load only what you need
from api_toolkit.services.supabase.api import SupabaseAPI
# Not: from api_toolkit.services import *
```

### 2. Environment Variables
```python
# Check configuration before use
from api_toolkit.core.config import Config

config = Config()
if not config.get('SUPABASE_URL'):
    print("Warning: Supabase not configured")
```

### 3. Error Handling
```python
from api_toolkit.services.supabase.api import SupabaseAPI

try:
    api = SupabaseAPI('project1')
    data = api.query('users')
except Exception as e:
    print(f"API Error: {e}")
    # Fallback logic
```

### 4. Project Organization
```
your-project/
├── api-toolkit/           # Toolkit (symlink recommended)
├── .env                   # Your API keys
├── .gitignore            # Exclude .env and api-toolkit if symlink
├── requirements.txt      # Include api-toolkit requirements
└── src/
    └── integrations.py   # Your integration code
```

## Updating the Toolkit

### For Symlinks
```bash
# Updates automatically when source is updated
cd /path/to/api-toolkit
git pull
```

### For Copies
```bash
# Re-run installer and choose "Copy files"
cd your-project
rm -rf api-toolkit
/path/to/api-toolkit/install.sh
# Choose option 2
```

### For Package Installs
```bash
# Already linked, just pull updates
cd /path/to/api-toolkit
git pull
```

## Troubleshooting

### Import Errors
```python
# Fix: Add to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api-toolkit'))
```

### Environment Not Loading
```python
# Fix: Explicitly load .env
from dotenv import load_dotenv
load_dotenv()  # Or load_dotenv('.env')
```

### API Key Issues
```bash
# Debug: Check what's loaded
python api-toolkit/toolkit.py supabase check
```

### Permission Errors
```bash
# Fix: Make scripts executable
chmod +x api-toolkit/toolkit.py
chmod +x api-toolkit/install.sh
```

## Quick Start Commands

```bash
# 1. Install in your project
cd your-project
/path/to/api-toolkit/install.sh

# 2. Configure environment
cp api-toolkit/.env.example .env
# Edit .env with your keys

# 3. Test connection
python api-toolkit/toolkit.py supabase test

# 4. Start using
python -c "from api_toolkit.services.supabase.api import SupabaseAPI; print(SupabaseAPI('project1').test_connection())"
```

---

**Remember**: The toolkit saves ~89,400 tokens per conversation compared to MCP servers!