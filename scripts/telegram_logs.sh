#!/usr/bin/env bash
# ------------------------------------------------------------------
# Telegram Logs Module
# Sends last N lines of log files to Telegram or stdout
# Designed to be modular and Termux-safe
# ------------------------------------------------------------------

# Config: default number of lines to send
LOG_LINES=20

# Function: send log file
# Arguments:
#   $1 - path to log file
#   $2 - optional number of lines to send
send_log() {
    local file="$1"
    local lines="${2:-$LOG_LINES}"

    # Check if file exists
    if [[ ! -f "$file" ]]; then
        echo "📄 Log file not found: $file"
        return 1
    fi

    # Read last N lines
    local content
    content=$(tail -n "$lines" "$file")

    # Send to Telegram if function send_info exists, else print to stdout
    if declare -f send_info >/dev/null 2>&1; then
        send_info "📄 Log: $file\n$content"
    else
        echo -e "📄 Log: $file\n$content"
    fi
}

# Function: send multiple logs at once
# Arguments:
#   $@ - list of log files
send_logs() {
    for log_file in "$@"; do
        send_log "$log_file"
    done
}
