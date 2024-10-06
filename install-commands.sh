#!/bin/bash
# Install API Toolkit slash commands in current project

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="${1:-.}"  # Use provided path or current directory
TOOLKIT_COMMANDS="/path/to/api-toolkit/.claude/commands"

echo -e "${BLUE}Installing API Toolkit slash commands...${NC}"

# Create commands directory
mkdir -p "$PROJECT_DIR/.claude/commands"

# List of commands to install (excluding documentation files)
COMMANDS=("api-toolkit" "supabase" "smartlead" "metabase" "render" "brightdata")

# Copy each command
for cmd in "${COMMANDS[@]}"; do
    if [ -f "$TOOLKIT_COMMANDS/${cmd}.md" ]; then
        cp "$TOOLKIT_COMMANDS/${cmd}.md" "$PROJECT_DIR/.claude/commands/"
        echo -e "${GREEN}✅${NC} Installed /${cmd}"
    else
        echo "⚠️  Warning: ${cmd}.md not found"
    fi
done

echo ""
echo -e "${GREEN}✅ All API toolkit commands installed in${NC} $PROJECT_DIR"
echo ""
echo "Available commands:"
echo "  /api-toolkit  - Check installation, get overview"
echo "  /supabase     - Database operations"
echo "  /smartlead    - Email campaigns"
echo "  /metabase     - Analytics & BI"
echo "  /render       - Cloud deployments"
echo "  /brightdata   - Web scraping"
echo ""
echo "Try: Open Claude Code and type /supabase"
