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

**Interview-Ready Answer (RU)**

«Выполнение программы на Python состоит из нескольких этапов. Исходный код разбирается в структурированное представление, обычно AST, а затем компилируется в code objects. В CPython эти объекты содержат байткод и метаданные. Механизм исполнения интерпретатора выполняет байткод в контексте runtime-объектов и пространств имён, а runtime-службы обеспечивают вызовы функций, импорт, обработку исключений и управление памятью.

При выполнении модуля исполняются инструкции верхнего уровня и создаются привязки имён. Определение функции создаёт объект функции, который ссылается на скомпилированный код и контекст выполнения; тело функции выполняется при её вызове. Некоторые операции обращаются к native extensions или средствам операционной системы.

Я различаю семантику языка Python и детали реализации CPython. Формат байткода, названия opcode, внутреннее устройство frames и стратегии специализации могут меняться между версиями. Я использую такие инструменты, как dis и inspect, когда они помогают проверить конкретную гипотезу, но не строю корректность приложения на внутренних деталях интерпретатора.»

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

**Interview-Ready Answer (RU)**

«CPython читает и декодирует исходный код, разбирает его в AST, а затем компилирует в code objects, содержащие байткод и метаданные. Интерпретатор выполняет эти объекты в runtime-контекстах, включающих пространства имён и объекты. Инструкции уровня модуля выполняются при запуске модуля, тогда как тело функции выполняется при вызове этой функции. Кеширование байткода является оптимизацией, а конкретный байткод и внутренние механизмы исполнения зависят от версии интерпретатора.»

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

**Interview-Ready Answer (RU)**

«Сначала я проверяю контекст выполнения. При прямом запуске файла значение __name__ обычно равно __main__, тогда как при импорте используется импортное имя модуля. Я проверяю __name__, __package__, __file__, sys.path, текущую рабочую директорию и точную команду запуска. Затем анализирую относительные импорты, побочные эффекты при импорте и вероятность загрузки одного файла под двумя разными именами. Для приложений с пакетной структурой я предпочитаю единый запуск с сохранением контекста пакета, например python -m package.module, либо установленную точку входа приложения.»

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

**Interview-Ready Answer (RU)**

«Python определяет семантику языка, но не стандартизирует каждый механизм, с помощью которого интерпретатор обеспечивает это поведение. В CPython байткодовые opcode, внутреннее устройство frames, оптимизации цикла интерпретации, организация памяти и детали подсчёта ссылок относятся к реализации и могут меняться. Модуль dis показывает байткод текущего интерпретатора, но это не переносимый контракт. Корректность приложения я основываю на документированном поведении языка и библиотек. Если я использую особенность CPython, то изолирую её, документирую зависимость от версии и проверяю её при обновлениях.»

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

**Interview-Ready Answer (RU)**

«Я выбираю уровень диагностики исходя из симптома и имеющихся доказательств. Сначала определяю масштаб, временную последовательность и влияние проблемы, используя метрики сервиса, логи и трассировки. Поведение приложения я исследую, если проблема связана с бизнес-логикой, состоянием или использованием зависимостей. К диагностике Python и CPython перехожу, когда профилирование, stack traces, данные об аллокациях или особенности интерпретатора указывают на проблему runtime. Уровень ОС и контейнера проверяю при признаках ограничения CPU, лимитов памяти, OOM kill, исчерпания файловых дескрипторов, сетевых проблем или сбоев процессов.

Я не начинаю с изучения внутренних механизмов без гипотезы. Сопоставляю данные разных уровней, проверяю наиболее вероятное объяснение минимальным экспериментом, затем валидирую исправление под репрезентативной нагрузкой и добавляю мониторинг или регрессионные тесты.»

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

## Answer Development — PY-002

**Status:** Initial complete answer set authored; technical and editorial review remain pending.  
**Scope:** PY-002 and FU-005–FU-008. CPython call mechanics are described conceptually; internal structures and optimizations are version-dependent.

---

### PY-002 — Main Question

**Question (EN):** What happens during a function call in CPython?

**Перевод (RU):** Что происходит при вызове функции в CPython?

**What the interviewer evaluates**

- Understanding of Python's call semantics and argument binding.
- Knowledge of function objects, code objects, local and global namespaces, and execution frames.
- Understanding of return values, exception propagation, and nested calls.
- Ability to distinguish language-level behavior from CPython's internal call implementation.
- Ability to reason about call overhead without prematurely optimizing code.

**Short Answer**

When a Python function is called, Python evaluates the callable and its arguments, applies the call protocol, binds the supplied arguments to the function's parameters, and begins executing the function body. Conceptually, the call runs the function's code object in a new execution context with access to local, global, built-in, and closure-related state. In CPython, this involves interpreter-managed execution state and frame machinery, although the exact frame allocation and call path have evolved across versions.

The function either returns a value, raises an exception, or—in the case of a generator or coroutine function—produces a generator or coroutine object whose body is executed according to its own lifecycle.

**Detailed Answer**

A normal Python function call can be understood as a sequence of semantic and runtime operations:

1. **Evaluate the call expression.** Python evaluates the callable expression and the argument expressions according to the language's evaluation rules. This can itself execute arbitrary code or raise an exception before the function body starts.
2. **Resolve the callable and perform the call protocol.** The target may be a Python function, a bound method, a class, a built-in callable, or a user-defined object implementing the __call__ method. Different callable categories may use different internal paths, but they must obey the applicable call semantics.
3. **Bind arguments to parameters.** Positional arguments, keyword arguments, defaults, positional-only parameters, keyword-only parameters, and variadic parameters (*args and **kwargs) are handled according to the function signature. Invalid combinations raise TypeError before the function body executes. For Python functions, default argument expressions are evaluated when the function definition executes, not afresh on every call.
4. **Establish execution state.** The function executes with local state and access to its global namespace, built-ins, and any closure cells. Conceptually, Python needs an execution frame for the active function call. CPython's internal representation and allocation strategy for this state have changed; it is not correct to assume every call always allocates a traditional heap-allocated frame object in exactly the same way.
5. **Execute the function body.** The interpreter evaluates statements and expressions, performs name lookups, calls other functions, handles control flow, and may enter native code. Local variable access and global lookup have different semantics and may have different performance characteristics.
6. **Complete the call.** A return statement produces the return value. Reaching the end of a function without an explicit return produces None. An exception that is not handled inside the function propagates to the caller, unwinding execution state as required.
7. **Release or retain relevant state.** Once a call completes, its active execution state is no longer needed as an active call. Objects referenced by local variables may remain alive if other references exist—for example, through returned objects, closures, tracebacks, or other retained references. A traceback can retain frames and their local state, which is one reason long-lived exception references can contribute to memory retention.

A function call is therefore more than a jump to another instruction address: it includes argument evaluation and binding, execution-context management, control-flow handling, and result or exception propagation.

**Internal Mechanics**

- **Function object:** contains or references the function's code and runtime metadata, including its global namespace and defaults; closure information is available when applicable.
- **Code object:** contains compiled instructions and metadata. It is reusable across calls; each call does not recompile the function body.
- **Argument binding:** maps supplied positional and keyword arguments to the declared parameters and applies defaults and variadic collection rules.
- **Execution frame:** represents the active execution context, including local state and links to relevant namespaces and execution information. CPython's frame internals and optimization strategy are implementation details.
- **Call protocol:** Python supports multiple callable categories. CPython has optimized internal call paths, but their exact details are not a language guarantee.
- **Return and exception paths:** normal completion returns a value to the caller; exceptional completion propagates an exception and associated traceback information.
- **Closures:** nested functions can retain references to variables from enclosing scopes through closure cells, allowing those values to outlive the outer function call.

**Practical Example**

~~~python
def make_multiplier(factor):
    def multiply(value, *, offset=0):
        return value * factor + offset
    return multiply

triple = make_multiplier(3)
result = triple(10, offset=2)
~~~

When make_multiplier(3) is called, its parameter is bound and its body creates a nested function object. The returned multiply function retains access to factor through its closure. Later, triple(10, offset=2) binds value positionally and offset by keyword, executes the function body, resolves factor through the closure, and returns 32.

**Code Example — Inspecting a Function's Metadata**

~~~python
import inspect

def describe(item, limit=10, *, strict=False):
    return item[:limit]

print(inspect.signature(describe))
print(describe.__code__.co_varnames)
print(describe.__code__.co_freevars)
~~~

inspect.signature() exposes the callable's signature where supported. Code-object attributes provide implementation-oriented introspection. These facilities are useful for debugging and tooling, but code-object internals should not be treated as a stable application-level data format. In this example, co_freevars is empty because describe does not close over an enclosing variable.

**Best Practices**

- Keep function signatures explicit and avoid unnecessary positional/keyword ambiguity.
- Understand that default values are evaluated once when the function definition executes.
- Use closures intentionally and be aware of the objects they retain.
- Keep exception handling close to the layer that can make a meaningful recovery decision.
- Use profiling to establish whether call overhead is material before changing function boundaries.
- Prefer readable decomposition over premature inlining or complicated dispatch tricks.
- When inspecting frames or tracebacks, avoid retaining them longer than necessary if they hold large object graphs.

**Trade-offs & Alternatives**

- **Many small functions:** improve modularity, testing, reuse, and readability, but may add some call overhead in hot paths.
- **Larger functions or inlining:** can reduce some call overhead but may harm maintainability and make testing harder; arbitrary source-level function inlining is not a universal Python guarantee.
- **Closures:** provide convenient encapsulation of lexical state, but can extend object lifetimes.
- **Decorators and wrappers:** add composability and cross-cutting behavior, but can add call layers and affect introspection unless metadata is preserved.
- **Python versus native callables:** built-ins and extension functions may have different performance characteristics, but benchmark results depend on workload and interpreter version.

**Common Mistakes**

- Saying that every call recompiles the function.
- Assuming every callable is an ordinary Python function.
- Assuming all arguments are copied when passed to a function; Python uses object-reference assignment semantics.
- Forgetting that argument expressions are evaluated before the call and can have side effects.
- Assuming default expressions are evaluated on every invocation.
- Treating a frame as necessarily a Python dictionary containing all locals at all times.
- Assuming function-call overhead is the bottleneck without profiling.
- Ignoring traceback and closure references when investigating retained memory.

**Senior-Level Perspective**

A senior engineer should understand both the semantic contract and the implementation boundary. For correctness, reason about argument binding, object references, scope, return behavior, and exception propagation. For performance, measure realistic workloads and identify whether time is spent in Python call dispatch, the function body, serialization, allocation, I/O, or downstream services.

CPython has changed its internal call machinery and frame optimizations over time. Therefore, avoid basing architecture on assumptions about a specific internal frame allocation path. If an optimization depends on CPython internals, isolate it, pin and test supported versions, and document why the measured benefit justifies the coupling.

**Interview-Ready Answer (EN)**

“When a function call is evaluated, Python first evaluates the callable and argument expressions, then applies the call protocol and binds positional and keyword arguments to the function's parameters. The function body executes using its compiled code object and a runtime context that provides local state, globals, built-ins, and closure variables where applicable.

Conceptually, an execution frame represents the active call. In CPython, the exact frame representation and call path are implementation details and have changed across versions. During execution, the function can return a value or propagate an exception. If it is a generator or coroutine function, calling it creates a generator or coroutine object rather than immediately running the body to completion.

For performance, I profile representative workloads before optimizing call boundaries, because the dominant cost may be inside the function or in I/O rather than the call mechanism itself.”

**Interview-Ready Answer (RU)**

«При вызове функции Python сначала вычисляет вызываемый объект и выражения аргументов, затем применяет протокол вызова и связывает позиционные и именованные аргументы с параметрами функции. Тело функции выполняется с использованием её скомпилированного code object и runtime-контекста, предоставляющего локальное состояние, глобальные и встроенные пространства имён, а также переменные замыкания, если они есть.

Концептуально активный вызов представлен execution frame. В CPython конкретное представление frame и путь вызова являются деталями реализации и менялись между версиями. Во время выполнения функция может вернуть значение или передать исключение вызывающему коду. Если это генераторная или асинхронная функция, вызов создаёт объект генератора или coroutine, а не выполняет тело немедленно до завершения.

При анализе производительности я сначала профилирую репрезентативную нагрузку, прежде чем оптимизировать границы вызовов: основная стоимость может находиться внутри функции или быть связана с I/O, а не с самим механизмом вызова.»

**Follow-up Questions & Answers**

---

### FU-005 — Execution state during a function call

**Question (EN):** What execution state does CPython need to establish or maintain when entering and executing a Python function?

**Перевод (RU):** Какое состояние выполнения CPython должен создать или поддерживать при входе в Python-функцию и во время её выполнения?

**What the interviewer evaluates:** Understanding of code objects, function objects, argument binding, local state, globals, built-ins, closures, and frames.

**Short Answer**

CPython must make the function's code and execution context available: bound arguments, local-variable state, references to the function's global namespace and built-ins, closure cells when present, and the control-flow state needed to execute and return or raise an exception. Conceptually this is represented by an execution frame. The exact internal frame layout and allocation strategy are CPython implementation details and vary by version.

**Detailed Answer**

The function object provides the compiled code and associated runtime metadata. Before executing the body, the call machinery validates and binds arguments to parameters. The executing function then needs access to its local variables and parameter values, global namespace, built-ins namespace, closure cells for free variables, current instruction and exception-handling state, and caller/execution metadata needed for tracing and propagation.

Not every implementation stores all of this in one Python-visible object. In CPython, internal frame and interpreter structures have evolved, and optimized execution may avoid materializing a full Python frame object until introspection or tracing requires it.

**Internal Mechanics**

A code object describes the compiled block. A function object connects that code to globals, defaults, and closure information. Local-variable storage is optimized for execution and should not be assumed to be a normal dictionary in every circumstance. When frame introspection is requested, CPython may expose or materialize a frame object according to the version's implementation.

**Practical Example**

~~~python
def outer(prefix):
    suffix = "!"
    def inner(name):
        return prefix + name + suffix
    return inner

greet = outer("Hello, ")
print(greet("Ada"))
~~~

The inner function uses its own parameter name, but it also needs access to prefix and suffix from the enclosing scope. Those free variables are retained through closure cells after outer has returned.

**Best Practices**

Understand the distinction between locals, globals, built-ins, and closure variables. Use inspect and frame inspection for targeted debugging, not as a routine dependency of application logic. Avoid retaining frame and traceback objects unnecessarily.

**Trade-offs & Alternatives**

Materializing and inspecting frames is valuable for debuggers, profilers, and diagnostics, but introspection can add overhead and may retain references to large object graphs. Optimized execution paths can reduce overhead but make assumptions about internal frame layout less portable.

**Common Mistakes**

- Assuming every local namespace is always a fully materialized dictionary.
- Assuming a function's globals are taken from the caller's module.
- Forgetting that closures retain enclosing variables.
- Assuming a Python-visible frame object must be allocated in exactly the same way for every call and every CPython version.

**Senior-Level Perspective**

When debugging memory retention, inspect whether closures, tracebacks, or stored frame references are keeping objects alive. When building profilers or debuggers, use documented introspection APIs and test against supported CPython versions rather than depending on private frame internals.

**Interview-Ready Answer (EN)**

“CPython needs the function's code object, bound arguments, local execution state, and access to the function's globals, built-ins, and closure cells. It also maintains control-flow and exception state so the function can continue, return, or propagate an exception. Conceptually this is an execution frame, but CPython's internal frame representation and allocation strategy have changed over time. A full Python-visible frame is not necessarily materialized in the same way for every call.”

**Interview-Ready Answer (RU)**

«Для выполнения функции CPython необходимы её code object, связанные аргументы, локальное состояние выполнения и доступ к глобальному пространству имён функции, built-ins и ячейкам замыкания. Также поддерживается состояние управления потоком и обработки исключений, чтобы функция могла продолжить выполнение, вернуть результат или передать исключение. Концептуально это execution frame, однако внутреннее представление frame и стратегия его выделения в CPython со временем менялись. Полноценный Python-visible frame не обязательно материализуется одинаковым способом при каждом вызове.»

---

### FU-006 — Profiling function-call overhead

**Question (EN):** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?

**Перевод (RU):** Как с помощью профилирования и информации о стеке вызовов исследовать чрезмерные накладные расходы на вызовы функций в Python-сервисе?

**What the interviewer evaluates:** Profiling methodology, interpretation of cumulative and self time, sampling versus deterministic profiling, and production-safe optimization.

**Short Answer**

I reproduce or capture a representative workload, measure a baseline, and use a profiler to identify functions with high call counts and meaningful cumulative or self time. I correlate profiles with traces and request-level latency so I can distinguish Python call overhead from time spent in I/O, database operations, serialization, locks, or native code. I then test a targeted change and compare results under the same workload.

**Detailed Answer**

1. **Define the performance objective.** Determine whether the issue is throughput, CPU utilization, p95/p99 latency, or a specific endpoint's response time.
2. **Capture a representative workload.** Use realistic input sizes, concurrency, and request mix. Microbenchmarks alone may not reflect production behavior.
3. **Measure a baseline.** Record wall-clock latency, CPU time, throughput, memory, and relevant service-level indicators.
4. **Profile call paths.** A deterministic profiler such as cProfile can show call counts and time attributed to functions. Sampling profilers can often provide lower-overhead insight into production-like workloads.
5. **Interpret the metrics correctly.** Self time estimates time spent in a function excluding subcalls; cumulative time includes time in subcalls. A function with many calls is not automatically a bottleneck.
6. **Correlate with distributed traces.** Determine whether time is spent in Python execution, database queries, remote calls, serialization, lock contention, or other waits.
7. **Form a specific hypothesis.** Excessive tiny helper calls in a hot CPU path may be relevant, while a high call count in a database client may simply reflect expected I/O behavior.
8. **Change one thing and remeasure.** Compare the same workload and environment, including correctness, latency distribution, CPU, memory, and maintainability.

**Internal Mechanics**

Call-stack profiles reveal the hierarchy of calls and where time accumulates. Deterministic profiling instruments function-call events and can perturb timing; sampling profiling periodically samples execution state and typically has lower overhead but may miss very short events. Native extensions and blocking system calls may require tools beyond a Python-only profiler.

**Practical Example**

Suppose an endpoint transforms thousands of records. A profile shows a small normalization helper called millions of times with substantial cumulative CPU time. After verifying correctness, you may reduce repeated work by normalizing once, using a more suitable built-in operation, or changing the data flow. If instead the profile and traces show most latency inside a database query, merging Python helper functions is unlikely to improve endpoint latency.

**Best Practices**

- Profile production-representative workloads.
- Distinguish self time from cumulative time.
- Use sampling tools when deterministic profiling overhead is unacceptable.
- Correlate CPU profiles with request traces and infrastructure metrics.
- Benchmark before and after under controlled conditions.
- Keep performance changes small and preserve readable abstractions where possible.

**Trade-offs & Alternatives**

Deterministic profiling gives detailed call counts but may distort timing. Sampling is less intrusive but statistically approximate. Microbenchmarks are useful for isolated operations but cannot replace end-to-end measurements. Native profilers may be necessary when time is spent in extension code or system calls.

**Common Mistakes**

- Optimizing the function with the highest call count without examining time.
- Confusing cumulative time with self time.
- Treating wall-clock waiting as Python CPU overhead.
- Comparing benchmarks with different input sizes or environments.
- Removing useful abstractions based on intuition rather than measured benefit.

**Senior-Level Perspective**

The optimization decision should be based on service-level impact, not an attractive microbenchmark. Establish whether call overhead contributes materially to the endpoint's latency or CPU budget. Estimate the maximum possible benefit, account for maintainability costs, and validate the change under realistic concurrency. If the bottleneck is downstream I/O, focus on query plans, connection pooling, batching, caching, or concurrency limits instead.

**Interview-Ready Answer (EN)**

“I start by defining the target metric and capturing a representative workload. I use a profiler to inspect call counts, self time, and cumulative time, and I correlate that data with request traces. A high call count alone does not prove that calls are expensive; the time may be in a database, network request, serialization routine, or native extension. Once I have a specific hypothesis, I make a targeted change and compare the same workload before and after, checking latency percentiles, CPU, memory, and correctness. I avoid sacrificing maintainability for an optimization that has no measurable service-level benefit.”

**Interview-Ready Answer (RU)**

«Сначала я определяю целевую метрику и собираю репрезентативную нагрузку. Затем использую профилировщик, чтобы изучить количество вызовов, self time и cumulative time, и сопоставляю эти данные с трассировками запросов. Большое количество вызовов само по себе не доказывает, что они дороги: время может уходить на запросы к БД, сетевые вызовы, сериализацию или native extension. После формулирования конкретной гипотезы я вношу целевое изменение и сравниваю результаты на той же нагрузке до и после него, проверяя перцентили latency, CPU, память и корректность. Я не жертвую сопровождаемостью ради оптимизации, которая не даёт измеримого эффекта на уровне сервиса.»

---

### FU-007 — Different execution lifecycles

**Question (EN):** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?

**Перевод (RU):** Как рекурсия, исключения, генераторы и асинхронные функции влияют на жизненный цикл выполнения по сравнению с обычным вызовом функции?

**What the interviewer evaluates:** Control-flow semantics, suspended execution, coroutine scheduling, exception propagation, and resource-lifecycle awareness.

**Short Answer**

Recursion creates nested active calls and therefore nested execution state. Exceptions transfer control through stack unwinding until a matching handler is found. A generator function call creates a generator object and suspends its body until iteration advances it; its state is retained between yields. An async function call creates a coroutine object; its body runs when the coroutine is awaited or scheduled by an event loop. These are different lifecycles from an ordinary function that runs immediately to completion.

**Detailed Answer**

- **Ordinary function:** after arguments are evaluated and bound, the function body runs until it returns or raises. Its active execution state is then left.
- **Recursion:** each recursive invocation has its own logical call state and parameter/local values. Deep recursion can hit the interpreter's recursion limit or exhaust available resources. Tail-call elimination is not a general Python language guarantee.
- **Exceptions:** raising an exception changes control flow. Python searches for a matching handler while unwinding execution contexts. A traceback records the propagation path and can retain references to frames and local objects.
- **Generator functions:** calling a generator function returns a generator object without immediately executing the body to completion. Advancing it with next() or iteration runs until the next yield, return, or exception. The generator retains its suspended execution state between advances.
- **Async functions:** calling an async def function creates a coroutine object; it does not by itself run the coroutine body. Awaiting or scheduling it allows an event loop to drive its execution. At an await that suspends, control can return to the event loop so other tasks can run. An awaitable that completes immediately may not cause a scheduling suspension.
- **Cancellation and cleanup:** asynchronous tasks can receive cancellation, typically delivered at a suspension point. Cleanup should use try/finally and asynchronous context managers appropriately; cancellation should not be accidentally swallowed.

**Internal Mechanics**

Generators and coroutines preserve state across suspension points, including the information needed to resume execution. CPython has specialized runtime objects and execution machinery for generators and coroutines. The event loop schedules coroutine progress; it is not the same thing as a separate OS thread for each coroutine.

**Practical Example**

~~~python
def ordinary():
    print("body runs during call")
    return 1

def generate():
    print("body starts on iteration")
    yield 1

async def asynchronous():
    print("body starts when awaited/scheduled")
    return 1

ordinary()
g = generate()
next(g)
coro = asynchronous()
~~~

The coroutine object in this example must be awaited or scheduled to execute; creating it alone is not enough.

**Best Practices**

- Bound recursive depth or use an iterative algorithm when appropriate.
- Handle exceptions at meaningful recovery boundaries and preserve diagnostic context.
- Close generators or use context-manager patterns when they own resources.
- Await or schedule coroutine objects and do not leave them unawaited.
- Make cancellation-safe cleanup explicit in asynchronous code.
- Avoid blocking operations on an event-loop thread.

**Trade-offs & Alternatives**

Recursion can express tree and divide-and-conquer algorithms clearly, while iteration avoids deep call nesting. Generators provide lazy processing and lower peak memory for streams, but introduce suspended state and lifecycle concerns. Asyncio supports high concurrency for I/O-bound work, but requires cooperative non-blocking operations and does not automatically accelerate CPU-bound work.

**Common Mistakes**

- Assuming a generator body executes when the generator function is called.
- Assuming an async function runs immediately when called.
- Treating an event loop as one thread per coroutine.
- Assuming Python performs general tail-call optimization.
- Swallowing cancellation or failing to release resources.
- Retaining exceptions and tracebacks indefinitely without considering referenced frames.

**Senior-Level Perspective**

Choose the execution model according to workload and lifecycle requirements. Use recursion when depth is bounded and clarity benefits; generators for lazy synchronous pipelines; coroutines for cooperative I/O concurrency; and threads or processes when their respective execution and isolation properties fit the workload. Design cleanup, cancellation, backpressure, and observability as part of the lifecycle—not as afterthoughts.

**Interview-Ready Answer (EN)**

“An ordinary function runs when called and completes by returning or raising. Recursion creates nested calls with separate logical execution state. Exceptions unwind control flow until a handler is found. A generator call returns a generator object whose body advances on iteration and retains state between yields. An async function call returns a coroutine object; it runs when awaited or scheduled, and the event loop drives it across suspension points. These differences matter for resource cleanup, cancellation, stack depth, and scheduling.”

**Interview-Ready Answer (RU)**

«Обычная функция выполняется при вызове и завершается возвратом значения либо возбуждением исключения. Рекурсия создаёт вложенные вызовы с отдельным логическим состоянием выполнения. Исключения разматывают поток управления до тех пор, пока не будет найден подходящий обработчик. Вызов генераторной функции возвращает объект генератора: его тело выполняется по мере итерации, а состояние сохраняется между yield. Вызов async-функции возвращает coroutine object; выполнение начинается при await или планировании задачи, а event loop управляет её продвижением через точки приостановки. Эти различия важны для освобождения ресурсов, отмены задач, глубины стека и планирования.»

---

### FU-008 — When call mechanics matter for optimization

**Question (EN):** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?

**Перевод (RU):** В каких случаях знание механики вызовов CPython может существенно повлиять на решение об оптимизации и как проверить, что такая оптимизация действительно оправданна?

**What the interviewer evaluates:** Performance judgment, measurement discipline, version awareness, and maintainability trade-offs.

**Short Answer**

It matters when profiling demonstrates that Python-level call dispatch or repeated wrapper/dispatch layers consume a meaningful part of a CPU-bound workload. Knowledge of CPython's call optimizations can explain results and guide targeted experiments, but it should not replace measurement. I validate an optimization with representative benchmarks and service-level metrics, compare supported interpreter versions, and ensure correctness and maintainability are preserved.

**Detailed Answer**

Call mechanics may matter in extremely hot loops that invoke tiny Python functions millions of times; deep wrapper or decorator chains; callback-heavy code where dispatch is a measurable fraction of CPU time; transformation pipelines with many small per-item calls; or framework paths where repeated indirection accumulates under high request volume.

Even in these cases, call overhead should be isolated from the work performed by the function. A call may appear frequently in a profile but consume little self time; the actual cost may be allocations, attribute lookup, data conversion, locks, or I/O.

Potential optimizations include reducing redundant wrapper layers, moving invariant work out of hot loops, batching operations, using appropriate built-ins, reducing repeated dynamic lookup, or changing the algorithm and data flow. In selected cases, a native extension or vectorized library may be appropriate. The choice should be driven by the workload and operational constraints.

**Internal Mechanics**

CPython versions can optimize calls and execution paths differently. Specialization, vectorcall-related mechanisms, and frame optimizations may affect measured costs. These are implementation details; a micro-optimization that helps one interpreter release may be neutral or harmful on another. Do not write code that depends on private call internals unless the dependency is intentional and isolated.

**Practical Validation Plan**

1. Capture a representative input distribution and concurrency profile.
2. Establish a baseline using repeatable benchmarks and production telemetry.
3. Confirm that call overhead is material using profiles, not only call counts.
4. Estimate the maximum possible gain: if calls account for only a small fraction of total CPU time, the end-to-end improvement is bounded.
5. Implement one targeted alternative while preserving behavior.
6. Run correctness, edge-case, and regression tests.
7. Benchmark on each supported Python implementation/version and deployment configuration.
8. Compare p50/p95/p99 latency, throughput, CPU, memory, and operational complexity.
9. Retain the optimization only if the measured benefit justifies its maintenance cost.

**Best Practices**

- Optimize algorithms and unnecessary work before relying on interpreter-specific tricks.
- Benchmark realistic workloads, not only synthetic single-call loops.
- Keep a before/after record and pin the runtime used for comparison.
- Include correctness and maintainability in the decision.
- Reassess performance-sensitive assumptions during Python upgrades.

**Trade-offs & Alternatives**

Inlining may reduce call overhead but can duplicate logic and reduce testability. Batching can reduce repeated calls and I/O but may increase memory use and latency for individual items. Native code can improve CPU performance but adds build, ABI, debugging, and deployment complexity. Keeping small functions may be the best choice when their overhead is negligible relative to the clarity they provide.

**Common Mistakes**

- Optimizing based on intuition or a single microbenchmark.
- Assuming a specific CPython optimization will exist in every version.
- Ignoring algorithmic complexity and data-structure costs.
- Trading away readability for a negligible speedup.
- Measuring only average latency while p95/p99 regresses.
- Failing to retest after a runtime upgrade.

**Senior-Level Perspective**

The decision should connect a measured low-level cost to a meaningful service-level outcome. If function dispatch consumes a substantial CPU budget in a hot path, reducing redundant calls may be justified. If it contributes negligibly to end-to-end latency, preserve clean abstractions and focus on the actual bottleneck. Document the evidence, runtime scope, expected benefit, and rollback criteria.

**Interview-Ready Answer (EN)**

“I would only optimize call mechanics after profiling shows that Python call dispatch or repeated wrapper layers are a material cost in a representative CPU-bound workload. I would inspect self time and call paths, estimate the maximum possible end-to-end gain, and test a focused alternative such as reducing redundant calls or batching work. Then I would compare correctness, latency percentiles, throughput, CPU, memory, and maintainability on the supported Python versions. CPython call optimizations change over time, so I would avoid relying on private internals unless the dependency is isolated and justified by measured results.”

**Interview-Ready Answer (RU)**

«Я оптимизирую механику вызовов только после того, как профилирование показывает, что диспетчеризация Python-вызовов или повторяющиеся слои обёрток существенно влияют на репрезентативную CPU-bound нагрузку. Я анализирую self time и call paths, оцениваю максимально возможный сквозной выигрыш и проверяю целевой вариант, например устранение лишних вызовов или пакетную обработку. Затем сравниваю корректность, перцентили latency, throughput, CPU, память и сопровождаемость на поддерживаемых версиях Python. Оптимизации вызовов в CPython меняются со временем, поэтому я не полагаюсь на приватные внутренние механизмы, если такая зависимость не изолирована и не оправдана измеренными результатами.»

---

## PY-002 answer review checklist

- [x] Main question includes English and Russian wording.
- [x] Short and detailed answers explain call semantics and runtime behavior.
- [x] Argument binding, function/code objects, frames, namespaces, closures, return, and exceptions are covered.
- [x] Practical example and introspection example are included.
- [x] Best practices, trade-offs, common mistakes, and senior-level judgment are covered.
- [x] Interview-ready English answer is included.
- [x] FU-005–FU-008 each have substantive answers.
- [x] Ordinary functions, recursion, exceptions, generators, and coroutines are distinguished.
- [ ] Independent technical review against the target CPython versions.
- [ ] Final editorial review and mastery assessment.

**Completion rule:** This record is authored, but not finally approved, until the technical and editorial review items above are completed.


## Answer Development — PY-003

**Status:** Initial complete main-question answer authored; technical and editorial review remain pending.  
**Scope:** Main question PY-003. Follow-ups FU-009–FU-012 remain part of the question map and will receive their own complete answers.

---

### PY-003 — Main Question

**Question (EN):** Explain Python's object model: identity, type, and value.

**Перевод (RU):** Объясните объектную модель Python: идентичность, тип и значение объекта.

**What the interviewer evaluates**

- Understanding that Python variables are names bound to objects rather than typed storage locations.
- Ability to distinguish object identity, type, and value.
- Understanding of mutability and object lifetime.
- Correct use of `is`, `==`, and `type()`.
- Awareness of equality customization, aliasing, and implementation-specific identity behavior.
- Ability to apply these concepts to API design, debugging, and concurrency.

**Short Answer**

In Python, every object has an identity, a type, and a value. Identity distinguishes a particular object instance during its lifetime; type determines the operations and behavior supported by the object; and value is the data or state represented by that object.

A variable is a name bound to an object, not a container that owns a value independently. Multiple names can refer to the same object. An object's identity and type remain stable during its lifetime, while its value may change if the object is mutable. Immutable objects do not expose in-place state changes; operations that appear to modify them produce another object or value instead.

The `is` operator tests identity, `==` tests equality according to the object's equality implementation, and `type()` returns the object's concrete type. These concepts should not be confused.

**Detailed Answer**

Python's object model is based on objects and name bindings. At runtime, values are objects, and names in namespaces refer to those objects.

1. **Identity** describes which particular object an expression refers to. The `is` operator tests whether two references point to the same object. The built-in `id()` returns an identity value that is unique and constant for that object's lifetime. In CPython, this is commonly related to the object's memory address, but that is an implementation detail; portable code must not assume that `id()` is a memory address or that it is never reused after an object's lifetime ends.
2. **Type** determines an object's behavior: which operations it supports, how it participates in protocols, and how operations such as attribute access, iteration, arithmetic, and comparison are implemented. The built-in `type(obj)` returns the object's concrete type. Python is dynamically typed: names are not declared with fixed runtime types, and a name can be rebound to objects of different types.
3. **Value** is the information or state represented by an object. For an integer, it is the numeric value; for a list, it is the sequence of elements; for a domain object, it may be the state represented by its attributes.

**Mutability and lifetime**

An object's identity and type do not change during its lifetime. Its value may change if its type supports mutation. For example, a list can be modified in place while remaining the same list object. An integer is immutable: an operation such as adding one produces an integer result rather than changing the original integer object.

A name can also be rebound. Rebinding a name does not mutate the original object; it changes which object that name refers to. This distinction is central to understanding assignment, argument passing, aliasing, and shared state.

**Identity versus equality**

The expression `a is b` asks whether `a` and `b` refer to the same object. The expression `a == b` asks whether the objects compare equal according to their equality semantics, commonly implemented through `__eq__`. Two distinct objects may compare equal. Equality may be customized, may have domain-specific meaning, and is not guaranteed to imply identity.

Use identity checks for singleton sentinels such as `None`, and equality checks for value comparisons. Do not use `is` to compare strings, numbers, or other values.

**Type checks and polymorphism**

The concrete type can be inspected with `type()`, while `isinstance()` checks whether an object is an instance of a class or its subclasses (and can also honor the relevant abstract base class or runtime protocol mechanisms). Application code should generally prefer behavior-oriented interfaces and polymorphism over unnecessary checks for exact concrete types.

**Detailed code example**

~~~python
first = [1, 2]
alias = first
another = [1, 2]

print(first is alias)       # True: same object
print(first == another)     # True: equal values
print(first is another)     # False: distinct objects

alias.append(3)

print(first)                # [1, 2, 3]
print(alias)                # [1, 2, 3]
print(another)              # [1, 2]
~~~

The assignment `alias = first` binds a second name to the same list. Mutating the list through either name is visible through both references. The independently created `another` list has an equal initial value but a different identity.

**Best Practices**

- Use `is None` and other identity checks only when identity is the intended question.
- Use `==` for value equality.
- Prefer `isinstance()` when a type check is genuinely needed and subclass compatibility is intended.
- Prefer protocols and behavior-based design over exact type checks when designing extensible APIs.
- Be explicit about mutability and ownership in APIs that accept or return collections and domain objects.
- Avoid relying on object identity across serialization, process boundaries, database round trips, or distributed systems.
- When sharing mutable objects, define ownership and synchronization expectations.

**Trade-offs & Alternatives**

- **Identity-based comparison** is efficient and precise for singleton sentinels and object-aliasing checks, but it is unsuitable for general value comparison.
- **Equality-based comparison** expresses value semantics and supports domain-specific comparison, but custom equality can be expensive, surprising, or inconsistent if poorly implemented.
- **Exact type checks** can enforce a narrow contract, but they reduce substitutability and can reject valid subclasses or compatible implementations.
- **`isinstance()` checks** support inheritance-aware contracts, but excessive branching on types can still make code rigid; polymorphic interfaces or protocols may be clearer.
- **Mutable objects** support efficient in-place updates and shared state, but aliasing creates coupling and can introduce concurrency bugs.
- **Immutable objects** simplify reasoning and sharing, but updates require producing replacement values and may involve allocation.

**Common Mistakes**

- Saying that a variable itself has a fixed type in the same sense as a statically typed storage location.
- Confusing identity with equality.
- Using `is` to compare strings or integers because an interactive test appeared to work.
- Assuming `id()` is a portable memory address.
- Assuming equal objects must be the same object.
- Assuming assignment copies a mutable object.
- Assuming immutability means an object can never refer to mutable state internally.
- Using exact `type(x) is SomeClass` checks when subclasses or compatible implementations should be accepted.
- Assuming object identity remains meaningful after serialization or across processes.

**Senior-Level Perspective**

A senior engineer uses the object model to reason about correctness at API and system boundaries. Aliasing and mutability affect whether callers can unexpectedly change shared state. Equality semantics affect deduplication, caching, sets, dictionary keys, and domain comparisons. Type checks affect extensibility and substitutability. Identity is process-local object identity, not a durable business identifier.

For domain models, distinguish technical object identity from domain identity. Two separately loaded ORM entities may represent the same database row without being the same Python object. Likewise, two deserialized objects may represent the same logical value while having different identities. Distributed systems should use explicit stable identifiers rather than Python's `id()`.

When mutable state is shared between threads or tasks, define ownership, synchronization, and mutation boundaries. Prefer immutable values or defensive copying where they reduce accidental coupling, while considering the allocation and performance costs.

**Interview-Ready Answer (EN)**

“Python objects have three fundamental characteristics: identity, type, and value. Identity tells us which particular object we are referring to; type defines its behavior and supported operations; and value represents the data or state it carries.

Python names are references bound to objects, so multiple names can refer to the same object. An object's identity and type remain stable during its lifetime, while its value can change if the object is mutable. For example, a list can be modified in place, whereas an integer is immutable.

I distinguish identity from equality: `is` checks whether two references point to the same object, while `==` checks equality according to the object's comparison semantics. I use `is None` for the None singleton and `==` for value comparisons. For type checks, I generally prefer `isinstance()` when subclass compatibility is appropriate, and I prefer protocols or polymorphic interfaces when designing extensible APIs.

At the system-design level, I also distinguish Python object identity from domain identity. Object identity is not stable across serialization or process boundaries, so applications should use explicit domain identifiers when identity must persist.”

**Interview-Ready Answer (RU)**

«У объектов Python есть три фундаментальные характеристики: идентичность, тип и значение. Идентичность показывает, о каком конкретном объекте идёт речь; тип определяет его поведение и поддерживаемые операции; значение представляет данные или состояние, которые объект содержит.

Имена в Python связываются с объектами, поэтому несколько имён могут ссылаться на один и тот же объект. Идентичность и тип объекта остаются неизменными на протяжении его жизненного цикла, тогда как значение может изменяться, если объект изменяемый. Например, список можно изменить на месте, а целое число является неизменяемым объектом.

Я различаю идентичность и равенство: оператор `is` проверяет, ссылаются ли две переменные на один и тот же объект, а `==` проверяет равенство согласно правилам сравнения, определённым для этого объекта. Для проверки на `None` я использую `is None`, а для сравнения значений — `==`. При проверке типа обычно предпочитаю `isinstance()`, если требуется учитывать наследование. При проектировании расширяемых API отдаю предпочтение протоколам и полиморфным интерфейсам.

На уровне архитектуры системы я также отделяю идентичность Python-объекта от идентичности сущности предметной области. Идентичность объекта не сохраняется как надёжный идентификатор после сериализации или между процессами, поэтому для устойчивой идентификации приложение должно использовать явные доменные идентификаторы.»

**Follow-up Questions & Answers**

The four mapped follow-ups FU-009–FU-012 are developed as separate answer sections so that each receives a complete technical explanation and bilingual interview-ready answer.

---


### FU-009 — Identity, type, and value during an object's lifetime

**Parent Main Question:** PY-003 — Explain Python's object model: identity, type, and value.

**Question (EN):** How are an object's identity, type, and value represented conceptually, and which of them can change during an object's lifetime?

**Перевод (RU):** Как концептуально представлены идентичность, тип и значение объекта и какие из этих характеристик могут изменяться в течение его жизненного цикла?

**What the interviewer evaluates**

- Precise understanding of Python object semantics.
- Ability to distinguish an object's identity from its representation or memory location.
- Understanding of type stability, mutability, and object lifetime.
- Awareness of name binding, aliasing, and implementation-specific explanations.

**Short Answer**

Conceptually, every Python object has an identity, a type, and a value. Identity distinguishes the particular object; type defines its behavior and supported operations; value is the data or state it represents.

An object's identity and type remain constant during its lifetime. Its value may change when the object is mutable. A name can be rebound to another object, but rebinding the name does not change the identity, type, or value of the original object.

**Detailed Answer**

Python's data model describes objects through three fundamental properties:

1. **Identity** — the object's identity distinguishes it from every other simultaneously existing object. The is operator tests whether two references designate the same object. The built-in id(obj) returns an integer representing that identity. The identity is guaranteed to remain constant during the object's lifetime. The language does not require this integer to be a memory address.
2. **Type** — an object's type determines the operations it supports and the semantics of those operations. It is available through type(obj). The type of an object does not change during that object's lifetime. Python is dynamically typed because names are not permanently attached to a declared type; a name may be rebound to an object of another type.
3. **Value** — the value is the information or state represented by the object. Whether that value can change depends on the object's mutability. A mutable object can expose state changes while retaining the same identity and type. An immutable object does not support changing its own value after creation.

**Object lifetime and identity**

Identity is meaningful for the lifetime of an object. Once an object is no longer reachable and its lifetime ends, its identity value may later be reused for another object. Therefore, id() is not a durable identifier and must not be stored as a business key or assumed unique across time, processes, or machines.

In CPython, an object's identity is commonly associated with its memory address. This is an implementation detail, not a portable Python-language guarantee. Other Python implementations may represent identity differently.

**Mutation versus rebinding**

These are different operations:

- **Mutation** changes the state of an existing mutable object.
- **Rebinding** changes which object a name refers to; it does not mutate the old object.

~~~python
items = [10, 20]
alias = items

items.append(30)       # Mutates the existing list.
print(alias)           # [10, 20, 30]
print(items is alias)  # True

items = ["new"]        # Rebinds the name items.
print(items)           # ['new']
print(alias)           # [10, 20, 30]
print(items is alias)  # False
~~~

After the append, both names still refer to the same list object, whose value has changed. After the assignment to items, that name refers to a different list; the object referenced by alias remains unchanged.

**Immutable objects and nested state**

An immutable object's own value cannot be changed in place. An operation that appears to modify an immutable object produces another result rather than changing the original object. However, immutability is not necessarily deep: an immutable container can hold references to mutable objects.

~~~python
record = (["draft"],)
record[0].append("published")

print(record)  # (['draft', 'published'],)
~~~

The tuple's structure and references are unchanged, but the list referenced by the tuple is mutable and has changed. This distinction matters when reasoning about shared state and hashability.

**How to inspect the properties**

- Use is when the question is whether two expressions refer to the same object.
- Use id(obj) when investigating identity during the object's lifetime, not as a persistent identifier.
- Use type(obj) to inspect the concrete type.
- Use == to compare values according to the object's equality semantics.
- Use controlled mutation tests or state inspection to understand whether an object's value can change.

These operations answer different questions and should not be substituted for one another.

**Best Practices**

- Explain identity independently of physical memory layout.
- Treat id() as lifetime-scoped diagnostic information, not a database key or distributed identifier.
- Distinguish rebinding from mutation when reviewing assignments and function arguments.
- Document whether APIs retain, mutate, copy, or return caller-owned mutable objects.
- Consider nested mutable members when describing an object as immutable.
- Avoid depending on CPython-specific memory behavior unless the application explicitly targets a known CPython version and the dependency is justified.

**Trade-offs & Edge Cases**

- Mutable objects can be updated efficiently in place, but aliases observe those changes and may create hidden coupling.
- Immutable objects simplify reasoning about state and sharing, but nested mutable references can still introduce state changes.
- id() is useful for debugging aliasing, but its value is not stable after object destruction and is not portable as a memory address.
- Rebinding is local to a namespace binding; it does not alter other names that still reference the previous object.
- A type may define complex or customized behavior, but the object's type itself remains stable throughout its lifetime.

**Common Mistakes**

- Claiming that an object's identity is necessarily its memory address in Python.
- Assuming an id() value can never be reused after the original object is destroyed.
- Confusing a name's rebinding with mutation of the object previously referenced by that name.
- Saying that an object's type changes when a variable is assigned a value of another type.
- Assuming immutable containers guarantee that all reachable state is immutable.
- Treating identity, equality, and value as interchangeable concepts.

**Senior-Level Perspective**

This distinction is important when designing APIs and diagnosing state-related defects. If a function receives a mutable object and modifies it, every alias to that object can observe the change. If a function instead rebinds one of its local parameter names, the caller's binding is not changed by that rebinding.

At application boundaries, object identity should not be confused with domain identity. ORM instances, deserialized values, and objects reconstructed in another process may represent the same logical entity while having different Python identities. Use explicit stable identifiers for domain entities and distributed references.

A senior engineer should also make ownership and mutation contracts explicit: whether a component may mutate an input, whether it retains a reference, whether it returns a copy, and how shared mutable state is synchronized.

**Interview-Ready Answer (EN)**

“Conceptually, every Python object has an identity, a type, and a value. Identity distinguishes the particular object, type defines its behavior and supported operations, and value represents its data or state.

An object's identity and type remain constant throughout its lifetime. Its value can change if it is mutable. For example, appending to a list changes the state of the existing list without changing its identity or type. By contrast, assigning a new object to a variable rebinds the name; it does not mutate the object that the name previously referenced.

The id() function exposes an identity value that is guaranteed to remain constant during the object's lifetime, but Python does not guarantee that it is a memory address. In CPython it is commonly related to the object's address, which is an implementation detail. The identity value may also be reused after the object's lifetime ends.

This distinction is useful when reasoning about aliasing, API ownership contracts, mutable state, and the difference between Python object identity and stable domain identity.”

**Interview-Ready Answer (RU)**

«Концептуально каждый объект Python обладает идентичностью, типом и значением. Идентичность отличает конкретный объект от других объектов, тип определяет его поведение и поддерживаемые операции, а значение представляет его данные или состояние.

Идентичность и тип объекта остаются неизменными на протяжении всего его жизненного цикла. Значение может изменяться, если объект является изменяемым. Например, добавление элемента в список изменяет состояние существующего объекта списка, не меняя его идентичность и тип. Напротив, присваивание новой ссылки переменной означает переназначение имени: оно не изменяет объект, на который это имя ссылалось ранее.

Функция id() возвращает идентификатор, который гарантированно остаётся постоянным в течение жизненного цикла объекта, однако Python не гарантирует, что это адрес памяти. В CPython он обычно связан с адресом объекта, но это деталь реализации. После завершения жизненного цикла объекта его идентификатор может быть использован повторно.

Это различие важно при анализе aliasing, контрактов владения данными в API, изменяемого состояния и при отделении идентичности Python-объекта от устойчивой идентичности сущности предметной области.»

**Status:** Authored; independent technical and editorial review pending.

---


### FU-010 — Applying identity, equality, and type checks in code review

**Parent Main Question:** PY-003 — Explain Python's object model: identity, type, and value.

**Question (EN):** How would you use identity checks, equality checks, and type checks appropriately when reviewing application code?

**Перевод (RU):** Как правильно применять проверки идентичности, равенства и типа при ревью прикладного кода?

**What the interviewer evaluates**

- Correct distinction between object identity and value equality.
- Appropriate use of `is`, `==`, `type()`, and `isinstance()`.
- Understanding of Python's data model and custom equality behavior.
- Ability to review contracts, polymorphism, and edge cases rather than merely syntax.
- Awareness of maintainability and correctness implications.

**Short Answer**

I first identify what the code intends to compare. I use `is` for identity checks, especially for singleton sentinels such as `None`; `==` for value equality; and `isinstance()` when the contract requires an object to belong to a class hierarchy or supported abstract type. I use exact `type(x) is T` checks only when the API explicitly requires that exact concrete type. I also review custom equality, hash consistency, and whether type branching should be replaced by polymorphism or a protocol.

**Detailed Answer**

A code review should begin with the semantic question being asked, not with a preferred operator.

1. **Identity checks — `is`**

   Use `is` when correctness depends on two references designating the same object. The canonical example is checking the `None` singleton:

   ```python
   if result is None:
       handle_missing_result()
   ```

   Identity checks are also appropriate for private sentinel objects created to represent a state that must not be confused with an ordinary value:

   ```python
   MISSING = object()

   def get_value(value=MISSING):
       if value is MISSING:
           return use_default()
       return value
   ```

   This avoids conflating an omitted argument with an explicitly supplied value such as `None`.

2. **Equality checks — `==`**

   Use `==` when the requirement concerns equivalent values rather than the same object:

   ```python
   if response.status == "ready":
       process_response()
   ```

   Equality is governed by the object's comparison behavior, commonly through `__eq__`. It may be customized by domain classes, ORM entities, numerical libraries, or other types. Reviewers should consider whether equality is meaningful, side-effect free, sufficiently efficient, and returns a scalar boolean as expected by the surrounding control flow. Some libraries, notably array-oriented libraries, may return element-wise comparison results rather than a single bool.

3. **Type checks — `isinstance()`**

   Use `isinstance(value, ExpectedType)` when the contract is based on a type or its accepted subclasses:

   ```python
   if isinstance(payload, Mapping):
       process_mapping(payload)
   ```

   This can preserve substitutability and accept multiple implementations of an abstract interface. Abstract base classes may provide a common runtime classification. Runtime-checkable protocols can also support structural checks, but those checks have limitations and should not be mistaken for complete static type validation.

4. **Exact concrete type checks — `type()`**

   An exact check such as `type(value) is int` deliberately rejects subclasses. This may be appropriate when an API must exclude special subclass behavior or enforce a narrowly defined serialization or validation contract. It should be intentional and documented, not an accidental substitute for `isinstance()`.

5. **Prefer behavior-oriented design where possible**

   If code checks several concrete types to decide which method to call, consider whether a shared interface, protocol, polymorphic method, or explicit adapter would express the contract more clearly. Type checks are not inherently wrong; they are often useful at validation and integration boundaries. The review question is whether they make the contract safer or unnecessarily couple the code to implementation details.

**Practical Code Review Example**

~~~python
def process(value):
    if value is None:
        return "missing"

    if isinstance(value, str):
        return value.strip()

    if type(value) is int:
        return str(value)

    raise TypeError("Unsupported value")
~~~

Review observations:

- `value is None` is correct because None is a singleton.
- `isinstance(value, str)` accepts string subclasses, which is often appropriate.
- `type(value) is int` rejects bool and custom int subclasses. This may be intentional, because bool is a subclass of int, but the contract should make that choice explicit.
- If the function should accept any object that can be converted to text, a behavior-based contract may be more appropriate than these branches.
- If it is validating a strict wire-format schema, explicit type restrictions may be justified.

**Equality and Hashing Review**

When objects are used as dictionary keys or set members, review the relationship between equality and hashing. If two objects compare equal, their hash values must be equal. A class that customizes `__eq__` without providing a compatible hash implementation may become unhashable or violate the expected hash contract if it defines an unsafe custom hash.

Mutable objects whose hash depends on mutable state are especially dangerous as dictionary keys or set elements: changing the relevant state after insertion can make lookup behavior unreliable. Prefer immutable key state.

**Best Practices**

- Choose the operator based on the semantic contract: identity, value equality, or type compatibility.
- Use `is None` rather than `== None`.
- Use `==` for value comparisons; never rely on `is` for string or numeric value comparison.
- Prefer `isinstance()` when subclasses are valid.
- Reserve exact type checks for documented, deliberate constraints.
- Inspect custom `__eq__` and `__hash__` implementations when objects participate in sets or dictionary keys.
- Keep validation at system boundaries explicit; use polymorphism or protocols for internal extensibility when appropriate.
- Add tests for subclass behavior, sentinel values, and equality edge cases.

**Trade-offs & Edge Cases**

- `is` is a direct identity test, but it does not express value equivalence.
- `==` expresses value semantics, but custom equality may be expensive, non-scalar, or surprising.
- `isinstance()` supports subclassing, but can accept subclasses whose behavior differs from the base class's assumptions.
- Exact type checks provide strictness, but can reject valid substitutable implementations.
- Protocol-based design reduces coupling, while runtime protocol checks generally verify only a limited structural surface; static type checking can provide broader development-time analysis.
- Type dispatch can be clear at parsing and validation boundaries, while repeated type branching deep inside business logic can signal a missing abstraction.

**Common Mistakes**

- Writing `value == None` instead of `value is None`.
- Using `is` to compare strings, integers, or other ordinary values.
- Replacing every `isinstance()` with an exact `type()` check.
- Assuming `isinstance(value, int)` excludes booleans; in Python, `bool` is a subclass of `int`.
- Assuming all `==` operations return a plain boolean.
- Ignoring custom equality and hash behavior in domain objects.
- Using mutable state in hash calculations for objects stored in dictionaries or sets.
- Treating a runtime protocol check as a complete validation of an object's behavior.

**Senior-Level Perspective**

A senior reviewer evaluates whether comparison semantics match the domain contract and remain correct under extension. For example, a payment amount may require value equality with explicit currency and precision semantics; a missing-field sentinel requires identity; a plugin boundary may need an interface-oriented type check or adapter.

The reviewer also considers compatibility: accepting subclasses can support extension but may broaden behavior; exact checks can protect strict boundaries but make future implementations harder. Equality and hashing affect caches, deduplication, ORM identity maps, and collection membership. The right choice should be documented where it is not obvious and covered by tests at the relevant boundary.

**Interview-Ready Answer (EN)**

“I choose the check based on what the code needs to establish. I use `is` when object identity matters, most commonly for `None` or a private sentinel. I use `==` when comparing values according to the object's equality semantics. For type compatibility, I generally use `isinstance()` because it supports subclasses and abstract base classes. I use an exact `type()` comparison only when rejecting subclasses is an explicit part of the contract.

During code review, I also inspect custom equality and hashing behavior, especially for objects used as dictionary keys or set members. I check whether type branching is appropriate at a validation boundary or whether an interface, protocol, or polymorphic design would reduce coupling. The goal is to make the comparison express the intended contract, preserve substitutability where appropriate, and avoid implementation-dependent assumptions.”

**Interview-Ready Answer (RU)**

«Я выбираю способ проверки в зависимости от того, что именно должен установить код. Оператор `is` использую, когда важна идентичность объекта, прежде всего при проверке на `None` или специальный sentinel-объект. Оператор `==` применяю для сравнения значений в соответствии с семантикой равенства, определённой для конкретного типа. Для проверки совместимости типов обычно использую `isinstance()`, поскольку он учитывает наследование и абстрактные базовые классы. Точное сравнение через `type()` применяю только тогда, когда запрет на использование подклассов является осознанной частью контракта.

При code review я также проверяю пользовательскую реализацию равенства и хеширования, особенно если объекты используются как ключи словарей или элементы множеств. Оцениваю, оправданы ли проверки типов на границе валидации или интерфейс, протокол либо полиморфизм позволили бы уменьшить связанность. Цель — чтобы проверка точно выражала контракт, сохраняла возможность подстановки реализаций там, где это необходимо, и не опиралась на случайные особенности реализации Python.»

**Status:** Authored; independent technical and editorial review pending.

---

## PY-003 answer review checklist

- [x] Main question includes English and Russian wording.
- [x] Identity, type, value, name binding, and mutability are distinguished.
- [x] Identity versus equality and `is` versus `==` are explained.
- [x] `type()` and `isinstance()` are distinguished.
- [x] Aliasing and mutable-state implications are covered.
- [x] Practical code example is included.
- [x] Best practices, trade-offs, common mistakes, and senior-level design implications are covered.
- [x] Interview-ready answers are provided in English and Russian.
- [ ] Independent technical review.
- [ ] Final editorial review and mastery assessment.

**Completion rule:** This record is authored, but not finally approved, until the technical and editorial review items above are completed.
