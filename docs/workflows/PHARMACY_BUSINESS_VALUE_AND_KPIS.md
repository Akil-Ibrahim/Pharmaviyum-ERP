# Pharmaviyum — Pharmacy Business Value & KPI Specification

**Document type:** Business value and KPI specification  
**Status:** Working baseline; KPI definitions require owner approval and baseline collection  
**Scope:** Pharmacists, individual pharmacies, pharmacy networks and management  
**Language:** English  
**Related workflow specification:** [Pharmacy workflow](./pharmacy-workflow.en.md)  
**Russian version:** [Русская версия](./PHARMACY_BUSINESS_VALUE_AND_KPIS.ru.md)

## 1. Purpose and source hierarchy

This document translates pharmacy-domain needs into business outcomes and measurable KPIs for Pharmaviyum. It complements, and does not replace, the canonical operational workflow specification.

**Primary engineering requirements and measurement source:** [ENGINEERING_BENCHMARK_REQUIREMENTS.md](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md). It defines the engineering measurement contract, evidence labels, benchmark reporting requirements, quality gates and technical evaluation areas. Technical tests and measurement evidence must follow that document.

Source hierarchy:
1. **Engineering requirements, benchmark methodology and evidence rules:** `docs/devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md`.
2. **Canonical pharmacy operating workflows and business controls:** [pharmacy-workflow.en.md](./pharmacy-workflow.en.md).
3. **Domain context and practitioner perspective:** [AI in the Pharmacy: How Technology Can Support the Pharmacist](https://medium.com/@ibrahimengpy/ai-in-the-pharmacy-how-technology-can-support-the-pharmacist-a755ba3a2c9a).
4. **This document:** business-value model, KPI definitions and their relationship to pharmacy workflows.

The Medium article is a first-person domain reference based on pharmacy practice and Pharmaviyum development. It informs problem discovery and workflow context; it is not proof that a described capability has been implemented or validated.

## 2. Product value proposition

**Pharmaviyum is an AI-powered Pharmacy ERP/CRM platform designed to improve operational efficiency across pharmacists, individual pharmacies and pharmacy networks through workflow automation, centralized operations management and controlled AI assistance.**

The business objective is to reduce avoidable routine work, improve staff productivity, strengthen inventory and expiry control, and support consistent operations across branches.

AI is an assistive capability. The deterministic business core remains the source of truth for inventory, pricing, batch eligibility, dispensing state, payments, authorization and audit. Professional decisions remain with the pharmacist.

## 3. Business value by operating level

### 3.1 Pharmacist

| KPI / measure | Intended value |
|---|---|
| Customer Service Time | Reduce avoidable time spent searching for information during service |
| Administrative Time Saved | Reduce time spent on repetitive administrative work |
| Medication Search Time | Retrieve medicine and product information faster |
| AI Task Completion Rate | Complete eligible pharmacist-support tasks with controlled AI assistance |

Benefits: fewer repetitive manual operations; faster access to medicine information; authorized access to relevant patient and dispensing history where permitted; AI-assisted retrieval, comparison and summarization; more time for patient consultation and professional work.

### 3.2 Individual pharmacy

| KPI / measure | Intended value |
|---|---|
| Inventory Accuracy | Improve agreement between recorded and physically counted stock |
| Stockout Rate | Reduce valid demand that cannot be fulfilled because an item is unavailable |
| Expired Stock Rate | Reduce the share of stock that has expired |
| FEFO Compliance | Apply deterministic First-Expired, First-Out rotation to eligible batches |
| Procurement Lead Time | Improve the time from approved replenishment need/order to receipt |

Benefits: visibility and control of batch-level inventory; expiry monitoring, quarantine and write-off controls; structured procurement and replenishment; visible receiving and stocktake discrepancies; better assortment and availability oversight.

### 3.3 Pharmacy network / company

| KPI / measure | Intended value |
|---|---|
| Centralized Operations Coverage | Increase the share of branches managed through common operational controls |
| Cross-Branch Data Consistency | Improve consistency of shared and replicated business data |
| Workflow Automation Rate | Reduce eligible manual steps across branch workflows |
| Network Synchronization Lag | Monitor delay between a committed source change and its availability at intended branches |

Benefits: centralized branch oversight; consolidated analytics; consistent data and process controls; network-wide exception monitoring; data-informed operational decisions.

Network Synchronization Lag is primarily a technical/operational service metric, not a standalone business outcome. Interpret it alongside data consistency and successful reconciliation.

## 4. Six primary business KPIs for CV

These six indicators form the primary business-value vocabulary for CV positioning. They are **measurement dimensions, not claims of achieved improvement**.

| KPI | Definition / intended outcome |
|---|---|
| Employee Productivity Improvement | Change in validated work completed per employee or paid work hour, with quality guardrails |
| Administrative Time Reduction | Reduction in time spent on defined administrative tasks |
| Inventory Accuracy | Agreement between recorded and physically counted inventory at product/batch/location level |
| Stock Availability | Share of valid demand lines that can be fulfilled from eligible available stock |
| Expired Stock Reduction | Reduction in expired stock quantity or expired-stock share, measured consistently over time |
| Cross-Branch Operational Consistency | Consistency of defined operational controls, data states and workflow outcomes across branches |

**Workflow Automation** is a separate, cross-cutting product capability and value driver. It complements the six primary KPIs; it is not a seventh primary CV KPI.

## 5. KPI measurement contracts

Every KPI needs an agreed owner, population, unit of analysis, numerator/denominator, exclusions, data source, time window, baseline, target and validation method before it is reported as a result.

Recommended starting definitions (final formulas require approval against the actual data model and workflow):

| KPI | Suggested operational definition |
|---|---|
| Employee Productivity Improvement | Compare validated completed work units per paid staff hour against a comparable baseline. Segment by role, shift and workload; apply service-quality and safety guardrails. |
| Administrative Time Reduction | `(baseline task time − measured task time) / baseline task time × 100%` for the same defined task set and comparable conditions. |
| Inventory Accuracy | Exact-match rate of stocktake lines at product + batch + location level; report quantity variance separately. |
| Stock Availability | Fulfillable valid demand lines / all eligible valid demand lines. Define treatment of substitutions, discontinued products, reservations and supplier backorders. |
| Expired Stock Reduction | Compare expired units or expired-unit share of on-hand units over equivalent periods. Do not publish confidential monetary valuations. |
| Cross-Branch Operational Consistency | Measure branch compliance with the same workflow/control set and reconciliation success for shared data. Report branch coverage and exceptions, not only a network-wide average. |

Supporting measures:
- **Stockout Rate:** valid demand lines not fulfilled because of unavailable stock / all eligible valid demand lines.
- **FEFO Compliance:** eligible batch picks selecting the earliest-expiring eligible batch / all eligible batch picks.
- **Procurement Lead Time:** elapsed time between the explicitly defined procurement start and goods-received event; segment by supplier and order type.
- **Workflow Automation Rate:** eligible workflow instances completed through approved automation / all eligible workflow instances.
- **Hours Saved per Employee:** measured reduction in time for a defined task set, aggregated over a stated period.
- **Manual Operations Reduction:** reduction in count or share of defined manual steps per completed workflow.
- **Pharmacies Managed per Operator:** branches overseen per operator, interpreted with workload, risk and service-quality guardrails.

Do not use a metric name without its definition and denominator. Do not compare branches unless scope, data completeness and measurement windows are comparable.

## 6. Workflow automation and AI assistance

Workflow Automation spans pharmacist, pharmacy and network operations:
- automate repetitive administrative and document-handling steps where permitted;
- reduce duplicate manual data entry;
- support receiving, inventory, expiry and procurement workflows;
- coordinate and reconcile cross-branch processes;
- use AI to retrieve, compare, summarize and structure authorized information.

The domain article describes a representative AI-assisted interaction:

**Pharmacist request → access control → data retrieval → context retrieval → AI model → structured response → pharmacist review and decision.**

Required safeguards:
- enforce authorization before retrieving patient, prescription, inventory or branch data;
- preserve tenant and patient-context isolation;
- ground answers in authorized sources and expose citations where applicable;
- validate medication entities, strengths, dosage, form, route, frequency and negation where relevant;
- escalate uncertain, unsafe or out-of-scope requests;
- keep critical transaction rules deterministic and auditable;
- AI supports the pharmacist; it does not replace professional judgment or independently finalize critical pharmacy transactions.

AI Task Completion Rate must measure correctness and policy compliance, not merely whether an agent run or tool call returned successfully. Use the agent, RAG, citation, pharmacy-specific and security evaluations defined in the primary engineering benchmark.

## 7. Economic value without disclosing financial results

Financial outcomes are subject to NDA. Public CV and project documentation must not disclose revenue, profit, margin, monetary savings, unit economics or other confidential commercial results.

Operational proxies can demonstrate the mechanisms behind economic value without publishing financial figures:

| Value area | Non-financial measure |
|---|---|
| Staff time | Hours Saved per Employee |
| Service efficiency | Average Customer Service Time |
| Inventory loss control | Expired Stock Rate / Expired Units |
| Medicine availability | Product Availability Rate / Stockout Rate |
| Inventory efficiency | Inventory Turnover, with a defined unit and period |
| Stock-record quality | Inventory Accuracy |
| Automation | Manual Operations Reduction / Workflow Automation Rate |
| Network scalability | Pharmacies Managed per Operator, with workload and quality context |

These indicators do not automatically prove monetary savings. Any financial analysis remains internal and subject to NDA.

## 8. Evidence, implementation status and CV claims

Use the evidence labels from the primary benchmark for test and measurement reporting. For feature and workflow maturity, distinguish:
- **Designed** — requirement or design is documented.
- **Implemented** — implementation is present in the current codebase.
- **Tested** — relevant automated or manual verification has been executed.
- **Measured** — a metric has a reproducible result, defined environment and evidence.
- **Production-validated** — verified in production with appropriate safeguards, representative data and operational evidence.

These labels are not interchangeable. A planned capability, passing unit test, synthetic benchmark or local mock does not establish production impact.

For CV: use the six primary KPIs as business-value areas; describe capabilities as designed or implemented only when repository evidence supports the claim; state quantified improvements only when reproducible measurement supports them; keep NDA-covered financial results confidential; do not imply that the Medium article proves implementation or measured outcomes.

## 9. Relationship to engineering benchmarks

The primary engineering benchmark remains [ENGINEERING_BENCHMARK_REQUIREMENTS.md](../devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md). It governs technical measurement and evidence for backend/API, database, Redis and capacity performance; RAG retrieval and Ragas; citation correctness and pharmacy-specific quality; LangGraph, Agent Harness and MCP; security, privacy and tenant isolation; OpenTelemetry; frontend/E2E, load testing and release quality gates.

Business KPIs must be connected to observable events and data sources, but technical benchmark scores must not be presented as business outcomes. Conversely, business improvements must not be inferred from the existence of a technical feature.

## 10. Review and ownership

Before treating this as an approved measurement program:
1. assign a business owner and technical data owner to each KPI;
2. confirm definitions and denominators against the implemented domain model;
3. identify authoritative event/data sources and data-quality limitations;
4. collect a baseline using comparable workflows and periods;
5. approve targets with pharmacy operations and relevant reviewers;
6. implement dashboards/evaluators and auditability;
7. review results by branch, role and workflow where appropriate;
8. update this document and the benchmark report when definitions or evidence change.

No KPI target or achieved result is asserted by this working baseline.
