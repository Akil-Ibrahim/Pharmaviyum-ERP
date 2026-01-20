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
# CREATE BRANCHES (idempotent)
# -------------------
echo "🚀 Creating git branches if they don't exist..."
git fetch origin

for branch in prod dev demo; do
  if git rev-parse --verify "$branch" >/dev/null 2>&1; then
    echo "✅ Branch '$branch' already exists"
  else
    base="prod"
    [ "$branch" == "prod" ] && base=""
    git checkout -b "$branch" ${base:+$base}
    git commit --allow-empty -m "Initial commit on $branch"
    git push origin "$branch"
  fi
done

# Switch to dev for ongoing development
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
# GITHUB ACTIONS WORKFLOWS
# -------------------
echo "⚙️ Setting up GitHub Actions workflows..."
mkdir -p .github/workflows

# DEV WORKFLOW
[ ! -f ".github/workflows/dev.yml" ] && cat > .github/workflows/dev.yml <<EOL
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

# DEMO WORKFLOW
[ ! -f ".github/workflows/demo.yml" ] && cat > .github/workflows/demo.yml <<EOL
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

# PROD WORKFLOW
[ ! -f ".github/workflows/prod.yml" ] && cat > .github/workflows/prod.yml <<EOL
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
