#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

generate_inventory() {
  local count="$1"
  local output="$2"
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

inventory_100="$TMP_DIR/fleet-100.yml"
inventory_101="$TMP_DIR/fleet-101.yml"
generate_inventory 100 "$inventory_100"
generate_inventory 101 "$inventory_101"

sha="$(printf '%064d' 0)"
restore_vars="{\"restore_approved\":true,\"restore_approval_reference\":\"TEST-RESTORE-001\",\"restore_target_confirmation\":\"pharmacy-edge-test-001\",\"restore_target_database\":\"pharmaviyum_restore_ci_001\",\"restore_backup_file\":\"/opt/pharmaviyum/backups/pharmaviyum_20261112.sql.gz\",\"restore_expected_sha256\":\"$sha\",\"app_directory\":\"/opt/pharmaviyum\",\"postgres_db\":\"pharmaviyum\"}"

echo "Checking that an explicitly approved isolated restore passes controller preflight."
ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$restore_vars"

echo "Checking that restore without explicit approval is rejected."
if output="$(ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight \
  -e "$restore_vars" -e restore_approved=false 2>&1)"; then
  echo "ERROR: restore without approval unexpectedly passed."
  exit 1
fi
grep -q "Restore requires explicit approval" <<<"$output"

echo "Checking that restore cannot select multiple pharmacy hosts."
if output="$(ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit "$(make_limit 2)" --tags preflight \
  -e "$restore_vars" 2>&1)"; then
  echo "ERROR: multi-host restore unexpectedly passed."
  exit 1
fi
grep -q "ansible_play_hosts_all | length == 1" <<<"$output"

echo "Checking that restore target confirmation must match the selected host."
if output="$(ansible-playbook -i "$inventory_100" playbooks/restore.yml \
  --limit pharmacy-edge-test-001 --tags preflight \
  -e "$restore_vars" -e restore_target_confirmation=pharmacy-edge-test-002 2>&1)"; then
  echo "ERROR: mismatched restore target confirmation unexpectedly passed."
  exit 1
fi
grep -q "restore_target_confirmation == inventory_hostname" <<<"$output"

rollback_targets="$(make_targets_json 1)"
rollback_vars="{\"rollback_approved\":true,\"rollback_approval_reference\":\"TEST-ROLLBACK-001\",\"rollback_target_confirmations\":$rollback_targets,\"rollback_version\":\"release-test-previous\",\"rollback_image_digest\":\"sha256:$sha\",\"rollback_schema_compatibility_confirmed\":true,\"rollback_schema_compatibility_reference\":\"COMPAT-TEST-001\"}"

echo "Checking that an approved, schema-compatible one-site rollback passes controller preflight."
ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$rollback_vars"

echo "Checking that rollback without schema compatibility evidence is rejected."
if output="$(ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight \
  -e "$rollback_vars" -e rollback_schema_compatibility_confirmed=false 2>&1)"; then
  echo "ERROR: rollback without schema compatibility confirmation unexpectedly passed."
  exit 1
fi
grep -q "rollback_schema_compatibility_confirmed | bool" <<<"$output"

echo "Checking that an 11-site rollback wave is rejected."
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
if output="$(ansible-playbook -i "$inventory_100" playbooks/rollback.yml \
  --limit "$(make_limit 11)" --tags preflight -e "$rollback_vars_11" 2>&1)"; then
  echo "ERROR: an 11-site rollback wave unexpectedly passed."
  exit 1
fi
grep -q "ansible_play_hosts_all | length <= (active_rollout_limit | int)" <<<"$output"

echo "Checking that a 101-site inventory is rejected before rollback."
if output="$(ansible-playbook -i "$inventory_101" playbooks/rollback.yml \
  --limit pharmacy-edge-test-001 --tags preflight -e "$rollback_vars" 2>&1)"; then
  echo "ERROR: a 101-site inventory unexpectedly passed rollback preflight."
  exit 1
fi
grep -q "groups\['pharmacy_servers'\] | length <= (max_supported_pharmacy_sites | int)" <<<"$output"

echo "Ansible recovery guardrail tests passed."
