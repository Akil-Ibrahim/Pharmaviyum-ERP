#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

export PHARMAVIYUM_APP_VERSION="ansible-preflight-test"
export PHARMAVIYUM_BACKEND_IMAGE_DIGEST="sha256:$(printf '%064d' 0)"

EXTRA_VARS='{"docker_package_versions":{"docker-ce":"test","docker-ce-cli":"test","containerd.io":"test","docker-buildx-plugin":"test","docker-compose-plugin":"test"}}'

generate_inventory() {
  local count="$1"
  local output="$2"
  local mode="${3:-normal}"
  python - "$count" "$output" "$mode" <<'PY'
import sys
count = int(sys.argv[1])
path = sys.argv[2]
mode = sys.argv[3]
with open(path, "w", encoding="utf-8") as stream:
    stream.write("---\nall:\n  children:\n    pharmacy_servers:\n      hosts:\n")
    for index in range(1, count + 1):
        suffix = f"{index:03d}"
        password = f"test-only-password-{suffix}"
        site_code = f"TEST-{suffix}"
        if mode == "duplicate-password" and index == count:
            password = "test-only-password-001"
        if mode == "missing-site-code" and index == count:
            site_code = ""
        stream.write(
            f"        pharmacy-edge-test-{suffix}:\n"
            f"          ansible_host: 127.0.0.1\n"
            f"          ansible_user: ansible-test\n"
            f"          ansible_connection: local\n"
            f"          pharmacy_id: test-pharmacy-{suffix}\n"
            f"          site_code: {site_code}\n"
            f"          postgres_password: {password}\n"
            f"          pharmaviyum_edge_node_id: ''\n"
            f"          pharmaviyum_edge_token: ''\n"
            f"          pharmaviyum_central_sync_url: ''\n"
)
PY
}

make_limit() {
  local count="$1"
  local limit=""
  for ((index = 1; index <= count; index++)); do
    suffix="$(printf '%03d' "$index")"
    host="pharmacy-edge-test-$suffix"
    if [[ -n "$limit" ]]; then
      limit+=","
    fi
    limit+="$host"
  done
  printf '%s' "$limit"
}

inventory_100="$TMP_DIR/fleet-100.yml"
inventory_101="$TMP_DIR/fleet-101.yml"
inventory_duplicate_password="$TMP_DIR/fleet-100-duplicate-password.yml"
inventory_missing_site_code="$TMP_DIR/fleet-100-missing-site-code.yml"
generate_inventory 100 "$inventory_100"
generate_inventory 101 "$inventory_101"
generate_inventory 100 "$inventory_duplicate_password" duplicate-password
generate_inventory 100 "$inventory_missing_site_code" missing-site-code

echo "Checking that a 10-site wave succeeds from a 100-site inventory."
ansible-playbook -i "$inventory_100" playbooks/deploy.yml \
  --limit "$(make_limit 10)" --tags preflight -e "$EXTRA_VARS"

echo "Checking that an 11-site wave is rejected."
if output="$(ansible-playbook -i "$inventory_100" playbooks/deploy.yml \
  --limit "$(make_limit 11)" --tags preflight -e "$EXTRA_VARS" 2>&1)"; then
  echo "ERROR: an 11-site rollout unexpectedly passed the active rollout guardrail."
  exit 1
fi
grep -q "active rollout limit is 10" <<<"$output"

echo "Checking that a 101-site inventory is rejected even for a 10-site wave."
if output="$(ansible-playbook -i "$inventory_101" playbooks/deploy.yml \
  --limit "$(make_limit 10)" --tags preflight -e "$EXTRA_VARS" 2>&1)"; then
  echo "ERROR: a 101-site inventory unexpectedly passed the architecture ceiling."
  exit 1
fi
grep -q "architecture inventory ceiling" <<<"$output"

echo "Checking that a duplicate DB credential in an unselected site is rejected."
if output="$(ansible-playbook -i "$inventory_duplicate_password" playbooks/deploy.yml \
  --limit "$(make_limit 10)" --tags preflight -e "$EXTRA_VARS" 2>&1)"; then
  echo "ERROR: a duplicate PostgreSQL credential outside the selected wave was accepted."
  exit 1
fi
grep -q "configured PostgreSQL credential must be unique" <<<"$output"

echo "Checking that a missing site code in an unselected site is rejected."
if output="$(ansible-playbook -i "$inventory_missing_site_code" playbooks/deploy.yml \
  --limit "$(make_limit 10)" --tags preflight -e "$EXTRA_VARS" 2>&1)"; then
  echo "ERROR: an inventory with a missing site_code was accepted."
  exit 1
fi
grep -q "non-empty site_code" <<<"$output"

echo "Ansible fleet-selection guardrail tests passed."
