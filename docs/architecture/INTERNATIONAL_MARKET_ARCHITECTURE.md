# International Market Architecture

## Product principle

Pharmaviyum ERP/CRM is an international pharmacy operations platform. Vietnam is a supported market, not the product's global default or the only target market. Existing country-specific work must remain available while being isolated from global behavior.

## Architecture boundaries

### Global core

Keep reusable workflows and domain concepts in the shared core: pharmacy and branch management, patients, prescriptions, POS, products, inventory, batches, FEFO, procurement, suppliers, audit trails, and Mortarium AI orchestration.

Global product identity should support active ingredients/INN, brands, strengths, dosage forms, pack sizes, and stable identifiers. National registrations, reimbursement identifiers, and local package/label details belong in market-specific data.

### Market profile / regulatory adapter

Regulatory behavior must be selected from an explicit pharmacy/tenant jurisdiction or an explicitly supplied request context. Do not infer jurisdiction from UI language, user language, product brand, or deployment region.

A market adapter may define validated prescription validity, controlled-drug schedules and quantity limits, prescription requirements, registration status, tax and currency rules, labeling/serialization, locale, and timezone. Unknown or unconfigured rules must not be represented as verified legal compliance. Do not invent defaults to fill gaps in national regulation.

The currently implemented VN/TH/ID prescription rule tables are partial market coverage, not a global regulatory source. Add or update values only against verified, maintained regulatory sources and tests.

### Mortarium AI

AI requests that need local regulatory interpretation should carry the applicable jurisdiction explicitly. Language is a separate field. Retrieval and evaluations should include global/jurisdiction-neutral cases alongside market-specific cases. Safety rules that apply generally (for example, avoiding dangerous dosage advice and handling prompt injection) should remain independent of local law.

### Internationalization

Locale selection controls translated UI/content, formatting, and language detection. It must not silently choose a country's legal rules. Available locales and supported market profiles are separate capabilities and should be documented separately.

## Migration plan

1. Inventory hard-coded country defaults and legal assumptions in models, settings, APIs, seed data, tests, and AI tools.
2. Make jurisdiction resolution explicit and define safe behavior when it is missing.
3. Keep existing VN/TH/ID rules as named market adapters; validate sources before broadening coverage.
4. Add neutral/global and non-Vietnam market tests without deleting existing Vietnamese cases.
5. Separate international drug identity from national registration and packaging data.
6. Report coverage honestly: language support, market configuration, and validated regulatory coverage are different metrics.

## Non-goals for this change

This architecture note does not certify compliance in any country, add unverified legal limits, migrate production data, or change deployment configuration.
