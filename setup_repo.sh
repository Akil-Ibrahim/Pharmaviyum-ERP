#!/bin/bash
# ======================================================
# Pharmavium-CRM Full Setup Script (Best Practices)
# For already cloned repository
# ======================================================

# -------------------
# CONFIG
# -------------------
PROJECT_DIR="Pharmavium-CRM"

# -------------------
# MOVE TO PROJECT
# -------------------
cd "$PROJECT_DIR" || { echo "Project directory not found!"; exit 1; }

# -------------------
# CREATE BRANCHES
# -------------------
git checkout -b prod
git commit --allow-empty -m "Initial commit on prod"
git push origin prod

git checkout -b dev prod
git push origin dev

git checkout -b demo prod
git push origin demo

git checkout dev

# -------------------
# CREATE PROJECT STRUCTURE
# -------------------
echo "Creating project structure..."
chmod +x create_structure.sh
./create_structure.sh

# -------------------
# CREATE .gitignore
# -------------------
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
mkdir -p .github/workflows

# Dev workflow (frontend + backend + auto PR to prod)
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

# Demo workflow (PR prod -> demo)
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

# Prod workflow (push prod -> deploy prod)
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

# -------------------
# COMMIT AND PUSH
# -------------------
git add .
git commit -m "Add full project structure, .gitignore, and workflows with Node 20.10.0, Python 3.14.2, Postgres 16.6"
git push origin dev

echo "✅ Setup complete!"
echo "Branches: prod, dev, demo"
echo "Workflows: Dev (auto PR), Demo (PR), Prod (push prod)"
