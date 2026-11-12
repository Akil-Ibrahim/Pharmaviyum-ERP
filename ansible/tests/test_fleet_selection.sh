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
  python - "$count" "$output" <<'PY'
import sys
count = int(sys.argv[1])
path = sys.argv[2]
with open(path, "w", encoding="utf-8") as stream:
    stream.write("---\nall:\n  children:\n    pharmacy_servers:\n      hosts:\n")
    for index in range(1, count + 1):
        suffix = f"{index:03d}"
        stream.write(
            f"        pharmacy-edge-test-{suffix}:\n"
            f"          ansible_host: 127.0.0.1\n"
            f"          ansible_user: ansible-test\n"
            f"          ansible_connection: local\n"
            f"          pharmacy_id: test-pharmacy-{suffix}\n"
            f"          site_code: TEST-{suffix}\n"
            f"          postgres_password: test-only-password-{suffix}\n"
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
generate_inventory 100 "$inventory_100"
generate_inventory 101 "$inventory_101"

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

echo "Ansible fleet-selection guardrail tests passed."
