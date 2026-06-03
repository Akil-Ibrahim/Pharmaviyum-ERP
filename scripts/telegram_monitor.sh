#!/usr/bin/env bash
set -Eeuo pipefail

# --------------------------------------
# TELEGRAM SERVICE MONITOR (TERMUX SAFE)
# --------------------------------------

info() {
    echo "[INFO] $1"
}

check_docker() {
    if command -v docker >/dev/null 2>&1; then
        docker ps --format "  {{.Names}} - {{.Status}}"
    else
        echo "• DOCKER: not available (skipped)"
    fi
}

check_redis() {
    if command -v redis-cli >/dev/null 2>&1; then
        redis-cli ping || echo "• REDIS: not responding"
    else
        echo "• REDIS: not available (skipped)"
    fi
}

check_postgres() {
    if command -v pg_isready >/dev/null 2>&1; then
        pg_isready || echo "• POSTGRES: not responding"
    else
        echo "• POSTGRES: not available (skipped)"
    fi
}

check_celery() {
    if command -v celery >/dev/null 2>&1; then
        celery status || echo "• CELERY: not responding"
    else
        echo "• CELERY: not available (skipped)"
    fi
}

check_services() {
    info "SERVICE STATUS:"
    check_docker
    check_redis
    check_postgres
    check_celery
}
