#!/usr/bin/env bash
set -Eeuo pipefail

# --------------------------------------
# VARIABLES
# --------------------------------------
workflow="${1:-}"           # workflow filename, e.g., load_test.yml
ref="${2:-dev}"             # default branch
LOG_FILE="trigger_workflow.log"

# --------------------------------------
# LOGGING
# --------------------------------------
log() { echo "[INFO] $(date '+%F %T') $*"; }
success() { echo "[SUCCESS] $(date '+%F %T') $*"; }
error() { echo "[ERROR] $(date '+%F %T') $*" >&2; }

# --------------------------------------
# TELEGRAM (optional)
# --------------------------------------
send_info() { [[ "$(type -t send_info 2>/dev/null)" == "function" ]] && send_info "$*" || log "$*"; }
send_success() { [[ "$(type -t send_success 2>/dev/null)" == "function" ]] && send_success "$*" || success "$*"; }
send_error() { [[ "$(type -t send_error 2>/dev/null)" == "function" ]] && send_error "$*" || error "$*"; }

# --------------------------------------
# VALIDATION
# --------------------------------------
if [[ -z "$workflow" ]]; then
    send_error "Workflow file not specified! Usage: $0 <workflow.yml> [branch]"
    exit 1
fi

# --------------------------------------
# CHECK GH CLI
# --------------------------------------
if ! command -v gh >/dev/null 2>&1; then
    send_info "gh CLI not found, skipping workflow trigger for $workflow"
    exit 0
fi

# --------------------------------------
# TRIGGER WORKFLOW
# --------------------------------------
send_info "📤 Triggering GitHub Actions workflow: $workflow on branch $ref"

if gh workflow run "$workflow" --ref "$ref" >/dev/null 2>&1; then
    send_success "✅ Workflow $workflow triggered successfully on $ref"
else
    send_error "❌ Failed to trigger workflow $workflow on $ref"
    exit 1
fi
