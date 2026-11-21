# ADR-0001: WebSocket Gateway

## Status

Accepted — implementation is currently a development template and does not yet satisfy the full production contract described by this ADR.

## Context

Pharmaviyum requires real-time communication between clients, pharmacists, and pharmacy managers for chat, notifications, and presence updates.

The application is currently a modular FastAPI monolith. WebSocket support should remain inside the application boundary until measured scale or operational requirements justify a dedicated gateway.

## Decision

- Keep WebSocket handling inside the FastAPI application.
- Use `/ws` as the WebSocket namespace.
- Keep the protocol versioned (`v1`) so the client contract can evolve deliberately.
- Separate routing, connection management, authentication, schemas, channel naming, and feature handlers as the implementation grows.
- Add heartbeat/ping-pong handling, connection lifecycle logging, authorization, and message rate limiting as part of the production contract.
- Use Redis-backed coordination/pub-sub only when horizontal WebSocket scaling requires it; do not introduce a separate service prematurely.

## Current implementation status

The current code under `src/pharmaviyum/api/websocket/` is intentionally minimal:

- `router.py` mounts WebSocket handlers under `/ws`.
- `handlers/chat.py` currently provides an echo-style `/ws/chat` development endpoint.
- The current handler does not yet implement the JWT authentication, role-based authorization, persistence, heartbeat, or production connection controls required by this ADR.

Therefore, this ADR documents the architectural decision and target contract; it must not be interpreted as proof that the complete production WebSocket feature is implemented.

## Consequences

- WebSocket functionality stays within the existing application deployment model.
- The code can evolve from the current development template without committing to a premature microservice.
- A versioned protocol gives the frontend an explicit compatibility boundary.
- Horizontal scaling can be introduced later through shared Redis coordination if required by measured workload.

## Alternatives considered

1. **Multiple WebSocket endpoints per feature**
   - Rejected as the primary architecture because it increases routing and compatibility complexity.
2. **Separate WebSocket microservice**
   - Rejected for the current scale because it adds operational complexity before the need is demonstrated.
3. **Polling via REST API**
   - Rejected for use cases that require low-latency bidirectional communication.

## References

- `src/pharmaviyum/api/websocket/` — current implementation.
- `docs/websocket-protocol.md` — current protocol/design note.

**Author:** Ibrahim Akil  
**Date:** 2026-01-28
