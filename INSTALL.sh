#!/bin/bash
# Token-Efficient Coding Stack - Installation Script for macOS
# Installs AuZoom, Orchestrator, and configures Claude Code with MCP servers

set -e  # Exit on error

echo "=========================================="
echo "Token-Efficient Coding Stack - Installer"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This installer is designed for macOS only${NC}"
    exit 1
fi

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo -e "${RED}Error: Python $PYTHON_VERSION found, but 3.10+ required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if Claude Code is installed
echo "Checking Claude Code installation..."
if ! command -v claude &> /dev/null; then
    echo -e "${RED}Error: Claude Code CLI not found${NC}"
    echo "Please install Claude Code first: https://claude.com/claude-code"
    exit 1
fi
echo -e "${GREEN}✓ Claude Code found${NC}"

# Get installation directory (script location)
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $INSTALL_DIR"
echo ""

# Install AuZoom
echo "Installing AuZoom..."
cd "$INSTALL_DIR/auzoom"
python3 -m pip install -e . --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ AuZoom installed${NC}"
else
    echo -e "${RED}✗ AuZoom installation failed${NC}"
    exit 1
fi

# Verify AuZoom MCP server
if ! command -v auzoom-mcp &> /dev/null; then
    echo -e "${RED}Error: auzoom-mcp not found after installation${NC}"
    exit 1
fi
AUZOOM_MCP_PATH=$(which auzoom-mcp)
echo "  AuZoom MCP server: $AUZOOM_MCP_PATH"

# Install Orchestrator
echo ""
echo "Installing Orchestrator..."
cd "$INSTALL_DIR/orchestrator"
python3 -m pip install -e . --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Orchestrator installed${NC}"
else
    echo -e "${RED}✗ Orchestrator installation failed${NC}"
    exit 1
fi

# Get Python path for orchestrator MCP
PYTHON_PATH=$(which python3)
echo "  Orchestrator will use: $PYTHON_PATH"

# Configure MCP servers at user scope
echo ""
echo "Configuring MCP servers..."

# Check if MCP servers already configured
AUZOOM_CONFIGURED=$(claude mcp list 2>/dev/null | grep -c "auzoom" || echo "0")
ORCHESTRATOR_CONFIGURED=$(claude mcp list 2>/dev/null | grep -c "orchestrator" || echo "0")

# Add AuZoom MCP server
if [ "$AUZOOM_CONFIGURED" -eq "0" ]; then
    echo "Adding AuZoom MCP server..."
    claude mcp add --scope user auzoom "$AUZOOM_MCP_PATH"
    echo -e "${GREEN}✓ AuZoom MCP server added${NC}"
else
    echo -e "${YELLOW}⚠ AuZoom MCP server already configured, skipping${NC}"
fi

# Add Orchestrator MCP server
if [ "$ORCHESTRATOR_CONFIGURED" -eq "0" ]; then
    echo "Adding Orchestrator MCP server..."
    claude mcp add --scope user orchestrator "$PYTHON_PATH" -m orchestrator.mcp.server
    echo -e "${GREEN}✓ Orchestrator MCP server added${NC}"
else
    echo -e "${YELLOW}⚠ Orchestrator MCP server already configured, skipping${NC}"
fi

# Install skills
echo ""
echo "Installing Claude Code skills..."
SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$SKILLS_DIR"

# Copy skill files
cp "$INSTALL_DIR/.claude/skills/"*.md "$SKILLS_DIR/" 2>/dev/null || echo -e "${YELLOW}⚠ No skill files found, skipping${NC}"

if [ -f "$SKILLS_DIR/token-efficient-coding.md" ]; then
    echo -e "${GREEN}✓ Skills installed to $SKILLS_DIR${NC}"
else
    echo -e "${YELLOW}⚠ Skills installation incomplete${NC}"
fi

# Verify installation
echo ""
echo "Verifying installation..."
echo ""

# Test AuZoom MCP
echo "Testing AuZoom MCP server..."
if echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | "$AUZOOM_MCP_PATH" 2>/dev/null | grep -q "auzoom"; then
    echo -e "${GREEN}✓ AuZoom MCP server responds correctly${NC}"
else
    echo -e "${RED}✗ AuZoom MCP server test failed${NC}"
fi

# Test Orchestrator MCP
echo "Testing Orchestrator MCP server..."
if echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | "$PYTHON_PATH" -m orchestrator.mcp.server 2>/dev/null | grep -q "orchestrator"; then
    echo -e "${GREEN}✓ Orchestrator MCP server responds correctly${NC}"
else
    echo -e "${RED}✗ Orchestrator MCP server test failed${NC}"
fi

# Run tests
echo ""
echo "Running test suites..."
cd "$INSTALL_DIR/auzoom"
python3 -m pytest tests/ -q --tb=no 2>/dev/null
AUZOOM_TESTS=$?

cd "$INSTALL_DIR/orchestrator"
python3 -m pytest tests/ -q --tb=no 2>/dev/null
ORCHESTRATOR_TESTS=$?

if [ $AUZOOM_TESTS -eq 0 ] && [ $ORCHESTRATOR_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passing${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed (non-critical)${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart Claude Code to load MCP servers"
echo "2. Verify with: claude mcp list"
echo ""
echo "Usage:"
echo "  - Use auzoom_read for efficient file navigation"
echo "  - Use orchestrator_route for smart model selection"
echo "  - See skills in Claude Code: /skills"
echo ""
echo "Documentation:"
echo "  - README: $INSTALL_DIR/README.md"
echo "  - AuZoom docs: $INSTALL_DIR/auzoom/README.md"
echo "  - Orchestrator docs: $INSTALL_DIR/orchestrator/README.md"
echo ""
echo -e "${YELLOW}Please restart Claude Code now to activate MCP servers${NC}"
echo ""
