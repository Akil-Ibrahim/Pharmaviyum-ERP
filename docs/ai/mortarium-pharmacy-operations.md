# Mortarium Pharmacy Operations

## Architectural decision

Mortarium remains one pharmacist-facing AI assistant backed by the existing
LangGraph PharmacistAgent and Agent Harness. Pharmacy capabilities are exposed
as bounded workflows and registered MCP tools, not as separate chatbots or
independent agents.

The LLM may interpret a request, explain an approved pharmacy procedure, and
request read-only operational data. Pharmaviyum's ERP services remain the
source of truth for all business state and deterministic rules.

## Current read-only operational tools

The following tools are registered in the single Pharmaviyum MCP server:

| Tool | Domain | Contract |
|---|---|---|
| `search_pharmacy_products` | Medicine / sellable catalog | Search active pharmacy products by name, INN, SKU, barcode, manufacturer, strength or form; returns available stock |
| `get_inventory_overview` | Inventory | Read lot-level on-hand, reserved, available quantity and reorder level |
| `get_expiring_inventory` | Batch / expiry | Find expired or soon-to-expire available lots |
| `get_sales_summary` | POS / sales | Read completed revenue and transaction counts for an inclusive date range |

All four tools are read-only. Pharmacy and user identity are taken from the
trusted request-scoped MCP authorization context, never from LLM-supplied tool
arguments. Product search applies the existing sellable-catalog exclusions.
Inventory and sales queries are filtered by the authenticated pharmacy.

The tool schemas bound query length, result limits and date ranges. These tools
do not create orders, receive stock, complete sales, issue refunds, write off
stock or change product prices.

## Workflow assistance versus workflow execution

Mortarium supports two distinct behaviors:

1. **Knowledge assistance:** explain a workflow using approved, jurisdiction-
   appropriate retrieved evidence. If no relevant evidence is retrieved, say
   that the procedure could not be verified.
2. **Operational assistance:** call an authorized read-only MCP tool to inspect
   current ERP data and summarize the result with its provenance.

Write operations remain in deterministic ERP endpoints and user interfaces.
A future write-capable tool must have a typed narrow schema, server-derived
tenant context, role/permission checks, idempotency where applicable, audit
logging, and explicit human confirmation. The LLM must never write directly to
the database or infer that a transaction succeeded.

## Not yet exposed to Mortarium as operational tools

The current domain model and API coverage must be audited before adding tools
for purchase-order creation, supplier receiving, inter-branch transfers,
stocktakes, returns/refunds, recall/quarantine, cash-shift management or
financial posting. A workflow described in documentation is not proof that a
corresponding executable API exists.

The procurement domain currently has supplier records, but a complete
purchase-order lifecycle was not found in the inspected model/API surface.
Mortarium must not fabricate procurement status or create a purchase order
until the authoritative workflow is implemented.

## Security and safety

- Tenant identity and role come from authenticated API dependencies and the
  request-scoped MCP context.
- Tools are registered with role metadata and execution class.
- The LLM sees only tools available to the authenticated role.
- No unrestricted SQL, shell, filesystem or arbitrary code tools are exposed.
- Inventory quantities, expiry eligibility, FEFO, prices, payment state,
  prescription requirements and authorization are determined by ERP rules.
- Patient-specific information remains subject to patient-scope authorization.
- Tool output and retrieved documents are untrusted data, not instructions.
- No patient data is added to evaluation fixtures or external judge prompts.

## Validation

Run the deterministic registration and schema contract tests:

```bash
uv run pytest tests/unit/ai/test_pharmacy_operations_mcp.py -v
```

The next integration-test layer must exercise the tools against a test database
with cross-pharmacy decoy records and verify that no result crosses tenant
boundaries. Do not treat schema tests alone as proof of production isolation.
