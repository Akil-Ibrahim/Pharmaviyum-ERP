#!/bin/bash
# Setup pre-commit hooks for Ansible development

set -e

echo "🔧 Setting up pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Install hooks
cd "$(dirname "$0")/.."
pre-commit install

echo "✅ Pre-commit hooks installed!"
echo "   Hooks will run automatically on 'git commit'"
echo ""
echo "To run manually: pre-commit run --all-files"
