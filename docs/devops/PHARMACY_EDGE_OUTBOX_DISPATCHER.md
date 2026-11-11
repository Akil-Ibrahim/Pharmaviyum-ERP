# Pharmacy Edge Outbox Dispatcher

## Purpose

The dispatcher delivers committed local outbox_events to the configured Central Inbox. PostgreSQL is the durable source of truth. Redis/Celery is only the scheduler and execution mechanism; losing or flushing Redis must not delete business events.

## Configuration per Edge node

Set these environment variables on the Pharmacy Edge worker and Beat containers:

| Variable | Purpose |
|---|---|
| PHARMAVIYUM_EDGE_NODE_ID | UUID returned when the Edge installation is enrolled centrally |
| PHARMAVIYUM_EDGE_TOKEN | One-time-issued bearer credential for that Edge node |
| PHARMAVIYUM_CENTRAL_SYNC_URL | HTTPS base URL of the Central API |
| PHARMAVIYUM_SYNC_BATCH_SIZE | Maximum rows claimed per dispatch pass (default 50, hard cap 500) |
| PHARMAVIYUM_SYNC_LEASE_SECONDS | Lease duration (default 30 seconds; minimum 15) |
| PHARMAVIYUM_SYNC_HTTP_TIMEOUT_SECONDS | Central request timeout (default 10 seconds) |

Keep the token in Ansible Vault or the deployment platform's secret store. Never commit it to Git, bake it into an image, place it in a URL, or expose it to the frontend. Configure the same node ID and token only on that pharmacy's Edge installation. The API must be reachable through HTTPS/TLS; mTLS and automated credential rotation remain required hardening work before broad fleet rollout.

If any of the three required Edge variables is missing, the task safely performs no delivery. A Central-only installation should not receive Edge credentials.
The Ansible app-backend role deploys the API, Celery worker and one Beat scheduler together. It renders the secret-bearing .env with mode 0600 and suppresses task output; deploy validation requires the three Edge identity values to be supplied together and requires an HTTPS Central URL.

## Delivery protocol

1. A POS transaction commits its business rows and outbox event in the same PostgreSQL transaction.
2. Celery Beat enqueues a bounded dispatcher pass every five seconds. Run one Beat scheduler per Edge installation.
3. The dispatcher claims eligible rows in a short transaction using FOR UPDATE SKIP LOCKED.
4. Each claim receives a unique lease fencing token and expiry. The attempt counter is incremented before the network call.
5. The HTTP request runs outside the database transaction and includes the immutable event_id, edge_node_id, aggregate identity/version and payload. Central derives the authoritative pharmacy scope from the authenticated Edge registration; the Edge does not send a trusted pharmacy_id field.
   POS product references use the shared product SKU and lot number; local integer product/inventory primary keys are deliberately excluded because they are not portable between independent Edge databases. Central must resolve the SKU in the pharmacy's canonical catalog and quarantine unknown or ambiguous mappings.
Sale aggregate IDs use the immutable receipt number, not a local auto-increment sale ID. Cashier and payment database row IDs are not transmitted; Central must not infer cross-site identity from local numeric keys.
6. Only a matching Central accepted acknowledgement allows the dispatcher to set published_at.
7. A timeout or failure releases the still-owned lease and schedules exponential backoff with jitter. The event remains durable and is never silently discarded.

The Central acknowledgement means durable inbox receipt, not that inventory or other domain effects have been applied.

## Ordering and concurrency

The dispatcher does not claim a later unpublished version while an earlier event for the same (pharmacy_id, aggregate_type, aggregate_id) remains unpublished. Different aggregates can progress concurrently. SKIP LOCKED allows multiple worker processes to claim disjoint rows.

The lease token is a fencing token: a worker whose lease has been replaced cannot mark the row published or reschedule the newer worker's claim. If Central stores an event but the HTTP acknowledgement is lost, the same event_id is sent again; Central Inbox deduplication makes this at-least-once protocol safe.

An earlier event that is rejected or repeatedly failing intentionally blocks later versions of that aggregate. Operators must resolve the failure; do not skip versions or rewrite payloads in place.

## Operational limitations and rollout gates

- This dispatcher only transports the POS event types emitted by the current producer. It does not implement a Central ordered consumer or apply inventory, payment, dispensing, returns or purchasing effects.
- It does not yet include a dead-letter management UI, operator replay endpoint, mTLS, automatic secret rotation, or per-pharmacy monitoring dashboards.
- A 4xx response is retained and retried with backoff; investigate the event and credential rather than deleting the row.
- The worker and Beat containers must use the same local PostgreSQL database as the POS API and must receive the same Edge identity configuration.
- Test Central unavailability, lost acknowledgements, worker termination after claim, lease expiry, duplicate deliveries, aggregate ordering and full-disk conditions before enabling a pilot.
- Do not run production migrations or enable fleet dispatch until the stacked PRs have passed CI, the Central consumer and inventory conflict policy are implemented, and a controlled pilot has passed failure-injection tests.