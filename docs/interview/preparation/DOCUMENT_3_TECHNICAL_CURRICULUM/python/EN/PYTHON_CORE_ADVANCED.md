# Python Core & Advanced Python — Question Map (EN)

**Language:** English  
**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Current coverage:** PY-001–PY-002 and FU-001–FU-008  
**Answer file:** [PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md](./PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md)  
**Russian version:** [RU Question Map](../RU/PYTHON_CORE_ADVANCED.md)

## PY-001 — Python Execution Model & Runtime

**Main Question:** How does Python execute a program from source code to runtime behavior?

**Evaluation focus:** Compilation, bytecode, interpreter/runtime model.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-001 — Mechanism:** What are the main stages between Python source code and the execution of its instructions in CPython?
- **FU-002 — Application:** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?
- **FU-003 — Edge cases and trade-offs:** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?
- **FU-004 — Senior judgment:** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?

## Coverage status

- PY-001: authored in English; independent technical and editorial review pending.
- FU-001–FU-004: authored in English; independent technical and editorial review pending.
- PY-002 and FU-005–FU-008: authored in English; independent technical and editorial review pending.
- Remaining Main Questions PY-003–PY-045 and FU-009–FU-180: not yet migrated into the language-separated structure.

**Allocation rule:** Every Main Question receives exactly four Follow-ups covering mechanism, practical application, edge cases/trade-offs, and senior-level judgment or production implications.


## PY-002 — Function Calls & Execution State

**Main Question:** What happens during a function call in CPython?

**Evaluation focus:** Call semantics, argument binding, function/code objects, execution state, frames, closures, return and exception paths.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-005 — Mechanism:** What execution state does CPython need to establish or maintain when entering and executing a Python function?
- **FU-006 — Application:** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?
- **FU-007 — Edge cases and lifecycle:** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?
- **FU-008 — Senior judgment:** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?
