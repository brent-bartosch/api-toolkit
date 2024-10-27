# Environment Variable Troubleshooting Guide

> **Universal Guide:** Works for Python scripts, LLMs (Claude Code, Cursor, Aider), Jupyter notebooks, and any automation tool.

## 🎯 Quick Answer: Where Should My .env File Be?

**Put it in your PROJECT ROOT, not in the `api-toolkit/` subdirectory.**

```bash
✅ CORRECT:
your-project/
├── .env                    # HERE!
├── api-toolkit/           # Symlink to toolkit
└── main.py

❌ WRONG:
your-project/
├── api-toolkit/
│   └── .env               # Not here (will work but not ideal)
└── main.py
```

---

## 🔍 How .env Loading Works

The toolkit searches for `.env` files in **priority order**:

### Priority 1: Project Root (✅ Recommended)
```bash
./your-project/.env
```
- **Why**: Keeps credentials with your project
- **Git**: Easy to add to `.gitignore`
- **Standard**: Most projects expect `.env` in root

### Priority 2: Toolkit Directory (Fallback)
```bash
./your-project/api-toolkit/.env
```
- **Why**: For standalone toolkit usage
- **Use case**: Testing toolkit directly

### Priority 3: Home Directory (Global Fallback)
```bash
~/.api-toolkit.env
```
- **Why**: Global credentials across all projects
- **Use case**: Same credentials for all projects

---

## 🛠 Diagnosing Issues

### Test 1: Check Which .env Is Loaded

```bash
cd /your/project
python api-toolkit/test-env-loading.py
```

**Expected output:**
```
✅ Environment loaded from:
   /Users/you/your-project/.env
```

### Test 2: Verify from Python

```python
from api_toolkit.core.config import Config

# Show where env was loaded from
print(f"Loaded from: {Config.get_env_source()}")

# Check specific service
status = Config.check_environment('smartlead')
print(status)  # {'SMARTLEAD_API_KEY': True}
```

---

## 🚨 Common Problems & Solutions

### Problem 1: "Credentials Not Found"

**Symptoms:**
- `api.test_connection()` returns False
- Errors about missing API keys

**Diagnosis:**
```bash
python api-toolkit/test-env-loading.py
```

**Solutions:**

1. **No .env file found anywhere**
   ```bash
   # Create .env in project root
   touch .env
   # Add your credentials
   echo "SMARTLEAD_API_KEY=your-key-here" >> .env
   ```

2. **.env exists but wrong location**
   ```bash
   # Move it to project root
   mv api-toolkit/.env ./.env
   ```

3. **.env exists but wrong variable names**
   ```bash
   # Check exact variable names needed
   python -c "from api_toolkit.core.config import Config; print(Config.SERVICES['smartlead']['env_vars'])"
   # Output: ['SMARTLEAD_API_KEY']
   ```

### Problem 2: "Wrong .env Being Used"

**Symptoms:**
- Test script shows different path than expected
- Wrong credentials being used

**Solution:**
```bash
# 1. Check current working directory
pwd

# 2. Check where .env files exist
ls -la .env
ls -la api-toolkit/.env
ls -la ~/.api-toolkit.env

# 3. Remove unwanted .env files (keep project root only)
rm api-toolkit/.env  # If you want to use project root
```

### Problem 3: "Environment Variables Not Updating"

**Symptoms:**
- Changed .env but code still uses old values
- Added new keys but not detected

**Solutions:**

1. **Python caches .env on first import**
   ```bash
   # Restart your Python process/script
   # OR force reload:
   python -c "
   from dotenv import load_dotenv
   load_dotenv('.env', override=True)
   "
   ```

2. **Check for system environment variables**
   ```bash
   # System env vars override .env files
   env | grep SMARTLEAD

   # If found and wrong, unset it:
   unset SMARTLEAD_API_KEY
   ```

### Problem 4: "Different Projects Need Different Keys"

**Scenario:**
- Project A: Smartlead account 1
- Project B: Smartlead account 2

**Solution: Keep separate .env per project**

```bash
# Project A
/projects/project-a/
├── .env                    # Account 1 credentials
└── api-toolkit/           # Symlink

# Project B
/projects/project-b/
├── .env                    # Account 2 credentials
└── api-toolkit/           # Same symlink
```

When you run code, it automatically uses the `.env` in that project's root!

---

## ✅ Best Practices

### 1. One .env Per Project
```bash
# ✅ DO THIS
project-a/.env
project-b/.env

# ❌ NOT THIS
api-toolkit/.env (shared by all projects)
```

### 2. Add to .gitignore
```bash
# In your project root
echo ".env" >> .gitignore
```

### 3. Use .env.example for Documentation
```bash
# Create template
cp .env .env.example

# Remove actual keys
sed -i '' 's/=.*/=your-key-here/g' .env.example

# Commit the template
git add .env.example
```

### 4. Verify Before Running
```bash
# Quick pre-flight check
python api-toolkit/test-env-loading.py | grep "✅ Environment"
```

---

## 🔐 Security Notes

### Never Commit Real Credentials
```bash
# Check .gitignore includes .env
cat .gitignore | grep "^\.env$"

# Verify .env not tracked
git status | grep ".env"
# Should see nothing (good!) or "Untracked" (fine)
```

### Check for Accidental Commits
```bash
# Search git history for leaked keys
git log --all --full-history -- .env

# If found, rotate those credentials immediately!
```

---

## 📋 Required Variables by Service

### Supabase
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Multiple projects:
SUPABASE_URL_2=https://second-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY_2=your-second-key
```

### Smartlead
```bash
SMARTLEAD_API_KEY=your-api-key
SMARTLEAD_WEBHOOK_SECRET=your-webhook-secret  # Optional
```

### Metabase
```bash
METABASE_URL=http://localhost:3000
METABASE_USERNAME=your-email@example.com
METABASE_PASSWORD=your-password
# OR
METABASE_API_KEY=mb_your_api_key
```

### BrightData
```bash
BRIGHTDATA_API_KEY=your-api-key
BRIGHTDATA_CUSTOMER_ID=your-customer-id
```

### Render
```bash
RENDER_API_KEY=your-api-key
```

---

## 🆘 Still Having Issues?

1. **Run the diagnostic:**
   ```bash
   python api-toolkit/test-env-loading.py
   ```

2. **Check the output carefully:**
   - Which .env file was loaded?
   - Which variables are set vs. not set?

3. **Common fixes:**
   - Create `.env` in project root if missing
   - Copy variables from `api-toolkit/.env` to project `.env`
   - Restart your Python process/terminal
   - Check for typos in variable names

4. **Test individual service:**
   ```python
   from api_toolkit.services.smartlead.api import SmartleadAPI
   api = SmartleadAPI()
   # This will show clear error if credentials missing
   ```

---

**Last Updated:** 2025-10-10
**Toolkit Version:** 2.1+
