#!/bin/bash
# ======================================================
# Pharmavium-CRM Master Setup Script (Best Practices)
# For already cloned repository
# ======================================================

# -------------------
# CONFIG
# -------------------
PROJECT_DIR="Pharmavium-CRM"

# -------------------
# MOVE TO PROJECT DIRECTORY
# -------------------
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Project directory '$PROJECT_DIR' not found! Clone the repository first."
  exit 1
fi

cd "$PROJECT_DIR" || exit

# -------------------
# CREATE BRANCHES (if they don't exist)
# -------------------
echo "🚀 Creating git branches if they don't exist..."

git fetch origin

# Prod branch
if git rev-parse --verify prod >/dev/null 2>&1; then
  echo "✅ Branch 'prod' already exists"
else
  git checkout -b prod
  git commit --allow-empty -m "Initial commit on prod"
  git push origin prod
fi

# Dev branch
if git rev-parse --verify dev >/dev/null 2>&1; then
  echo "✅ Branch 'dev' already exists"
else
  git checkout -b dev prod
  git push origin dev
fi

# Demo branch
if git rev-parse --verify demo >/dev/null 2>&1; then
  echo "✅ Branch 'demo' already exists"
else
  git checkout -b demo prod
  git push origin demo
fi

# Switch back to dev for ongoing development
git checkout dev

# -------------------
# CREATE PROJECT STRUCTURE
# -------------------
echo "📁 Creating project structure..."
if [ -f "./create_structure.sh" ]; then
  chmod +x create_structure.sh
  ./create_structure.sh
else
  echo "❌ create_structure.sh not found!"
fi

# -------------------
# CREATE .gitignore
# -------------------
echo "📝 Creating .gitignore..."
cat > .gitignore <<EOL
# Node
node_modules/
dist/
.vite/
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
*.pyo
.env
.venv/
*.sqlite3

# IDE
.vscode/
.idea/

# Logs
*.log
EOL

# -------------------
# CREATE GITHUB ACTIONS WORKFLOWS
# -------------------
echo "⚙️ Setting up GitHub Actions workflows..."
mkdir -p .github/workflows

# -------------------
# DEV WORKFLOW
# -------------------
if [ ! -f ".github/workflows/dev.yml" ]; then
cat > .github/workflows/dev.yml <<EOL
name: Dev Workflow
on:
  push:
    branches: [ dev ]
  pull_request:
    branches: [ dev ]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 20.10.0
      - run: cd frontend && npm install
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run test

  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16.6
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
          POSTGRES_DB: pharmavium
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.14.2
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests

  auto-pr-to-prod:
    needs: [frontend, backend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Pull Request to prod
        uses: peter-evans/create-pull-request@v5
        with:
          token: \${{ secrets.GITHUB_TOKEN }}
          commit-message: "Sync dev → prod (auto PR)"
          title: "Auto PR: dev → prod"
          body: "Automated pull request from dev to prod after passing tests."
          base: prod
          branch: dev
EOL
else
  echo "✅ dev.yml workflow already exists, skipping"
fi

# -------------------
# DEMO WORKFLOW
# -------------------
if [ ! -f ".github/workflows/demo.yml" ]; then
cat > .github/workflows/demo.yml <<EOL
name: Demo Workflow
on:
  pull_request:
    branches: [ demo ]

jobs:
  deploy-demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Demo (Placeholder)
        run: echo "Deploy demo environment here using secrets"
EOL
else
  echo "✅ demo.yml workflow already exists, skipping"
fi

# -------------------
# PROD WORKFLOW
# -------------------
if [ ! -f ".github/workflows/prod.yml" ]; then
cat > .github/workflows/prod.yml <<EOL
name: Production Deployment
on:
  push:
    branches: [ prod ]

jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Production (Placeholder)
        run: echo "Deploy production environment here using secrets"
EOL
else
  echo "✅ prod.yml workflow already exists, skipping"
fi

# -------------------
# COMMIT AND PUSH
# -------------------
echo "💾 Committing and pushing changes..."
git add .
git commit -m "chore: initial project structure and CI/CD workflows" || echo "Nothing to commit"
git push origin dev

# -------------------
# FINAL OUTPUT
# -------------------
echo "✅ Setup complete!"
echo "Branches: dev, prod, demo"
echo "Flow: dev → prod → demo"
echo "Workflows:"
echo "  - Dev: CI + auto PR to prod"
echo "  - Prod: deploy on push"
echo "  - Demo: inherits from prod (PR)"
