#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

generate_inventory() {
  local count="$1" output="$2"
  python - "$count" "$output" <<'PY'
import sys
count, path = int(sys.argv[1]), sys.argv[2]
with open(path, "w", encoding="utf-8") as stream:
    stream.write("---\nall:\n  children:\n    pharmacy_servers:\n      hosts:\n")
    for index in range(1, count + 1):
        pharmacy_id = f"pharmacy-{index:03d}"
        stream.write(
            f"        pharmacy-edge-test-{index:03d}:\n"
            "          ansible_host: 192.0.2.1\n"
            "          ansible_user: ansible-test\n"
            f"          pharmacy_id: {pharmacy_id}\n"
            f"          site_code: TEST-{index:03d}\n"
            f"          restic_repository_url: rest:https://backup.example.invalid/{pharmacy_id}\n"
            "          restic_repository_password: test-only-encryption-password-123\n"
            "          restic_rest_username: test-only-user\n"
            "          restic_rest_password: test-only-password\n"
        )
PY
}

make_limit() {
  local count="$1" result="" index host
  for ((index=1; index<=count; index++)); do
    host="$(printf 'pharmacy-edge-test-%03d' "$index")"
    [[ -z "$result" ]] || result+=","
    result+="$host"
  done
  printf '%s' "$result"
}

expect_rejected() {
  local description="$1" expected_message="$2"
  shift 2
  local output
  echo "Checking rejection: $description"
  if output="$("$@" 2>&1)"; then
    echo "ERROR: $description unexpectedly passed."
    exit 1
  fi
  if ! grep -q "$expected_message" <<<"$output"; then
    echo "ERROR: $description failed for an unexpected reason:"
    printf '%s\n' "$output"
    exit 1
  fi
}

inventory_100="$TMP_DIR/fleet-100.yml"
inventory_101="$TMP_DIR/fleet-101.yml"
generate_inventory 100 "$inventory_100"
generate_inventory 101 "$inventory_101"

vars='{"offsite_backup_approved":true,"offsite_backup_approval_reference":"TEST-OFFSITE-001","offsite_backup_file":"/opt/pharmaviyum/backups/pharmaviyum_20261112.sql.gz","app_directory":"/opt/pharmaviyum","active_rollout_limit":10,"max_supported_pharmacy_sites":100}'

echo "Checking approved single-site off-site preflight (controller-local only)."
ansible-playbook -i "$inventory_100" playbooks/backup-offsite.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$vars"

expect_rejected "off-site transfer without explicit approval" "Off-site transfer requires approval" \
  ansible-playbook -i "$inventory_100" playbooks/backup-offsite.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$vars" -e offsite_backup_approved=false

expect_rejected "11-site off-site upload wave" "selected wave of 1-10 pharmacies" \
  ansible-playbook -i "$inventory_100" playbooks/backup-offsite.yml \
  --limit "$(make_limit 11)" --tags preflight -e "$vars"

expect_rejected "101-site inventory" "selected wave of 1-10 pharmacies" \
  ansible-playbook -i "$inventory_101" playbooks/backup-offsite.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$vars"

echo "Ansible off-site backup preflight tests passed."
