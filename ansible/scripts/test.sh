#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]})" && pwd)"
cd "$SCRIPT_DIR/.."

echo "== YAML lint =="
yamllint -c .yamllint .

echo "== Ansible lint =="
ansible-lint --profile production

echo "== Ansible syntax check =="
ansible-playbook -i inventory/production/hosts.yml playbooks/deploy.yml --syntax-check
ansible-playbook -i inventory/production/hosts.yml playbooks/backup.yml --syntax-check
ansible-playbook -i inventory/production/hosts.yml playbooks/rollback.yml --syntax-check

echo "== Molecule =="
molecule test

echo "All Ansible checks passed."
