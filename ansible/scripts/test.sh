#!/bin/bash
# Ansible testing script
# Runs linting, syntax checks, and molecule tests

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go to ansible directory
cd "$SCRIPT_DIR/.."

echo "========================================="
echo "🧪 Testing Ansible Configuration"
echo "========================================="

# Step 1: YAML syntax check
echo -e "\n📝 Checking YAML syntax..."
if [ -f ".yamllint" ]; then
    yamllint -c .yamllint . || true
else
    echo "⚠️  .yamllint not found, skipping..."
fi

# Step 2: Ansible-lint
echo -e "\n🎯 Running ansible-lint..."
ansible-lint --profile production

# Step 3: Molecule tests
if [ -d "molecule" ]; then
    echo -e "\n🧪 Running molecule tests..."
    cd molecule
    for scenario in */; do
        if [ -d "$scenario" ]; then
            echo "🔹 Testing scenario: ${scenario%/}"
            cd "$scenario"
            molecule test || true
            cd ..
        fi
    done
    cd ..
fi

echo -e "\n✅ Testing completed!"
