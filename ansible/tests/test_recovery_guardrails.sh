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
        host = f"pharmacy-edge-test-{index:03d}"
        stream.write(
            f"        {host}:\n"
            "          ansible_host: 127.0.0.1\n"
            "          ansible_user: ansible-test\n"
            "          ansible_connection: local\n"
            f"          pharmacy_id: test-pharmacy-{index:03d}\n"
            f"          site_code: TEST-{index:03d}\n"
            f"          postgres_password: test-only-password-{index:03d}\n"
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

make_targets_json() {
  python - "$1" <<'PY'
import json, sys
print(json.dumps([f"pharmacy-edge-test-{i:03d}" for i in range(1, int(sys.argv[1]) + 1)]))
PY
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

sha="$(printf '%064d' 0)"
restore_vars="{\"restore_approved\":true,\"restore_approval_reference\":\"TEST-RESTORE-001\",\"restore_target_confirmation\":\"pharmacy-edge-test-001\",\"restore_target_database\":\"pharmaviyum_restore_ci_001\",\"restore_backup_file\":\"/opt/pharmaviyum/backups/pharmaviyum_20261112.sql.gz\",\"restore_expected_sha256\":\"$sha\",\"app_directory\":\"/opt/pharmaviyum\",\"postgres_db\":\"pharmaviyum\"}"

echo "Checking approved single-host restore preflight (controller-local only)."
ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$restore_vars"

expect_rejected "restore without approval" "Restore requires explicit approval" \
  ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$restore_vars" -e restore_approved=false

expect_rejected "restore selecting two hosts" "Restore requires explicit approval" \
  ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit "$(make_limit 2)" --tags preflight -e "$restore_vars"

expect_rejected "restore target confirmation mismatch" "Restore requires explicit approval" \
  ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$restore_vars" \
  -e restore_target_confirmation=pharmacy-edge-test-002

expect_rejected "restore with 101-site inventory" "Restore requires explicit approval" \
  ansible-playbook -i "$inventory_101" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$restore_vars"

rollback_targets="$(make_targets_json 1)"
rollback_vars="{\"rollback_approved\":true,\"rollback_approval_reference\":\"TEST-ROLLBACK-001\",\"rollback_target_confirmations\":$rollback_targets,\"rollback_version\":\"release-test-previous\",\"rollback_image_digest\":\"sha256:$sha\",\"rollback_schema_compatibility_confirmed\":true,\"rollback_schema_compatibility_reference\":\"COMPAT-TEST-001\"}"

echo "Checking approved, schema-compatible one-site rollback preflight (controller-local only)."
ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$rollback_vars"

expect_rejected "rollback without schema compatibility evidence" "Rollback requires explicit change approval" \
  ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$rollback_vars" \
  -e rollback_schema_compatibility_confirmed=false

rollback_targets_11="$(make_targets_json 11)"
rollback_vars_11="$(python - "$rollback_targets_11" "$sha" <<'PY'
import json, sys
print(json.dumps({
    "rollback_approved": True,
    "rollback_approval_reference": "TEST-ROLLBACK-011",
    "rollback_target_confirmations": json.loads(sys.argv[1]),
    "rollback_version": "release-test-previous",
    "rollback_image_digest": "sha256:" + sys.argv[2],
    "rollback_schema_compatibility_confirmed": True,
    "rollback_schema_compatibility_reference": "COMPAT-TEST-011",
}))
PY
)"
expect_rejected "11-site rollback wave" "Rollback requires explicit change approval" \
  ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit "$(make_limit 11)" --tags preflight -e "$rollback_vars_11"

expect_rejected "rollback with 101-site inventory" "Rollback requires explicit change approval" \
  ansible-playbook -i "$inventory_101" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$rollback_vars"

echo "Ansible recovery guardrail tests passed."
