#!/usr/bin/env bash

# Load .env safely
if [[ -f .env ]]; then
    export $(grep -v '^#' .env | xargs)
fi

_send_telegram() {
    local message="$1"

    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" || -z "${TELEGRAM_CHAT_ID:-}" ]]; then
        echo "[TELEGRAM] Not configured, skipping message"
        return 0
    fi

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="$message" \
        -d parse_mode="Markdown" \
        > /dev/null
}

send_info()    { _send_telegram "ℹ️ *INFO*\n$1"; }
send_success() { _send_telegram "✅ *SUCCESS*\n$1"; }
send_error()   { _send_telegram "❌ *ERROR*\n$1"; }


