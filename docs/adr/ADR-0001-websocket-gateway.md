# ADR-0001: WebSocket Gateway

## Status
Accepted

## Context
PharmaViyum requires real-time communication between clients, on-duty pharmacists, and pharmacy managers.  
The system must support chat, notifications, and presence updates.  

Currently, the project is a monolith, but we want to design WebSocket support in a modular way that allows future horizontal scaling.

## Decision
- Implement a WebSocket gateway inside the backend monolith.
- Use a single `/ws` endpoint with JWT authentication.
- Version the protocol (`v1`) for backward compatibility.
- Define channels/rooms based on roles:
  - `client:{id}`
  - `pharmacy:{id}`
  - `duty:{city}`
  - `admins`
- Separate concerns:
  - `router.py` — endpoint
  - `manager.py` — connection handling, broadcasting
  - `auth.py` — JWT validation
  - `schemas.py` — message format (contract)
  - `channels.py` — room/channel naming
  - `handlers/` — chat, presence, notifications
- Heartbeat messages (`ping/pong`) to detect dead connections.
- Log connection/disconnection events for observability.
- Rate limit messages to prevent abuse.

## Consequences
- WebSocket logic is modular and testable.
- Protocol is versioned, safe for future changes.
- Easy to scale horizontally using Redis pub/sub in the future.
- Clear separation of responsibilities aligns with best practices.
- Frontend can reliably consume the contract from `docs/websocket-protocol.md`.

## Alternatives considered
1. **Multiple WebSocket endpoints per feature**
   - Rejected: adds complexity and routing issues.
2. **Separate microservice for WebSockets**
   - Rejected: premature optimization; current load can be handled within monolith.
3. **Polling via REST API**
   - Rejected: inefficient for real-time updates.

## References
- `docs/websocket-protocol.md` — message contract
- `backend/app/api/websocket/` — implementation modules

**Author:** [Ibrahim Akil]  
**Date:** 2026-01-28


