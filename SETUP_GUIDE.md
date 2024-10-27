# API Toolkit Setup Guide (5 Minutes)

> **For:** Developers, LLM users (Claude Code, Cursor, Aider), automation scripts

---

## Step 1: Install the Toolkit (1 min)

```bash
# Navigate to your project
cd /path/to/your/project

# Run installer
/path/to/api-toolkit/install.sh

# Choose option 1 (symlink - recommended)
# Type: 1 + Enter
```

**What this does:**
- Creates `api-toolkit/` symlink in your project
- Toolkit updates automatically when source updates
- No code duplication

---

## Step 2: Create .env File (2 min)

```bash
# Still in your project directory
cp api-toolkit/.env.example .env
```

**Edit .env with your API keys:**
```bash
# Use any editor
nano .env
# or
code .env
# or
vim .env
```

**Add your credentials** (example):
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...your-key

# Smartlead
SMARTLEAD_API_KEY=your-smartlead-key

# Only add the services you actually use!
```

**Save and close** the file.

---

## Step 3: Test It Works (1 min)

```bash
# Test which .env is loaded
python api-toolkit/test-env-loading.py
```

**You should see:**
```
✅ Environment loaded from:
   /path/to/your/project/.env

SUPABASE:
  ✅ SUPABASE_URL: SET
  ✅ SUPABASE_SERVICE_ROLE_KEY: SET

SMARTLEAD:
  ✅ SMARTLEAD_API_KEY: SET
```

**If you see ❌ NOT SET:**
- Open `.env` again
- Check for typos in variable names
- Make sure you saved the file

---

## Step 4: Use It! (1 min)

**Create a test script:**
```bash
# Create test file
cat > test_toolkit.py << 'EOF'
from api_toolkit.services.supabase.api import SupabaseAPI

# Connect to Supabase
api = SupabaseAPI('project1')

# Show what's available
api.quick_start()

# Query some data
results = api.query('leads', limit=5)
print(f"\nGot {len(results)} results!")
EOF

# Run it
python test_toolkit.py
```

**Expected output:**
```
🚀 Supabase Quick Start (smoothed)
==================================================
✅ Connected successfully
📊 Available tables: leads, brands, scraping_results
...
Got 5 results!
```

---

## ✅ You're Done!

**Your project structure:**
```
your-project/
├── .env                    # Your API keys (add to .gitignore!)
├── api-toolkit/           # Symlink to toolkit
├── test_toolkit.py        # Your test script
└── main.py                # Your actual code
```

**Next steps:**
- Read [README.md](README.md) for full documentation
- See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common patterns
- Check [ENV_TROUBLESHOOTING.md](ENV_TROUBLESHOOTING.md) if issues arise

---

## 🚨 Troubleshooting

### "Module not found" Error
```bash
# Make sure you're in project directory
pwd

# Check api-toolkit exists
ls -la api-toolkit/

# If missing, re-run install.sh
```

### "No environment variables set"
```bash
# Check .env exists in project root
ls -la .env

# Check .env location
python api-toolkit/test-env-loading.py

# If wrong location, move it:
mv api-toolkit/.env ./.env
```

### "Connection failed"
```bash
# Verify your API keys are correct
cat .env | grep SUPABASE_URL

# Test specific service
python api-toolkit/toolkit.py supabase test
```

---

## 🔐 Security Note

**Add .env to .gitignore:**
```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Ignore .env file"
```

**Never commit:**
- `.env` (actual credentials)

**Safe to commit:**
- `.env.example` (template with fake values)
- `api-toolkit/` (if using symlink, it's just a pointer)

---

## 💡 Tips

1. **One .env per project** - Different projects can have different credentials
2. **Use .env.example** - Document which variables are needed
3. **Test first** - Run `test-env-loading.py` before writing code
4. **Check the docs** - README.md has tons of examples

---

## 🆘 Still Stuck?

Run the diagnostic and share the output:
```bash
python api-toolkit/test-env-loading.py > diagnostic.txt
cat diagnostic.txt
```

Look for:
- Which .env file was loaded
- Which variables are SET vs NOT SET
- Follow the hints in the output

---

**Setup time:** ~5 minutes
**Works with:** Python scripts, notebooks, LLMs, automation
**Token cost:** 500-1000 (vs 90,000 for MCP servers!)
