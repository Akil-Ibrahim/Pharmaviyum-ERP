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


### PY-003 — Explain Python's object model: identity, type, and value.

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-009 | Mechanism | How are an object's identity, type, and value represented conceptually, and which of them can change during an object's lifetime? | Как концептуально представлены идентичность, тип и значение объекта и какие из этих характеристик могут изменяться в течение его жизненного цикла? |
| FU-010 | Application | How would you use identity checks, equality checks, and type checks appropriately when reviewing application code? | Как правильно применять проверки идентичности, равенства и типа при ревью прикладного кода? |
| FU-011 | Edge cases and trade-offs | Why can relying on object identity or the `is` operator for value comparisons produce incorrect or implementation-dependent results? | Почему использование идентичности объекта или оператора `is` для сравнения значений может приводить к ошибкам или зависеть от реализации? |
| FU-012 | Senior judgment | How should API and domain-model design avoid exposing accidental assumptions about object identity, mutability, or concrete implementation types? | Как при проектировании API и доменных моделей избежать зависимости от случайных предположений об идентичности объектов, изменяемости и конкретных типах реализации? |

### PY-004 — How do attribute lookup and special methods work in Python?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-013 | Mechanism | How does Python resolve an instance attribute, and where do the instance dictionary, class attributes, and descriptors participate? | Как Python разрешает обращение к атрибуту экземпляра и какую роль играют словарь экземпляра, атрибуты класса и дескрипторы? |
| FU-014 | Application | How would you investigate an attribute that appears to exist on a class but is unexpectedly missing or different on an instance? | Как исследовать ситуацию, когда атрибут присутствует у класса, но неожиданно отсутствует или имеет другое значение у экземпляра? |
| FU-015 | Edge cases and trade-offs | Why can special-method lookup behave differently from ordinary attribute lookup, and what consequences does this have for proxy objects and dynamic interception? | Почему поиск специальных методов может отличаться от обычного поиска атрибутов и как это влияет на прокси-объекты и динамическое перехватывание вызовов? |
| FU-016 | Senior judgment | When designing a framework or reusable library, how would you decide whether to use descriptors, properties, inheritance, or explicit methods for controlling attribute behavior? | Как при проектировании фреймворка или переиспользуемой библиотеки выбрать между дескрипторами, свойствами, наследованием и явными методами для управления поведением атрибутов? |

### PY-005 — What is the difference between `__new__` and `__init__`?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-017 | Mechanism | What is the object-construction sequence involving `__new__` and `__init__`, and what happens if `__new__` returns an object of a different type? | Какова последовательность создания объекта с участием `__new__` и `__init__` и что происходит, если `__new__` возвращает объект другого типа? |
| FU-018 | Application | In what practical situations might overriding `__new__` be justified, for example with immutable types or controlled instance creation? | В каких практических ситуациях оправдано переопределение `__new__`, например для неизменяемых типов или контролируемого создания экземпляров? |
| FU-019 | Edge cases and trade-offs | What initialization pitfalls can arise with inheritance, immutable built-in subclasses, and repeated or partially completed construction? | Какие проблемы инициализации могут возникать при наследовании, создании подклассов неизменяемых встроенных типов и повторном или частично завершённом создании объектов? |
| FU-020 | Senior judgment | Why should custom construction logic be kept minimal, and what simpler alternatives should be considered before introducing a custom `__new__`? | Почему пользовательскую логику создания объектов следует делать минимальной и какие более простые альтернативы нужно рассмотреть до введения собственного `__new__`? |

### PY-006 — How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-021 | Mechanism | What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython? | В чём ключевые семантические и типичные реализационные различия между списками, кортежами, множествами и словарями в CPython? |
| FU-022 | Application | How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service? | Как выбрать встроенную коллекцию для упорядоченной последовательности, проверки принадлежности, удаления дубликатов и поиска по ключу в реальном сервисе? |
| FU-023 | Edge cases and trade-offs | What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity? | Что необходимо учитывать при использовании порядка вставки, поверхностного копирования, вложенных изменяемых значений и средней временной сложности операций? |
| FU-024 | Senior judgment | How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy? | Как характер нагрузки, объём данных, частота изменений и давление на память влияют на выбор коллекции и стратегию бенчмаркинга? |

### PY-007 — How do dictionaries work, and what are the implications of hash-table behavior?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-025 | Mechanism | How do hashing, index selection, collision resolution, and equality checks cooperate during dictionary lookup? | Как хеширование, выбор позиции, разрешение коллизий и проверки равенства взаимодействуют при поиске в словаре? |
| FU-026 | Application | How would you investigate unexpectedly slow dictionary operations or high memory consumption in a workload dominated by mappings? | Как исследовать неожиданно медленные операции со словарями или высокий расход памяти в нагрузке, где преобладают отображения? |
| FU-027 | Edge cases and trade-offs | What happens when many keys collide, when a key's hash-relevant state changes, or when custom equality is expensive? | Что происходит при большом количестве коллизий, изменении состояния ключа, влияющего на хеш, или высокой стоимости пользовательского сравнения? |
| FU-028 | Senior judgment | How should engineers use complexity guarantees, implementation details, and adversarial-input considerations when choosing dictionaries for critical paths? | Как инженерам учитывать оценки сложности, детали реализации и возможность специально подобранных входных данных при использовании словарей в критических участках? |

### PY-008 — How do list and dictionary comprehensions behave, including their scope and performance characteristics?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-029 | Mechanism | How are comprehension variables scoped, and how do nested comprehensions evaluate their iterables and filters? | Как определяется область видимости переменных comprehensions и как вычисляются итерируемые выражения и фильтры во вложенных comprehensions? |
| FU-030 | Application | How would you choose between a comprehension, an explicit loop, and a generator expression when transforming a large dataset? | Как выбрать между comprehension, обычным циклом и generator expression при обработке большого набора данных? |
| FU-031 | Edge cases and trade-offs | What readability, evaluation-order, exception, and memory pitfalls can arise in complex or nested comprehensions? | Какие проблемы читаемости, порядка вычисления, обработки исключений и расхода памяти могут возникать в сложных или вложенных comprehensions? |
| FU-032 | Senior judgment | What criteria would you use in code review to decide whether a comprehension is clear and efficient enough or should be replaced with a named transformation or streaming pipeline? | По каким критериям при code review определить, что comprehension достаточно понятен и эффективен или его следует заменить именованным преобразованием либо потоковой обработкой? |


### PY-009 — What does mutability mean in Python, and how does aliasing create bugs?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-033 | Mechanism | What is the relationship between names, object references, and mutable object state in Python, and why does assignment not copy an object? | Как связаны имена, ссылки на объекты и состояние изменяемых объектов в Python и почему присваивание не копирует объект? |
| FU-034 | Application | How would you diagnose and prevent an unintended mutation when the same list or dictionary is shared across several layers of an application? | Как диагностировать и предотвратить непреднамеренное изменение одного списка или словаря, совместно используемого несколькими слоями приложения? |
| FU-035 | Edge cases and trade-offs | What are the differences and limitations of shallow copying, deep copying, and custom copy behavior for nested or cyclic object graphs? | В чём различия и ограничения поверхностного копирования, глубокого копирования и пользовательской логики копирования для вложенных или циклических графов объектов? |
| FU-036 | Senior judgment | At API and domain boundaries, when would you prefer immutable data, defensive copying, ownership conventions, or controlled mutation? | На границах API и доменных слоёв когда предпочтительнее неизменяемые данные, защитное копирование, соглашения о владении данными или контролируемая мутация? |

### PY-010 — What are the equality and hashing contracts, and why must they remain consistent?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-037 | Mechanism | What invariants must hold between `__eq__` and `__hash__`, and what does Python do when a class overrides equality without defining a hash? | Какие инварианты должны соблюдаться между `__eq__` и `__hash__` и что делает Python, если класс переопределяет равенство, но не определяет хеширование? |
| FU-038 | Application | How would you implement equality and hashing for a value object whose identity is defined by a selected set of domain fields? | Как реализовать равенство и хеширование value object, идентичность которого определяется выбранным набором доменных полей? |
| FU-039 | Edge cases and trade-offs | What problems can arise from inheritance, asymmetric equality, mutable comparison fields, or unusual values such as NaN? | Какие проблемы могут возникать из-за наследования, несимметричного равенства, изменяемых полей сравнения или необычных значений, например NaN? |
| FU-040 | Senior judgment | How would you decide whether a domain type should be hashable, and how would you keep its equality semantics stable across application versions? | Как определить, должен ли доменный тип поддерживать хеширование, и как сохранить стабильность семантики равенства между версиями приложения? |

### PY-011 — Why are mutable objects generally unsuitable as dictionary keys or set members?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-041 | Mechanism | What can happen to dictionary or set lookup when the hash-relevant state of a stored key changes after insertion? | Что может произойти с поиском в словаре или множестве, если после вставки изменится состояние ключа, влияющее на его хеш? |
| FU-042 | Application | How would you model a mutable business entity that must be referenced reliably from a dictionary or set? | Как смоделировать изменяемую бизнес-сущность, на которую необходимо надёжно ссылаться из словаря или множества? |
| FU-043 | Edge cases and trade-offs | Why is a tuple not necessarily hashable, and what risks arise when a custom mutable object retains identity-based hashing? | Почему кортеж не обязательно является хешируемым и какие риски возникают, если пользовательский изменяемый объект сохраняет хеширование по идентичности? |
| FU-044 | Senior judgment | What design alternatives—immutable keys, stable identifiers, snapshots, or explicit indexes—would you consider for long-lived caches and registries? | Какие варианты проектирования — неизменяемые ключи, стабильные идентификаторы, снимки состояния или явные индексы — следует рассмотреть для долгоживущих кешей и реестров? |

### PY-012 — Explain Python's LEGB name-resolution rule and scope behavior.

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-045 | Mechanism | How does Python determine whether a name is local, enclosing, global, or built-in, and when are local variables classified? | Как Python определяет, является ли имя локальным, именем охватывающей области, глобальным или встроенным, и когда классифицируются локальные переменные? |
| FU-046 | Application | How would you refactor code that relies heavily on `global` or `nonlocal` state to make dependencies and state changes easier to reason about? | Как переработать код, который активно использует состояние `global` или `nonlocal`, чтобы зависимости и изменения состояния было проще анализировать? |
| FU-047 | Edge cases and trade-offs | How do class bodies, comprehensions, exception targets, and assignment expressions interact with Python's scope rules? | Как тела классов, comprehensions, цели обработки исключений и выражения присваивания взаимодействуют с правилами областей видимости Python? |
| FU-048 | Senior judgment | What scope-related design rules would you establish for a large codebase to reduce hidden coupling and make tests deterministic? | Какие правила проектирования областей видимости вы установили бы в большой кодовой базе, чтобы уменьшить скрытую связанность и обеспечить детерминированность тестов? |

### PY-013 — What are closures, and how does Python capture variables in nested functions?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-049 | Mechanism | What is a closure in Python, and how are free variables retained and accessed after the enclosing function has returned? | Что такое замыкание в Python и как свободные переменные сохраняются и используются после завершения охватывающей функции? |
| FU-050 | Application | How can a closure be used to encapsulate configuration or state without introducing a module-level global variable? | Как использовать замыкание для инкапсуляции конфигурации или состояния без введения глобальной переменной уровня модуля? |
| FU-051 | Edge cases and trade-offs | Why can closures created in loops exhibit late-binding behavior, and how can this affect callbacks or deferred asynchronous work? | Почему замыкания, созданные в циклах, могут демонстрировать позднее связывание переменных и как это влияет на callbacks или отложенные асинхронные операции? |
| FU-052 | Senior judgment | When is a closure a suitable abstraction, and when would a callable object, explicit dependency, or small class make lifecycle and state ownership clearer? | Когда замыкание является подходящей абстракцией, а когда объект с методом вызова, явная зависимость или небольшой класс лучше проясняют жизненный цикл и владение состоянием? |

### PY-014 — What are the differences between positional, keyword-only, variadic, and default arguments?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-053 | Mechanism | How does Python bind positional-only, positional-or-keyword, keyword-only, `*args`, and `**kwargs` parameters to call arguments? | Как Python связывает позиционные-only, позиционные или именованные, только именованные, `*args` и `**kwargs` параметры с аргументами вызова? |
| FU-054 | Application | How would you design a stable public function signature that supports extension without making callers depend on fragile positional argument ordering? | Как спроектировать стабильную публичную сигнатуру функции, допускающую расширение без зависимости вызывающего кода от хрупкого порядка позиционных аргументов? |
| FU-055 | Edge cases and trade-offs | Why are default argument expressions evaluated once, and what bugs can mutable defaults or ambiguous argument forwarding introduce? | Почему выражения значений аргументов по умолчанию вычисляются один раз и какие ошибки могут вызвать изменяемые значения по умолчанию или неоднозначная передача аргументов? |
| FU-056 | Senior judgment | How should signature design balance backward compatibility, discoverability, strictness, and extensibility in a library or service API? | Как при проектировании сигнатуры сбалансировать обратную совместимость, понятность интерфейса, строгость и расширяемость API библиотеки или сервиса? |

### PY-015 — How do decorators work, and what happens when Python applies one?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-057 | Mechanism | What does the decorator syntax translate to, and in what order are stacked decorators evaluated and applied? | Во что преобразуется синтаксис декораторов и в каком порядке вычисляются и применяются несколько декораторов? |
| FU-058 | Application | How would you use a decorator to add cross-cutting behavior such as timing, authorization checks, or structured logging without duplicating code? | Как с помощью декоратора добавить сквозное поведение, например измерение времени, проверку авторизации или структурированное логирование, не дублируя код? |
| FU-059 | Edge cases and trade-offs | What can go wrong when decorating methods, class methods, static methods, generators, or asynchronous functions? | Какие проблемы могут возникнуть при декорировании методов экземпляра, методов класса, статических методов, генераторов или асинхронных функций? |
| FU-060 | Senior judgment | What risks do decorators introduce for control flow, observability, dependency injection, and debugging, and how would you constrain their use in a large codebase? | Какие риски декораторы создают для потока управления, наблюдаемости, внедрения зависимостей и отладки и как ограничить их использование в большой кодовой базе? |

### PY-016 — How do you design decorators that preserve metadata and support arguments?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-061 | Mechanism | What metadata does `functools.wraps` preserve, and how does the wrapped function's `__wrapped__` reference support introspection? | Какие метаданные сохраняет `functools.wraps` и как ссылка `__wrapped__` обёрнутой функции помогает интроспекции? |
| FU-062 | Application | How would you structure a decorator factory that accepts configuration while preserving the decorated callable's intended interface? | Как организовать фабрику декораторов, принимающую конфигурацию и сохраняющую предполагаемый интерфейс декорируемого вызываемого объекта? |
| FU-063 | Edge cases and trade-offs | How should a decorator handle coroutine functions, generator functions, exceptions, and cancellation without changing their execution semantics? | Как декоратору обрабатывать coroutine functions, generator functions, исключения и отмену задач, не изменяя семантику их выполнения? |
| FU-064 | Senior judgment | How would you test and document a reusable decorator so that its signature, metadata, typing, composition order, and runtime behavior remain reliable? | Как тестировать и документировать переиспользуемый декоратор, чтобы его сигнатура, метаданные, типизация, порядок композиции и поведение во время выполнения оставались надёжными? |


### PY-017 — What is the iterator protocol, and how does iteration work in Python?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-065 | Mechanism | What methods define the iterator protocol, and how does a `for` loop obtain and consume an iterator? | Какие методы определяют протокол итератора и как цикл `for` получает и использует итератор? |
| FU-066 | Application | How would you implement a custom iterable domain object that supports repeated independent iterations? | Как реализовать собственный итерируемый доменный объект, поддерживающий повторные независимые проходы? |
| FU-067 | Edge cases and trade-offs | What is the difference between an iterable and an iterator, and what problems arise when an exhausted or stateful iterator is reused? | В чём разница между iterable и iterator и какие проблемы возникают при повторном использовании исчерпанного или хранящего состояние итератора? |
| FU-068 | Senior judgment | When should an API return a reusable collection, a fresh iterator, or a one-shot streaming iterator, and how should that contract be communicated? | Когда API должен возвращать повторно используемую коллекцию, новый итератор или одноразовый потоковый итератор и как документировать этот контракт? |

### PY-018 — How do generators work, including `yield`, suspension, and resumption?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-069 | Mechanism | What execution state does a generator preserve when it suspends at `yield`, and how does execution resume on the next request? | Какое состояние выполнения сохраняет генератор при приостановке на `yield` и как выполнение возобновляется при следующем запросе? |
| FU-070 | Application | How would you build a generator pipeline that reads, transforms, and validates a large input without loading it entirely into memory? | Как построить конвейер генераторов для чтения, преобразования и проверки большого входного потока без полной загрузки в память? |
| FU-071 | Edge cases and trade-offs | How do `send()`, `throw()`, `close()`, generator return values, and exceptions affect generator control flow and cleanup? | Как `send()`, `throw()`, `close()`, возвращаемые значения генератора и исключения влияют на управление потоком и очистку ресурсов? |
| FU-072 | Senior judgment | What operational risks should be considered when generators hold files, database cursors, network responses, or other resources across suspension points? | Какие эксплуатационные риски следует учитывать, если генераторы удерживают файлы, курсоры БД, сетевые ответы или другие ресурсы между точками приостановки? |

### PY-019 — When should you use generators instead of materialized collections?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-073 | Mechanism | How do lazy evaluation and materialization differ in evaluation timing, memory allocation, and exception timing? | Чем ленивое вычисление отличается от материализации с точки зрения времени вычисления, выделения памяти и момента возникновения исключений? |
| FU-074 | Application | How would you choose between a generator pipeline and a materialized list for a paginated database export or large file-processing task? | Как выбрать между конвейером генераторов и материализованным списком для постраничного экспорта из БД или обработки большого файла? |
| FU-075 | Edge cases and trade-offs | How can one-shot consumption, repeated traversal, debugging difficulty, and downstream buffering undermine the expected benefits of laziness? | Как одноразовое потребление, повторный обход, сложность отладки и буферизация на следующих этапах могут нивелировать преимущества ленивых вычислений? |
| FU-076 | Senior judgment | How would you define backpressure, batching, resource lifetime, and failure handling in a production streaming pipeline? | Как определить backpressure, пакетную обработку, жизненный цикл ресурсов и обработку ошибок в production-потоке данных? |

### PY-020 — How does Python's method resolution order work in multiple inheritance?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-077 | Mechanism | How does C3 linearization construct a class's method resolution order, and what consistency constraints must it satisfy? | Как алгоритм линеаризации C3 строит порядок разрешения методов класса и каким ограничениям согласованности он должен удовлетворять? |
| FU-078 | Application | How would you trace a cooperative method call across a multiple-inheritance hierarchy that uses `super()`? | Как проследить кооперативную цепочку вызовов методов в иерархии множественного наследования, использующей `super()`? |
| FU-079 | Edge cases and trade-offs | Why can inconsistent base-class ordering make a class hierarchy invalid, and what assumptions about `super()` commonly cause bugs? | Почему несогласованный порядок базовых классов может сделать иерархию недопустимой и какие распространённые предположения о `super()` вызывают ошибки? |
| FU-080 | Senior judgment | What criteria would make multiple inheritance acceptable in a framework, and when would composition or explicit delegation be safer? | По каким критериям множественное наследование можно считать приемлемым во фреймворке и когда композиция или явное делегирование безопаснее? |

### PY-021 — How do inheritance and composition differ, and when should each be preferred?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-081 | Mechanism | How do inheritance and composition differ in terms of type relationships, method reuse, and runtime collaboration between objects? | Чем наследование и композиция отличаются с точки зрения отношений типов, повторного использования методов и взаимодействия объектов во время выполнения? |
| FU-082 | Application | How would you refactor a base class with many conditional branches into collaborators composed around explicit responsibilities? | Как переработать базовый класс с большим количеством условных ветвей, выделив collaborators с явно заданными обязанностями? |
| FU-083 | Edge cases and trade-offs | What coupling, fragile-base-class, initialization, and behavioral-subtyping problems can arise with inheritance, and what complexity can composition introduce? | Какие проблемы связанности, хрупкого базового класса, инициализации и поведенческой подстановки возникают при наследовании и какую сложность может добавить композиция? |
| FU-084 | Senior judgment | How would you choose an extension mechanism for a public library whose users need customization without being tightly coupled to internal implementation? | Как выбрать механизм расширения публичной библиотеки, пользователям которой нужна настройка без жёсткой зависимости от внутренней реализации? |

### PY-022 — How do polymorphism, abstract base classes, and duck typing relate?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-085 | Mechanism | How do duck typing, abstract base classes, and structural protocols express or enforce different forms of substitutability? | Как duck typing, абстрактные базовые классы и структурные протоколы выражают или обеспечивают разные формы взаимозаменяемости? |
| FU-086 | Application | How would you define an interface for interchangeable storage backends while keeping business logic independent of a specific implementation? | Как определить интерфейс взаимозаменяемых backend-хранилищ, сохранив независимость бизнес-логики от конкретной реализации? |
| FU-087 | Edge cases and trade-offs | What can go wrong when an object satisfies an interface syntactically but violates its behavioral expectations or invariants? | Что может пойти не так, если объект синтаксически соответствует интерфейсу, но нарушает ожидаемое поведение или инварианты? |
| FU-088 | Senior judgment | How would you balance runtime validation, static typing, explicit registration, and duck typing at plugin or integration boundaries? | Как сбалансировать runtime-валидацию, статическую типизацию, явную регистрацию и duck typing на границах плагинов или интеграций? |

### PY-023 — What are descriptors, and how do they participate in attribute access?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-089 | Mechanism | What distinguishes data descriptors from non-data descriptors, and how does their precedence affect instance attribute lookup? | Чем data descriptors отличаются от non-data descriptors и как их приоритет влияет на поиск атрибутов экземпляра? |
| FU-090 | Application | How would you implement a reusable descriptor for validation, lazy computation, or managed per-instance attributes? | Как реализовать переиспользуемый дескриптор для валидации, ленивого вычисления или управляемых атрибутов экземпляра? |
| FU-091 | Edge cases and trade-offs | How do descriptor binding, `__set_name__`, inheritance, and storage strategy affect correctness when the same descriptor is used by multiple classes? | Как связывание дескрипторов, `__set_name__`, наследование и стратегия хранения влияют на корректность, если один дескриптор используется несколькими классами? |
| FU-092 | Senior judgment | When does a descriptor provide a meaningful abstraction over a property or explicit method, and how would you test its lifecycle and isolation guarantees? | Когда дескриптор даёт значимую абстракцию по сравнению со свойством или явным методом и как проверить его жизненный цикл и гарантии изоляции? |

### PY-024 — What does `__slots__` change, and what trade-offs does it introduce?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-093 | Mechanism | How does declaring `__slots__` affect instance attribute storage and the availability of an instance `__dict__`? | Как объявление `__slots__` влияет на хранение атрибутов экземпляра и наличие у экземпляра `__dict__`? |
| FU-094 | Application | How would you determine whether using `__slots__` is worthwhile for a high-volume population of small Python objects? | Как определить, оправдано ли использование `__slots__` для большого количества небольших объектов Python? |
| FU-095 | Edge cases and trade-offs | What inheritance, multiple-inheritance, weak-reference, subclassing, and dynamic-attribute constraints can arise with `__slots__`? | Какие ограничения, связанные с наследованием, множественным наследованием, weak references, созданием подклассов и динамическими атрибутами, возникают при использовании `__slots__`? |
| FU-096 | Senior judgment | What measurements and compatibility checks should precede introducing `__slots__` into a public model or widely used library type? | Какие измерения и проверки совместимости должны предшествовать добавлению `__slots__` в публичную модель или широко используемый тип библиотеки? |


### PY-025 — How does Python's exception hierarchy and exception propagation work?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-097 | Mechanism | How does exception propagation unwind the call stack, and how do exception matching and the built-in hierarchy determine which handler is selected? | Как распространение исключения разворачивает стек вызовов и как сопоставление типов и встроенная иерархия определяют выбранный обработчик? |
| FU-098 | Application | How would you define exception boundaries in a layered backend so that low-level failures are handled without hiding useful diagnostic context? | Как определить границы обработки исключений в многослойном backend, чтобы обрабатывать низкоуровневые сбои, не скрывая полезный диагностический контекст? |
| FU-099 | Edge cases and trade-offs | What are the risks of catching broad exceptions, catching exceptions too early, or allowing exceptions to cross asynchronous and thread boundaries? | Каковы риски перехвата слишком общих исключений, слишком ранней обработки или передачи исключений через границы асинхронных задач и потоков? |
| FU-100 | Senior judgment | How would you establish an exception taxonomy that distinguishes expected domain outcomes, validation failures, transient infrastructure errors, and programming defects? | Как выстроить таксономию исключений, различающую ожидаемые доменные результаты, ошибки валидации, временные инфраструктурные сбои и дефекты программирования? |

### PY-026 — How should exceptions be chained, handled, and translated across application layers?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-101 | Mechanism | What is the difference between implicit exception context and explicit exception causes, and how do `raise`, `raise ... from`, and `from None` affect traceback presentation? | В чём разница между неявным контекстом исключения и явно указанной причиной и как `raise`, `raise ... from` и `from None` влияют на отображение traceback? |
| FU-102 | Application | How would you translate a database-driver exception into an application-level error while preserving the original cause for diagnosis? | Как преобразовать исключение драйвера базы данных в ошибку уровня приложения, сохранив исходную причину для диагностики? |
| FU-103 | Edge cases and trade-offs | How can exception translation accidentally leak sensitive data, destroy retry semantics, or cause duplicate logging across layers? | Как преобразование исключений может случайно раскрыть чувствительные данные, нарушить семантику повторных попыток или привести к дублированию логирования между слоями? |
| FU-104 | Senior judgment | What error information should be exposed to API clients, recorded internally, correlated across services, and retained for incident investigation? | Какую информацию об ошибках следует показывать API-клиентам, записывать внутри системы, связывать между сервисами и сохранять для расследования инцидентов? |

### PY-027 — How do context managers work, and how do you implement reliable resource cleanup?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-105 | Mechanism | How do `__enter__` and `__exit__` control a `with` statement, and how can `__exit__` influence exception propagation? | Как `__enter__` и `__exit__` управляют оператором `with` и как `__exit__` может влиять на распространение исключения? |
| FU-106 | Application | How would you implement or compose context managers for a transaction, temporary resource, or lock that must be released reliably? | Как реализовать или объединить контекстные менеджеры для транзакции, временного ресурса или блокировки, которые необходимо надёжно освобождать? |
| FU-107 | Edge cases and trade-offs | What cleanup hazards arise when acquisition partially fails, cleanup itself raises, or several context managers are nested? | Какие риски очистки ресурсов возникают, если получение ресурса завершается частично, сама очистка вызывает исключение или вложено несколько контекстных менеджеров? |
| FU-108 | Senior judgment | How would you define resource ownership and cleanup guarantees across synchronous and asynchronous code, including cancellation and shutdown? | Как определить владение ресурсами и гарантии их освобождения в синхронном и асинхронном коде, включая отмену задач и завершение приложения? |

### PY-028 — What do Python type hints provide, and what do they not enforce at runtime?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-109 | Mechanism | How are annotations represented and exposed at runtime, and how does a static type checker use information that the interpreter generally does not enforce? | Как аннотации представлены и доступны во время выполнения и как статический анализатор использует информацию, которую интерпретатор обычно не обеспечивает? |
| FU-110 | Application | How would you introduce type checking incrementally into a mature Python codebase with dynamic boundaries and legacy modules? | Как постепенно внедрить проверку типов в зрелую кодовую базу Python с динамическими границами и legacy-модулями? |
| FU-111 | Edge cases and trade-offs | What limitations arise from `Any`, type narrowing, runtime-generated values, forward references, and differences between checker implementations? | Какие ограничения связаны с `Any`, сужением типов, динамически создаваемыми значениями, forward references и различиями между реализациями анализаторов типов? |
| FU-112 | Senior judgment | Where should static typing end and runtime validation begin in an application that accepts untrusted API, database, or external-service data? | Где должна заканчиваться статическая типизация и начинаться runtime-валидация в приложении, принимающем недоверенные данные API, БД или внешних сервисов? |

### PY-029 — What is the difference between nominal and structural typing, including Protocols?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-113 | Mechanism | How does a `Protocol` describe structural compatibility, and what is the difference between ordinary protocols and runtime-checkable protocols? | Как `Protocol` описывает структурную совместимость и чем обычные протоколы отличаются от протоколов, поддерживающих runtime-проверку? |
| FU-114 | Application | How would you define a protocol for a dependency that can be implemented by production infrastructure and lightweight test doubles? | Как определить протокол для зависимости, который могут реализовать production-инфраструктура и облегчённые тестовые объекты? |
| FU-115 | Edge cases and trade-offs | What can static protocols verify about attributes and method signatures, and what behavioral or runtime properties remain outside their guarantees? | Что статические протоколы могут проверить в атрибутах и сигнатурах методов и какие поведенческие или runtime-свойства остаются вне их гарантий? |
| FU-116 | Senior judgment | How would you decide between a protocol, an abstract base class, and a concrete dependency when designing extension points for a large system? | Как выбрать между протоколом, абстрактным базовым классом и конкретной зависимостью при проектировании точек расширения большой системы? |

### PY-030 — When should you use dataclasses, and what design trade-offs do they introduce?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-117 | Mechanism | Which methods and behaviors can dataclasses generate, and how do options such as `frozen`, `slots`, `eq`, and `kw_only` affect the generated class? | Какие методы и виды поведения могут генерировать dataclasses и как параметры `frozen`, `slots`, `eq` и `kw_only` влияют на создаваемый класс? |
| FU-118 | Application | How would you model a validated immutable value object with dataclasses while keeping parsing and domain invariants explicit? | Как смоделировать проверяемый неизменяемый value object с помощью dataclasses, сохранив явную логику разбора данных и доменных инвариантов? |
| FU-119 | Edge cases and trade-offs | What pitfalls involve mutable defaults, inheritance field ordering, equality semantics, frozen instances, and serialization? | Какие подводные камни связаны с изменяемыми значениями по умолчанию, порядком полей при наследовании, семантикой равенства, frozen-экземплярами и сериализацией? |
| FU-120 | Senior judgment | When would a dataclass be preferable to a Pydantic model, a hand-written class, or a named tuple, and what validation boundary drives that choice? | Когда dataclass предпочтительнее модели Pydantic, класса с ручной реализацией или named tuple и какая граница валидации определяет этот выбор? |

### PY-031 — How does CPython manage object memory and object lifetime?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-121 | Mechanism | How does reference counting contribute to object lifetime in CPython, and what roles do allocation arenas, pools, and blocks play at a high level? | Как подсчёт ссылок влияет на жизненный цикл объектов в CPython и какую роль на высоком уровне играют arenas, pools и blocks аллокатора? |
| FU-122 | Application | How would you investigate memory growth in a long-running worker to distinguish live application objects from allocator-retained memory? | Как исследовать рост памяти в долгоживущем worker, чтобы отличить живые объекты приложения от памяти, удерживаемой аллокатором? |
| FU-123 | Edge cases and trade-offs | Why does releasing references not guarantee an immediate reduction in process RSS, and how can extension modules complicate memory ownership? | Почему освобождение ссылок не гарантирует немедленного уменьшения RSS процесса и как модули расширения могут усложнять владение памятью? |
| FU-124 | Senior judgment | How would you choose measurements and tools to investigate object retention, allocation hotspots, native allocations, and container-level memory pressure? | Как выбрать метрики и инструменты для исследования удержания объектов, горячих точек выделения памяти, нативных аллокаций и давления на память на уровне контейнера? |

### PY-032 — How does cyclic garbage collection work, and what does it not collect?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-125 | Mechanism | Why is reference counting insufficient for unreachable reference cycles, and how does cyclic garbage collection identify candidate cycles? | Почему подсчёта ссылок недостаточно для недостижимых циклов ссылок и как циклический сборщик мусора обнаруживает потенциальные циклы? |
| FU-126 | Application | How would you use the `gc` module and object-reference inspection to investigate a suspected cycle in a Python service? | Как использовать модуль `gc` и анализ ссылок на объекты для исследования предполагаемого цикла в Python-сервисе? |
| FU-127 | Edge cases and trade-offs | How can finalizers, weak references, uncollectable objects, and extension-type references complicate garbage-collection behavior? | Как финализаторы, слабые ссылки, не подлежащие сборке объекты и ссылки в типах расширений могут усложнять работу сборщика мусора? |
| FU-128 | Senior judgment | When is changing garbage-collector thresholds or disabling cyclic GC justified, and what measurements and regression safeguards are required? | Когда оправдано изменение порогов сборщика мусора или отключение циклического GC и какие измерения и меры защиты от регрессий необходимы? |


### PY-033 — How do memory leaks and unbounded memory growth arise in long-running Python services?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-129 | Mechanism | How can references held by caches, registries, closures, callbacks, and task queues keep objects alive beyond their intended lifetime? | Как ссылки в кешах, реестрах, замыканиях, callbacks и очередях задач могут удерживать объекты дольше предполагаемого срока жизни? |
| FU-130 | Application | How would you investigate steadily increasing memory in a worker using allocation snapshots, object counts, and workload correlation? | Как исследовать устойчивый рост памяти в worker с помощью снимков аллокаций, количества объектов и корреляции с нагрузкой? |
| FU-131 | Edge cases and trade-offs | How would you distinguish a true retention leak from legitimate cache growth, fragmentation, allocator behavior, or native-library allocations? | Как отличить реальную утечку удержания объектов от закономерного роста кеша, фрагментации, поведения аллокатора или аллокаций нативной библиотеки? |
| FU-132 | Senior judgment | What production safeguards would you introduce for memory-bounded workers, including cache limits, workload limits, telemetry, and restart policy? | Какие production-механизмы защиты вы внедрили бы для worker с ограниченной памятью, включая лимиты кешей и нагрузки, телеметрию и политику перезапуска? |

### PY-034 — What is the GIL, and how does it affect Python thread execution?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-133 | Mechanism | What does the Global Interpreter Lock protect in conventional GIL-enabled CPython, and how does it affect execution of Python bytecode by threads? | Что защищает Global Interpreter Lock в обычной сборке CPython с GIL и как он влияет на выполнение Python-байткода потоками? |
| FU-134 | Application | How would you determine whether a threaded workload is limited by the GIL, I/O latency, native code, or another bottleneck? | Как определить, ограничена ли многопоточная нагрузка GIL, задержками ввода-вывода, нативным кодом или другим узким местом? |
| FU-135 | Edge cases and trade-offs | Why does the GIL not eliminate race conditions, and how can native extensions or blocking I/O change the concurrency picture? | Почему GIL не устраняет race conditions и как нативные расширения или блокирующий ввод-вывод могут изменить картину конкурентного выполнения? |
| FU-136 | Senior judgment | How should a team document and test GIL-related assumptions across supported Python versions, builds, and deployment environments? | Как команде документировать и проверять предположения, связанные с GIL, для поддерживаемых версий Python, сборок и deployment-окружений? |

### PY-035 — When should you use threads, processes, or asynchronous I/O?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-137 | Mechanism | How do threads, processes, and event-loop-based asynchronous I/O differ in scheduling, memory isolation, and communication costs? | Чем потоки, процессы и асинхронный ввод-вывод на основе event loop отличаются по планированию, изоляции памяти и стоимости взаимодействия? |
| FU-138 | Application | How would you choose an execution model for a backend workload combining network calls, CPU-heavy transformations, and database access? | Как выбрать модель выполнения для backend-нагрузки, сочетающей сетевые вызовы, CPU-интенсивные преобразования и обращения к базе данных? |
| FU-139 | Edge cases and trade-offs | What constraints do process startup methods, serialization, connection pools, cancellation, and shared mutable state introduce? | Какие ограничения создают способы запуска процессов, сериализация, пулы соединений, отмена задач и совместно используемое изменяемое состояние? |
| FU-140 | Senior judgment | How would you benchmark and capacity-plan a mixed concurrency architecture while accounting for throughput, tail latency, memory, and operational complexity? | Как провести бенчмаркинг и спланировать ресурсы смешанной concurrency-архитектуры с учётом throughput, tail latency, памяти и эксплуатационной сложности? |

### PY-036 — How do race conditions and synchronization problems arise in Python applications?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-141 | Mechanism | What makes a compound operation non-atomic, and how can thread interleaving expose inconsistent shared state? | Почему составная операция не является атомарной и как чередование потоков может привести к несогласованному общему состоянию? |
| FU-142 | Application | How would you protect a shared in-memory counter, cache entry, or work queue when several threads access it concurrently? | Как защитить общий счётчик в памяти, запись кеша или очередь задач при конкурентном доступе нескольких потоков? |
| FU-143 | Edge cases and trade-offs | How can lock ordering, re-entrant calls, condition-variable misuse, and excessive critical sections cause deadlocks or contention? | Как порядок захвата блокировок, повторные вызовы, неправильное использование condition variables и слишком большие критические секции могут приводить к deadlock или contention? |
| FU-144 | Senior judgment | How would you decide between locks, message passing, immutable data, and database-level concurrency control for a production workflow? | Как выбрать между блокировками, обменом сообщениями, неизменяемыми данными и механизмами конкурентного доступа на уровне БД для production-процесса? |

### PY-037 — What changes with free-threaded CPython, and how should engineers reason about compatibility?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-145 | Mechanism | What does a free-threaded CPython build change about interpreter-level thread serialization, and what guarantees should not be inferred from its availability? | Что free-threaded-сборка CPython меняет в сериализации потоков на уровне интерпретатора и какие гарантии нельзя автоматически выводить из её наличия? |
| FU-146 | Application | How would you audit an existing library or service for assumptions that may fail when run on a free-threaded build? | Как провести аудит существующей библиотеки или сервиса на предмет предположений, которые могут оказаться неверными при запуске в free-threaded-сборке? |
| FU-147 | Edge cases and trade-offs | What compatibility concerns involve C extensions, thread safety, object-level locking, build variants, and performance regressions? | Какие вопросы совместимости связаны с C-расширениями, thread safety, блокировками на уровне объектов, вариантами сборки и регрессиями производительности? |
| FU-148 | Senior judgment | What rollout strategy and evidence would you require before adopting free-threaded Python in a latency-sensitive production service? | Какая стратегия внедрения и какие доказательства необходимы перед переходом на free-threaded Python в production-сервисе, чувствительном к задержкам? |

### PY-038 — How does the asyncio event loop schedule and execute coroutines?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-149 | Mechanism | How does an event loop schedule coroutine execution, and what causes a running coroutine to suspend and allow other tasks to progress? | Как event loop планирует выполнение корутин и что заставляет выполняющуюся корутину приостановиться, позволяя другим задачам продолжить работу? |
| FU-150 | Application | How would you trace task scheduling and identify event-loop stalls in an asynchronous web service? | Как проследить планирование задач и выявить задержки event loop в асинхронном веб-сервисе? |
| FU-151 | Edge cases and trade-offs | What happens when synchronous code blocks the event-loop thread, when callbacks raise exceptions, or when tasks are created without being retained? | Что происходит, когда синхронный код блокирует поток event loop, callbacks вызывают исключения или задачи создаются без сохранения ссылок на них? |
| FU-152 | Senior judgment | How would you set event-loop ownership, task lifecycle, shutdown behavior, and observability conventions in a large async application? | Как определить владение event loop, жизненный цикл задач, поведение при завершении и правила наблюдаемости в большом асинхронном приложении? |


### PY-039 — What is the difference between a coroutine, Task, and Future?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-153 | Mechanism | How do coroutine objects, `asyncio.Task`, and `asyncio.Future` differ in purpose and lifecycle? | Чем объекты coroutine, `asyncio.Task` и `asyncio.Future` отличаются по назначению и жизненному циклу? |
| FU-154 | Application | How would you coordinate several independent asynchronous operations and collect their results while preserving clear ownership of the tasks? | Как скоординировать несколько независимых асинхронных операций и собрать их результаты, сохранив понятное владение задачами? |
| FU-155 | Edge cases and trade-offs | What happens when a coroutine is never awaited, a task fails without its result being retrieved, or a Future is completed more than once? | Что происходит, если coroutine никогда не ожидается через await, ошибка задачи остаётся без получения результата или Future завершается более одного раза? |
| FU-156 | Senior judgment | When should application code create tasks explicitly, use structured concurrency primitives, or expose an awaitable abstraction to callers? | Когда прикладному коду следует явно создавать задачи, использовать примитивы structured concurrency или предоставлять вызывающему коду awaitable-абстракцию? |

### PY-040 — How should cancellation, timeouts, and exceptions be handled in asyncio?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-157 | Mechanism | How is cancellation delivered to an asyncio task, and why is `CancelledError` part of the task's control-flow semantics? | Как отмена передаётся задаче asyncio и почему `CancelledError` является частью семантики управления потоком задачи? |
| FU-158 | Application | How would you implement a request deadline that propagates through several asynchronous service calls and database operations? | Как реализовать deadline запроса, который распространяется через несколько асинхронных вызовов сервисов и операций с базой данных? |
| FU-159 | Edge cases and trade-offs | What can go wrong if cancellation is swallowed, cleanup is not shielded appropriately, or timeout scopes are nested inconsistently? | Что может пойти не так, если отмена подавляется, очистка ресурсов неправильно защищена от отмены или timeout scopes вложены несогласованно? |
| FU-160 | Senior judgment | How would you define cancellation safety, timeout budgets, partial-result behavior, and graceful shutdown for an async service? | Как определить безопасность отмены, бюджеты таймаутов, поведение при частичных результатах и graceful shutdown асинхронного сервиса? |

### PY-041 — How do you prevent blocking operations from degrading an async application?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-161 | Mechanism | Why does calling blocking code on the event-loop thread prevent other tasks from making progress, even when those tasks are awaiting I/O? | Почему вызов блокирующего кода в потоке event loop мешает другим задачам выполняться, даже если они ожидают ввода-вывода? |
| FU-162 | Application | How would you integrate a synchronous third-party SDK or CPU-intensive function into an asynchronous FastAPI endpoint safely? | Как безопасно интегрировать синхронный сторонний SDK или CPU-интенсивную функцию в асинхронный endpoint FastAPI? |
| FU-163 | Edge cases and trade-offs | What limitations do thread and process executors introduce around cancellation, context propagation, serialization, and bounded concurrency? | Какие ограничения thread и process executors создают для отмены, передачи контекста, сериализации и ограничения конкурентности? |
| FU-164 | Senior judgment | How would you detect, isolate, and prevent event-loop starvation under production load without simply increasing worker or thread counts? | Как обнаруживать, изолировать и предотвращать starvation event loop под production-нагрузкой, не ограничиваясь простым увеличением числа workers или threads? |

### PY-042 — How does Python's import system work, including module caching and circular imports?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-165 | Mechanism | What roles do `sys.modules`, finders, loaders, and module specifications play during an import? | Какую роль во время импорта играют `sys.modules`, finders, loaders и спецификации модулей? |
| FU-166 | Application | How would you investigate an import that resolves to an unexpected module or behaves differently across working directories and execution modes? | Как исследовать импорт, который разрешается в неожиданный модуль или ведёт себя по-разному в зависимости от рабочей директории и режима запуска? |
| FU-167 | Edge cases and trade-offs | Why can circular imports expose partially initialized modules, and how do package re-exports and import-time side effects complicate diagnosis? | Почему циклические импорты могут открывать доступ к частично инициализированным модулям и как re-exports пакетов и побочные эффекты при импорте усложняют диагностику? |
| FU-168 | Senior judgment | What package-boundary and initialization rules would you establish to keep imports deterministic, testable, and safe for application startup? | Какие правила границ пакетов и инициализации вы установили бы, чтобы импорты оставались детерминированными, тестируемыми и безопасными при запуске приложения? |

### PY-043 — How should Python packages and dependencies be structured for reliable deployment?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-169 | Mechanism | What are the roles of project metadata, build backends, wheels, source distributions, and environment markers in Python packaging? | Какую роль в упаковке Python играют метаданные проекта, build backends, wheels, source distributions и environment markers? |
| FU-170 | Application | How would you structure and package a Python service so that local development, CI, container builds, and production install the same application consistently? | Как структурировать и упаковать Python-сервис, чтобы local development, CI, сборка контейнеров и production согласованно устанавливали одно и то же приложение? |
| FU-171 | Edge cases and trade-offs | What dependency-resolution risks arise from loose version constraints, transitive dependencies, optional extras, platform-specific wheels, and editable installs? | Какие риски разрешения зависимостей возникают из-за широких ограничений версий, транзитивных зависимостей, optional extras, platform-specific wheels и editable installs? |
| FU-172 | Senior judgment | How would you balance reproducible lockfiles, security updates, dependency freshness, build isolation, and deployment rollback requirements? | Как сбалансировать воспроизводимые lockfiles, обновления безопасности, актуальность зависимостей, изоляцию сборки и требования к rollback deployment? |

### PY-044 — How do you profile and optimize a Python application without premature optimization?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-173 | Mechanism | What do deterministic profilers, sampling profilers, microbenchmarks, and memory profilers measure, and what biases can each introduce? | Что измеряют детерминированные профилировщики, sampling profilers, микробенчмарки и профилировщики памяти и какие искажения может вносить каждый из них? |
| FU-174 | Application | How would you profile a slow API endpoint end to end and determine whether time is spent in Python code, database access, serialization, or network I/O? | Как профилировать медленный API endpoint от начала до конца и определить, тратится ли время на Python-код, доступ к БД, сериализацию или сетевой ввод-вывод? |
| FU-175 | Edge cases and trade-offs | Why can microbenchmarks mislead when they ignore warm-up, workload distribution, concurrency, cache effects, or measurement overhead? | Почему микробенчмарки могут вводить в заблуждение, если не учитывают прогрев, распределение нагрузки, конкурентность, влияние кешей или накладные расходы измерения? |
| FU-176 | Senior judgment | How would you prioritize an optimization using user impact, latency percentiles, resource cost, complexity, and regression risk? | Как расставить приоритеты оптимизации с учётом влияния на пользователей, перцентилей задержки, стоимости ресурсов, сложности и риска регрессии? |

### PY-045 — How do you investigate Python performance across CPU, memory, I/O, and concurrency?

| Follow-up ID | Focus | Follow-up question (EN) | Перевод (RU) |
|---|---|---|---|
| FU-177 | Mechanism | How do CPU saturation, memory pressure, I/O wait, lock contention, and event-loop lag produce different performance symptoms? | Как насыщение CPU, давление на память, ожидание ввода-вывода, конкуренция за блокировки и задержка event loop создают различные симптомы производительности? |
| FU-178 | Application | How would you investigate a service whose throughput has fallen while p95 and p99 latency have increased after a deployment? | Как исследовать сервис, у которого после deployment снизилась пропускная способность, а задержки p95 и p99 выросли? |
| FU-179 | Edge cases and trade-offs | How can queue buildup, coordinated omission, noisy neighbors, autoscaling delays, and retry amplification distort performance diagnosis? | Как накопление очередей, coordinated omission, noisy neighbors, задержки autoscaling и усиление нагрузки повторными попытками искажают диагностику производительности? |
| FU-180 | Senior judgment | How would you lead a production performance investigation from hypothesis and instrumentation through remediation, load validation, and regression prevention? | Как организовать production-расследование проблем производительности — от гипотезы и инструментирования до исправления, нагрузочной проверки и предотвращения регрессий? |


## Answer Development — PY-001

**Status:** Initial complete answer set authored; technical and editorial review remain pending.  
**Scope:** PY-001 and FU-001–FU-004. CPython-specific behavior is explicitly distinguished from Python language guarantees.

---

### PY-001 — Main Question

**Question (EN):** How does Python execute a program from source code to runtime behavior?

**Перевод (RU):** Как Python выполняет программу: от исходного кода до поведения во время выполнения?

**What the interviewer evaluates**

- Understanding of the source-to-runtime pipeline.
- Ability to distinguish Python language semantics from CPython implementation details.
- Knowledge of parsing, AST, compilation, code objects, bytecode, namespaces, and runtime execution.
- Ability to apply this model to debugging and performance analysis.

**Short Answer**

Python source code is parsed and compiled into an executable representation. In CPython, parsing produces an abstract syntax tree (AST), and compilation produces code objects containing bytecode and metadata. CPython's evaluation machinery executes those code objects in a runtime environment containing objects, namespaces, and execution state. During execution, operations may invoke Python code, native extensions, or operating-system services.

The bytecode format and exact execution strategy are implementation details. Other Python implementations may use different mechanisms while preserving Python's specified behavior.

**Detailed Answer**

A useful model separates execution into these stages:

1. **Source acquisition and decoding.** The interpreter obtains source text from a file or another execution mechanism and decodes it according to the applicable source-encoding rules.
2. **Parsing.** Lexical and syntactic analysis validates the program's structure and produces an AST. The AST represents expressions, assignments, definitions, imports, and control-flow constructs; it is not itself the final executable representation.
3. **Compilation.** The compiler analyzes scopes and control flow and creates code objects. A code object contains executable instructions and metadata such as constants, names, variable information, and source-location information.
4. **Runtime object creation.** As module code executes, Python creates and binds runtime objects. A function definition creates a function object that references compiled code and its execution environment; defining a function does not execute its body.
5. **Bytecode execution in CPython.** CPython's evaluation machinery processes instructions, evaluates expressions, performs calls, and handles control flow. Exact opcodes and evaluation optimizations vary across CPython versions.
6. **Runtime services.** Object allocation, name resolution, imports, exception propagation, memory management, and calls into native extensions support program execution.
7. **Operating-system interaction.** File access, sockets, processes, signals, and other system operations ultimately use operating-system facilities.

CPython may cache compiled bytecode in files under __pycache__ and reuse a valid cache during later imports. This is an optimization, not a requirement of the Python language, and a .pyc file is not a native machine-code executable.

**Internal Mechanics**

- **AST:** structured representation of source syntax used by the compiler.
- **Code object:** compiled instructions plus metadata; it is distinct from a function object.
- **Function object:** runtime object that wraps a code object and carries references such as globals, defaults, and closure state.
- **Frame/execution state:** state required to execute a code block, including namespace references and the current instruction position. Its implementation can change between CPython versions.
- **Evaluation machinery:** CPython processes bytecode and performs the associated operations. Recent versions use adaptive specialization and other optimizations, but exact details are version-dependent.
- **Runtime services:** memory management, import machinery, exception handling, and native-extension integration.

**Practical Example**

Consider:

~~~python
RATE = 1.2

def calculate(amount: float) -> float:
    return amount * RATE

result = calculate(10)
~~~

Conceptually, CPython compiles the module and function body into code objects. When the module executes, it binds RATE in the module namespace, creates a function object for calculate, and binds that object to the name. The final statement calls the function. During the call, the function executes its code object and resolves RATE through the relevant global namespace.

**Code Example — Inspection**

~~~python
import dis

RATE = 1.2

def calculate(amount: float) -> float:
    return amount * RATE

print(calculate.__code__)
dis.dis(calculate)
~~~

The dis module is useful for inspecting the bytecode exposed by the running interpreter. Its output is version-dependent. Application correctness should not depend on an exact disassembly unless the code is deliberately tied to a specific interpreter version and tested accordingly.

**Best Practices**

- Explain the conceptual pipeline before discussing internals.
- Separate language guarantees from CPython-specific behavior.
- Use documented introspection tools such as dis and inspect for targeted diagnostics.
- Record the interpreter implementation and version when reproducing runtime issues.
- Treat bytecode caches as optimizations, not deployment contracts.
- Diagnose imports by checking entry points, module names, working directory, sys.path, side effects, and environment configuration.
- Prefer documented public contracts over assumptions based on one interpreter build.

**Trade-offs & Alternatives**

CPython is the dominant implementation for many backend workloads and uses bytecode execution with implementation-specific optimizations. Other implementations may use different execution strategies, including JIT compilation. Native extensions can improve performance for suitable workloads but introduce packaging, ABI, memory-safety, and compatibility concerns. Precompilation or bytecode caching can reduce some repeated compilation work, but may not matter when startup is dominated by imports, I/O, or application initialization.

**Common Mistakes**

- Claiming Python has no compilation stage because it is interpreted.
- Assuming every Python implementation executes CPython bytecode.
- Treating opcode names and bytecode sequences as stable language guarantees.
- Confusing code objects with function objects.
- Assuming .pyc files are native executables.
- Forgetting that module-level statements normally execute during import.
- Ignoring native extensions, runtime configuration, or OS behavior when diagnosing a problem.

**Senior-Level Perspective**

Use the execution model as a diagnostic framework, not as trivia. Reproduce the issue under a known interpreter and version, then isolate whether it belongs to source semantics, compilation, import and initialization, runtime object behavior, a native dependency, or the operating system. For performance work, measure the actual workload: bytecode-level optimization is irrelevant if the endpoint is waiting on a database, network, lock, or external service. For portability, rely on Python's documented semantics and explicitly document any CPython-specific dependency.

**Interview-Ready Answer (EN)**

“Python execution is a multi-stage process. The source is parsed into a structured representation, typically an AST, and compiled into code objects. In CPython, those objects contain bytecode and metadata. The interpreter's evaluation machinery executes the bytecode against runtime objects and namespaces, while runtime services handle function calls, imports, exceptions, and memory management.

At module level, execution creates bindings and runs top-level statements. A function definition creates a function object that references compiled code and its execution environment; the function body runs when the function is called. Some operations invoke native extensions or operating-system facilities.

I distinguish Python language semantics from CPython implementation details. Bytecode format, opcode names, frame internals, and specialization strategies can change between versions. I use tools such as dis and inspect when they help answer a measured question, but I do not make application correctness depend on interpreter internals.”

---

### FU-001 — Execution stages in CPython

**Question (EN):** What are the main stages between Python source code and the execution of its instructions in CPython?

**Перевод (RU):** Какие основные этапы проходит исходный код Python до выполнения инструкций в CPython?

**What the interviewer evaluates:** Understanding of parsing, compilation, bytecode execution, and runtime behavior.

**Short Answer**

CPython decodes source text, parses it into an AST, compiles the AST into code objects containing bytecode and metadata, and executes those code objects using its interpreter machinery. Runtime objects, namespaces, frames, built-ins, native extensions, and OS services participate as required. Bytecode caching may avoid some repeated compilation work, but it is an optimization rather than a mandatory language stage.

**Detailed Answer**

The sequence is: source decoding; lexical and syntactic analysis; AST construction; compilation into code objects; runtime creation of objects and bindings; bytecode execution; and interaction with runtime and OS services. A function body is compiled with its containing code but normally executes only when the function is called. Executing a function definition statement creates and binds a function object.

**Internal Mechanics**

A code object stores executable instructions and metadata. A function object references a code object and runtime context such as globals and defaults. At call time, CPython establishes the execution state needed by the function. Frame representation, bytecode instructions, and evaluation optimizations are implementation- and version-specific.

**Practical Example**

~~~python
def greet(name):
    print(f"Hello, {name}")

print("module initialization")
~~~

Executing the module creates and binds the greet function and runs the module-level print. The body of greet does not run until greet is called.

**Best Practices**

Use AST inspection for source structure and disassembly for CPython-specific execution analysis. Verify the interpreter version. Do not infer that a function body executes merely because its definition was imported.

**Trade-offs & Alternatives**

AST analysis is useful for source-level tooling; bytecode analysis helps with CPython-specific questions. Neither alone explains external I/O, native extensions, or OS scheduling. Choose the narrowest diagnostic layer supported by evidence.

**Common Mistakes**

Conflating parsing with execution; assuming function bodies run at import time; treating __pycache__ as mandatory; assuming bytecode is identical across versions.

**Senior-Level Perspective**

For a startup incident, identify whether failure occurs during parsing, import resolution, module initialization, or request handling. This narrows the search space and avoids investigating bytecode when the cause is a missing dependency, import cycle, or failing top-level side effect.

**Interview-Ready Answer (EN)**

“CPython reads and decodes the source, parses it into an AST, and compiles it into code objects containing bytecode and metadata. The interpreter executes those objects in runtime contexts containing namespaces and objects. Module-level statements run when the module executes, while a function body runs when the function is called. Bytecode caching is an optimization, and the exact bytecode and evaluation internals are version-specific.”

---

### FU-002 — Script execution versus module import

**Question (EN):** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?

**Перевод (RU):** Как бы вы исследовали ситуацию, когда модуль Python ведёт себя по-разному при запуске как скрипт и при импорте из другого модуля?

**What the interviewer evaluates:** Knowledge of module identity, __name__, __main__, package context, import paths, working directory, and import-time side effects.

**Short Answer**

I compare the execution modes and inspect __name__, __package__, __file__, sys.path, the working directory, and the exact command. Direct execution normally binds the module as __main__; import uses its import name. This can change conditional execution, relative-import behavior, module identity, and initialization order. I also check for duplicate imports under different names and avoid relying on the working directory as implicit package configuration.

**Detailed Answer**

With a command such as python path/to/module.py, the file normally executes as __main__, and its package context may differ from normal package import. When imported, Python resolves a module name, checks sys.modules, locates a loader, creates or retrieves a module object, and executes its top-level code when appropriate. Running a package module with python -m package.module uses package-aware import machinery and is often more predictable for relative imports.

A guard such as if __name__ == "__main__": runs for the entry-point execution but not during ordinary import. A subtle issue occurs when one source file is loaded under two names, for example as __main__ and as package.module. Python can create two module objects, so class identity, registries, singleton assumptions, and module-level state may diverge.

**Internal Mechanics**

sys.modules caches modules by import name. __name__ identifies the current module name; __package__ provides package context for relative imports. sys.path and the import finders/loaders determine how a module is located and loaded.

**Practical Investigation**

1. Record the exact command, working directory, Python executable, and environment.
2. Compare __name__, __package__, __file__, and sys.path in both modes.
3. Verify the expected package root is on the import path.
4. Check relative imports and module-level side effects.
5. Look for the same source loaded under multiple names in sys.modules.
6. Reproduce using the intended package entry point, often python -m package.module.
7. Add a test that imports the module and verifies import has no unintended side effects.

**Best Practices**

Use a clear package layout and documented entry point; keep module-level code lightweight; put executable startup behavior in main() behind the standard name guard; avoid routine sys.path mutation; and avoid importing the same source under multiple names.

**Trade-offs & Alternatives**

Direct script execution is convenient for standalone scripts. Package-aware execution is more reliable for modules using relative imports. An installed console-script entry point can provide a clear operational interface for deployable applications.

**Common Mistakes**

Assuming __name__ is always the package name; confusing working directory with sys.path; ignoring import-time database or network calls; and adding arbitrary path mutations without understanding module identity.

**Senior-Level Perspective**

Standardize one entry point across local development, tests, containers, and deployment. Make imports deterministic and side-effect-light, then validate startup in a production-like environment. This reduces failures caused by different working directories and import paths.

**Interview-Ready Answer (EN)**

“I compare the execution context first. Direct execution normally sets __name__ to __main__, while import uses the module's import name. I inspect __name__, __package__, __file__, sys.path, the working directory, and the exact command. I then check relative imports, import-time side effects, and whether the same file has been loaded under two names. For package applications, I prefer a consistent package-aware entry point, such as python -m package.module, or an installed application entry point.”

---

### FU-003 — Language guarantees versus implementation details

**Question (EN):** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?

**Перевод (RU):** Какие аспекты байткода и поведения интерпретатора являются деталями реализации, а не гарантиями языка, и почему это различие важно?

**What the interviewer evaluates:** Portability, compatibility, documented contracts, and the boundary between Python semantics and CPython internals.

**Short Answer**

Python defines observable semantics such as expression behavior, object protocols, exceptions, and documented built-in behavior. It does not generally promise a particular bytecode format, opcode sequence, frame layout, evaluation-loop implementation, reference-counting strategy, or specialization mechanism. Depending on those details can make code fragile across interpreter versions and implementations.

**Detailed Answer**

Language guarantees are behaviors required by the language specification or documented public APIs. Implementation details are choices made by a particular interpreter. CPython-specific examples include exact bytecode instructions, opcode operands and inline caches, frame representation, evaluation-loop organization, allocator behavior, and reference-counting implementation.

Documented semantics include assignment and expression behavior, function-call rules, exception handling, iterator and context-manager protocols, and specified behavior of built-in types. Some behavior may become a documented guarantee in a particular language version, so engineers must verify the target version's documentation rather than rely on folklore.

The dis module exposes bytecode for the currently running interpreter; it is not a cross-version serialization contract. sys.getsizeof reports implementation-specific size and does not measure the full object graph reachable from an object.

**Practical Example**

A test asserting an exact sequence of disassembled opcodes may fail after a CPython upgrade even when externally visible behavior is unchanged. A robust test asserts the actual contract: returned values, raised exceptions, or documented side effects.

**Best Practices**

Depend on documented semantics and public APIs. Pin interpreter versions where reproducibility requires it. Isolate implementation-specific optimizations, separate portable behavioral tests from implementation-specific tests, and revalidate assumptions during upgrades.

**Trade-offs & Alternatives**

CPython internals may be justified in profilers, debuggers, runtime tooling, or specialized libraries. The trade-off is tighter coupling and higher maintenance cost. Ordinary application code should prefer portable abstractions.

**Common Mistakes**

Treating disassembly as stable; assuming CPython memory behavior applies to every implementation; treating shallow object size as total memory use; and making compatibility claims without naming the interpreter and version.

**Senior-Level Perspective**

Classify assumptions as language contract, documented library contract, implementation-specific behavior, or observed optimization. Depend on internals only when justified, isolate the dependency, document it, and test supported interpreter versions.

**Interview-Ready Answer (EN)**

“Python specifies language behavior, but it does not standardize every mechanism an interpreter uses. In CPython, bytecode opcodes, frame internals, evaluation-loop optimizations, memory layout, and reference-counting details are implementation-specific and can change. The dis module describes the bytecode of the interpreter currently running; it is not a portable contract. I build correctness on documented language and library behavior. If I rely on a CPython-specific feature, I isolate it, document the version dependency, and test it during upgrades.”

---

### FU-004 — Choosing the diagnostic layer in production

**Question (EN):** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?

**Перевод (RU):** Как при диагностике production-проблемы определить, нужно ли исследовать поведение на уровне Python, внутреннее устройство CPython или окружение операционной системы и runtime?

**What the interviewer evaluates:** Evidence-driven troubleshooting, observability, performance reasoning, and safe production diagnosis.

**Short Answer**

I start with the observable symptom, scope, timeline, and recent changes. I collect metrics, logs, traces, and a reproducible example, then move from the highest-level likely cause toward lower-level mechanisms. I inspect Python behavior for logic or application-state problems; CPython internals when evidence points to interpreter behavior, memory, bytecode, or runtime overhead; and the OS/container layer when symptoms indicate resource limits, scheduling, file descriptors, sockets, signals, or process failures.

**Detailed Answer**

1. **Define the symptom:** incorrect output, startup failure, latency, throughput, memory growth, process termination, or intermittent availability.
2. **Establish scope and baseline:** determine whether one process, host, endpoint, or all instances are affected; compare with a known-good baseline.
3. **Inspect application evidence:** structured logs, traces, exception chains, request context, database timings, dependency calls, and recent changes.
4. **Inspect Python runtime behavior when indicated:** profiling, stack traces, thread state, tracemalloc, garbage-collection diagnostics, disassembly, interpreter version, startup flags, and loaded extensions.
5. **Inspect OS/container evidence:** CPU throttling, memory limits and OOM events, process/thread counts, file-descriptor limits, disk pressure, network errors, DNS, socket states, signals, and container configuration.
6. **Test hypotheses:** change one relevant variable where possible, reproduce under representative load, and compare measurements.
7. **Remediate and prevent recurrence:** apply the smallest safe correction, validate functional and performance behavior, and add instrumentation or regression tests.

The layers interact. Apparent Python memory leaks can be caused by unbounded caches, retained references, native allocations, allocator behavior, or container limits. Slow endpoints may be waiting on a database rather than executing Python code.

**Internal Mechanics**

Python profilers identify expensive call paths; runtime tools expose allocation patterns, GC activity, thread state, and interpreter information. OS metrics reveal resource constraints and scheduling behavior that Python stack traces cannot explain. Correlation across traces, process metrics, and infrastructure telemetry is essential.

**Practical Example**

If API latency rises after deployment:
- If traces show time inside a database call, investigate query plans, pool saturation, and network/database health before optimizing Python bytecode.
- If traces show high CPU in serialization, profile the Python call path and representative payloads.
- If container memory rises while Python allocation snapshots remain stable, investigate native extensions, mapped resources, allocator behavior, and process/container metrics.
- If workers restart with OOM events, inspect container limits and process-level memory before selecting a remediation.

**Best Practices**

Start with user-visible symptoms and service-level indicators; correlate logs, metrics, and traces; compare against a baseline; use tools matching the suspected bottleneck; reproduce under representative data and concurrency; distinguish root cause from contributing conditions; and validate the fix with regression guards.

**Trade-offs & Alternatives**

Deep runtime inspection can reveal subtle causes but may be expensive or intrusive. Sampling profilers and targeted tracing can be safer than deterministic profiling under live traffic. Staging is preferable for intrusive diagnostics when it is sufficiently representative.

**Common Mistakes**

Starting with bytecode before establishing CPU-bound behavior; treating every memory increase as a Python object leak; ignoring container limits or downstream latency; increasing workers without checking memory and dependency capacity; changing many variables at once; and declaring root cause from correlation alone.

**Senior-Level Perspective**

A senior engineer owns the investigation end to end: problem framing, diagnostic-layer selection, coordination of application and platform evidence, production-risk management, communication of uncertainty, and validation. The goal is safe service restoration and recurrence prevention, not demonstrating knowledge of interpreter internals.

**Interview-Ready Answer (EN)**

“I choose the diagnostic layer based on the symptom and evidence. I establish scope, timeline, impact, and a baseline using service metrics, logs, and traces. I inspect application behavior when the issue points to business logic, state, or dependency usage. I move into Python and CPython diagnostics when profiling, stack traces, allocation data, or interpreter-specific behavior indicate a runtime problem. I inspect the OS and container layer when there are signs of CPU throttling, memory limits, OOM kills, file-descriptor exhaustion, network problems, or process-level failures.

I avoid starting with internals without a hypothesis. I correlate evidence across layers, test the smallest plausible explanation, validate the remediation under representative load, and add monitoring or regression tests to reduce recurrence.”

---

## PY-001 answer review checklist

- [x] Main question has an English answer and Russian explanation.
- [x] Short and detailed answers are present.
- [x] Internal mechanics are explained.
- [x] Practical examples and a relevant code example are included.
- [x] Best practices, trade-offs, common mistakes, and senior-level judgment are covered.
- [x] Interview-ready English answer is included.
- [x] FU-001–FU-004 each have substantive answers.
- [x] CPython-specific behavior is distinguished from language guarantees.
- [ ] Independent technical review against the target Python/CPython version.
- [ ] Final editorial review and mastery assessment.

**Completion rule:** This record is authored, but not finally approved, until the technical and editorial review items above are completed.
