# WebSocket Protocol (v1)

**Status:** Proposed application protocol. Current handlers are development scaffolds, not a production implementation.

## Namespace and current routes

The application mounts handlers under /ws. Current source files:
- src/pharmaviyum/api/websocket/router.py
- src/pharmaviyum/api/websocket/handlers/chat.py
- src/pharmaviyum/api/websocket/handlers/notifications.py

The development handlers accept a connection and echo/acknowledge plain text. They do not implement the JSON envelope below, JWT authentication, pharmacy authorization, durable delivery, heartbeat policy or production connection controls. Do not use them for real patient or production traffic.

## Protocol goals

The v1 contract is intended for real-time chat, pharmacy-scoped notifications and presence. It must provide explicit protocol version and message type, request correlation, strict payload schemas, authenticated identity, server-authorized channel membership, bounded message size/rate/concurrency, predictable errors and graceful close behavior.

## Proposed JSON envelope

    {
      "version": "v1",
      "type": "chat.message",
      "request_id": "opaque-client-generated-id",
      "payload": {}
    }

- version: required protocol version.
- type: namespaced event type, such as chat.message, notification.subscribe or presence.update.
- request_id: opaque correlation ID, not an authorization credential.
- payload: event-specific object validated against a server-side schema.

Payload schemas and limits must be implemented and contract-tested before the protocol is stable. Unknown versions/types and malformed payloads must not reach business handlers.

## Proposed server event types

| Type | Purpose | Security requirement |
|---|---|---|
| connection.ready | Confirm authenticated connection/version | Server-generated |
| chat.message | Submit a chat message | Validate tenant, sender and recipient |
| chat.message.ack | Acknowledge accepted message | Correlation and durable ID if persistence exists |
| notification.subscribe | Request subscription | Server authorizes each channel |
| notification.event | Deliver notification | No cross-tenant broadcast |
| presence.update | Update duty/presence | Role- and pharmacy-scoped |
| protocol.error | Report protocol failure | No stack traces or secrets |

These names define design vocabulary, not current runtime capabilities.

## Authentication and authorization

Production connection establishment must authenticate the user before accepting application messages. Validate active user, active pharmacy membership, role permission and resource access.

Do not trust pharmacy ID, role, channel name or recipient supplied by the client. Derive identity from the authenticated server-side principal. Define token expiry/revocation behavior for long-lived connections. Avoid long-lived bearer tokens in query strings.

## Validation, limits and errors

Define maximum frame/payload size, allowed content types, per-user/tenant/connection rate limits, maximum concurrent connections, idle timeout, heartbeat interval, backpressure and slow-consumer behavior.

Suggested error codes: UNAUTHENTICATED, FORBIDDEN, UNSUPPORTED_VERSION, UNKNOWN_EVENT_TYPE, INVALID_PAYLOAD, RATE_LIMITED, MESSAGE_TOO_LARGE and TEMPORARILY_UNAVAILABLE.

Errors should include a safe message and request_id where available. Never return exception text, SQL, credentials or patient data.

## Lifecycle and delivery semantics

Target lifecycle: connect → authenticate → negotiate version → authorize subscriptions → validate messages → enforce rate/backpressure → acknowledge accepted work → emit bounded telemetry → graceful close.

If durable delivery is implemented, define message IDs, deduplication, acknowledgement, retention and replay. Do not promise exactly-once delivery. Prefer at-least-once delivery with idempotent consumers where appropriate.

## Scaling

Keep the gateway inside FastAPI initially, consistent with [ADR-0001](./adr/ADR-0001-websocket-gateway.md). Add Redis pub/sub only when measured horizontal scaling requires it. Pub/sub is not a durable queue; durable notifications require persistence and replay semantics.

## Observability and privacy

Record connection counts, close categories, rate-limit outcomes, event type, processing latency and delivery failures with bounded labels. Do not log message bodies, tokens, patient identifiers or full channel membership lists.

## Production readiness checklist

- [ ] Authentication before application messages.
- [ ] Tenant and role authorization for every channel/action.
- [ ] Resource authorization where applicable.
- [ ] Strict versioned schemas and contract tests.
- [ ] Frame limits, rate limits and connection quotas.
- [ ] Heartbeat, idle timeout and graceful shutdown.
- [ ] Backpressure and slow-consumer policy.
- [ ] Durable delivery semantics documented if required.
- [ ] Cross-instance behavior tested if horizontally scaled.
- [ ] Privacy-reviewed telemetry and security tests.

Until these gates pass, /ws/chat and /ws/notifications remain development-only scaffolding.

## References

- [ADR-0001: WebSocket Gateway](./adr/ADR-0001-websocket-gateway.md)
- [System context](./architecture/system-context.md)
- [Testing guide](./guides/TESTING.md)
