# Python Core & Advanced Python — Question Map (EN)

**Language:** English  
**Python baseline:** 3.15.2 — label version-specific behavior and distinguish Python language guarantees from CPython implementation details.  
**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Current coverage:** PY-001–PY-019; 19 Main Questions and 76 Follow-ups (FU-1–FU-4 per Main Question)  
**Numbering rule:** Exactly four Follow-ups per Main Question, locally numbered FU-1 through FU-4. Follow-ups are nested under their parent PY question.  
**Answer file:** [PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md](./PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md)  
**Russian version:** [RU Question Map](../RU/PYTHON_CORE_ADVANCED.md)

## Technical Entity Badge Registry — PY-001

Use the same entity badge and color whenever the entity appears in this curriculum. Badges identify technical concepts; they do not replace definitions or question-type badges.

- ![ENTITY: GIL](https://img.shields.io/badge/ENTITY-GIL-2563eb) — GIL
- ![ENTITY: Thread](https://img.shields.io/badge/ENTITY-Thread-16a34a) — Thread
- ![ENTITY: Process](https://img.shields.io/badge/ENTITY-Process-7c3aed) — Process
- ![ENTITY: Multithreading](https://img.shields.io/badge/ENTITY-Multithreading-16a34a) — Multithreading
- ![ENTITY: Multiprocessing](https://img.shields.io/badge/ENTITY-Multiprocessing-7c3aed) — Multiprocessing
- ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) — Concurrency
- ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) — Parallelism
- ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) — CPU-bound
- ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) — I/O-bound
- ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b) — CPython
- ![ENTITY: Python Bytecode](https://img.shields.io/badge/ENTITY-Python-Bytecode-64748b) — Python Bytecode
- ![ENTITY: Native Extension](https://img.shields.io/badge/ENTITY-Native-Extension-0f766e) — Native Extension
- ![ENTITY: Mutex](https://img.shields.io/badge/ENTITY-Mutex-be123c) — Mutex
- ![ENTITY: Condition Variable](https://img.shields.io/badge/ENTITY-Condition-Variable-be123c) — Condition Variable
- ![ENTITY: Lock](https://img.shields.io/badge/ENTITY-Lock-be123c) — Lock
- ![ENTITY: Free-threaded](https://img.shields.io/badge/ENTITY-Free-threaded-0f766e) — Free-threaded
- ![ENTITY: Asyncio](https://img.shields.io/badge/ENTITY-Asyncio-0891b2) — Asyncio
- ![ENTITY: Task](https://img.shields.io/badge/ENTITY-Task-0ea5e9) — Task
- ![ENTITY: Synchronization](https://img.shields.io/badge/ENTITY-Synchronization-be123c) — Synchronization
- ![ENTITY: Thread Safety](https://img.shields.io/badge/ENTITY-Thread-Safety-16a34a) — Thread Safety
- ![ENTITY: Shared State](https://img.shields.io/badge/ENTITY-Shared-State-d97706) — Shared State

## PY-001 — GIL ![ENTITY: GIL](https://img.shields.io/badge/ENTITY-GIL-2563eb), Concurrency & Parallelism ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What is the Global Interpreter Lock (GIL) in CPython ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b), and how does it affect concurrency ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) and parallelism ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706)?

**Evaluation focus:** CPython runtime synchronization, CPU-bound ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) versus I/O-bound ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) workloads, thread safety ![ENTITY: Thread Safety](https://img.shields.io/badge/ENTITY-Thread-Safety-16a34a), concurrency-model selection, and free-threaded ![ENTITY: Free-threaded](https://img.shields.io/badge/ENTITY-Free-threaded-0f766e) Python.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core / High interview frequency

Follow-ups:

- **FU-1 — Mechanism:** Why does the conventional CPython build use the GIL, and what does the lock actually protect? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads in conventional CPython? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Design trade-offs:** How would you choose between threading ![ENTITY: Multithreading](https://img.shields.io/badge/ENTITY-Multithreading-16a34a), multiprocessing ![ENTITY: Multiprocessing](https://img.shields.io/badge/ENTITY-Multiprocessing-7c3aed), and asyncio ![ENTITY: Asyncio](https://img.shields.io/badge/ENTITY-Asyncio-0891b2) for a Python backend workload? ![TYPE](https://img.shields.io/badge/TYPE-Design_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** What changes in free-threaded CPython, and what should an engineering team verify before adopting it? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-002 — Concurrency vs Parallelism ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What is the difference between concurrency ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) and parallelism ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706), and why is the distinction important in Python?

**Evaluation focus:** Concurrency versus simultaneous execution, I/O-bound ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) and CPU-bound ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) workloads, and selecting an appropriate Python execution model.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Fundamentals:** Can concurrency exist without parallelism? ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Fundamentals-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Workload analysis:** What is the difference between I/O-bound and CPU-bound workloads? ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Workload_analysis-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — CPython ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b) behavior:** How does the GIL ![ENTITY: GIL](https://img.shields.io/badge/ENTITY-GIL-2563eb) affect concurrency and parallelism in CPython? ![TYPE](https://img.shields.io/badge/TYPE-CPython_behavior-64748b) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** How do you decide whether a workload needs concurrency or parallelism? ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-003 — Python Execution Model & Runtime ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does Python execute a program from source code to runtime behavior?

**Evaluation focus:** Compilation, bytecode, interpreter/runtime model.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What are the main stages between Python source code and the execution of its instructions in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases and trade-offs:** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## Coverage status

- PY-001–PY-019 and their 76 locally numbered Follow-ups (FU-1–FU-4 per Main Question): authored in English; independent technical and editorial review pending.
- Remaining Main Questions PY-020–PY-045 and their 104 Follow-ups: not yet authored in the language-separated structure.

**Allocation rule:** Every Main Question receives exactly four Follow-ups covering mechanism, practical application, edge cases/trade-offs, and senior-level judgment or production implications.


## PY-004 — Function Calls & Execution State ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What happens during a function call in CPython?

**Evaluation focus:** Call semantics, argument binding, function/code objects, execution state, frames, closures, return and exception paths.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What execution state does CPython need to establish or maintain when entering and executing a Python function? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases and lifecycle:** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-005 — Python Object Model: Identity, Type & Value ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's object model: identity, type, and value.

**Evaluation focus:** Name binding, identity versus equality, mutability, type checks, and domain identity.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** Which of an object's identity, type, and value can change during its lifetime? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How would you choose between identity checks, equality checks, and type checks in a code review? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases and trade-offs:** Why can using is to compare strings, numbers, or other values produce unreliable results? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-006 — Attribute Lookup, Descriptors & Special Methods ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does Python resolve attribute access, and how do descriptors and special methods affect that process?

**Evaluation focus:** Attribute lookup precedence, descriptor protocol, attribute access hooks, method binding, and implicit special-method lookup.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** In what order does Python search for an attribute on an instance, and how can an instance attribute interact with a class attribute? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Mechanism and application:** What is the difference between a data descriptor and a non-data descriptor, and why does the distinction matter? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism_and_application-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** What is the difference between `__getattribute__` and `__getattr__`, and what risks arise when overriding them? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** Why can assigning a special method to an instance fail to change the behavior of an implicit operation such as `len(obj)`? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-007 — Built-in Collections: Semantics & Selection ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

**Evaluation focus:** Collection contracts, mutability, ordering, hashability, typical complexity, and memory/performance trade-offs.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases and trade-offs:** What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)


## PY-008 — Dictionary Internals & Hash Tables ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python dictionaries work internally, and what are the performance and correctness implications of hash-table behavior?

**Evaluation focus:** Hashing, equality, collision resolution, resizing, complexity, and custom-key correctness.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Core contract:** What contract must __hash__() and __eq__() satisfy for objects used as dictionary keys? ![TYPE](https://img.shields.io/badge/TYPE-Core_contract-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Internal mechanism:** What happens when dictionary keys collide, and why can insertion or lookup become slower? ![TYPE](https://img.shields.io/badge/TYPE-Internal_mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Correctness and design:** Why is it dangerous to use a mutable object as a dictionary key, and how should a custom key type be designed? ![TYPE](https://img.shields.io/badge/TYPE-Correctness_and_design-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Security and production:** How does hash randomization help protect Python services, and why should hash() not be used as a persistent identifier? ![TYPE](https://img.shields.io/badge/TYPE-Security_and_production-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-009 — Memory Management & Garbage Collection ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How does memory management work in Python, and how do reference counting and garbage collection interact?

**Evaluation focus:** Object lifetime, strong references, reachability, reference counting, cyclic GC, deterministic resource cleanup, and production memory diagnostics.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What is the difference between reference counting and cyclic garbage collection in CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Reachability:** Why can a reference cycle remain in memory even when the application no longer uses any of its objects? ![TYPE](https://img.shields.io/badge/TYPE-Reachability-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Resource lifecycle:** Does using del or defining __del__() guarantee that an object or its resources are released immediately? ![TYPE](https://img.shields.io/badge/TYPE-Resource_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Production diagnosis:** How would you investigate steadily increasing memory usage in a long-running Python service? ![TYPE](https://img.shields.io/badge/TYPE-Production_diagnosis-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-010 — Weak References, Object Lifetime & Memory Ownership ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** What are weak references in Python, how do they differ from strong references, and when should they be used?

**Evaluation focus:** Strong versus weak reachability, the `weakref` API, weak containers, weak-referenceable types, object ownership, caches, observer registries, and finalization pitfalls.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What exactly changes in an object's lifetime when a strong reference is replaced by a weak reference? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** When would you choose a `WeakValueDictionary`, a `WeakKeyDictionary`, or a `WeakSet` in a real application? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** Can every Python object be weakly referenced, and what should you check when a class uses `__slots__`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** How would you design a weak-reference-based registry without introducing a new memory leak or unreliable cleanup behavior? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-011 — Context Managers, Resource Management & RAII ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** How do Python context managers work, how do they provide deterministic resource management, and how do they compare with RAII?

**Evaluation focus:** Context manager protocol, `with` execution lifecycle, exception propagation and suppression, deterministic cleanup, synchronous and asynchronous contexts, `contextlib`, exit stacks, partial acquisition, and RAII distinctions.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What exactly happens when a `with` block exits because of an exception? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** When should you use `ExitStack` instead of nested `with` statements? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** What happens if `__enter__()` fails, or if `__exit__()` itself raises? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** How would you design reliable resource management in a synchronous and asynchronous backend? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-012 — Exception Handling, Exception Hierarchy & Exception Groups ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's exception hierarchy and exception-handling model. How do propagation, exception chaining, and exception groups work?

**Evaluation focus:** `BaseException` versus `Exception`, selective exception handling, `try/except/else/finally`, propagation and termination semantics, exception chaining, custom exception design, `ExceptionGroup`, and `except*`.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** Why should application code usually catch `Exception` rather than `BaseException`? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How should a backend translate a low-level exception into a domain-level or API error? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** What is the difference between `__cause__`, `__context__`, and `raise ... from None`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** When should you use `ExceptionGroup` and `except*` in concurrent systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-013 — Iterators, Generators & Lazy Evaluation ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's iteration model. What is the difference between an iterable, an iterator, and a generator, and how do generators enable lazy evaluation?

**Evaluation focus:** Iterable versus iterator, iterator protocol (`__iter__` / `__next__`), exhaustion and `StopIteration`, generator creation and suspension, generator expressions versus eager comprehensions, lazy evaluation, `send()` / `throw()` / `close()`, `yield from`, PEP 479, asynchronous iteration and generator cleanup, streaming and resource lifecycle.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** What is the difference between an iterable and an iterator, and why is an iterator usually stateful? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** When would you choose a generator instead of a list in a backend data-processing pipeline? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** What happens when `StopIteration` is raised inside a generator, and how does `yield from` handle delegation? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** What production risks should you consider when using generators and asynchronous generators for resource-backed streams? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-014 — Decorators, Closures & Function Wrapping ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain how Python decorators work. How are decorators related to closures and function wrappers, and what production concerns should you consider?

**Evaluation focus:** Decorator application and definition-time evaluation, callable transformation, wrapper execution, closure and free-variable semantics, `nonlocal` versus `global`, decorator factories, `functools.wraps` / `__wrapped__`, decorator stacking order, async-aware wrappers, mutable closure state and concurrency, exception and return-value preservation.  
**Level:** L3 — Advanced/Senior  
**Priority:** P0 — Core

Follow-ups:

- **FU-1 — Mechanism:** How does Python apply a decorator, and when is the decorator executed? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** How would you implement a configurable decorator for logging, retries, or access control? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** What is a closure, how does `nonlocal` work, and what problems can mutable closure state introduce? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** Why are `functools.wraps`, decorator order, and async-aware wrappers important in production systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-015 — Scope, LEGB Rule & Name Resolution** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Mechanism:** How does Python apply LEGB, and how are local names determined? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Application:** How would you diagnose UnboundLocalError and choose local, global, or nonlocal? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Edge cases:** Why do methods not close over class namespaces, and what is late binding? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior judgment:** How should senior engineers manage scope and dynamic name resolution in production? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-016 — Mutable vs Immutable Objects, Aliasing & Object Sharing** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Mechanism:** What is the difference between mutation, rebinding, and aliasing? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Application:** How do shallow copy and deep copy differ, and when would you use each? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Edge cases:** Why can a tuple contain mutable state, and what happens when mutable objects are passed to functions? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior judgment:** How do you prevent unintended shared mutable state in production systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-017 — Python Argument Passing, Parameter Semantics & Function Signatures** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Mechanism:** How does Python bind positional and keyword arguments, and which errors can occur? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Application:** When should an API use positional-only and keyword-only parameters? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Edge cases:** Why are mutable defaults dangerous, and what is the role of annotations? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior judgment:** How do you inspect and validate callable signatures in frameworks and production tooling? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-018 — Python Functions: First-Class Objects, Higher-Order Functions & Functional Programming** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Mechanism:** What makes a function a first-class object, and how is that different from a callable? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Application:** How would you use higher-order functions in a backend application? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Edge cases:** What are closure late binding and shared mutable state risks? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior judgment:** When should you choose functional composition over classes or imperative code? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)


## PY-019 — Lambda Functions, Anonymous Functions & Functional Idioms ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2--L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P1-d97706)

**Main Question:** What are lambda expressions in Python, how do they work, and when should you use them instead of named functions?

**Evaluation focus:** Lambda syntax and semantics, function objects, expression-only bodies, closures, practical callback use, readability, and choosing between lambda, def, and built-in idioms.  
**Level:** L2–L3 — Intermediate/Advanced  
**Priority:** P1 — Important Python Core topic

Follow-ups:

- **FU-1 — Mechanism:** What function object does a lambda expression create, and how does its body differ from a function defined with def? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Application:** Where are lambda functions useful in Python APIs and data transformations? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Edge cases:** How do lambda expressions interact with closures, late binding, default arguments, and introspection? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior judgment:** When should you replace a lambda with a named function or a clearer built-in expression? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
