#!/bin/bash
set -e

# Token-Efficient Coding Stack - Quick Installer
# This script can be run directly via curl:
# curl -fsSL https://raw.githubusercontent.com/daga004/token-efficient-coding-stack/main/quick-install.sh | bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Token-Efficient Coding Stack - Quick Installer             ║"
echo "║                                                                 ║"
echo "║     Cut Claude Code costs ~51% with intelligent model           ║"
echo "║     routing + progressive code reading (V1 validated)          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check for git
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    echo "Please install git first: https://git-scm.com/downloads"
    exit 1
fi

# Check for Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Error: Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Check for Claude Code CLI
if ! command -v claude &> /dev/null; then
    echo "❌ Error: Claude Code CLI is not installed"
    echo "Please install Claude Code first: https://claude.ai/download"
    exit 1
fi

echo "✅ Claude Code CLI found"

# Check for Gemini CLI
if ! command -v gemini &> /dev/null; then
    echo "⚠️  Gemini CLI not found"
    echo "The INSTALL.sh script will attempt to install it automatically"
    echo "Or install manually: npm install -g @google/gemini-cli"
    echo ""
else
    echo "✅ Gemini CLI found"
fi
echo ""

# Determine installation directory
INSTALL_DIR="${HOME}/token-efficient-coding-stack"

# Check if directory already exists
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory $INSTALL_DIR already exists"
    read -p "Do you want to remove it and reinstall? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing installation..."
        rm -rf "$INSTALL_DIR"
    else
        echo "Installation cancelled"
        exit 0
    fi
fi

# Clone repository
echo "📦 Cloning repository..."
git clone https://github.com/daga004/token-efficient-coding-stack.git "$INSTALL_DIR"

if [ $? -ne 0 ]; then
    echo "❌ Failed to clone repository"
    exit 1
fi

echo "✅ Repository cloned to $INSTALL_DIR"
echo ""

# Change to repository directory
cd "$INSTALL_DIR"

# Make installation script executable
chmod +x INSTALL.sh

# Run the full installation script
echo "🚀 Running full installation..."
echo ""
./INSTALL.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                 ✅ Installation Complete!                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "The Token-Efficient Coding Stack is now installed."
    echo ""
    echo "📖 Documentation:"
    echo "   - README: $INSTALL_DIR/README.md"
    echo "   - Usage examples: $INSTALL_DIR/USAGE-EXAMPLES.md"
    echo "   - Workflows: $INSTALL_DIR/.claude/workflows/"
    echo ""
    echo "🎯 Quick Start:"
    echo "   1. Restart Claude Code"
    echo "   2. Use auzoom_read() for file operations"
    echo "   3. Use orchestrator_route() for task routing"
    echo "   4. See /skills token-efficient-coding for guidance"
    echo ""
    echo "💡 Expected savings (V1 audit-validated):"
    echo "   - Token reduction: 71.3% (progressive disclosure)"
    echo "   - Cost reduction: ~51% (model routing)"
    echo "   - Quality: 100% maintained (simple tasks)"
    echo ""
else
    echo ""
    echo "❌ Installation failed"
    echo "Please check the error messages above and try again"
    echo ""
    echo "For help, please visit:"
    echo "https://github.com/daga004/token-efficient-coding-stack/issues"
    exit 1
fi
