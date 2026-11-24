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

- ![GIL](https://img.shields.io/badge/-GIL-2563eb?style=flat-square) — GIL
- ![Thread](https://img.shields.io/badge/-Thread-16a34a?style=flat-square) — Thread
- ![Process](https://img.shields.io/badge/-Process-7c3aed?style=flat-square) — Process
- ![Multithreading](https://img.shields.io/badge/-Multithreading-16a34a?style=flat-square) — Multithreading
- ![Multiprocessing](https://img.shields.io/badge/-Multiprocessing-7c3aed?style=flat-square) — Multiprocessing
- ![Concurrency](https://img.shields.io/badge/-Concurrency-0ea5e9?style=flat-square) — Concurrency
- ![Parallelism](https://img.shields.io/badge/-Parallelism-d97706?style=flat-square) — Parallelism
- ![CPU-bound](https://img.shields.io/badge/-CPU-bound-d97706?style=flat-square) — CPU-bound
- ![I/O-bound](https://img.shields.io/badge/-I%2FO-bound-0891b2?style=flat-square) — I/O-bound
- ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square) — CPython
- ![Python Bytecode](https://img.shields.io/badge/-Python-Bytecode-64748b?style=flat-square) — Python Bytecode
- ![Native Extension](https://img.shields.io/badge/-Native-Extension-0f766e?style=flat-square) — Native Extension
- ![Mutex](https://img.shields.io/badge/-Mutex-be123c?style=flat-square) — Mutex
- ![Condition Variable](https://img.shields.io/badge/-Condition-Variable-be123c?style=flat-square) — Condition Variable
- ![Lock](https://img.shields.io/badge/-Lock-be123c?style=flat-square) — Lock
- ![Free-threaded](https://img.shields.io/badge/-Free-threaded-0f766e?style=flat-square) — Free-threaded
- ![Asyncio](https://img.shields.io/badge/-Asyncio-0891b2?style=flat-square) — Asyncio
- ![Task](https://img.shields.io/badge/-Task-0ea5e9?style=flat-square) — Task
- ![Synchronization](https://img.shields.io/badge/-Synchronization-be123c?style=flat-square) — Synchronization
- ![Thread Safety](https://img.shields.io/badge/-Thread-Safety-16a34a?style=flat-square) — Thread Safety
- ![Shared State](https://img.shields.io/badge/-Shared-State-d97706?style=flat-square) — Shared State

- ![Callable](https://img.shields.io/badge/-Callable-2563eb?style=flat-square) — Callable
- ![Argument Binding](https://img.shields.io/badge/-Argument-Binding-7c3aed?style=flat-square) — Argument Binding
- ![Parameter](https://img.shields.io/badge/-Parameter-7c3aed?style=flat-square) — Parameter
- ![Execution Frame](https://img.shields.io/badge/-Execution-Frame-0ea5e9?style=flat-square) — Execution Frame
- ![_PyInterpreterFrame](https://img.shields.io/badge/-_PyInterpreterFrame-64748b?style=flat-square) — _PyInterpreterFrame
- ![PyFrameObject](https://img.shields.io/badge/-PyFrameObject-64748b?style=flat-square) — PyFrameObject
- ![Closure Cell](https://img.shields.io/badge/-Closure-Cell-16a34a?style=flat-square) — Closure Cell
- ![Global Namespace](https://img.shields.io/badge/-Global-Namespace-64748b?style=flat-square) — Global Namespace
- ![Builtins Namespace](https://img.shields.io/badge/-Builtins-Namespace-64748b?style=flat-square) — Builtins Namespace
- ![Traceback](https://img.shields.io/badge/-Traceback-d97706?style=flat-square) — Traceback
- ![Vectorcall](https://img.shields.io/badge/-Vectorcall-0891b2?style=flat-square) — Vectorcall
- ![tp_call](https://img.shields.io/badge/-tp_call-0891b2?style=flat-square) — tp_call
- ![Generator](https://img.shields.io/badge/-Generator-0891b2?style=flat-square) — Generator
- ![Coroutine](https://img.shields.io/badge/-Coroutine-0891b2?style=flat-square) — Coroutine
- ![Event Loop](https://img.shields.io/badge/-Event-Loop-0891b2?style=flat-square) — Event Loop
- ![Recursion](https://img.shields.io/badge/-Recursion-7c3aed?style=flat-square) — Recursion
- ![Profiler](https://img.shields.io/badge/-Profiler-16a34a?style=flat-square) — Profiler
- ![Sampling Profiler](https://img.shields.io/badge/-Sampling-Profiler-16a34a?style=flat-square) — Sampling Profiler
- ![Self Time](https://img.shields.io/badge/-Self-Time-d97706?style=flat-square) — Self Time
- ![Cumulative Time](https://img.shields.io/badge/-Cumulative-Time-d97706?style=flat-square) — Cumulative Time
- ![Call Count](https://img.shields.io/badge/-Call-Count-d97706?style=flat-square) — Call Count
- ![Benchmark](https://img.shields.io/badge/-Benchmark-d97706?style=flat-square) — Benchmark
- ![CPU-bound](https://img.shields.io/badge/-CPU-bound-d97706?style=flat-square) — CPU-bound
- ![I/O-bound](https://img.shields.io/badge/-I-O-bound-0891b2?style=flat-square) — I/O-bound
- ![Native Code](https://img.shields.io/badge/-Native-Code-0f766e?style=flat-square) — Native Code
- ![Function Call](https://img.shields.io/badge/-Function-Call-2563eb?style=flat-square) — Function Call
- ![Return Value](https://img.shields.io/badge/-Return-Value-16a34a?style=flat-square) — Return Value
- ![Exception](https://img.shields.io/badge/-Exception-dc2626?style=flat-square) — Exception
- ![Suspension Point](https://img.shields.io/badge/-Suspension-Point-0891b2?style=flat-square) — Suspension Point
- ![Await](https://img.shields.io/badge/-Await-0891b2?style=flat-square) — Await
- ![Yield](https://img.shields.io/badge/-Yield-0891b2?style=flat-square) — Yield
- ![Cancellation](https://img.shields.io/badge/-Cancellation-dc2626?style=flat-square) — Cancellation
- ![Call Stack](https://img.shields.io/badge/-Call-Stack-64748b?style=flat-square) — Call Stack
- ![Latency](https://img.shields.io/badge/-Latency-d97706?style=flat-square) — Latency
- ![Throughput](https://img.shields.io/badge/-Throughput-d97706?style=flat-square) — Throughput

- ![Object](https://img.shields.io/badge/-Object-2563eb?style=flat-square) — Object
- ![Identity](https://img.shields.io/badge/-Identity-64748b?style=flat-square) — Identity
- ![Type](https://img.shields.io/badge/-Type-7c3aed?style=flat-square) — Type
- ![Value](https://img.shields.io/badge/-Value-0ea5e9?style=flat-square) — Value
- ![Name Binding](https://img.shields.io/badge/-Name-Binding-7c3aed?style=flat-square) — Name Binding
- ![Equality](https://img.shields.io/badge/-Equality-0ea5e9?style=flat-square) — Equality
- ![Mutability](https://img.shields.io/badge/-Mutability-d97706?style=flat-square) — Mutability
- ![Mutable Object](https://img.shields.io/badge/-Mutable-Object-d97706?style=flat-square) — Mutable Object
- ![Immutable Object](https://img.shields.io/badge/-Immutable-Object-0891b2?style=flat-square) — Immutable Object
- ![Reference](https://img.shields.io/badge/-Reference-64748b?style=flat-square) — Reference
- ![Aliasing](https://img.shields.io/badge/-Aliasing-d97706?style=flat-square) — Aliasing
- ![Rebinding](https://img.shields.io/badge/-Rebinding-0891b2?style=flat-square) — Rebinding
- ![Domain Identity](https://img.shields.io/badge/-Domain-Identity-16a34a?style=flat-square) — Domain Identity
- ![id()](https://img.shields.io/badge/-id%28%29-64748b?style=flat-square) — id()
- ![is](https://img.shields.io/badge/-is-2563eb?style=flat-square) — is
- ![==](https://img.shields.io/badge/-%3D%3D-0ea5e9?style=flat-square) — ==
- ![isinstance()](https://img.shields.io/badge/-isinstance%28%29-7c3aed?style=flat-square) — isinstance()
- ![__eq__](https://img.shields.io/badge/-__eq__-0ea5e9?style=flat-square) — __eq__
- ![__hash__](https://img.shields.io/badge/-__hash__-7c3aed?style=flat-square) — __hash__
- ![Hashability](https://img.shields.io/badge/-Hashability-7c3aed?style=flat-square) — Hashability

## PY-001 — GIL ![GIL](https://img.shields.io/badge/-GIL-2563eb?style=flat-square), конкурентность и параллелизм ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Что такое Global Interpreter Lock (GIL) в CPython ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square) и как он влияет на конкурентность и параллелизм?

**Оригинальная формулировка (EN):** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency ![Concurrency](https://img.shields.io/badge/-Concurrency-0ea5e9?style=flat-square) and parallelism ![Parallelism](https://img.shields.io/badge/-Parallelism-d97706?style=flat-square)?

**Что оценивается:** Синхронизация runtime CPython, CPU-bound ![CPU-bound](https://img.shields.io/badge/-CPU-bound-d97706?style=flat-square) и I/O-bound ![I/O-bound](https://img.shields.io/badge/-I%2FO-bound-0891b2?style=flat-square) нагрузки, потокобезопасность, выбор модели конкурентности и free-threaded ![Free-threaded](https://img.shields.io/badge/-Free-threaded-0f766e?style=flat-square) Python.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core / высокая частота на технических интервью

Дополнительные вопросы:

- **FU-1 — Механизм:** Почему традиционная сборка CPython использует GIL и что именно защищает эта блокировка? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как GIL влияет на CPU-bound и I/O-bound многопоточные нагрузки в традиционной сборке CPython? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Архитектурный выбор:** Как выбрать между threading ![Multithreading](https://img.shields.io/badge/-Multithreading-16a34a?style=flat-square), multiprocessing ![Multiprocessing](https://img.shields.io/badge/-Multiprocessing-7c3aed?style=flat-square) и asyncio ![Asyncio](https://img.shields.io/badge/-Asyncio-0891b2?style=flat-square) для нагрузки Python backend? ![TYPE](https://img.shields.io/badge/TYPE-Design_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Что меняется в free-threaded CPython и что инженерной команде следует проверить перед его внедрением? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-002 — Конкурентность и параллелизм ![Parallelism](https://img.shields.io/badge/-Parallelism-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** В чём разница между конкурентность ![Concurrency](https://img.shields.io/badge/-Concurrency-0ea5e9?style=flat-square)ю и параллелизмом и почему это различие важно в Python?

**Оригинальная формулировка (EN):** What is the difference between concurrency and parallelism, and why is the distinction important in Python?

**Что оценивается:** Различие конкурентности и одновременного выполнения, I/O-bound ![I/O-bound](https://img.shields.io/badge/-I%2FO-bound-0891b2?style=flat-square) и CPU-bound ![CPU-bound](https://img.shields.io/badge/-CPU-bound-d97706?style=flat-square) нагрузки, выбор подходящей модели выполнения в Python.  
**Уровень:** L2–L3 — Intermediate/Advanced  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Основы:** Может ли конкурентность существовать без параллелизма? ![Concurrency](https://img.shields.io/badge/-Concurrency-0ea5e9?style=flat-square) ![Parallelism](https://img.shields.io/badge/-Parallelism-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Fundamentals-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Анализ нагрузки:** Чем отличаются I/O-bound и CPU-bound задачи? ![I/O-bound](https://img.shields.io/badge/-I%2FO-bound-0891b2?style=flat-square) ![CPU-bound](https://img.shields.io/badge/-CPU-bound-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Workload_analysis-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Поведение CPython ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square):** Как GIL ![GIL](https://img.shields.io/badge/-GIL-2563eb?style=flat-square) влияет на конкурентность и параллелизм в CPython? ![TYPE](https://img.shields.io/badge/TYPE-CPython_behavior-64748b) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как определить, нужна ли задаче конкурентность или параллелизм? ![Concurrency](https://img.shields.io/badge/-Concurrency-0ea5e9?style=flat-square) ![Parallelism](https://img.shields.io/badge/-Parallelism-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## PY-003 — Модель исполнения Python ![Python](https://img.shields.io/badge/-Python-2563eb?style=flat-square) и runtime ![Runtime](https://img.shields.io/badge/-Runtime-0ea5e9?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Как Python выполняет программу: от исходного кода до поведения во время выполнения?

**Что оценивается:** Компиляция, байткод ![Python Bytecode](https://img.shields.io/badge/-Python-Bytecode-64748b?style=flat-square), модель интерпретатор ![Interpreter](https://img.shields.io/badge/-Interpreter-64748b?style=flat-square)а и runtime.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какие основные этапы проходит исходный код Python до выполнения инструкций в CPython ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square)? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как бы вы исследовали ситуацию, когда модуль ![Module](https://img.shields.io/badge/-Module-0ea5e9?style=flat-square) Python ведёт себя по-разному при запуске как скрипт и при импорт ![Import](https://img.shields.io/badge/-Import-0ea5e9?style=flat-square)е из другого модуля? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и компромиссы:** Какие аспекты байткода и поведения интерпретатора являются деталями реализации, а не гарантиями языка, и почему это различие важно? ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square) ![Python Bytecode](https://img.shields.io/badge/-Python-Bytecode-64748b?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как при диагностике production-проблемы определить, нужно ли исследовать поведение на уровне Python, внутреннее устройство CPython или окружение операционной системы ![Operating System](https://img.shields.io/badge/-Operating-System-64748b?style=flat-square) и runtime? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

## Статус покрытия

- PY-001–PY-019 и соответствующие 76 дополнительных вопросов с локальной нумерацией FU-1–FU-4: материалы подготовлены на русском; независимая техническая и редакторская проверки ожидаются.
- Оставшиеся основные вопросы PY-020–PY-045 и соответствующие 104 дополнительных вопроса: ещё не подготовлены в раздельной языковой структуре.

**Правило распределения:** для каждого Main Question предусматриваются ровно четыре Follow-up: механизм, практическое применение, граничные случаи и компромиссы, а также Senior-level суждение или production-последствия.


## PY-004 — Вызовы функций и состояние выполнения ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Что происходит при вызове функции в CPython?

**Что оценивается:** Семантика вызова, связывание аргументов ![Argument Binding](https://img.shields.io/badge/-Argument-Binding-7c3aed?style=flat-square), function/code objects, состояние выполнения, frames, closures, возврат значений и распространение исключений.  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какое состояние выполнения CPython должен создать или поддерживать при входе в Python-функцию и во время её выполнения? ![Execution Frame](https://img.shields.io/badge/-Execution-Frame-0ea5e9?style=flat-square) ![_PyInterpreterFrame](https://img.shields.io/badge/-_PyInterpreterFrame-64748b?style=flat-square) ![PyFrameObject](https://img.shields.io/badge/-PyFrameObject-64748b?style=flat-square) ![Closure Cell](https://img.shields.io/badge/-Closure-Cell-16a34a?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как с помощью профилирования и информации о стеке вызовов исследовать чрезмерные накладные расходы на вызовы функций в Python-сервисе? ![Profiler](https://img.shields.io/badge/-Profiler-16a34a?style=flat-square) ![Call Stack](https://img.shields.io/badge/-Call-Stack-64748b?style=flat-square) ![Self Time](https://img.shields.io/badge/-Self-Time-d97706?style=flat-square) ![Cumulative Time](https://img.shields.io/badge/-Cumulative-Time-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и жизненный цикл:** Как рекурсия ![Recursion](https://img.shields.io/badge/-Recursion-7c3aed?style=flat-square), исключения, генератор ![Generator](https://img.shields.io/badge/-Generator-0891b2?style=flat-square)ы и асинхронные функции влияют на жизненный цикл выполнения по сравнению с обычным вызовом функции? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** В каких случаях знание механики вызовов CPython может существенно повлиять на решение об оптимизации и как проверить, что такая оптимизация действительно оправданна? ![CPython](https://img.shields.io/badge/-CPython-64748b?style=flat-square) ![Vectorcall](https://img.shields.io/badge/-Vectorcall-0891b2?style=flat-square) ![Benchmark](https://img.shields.io/badge/-Benchmark-d97706?style=flat-square) ![Latency](https://img.shields.io/badge/-Latency-d97706?style=flat-square) ![Throughput](https://img.shields.io/badge/-Throughput-d97706?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)



## PY-005 — Объектная модель Python: ![Object](https://img.shields.io/badge/-Object-2563eb?style=flat-square), идентичность ![Identity](https://img.shields.io/badge/-Identity-64748b?style=flat-square), тип ![Type](https://img.shields.io/badge/-Type-7c3aed?style=flat-square) и значение ![Value](https://img.shields.io/badge/-Value-0ea5e9?style=flat-square) ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Основной вопрос:** Объясните объектную модель Python: идентичность, тип и значение объекта.

**Что оценивается:** Связывание имён ![Name Binding](https://img.shields.io/badge/-Name-Binding-7c3aed?style=flat-square), различие идентичности и равенства ![Equality](https://img.shields.io/badge/-Equality-0ea5e9?style=flat-square), изменяемость ![Mutability](https://img.shields.io/badge/-Mutability-d97706?style=flat-square), проверки типов и доменная идентичность ![Domain Identity](https://img.shields.io/badge/-Domain-Identity-16a34a?style=flat-square).  
**Уровень:** L3 — Advanced/Senior  
**Приоритет:** P0 — Core

Дополнительные вопросы:

- **FU-1 — Механизм:** Какие из характеристик объекта — идентичность, тип и значение — могут изменяться в течение его жизненного цикла? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)
- **FU-2 — Практическое применение:** Как выбирать между проверками идентичности, равенства и типа при code review? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)
- **FU-3 — Граничные случаи и компромиссы:** Почему использование is ![is](https://img.shields.io/badge/-is-2563eb?style=flat-square) для сравнения строк, чисел и других значений может приводить к ненадёжным результатам? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)
- **FU-4 — Senior-level суждение:** Как при проектировании API избежать случайной зависимости от идентичности объектов, их изменяемости ![Mutability](https://img.shields.io/badge/-Mutability-d97706?style=flat-square) или конкретных типов реализации? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

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
