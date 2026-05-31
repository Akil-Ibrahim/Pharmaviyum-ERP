#!/bin/bash

echo "=== Force Fix Git Commit Issue ==="

# 1. Completely disable GPG signing (multiple methods to ensure it works)
git config --global commit.gpgsign false    # Disable globally
git config --local commit.gpgsign false 2>/dev/null   # Disable for this repo only
unset GPG_TTY                              # Clear GPG terminal variable
unset GPG_AGENT_INFO                       # Clear GPG agent variable

# 2. Set user name and email (REPLACE with your GitHub noreply email!)
git config --global user.name "Akil Ibrahim"
git config --global user.email "Akil-Ibrahim@users.noreply.github.com"

# 3. Verify current settings
echo ""
echo "=== VERIFICATION ==="
echo "Name: $(git config --global user.name)"
echo "Email: $(git config --global user.email)"
echo "GPG Signing: $(git config --global commit.gpgsign)"
echo ""

# 4. Commit without GPG signature
echo "=== COMMITTING ==="
git add .                                 # Stage all changes
git commit -m "refactoring" --no-gpg-sign # Commit without signing

# 5. Push to remote repository
echo ""
echo "=== PUSHING ==="
git push

echo ""
echo "=== DONE ==="
