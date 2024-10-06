#!/bin/bash

# API Toolkit Installation Script
# Installs the toolkit into any project directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the source directory (where this script lives)
SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}API Toolkit Installer${NC}"
echo "========================"
echo ""

# Check if we're in the source directory
if [ "$PWD" == "$SOURCE_DIR" ]; then
    echo -e "${RED}Error: Don't run this from the api-toolkit source directory!${NC}"
    echo "Usage: Run this from your project directory:"
    echo "  cd /path/to/your/project"
    echo "  $SOURCE_DIR/install.sh"
    exit 1
fi

# Get installation type
echo "How would you like to install the API Toolkit?"
echo "1) Symbolic link (recommended - updates automatically)"
echo "2) Copy files (standalone - won't receive updates)"
echo "3) Python package (install as module)"
read -p "Choose [1-3]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Creating symbolic link...${NC}"
        
        # Create symlink
        if [ -e "api-toolkit" ]; then
            echo -e "${YELLOW}api-toolkit already exists. Overwrite? (y/N)${NC}"
            read -p "> " confirm
            if [ "$confirm" != "y" ]; then
                echo "Installation cancelled."
                exit 0
            fi
            rm -rf api-toolkit
        fi
        
        ln -s "$SOURCE_DIR" api-toolkit
        echo -e "${GREEN}✓ Symbolic link created${NC}"

        # Create installation marker
        cat > api-toolkit/.toolkit-installed << EOF
# API Toolkit Installation Marker
# This file indicates the toolkit is installed in this project.
# Created by: install.sh
# Installation date: $(date +%Y-%m-%d)

TOOLKIT_VERSION=2.0
INSTALLATION_TYPE=symlink
SOURCE_PATH=$SOURCE_DIR
PROJECT_PATH=$PWD

# DO NOT DELETE THIS FILE
# Claude Code uses this to detect existing installations
EOF

        # Check for .env
        if [ ! -f "api-toolkit/.env" ] && [ ! -f ".env" ]; then
            echo -e "\n${YELLOW}Creating .env file...${NC}"
            cp "$SOURCE_DIR/.env.example" .env
            echo -e "${GREEN}✓ Created .env file - please configure your API keys${NC}"
        elif [ -f ".env" ]; then
            echo -e "${GREEN}✓ Using existing .env file${NC}"
        fi
        ;;
        
    2)
        echo -e "\n${YELLOW}Copying files...${NC}"
        
        # Copy toolkit
        if [ -e "api-toolkit" ]; then
            echo -e "${YELLOW}api-toolkit already exists. Overwrite? (y/N)${NC}"
            read -p "> " confirm
            if [ "$confirm" != "y" ]; then
                echo "Installation cancelled."
                exit 0
            fi
            rm -rf api-toolkit
        fi
        
        cp -r "$SOURCE_DIR" api-toolkit

        # Remove git history and unnecessary files
        rm -rf api-toolkit/.git
        rm -rf api-toolkit/.gitignore
        rm -f api-toolkit/install.sh

        echo -e "${GREEN}✓ Files copied${NC}"

        # Create installation marker
        cat > api-toolkit/.toolkit-installed << EOF
# API Toolkit Installation Marker
# This file indicates the toolkit is installed in this project.
# Created by: install.sh
# Installation date: $(date +%Y-%m-%d)

TOOLKIT_VERSION=2.0
INSTALLATION_TYPE=copy
SOURCE_PATH=$SOURCE_DIR
PROJECT_PATH=$PWD

# DO NOT DELETE THIS FILE
# Claude Code uses this to detect existing installations
EOF

        # Setup .env
        if [ ! -f "api-toolkit/.env" ]; then
            echo -e "\n${YELLOW}Creating .env file...${NC}"
            cp api-toolkit/.env.example api-toolkit/.env
            echo -e "${GREEN}✓ Created .env file - please configure your API keys${NC}"
        fi
        ;;
        
    3)
        echo -e "\n${YELLOW}Installing as Python package...${NC}"
        
        # Create __init__.py files if they don't exist
        touch "$SOURCE_DIR/__init__.py" 2>/dev/null || true
        
        # Install with pip in editable mode
        pip install -e "$SOURCE_DIR"

        echo -e "${GREEN}✓ Installed as Python package${NC}"
        echo ""
        echo "You can now import directly:"
        echo "  from api_toolkit.services.supabase.api import SupabaseAPI"

        # Create installation marker in current directory
        cat > .toolkit-installed << EOF
# API Toolkit Installation Marker
# This file indicates the toolkit is installed in this project.
# Created by: install.sh
# Installation date: $(date +%Y-%m-%d)

TOOLKIT_VERSION=2.0
INSTALLATION_TYPE=python_package
SOURCE_PATH=$SOURCE_DIR
PROJECT_PATH=$PWD

# DO NOT DELETE THIS FILE
# Claude Code uses this to detect existing installations
EOF

        # Setup .env
        if [ ! -f ".env" ]; then
            echo -e "\n${YELLOW}Creating .env file...${NC}"
            cp "$SOURCE_DIR/.env.example" .env
            echo -e "${GREEN}✓ Created .env file - please configure your API keys${NC}"
        fi
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Install Python dependencies
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
pip install -q -r "$SOURCE_DIR/requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Test the installation
echo -e "\n${YELLOW}Testing installation...${NC}"

if [ "$choice" == "3" ]; then
    python -c "from api_toolkit.services.supabase.api import SupabaseAPI; print('✓ Import successful')" 2>/dev/null || {
        echo -e "${RED}✗ Import failed${NC}"
        exit 1
    }
else
    python api-toolkit/toolkit.py list >/dev/null 2>&1 && {
        echo -e "${GREEN}✓ Toolkit is working${NC}"
    } || {
        echo -e "${RED}✗ Toolkit test failed${NC}"
        echo "  Please check your Python environment"
        exit 1
    }
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""

# Ask about project configuration
echo -e "${YELLOW}Would you like to configure which services this project will use?${NC}"
echo "This creates a .api-toolkit-config.md file that Claude Code will read"
echo "to know which services are active for this specific project."
echo ""
read -p "Create project configuration now? (Y/n): " config_choice
config_choice=${config_choice:-y}

if [ "$config_choice" == "y" ] || [ "$config_choice" == "Y" ]; then
    echo ""
    "$SOURCE_DIR/init-project.sh"
else
    echo ""
    echo "You can create the project configuration later by running:"
    echo "  $SOURCE_DIR/init-project.sh"
fi

echo ""
echo "Next steps:"
echo "1. Configure your API keys in .env"
echo "2. Test a connection:"

if [ "$choice" == "3" ]; then
    echo "   python -c \"from api_toolkit.services.supabase.api import SupabaseAPI; api = SupabaseAPI('project1'); print(api.test_connection())\""
else
    echo "   python api-toolkit/toolkit.py supabase test"
fi

echo ""
echo "For more info: cat api-toolkit/README.md"