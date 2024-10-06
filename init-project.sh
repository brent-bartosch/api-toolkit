#!/bin/bash

# API Toolkit Project Configuration Initializer
# Creates a project-specific configuration file

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOOLKIT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}API Toolkit Project Configuration${NC}"
echo "===================================="
echo ""

# Check if api-toolkit is installed in current project
if [ ! -e "api-toolkit" ] && [ ! -f ".toolkit-installed" ]; then
    echo -e "${YELLOW}Warning: API Toolkit doesn't appear to be installed.${NC}"
    echo "Run the installer first: $TOOLKIT_DIR/install.sh"
    echo ""
    read -p "Continue anyway? (y/N): " continue
    if [ "$continue" != "y" ]; then
        exit 0
    fi
fi

# Get project name
read -p "Project name: " PROJECT_NAME
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME=$(basename "$PWD")
fi

# Get project description
read -p "Brief project description: " PROJECT_DESC

echo ""
echo "Select which services this project will use:"
echo "(You can always update this later in .api-toolkit-config.md)"
echo ""

# Function to ask about service
ask_service() {
    local service=$1
    local default=${2:-n}
    read -p "Use $service? (y/N): " response
    response=${response:-$default}
    echo $response
}

# Ask about each service
USE_SUPABASE=$(ask_service "Supabase")
if [ "$USE_SUPABASE" = "y" ]; then
    echo "  Which Supabase project(s)? (comma-separated: smoothed,blingsting,scraping)"
    read -p "  Projects: " SUPABASE_PROJECTS
fi

USE_METABASE=$(ask_service "Metabase")
USE_SMARTLEAD=$(ask_service "Smartlead")
USE_RENDER=$(ask_service "Render")
USE_BRIGHTDATA=$(ask_service "BrightData")
USE_CONTEXT7=$(ask_service "Context7")
USE_KLAVIYO=$(ask_service "Klaviyo")
USE_SHOPIFY=$(ask_service "Shopify")

# Create config file
CONFIG_FILE=".api-toolkit-config.md"

echo ""
echo -e "${YELLOW}Creating $CONFIG_FILE...${NC}"

# Start with template
cp "$TOOLKIT_DIR/.api-toolkit-config.template.md" "$CONFIG_FILE"

# Update basic info
sed -i '' "s/\[PROJECT_NAME\]/$PROJECT_NAME/g" "$CONFIG_FILE"
sed -i '' "s/\[DATE\]/$(date +%Y-%m-%d)/g" "$CONFIG_FILE"

# Update installation status
if [ -L "api-toolkit" ]; then
    sed -i '' "s/Installation Type\]: \[symlink.*/Installation Type]: symlink/g" "$CONFIG_FILE"
elif [ -d "api-toolkit" ]; then
    sed -i '' "s/Installation Type\]: \[symlink.*/Installation Type]: copy/g" "$CONFIG_FILE"
elif [ -f ".toolkit-installed" ]; then
    sed -i '' "s/Installation Type\]: \[symlink.*/Installation Type]: python_package/g" "$CONFIG_FILE"
fi

# Update service statuses
update_service_status() {
    local service=$1
    local use=$2
    local status="⚪ Not Configured"

    if [ "$use" = "y" ]; then
        status="🟡 Configured"
    fi

    # Find and replace the status line for this service
    sed -i '' "/^### $service$/,/^### / s/Status\*\*: ⚪ Not Configured.*/Status**: $status/g" "$CONFIG_FILE"
}

update_service_status "Supabase" "$USE_SUPABASE"
update_service_status "Metabase" "$USE_METABASE"
update_service_status "Smartlead" "$USE_SMARTLEAD"
update_service_status "Render" "$USE_RENDER"
update_service_status "BrightData" "$USE_BRIGHTDATA"
update_service_status "Context7" "$USE_CONTEXT7"
update_service_status "Klaviyo" "$USE_KLAVIYO"
update_service_status "Shopify" "$USE_SHOPIFY"

# Update project description
if [ -n "$PROJECT_DESC" ]; then
    sed -i '' "s/Brief description of the project's purpose and main functionality./$PROJECT_DESC/g" "$CONFIG_FILE"
fi

# Update Supabase projects if specified
if [ -n "$SUPABASE_PROJECTS" ]; then
    sed -i '' "s/\*\*Project(s) Used\*\*: \[smoothed.*/\*\*Project(s) Used**: $SUPABASE_PROJECTS/g" "$CONFIG_FILE"
fi

echo -e "${GREEN}✓ Configuration file created: $CONFIG_FILE${NC}"
echo ""
echo "Next steps:"
echo "1. Review and customize $CONFIG_FILE"
echo "2. Add your environment variables to .env"
echo "3. Document your common patterns in the config file"
echo ""
echo "To activate a service later:"
echo "  - Edit $CONFIG_FILE"
echo "  - Change status from ⚪ Not Configured to 🟡 Configured"
echo "  - Fill in the service-specific details"
echo "  - Update to ✅ Active once tested and working"
echo ""
echo -e "${BLUE}Pro tip:${NC} Keep this file updated as you work. Claude Code will read it"
echo "at the start of each conversation to know what's available!"
