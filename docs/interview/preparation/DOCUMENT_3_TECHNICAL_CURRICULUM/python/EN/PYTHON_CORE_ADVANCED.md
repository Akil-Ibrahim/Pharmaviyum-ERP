# Python Core & Advanced Python — Question Map (EN)

**Language:** English  
**Python baseline:** 3.15.2 — label version-specific behavior and distinguish Python language guarantees from CPython implementation details.  
**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Current coverage:** PY-001–PY-009 and FU-001–FU-036  
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

## PY-002 — Concurrency vs Parallelism

**Main Question:** What is the difference between concurrency and parallelism, and why is the distinction important in Python?

**Evaluation focus:** Concurrency versus simultaneous execution, I/O-bound and CPU-bound workloads, and selecting an appropriate Python execution model.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-005 — Fundamentals:** Can concurrency exist without parallelism?
- **FU-006 — Workload analysis:** What is the difference between I/O-bound and CPU-bound workloads?
- **FU-007 — CPython behavior:** How does the GIL affect concurrency and parallelism in CPython?
- **FU-008 — Senior judgment:** How do you decide whether a workload needs concurrency or parallelism?

## PY-003 — Python Execution Model & Runtime

**Main Question:** How does Python execute a program from source code to runtime behavior?

**Evaluation focus:** Compilation, bytecode, interpreter/runtime model.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-009 — Mechanism:** What are the main stages between Python source code and the execution of its instructions in CPython?
- **FU-010 — Application:** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?
- **FU-011 — Edge cases and trade-offs:** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?
- **FU-012 — Senior judgment:** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?

## Coverage status

- PY-001–PY-009 and FU-001–FU-036: authored in English; independent technical and editorial review pending.
- Remaining Main Questions PY-010–PY-045 and FU-037–FU-180: not yet authored in the language-separated structure.

**Allocation rule:** Every Main Question receives exactly four Follow-ups covering mechanism, practical application, edge cases/trade-offs, and senior-level judgment or production implications.


## PY-004 — Function Calls & Execution State

**Main Question:** What happens during a function call in CPython?

**Evaluation focus:** Call semantics, argument binding, function/code objects, execution state, frames, closures, return and exception paths.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-013 — Mechanism:** What execution state does CPython need to establish or maintain when entering and executing a Python function?
- **FU-014 — Application:** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?
- **FU-015 — Edge cases and lifecycle:** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?
- **FU-016 — Senior judgment:** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?



## PY-005 — Python Object Model: Identity, Type & Value

**Main Question:** Explain Python's object model: identity, type, and value.

**Evaluation focus:** Name binding, identity versus equality, mutability, type checks, and domain identity.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-017 — Mechanism:** Which of an object's identity, type, and value can change during its lifetime?
- **FU-018 — Application:** How would you choose between identity checks, equality checks, and type checks in a code review?
- **FU-019 — Edge cases and trade-offs:** Why can using is to compare strings, numbers, or other values produce unreliable results?
- **FU-020 — Senior judgment:** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types?

## PY-006 — Attribute Lookup, Descriptors & Special Methods

**Main Question:** How does Python resolve attribute access, and how do descriptors and special methods affect that process?

**Evaluation focus:** Attribute lookup precedence, descriptor protocol, attribute access hooks, method binding, and implicit special-method lookup.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-021 — Mechanism:** In what order does Python search for an attribute on an instance, and how can an instance attribute interact with a class attribute?
- **FU-022 — Mechanism and application:** What is the difference between a data descriptor and a non-data descriptor, and why does the distinction matter?
- **FU-023 — Edge cases:** What is the difference between `__getattribute__` and `__getattr__`, and what risks arise when overriding them?
- **FU-024 — Senior judgment:** Why can assigning a special method to an instance fail to change the behavior of an implicit operation such as `len(obj)`?



## PY-007 — Built-in Collections: Semantics & Selection

**Main Question:** How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

**Evaluation focus:** Collection contracts, mutability, ordering, hashability, typical complexity, and memory/performance trade-offs.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-025 — Mechanism:** What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython?
- **FU-026 — Application:** How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service?
- **FU-027 — Edge cases and trade-offs:** What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity?
- **FU-028 — Senior judgment:** How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy?


## PY-008 — Dictionary Internals & Hash Tables

**Main Question:** How do Python dictionaries work internally, and what are the performance and correctness implications of hash-table behavior?

**Evaluation focus:** Hashing, equality, collision resolution, resizing, complexity, and custom-key correctness.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-029 — Core contract:** What contract must __hash__() and __eq__() satisfy for objects used as dictionary keys?
- **FU-030 — Internal mechanism:** What happens when dictionary keys collide, and why can insertion or lookup become slower?
- **FU-031 — Correctness and design:** Why is it dangerous to use a mutable object as a dictionary key, and how should a custom key type be designed?
- **FU-032 — Security and production:** How does hash randomization help protect Python services, and why should hash() not be used as a persistent identifier?

## PY-009 — Memory Management & Garbage Collection

**Main Question:** How does memory management work in Python, and how do reference counting and garbage collection interact?

**Evaluation focus:** Object lifetime, strong references, reachability, reference counting, cyclic GC, deterministic resource cleanup, and production memory diagnostics.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-033 — Mechanism:** What is the difference between reference counting and cyclic garbage collection in CPython?
- **FU-034 — Reachability:** Why can a reference cycle remain in memory even when the application no longer uses any of its objects?
- **FU-035 — Resource lifecycle:** Does using del or defining __del__() guarantee that an object or its resources are released immediately?
- **FU-036 — Production diagnosis:** How would you investigate steadily increasing memory usage in a long-running Python service?
