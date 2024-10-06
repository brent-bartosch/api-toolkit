#!/bin/bash

# Quick installation check for Claude Code
# Run this to determine if API Toolkit is already installed

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}API Toolkit Installation Check${NC}"
echo "================================"
echo ""

# Check for api-toolkit directory
if [ -d "api-toolkit" ]; then
    echo -e "${GREEN}✓ api-toolkit/ directory found${NC}"

    # Check if it's a symlink
    if [ -L "api-toolkit" ]; then
        TARGET=$(readlink api-toolkit)
        echo -e "  Type: Symbolic link → $TARGET"
    else
        echo -e "  Type: Copied files"
    fi

    # Check for marker file
    if [ -f "api-toolkit/.toolkit-installed" ]; then
        echo -e "${GREEN}✓ Installation marker found${NC}"
        echo ""
        echo "Installation details:"
        cat api-toolkit/.toolkit-installed | grep -E "TOOLKIT_VERSION|INSTALLATION_TYPE|Installation date" | sed 's/^/  /'
    fi

    echo ""
    echo -e "${GREEN}STATUS: Toolkit IS installed ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Use the toolkit directly (no installation needed)"
    echo "  2. Test connection: python api-toolkit/toolkit.py supabase test"
    echo "  3. Quick start: python -c 'from api_toolkit.services.supabase.api import SupabaseAPI; SupabaseAPI(\"smoothed\").quick_start()'"

elif [ -f ".toolkit-installed" ]; then
    echo -e "${GREEN}✓ Python package installation marker found${NC}"
    echo ""
    echo "Installation details:"
    cat .toolkit-installed | grep -E "TOOLKIT_VERSION|INSTALLATION_TYPE|Installation date" | sed 's/^/  /'

    echo ""
    echo -e "${GREEN}STATUS: Toolkit IS installed (as Python package) ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Use the toolkit directly (no installation needed)"
    echo "  2. Import: from api_toolkit.services.supabase.api import SupabaseAPI"

else
    echo -e "${RED}✗ No installation found${NC}"
    echo ""
    echo -e "${YELLOW}STATUS: Toolkit NOT installed${NC}"
    echo ""
    echo "To install:"
    echo "  /path/to/api-toolkit/install.sh"
fi

echo ""
