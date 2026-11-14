# Email delivery and local testing

Pharmaviyum's active password-recovery route sends messages through SMTP. A one-time account-setup email generator and modular user-creation route are present, but that modular user router is not mounted in the active API yet; do not assume active user creation sends setup emails. The transport uses Python's standard-library smtplib and EmailMessage; synchronous SMTP I/O runs in a worker thread so it does not block the FastAPI event loop.

## Local development with Docker Compose

Start the API and its dependencies:

```bash
docker compose up -d api
```

Compose starts Mailpit automatically. Open the local inbox at:

- Web UI: http://localhost:8025
- SMTP host from the API container: mailpit
- SMTP port: 1025
- TLS: disabled for this local-only Mailpit connection

The Mailpit ports are bound to 127.0.0.1, so the local capture service is not exposed to the LAN. The Compose API defaults EMAILS_ENABLED=true so account setup and password-recovery messages can be tested locally.

When running FastAPI directly on the host rather than in Docker, set SMTP_HOST=localhost.

## Configuration

The supported environment variables are documented in .env.example:

- EMAILS_ENABLED
- APP_URL — public origin used to build password setup/reset links
- SMTP_HOST, SMTP_PORT
- SMTP_USER, SMTP_PASSWORD — configure both or neither
- SMTP_STARTTLS or SMTP_SSL — do not enable both
- SMTP_TIMEOUT_SECONDS
- EMAILS_FROM

Production configuration must be supplied through the FastAPI Cloud environment, not committed to Git. If production email is enabled, the application requires an SMTP host, TLS, and an HTTPS APP_URL. Set the sender address and provider credentials according to the selected SMTP provider. This code change does not enable production email or set production secrets.

## Delivery semantics

Password-recovery messages are scheduled with FastAPI background tasks after the API response is prepared. The account-setup helper is implemented, but its modular user router is not mounted in the active API. SMTP failures are logged without logging message bodies or reset tokens. FastAPI background tasks are best-effort, not a durable queue; a transactional outbox/Celery delivery worker remains a future reliability improvement for guaranteed delivery and retry.

## Security

- Passwords are never included in welcome emails.
- Setup/reset links contain short-lived, one-time-use tokens.
- SMTP authentication requires both username and password.
- Production SMTP requires TLS.
- Do not use Mailpit or unencrypted SMTP for production.
