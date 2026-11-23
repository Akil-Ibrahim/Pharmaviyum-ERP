# Python Core & Advanced Python — Question Map

**Domain allocation:** 45 Main Questions + 180 Follow-ups = 225  
**Status:** Working question map; answers are authored separately and remain incomplete until reviewed.  
**Standard:** [Document 1](../../DOCUMENT_1_INTERVIEW_STANDARD.md) · [Architecture](../../DOCUMENT_2_CURRICULUM_ARCHITECTURE.md)

## Competency allocation

| # | Competency group | Main questions | IDs |
|---:|---|---:|---|
| 1 | Python Execution Model & Runtime | 2 | PY-001–PY-002 |
| 2 | Python Object & Data Model | 3 | PY-003–PY-005 |
| 3 | Built-in Types & Collections | 3 | PY-006–PY-008 |
| 4 | Mutability, Hashing & Equality | 3 | PY-009–PY-011 |
| 5 | Functions, Scope & Closures | 3 | PY-012–PY-014 |
| 6 | Decorators | 2 | PY-015–PY-016 |
| 7 | Iterators & Generators | 3 | PY-017–PY-019 |
| 8 | OOP, Inheritance & MRO | 3 | PY-020–PY-022 |
| 9 | Descriptors, Properties & \`__slots__\` | 2 | PY-023–PY-024 |
| 10 | Exceptions & Context Managers | 3 | PY-025–PY-027 |
| 11 | Type Hints, Protocols & Dataclasses | 3 | PY-028–PY-030 |
| 12 | Memory Management & Garbage Collection | 3 | PY-031–PY-033 |
| 13 | Concurrency, GIL, Threads & Multiprocessing | 4 | PY-034–PY-037 |
| 14 | Asyncio & Asynchronous Programming | 4 | PY-038–PY-041 |
| 15 | Modules, Imports, Packaging & Performance | 4 | PY-042–PY-045 |
| | **Total** | **45** | **PY-001–PY-045** |

## Main question map

Each Main Question receives exactly four follow-ups, with a distinct focus on:
1. mechanism and internal behavior;
2. application and practical engineering use;
3. edge cases, failure modes, and trade-offs;
4. senior-level judgment, production implications, or version-specific behavior.

| ID | Main question (EN) | Primary evaluation focus | Level | Priority |
|---|---|---|---|---|
| PY-001 | How does Python execute a program from source code to runtime behavior? | Compilation, bytecode, interpreter/runtime model | L3 | P0 |
| PY-002 | What happens during a function call in CPython? | Frames, evaluation, call semantics, implementation details | L3 | P1 |
| PY-003 | Explain Python's object model: identity, type, and value. | Object identity and data model | L2 | P0 |
| PY-004 | How do attribute lookup and special methods work in Python? | Data model and special method dispatch | L3 | P0 |
| PY-005 | What is the difference between \`__new__\` and \`__init__\`? | Object construction and initialization | L3 | P1 |
| PY-006 | How do Python lists, tuples, sets, and dictionaries differ internally and semantically? | Built-in collection behavior and selection | L2 | P0 |
| PY-007 | How do dictionaries work, and what are the implications of hash-table behavior? | Hash tables, lookup, collision handling | L3 | P0 |
| PY-008 | How do list and dictionary comprehensions behave, including their scope and performance characteristics? | Comprehensions, scope, allocation | L2 | P1 |
| PY-009 | What does mutability mean in Python, and how does aliasing create bugs? | Mutability, references, shared state | L2 | P0 |
| PY-010 | What are the equality and hashing contracts, and why must they remain consistent? | \`__eq__\`, \`__hash__\`, hashability | L3 | P0 |
| PY-011 | Why are mutable objects generally unsuitable as dictionary keys or set members? | Hash invariants and collection correctness | L3 | P0 |
| PY-012 | Explain Python's LEGB name-resolution rule and scope behavior. | Name binding and scope | L2 | P0 |
| PY-013 | What are closures, and how does Python capture variables in nested functions? | Closures, cells, late binding | L3 | P1 |
| PY-014 | What are the differences between positional, keyword-only, variadic, and default arguments? | Function signatures and API design | L2 | P0 |
| PY-015 | How do decorators work, and what happens when Python applies one? | Higher-order functions and decoration semantics | L3 | P0 |
| PY-016 | How do you design decorators that preserve metadata and support arguments? | Descriptor interaction, wrappers, \`functools\` | L3 | P1 |
| PY-017 | What is the iterator protocol, and how does iteration work in Python? | \`iter\`, \`next\`, iteration protocol | L2 | P0 |
| PY-018 | How do generators work, including \`yield\`, suspension, and resumption? | Generator state and lazy evaluation | L3 | P0 |
| PY-019 | When should you use generators instead of materialized collections? | Streaming, memory, backpressure, trade-offs | L3 | P1 |
| PY-020 | How does Python's method resolution order work in multiple inheritance? | C3 linearization and MRO | L3 | P0 |
| PY-021 | How do inheritance and composition differ, and when should each be preferred? | Object-oriented design and coupling | L3 | P0 |
| PY-022 | How do polymorphism, abstract base classes, and duck typing relate? | Substitutability and interface design | L3 | P1 |
| PY-023 | What are descriptors, and how do they participate in attribute access? | Descriptor protocol and lookup precedence | L4 | P1 |
| PY-024 | What does \`__slots__\` change, and what trade-offs does it introduce? | Instance layout, memory, inheritance constraints | L3 | P1 |
| PY-025 | How does Python's exception hierarchy and exception propagation work? | Exception semantics and error boundaries | L2 | P0 |
| PY-026 | How should exceptions be chained, handled, and translated across application layers? | Error contracts and observability | L3 | P0 |
| PY-027 | How do context managers work, and how do you implement reliable resource cleanup? | \`with\`, \`__enter__\`, \`__exit__\`, cleanup | L3 | P0 |
| PY-028 | What do Python type hints provide, and what do they not enforce at runtime? | Static typing boundaries | L2 | P0 |
| PY-029 | What is the difference between nominal and structural typing, including Protocols? | Protocols, subtyping, API contracts | L3 | P1 |
| PY-030 | When should you use dataclasses, and what design trade-offs do they introduce? | Generated methods, mutability, equality, API modeling | L2 | P1 |
| PY-031 | How does CPython manage object memory and object lifetime? | Reference counting and allocator concepts | L3 | P0 |
| PY-032 | How does cyclic garbage collection work, and what does it not collect? | Generational/cyclic GC concepts and limitations | L3 | P1 |
| PY-033 | How do memory leaks and unbounded memory growth arise in long-running Python services? | Retention, caches, references, profiling | L4 | P0 |
| PY-034 | What is the GIL, and how does it affect Python thread execution? | GIL semantics and version/build qualification | L3 | P0 |
| PY-035 | When should you use threads, processes, or asynchronous I/O? | Concurrency model selection | L3 | P0 |
| PY-036 | How do race conditions and synchronization problems arise in Python applications? | Shared state, locks, atomicity assumptions | L3 | P0 |
| PY-037 | What changes with free-threaded CPython, and how should engineers reason about compatibility? | Version/build-specific concurrency and ecosystem readiness | L4 | P1 |
| PY-038 | How does the asyncio event loop schedule and execute coroutines? | Coroutine lifecycle and cooperative scheduling | L3 | P0 |
| PY-039 | What is the difference between a coroutine, Task, and Future? | Async abstractions and lifecycle | L3 | P0 |
| PY-040 | How should cancellation, timeouts, and exceptions be handled in asyncio? | Structured concurrency, cancellation safety | L4 | P0 |
| PY-041 | How do you prevent blocking operations from degrading an async application? | Event-loop blocking, executors, async boundaries | L3 | P0 |
| PY-042 | How does Python's import system work, including module caching and circular imports? | Import machinery and module lifecycle | L3 | P1 |
| PY-043 | How should Python packages and dependencies be structured for reliable deployment? | Packaging, environments, reproducibility | L2 | P1 |
| PY-044 | How do you profile and optimize a Python application without premature optimization? | Profiling, bottleneck analysis, measurement | L3 | P0 |
| PY-045 | How do you investigate Python performance across CPU, memory, I/O, and concurrency? | End-to-end performance diagnosis | L4 | P0 |

## Follow-up map and answer status

Follow-up IDs are assigned sequentially from FU-001 to FU-180, four per Main Question, in the order defined above. For each parent question, the four follow-ups must cover mechanism, application, edge cases/trade-offs, and senior judgment. The detailed interviewer wording and substantive answers are to be authored and technically reviewed in the question records.

**Important:** this map records the 45-question allocation and stable IDs. It does not claim that the 180 follow-up wordings or any of the 225 answers are complete.


## Audit findings — 23 November 2026

**Audit status:** structural audit completed; question wording refinements and detailed follow-ups are being authored in controlled batches. The 45 Main Question allocation and the 180 Follow-up target remain unchanged.

### Strengths confirmed
- The map covers Python semantics, object/data model, collections, functions, decorators, iteration, OOP, descriptors, exceptions, typing, memory, concurrency, asynchronous programming, packaging, and performance.
- The 15 competency groups provide a coherent progression from language fundamentals to runtime and production-level reasoning.
- The current IDs and allocation are retained to preserve traceability.

### Refinements required during follow-up authoring
1. Distinguish Python language guarantees from CPython implementation details and version-specific behavior.
2. Test collection semantics separately from hash-table internals, including complexity, collision behavior, ordering guarantees, and memory trade-offs.
3. Expand typing coverage through generics, TypeVar, variance, TypedDict, ParamSpec, and static-analysis boundaries.
4. Include practical memory-retention diagnosis and profiling, not only reference counting and cyclic GC theory.
5. Cover process start methods, shared state, synchronization, and free-threaded compatibility in concurrency questions.
6. Expand asyncio into task lifecycle, structured concurrency, cancellation safety, async generators, context propagation, and backpressure.
7. Include reproducible dependency resolution, build backends, lockfiles, and packaging/deployment boundaries.

### Overlap controls
- PY-004 covers general attribute lookup and special-method dispatch; PY-023 covers the descriptor protocol in depth.
- PY-006 covers collection selection and semantics; PY-007 focuses on dictionary/hash-table mechanics.
- PY-009 covers mutability and aliasing; PY-010 covers the equality/hash contract; PY-011 covers consequences for hashed collections.
- PY-031 covers object lifetime and memory management; PY-032 covers cyclic GC; PY-033 covers diagnosis of retention and unbounded growth.
- PY-034 covers GIL semantics; PY-035 concurrency-model selection; PY-036 synchronization hazards; PY-037 free-threaded CPython and compatibility.

## Follow-up question records

**Authoring status:** question wording only. Substantive answers will be authored after the complete follow-up map has been reviewed. Each Main Question has exactly four follow-ups, covering distinct dimensions: (1) mechanism, (2) application, (3) edge cases/trade-offs, and (4) senior judgment/production implications.

### PY-001 — How does Python execute a program from source code to runtime behavior?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-001 | Mechanism | What are the main stages between Python source code and the execution of its instructions in CPython? | Какие основные этапы проходит исходный код Python до выполнения инструкций в CPython? |
| FU-002 | Application | How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module? | Как бы вы исследовали ситуацию, когда модуль Python ведёт себя по-разному при запуске как скрипт и при импорте из другого модуля? |
| FU-003 | Edge cases and trade-offs | Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter? | Какие аспекты байткода и поведения интерпретатора являются деталями реализации, а не гарантиями языка, и почему это различие важно? |
| FU-004 | Senior judgment | When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment? | Как при диагностике production-проблемы определить, нужно ли исследовать поведение на уровне Python, внутреннее устройство CPython или окружение операционной системы и runtime? |

### PY-002 — What happens during a function call in CPython?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-005 | Mechanism | What execution state does CPython need to establish or maintain when entering and executing a Python function? | Какое состояние выполнения CPython должен создать или поддерживать при входе в Python-функцию и во время её выполнения? |
| FU-006 | Application | How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service? | Как с помощью профилирования и информации о стеке вызовов исследовать чрезмерные накладные расходы на вызовы функций в Python-сервисе? |
| FU-007 | Edge cases and trade-offs | How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call? | Как рекурсия, исключения, генераторы и асинхронные функции влияют на жизненный цикл выполнения по сравнению с обычным вызовом функции? |
| FU-008 | Senior judgment | When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile? | В каких случаях знание механики вызовов CPython может существенно повлиять на решение об оптимизации и как проверить, что такая оптимизация действительно оправданна? |

