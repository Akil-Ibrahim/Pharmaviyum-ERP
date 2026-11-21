#!/usr/bin/env bash
# Fail-closed Ansible validation entry point.
# Run from any directory; all paths are resolved relative to this script.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ANSIBLE_DIR"

echo "========================================="
echo "Ansible validation"
echo "========================================="

echo
echo "[1/5] YAML lint"
yamllint -c .yamllint .

echo
echo "[2/5] Ansible lint"
ansible-lint --profile production

echo
echo "[3/5] Fleet and recovery guardrails"
bash tests/test_fleet_selection.sh
bash tests/test_recovery_guardrails.sh
bash tests/test_offsite_backup_guardrails.sh

echo
echo "[4/5] Playbook syntax against isolated Lab inventory"
while IFS= read -r playbook; do
    echo "Checking $playbook"
    ansible-playbook --syntax-check -i inventory/lab/hosts.yml "$playbook"
done < <(find playbooks -maxdepth 1 -type f -name '*.yml' | sort)

echo
echo "[5/5] Molecule default scenario"
molecule test -s default

echo
echo "All Ansible validation stages passed."
