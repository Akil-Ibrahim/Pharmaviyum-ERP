# Python Core & Advanced Python — Question Map (EN)

**Language:** English  
**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Current coverage:** PY-001–PY-004 and FU-001–FU-016  
**Answer file:** [PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md](./PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md)  
**Russian version:** [RU Question Map](../RU/PYTHON_CORE_ADVANCED.md)

## PY-001 — GIL, Concurrency & Parallelism

**Main Question:** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency and parallelism?

**Evaluation focus:** CPython runtime synchronization, CPU-bound versus I/O-bound workloads, thread safety, concurrency-model selection, and free-threaded Python.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core / High interview frequency

Follow-ups:

- **FU-001 — Mechanism:** Why does the conventional CPython build use the GIL, and what does the lock actually protect?
- **FU-002 — Application:** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads in conventional CPython?
- **FU-003 — Design trade-offs:** How would you choose between threading, multiprocessing, and asyncio for a Python backend workload?
- **FU-004 — Senior judgment:** What changes in free-threaded CPython, and what should an engineering team verify before adopting it?

## PY-002 — Python Execution Model & Runtime

**Main Question:** How does Python execute a program from source code to runtime behavior?

**Evaluation focus:** Compilation, bytecode, interpreter/runtime model.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-005 — Mechanism:** What are the main stages between Python source code and the execution of its instructions in CPython?
- **FU-006 — Application:** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?
- **FU-007 — Edge cases and trade-offs:** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?
- **FU-008 — Senior judgment:** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?

## Coverage status

- PY-001–PY-004 and FU-001–FU-016: authored in English; independent technical and editorial review pending.
- Remaining Main Questions PY-004–PY-045 and FU-017–FU-184: not yet migrated into the language-separated structure.

**Allocation rule:** Every Main Question receives exactly four Follow-ups covering mechanism, practical application, edge cases/trade-offs, and senior-level judgment or production implications.


## PY-003 — Function Calls & Execution State

**Main Question:** What happens during a function call in CPython?

**Evaluation focus:** Call semantics, argument binding, function/code objects, execution state, frames, closures, return and exception paths.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-009 — Mechanism:** What execution state does CPython need to establish or maintain when entering and executing a Python function?
- **FU-010 — Application:** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?
- **FU-011 — Edge cases and lifecycle:** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?
- **FU-012 — Senior judgment:** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?



## PY-004 — Python Object Model: Identity, Type & Value

**Main Question:** Explain Python's object model: identity, type, and value.

**Evaluation focus:** Name binding, identity versus equality, mutability, type checks, and domain identity.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-013 — Mechanism:** Which of an object's identity, type, and value can change during its lifetime?
- **FU-014 — Application:** How would you choose between identity checks, equality checks, and type checks in a code review?
- **FU-015 — Edge cases and trade-offs:** Why can using is to compare strings, numbers, or other values produce unreliable results?
- **FU-016 — Senior judgment:** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types?

