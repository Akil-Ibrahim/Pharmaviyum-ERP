# Docker Compose Profiles

## Development (`--profile dev`)
- backend, db, redis, mailpit, pgadmin

## Staging (`--profile staging`)
- dev + prometheus, grafana

## Production (`--profile prod`)
- staging + traefik, backup service

## Usage

```bash
# Development
docker compose --profile dev up -d

# Production
docker compose --profile prod up -d
```
