# Installing Slash Commands in Your Projects

## Quick Install

To use these slash commands in other projects:

### Option 1: Copy Individual Commands (Recommended)

```bash
# In your project directory
mkdir -p .claude/commands

# Copy the commands you need
cp /path/to/api-toolkit/.claude/commands/api-toolkit.md .claude/commands/
cp /path/to/api-toolkit/.claude/commands/supabase.md .claude/commands/
cp /path/to/api-toolkit/.claude/commands/smartlead.md .claude/commands/

# Now /api-toolkit, /supabase, /smartlead work in this project!
```

### Option 2: Copy All Commands

```bash
# In your project directory
mkdir -p .claude/commands

# Copy all API toolkit commands
cp /path/to/api-toolkit/.claude/commands/*.md .claude/commands/

# Skip the documentation files
rm .claude/commands/README.md .claude/commands/INSTALLATION.md
```

### Option 3: Symlink (Advanced - Auto-Updates)

```bash
# In your project directory
# WARNING: This links ALL commands, they'll update when api-toolkit updates
ln -s /path/to/api-toolkit/.claude/commands .claude/commands
```

## Verification

After installing, verify the commands are available:

```bash
# List commands in your project
ls .claude/commands/

# Should see:
# api-toolkit.md
# supabase.md
# smartlead.md
# metabase.md
# render.md
# brightdata.md
```

## Usage

In Claude Code:

```
/api-toolkit    # Check installation, get overview
/supabase       # Load Supabase context
/smartlead      # Load Smartlead context
/metabase       # Load Metabase context
/render         # Load Render context
/brightdata     # Load BrightData context
```

## Per-Project Customization

After copying, you can customize commands for your project:

```bash
# Edit to add project-specific patterns
nano .claude/commands/supabase.md

# Add your common queries:
## Your Common Queries

**Get active customers:**
```python
api = SupabaseAPI('project2')
customers = api.query('customers', filters={'status': 'eq.active'})
```
\`\`\`
```

## Updating Commands

If api-toolkit slash commands get updated:

### If you copied files:
```bash
# Re-copy the updated command
cp /path/to/api-toolkit/.claude/commands/supabase.md .claude/commands/
```

### If you symlinked:
Already updated automatically!

## Project Template

Create a script to setup commands in new projects:

```bash
#!/bin/bash
# setup-api-toolkit-commands.sh

PROJECT_DIR=$1
TOOLKIT_COMMANDS="/path/to/api-toolkit/.claude/commands"

if [ -z "$PROJECT_DIR" ]; then
    echo "Usage: ./setup-api-toolkit-commands.sh /path/to/project"
    exit 1
fi

mkdir -p "$PROJECT_DIR/.claude/commands"

# Copy commands (exclude docs)
for cmd in api-toolkit supabase smartlead metabase render brightdata; do
    cp "$TOOLKIT_COMMANDS/${cmd}.md" "$PROJECT_DIR/.claude/commands/"
    echo "✅ Installed /${cmd}"
done

echo "✅ All API toolkit commands installed in $PROJECT_DIR"
```

Usage:
```bash
chmod +x setup-api-toolkit-commands.sh
./setup-api-toolkit-commands.sh ~/projects/my-new-project
```

## Troubleshooting

### Commands not showing up

**Check directory structure:**
```bash
ls -la .claude/commands/
```

Should see `.md` files, not a directory of commands.

**Restart Claude Code:**
Sometimes needed for new commands to be recognized.

### "Command not found" error

**Verify file exists:**
```bash
cat .claude/commands/supabase.md
```

**Check file has description:**
```bash
head -n 5 .claude/commands/supabase.md
```

Should see:
```markdown
---
description: Load Supabase API toolkit context
---
```

### Commands work but don't load context

**Check file paths in command:**
Edit `.claude/commands/supabase.md` and verify paths point to `api-toolkit/` in your project.

If toolkit is in different location, update paths:
```markdown
- `path/to/api-toolkit/services/supabase/api.py`
```

## Complete Example

Setting up a new project:

```bash
# 1. Create project
mkdir ~/projects/my-crm
cd ~/projects/my-crm

# 2. Install api-toolkit
/path/to/api-toolkit/install.sh
# Choose: 1 (symlink)

# 3. Setup .env
cp api-toolkit/.env.example .env
nano .env  # Add your API keys

# 4. Install slash commands
mkdir -p .claude/commands
cp /path/to/api-toolkit/.claude/commands/api-toolkit.md .claude/commands/
cp /path/to/api-toolkit/.claude/commands/supabase.md .claude/commands/

# 5. Test
# Open Claude Code, type:
# /api-toolkit
```

## See Also

- `SLASH_COMMANDS.md` - Complete guide to using slash commands
- `README.md` - Command structure and customization
- `/path/to/api-toolkit/CLAUDE.md` - General Claude Code guidance
