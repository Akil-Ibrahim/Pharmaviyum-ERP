# Python Core & Advanced Python — Question Map (EN)

**Language:** English  
**Python baseline:** 3.15.2 — label version-specific behavior and distinguish Python language guarantees from CPython implementation details.  
**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Current coverage:** PY-001–PY-010 and FU-001–FU-040  
**Numbering rule:** Exactly four Follow-ups per Main Question; FU IDs are globally sequential and never reset between Main Questions.  
**Answer file:** [PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md](./PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md)  
**Russian version:** [RU Question Map](../RU/PYTHON_CORE_ADVANCED.md)

## PY-001 — GIL, Concurrency & Parallelism ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency and parallelism?

**Evaluation focus:** CPython runtime synchronization, CPU-bound versus I/O-bound workloads, thread safety, concurrency-model selection, and free-threaded Python.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core / High interview frequency

Follow-ups:

- **FU-001 — Mechanism:** Why does the conventional CPython build use the GIL, and what does the lock actually protect? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-002 — Application:** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads in conventional CPython? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-003 — Design trade-offs:** How would you choose between threading, multiprocessing, and asyncio for a Python backend workload? ![TYPE](https://img.shields.io/badge/TYPE-Design_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-004 — Senior judgment:** What changes in free-threaded CPython, and what should an engineering team verify before adopting it? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-002 — Concurrency vs Parallelism ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What is the difference between concurrency and parallelism, and why is the distinction important in Python?

**Evaluation focus:** Concurrency versus simultaneous execution, I/O-bound and CPU-bound workloads, and selecting an appropriate Python execution model.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-005 — Fundamentals:** Can concurrency exist without parallelism? ![TYPE](https://img.shields.io/badge/TYPE-Fundamentals-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-006 — Workload analysis:** What is the difference between I/O-bound and CPU-bound workloads? ![TYPE](https://img.shields.io/badge/TYPE-Workload_analysis-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-007 — CPython behavior:** How does the GIL affect concurrency and parallelism in CPython? ![TYPE](https://img.shields.io/badge/TYPE-CPython_behavior-64748b) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-008 — Senior judgment:** How do you decide whether a workload needs concurrency or parallelism? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-003 — Python Execution Model & Runtime ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does Python execute a program from source code to runtime behavior?

**Evaluation focus:** Compilation, bytecode, interpreter/runtime model.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-009 — Mechanism:** What are the main stages between Python source code and the execution of its instructions in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-010 — Application:** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-011 — Edge cases and trade-offs:** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-012 — Senior judgment:** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## Coverage status

- PY-001–PY-009 and FU-001–FU-036: authored in English; independent technical and editorial review pending.
- Remaining Main Questions PY-010–PY-045 and FU-037–FU-180: not yet authored in the language-separated structure.

**Allocation rule:** Every Main Question receives exactly four Follow-ups covering mechanism, practical application, edge cases/trade-offs, and senior-level judgment or production implications.


## PY-004 — Function Calls & Execution State ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What happens during a function call in CPython?

**Evaluation focus:** Call semantics, argument binding, function/code objects, execution state, frames, closures, return and exception paths.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-013 — Mechanism:** What execution state does CPython need to establish or maintain when entering and executing a Python function? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-014 — Application:** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-015 — Edge cases and lifecycle:** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-016 — Senior judgment:** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-005 — Python Object Model: Identity, Type & Value ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's object model: identity, type, and value.

**Evaluation focus:** Name binding, identity versus equality, mutability, type checks, and domain identity.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-017 — Mechanism:** Which of an object's identity, type, and value can change during its lifetime? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-018 — Application:** How would you choose between identity checks, equality checks, and type checks in a code review? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-019 — Edge cases and trade-offs:** Why can using is to compare strings, numbers, or other values produce unreliable results? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-020 — Senior judgment:** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-006 — Attribute Lookup, Descriptors & Special Methods ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does Python resolve attribute access, and how do descriptors and special methods affect that process?

**Evaluation focus:** Attribute lookup precedence, descriptor protocol, attribute access hooks, method binding, and implicit special-method lookup.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-021 — Mechanism:** In what order does Python search for an attribute on an instance, and how can an instance attribute interact with a class attribute? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-022 — Mechanism and application:** What is the difference between a data descriptor and a non-data descriptor, and why does the distinction matter? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism_and_application-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-023 — Edge cases:** What is the difference between `__getattribute__` and `__getattr__`, and what risks arise when overriding them? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-024 — Senior judgment:** Why can assigning a special method to an instance fail to change the behavior of an implicit operation such as `len(obj)`? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-007 — Built-in Collections: Semantics & Selection ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

**Evaluation focus:** Collection contracts, mutability, ordering, hashability, typical complexity, and memory/performance trade-offs.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-025 — Mechanism:** What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-026 — Application:** How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-027 — Edge cases and trade-offs:** What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-028 — Senior judgment:** How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)


## PY-008 — Dictionary Internals & Hash Tables ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python dictionaries work internally, and what are the performance and correctness implications of hash-table behavior?

**Evaluation focus:** Hashing, equality, collision resolution, resizing, complexity, and custom-key correctness.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-029 — Core contract:** What contract must __hash__() and __eq__() satisfy for objects used as dictionary keys? ![TYPE](https://img.shields.io/badge/TYPE-Core_contract-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-030 — Internal mechanism:** What happens when dictionary keys collide, and why can insertion or lookup become slower? ![TYPE](https://img.shields.io/badge/TYPE-Internal_mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-031 — Correctness and design:** Why is it dangerous to use a mutable object as a dictionary key, and how should a custom key type be designed? ![TYPE](https://img.shields.io/badge/TYPE-Correctness_and_design-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-032 — Security and production:** How does hash randomization help protect Python services, and why should hash() not be used as a persistent identifier? ![TYPE](https://img.shields.io/badge/TYPE-Security_and_production-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-009 — Memory Management & Garbage Collection ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does memory management work in Python, and how do reference counting and garbage collection interact?

**Evaluation focus:** Object lifetime, strong references, reachability, reference counting, cyclic GC, deterministic resource cleanup, and production memory diagnostics.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-033 — Mechanism:** What is the difference between reference counting and cyclic garbage collection in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-034 — Reachability:** Why can a reference cycle remain in memory even when the application no longer uses any of its objects? ![TYPE](https://img.shields.io/badge/TYPE-Reachability-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-035 — Resource lifecycle:** Does using del or defining __del__() guarantee that an object or its resources are released immediately? ![TYPE](https://img.shields.io/badge/TYPE-Resource_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-036 — Production diagnosis:** How would you investigate steadily increasing memory usage in a long-running Python service? ![TYPE](https://img.shields.io/badge/TYPE-Production_diagnosis-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-010 — Weak References, Object Lifetime & Memory Ownership ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What are weak references in Python, how do they differ from strong references, and when should they be used?

**Evaluation focus:** Strong versus weak reachability, the `weakref` API, weak containers, weak-referenceable types, object ownership, caches, observer registries, and finalization pitfalls.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-037 — Mechanism:** What exactly changes in an object's lifetime when a strong reference is replaced by a weak reference? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-038 — Application:** When would you choose a `WeakValueDictionary`, a `WeakKeyDictionary`, or a `WeakSet` in a real application? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-039 — Edge cases:** Can every Python object be weakly referenced, and what should you check when a class uses `__slots__`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-040 — Senior judgment:** How would you design a weak-reference-based registry without introducing a new memory leak or unreliable cleanup behavior? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-011 — Context Managers, Resource Management & RAII ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python context managers work, how do they provide deterministic resource management, and how do they compare with RAII?

**Evaluation focus:** Context manager protocol, `with` execution lifecycle, exception propagation and suppression, deterministic cleanup, synchronous and asynchronous contexts, `contextlib`, exit stacks, partial acquisition, and RAII distinctions.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-041 — Mechanism:** What exactly happens when a `with` block exits because of an exception? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-042 — Application:** When should you use `ExitStack` instead of nested `with` statements? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-043 — Edge cases:** What happens if `__enter__()` fails, or if `__exit__()` itself raises? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-044 — Senior judgment:** How would you design reliable resource management in a synchronous and asynchronous backend? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-012 — Exception Handling, Exception Hierarchy & Exception Groups ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's exception hierarchy and exception-handling model. How do propagation, exception chaining, and exception groups work?

**Evaluation focus:** `BaseException` versus `Exception`, selective exception handling, `try/except/else/finally`, propagation and termination semantics, exception chaining, custom exception design, `ExceptionGroup`, and `except*`.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-045 — Mechanism:** Why should application code usually catch `Exception` rather than `BaseException`? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-046 — Application:** How should a backend translate a low-level exception into a domain-level or API error? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-047 — Edge cases:** What is the difference between `__cause__`, `__context__`, and `raise ... from None`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-048 — Senior judgment:** When should you use `ExceptionGroup` and `except*` in concurrent systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
