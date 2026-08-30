#!/bin/bash
# Docker Secrets Setup
set -e

create_secret() {
    local name=$1
    local env_var=$2
    local value="${!env_var}"
    
    if docker secret inspect "$name" > /dev/null 2>&1; then
        echo "Secret '$name' already exists"
        return
    fi
    
    if [ -z "$value" ]; then
        echo "Enter value for $name:"
        read -s value
    fi
    
    echo "$value" | docker secret create "$name" -
    echo "Created secret: $name"
}

create_secret "pharmaviyum_db_password" "DB_PASSWORD"
create_secret "pharmaviyum_jwt_secret" "JWT_SECRET_KEY"
create_secret "pharmaviyum_redis_password" "REDIS_PASSWORD"

echo "All secrets created"
