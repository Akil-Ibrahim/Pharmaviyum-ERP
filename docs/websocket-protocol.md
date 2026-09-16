# WebSocket Protocol (v1)

## Status

This document describes the intended v1 contract and the current development implementation. The current server handlers are still templates; authentication, authorization, persistence, and production connection controls are not yet complete.

## Namespace

The WebSocket namespace is:

```text
/ws
```

The current development chat handler is exposed at:

```text
/ws/chat
```

## Authentication and authorization

The production contract requires JWT authentication and pharmacy/role authorization before accepting application messages.

The current development handler accepts the connection without the full production authentication layer. Do not treat `/ws/chat` as a production-safe endpoint until the authorization contract is implemented and covered by tests.

## Message model

The production protocol should use versioned JSON messages with an explicit message type and correlation identifier. A representative envelope is:

```json
{
  "version": "v1",
  "type": "chat.message",
  "request_id": "<opaque-id>",
  "payload": {}
}
```

The exact payload schemas should be defined in application code before the protocol is considered stable.

## Planned channels

The architecture reserves logical channels for:

- client-specific communication;
- pharmacy-scoped communication;
- duty/presence communication;
- administrative notifications.

Channel membership must always be authorized from authenticated application context. Client-provided channel names must never bypass tenant or role checks.

## Connection lifecycle

The production implementation should provide:

1. authenticated connection establishment;
2. authorization of requested channels;
3. heartbeat/ping-pong handling;
4. bounded message size and rate limits;
5. structured connect/disconnect/error telemetry;
6. graceful close handling;
7. explicit protocol errors for invalid messages.

## Scaling

The first implementation remains inside the FastAPI application. Redis pub/sub or another shared coordination mechanism may be introduced when measured horizontal scaling requires cross-instance message delivery.

A dedicated WebSocket service is not part of the current deployment contract.

## Current implementation

The active implementation is under:

```text
src/pharmaviyum/api/websocket/
├── router.py
├── logger.py
└── handlers/
    └── chat.py
```

`handlers/chat.py` currently implements an echo-style development endpoint. It should be treated as a scaffold for the v1 contract, not as a completed chat system.

## Related documentation

- `docs/adr/ADR-0001-websocket-gateway.md` — architectural decision and production requirements.
- `docs/guides/TESTING.md` — test strategy.
