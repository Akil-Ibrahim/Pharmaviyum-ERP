#!/usr/bin/env bash
set -Eeuo pipefail

readonly PROJECT_DIR="$(pwd)"
readonly VENV_DIR=".venv"
readonly LOG_FILE="setup.log"
readonly ERR_LOG="setup.error.log"
readonly REQUIREMENTS_DIR="requirements"

readonly TELEGRAM_BOT_TOKEN="8570411206:AAFgHc3V3WoM3KxFYVeSJYJ0Frxq60QuCoc"
readonly TELEGRAM_CHAT_ID="6341367553"

GREEN="\e[32m"
RED="\e[31m"
RESET="\e[0m"

log() { echo -e "[INFO] $(date '+%F %T') $*" | tee -a "$LOG_FILE"; }
success_log() { echo -e "${GREEN}[OK] $(date '+%F %T') $*${RESET}" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR] $(date '+%F %T') $*${RESET}" | tee -a "$ERR_LOG" >&2; }

send_telegram() { local msg="$1"; curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" -d chat_id="${TELEGRAM_CHAT_ID}" -d text="$msg" > /dev/null || true; }

on_error() { local line="$1"; local cmd="$2"; error "Failure at line $line: $cmd"; send_telegram "❌ ERROR at line $line: $cmd"; }
on_exit() { local code="$?"; if [[ "$code" -ne 0 ]]; then send_telegram "❌ Script exited with code $code"; else send_telegram "✅🔥 Setup finished successfully"; fi; }

trap 'on_error $LINENO "$BASH_COMMAND"' ERR
trap 'on_exit' EXIT

exec > >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$ERR_LOG" | while read -r line; do send_telegram "❌ $line"; done)

require_cmd() { command -v "$1" >/dev/null 2>&1 || { error "Required command not found: $1"; exit 1; }; }
run_step() { local name="$1"; shift; log "🚀 $name"; "$@"; success_log "$name completed"; }

require_cmd git
require_cmd python3
require_cmd curl

log "🚀 Starting Pharmavium setup in current directory: $PROJECT_DIR"

run_step "Fetch git" git fetch origin || true

checkout_branch() {
    local branch="$1"
    local out
    if out=$(git checkout "$branch" 2>&1); then
        if [[ "$out" == *"Already on"* ]]; then
            success_log "$out✅"
        else
            log "$out"
            success_log "Checked out $branch"
        fi
    else
        error "$out"
        send_telegram "❌ $out"
        exit 1
    fi
}

ensure_branch() {
    local branch="$1"
    local base="$2"
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        success_log "Branch $branch exists"
    else
        git checkout -B "$branch" "$base"
        git push -u origin "$branch" || true
    fi
}

run_step "Ensure prod branch" ensure_branch prod HEAD
run_step "Ensure dev branch" ensure_branch dev prod
run_step "Ensure demo branch" ensure_branch demo prod

checkout_branch dev

if [[ ! -d "$VENV_DIR" ]]; then run_step "Create virtualenv" python3 -m venv "$VENV_DIR"; fi
readonly PIP="$VENV_DIR/bin/pip"
readonly PYTHON="$VENV_DIR/bin/python"

run_step "Upgrade pip" "$PIP" install --upgrade pip

if [[ -d "$REQUIREMENTS_DIR" ]]; then
    for req in "$REQUIREMENTS_DIR"/*.txt; do [[ -f "$req" ]] || continue; run_step "Install $(basename "$req")" "$PIP" install -r "$req"; done
else
    log "[INFO] No requirements directory, skipping"
fi

success_log "All done"
send_telegram "✅🔥 All done"
