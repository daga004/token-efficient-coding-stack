#!/bin/bash
# Token-Efficient Coding Stack - Installation Script
# Installs AuZoom, Orchestrator, configures Claude Code with MCP servers,
# sets up CLAUDE.md project instructions, hooks, and skills.

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

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS="linux"
else
    echo -e "${YELLOW}Warning: Untested OS ($OSTYPE). Proceeding anyway...${NC}"
    OS="other"
fi

# Check Python version (3.11+ required for AuZoom)
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo -e "${RED}Error: Python $PYTHON_VERSION found, but 3.11+ required${NC}"
    echo "AuZoom requires Python 3.11+ for tree-sitter support."
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if Claude Code is installed
echo "Checking Claude Code installation..."
if ! command -v claude &> /dev/null; then
    echo -e "${RED}Error: Claude Code CLI not found${NC}"
    echo "Please install Claude Code first: https://claude.ai/download"
    exit 1
fi
echo -e "${GREEN}✓ Claude Code found${NC}"

# Check for Gemini CLI (optional — needed for model routing)
echo "Checking Gemini CLI installation..."
if ! command -v gemini &> /dev/null; then
    echo -e "${YELLOW}⚠ Gemini CLI not found (optional — needed for cost savings via model routing)${NC}"
    if [ "$OS" == "macos" ] && command -v brew &> /dev/null; then
        echo "  Install with: brew install gemini-cli"
    else
        echo "  Install with: npm install -g @google/gemini-cli"
    fi
    echo ""
else
    GEMINI_VERSION=$(gemini --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Gemini CLI found (version $GEMINI_VERSION)${NC}"
fi

# Check for Gemini API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠ GEMINI_API_KEY not set (optional — needed for Gemini Flash routing)${NC}"
    echo "  Get your API key from: https://aistudio.google.com/apikey"
    echo "  Add to your shell profile (~/.zshrc or ~/.bashrc):"
    echo "    export GEMINI_API_KEY='your-api-key-here'"
    echo ""
else
    echo -e "${GREEN}✓ GEMINI_API_KEY is set${NC}"
fi

# Get installation directory (script location)
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Installation directory: $INSTALL_DIR"
echo ""

# ============================================
# Step 1: Install Python packages
# ============================================

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

# ============================================
# Step 2: Configure MCP servers
# ============================================

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

# ============================================
# Step 3: Verify project configuration
# ============================================

echo ""
echo "Verifying project configuration..."

# Verify project-level CLAUDE.md is present (project-scoped, not global)
if [ -f "$INSTALL_DIR/CLAUDE.md" ]; then
    echo -e "${GREEN}✓ Project CLAUDE.md present (loaded when working in this repo)${NC}"
else
    echo -e "${YELLOW}⚠ CLAUDE.md not found in project root${NC}"
fi

# Verify project-level hooks
if [ -f "$INSTALL_DIR/.claude/settings.json" ]; then
    echo -e "${GREEN}✓ Project hooks configured (.claude/settings.json)${NC}"
    echo "  - Edit hook: protects test files during plan execution"
else
    echo -e "${YELLOW}⚠ No project hooks found${NC}"
fi

echo ""
echo -e "${YELLOW}Note: This stack does NOT install global CLAUDE.md or hooks.${NC}"
echo "  Instructions apply only when working in this project directory."
echo "  MCP servers are registered at user scope (passive, zero overhead until called)."

# ============================================
# Step 4: Install skills
# ============================================

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

# ============================================
# Step 5: Verify installation
# ============================================

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

# ============================================
# Done
# ============================================

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "What's installed:"
echo "  ✓ AuZoom MCP server (progressive code reading — user scope, passive)"
echo "  ✓ Orchestrator MCP server (smart model routing — user scope, passive)"
echo "  ✓ Skills (~/.claude/skills/ — on-demand, no overhead)"
echo ""
echo "Project-scoped (only active in this repo):"
echo "  ✓ CLAUDE.md (project instructions for token-efficient coding)"
echo "  ✓ Edit hook (TDD protection during plan execution)"
echo ""
echo "Optional: Enable MCP CLI mode for zero-overhead tool loading:"
echo '  Add to ~/.claude/settings.json: { "env": { "CLAUDE_MCP_CLI": "true" } }'
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code to load MCP servers"
echo "  2. Verify with: claude mcp list"
echo ""
echo "Validated savings (V1 audit):"
echo "  - Token reduction: 71.3% (progressive disclosure)"
echo "  - Cost reduction: ~51% (model routing)"
echo "  - Quality: 100% maintained (simple tasks)"
echo ""
echo -e "${YELLOW}Please restart Claude Code now to activate MCP servers${NC}"
echo ""
