# Python Core & Advanced Python — Карта вопросов (RU)

**Язык:** Русский  
**Базовая версия Python:** 3.15.2 — отмечать поведение, зависящее от версии, и отделять гарантии языка Python от деталей реализации CPython.  
**Распределение раздела:** 45 основных вопросов + 180 дополнительных вопросов = 225  
**Текущее покрытие:** PY-001–PY-019; 19 основных вопросов и 76 дополнительных (FU-1–FU-4 для каждого основного вопроса)  
**Правило нумерации:** Ровно четыре Follow-up на каждый основной вопрос с локальной нумерацией FU-1–FU-4. Дополнительные вопросы находятся внутри соответствующего основного PY-вопроса.  
**Файл ответов:** [PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md](./PYTHON_CORE_ADVANCED_QUESTIONS_AND_ANSWERS.md)  
**Английская версия:** [EN Question Map](../EN/PYTHON_CORE_ADVANCED.md)

## Реестр бейджей технических сущностей — PY-001

Одна и та же сущность всегда использует одинаковый бейдж и цвет во всей учебной программе. Бейджи обозначают технические понятия и не заменяют определения или бейджи типов вопросов.

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

- ![ENTITY: Callable](https://img.shields.io/badge/ENTITY-Callable-2563eb) — Callable
- ![ENTITY: Argument Binding](https://img.shields.io/badge/ENTITY-Argument-Binding-7c3aed) — Argument Binding
- ![ENTITY: Parameter](https://img.shields.io/badge/ENTITY-Parameter-7c3aed) — Parameter
- ![ENTITY: Execution Frame](https://img.shields.io/badge/ENTITY-Execution-Frame-0ea5e9) — Execution Frame
- ![ENTITY: _PyInterpreterFrame](https://img.shields.io/badge/ENTITY-_PyInterpreterFrame-64748b) — _PyInterpreterFrame
- ![ENTITY: PyFrameObject](https://img.shields.io/badge/ENTITY-PyFrameObject-64748b) — PyFrameObject
- ![ENTITY: Closure Cell](https://img.shields.io/badge/ENTITY-Closure-Cell-16a34a) — Closure Cell
- ![ENTITY: Global Namespace](https://img.shields.io/badge/ENTITY-Global-Namespace-64748b) — Global Namespace
- ![ENTITY: Builtins Namespace](https://img.shields.io/badge/ENTITY-Builtins-Namespace-64748b) — Builtins Namespace
- ![ENTITY: Traceback](https://img.shields.io/badge/ENTITY-Traceback-d97706) — Traceback
- ![ENTITY: Vectorcall](https://img.shields.io/badge/ENTITY-Vectorcall-0891b2) — Vectorcall
- ![ENTITY: tp_call](https://img.shields.io/badge/ENTITY-tp_call-0891b2) — tp_call
- ![ENTITY: Generator](https://img.shields.io/badge/ENTITY-Generator-0891b2) — Generator
- ![ENTITY: Coroutine](https://img.shields.io/badge/ENTITY-Coroutine-0891b2) — Coroutine
- ![ENTITY: Event Loop](https://img.shields.io/badge/ENTITY-Event-Loop-0891b2) — Event Loop
- ![ENTITY: Recursion](https://img.shields.io/badge/ENTITY-Recursion-7c3aed) — Recursion
- ![ENTITY: Profiler](https://img.shields.io/badge/ENTITY-Profiler-16a34a) — Profiler
- ![ENTITY: Sampling Profiler](https://img.shields.io/badge/ENTITY-Sampling-Profiler-16a34a) — Sampling Profiler
- ![ENTITY: Self Time](https://img.shields.io/badge/ENTITY-Self-Time-d97706) — Self Time
- ![ENTITY: Cumulative Time](https://img.shields.io/badge/ENTITY-Cumulative-Time-d97706) — Cumulative Time
- ![ENTITY: Call Count](https://img.shields.io/badge/ENTITY-Call-Count-d97706) — Call Count
- ![ENTITY: Benchmark](https://img.shields.io/badge/ENTITY-Benchmark-d97706) — Benchmark
- ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) — CPU-bound
- ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I-O-bound-0891b2) — I/O-bound
- ![ENTITY: Native Code](https://img.shields.io/badge/ENTITY-Native-Code-0f766e) — Native Code
- ![ENTITY: Function Call](https://img.shields.io/badge/ENTITY-Function-Call-2563eb) — Function Call
- ![ENTITY: Return Value](https://img.shields.io/badge/ENTITY-Return-Value-16a34a) — Return Value
- ![ENTITY: Exception](https://img.shields.io/badge/ENTITY-Exception-dc2626) — Exception
- ![ENTITY: Suspension Point](https://img.shields.io/badge/ENTITY-Suspension-Point-0891b2) — Suspension Point
- ![ENTITY: Await](https://img.shields.io/badge/ENTITY-Await-0891b2) — Await
- ![ENTITY: Yield](https://img.shields.io/badge/ENTITY-Yield-0891b2) — Yield
- ![ENTITY: Cancellation](https://img.shields.io/badge/ENTITY-Cancellation-dc2626) — Cancellation
- ![ENTITY: Call Stack](https://img.shields.io/badge/ENTITY-Call-Stack-64748b) — Call Stack
- ![ENTITY: Latency](https://img.shields.io/badge/ENTITY-Latency-d97706) — Latency
- ![ENTITY: Throughput](https://img.shields.io/badge/ENTITY-Throughput-d97706) — Throughput

## PY-001 — GIL ![ENTITY: GIL](https://img.shields.io/badge/ENTITY-GIL-2563eb), конкурентность и параллелизм ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Что такое Global Interpreter Lock (GIL) в CPython ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b) и как он влияет на конкурентность и параллелизм?

**Оригинальная формулировка (EN):** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) and parallelism ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706)?

**Что оценивается:** Синхронизация runtime CPython, CPU-bound ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) и I/O-bound ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) нагрузки, потокобезопасность, выбор модели конкурентности и free-threaded ![ENTITY: Free-threaded](https://img.shields.io/badge/ENTITY-Free-threaded-0f766e) Python.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core / высокая частота на технических интервью

Дополнительные вопросы:

- **FU-1 — Механизм:** Почему традиционная сборка CPython использует GIL и что именно защищает эта блокировка? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как GIL влияет на CPU-bound и I/O-bound многопоточные нагрузки в традиционной сборке CPython? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Архитектурный выбор:** Как выбрать между threading ![ENTITY: Multithreading](https://img.shields.io/badge/ENTITY-Multithreading-16a34a), multiprocessing ![ENTITY: Multiprocessing](https://img.shields.io/badge/ENTITY-Multiprocessing-7c3aed) и asyncio ![ENTITY: Asyncio](https://img.shields.io/badge/ENTITY-Asyncio-0891b2) для нагрузки Python backend? ![TYPE](https://img.shields.io/badge/TYPE-Design_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Что меняется в free-threaded CPython и что инженерной команде следует проверить перед его внедрением? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-002 — Конкурентность и параллелизм ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** В чём разница между конкурентность ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9)ю и параллелизмом и почему это различие важно в Python?

**Оригинальная формулировка (EN):** What is the difference between concurrency and parallelism, and why is the distinction important in Python?

**Что оценивается:** Различие конкурентности и одновременного выполнения, I/O-bound ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) и CPU-bound ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) нагрузки, выбор подходящей модели выполнения в Python.  
**Уровень:** L2–L3 — Intermediate/Advanced  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Основы:** Может ли конкурентность существовать без параллелизма? ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Fundamentals-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Анализ нагрузки:** Чем отличаются I/O-bound и CPU-bound задачи? ![ENTITY: I/O-bound](https://img.shields.io/badge/ENTITY-I/O-bound-0891b2) ![ENTITY: CPU-bound](https://img.shields.io/badge/ENTITY-CPU-bound-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Workload_analysis-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Поведение CPython ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b):** Как GIL ![ENTITY: GIL](https://img.shields.io/badge/ENTITY-GIL-2563eb) влияет на конкурентность и параллелизм в CPython? ![TYPE](https://img.shields.io/badge/TYPE-CPython_behavior-64748b) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как определить, нужна ли задаче конкурентность или параллелизм? ![ENTITY: Concurrency](https://img.shields.io/badge/ENTITY-Concurrency-0ea5e9) ![ENTITY: Parallelism](https://img.shields.io/badge/ENTITY-Parallelism-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-003 — Модель исполнения Python ![ENTITY: Python](https://img.shields.io/badge/ENTITY-Python-2563eb) и runtime ![ENTITY: Runtime](https://img.shields.io/badge/ENTITY-Runtime-0ea5e9) ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как Python выполняет программу: от исходного кода до поведения во время выполнения?

**Что оценивается:** Компиляция, байткод ![ENTITY: Python Bytecode](https://img.shields.io/badge/ENTITY-Python-Bytecode-64748b), модель интерпретатор ![ENTITY: Interpreter](https://img.shields.io/badge/ENTITY-Interpreter-64748b)а и runtime.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какие основные этапы проходит исходный код Python до выполнения инструкций в CPython ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b)? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как бы вы исследовали ситуацию, когда модуль ![ENTITY: Module](https://img.shields.io/badge/ENTITY-Module-0ea5e9) Python ведёт себя по-разному при запуске как скрипт и при импорт ![ENTITY: Import](https://img.shields.io/badge/ENTITY-Import-0ea5e9)е из другого модуля? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и компромиссы:** Какие аспекты байткода и поведения интерпретатора являются деталями реализации, а не гарантиями языка, и почему это различие важно? ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b) ![ENTITY: Python Bytecode](https://img.shields.io/badge/ENTITY-Python-Bytecode-64748b) ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как при диагностике production-проблемы определить, нужно ли исследовать поведение на уровне Python, внутреннее устройство CPython или окружение операционной системы ![ENTITY: Operating System](https://img.shields.io/badge/ENTITY-Operating-System-64748b) и runtime? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## Статус покрытия

- PY-001–PY-019 и соответствующие 76 дополнительных вопросов с локальной нумерацией FU-1–FU-4: материалы подготовлены на русском; независимая техническая и редакторская проверки ожидаются.
- Оставшиеся основные вопросы PY-020–PY-045 и соответствующие 104 дополнительных вопроса: ещё не подготовлены в раздельной языковой структуре.

**Правило распределения:** для каждого Main Question предусматриваются ровно четыре Follow-up: механизм, практическое применение, граничные случаи и компромиссы, а также Senior-level суждение или production-последствия.


## PY-004 — Вызовы функций и состояние выполнения ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Что происходит при вызове функции в CPython?

**Что оценивается:** Семантика вызова, связывание аргументов ![ENTITY: Argument Binding](https://img.shields.io/badge/ENTITY-Argument-Binding-7c3aed), function/code objects, состояние выполнения, frames, closures, возврат значений и распространение исключений.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какое состояние выполнения CPython должен создать или поддерживать при входе в Python-функцию и во время её выполнения? ![ENTITY: Execution Frame](https://img.shields.io/badge/ENTITY-Execution-Frame-0ea5e9) ![ENTITY: _PyInterpreterFrame](https://img.shields.io/badge/ENTITY-_PyInterpreterFrame-64748b) ![ENTITY: PyFrameObject](https://img.shields.io/badge/ENTITY-PyFrameObject-64748b) ![ENTITY: Closure Cell](https://img.shields.io/badge/ENTITY-Closure-Cell-16a34a) ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как с помощью профилирования и информации о стеке вызовов исследовать чрезмерные накладные расходы на вызовы функций в Python-сервисе? ![ENTITY: Profiler](https://img.shields.io/badge/ENTITY-Profiler-16a34a) ![ENTITY: Call Stack](https://img.shields.io/badge/ENTITY-Call-Stack-64748b) ![ENTITY: Self Time](https://img.shields.io/badge/ENTITY-Self-Time-d97706) ![ENTITY: Cumulative Time](https://img.shields.io/badge/ENTITY-Cumulative-Time-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и жизненный цикл:** Как рекурсия ![ENTITY: Recursion](https://img.shields.io/badge/ENTITY-Recursion-7c3aed), исключения, генератор ![ENTITY: Generator](https://img.shields.io/badge/ENTITY-Generator-0891b2)ы и асинхронные функции влияют на жизненный цикл выполнения по сравнению с обычным вызовом функции? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** В каких случаях знание механики вызовов CPython может существенно повлиять на решение об оптимизации и как проверить, что такая оптимизация действительно оправданна? ![ENTITY: CPython](https://img.shields.io/badge/ENTITY-CPython-64748b) ![ENTITY: Vectorcall](https://img.shields.io/badge/ENTITY-Vectorcall-0891b2) ![ENTITY: Benchmark](https://img.shields.io/badge/ENTITY-Benchmark-d97706) ![ENTITY: Latency](https://img.shields.io/badge/ENTITY-Latency-d97706) ![ENTITY: Throughput](https://img.shields.io/badge/ENTITY-Throughput-d97706) ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-005 — Объектная модель Python: идентичность, тип и значение ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Объясните объектную модель Python: идентичность, тип и значение объекта.

**Что оценивается:** Связывание имён, различие идентичности и равенства, изменяемость, проверки типов и доменная идентичность.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какие из характеристик объекта — идентичность, тип и значение — могут изменяться в течение его жизненного цикла? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как выбирать между проверками идентичности, равенства и типа при code review? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и компромиссы:** Почему использование is для сравнения строк, чисел и других значений может приводить к ненадёжным результатам? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как при проектировании API избежать случайной зависимости от идентичности объектов, их изменяемости или конкретных типов реализации? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-006 — Поиск атрибутов, дескрипторы и специальные методы ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как Python выполняет поиск атрибутов и какую роль в этом процессе играют дескрипторы и специальные методы?

**Оригинальная формулировка (EN):** How does Python resolve attribute access, and how do descriptors and special methods affect that process?

**Что оценивается:** Приоритет поиска атрибутов, протокол дескрипторов, методы перехвата доступа, связывание методов и неявный поиск специальных методов.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** В каком порядке Python ищет атрибут экземпляра и как атрибут экземпляра взаимодействует с атрибутом класса? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Механизм и применение:** Чем data descriptor отличается от non-data descriptor и почему это различие важно? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism_and_application-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Чем отличаются `__getattribute__` и `__getattr__` и какие риски возникают при их переопределении? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Почему присваивание специального метода экземпляру может не изменить поведение неявной операции, например `len(obj)`? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-007 — Встроенные коллекции: семантика и выбор ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Чем списки, кортежи, множества и словари Python отличаются по семантике и внутреннему устройству?

**Оригинальная формулировка (EN):** How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

**Что оценивается:** Контракты коллекций, изменяемость, порядок, хешируемость, типичная сложность операций и компромиссы производительности и памяти.  
**Уровень:** L2–L3 — Intermediate/Advanced  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** В чём ключевые семантические и типичные реализационные различия между списками, кортежами, множествами и словарями в CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как выбрать встроенную коллекцию для упорядоченной последовательности, проверки принадлежности, удаления дубликатов и поиска по ключу в реальном сервисе? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и компромиссы:** Что учитывать при использовании порядка вставки, поверхностного копирования, вложенных изменяемых значений и средней временной сложности? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как характер нагрузки, объём данных, частота изменений и давление на память влияют на выбор коллекции и стратегию бенчмаркинга? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)


## PY-008 — Внутреннее устройство словарей и хеш-таблицы ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как словари Python работают внутри и какие последствия для производительности и корректности имеет поведение хеш-таблиц?

**Оригинальная формулировка (EN):** How do Python dictionaries work internally, and what are the performance and correctness implications of hash-table behavior?

**Что оценивается:** Хеширование, равенство, разрешение коллизий, изменение размера, сложность операций и корректность пользовательских ключей.  
**Уровень:** L2–L3 — Intermediate/Advanced  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Базовый контракт:** Какие требования должны соблюдать __hash__() и __eq__() у объектов, используемых в качестве ключей словаря? ![TYPE](https://img.shields.io/badge/TYPE-Core_contract-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Внутренний механизм:** Что происходит при коллизии ключей словаря и почему поиск или вставка могут замедляться? ![TYPE](https://img.shields.io/badge/TYPE-Internal_mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Корректность и проектирование:** Почему опасно использовать изменяемый объект как ключ словаря и как следует проектировать пользовательский тип ключа? ![TYPE](https://img.shields.io/badge/TYPE-Correctness_and_design-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Безопасность и production:** Как рандомизация хешей помогает защищать Python-сервисы и почему hash() нельзя использовать как постоянный идентификатор? ![TYPE](https://img.shields.io/badge/TYPE-Security_and_production-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-009 — Управление памятью и сборка мусора ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как работает управление памятью в Python и как взаимодействуют подсчёт ссылок и сборка мусора?

**Оригинальная формулировка (EN):** How does memory management work in Python, and how do reference counting and garbage collection interact?

**Что оценивается:** Время жизни объектов, сильные ссылки, достижимость, подсчёт ссылок, циклический GC, детерминированное освобождение ресурсов и диагностика памяти в production.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Чем подсчёт ссылок отличается от сборки циклического мусора в CPython? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Достижимость:** Почему цикл ссылок может оставаться в памяти, даже если приложение больше не использует ни один из его объектов? ![TYPE](https://img.shields.io/badge/TYPE-Reachability-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Жизненный цикл ресурсов:** Гарантируют ли del или определение __del__() немедленное уничтожение объекта или освобождение его ресурсов? ![TYPE](https://img.shields.io/badge/TYPE-Resource_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Production-диагностика:** Как бы вы исследовали устойчивый рост потребления памяти в долго работающем Python-сервисе? ![TYPE](https://img.shields.io/badge/TYPE-Production_diagnosis-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-010 — Слабые ссылки, время жизни объектов и владение памятью ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Что такое слабые ссылки (weak references) в Python, чем они отличаются от сильных ссылок и когда их следует использовать?

**Оригинальная формулировка (EN):** What are weak references in Python, how do they differ from strong references, and when should they be used?

**Что оценивается:** Сильные и слабые ссылки, API `weakref`, слабые контейнеры, поддержка weak references типами, владение объектами, кэши, observer-реестры и риски финализации.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Что именно меняется во времени жизни объекта, когда сильная ссылка заменяется слабой? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Когда в реальном приложении следует выбирать `WeakValueDictionary`, `WeakKeyDictionary` или `WeakSet`? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Можно ли создать слабую ссылку на любой объект Python и что необходимо учитывать, если класс использует `__slots__`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как спроектировать реестр на основе слабых ссылок так, чтобы не создать новую утечку памяти и ненадёжную очистку? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-011 — Context Managers, Resource Management & RAII ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как работают контекстные менеджеры Python, как они обеспечивают детерминированное управление ресурсами и чем отличаются от RAII?

**Оригинальная формулировка (EN):** How do Python context managers work, how do they provide deterministic resource management, and how do they compare with RAII?

**Что оценивается:** Протокол контекстного менеджера, жизненный цикл `with`, распространение и подавление исключений, детерминированная очистка, синхронные и асинхронные контексты, `contextlib`, exit stacks, частичное получение ресурсов и отличие от RAII.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Что именно происходит, когда блок `with` завершается из-за исключения? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Когда следует использовать `ExitStack` вместо вложенных операторов `with`? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Что происходит, если `__enter__()` завершается ошибкой или если исключение возникает внутри самого `__exit__()`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как спроектировать надёжное управление ресурсами в синхронном и асинхронном backend-приложении? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
## PY-012 — Exception Handling, Exception Hierarchy & Exception Groups ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Объясните иерархию исключений и модель обработки исключений в Python. Как работают распространение исключений, связывание причин и группы исключений?

**Оригинальная формулировка (EN):** Explain Python's exception hierarchy and exception-handling model. How do propagation, exception chaining, and exception groups work?

**Что оценивается:** Различия `BaseException` и `Exception`, выборочная обработка исключений, `try/except/else/finally`, распространение и termination model, связывание исключений, проектирование пользовательских исключений, `ExceptionGroup` и `except*`.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Почему прикладной код обычно должен перехватывать `Exception`, а не `BaseException`? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как backend должен преобразовывать низкоуровневое исключение в доменную ошибку или ошибку API? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** В чём разница между `__cause__`, `__context__` и `raise ... from None`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Когда следует использовать `ExceptionGroup` и `except*` в конкурентных системах? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-013 — Iterators, Generators & Lazy Evaluation ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Объясните модель итерации Python. В чём разница между iterable, iterator и generator и как генераторы обеспечивают ленивые вычисления?

**Оригинальная формулировка (EN):** Explain Python's iteration model. What is the difference between an iterable, an iterator, and a generator, and how do generators enable lazy evaluation?

**Что оценивается:** Различие iterable и iterator, протокол итерации (`__iter__` / `__next__`), исчерпание и `StopIteration`, создание и приостановка генератора, generator expressions и eager comprehensions, ленивые вычисления, `send()` / `throw()` / `close()`, `yield from`, PEP 479, асинхронная итерация и очистка генераторов, потоковая обработка и жизненный цикл ресурсов.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** В чём разница между iterable и iterator и почему итератор обычно хранит состояние? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Когда в backend-пайплайне обработки данных следует выбрать генератор вместо списка? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Что происходит, если внутри генератора возникает `StopIteration`, и как `yield from` выполняет делегирование? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Какие production-риски следует учитывать при использовании генераторов и асинхронных генераторов для потоков, связанных с ресурсами? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-014 — Decorators, Closures & Function Wrapping ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Объясните, как работают декораторы Python. Как декораторы связаны с замыканиями и обёртками функций и какие production-аспекты необходимо учитывать?

**Оригинальная формулировка (EN):** Explain how Python decorators work. How are decorators related to closures and function wrappers, and what production concerns should you consider?

**Что оценивается:** Применение декораторов и вычисление при определении функции, преобразование callable, выполнение wrapper, семантика замыканий и free variables, различие `nonlocal` и `global`, фабрики декораторов, `functools.wraps` / `__wrapped__`, порядок вложенных декораторов, async-aware wrappers, изменяемое состояние замыканий и конкурентность, сохранение исключений и возвращаемых значений.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Как Python применяет декоратор и когда именно он выполняется? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как спроектировать настраиваемый декоратор для логирования, повторных попыток или контроля доступа? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Что такое замыкание, как работает `nonlocal` и какие проблемы может создавать изменяемое состояние замыкания? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Почему `functools.wraps`, порядок декораторов и поддержка async важны в production-системах? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-015 — Scope, LEGB Rule & Name Resolution** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Механизм:** Как Python применяет LEGB и определяет локальные имена? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Применение:** Как диагностировать UnboundLocalError и выбрать local, global или nonlocal? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Граничные случаи:** Почему методы не замыкают namespace класса и что такое late binding? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior-level суждение:** Как управлять областями видимости и динамическим поиском имён в production? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-016 — Mutable vs Immutable Objects, Aliasing & Object Sharing** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Механизм:** В чём разница между mutation, rebinding и aliasing? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Применение:** Чем отличаются shallow copy и deep copy и когда применять каждый вариант? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Граничные случаи:** Почему tuple может содержать изменяемое состояние и что происходит при передаче mutable-объектов в функцию? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior-level суждение:** Как предотвращать непреднамеренное совместное использование mutable-состояния в production? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-017 — Python Argument Passing, Parameter Semantics & Function Signatures** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Механизм:** Как Python связывает позиционные и именованные аргументы и какие ошибки могут возникнуть? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Применение:** Когда API следует использовать positional-only и keyword-only параметры? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Граничные случаи:** Почему изменяемые значения по умолчанию опасны и какова роль аннотаций? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior-level суждение:** Как анализировать и проверять сигнатуры callable в production-инструментах и фреймворках? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
- **PY-018 — Python Functions: First-Class Objects, Higher-Order Functions & Functional Programming** ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)
  - **FU-1 — Механизм:** Что означает, что функция является объектом первого класса, и чем это отличается от callable? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
  - **FU-2 — Применение:** Как применять функции высшего порядка в backend-приложении? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
  - **FU-3 — Граничные случаи:** Какие риски связаны с late binding и общим изменяемым состоянием замыкания? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
  - **FU-4 — Senior-level суждение:** Когда выбирать функциональную композицию вместо классов или императивного кода? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)


## PY-019 — Lambda-функции, анонимные функции и функциональные идиомы ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2--L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P1-d97706)

**Основной вопрос:** Что такое lambda-выражения в Python, как они работают и когда их следует использовать вместо именованных функций?

**Оригинальная формулировка (EN):** What are lambda expressions in Python, how do they work, and when should you use them instead of named functions?

**Что оценивается:** Синтаксис и семантика lambda, объекты-функции, тело из одного выражения, замыкания, практическое применение callbacks, читаемость и выбор между lambda, def и встроенными идиомами.  
**Уровень:** L2–L3 — Intermediate/Advanced  
**Приоритет:** P1 — Важная тема Python Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какой объект-функцию создаёт lambda-выражение и чем его тело отличается от функции, определённой через def? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** В каких API Python и преобразованиях данных полезны lambda-функции? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи:** Как lambda-выражения взаимодействуют с замыканиями, late binding, значениями параметров по умолчанию и introspection? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Когда следует заменить lambda именованной функцией или более понятным встроенным выражением? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)
