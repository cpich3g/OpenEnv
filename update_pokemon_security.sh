#!/bin/bash
# Security Update Script for Pokemon Environment
# This script updates all dependencies to secure versions
#
# Usage:
#   ./update_pokemon_security.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "================================================================================"
echo -e "${BLUE}Pokemon Environment Security Update Script${NC}"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Check current dependency versions"
echo "  2. Update to secure versions"
echo "  3. Verify no vulnerabilities remain"
echo ""

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    echo -e "${YELLOW}Installing pip-audit...${NC}"
    pip install pip-audit
fi

# Step 1: Check current vulnerabilities
echo ""
echo -e "${BLUE}Step 1: Checking current vulnerabilities...${NC}"
echo "--------------------------------------------------------------------------------"

VULN_COUNT=$(pip-audit --desc 2>&1 | grep -c "│" | grep -v "No known" || echo "0")

if pip-audit --desc 2>&1 | grep -q "No known vulnerabilities"; then
    echo -e "${GREEN}✅ No vulnerabilities found! Environment is already secure.${NC}"
    exit 0
else
    echo -e "${YELLOW}Found vulnerabilities in current environment${NC}"
    echo ""
    echo "Vulnerable packages:"
    pip-audit --desc 2>&1 | grep "│" | head -n 20 || true
    echo ""
fi

# Step 2: Backup current requirements
echo ""
echo -e "${BLUE}Step 2: Backing up current requirements...${NC}"
echo "--------------------------------------------------------------------------------"

if [ -f "requirements-backup.txt" ]; then
    echo -e "${YELLOW}Backup already exists: requirements-backup.txt${NC}"
else
    pip freeze > requirements-backup.txt
    echo -e "${GREEN}✅ Created backup: requirements-backup.txt${NC}"
fi

# Step 3: Update dependencies
echo ""
echo -e "${BLUE}Step 3: Updating dependencies to secure versions...${NC}"
echo "--------------------------------------------------------------------------------"

echo "Updating core security packages..."

# Update build tools first
echo -n "  Updating pip... "
pip install --upgrade "pip>=25.3" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating setuptools... "
pip install --upgrade "setuptools>=78.1.1" --quiet
echo -e "${GREEN}✅${NC}"

# Update critical dependencies
echo -n "  Updating certifi... "
pip install --upgrade "certifi>=2024.7.4" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating cryptography... "
pip install --upgrade "cryptography>=43.0.1" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating jinja2... "
pip install --upgrade "jinja2>=3.1.6" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating requests... "
pip install --upgrade "requests>=2.32.4" --quiet
echo -e "${GREEN}✅${NC}"

# Update medium priority dependencies
echo -n "  Updating urllib3... "
pip install --upgrade "urllib3>=2.5.0" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating twisted... "
pip install --upgrade "twisted>=24.7.0rc1" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating idna... "
pip install --upgrade "idna>=3.7" --quiet
echo -e "${GREEN}✅${NC}"

echo -n "  Updating configobj... "
pip install --upgrade "configobj>=5.0.9" --quiet 2>/dev/null || echo -e "${YELLOW}⚠️  (may not be installed)${NC}"

echo ""
echo -e "${GREEN}✅ All updates completed${NC}"

# Step 4: Verify updates
echo ""
echo -e "${BLUE}Step 4: Verifying updates...${NC}"
echo "--------------------------------------------------------------------------------"

echo "Checking updated versions:"
pip list | grep -E "pip|setuptools|certifi|cryptography|jinja2|requests|urllib3|twisted|idna|configobj" || true

# Step 5: Run vulnerability scan again
echo ""
echo -e "${BLUE}Step 5: Running final vulnerability scan...${NC}"
echo "--------------------------------------------------------------------------------"

if pip-audit --desc 2>&1 | grep -q "No known vulnerabilities"; then
    echo -e "${GREEN}✅ SUCCESS! No vulnerabilities found.${NC}"
    echo ""
    echo "Your Pokemon environment is now secure!"
    
    # Save updated requirements
    pip freeze > requirements-updated.txt
    echo -e "Updated requirements saved to: ${GREEN}requirements-updated.txt${NC}"
    
else
    echo -e "${YELLOW}⚠️  Some vulnerabilities may still exist${NC}"
    echo ""
    echo "Remaining issues:"
    pip-audit --desc 2>&1 | grep "│" | head -n 10 || true
    echo ""
    echo -e "${YELLOW}These may be in dependencies not directly used by Pokemon environment${NC}"
    echo "Review the output and determine if additional updates are needed."
fi

# Step 6: Summary
echo ""
echo "================================================================================"
echo -e "${BLUE}UPDATE SUMMARY${NC}"
echo "================================================================================"
echo ""
echo "Completed actions:"
echo "  ✅ Backed up original requirements"
echo "  ✅ Updated pip and setuptools"
echo "  ✅ Updated all critical dependencies"
echo "  ✅ Updated medium priority dependencies"
echo "  ✅ Ran vulnerability scan"
echo ""
echo "Files created:"
echo "  - requirements-backup.txt (original state)"
echo "  - requirements-updated.txt (new state)"
echo ""
echo "Next steps:"
echo "  1. Test your Pokemon environment"
echo "  2. Run: python comprehensive_pokemon_test.py --all"
echo "  3. If Docker testing: ./comprehensive_docker_test.sh"
echo "  4. Review SECURITY_ADVISORY_POKEMON_ENV.md for details"
echo ""
echo "To rollback if needed:"
echo "  pip install -r requirements-backup.txt"
echo ""
echo "================================================================================"
