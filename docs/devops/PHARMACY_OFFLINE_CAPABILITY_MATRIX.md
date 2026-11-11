# Pharmacy Offline Capability Matrix

**Status:** Conservative planning baseline; requires product, pharmacy-operations, provider and jurisdictional approval before production.  
**Principle:** A local Edge database can preserve a transaction, but it cannot make an unavailable external authority or payment provider available.

## Capability states

- **Supported offline:** the operation is fully local, deterministic and permitted by the approved business policy.
- **Restricted offline:** allowed only with explicit limits, freshness checks, local authorization and reconciliation controls.
- **Online-only:** must wait for a live provider/Central response.
- **Blocked pending validation:** do not enable until legal, fiscal, provider and operational requirements are documented and tested.

## Initial matrix

| Workflow | Initial state | Offline behavior and controls |
|---|---|---|
| POS cash sale using locally available catalog and stock | Supported offline | Commit sale, payment record, stock ledger movement, audit and outbox atomically in local PostgreSQL. Enforce local permissions, price/policy freshness and idempotency. |
| Local inventory lookup | Supported offline | Read the pharmacy's local stock ledger/materialized balance; show last catalog/policy sync time and data freshness. |
| Local stock receipt from an already authorized delivery | Restricted offline | Require a verifiable purchase/delivery reference, authorized staff and lot/expiry capture. Record immutable receipt facts; reconcile the upstream document later. |
| Stock adjustment, write-off or expiry removal | Restricted offline | Require elevated role, reason code, audit evidence and optional second-person approval. Never overwrite a quantity directly; append a ledger movement. |
| Sale return/refund | Restricted offline | Permit only against a locally known original sale and within configured policy. Cash refund may be locally recorded; external card refund remains pending until provider confirmation. |
| Card payment authorization | Online-only by default | Do not mark a card payment as settled without provider authorization. A separately certified terminal/store-and-forward mode may change this only after acquirer approval and risk limits. |
| Payment webhook/settlement confirmation | Online-only | Keep payment pending until a signed provider event or authenticated reconciliation confirms the outcome. |
| Fiscal receipt / fiscalization | Blocked pending validation | Behavior depends on country, fiscal device/provider and statutory rules. Never claim a receipt was fiscally registered while the authority/device is unavailable. |
| E-prescription verification or dispensing authorization | Blocked pending validation | Do not infer approval from cached prescription data. Offline dispensing requires explicit jurisdiction/provider authorization and an audited protocol. |
| Controlled / specially regulated medicines | Blocked pending validation | Require jurisdiction-specific legal and registry validation; no offline permission is assumed. |
| Cross-pharmacy stock transfer | Restricted offline | Source may record a dispatch/reservation; destination records receipt. Do not expose dispatched stock as sellable at the destination before receipt and validation. |
| Patient profile or prescription history | Blocked pending validation | Requires approved data-sharing basis, local access controls, minimization, retention and audit. No broad patient-data replication by default. |
| Central analytics and network-wide stock view | Online-only for freshness; cached read-only view may be shown | Show last successful sync timestamp and stale-data banner. Never represent a stale central aggregate as real-time stock. |
| Mortarium AI / RAG assistant | Optional / non-critical | If Central AI or model provider is unavailable, POS and deterministic pharmacy workflows continue. AI output must never authorize dispensing, payment or stock mutation. |
| User, role and policy changes | Restricted offline | Use signed/versioned cached policy with bounded validity. High-risk permission changes may require online confirmation; show the applied policy version. |

## Mandatory transaction rules

1. The local business state and its outbox event commit in one PostgreSQL transaction.
2. Every command has a stable idempotency key where replay is possible.
3. Stock is represented by append-only movements and reservations, not last-write-wins replicated counters.
4. A payment remains pending until the provider's authoritative outcome is known.
5. External fiscal, prescription and regulatory checks are never simulated.
6. The UI distinguishes local commit, awaiting synchronization, provider pending, rejected and confirmed states.
7. When cached catalog, price, policy or authorization data exceeds its approved freshness window, the relevant workflow is restricted or blocked.
8. Offline events remain durable locally until acknowledged by Central; a WAN outage must not discard them.

## Decisions required before pilot

- Country and applicable pharmacy/fiscal/e-prescription regulations.
- Payment acquirer and terminal capabilities, including certified offline/store-and-forward support.
- Fiscal device/provider behavior during WAN and power outages.
- Prescription and controlled-medicine registry requirements.
- Maximum permitted offline duration and stale-data windows for catalog, prices and policies.
- Local return/refund and stock-adjustment approval policy.
- Data residency, patient-data synchronization scope, retention and encryption requirements.
- Per-workflow RPO/RTO and site recovery objectives.

## Operational visibility

Every Edge UI and central fleet dashboard should expose:

- online/offline connectivity state;
- last successful Central sync time;
- oldest pending outbox event age and pending count;
- rejected/quarantined event count;
- applied catalog and policy versions;
- local database and disk health;
- last successful backup and backup verification time;
- UPS/battery state where hardware monitoring is configured.

A pharmacy is not considered synchronization-healthy merely because its API health endpoint returns HTTP 200.
