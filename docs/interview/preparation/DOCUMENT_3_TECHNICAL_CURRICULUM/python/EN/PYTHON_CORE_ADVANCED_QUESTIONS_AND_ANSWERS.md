# Python Core & Advanced Python — Questions and Answers (EN)

**Language:** English  
**Domain:** Python Core & Advanced Python  
**Python baseline:** 3.15.2. Version-specific behavior is labelled; language guarantees are distinguished from CPython implementation details.  
**Question map:** [English Question Map](./PYTHON_CORE_ADVANCED.md)  
**Navigation:** [Python curriculum index](../README.md)

English study material for PY-001–PY-018. Each Main Question has four locally numbered Follow-ups (FU-1 to FU-4). The Russian version uses the same question IDs.

**Numbering rule:** Every Main Question has exactly four Follow-ups, numbered locally as FU-1, FU-2, FU-3, and FU-4. The parent PY ID keeps each GitHub heading unique (for example, PY-018 / FU-1).

**Review status:** Authored; independent technical and editorial review pending. Do not treat this material as finally approved until both reviews are complete.

# PY-001 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency and parallelism?

## Understand the idea

In the conventional GIL-enabled CPython build, only one thread at a time can hold the GIL and execute Python bytecode. Think of it as a shared key: one thread has it, while the others wait for their turn. This is a simplified analogy, but it captures the main idea.

The GIL helps CPython coordinate access to interpreter state and Python objects. Historically, it also simplified reference counting and the integration of C extensions.

## Concurrency and parallelism

- **Concurrency:** multiple tasks make progress during overlapping periods; they do not have to run at exactly the same instant.
- **Parallelism:** multiple tasks execute at the same time, for example on different CPU cores.

With the conventional GIL-enabled build, threads can provide concurrency, but CPU-bound pure-Python threads generally cannot execute Python bytecode in parallel across multiple cores.

## When does the GIL matter?

- **I/O-bound work:** threads can be useful. While one thread waits for network, file, or other blocking I/O, the GIL is typically released and another thread can run.
- **CPU-bound pure-Python work:** adding threads usually does not provide multi-core parallelism. Multiprocessing may be a better fit.
- **Native extensions:** some libraries release the GIL while running native code, so their computations may run in parallel.

## Does the GIL make code thread-safe?

No. The GIL protects interpreter-level operations; it does not automatically protect application-level business logic. A sequence such as “read a value, modify it, write it back” may still need an explicit lock or another synchronization design.

## Is the GIL a mutex?

At a high level, the GIL is commonly described as a global mutual-exclusion lock. More precisely, in CPython 3.15.2 its state is protected by an internal mutex, and a condition variable is used to coordinate waiting threads. So “the GIL acts like a global mutex” is a useful simplification; “it is implemented as one ordinary mutex” is not precise.

## What about Python 3.15.2?

CPython also has an optional **free-threaded build**, introduced experimentally in Python 3.13 and officially supported as an optional configuration from Python 3.14. It can run Python threads in parallel without the traditional GIL.

It is not the default build. Some C extensions are not compatible and may cause the GIL to be enabled again. Free-threading does not guarantee that every application becomes faster: compatibility, synchronization, memory use, and real workload performance must be checked.

For runtime verification, `sysconfig.get_config_var("Py_GIL_DISABLED")` indicates whether the interpreter was built with free-threading support, while `sys._is_gil_enabled()` reports whether the GIL is currently enabled. A free-threaded build can run with the GIL enabled through `PYTHON_GIL` or `-X gil`; importing an extension that does not declare free-threading support can also enable it.

## Interview-ready answer (EN)

“The Global Interpreter Lock, or GIL, is an interpreter-level mutual-exclusion mechanism in the conventional CPython build. It allows only one thread at a time to hold the GIL and execute Python bytecode. This simplifies coordination around interpreter state and object management, but limits multi-core parallelism for CPU-bound pure-Python threads.

Threads are still useful for I/O-bound work because blocking I/O typically releases the GIL. For CPU-bound Python workloads, multiprocessing may be more appropriate, while some native extensions can release the GIL during computation. The GIL also does not guarantee application-level thread safety, so shared state may still require explicit synchronization.

Python additionally supports optional free-threaded builds, which can execute threads in parallel without the GIL. Before adopting one, I would verify dependency compatibility and benchmark the actual workload.”

---

## PY-001 / FU-1 — What does the GIL protect? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What does the GIL protect, and why does CPython use it?

**Explanation**

The GIL coordinates access to parts of CPython's internal state and Python objects. Historically, this simplified reference counting and runtime implementation. It does not protect every resource used by an application.

**Interview answer (EN)**

“The GIL coordinates access to interpreter-managed state and objects in the conventional CPython build. It historically simplified reference counting and runtime implementation. Its scope is limited, however: it does not protect arbitrary application data, database transactions, or external resources.”

---

## PY-001 / FU-2 — How does the GIL affect CPU-bound and I/O-bound work? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads?

**Explanation**

CPU-bound work spends most of its time calculating. I/O-bound work spends much of its time waiting for external operations. The GIL limits parallel execution of pure-Python CPU work, but blocking I/O typically releases it so another thread can run.

**Interview answer (EN)**

“In a conventional CPython build, CPU-bound pure-Python threads compete for the GIL and generally do not execute Python bytecode in parallel across cores. I/O-bound threads can still be effective because blocking I/O typically releases the GIL, allowing other threads to run while one is waiting.”

---

## PY-001 / FU-3 — How do you choose between threading, multiprocessing, and asyncio? ![TYPE](https://img.shields.io/badge/TYPE-Design_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** How would you choose between threading, multiprocessing, and asyncio for a Python backend workload?

**Explanation**

- **Threading:** useful for blocking I/O and some native libraries.
- **Multiprocessing:** useful for CPU-bound Python work; separate processes can run on different CPU cores.
- **Asyncio:** useful for many concurrent I/O tasks when libraries support non-blocking operations. It does not make CPU-heavy code parallel by itself.

**Interview answer (EN)**

“I first identify whether the workload mainly waits for I/O or performs CPU-intensive Python work. I use threads for blocking I/O, multiprocessing for CPU-bound Python tasks when process overhead is justified, and asyncio for high-concurrency I/O when the call stack supports non-blocking operations. I also consider latency, memory, cancellation, backpressure, and operational complexity.”

---

## PY-001 / FU-4 — What changes in free-threaded CPython? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** What changes in free-threaded CPython, and what should a team check before adopting it?

**Explanation**

A free-threaded build can execute Python threads in parallel without the traditional GIL. Dependencies, especially C extensions, must support it. The application must also synchronize shared state correctly.

**Interview answer (EN)**

“Free-threaded CPython is an optional build that allows Python threads to execute in parallel without the traditional GIL. Before adopting it, I would verify that dependencies and C extensions support free-threading, audit shared mutable state for race conditions, and benchmark representative workloads. I would not assume that removing the GIL automatically improves performance.”

**References**
- [Python 3.15.2 — Thread states and the GIL](https://docs.python.org/3.15/c-api/threads.html)
- [Python 3.15.2 — Threading](https://docs.python.org/3.15/library/threading.html)
- [Python 3.15.2 — Free-threaded Python](https://docs.python.org/3.15/howto/free-threading-python.html)
- [CPython 3.15.2 GIL implementation](https://github.com/python/cpython/blob/v3.15.2/Python/ceval_gil.c)

---

# PY-002 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** What is the difference between concurrency and parallelism, and why is the distinction important in Python?

## Understand the idea

- **Concurrency** means managing multiple tasks whose execution overlaps in time. The system lets each task make progress, often by switching between them.
- **Parallelism** means actually executing multiple tasks at the same time, for example on different CPU cores.

Concurrency is about coordinating multiple tasks. Parallelism is about simultaneous execution. Concurrency does not require multiple CPU cores.

## How this applies to Python

- **Threading:** multiple threads within one process; useful for blocking I/O and some native libraries.
- **Multiprocessing:** separate processes that can execute on different CPU cores; often useful for CPU-bound Python workloads.
- **Asyncio:** cooperative concurrency managed by an event loop. When one coroutine awaits I/O, the event loop can run another. Asyncio does not make CPU-heavy code parallel by itself.

In a conventional GIL-enabled CPython build, multiple threads do not execute Python bytecode in parallel. They can still provide concurrency, especially while waiting for I/O. A free-threaded CPython build can execute Python code in parallel when the GIL is disabled; this is optional and not the default build.

Python 3.15.2 also documents asyncio's use in free-threaded environments. A single event loop still runs its Python task code serially on its thread, but separate event loops in separate threads can run in parallel when the GIL is disabled. Asyncio synchronization primitives remain scoped to their event loop and should not be used as cross-thread synchronization tools.

## Practical example

A backend may need to call an external API, query a database, and process a large dataset. API and database operations spend much of their time waiting for I/O, so concurrency helps keep other work moving. Processing a large dataset may be CPU-bound; if it needs multiple cores, parallel execution may be appropriate.

## Interview-ready answer (EN)

“Concurrency is the ability to manage multiple tasks whose execution overlaps in time. Parallelism means executing multiple tasks at the same time, typically on different CPU cores.

Concurrency is useful for I/O-bound workloads because a program can make progress on other tasks while one task is waiting. Parallelism is useful for CPU-bound workloads because multiple computations can run simultaneously.

In Python, threading and asyncio are commonly used for concurrency, while multiprocessing can provide parallel execution. In conventional CPython builds, the GIL limits parallel execution of Python bytecode across threads.”

---

## PY-002 / FU-1 — Can concurrency exist without parallelism? ![TYPE](https://img.shields.io/badge/TYPE-Fundamentals-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** Can concurrency exist without parallelism?

**Explanation**

Yes. A single thread can make progress on multiple tasks by switching between them, for example while some tasks are waiting for I/O. Their execution overlaps in time, but they are not running simultaneously.

**Interview answer (EN)**

“Yes. Concurrency can exist without parallelism. A single thread can make progress on multiple tasks by switching between them, for example while some tasks are waiting for I/O. The tasks overlap in time but are not executed simultaneously.”

---

## PY-002 / FU-2 — What is the difference between I/O-bound and CPU-bound workloads? ![TYPE](https://img.shields.io/badge/TYPE-Workload_analysis-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** What is the difference between I/O-bound and CPU-bound workloads?

**Explanation**

An **I/O-bound** workload spends much of its time waiting for external operations, such as network or database responses. A **CPU-bound** workload spends most of its time performing computations. Threading or asyncio can help with I/O-bound workloads; multiprocessing is often a better fit for CPU-bound Python workloads in conventional CPython.

**Interview answer (EN)**

“An I/O-bound workload spends most of its time waiting for external operations, such as network or database responses. A CPU-bound workload spends most of its time performing computations. Threading or asyncio can help with I/O-bound workloads, while multiprocessing is often a better choice for CPU-bound Python workloads.”

---

## PY-002 / FU-3 — How does the GIL affect concurrency and parallelism in CPython? ![TYPE](https://img.shields.io/badge/TYPE-CPython_behavior-64748b) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** How does the GIL affect concurrency and parallelism in CPython?

**Explanation**

In conventional CPython builds, the GIL prevents multiple threads from executing Python bytecode simultaneously. Threads can still provide concurrency, especially for I/O-bound workloads, but generally do not provide parallel execution for CPU-bound Python code. Free-threaded builds change this limitation, although extension compatibility and synchronization still matter.

**Interview answer (EN)**

“In conventional CPython builds, the GIL prevents multiple threads from executing Python bytecode simultaneously. Threads can still provide concurrency, especially for I/O-bound workloads, but they generally do not provide parallel execution for CPU-bound Python code. Free-threaded builds change this limitation, although thread safety and extension compatibility still matter.”

---

## PY-002 / FU-4 — How do you decide whether a workload needs concurrency or parallelism? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How do you decide whether a workload needs concurrency or parallelism?

**Explanation**

First identify the bottleneck. If the workload mostly waits for network, database, or disk operations, concurrency is usually the first option to consider. If it mostly performs computations, parallelism may help. Benchmark before choosing asyncio, threading, or multiprocessing; each model has overhead and complexity.

**Interview answer (EN)**

“I first identify the workload's main bottleneck. If it spends most of its time waiting for I/O, I consider concurrency through asyncio or threading. If it is CPU-bound, I consider parallel execution, often through multiprocessing in conventional CPython. I then benchmark the solution and account for the overhead and complexity of the chosen model.”

**References**
- [Python 3.15.2 — Threading](https://docs.python.org/3.15/library/threading.html)
- [Python 3.15.2 — asyncio](https://docs.python.org/3.15/library/asyncio.html)
- [Python 3.15.2 — multiprocessing](https://docs.python.org/3.15/library/multiprocessing.html)
- [Python 3.15.2 — Free-threaded Python](https://docs.python.org/3.15/howto/free-threading-python.html)

---

# PY-003 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** How does Python execute a program from source code to runtime behavior?

## The main idea

Python does not simply execute source code one line at a time as it reads it. In CPython, source code is decoded, parsed, and compiled. The resulting code objects are then executed by the interpreter.

A useful mental model:

1. **Read and decode:** CPython reads the source and decodes it into text.
2. **Parse:** the parser checks the grammar and builds an abstract syntax tree (AST).
3. **Compile:** the compiler turns the parsed program into code objects containing bytecode and metadata.
4. **Execute:** the interpreter executes those code objects in a runtime environment.
5. **Interact:** the program may call native extensions, libraries, and operating-system services.

This describes the usual CPython path. Python defines language behavior, but other Python implementations may use different execution machinery.

## Compilation is not execution

Keep three events separate:

- **Compilation:** the function body is compiled into a code object.
- **Function definition:** when execution reaches a `def` statement, Python creates a function object and binds its name.
- **Function call:** the function body starts running when the function is called.

A function body is compiled when its containing module is compiled, but it does not run just because the function was defined. A runtime error inside the body may therefore appear only when the function is called. Syntax errors are detected during parsing or compilation, before the module's top-level statements execute.

## Bytecode, code objects, and function objects

- **Bytecode** is an instruction format used by CPython's interpreter. It is not native CPU machine code.
- **Code object** stores compiled instructions and metadata, such as constants, names, and source-position information.
- **Function object** is the callable object created by executing a function definition. It refers to a code object and carries execution context such as its global namespace, defaults, and closure.

A useful distinction: a code object represents compiled code; a function object connects that code to the context in which it will run.

## What happens inside the runtime?

The Python 3.15.2 execution model describes conceptual runtime layers:

- **Process:** operating-system resources such as memory, file descriptors, and sockets.
- **Python global runtime:** state shared at the runtime level.
- **Interpreter:** interpreter-specific state and execution environment.
- **Thread:** the host thread that executes Python and native code.
- **Thread state:** Python execution state associated with a thread.

A runtime can contain multiple interpreters, and an interpreter can have multiple thread states. This is a conceptual model: implementations do not have to represent every layer as a separate concrete object.

Do not confuse the Python interpreter with the operating-system process. A process is an OS-level execution container; the interpreter is the Python implementation executing code within that environment.

## Is bytecode machine code?

No. Native machine code is executed directly by the processor. CPython bytecode is interpreted by CPython's execution machinery. Normal CPython execution does not require producing a standalone native executable.

Also, avoid describing the interpreter as a permanently fixed loop over an unchanging set of opcodes. CPython's execution machinery and optimizations evolve across releases.

## Adaptive specialization in modern CPython

Modern CPython can adapt execution to observed runtime behavior. It may specialize instructions for common cases and use inline caches to make repeated operations faster.

This is an implementation optimization, not a change to Python's language semantics. The exact instructions and specialization strategy can change between CPython releases.

The `dis` module can inspect CPython bytecode. Its adaptive view can show specialized instructions (for example, with `dis.dis(function, adaptive=True)`). This is useful for investigation, but bytecode should not be treated as a stable application interface.

## What is a .pyc file?

Python can cache compiled module bytecode in `.pyc` files, usually under `__pycache__`. When the cache is valid, an import may reuse it instead of compiling the source again.

This is an optimization, not a requirement for every execution. A `.pyc` file contains Python bytecode, not native machine code. Cache validity is checked; the existence of a file alone does not mean Python will always use it.

## Why this matters in a backend service

Consider a FastAPI application. During startup, the process starts Python and the application imports its entry-point module and dependencies. Module-level statements execute: objects are created, routes are registered, and components are initialized.

Later, when an HTTP request arrives, the relevant endpoint and service functions are called. An error during import or module initialization can prevent startup; an error inside an endpoint may appear only when a request reaches that code.

This distinction helps separate startup failures from request-time failures.

## Interview-ready answer (EN)

“When CPython runs a program, it reads and decodes the source, parses it into an AST, and compiles it into code objects containing bytecode and metadata. The interpreter then executes those code objects in a runtime environment.

Compilation and execution are different. A function body is compiled with its containing module, but executing the function definition creates a function object; the body runs only when the function is called.

Bytecode is not native machine code, and its format is a CPython implementation detail. Modern CPython can adapt and specialize bytecode at runtime, but those optimizations do not change the language-level contract. Compiled module bytecode may also be cached in .pyc files.

For production diagnosis, I distinguish module import and startup behavior from request-time execution, and I separate Python language guarantees from CPython and operating-system implementation details.”

---

## PY-003 / FU-1 — What are the main stages of Python execution? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What are the main stages between Python source code and the execution of its instructions in CPython?

**Explanation**

The usual CPython path is: read and decode source, parse it into an AST, compile it into code objects, and execute those objects in the runtime. Execution can create objects, resolve names, call functions, and interact with native libraries or the operating system.

**Interview answer (EN)**

“CPython reads and decodes the source, parses it into an AST, compiles it into code objects containing bytecode and metadata, and then executes those objects in its runtime. During execution, Python creates objects, resolves names, calls functions, and may interact with native libraries and operating-system services.”

---

## PY-003 / FU-2 — Why does running a module differ from importing it? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?

**Explanation**

When a file is run directly, its `__name__` is normally `"__main__"`. When imported, its `__name__` is the module's import name. The package context, import path, working directory, and module-level side effects may also differ. Running a package module with `python -m package.module` often preserves the intended package context better than executing a file by path.

**Interview answer (EN)**

“I compare the execution context first: `__name__`, `__package__`, `sys.path`, the working directory, and the exact command. I then inspect relative imports and module-level side effects. Direct execution normally sets `__name__` to `__main__`, while importing uses the module's import name. For package applications, I prefer a consistent package-aware entry point, such as `python -m package.module`.”

---

## PY-003 / FU-3 — Which execution details are implementation-specific? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?

**Explanation**

Python specifies language semantics, not one universal bytecode format or interpreter architecture. CPython opcodes, inline caches, adaptive specialization, and internal frame representations are implementation details that may change between releases. In particular, do not assume every function call must materialize a Python-visible `PyFrameObject`; CPython's internal execution-frame representation and the frame objects exposed for introspection are distinct concepts.

**Interview answer (EN)**

“Python defines language semantics, but it does not guarantee a particular bytecode format or interpreter implementation. CPython opcodes, specialization strategies, and internal frame representations can change between releases. I rely on documented language behavior for application correctness and use implementation-specific details only when needed for debugging or measured optimization.”

---

## PY-003 / FU-4 — How do you choose the diagnostic layer? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?

**Explanation**

Choose the layer based on symptoms and evidence:

- **Application:** business logic, data, dependency usage, and request flow.
- **Python/CPython:** exceptions, imports, call stacks, object lifetime, memory behavior, and interpreter overhead.
- **Operating system/container:** CPU and memory limits, processes, networking, file descriptors, and system-level failures.

Start broad with metrics, logs, and traces. Go deeper only when the evidence points to a lower layer.

**Interview answer (EN)****

“I start with symptoms, metrics, logs, and traces. I inspect application behavior when the issue involves business logic or dependency usage. I investigate Python and CPython when evidence points to imports, exceptions, memory management, call stacks, or interpreter overhead. I inspect the operating system and container when there are signs of resource limits, process failures, networking problems, or file-descriptor exhaustion. I choose the diagnostic layer from evidence rather than assumptions.”

**References**
- [Python 3.15.2 — Execution model](https://docs.python.org/3.15/reference/executionmodel.html)
- [Python 3.15.2 — Code objects](https://docs.python.org/3.15/reference/datamodel.html#code-objects)
- [Python 3.15.2 — dis module](https://docs.python.org/3.15/library/dis.html)
- [Python 3.15.2 — Command-line and environment](https://docs.python.org/3.15/using/cmdline.html)
- [Python 3.15.2 — Import system](https://docs.python.org/3.15/reference/import.html)

---


# PY-004 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** What happens during a function call in CPython?

## The main idea

A function call is more than jumping to another line of code. Python evaluates the call expression, binds arguments to parameters, establishes the execution state, runs the function body, and then returns a result or propagates an exception.

A useful mental model:

1. Evaluate the callable expression and argument expressions.
2. Invoke the callable using Python's call semantics.
3. Bind positional and keyword arguments to parameters.
4. Establish or resume the function's execution state.
5. Execute the body.
6. Return a value or propagate an exception.

The exact internal call path is an implementation detail. The semantic behavior is what application code should rely on.

## 1. Evaluating the call

Before the function body starts, Python evaluates the callable expression and the argument expressions. Those expressions can have side effects or raise exceptions themselves.

The target does not have to be an ordinary Python function. It can be a bound method, a built-in function, a class, or an instance whose type implements `__call__`.

## 2. Argument binding

Python maps the supplied arguments to the function's parameters:

- Positional arguments are matched according to parameter order.
- Keyword arguments are matched by parameter name.
- Default values are used when an optional parameter is not supplied.
- `*args` collects extra positional arguments.
- `**kwargs` collects extra keyword arguments.
- Positional-only and keyword-only parameters restrict how an argument may be supplied.

Invalid calls—for example, a missing required argument, an unexpected keyword, or supplying the same parameter twice—raise `TypeError` before the function body executes.

Important: default argument expressions are evaluated once, when the `def` statement executes. They are not re-evaluated on every call.

## 3. Function object and code object

- **Function object:** the callable runtime object. It refers to the compiled code and carries context such as the global namespace, defaults, and closure information.
- **Code object:** the compiled instructions and metadata. It can be reused across many calls; Python does not recompile the function body on every invocation.

A function object therefore connects reusable compiled code to the context in which that code executes.

## 4. Execution state and frames

Conceptually, an active function call needs an execution frame. The frame represents information needed to execute the code and continue correctly, including:

- the code being executed and the current instruction position;
- local variables and parameter values;
- access to global and built-in namespaces;
- closure cells for variables captured from enclosing scopes;
- control-flow and exception-handling state;
- information needed for debugging, tracing, and returning to the caller.

Do not assume that all local variables are always stored in a normal Python dictionary or that every call allocates a fully materialized `PyFrameObject`.

In modern CPython, the internal `_PyInterpreterFrame` representation is distinct from the Python-visible `PyFrameObject`. A visible frame object can be created or exposed when introspection, tracing, or debugging needs it. This is an implementation detail, not a Python language guarantee.

## 5. How does the call return?

When the function executes `return expression`, the evaluated value is returned to the caller. If execution reaches the end of the function without an explicit return, the result is `None`.

If an exception is raised and not handled inside the function, it propagates to the caller. As it propagates, Python unwinds the active execution contexts until a matching handler is found or the exception reaches the top level.

Tracebacks contain references to execution frames. Retaining an exception or traceback can therefore retain local variables and objects referenced by those frames.

## 6. Important CPython implementation detail: optimized calls

CPython has optimized call machinery. Its C API documents the `tp_call` and `vectorcall` protocols; vectorcall can reduce argument packaging overhead for supported callables.

Since CPython 3.11, ordinary Python-to-Python calls can use an optimized interpreter path that avoids the older pattern of recursively re-entering the evaluator for every Python call. Internal frames are also lighter than the traditional model.

These are CPython implementation details. They explain performance behavior, but application correctness must not depend on a particular internal call path or frame layout.

## 7. Generators and coroutines are different

Calling an ordinary function starts executing its body immediately.

Calling a generator function creates a generator object; its body advances when the generator is iterated. Calling an `async def` function creates a coroutine object; its body runs when the coroutine is awaited or scheduled.

Generators and coroutines preserve execution state across suspension points. Their lifecycle is not the same as an ordinary function that runs to completion in one call.

## Practical example

~~~python
def make_multiplier(factor):
    def multiply(value, *, offset=0):
        return value * factor + offset
    return multiply

triple = make_multiplier(3)
result = triple(10, offset=2)  # 32
~~~

When `make_multiplier(3)` runs, it creates and returns a function object. The returned function retains `factor` through a closure. Later, the call binds `value` positionally and `offset` by keyword, executes the body, reads `factor` from the closure, and returns `32`.

## Interview-ready answer (EN)

“When a function call is evaluated, Python first evaluates the callable and argument expressions, then applies the call semantics and binds positional and keyword arguments to the function's parameters. The function body executes using its compiled code object and a runtime context that provides local state, globals, built-ins, and closure variables where applicable.

Conceptually, an execution frame represents the active call. In CPython, the internal frame representation and call path are implementation details and have changed across versions. During execution, the function can return a value or propagate an exception.

A generator or coroutine function has a different lifecycle: calling it creates a generator or coroutine object rather than immediately running its body to completion. For performance, I profile representative workloads before optimizing call boundaries, because the dominant cost may be inside the function or in I/O rather than the call mechanism itself.”

---

## PY-004 / FU-1 — What execution state is needed during a function call? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What execution state does CPython need to establish or maintain when entering and executing a Python function?

**Explanation**

The runtime needs the function's code, bound arguments, local execution state, access to globals and built-ins, closure cells where applicable, and control-flow information. Conceptually, this is represented by an execution frame.

In CPython, internal execution frames are not identical to Python-visible `PyFrameObject` instances. A visible frame may be exposed when introspection or debugging requires it.

**Interview answer (EN)**

“CPython needs the function's code object, bound arguments, local execution state, and access to globals, built-ins, and closure cells. It also maintains control-flow and exception state so execution can continue, return, or propagate an exception. Conceptually this is an execution frame, but the internal frame representation is an implementation detail and is not necessarily materialized as a Python-visible frame object for every call.”

---

## PY-004 / FU-2 — How do you investigate function-call overhead? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?

**Explanation**

Start with a representative workload and a measurable service objective. Use a profiler to inspect call counts, self time, and cumulative time, then correlate the results with request traces.

- **Self time:** time attributed to the function itself, excluding subcalls.
- **Cumulative time:** time in the function plus its subcalls.
- **Call count:** how often the function was invoked; a high count alone does not prove it is a bottleneck.

A deterministic profiler can provide detailed call information but add overhead. Sampling profilers are often less intrusive, but their results are statistical.

**Interview answer (EN)**

“I define the target metric and capture a representative workload. I inspect call counts, self time, and cumulative time, and correlate the profile with request traces. A high call count alone does not prove that call dispatch is expensive; time may be spent in a database, network request, serialization, or native code. I make a targeted change only after identifying the bottleneck, then compare latency percentiles, throughput, CPU, memory, and correctness under the same workload.”

---

## PY-004 / FU-3 — How do recursion, exceptions, generators, and coroutines change the lifecycle? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?

**Explanation**

- **Recursion:** creates nested logical calls with separate parameters and local execution state. Deep recursion can hit the recursion limit.
- **Exceptions:** transfer control by unwinding execution contexts until a matching handler is found.
- **Generators:** calling a generator function creates a generator object. Its body advances during iteration and retains state between `yield` points.
- **Coroutines:** calling an `async def` function creates a coroutine object. Its body runs when awaited or scheduled, and it can suspend at `await` points.

An event loop schedules coroutine progress; it does not create one operating-system thread per coroutine.

**Interview answer (EN)**

“An ordinary function runs when called and completes by returning or raising. Recursion creates nested calls with separate logical execution state. Exceptions unwind control flow until a handler is found. A generator call returns an object whose body advances during iteration and retains state between yields. An async function call returns a coroutine object that runs when awaited or scheduled. These differences affect stack depth, scheduling, cancellation, and resource cleanup.”

---

## PY-004 / FU-4 — When should call mechanics influence an optimization decision? ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?

**Explanation**

Call mechanics matter when profiling shows that call dispatch or repeated wrapper layers consume a meaningful part of a CPU-bound hot path. CPython optimizations such as vectorcall can reduce some overhead, but they do not make every call free.

Validate the hypothesis with representative benchmarks, production metrics, and the Python versions the service supports. Consider readability and maintenance cost as well as speed.

**Interview answer (EN)**

“I optimize call mechanics only when profiling shows that call dispatch or wrapper layers are a material cost in a representative workload. I estimate the maximum possible end-to-end gain, test a focused alternative, and compare latency percentiles, throughput, CPU, memory, correctness, and maintainability. CPython's call optimizations change over time, so I avoid depending on private internals unless that dependency is isolated and justified by measured results.”

**References**
- [Python 3.15.2 — Execution model](https://docs.python.org/3.15/reference/executionmodel.html)
- [Python 3.15.2 — Data model: frame objects](https://docs.python.org/3.15/reference/datamodel.html#frame-objects)
- [Python 3.15.2 — C API: Frame objects](https://docs.python.org/3.15/c-api/frame.html)
- [Python 3.15.2 — C API: Call protocol](https://docs.python.org/3.15/c-api/call.html)
- [Python 3.15.2 — sys.setprofile and sys.settrace](https://docs.python.org/3.15/library/sys.html)

---


# PY-005 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** Explain Python's object model: identity, type, and value.

**What it evaluates:** Name binding, identity versus equality, mutability, type checks, and API design.

Every Python object has an identity, a type, and a value. Identity distinguishes the particular object; type defines its behavior and supported operations; value is the data or state it represents. An object's identity and type remain stable during its lifetime, while its value may change if it is mutable.

A variable is a name bound to an object, not a typed storage container. Assignment normally binds a name; it does not copy the object. Multiple names can therefore refer to the same mutable object.

~~~python
first = [1, 2]
alias = first
another = [1, 2]

first is alias       # True: same object
first == another    # True: equal values, different objects

alias.append(3)     # The change is visible through first as well
~~~

Use is for identity-sensitive checks such as None or a private sentinel; use == for value equality. Use isinstance() when subclasses are acceptable. Prefer protocols or polymorphism when callers need behavior rather than a specific implementation.

Do not confuse Python object identity with domain identity. Two ORM instances may represent the same database row while being distinct Python objects. Use stable domain identifiers across persistence, serialization, and distributed boundaries. The id() result is guaranteed to be unique only while the object is alive; an ID may be reused after the object is destroyed. In CPython, id() is currently the object's memory address, but that is an implementation detail, not a language guarantee.

**Interview-Ready Answer (EN)**

“Every Python object has an identity, a type, and a value. Identity tells us which particular object we refer to, type defines its behavior, and value represents its data or state. Names are bound to objects, so multiple names can refer to the same object. A mutable object's value can change without changing its identity or type; rebinding a name is different from mutating the object. I use is for identity checks such as None, and == for value equality. I generally prefer isinstance() when subclasses are valid, and protocols when the design should depend on behavior. For persistence and distributed systems, I use explicit domain identifiers rather than Python object identity.”

---

## PY-005 / FU-1 — Identity, type, and value over an object's lifetime ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** Which of an object's identity, type, and value can change during its lifetime?

**Explanation:** Identity and type remain stable throughout an object's lifetime. Its value may change if it is mutable. Mutation changes the existing object; rebinding changes which object a name refers to. Immutability is not necessarily deep: a tuple can contain a mutable list whose contents still change.

**Interview-Ready Answer (EN)**

“An object's identity and type remain constant during its lifetime, while its value may change if it is mutable. Mutation changes the state of the existing object; rebinding changes the object referenced by a name. These are different operations. An immutable container also does not guarantee that every object reachable through it is immutable.”

---

## PY-005 / FU-2 — Choosing identity, equality, and type checks ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How would you choose between identity checks, equality checks, and type checks in a code review?

**Explanation:** Start with the contract being tested. Use is for object identity and singleton sentinels, == for value equality, and isinstance() when subclasses are accepted. An exact check such as type(value) is int deliberately rejects subclasses and should be used only when that restriction is part of the contract. Review custom __eq__ and __hash__ together when objects are dictionary keys or set members.

**Interview-Ready Answer (EN)**

“I first identify whether the code needs identity, value equality, or type compatibility. I use is for None and explicit sentinels, == for values, and isinstance() when subclasses should be accepted. Exact type checks are appropriate only for a deliberate strict contract. I also review custom equality and hashing because inconsistent implementations can break dictionary and set behavior.”

---

## PY-005 / FU-3 — Why is is not a value comparison? ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Why can using is to compare strings, numbers, or other values produce unreliable results?

**Explanation:** is tests whether references designate the same object; it does not compare values. Equal values can belong to distinct objects. CPython may reuse or intern some immutable objects, making an incorrect identity comparison appear to work in one context. Such reuse is an implementation optimization, not a language guarantee.

**Interview-Ready Answer (EN)**

“is checks object identity, whereas == invokes the type's equality semantics, which may be customized. Two separately created values can compare equal without being the same object. Interning or constant reuse may make identity comparisons appear to work for some strings or integers, but that behavior is implementation-dependent. I use is for sentinels and == for value comparisons. I also remember that id() is only unique during an object's lifetime and is not a persistent identifier.”

---

## PY-005 / FU-4 — Identity and mutability in API design ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types?

**Explanation:** Define whether an API mutates, retains, copies, or returns caller-owned objects. Use stable domain IDs when identity must survive database reloads or process boundaries. Prefer immutable value objects for value-based concepts, while accounting for nested mutability and hash stability. Expose required behavior through protocols or abstractions instead of requiring a concrete class without a clear reason. Validate and normalize external data at system boundaries.

**Interview-Ready Answer (EN)**

“I make ownership and mutation semantics explicit: callers should know whether an API changes an input, retains a reference, or returns shared state. I use stable domain identifiers rather than Python object identity across persistence and distributed boundaries. Immutable value objects are useful when equality is value-based, provided nested state and hashing are handled correctly. I expose required behavior through suitable abstractions or protocols so callers are not coupled to an unnecessary concrete implementation.”

**Status:** Audited against the Python 3.15.2 data model, comparison semantics, and programming FAQ; four follow-ups retained.

# PY-006 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** How does Python resolve attribute access, and how do descriptors and special methods affect that process?

**What the interviewer evaluates**

- Understanding of attribute lookup and the instance/class relationship.
- Descriptor protocol, including data and non-data descriptor precedence.
- The roles of `__getattribute__` and `__getattr__`.
- The distinction between ordinary attribute access and implicit special-method lookup.

**Short Answer**

Attribute access in Python is governed by the object model. For ordinary instance access, the lookup process involves the instance's type, its data descriptors, the instance namespace, and non-data descriptors or other class attributes. Descriptors customize access through `__get__`, `__set__`, and `__delete__`. `__getattribute__` intercepts ordinary attribute access, while `__getattr__` is a fallback invoked when normal lookup raises `AttributeError`. Implicit special-method operations often look up methods on the type rather than through the instance attribute namespace.

**Explanation**

An expression such as `obj.name` invokes attribute access machinery; it is not simply a dictionary lookup in `obj.__dict__`. The default behavior is implemented by `object.__getattribute__`, with the object's type and descriptor protocol determining the result.

For a typical instance, the important precedence rules are:

1. A **data descriptor** found on the type takes precedence over an entry with the same name in the instance namespace. A descriptor is a data descriptor when its type provides `__set__` or `__delete__`.
2. If no data descriptor applies, Python checks the instance namespace.
3. If the name is not found there, a **non-data descriptor** or another class attribute may provide the result. A descriptor that defines `__get__` but not `__set__` or `__delete__` is non-data.
4. If normal lookup fails, `__getattr__`, when defined, may provide a fallback value.

This is a useful model for ordinary instance attribute access, not a universal description of every lookup form. Class attribute access, slots, custom `__getattribute__`, metaclasses, and special-method lookup have additional rules.

**The descriptor protocol**

A descriptor is an object whose type defines one or more of `__get__`, `__set__`, or `__delete__`. Python recognizes these protocol methods on the descriptor's type, not merely as attributes attached to an individual descriptor instance. Descriptors are the foundation of properties, method binding, and several framework features. A function stored on a class is a non-data descriptor: accessing it through an instance invokes its binding behavior and produces a bound method. A `property` is a data descriptor and can control reads and writes even when an instance dictionary contains a same-named key. For instance access, `__get__` receives the instance and its type; for class access, it receives `None` and the owner class.

**Attribute access hooks**

- `__getattribute__(self, name)` is called for ordinary attribute access and can customize or intercept lookup. A custom implementation commonly delegates to `object.__getattribute__(self, name)`; otherwise, careless implementations can recurse indefinitely.
- `__getattr__(self, name)` is called only after ordinary lookup fails with `AttributeError`. It is appropriate for fallback behavior, such as proxy objects or dynamically exposed attributes.

**Special methods**

Operations such as `len(obj)`, `iter(obj)`, arithmetic, and context management use special-method lookup rules. For many implicit operations, Python looks up the special method on the type rather than consulting an instance attribute of the same name. Assigning `obj.__len__` therefore does not generally make `len(obj)` use that instance attribute. This type-level lookup supports consistent protocol behavior and allows optimized dispatch.

**Senior-Level Perspective**

When debugging unexpected attribute behavior, identify the exact lookup path: instance or class access, descriptor type, custom `__getattribute__`, fallback `__getattr__`, and whether the operation uses implicit special-method lookup. Avoid treating `__dict__` as the complete object model. Frameworks that use descriptors or dynamic attribute access should make these semantics explicit because they affect correctness, introspection, inheritance, and performance.

**Interview-Ready Answer (EN)**

“Python attribute access follows the object model and descriptor protocol; it is not merely a lookup in an instance dictionary. In ordinary instance access, data descriptors on the class take precedence over the instance namespace. If there is no data descriptor, Python checks the instance namespace and then class attributes, including non-data descriptors. Functions are non-data descriptors that become bound methods, while properties are data descriptors.

`__getattribute__` intercepts ordinary attribute access, and `__getattr__` is a fallback when normal lookup raises `AttributeError`. Implicit special-method operations, such as `len(obj)`, generally resolve the method on the type rather than using an instance attribute. Understanding these distinctions is essential when working with properties, descriptors, proxies, ORMs, and other frameworks that customize attribute behavior.”

---

## PY-006 / FU-1 — Attribute lookup precedence ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** In what order does Python search for an attribute on an instance, and how can an instance attribute interact with a class attribute?

**What the interviewer evaluates:** Instance and class namespaces, descriptor precedence, and the limits of the simplified lookup model.

**Short Answer**

For ordinary instance access under the default lookup behavior, a data descriptor on the type takes precedence, followed by the instance namespace, then a non-data descriptor or another class attribute. A custom `__getattribute__` can change this behavior, so the order should be understood as the default model rather than an unconditional rule.

**Detailed Answer**

An instance attribute does not always override a class attribute. If the class provides a data descriptor for that name, the descriptor controls access before the instance dictionary is consulted. Otherwise, an attribute stored directly on the instance normally shadows a same-named non-data descriptor or ordinary class attribute. If the instance does not contain the name, lookup can fall through to the class.

This explains why assigning to an attribute can shadow a method in some cases, while assigning a same-named value does not override a property in the same way. The property is a data descriptor and retains precedence.

**Interview-Ready Answer (EN)**

“With default instance lookup, data descriptors on the class have the highest precedence. If none applies, Python checks the instance namespace, then falls back to non-data descriptors and other class attributes. Therefore, an instance value can shadow an ordinary class attribute or method, but it does not override a data descriptor such as a property. Custom attribute hooks can modify the default behavior.”

---

## PY-006 / FU-2 — Data descriptors and non-data descriptors ![TYPE](https://img.shields.io/badge/TYPE-Mechanism_and_application-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** What is the difference between a data descriptor and a non-data descriptor, and why does the distinction matter?

**What the interviewer evaluates:** Descriptor protocol, lookup precedence, and practical use in Python APIs.

**Short Answer**

A descriptor is a data descriptor if its type defines `__set__` or `__delete__`; otherwise, a descriptor that defines `__get__` is a non-data descriptor. Data descriptors take precedence over the instance namespace, while instance attributes can shadow non-data descriptors.

**Detailed Answer**

Descriptors customize attribute access through methods implemented on the descriptor's type. A property is a common data descriptor: it can control reads and writes and takes precedence over a same-named value in the instance dictionary. A function stored on a class is a non-data descriptor; its `__get__` behavior creates a bound method when accessed through an instance. Because it is non-data, an instance attribute with the same name can shadow it under ordinary lookup.

This distinction is important in frameworks that use descriptors for validation, lazy loading, fields, relationships, or computed attributes.

**Interview-Ready Answer (EN)**

“The key difference is precedence. A data descriptor defines `__set__` or `__delete__` in addition to descriptor behavior and takes precedence over an instance attribute of the same name. A non-data descriptor defines `__get__` but not those write or delete methods, so an instance attribute can shadow it. Properties are data descriptors, while ordinary functions on a class are non-data descriptors that implement method binding.”

---

## PY-006 / FU-3 — `__getattribute__` versus `__getattr__` ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What is the difference between `__getattribute__` and `__getattr__`, and what risks arise when overriding them?

**What the interviewer evaluates:** Attribute interception, fallback semantics, recursion prevention, and API design.

**Short Answer**

`__getattribute__` is invoked for ordinary attribute access and can intercept every lookup. `__getattr__` is a fallback called only when normal lookup raises `AttributeError`. An override of `__getattribute__` must delegate carefully, usually to `object.__getattribute__`, to avoid infinite recursion.

**Detailed Answer**

A custom `__getattribute__` can implement proxies, access control, lazy resolution, or instrumentation, but it affects all ordinary attribute reads and can interfere with internal state access. Referring to `self.some_attribute` from inside the override can call the override again and recurse. Calling `object.__getattribute__(self, name)` provides the default lookup path.

`__getattr__` is narrower: it runs only after normal lookup fails with `AttributeError`. It is useful for dynamic fallback behavior, but it should not conceal unrelated programming errors by broadly catching exceptions other than the intended missing-attribute condition.

**Interview-Ready Answer (EN)**

“`__getattribute__` intercepts ordinary attribute access, so it is powerful but easy to misuse. Its implementation should normally delegate to `object.__getattribute__` to preserve the default lookup and avoid recursion. `__getattr__` is only a fallback after normal lookup raises `AttributeError`. I use the latter for dynamic missing attributes and override the former only when the design genuinely requires control over all attribute reads.”

---

## PY-006 / FU-4 — Implicit special-method lookup ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** Why can assigning a special method to an instance fail to change the behavior of an implicit operation such as `len(obj)`?

**What the interviewer evaluates:** Special-method lookup, type-level protocol dispatch, and the distinction between explicit and implicit calls.

**Short Answer**

Implicit special-method operations generally look up the relevant method on the object's type, not through the instance's ordinary attribute namespace. Therefore, assigning `obj.__len__` does not normally change the result of `len(obj)`; the type must implement the corresponding protocol method.

**Detailed Answer**

Python's data model defines protocols through special methods such as `__len__`, `__iter__`, `__next__`, and arithmetic methods. When syntax or a built-in invokes one of these protocols, the interpreter generally performs special lookup on the type. This behavior avoids treating an arbitrary instance attribute as an implementation of a type-level protocol and permits optimized dispatch.

This is different from explicitly evaluating `obj.__len__()`, which is ordinary attribute access followed by a call and may observe an instance attribute. The two expressions are therefore not interchangeable in all circumstances.

**Interview-Ready Answer (EN)**

“Implicit protocol operations such as `len(obj)` generally resolve special methods on the object's type rather than through the instance dictionary. Assigning `obj.__len__` therefore does not normally affect `len(obj)`; the class must provide the protocol implementation. An explicit call to `obj.__len__()` is ordinary attribute lookup, so it can behave differently. This distinction is part of Python's data model and matters when implementing custom container and operator behavior.”



# PY-007 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** How do Python lists, tuples, sets, and dictionaries differ internally and semantically?

**What the interviewer evaluates:** Collection semantics, mutability, ordering, hashability, complexity, and memory/performance trade-offs.

**Short Answer**

A list is a mutable ordered sequence; a tuple is an immutable ordered sequence; a set stores unique hashable elements; and a dictionary maps unique hashable keys to values while preserving insertion order. Choose by required semantics first, then validate performance and memory against the workload. In CPython, lists and tuples are array-like containers of object references, while sets and dictionaries use hash-table-based structures.

**Explanation**

- **List:** supports indexed access, in-place updates, append, and removal. Indexing is O(1); appending is amortized O(1); inserting or deleting near the beginning or middle is O(n) because elements may move.
- **Tuple:** an immutable sequence with indexed access and iteration. Immutability applies to the tuple's references, not recursively to contained objects. A tuple is hashable only if all its elements are hashable.
- **Set:** stores unique hashable elements and is optimized for membership, deduplication, and set algebra. Membership, insertion, and deletion are average-case O(1), but can degrade under heavy collisions.
- **Dictionary:** maps hashable keys to values, preserves insertion order as a language guarantee since Python 3.7, and provides average-case O(1) lookup, insertion, and deletion. Updating an existing key does not move it; deleting and reinserting it places it at the end.

These complexity figures are typical, not worst-case guarantees. They depend on hashing, collisions, resizing, and equality comparisons. CPython implementation details can change between versions and are not language guarantees.

**Choosing a Collection**

Use a list for an ordered, mutable sequence; a tuple for a fixed record or immutable sequence; a set when uniqueness and membership dominate; and a dictionary for key-based lookup. Do not choose a set or dictionary merely because O(1) sounds faster: consider ordering, memory overhead, hashability, and actual access patterns.

**Important Distinctions**

A shallow copy creates a new outer container but retains references to the same nested objects. Mutating a nested list or dictionary can therefore be visible through both containers. A tuple is not deeply immutable if it contains mutable objects. Dictionary keys and set elements must maintain stable hash and equality behavior while stored. Equal keys share one mapping entry: for example, `True`, `1`, and `1.0` compare equal and address the same dictionary key.

**Senior-Level Perspective**

Start with semantics and correctness, then profile representative data sizes and operation mixes. Consider memory per entry, allocation patterns, mutation frequency, iteration order, and whether a specialized structure is justified. Treat CPython layout and microbenchmark results as version- and workload-dependent evidence, not universal rules.

**Interview-Ready Answer (EN)**

“Lists and tuples are ordered sequences: lists are mutable, while tuples are immutable at the container level. Sets hold unique hashable elements and are useful for membership checks and set operations. Dictionaries map unique hashable keys to values and preserve insertion order. In CPython, lists and tuples are array-like containers of references, whereas sets and dictionaries use hash tables. Their common lookup and membership operations are typically average O(1), while list indexing is O(1) and middle insertion or deletion is O(n). In Python 3.15, `frozendict` adds a built-in immutable mapping. I choose based on required semantics first, then benchmark realistic workloads and account for memory, mutation patterns, and hash behavior.”

**References**

- [Python 3.15 documentation: Built-in Types](https://docs.python.org/3.15/library/stdtypes.html)
- [Python 3.15 documentation: Data model](https://docs.python.org/3.15/reference/datamodel.html)
- [Python 3.15: What's New — frozendict (PEP 814)](https://docs.python.org/3.15/whatsnew/3.15.html)

---

## PY-007 / FU-1 — Collection semantics and CPython representations ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython?

**Answer**

Lists and tuples are ordered sequences indexed by position; lists allow item replacement and resizing, while tuples do not. Sets contain unique hashable elements, and dictionaries associate hashable keys with values while preserving insertion order. CPython typically implements sequences as arrays of object references and sets/dictionaries with hash-table structures. The semantic contract should be separated from implementation: exact layouts, resizing policies, and memory costs may evolve.

**Interview-Ready Answer (EN)**

“Lists and tuples are ordered sequences, with mutability being the main semantic difference. Sets represent unique hashable members, while dictionaries represent key-value mappings with insertion-ordered iteration. In CPython, sequences use array-like reference storage, and sets and dictionaries use hash tables. I distinguish these implementation details from language-level guarantees.”

---

## PY-007 / FU-2 — Selecting a collection for a service ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service?

**Answer**

Use a list for an ordered sequence that may change, a tuple for a fixed sequence, a set for uniqueness and membership, and a dictionary for lookup by key. A request pipeline might use a list to preserve processing order, a set to track processed identifiers, and a dictionary to retrieve records by identifier. Maintaining duplicate structures adds memory and consistency costs, so do it only when the access pattern justifies it.

**Interview-Ready Answer (EN)**

“I map the collection to the dominant operation: list or tuple for sequence semantics, set for uniqueness and membership, and dict for keyed retrieval. If both stable order and fast membership are required, I may use a list plus a set, but I make update ownership explicit and test consistency.”

---

## PY-007 / FU-3 — Ordering, copying, and complexity edge cases ![TYPE](https://img.shields.io/badge/TYPE-Edge_cases_and_trade-offs-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity?

**Answer**

Dictionary insertion order is guaranteed by the language, but set iteration order is not a stable ordering contract. Shallow copies retain references to nested objects. Average-case hash-table complexity is not a worst-case guarantee, and tuples are only shallowly immutable. Since Python 3.7, dictionary insertion order is guaranteed. Do not rely on set iteration order for deterministic presentation. A shallow list or dictionary copy duplicates only the outer container. Hash collisions and expensive equality methods can increase lookup cost; a tuple containing a list is unhashable.

**Interview-Ready Answer (EN)**

“I rely on dictionary insertion order because it is a language guarantee, but I do not rely on set iteration order. Shallow copies share nested objects, and tuple immutability does not make referenced objects immutable. Average O(1) hash-table operations are not worst-case guarantees, so I consider collision behavior and real data.”

---

## PY-007 / FU-4 — Collection choice under production constraints ![TYPE](https://img.shields.io/badge/TYPE-Senior_judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy?

**Answer**

Identify the operation mix, data volume, ordering requirements, mutation frequency, and memory budget, then benchmark representative workloads. Measure latency, throughput, and memory rather than extrapolating from small synthetic examples. Include realistic key distributions, hit/miss ratios, object sizes, and construction/update costs. Avoid redundant indexes unless their measured latency benefit outweighs memory and consistency costs.

**Interview-Ready Answer (EN)**

“I start from the production access pattern: reads versus writes, lookup versus iteration, ordering, data size, and memory limits. Then I benchmark representative distributions and measure latency and memory, including build and update costs. I avoid choosing from asymptotic complexity alone, and keep redundant indexes only when their measured benefit justifies their operational cost.”


# PY-008 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L2-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** How do Python dictionaries work internally, and what are the performance and correctness implications of hash-table behavior?

**What the interviewer evaluates:** Understanding of hashing, key equality, collision resolution, resizing, complexity, and safe use of custom key types.

**Short Answer**

A dictionary is a mapping implemented in CPython with a hash-table design. For a lookup, Python computes the key's hash, uses it to locate candidate table positions, and checks equality when needed. This gives average-case O(1) lookup, insertion, and deletion, but collisions and expensive equality checks can degrade performance. Correctness depends on the key contract: equal keys must have equal hashes, and a key's hash/equality behavior must remain stable while it is stored.

**How Lookup Works**

1. Python obtains the key's hash through its hashing protocol.
2. The hash is used to identify a candidate position in the table.
3. If the position does not identify the requested key, the table follows its collision-resolution probe sequence.
4. Candidate keys are compared for identity/equality as required.
5. The value is returned when a matching key is found; otherwise the lookup reports absence.

A hash is not a unique identifier. Different keys may have the same hash, so equality checks are essential. The dictionary must preserve correctness even when collisions occur.

**Collisions, Resizing, and Complexity**

A collision occurs when distinct keys map to the same candidate position or hash value. CPython resolves collisions through probing within its table; the exact algorithm and layout are implementation details and should not be treated as Python language guarantees. As entries accumulate, the table may resize and redistribute entries to preserve efficient lookup. Consequently, individual insertions can be more expensive, while insertion is generally described as amortized O(1).

Lookup, insertion, and deletion are average-case O(1), not guaranteed worst-case O(1). Pathological collisions or costly equality methods can make operations much slower. Iterating over a dictionary is O(n) in the number of entries.

**Key Correctness Contract**

- If two keys compare equal, their hash values must be equal.
- Unequal keys may share a hash; collisions are permitted.
- A key's hash and equality behavior must not change while it is stored in a dictionary.
- If a class overrides __eq__() without defining a compatible __hash__(), Python normally makes its instances unhashable by setting __hash__ to None.
- Mutable objects whose equality depends on mutable state should generally not be hashable.

**CPython 3.15.2 Perspective**

CPython dictionaries use a compact, insertion-ordered hash-table design. At a high level, the table maintains indices used for lookup and entry storage containing keys and values. CPython also supports split-table dictionaries for certain instance attribute dictionaries. These are implementation details, not portable assumptions about every Python implementation. Exact layouts and probing behavior can evolve between CPython releases.

**Senior-Level Perspective**

Treat dictionary keys as stable values. For custom key classes, design __eq__() and __hash__() together and derive the hash from the same immutable fields used for equality. Avoid expensive or side-effecting equality methods. For untrusted input, consider algorithmic-complexity risks and keep hash randomization enabled; never use hash() as a persistent identifier, database key, or cross-process serialization value.

**Interview-Ready Answer (EN)**

“A Python dictionary is a hash-table-based mapping. Python hashes a key to find a candidate location, resolves collisions by probing, and uses equality to confirm the key. This provides average O(1) lookup, insertion, and deletion, but it is not a worst-case guarantee. Resizing keeps the table efficient as it grows, so insertion is generally amortized O(1). The key correctness rule is that equal objects must have equal hashes, and a key's hash and equality behavior must remain stable while it is in the dictionary. In production, I design custom keys around immutable equality fields, avoid relying on hash values across processes, and account for collision and memory costs.”

**References**

- [Python 3.15 data model: __hash__ and equality](https://docs.python.org/3.15/reference/datamodel.html#object.__hash__)
- [Python 3.15 built-in types: dictionary](https://docs.python.org/3.15/library/stdtypes.html#mapping-types-dict)
- [CPython dictionary implementation](https://github.com/python/cpython/blob/v3.15.2/Objects/dictobject.c)

---

## PY-008 / FU-1 — The hash and equality contract ![TYPE](https://img.shields.io/badge/TYPE-Core_contract-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What contract must __hash__() and __eq__() satisfy for objects used as dictionary keys?

**Answer**

The essential rule is: if a == b, then hash(a) == hash(b). The reverse is not required; unequal objects may have identical hashes. A key's hash and equality behavior must remain stable while it is stored. If a class overrides __eq__() but does not provide a compatible __hash__(), Python normally marks instances as unhashable. For value-based keys, compute equality and hashing from the same immutable state.

**Interview-Ready Answer (EN)**

“Equal objects must have equal hashes, but equal hashes do not imply equal objects. Hash collisions are valid and are resolved by equality checks. A key must also remain stable while stored, so I base custom hashing and equality on immutable fields.”

---

## PY-008 / FU-2 — Collision resolution and resizing ![TYPE](https://img.shields.io/badge/TYPE-Internal_mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** What happens when dictionary keys collide, and why can insertion or lookup become slower?

**Answer**

A collision means multiple keys compete for a candidate table position. CPython follows a probing strategy to find another slot and checks candidate keys for equality. As the table becomes more occupied, resizing allocates a larger table and redistributes entries. Typical operations remain average O(1), and insertion is amortized O(1), but pathological collision patterns or expensive equality checks can degrade performance. The exact probing algorithm is a CPython implementation detail.

**Interview-Ready Answer (EN)**

“Collisions are expected and do not break correctness: the table probes for candidate slots and equality determines whether a key matches. Resizing controls table occupancy as it grows. Average complexity is O(1), but worst-case behavior can be much slower, especially with pathological collisions or expensive equality methods.”

---

## PY-008 / FU-3 — Mutable custom keys and hash stability ![TYPE](https://img.shields.io/badge/TYPE-Correctness_and_design-7c3aed) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Why is it dangerous to use a mutable object as a dictionary key, and how should a custom key type be designed?

**Answer**

If a key's hash changes after insertion, the dictionary may search for it using a different location from the one where it was stored. If equality-relevant state changes, lookup and uniqueness behavior can also become inconsistent. A custom key should derive __eq__() and __hash__() from the same immutable fields. If equality is based on mutable state, the type should generally be unhashable.

**Interview-Ready Answer (EN)**

“A dictionary relies on a key's hash and equality remaining stable. Mutating fields that participate in either operation after insertion can make the entry effectively unreachable or create surprising behavior. I use immutable value fields for hashable keys, or make mutable domain objects unhashable.”

---

## PY-008 / FU-4 — Hash randomization and production security ![TYPE](https://img.shields.io/badge/TYPE-Security_and_production-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How does hash randomization help protect Python services, and why should hash() not be used as a persistent identifier?

**Answer**

Python salts the hashes of str and bytes with a process-specific unpredictable value by default. This makes precomputed collision attacks less practical and helps mitigate denial-of-service risks from adversarial dictionary keys. The resulting hash values can differ between process runs, so hash() is unsuitable for persistent IDs, database keys, cache keys shared across processes, or serialized identifiers. Use a stable, explicitly defined identifier or digest for those purposes.

**Interview-Ready Answer (EN)**

“Hash randomization makes collision attacks based on predictable string and bytes hashes harder. It is a mitigation, not a substitute for input limits and service-level protection. Since hashes are not stable across process runs, I never persist Python hash() results or use them as cross-process identifiers.”

---

# PY-009 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** How does memory management work in Python, and how do reference counting and garbage collection interact?

**What the interviewer evaluates**

- Understanding object lifetime, strong references, and reachability.
- Distinguishing reference counting from cyclic garbage collection.
- Awareness of CPython-specific behavior versus Python language guarantees.
- Ability to reason about resource cleanup and production memory growth.

**Short Answer**

Python manages objects through an implementation-controlled memory manager. In CPython, reference counting usually reclaims an object when its strong reference count reaches zero. Reference counting alone cannot reclaim unreachable reference cycles, so CPython also has a cyclic garbage collector that detects and collects supported cycles. These mechanisms manage object memory; they do not replace deterministic cleanup of external resources such as files, sockets, or database connections.

**Explanation**

A Python variable is a name bound to an object, not a manually managed memory slot. An object remains alive while it is reachable through references maintained by the runtime. Removing one name does not necessarily destroy the object: other names, containers, closures, frames, caches, or extension code may still hold references to it.

**Reference counting in CPython**

CPython maintains reference-count information for objects. Creating or releasing strong references changes the relevant count. When the count reaches zero, CPython can deallocate the object immediately and release references held by that object in turn. This often gives prompt reclamation for ordinary acyclic object graphs.

This is a CPython implementation strategy, not a language-level promise that an object is destroyed at a particular moment. Other Python implementations may use different memory-management strategies. Code must not depend on immediate finalization merely because it happens in a particular CPython build.

**Why a cyclic collector is needed**

Reference counting alone cannot reclaim a group of objects that refer to one another even when the group is no longer reachable from the rest of the program. Each object in the cycle still has an internal reference, so none reaches a zero count.

CPython's cyclic garbage collector supplements reference counting. It tracks relevant container objects, examines reference relationships, and identifies cycles that are unreachable from program roots. It can then clear and reclaim supported cyclic structures. Not every object needs to be tracked; atomic objects such as many integers and strings generally do not participate in reference cycles.

The gc module exposes collection controls, statistics, debugging facilities, and inspection helpers. Manual gc.collect() is primarily a diagnostic or specialized operational tool, not a routine fix for unexplained memory growth.

**Python 3.15.2 details**

The gc module documents generational collection and exposes per-generation statistics. In Python 3.15, gc.get_stats() and collection callbacks include duration and candidates, which help measure collection cost and work performed. Collection thresholds and generation behavior have changed across recent releases, including changes in 3.14 and 3.14.5; avoid memorizing old threshold behavior as a permanent contract. Consult the documentation for the exact runtime version being deployed.

**Free-threaded CPython distinction**

In a free-threaded build, do not assume that reaching a conventional reference-count value always causes immediate deallocation. CPython uses biased, deferred, and per-thread reference-counting techniques for selected objects; reclamation can be delayed until safe points or a GC run. QSBR can also defer reclamation of some internal data structures. Even after memory is reclaimed by the runtime, the allocator may retain it, so RSS may remain unchanged. These are free-threaded CPython implementation details, not general Python language guarantees.

**Object memory is not the same as process memory**

The Python memory manager allocates Python objects from a private heap and uses allocator layers. When an object is deallocated, its memory may become reusable by Python's allocator without being returned immediately to the operating system. Therefore, a process's RSS does not necessarily fall when objects are freed. A high or stable RSS alone does not prove that live Python objects are leaking.

Distinguish:
- **Live-object retention:** objects remain reachable because references are still held.
- **Uncollectable or delayed cycles:** cyclic structures or finalization behavior prevent immediate reclamation.
- **Allocator retention/fragmentation:** freed blocks remain available to the allocator but are not returned to the OS.
- **Native-memory growth:** C extensions or external libraries allocate memory outside the Python object heap.

**Resource management**

Memory management and resource management are related but different. Files, sockets, transactions, locks, and database connections should be released explicitly, normally with context managers or try/finally. Do not rely on __del__() or garbage collection to close them at a predictable time. Finalizers can run at uncertain times, and object resurrection or reference cycles can complicate finalization.

**Senior-Level Perspective**

When diagnosing memory growth, first define the symptom: increasing live objects, increasing allocation rate, rising RSS, or growth in native allocations. Reproduce under representative load, compare snapshots, identify retaining references, and inspect allocation sources. Tools such as tracemalloc, gc diagnostics, process metrics, and native profilers answer different questions. Do not disable cyclic GC or force frequent full collections without evidence; either can hide the real issue or add latency.

**Interview-Ready Answer (EN)**

“Python manages object memory automatically. In CPython, reference counting usually reclaims an object when its last strong reference is released. However, reference counting alone cannot reclaim unreachable groups of objects that reference one another, so CPython also has a cyclic garbage collector that detects and collects supported reference cycles.

I distinguish this implementation detail from the Python language guarantee: application code should not depend on a specific object-destruction time. I also distinguish object memory from external resources. Files, sockets, and database connections should be closed deterministically with context managers or try/finally, not by relying on garbage collection.

For production memory issues, I separate live-object retention from allocator behavior and native-memory growth. A process RSS that does not fall does not automatically mean Python objects are leaking. I use allocation tracing, object and GC diagnostics, and process-level metrics to find the actual source.”

**References**

- [Python 3.15.2 C API: Memory Management](https://docs.python.org/3.15/c-api/memory.html)
- [Python 3.15.2 Library Reference: gc — Garbage Collector interface](https://docs.python.org/3.15/library/gc.html)
- [Python 3.15.2 C API: Supporting Cyclic Garbage Collection](https://docs.python.org/3.15/c-api/gcsupport.html)
- [Python 3.15.2 Data Model: object.__del__()](https://docs.python.org/3.15/reference/datamodel.html#object.__del__)
- [Python FAQ: How does Python manage memory?](https://docs.python.org/3.15/faq/design.html#how-does-python-manage-memory)

---

## PY-009 / FU-1 — Reference counting versus cyclic garbage collection ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What is the difference between reference counting and cyclic garbage collection in CPython?

**What the interviewer evaluates:** Understanding of object lifetime, unreachable cycles, and the complementary roles of the two mechanisms.

**Answer**

Reference counting tracks strong references to an object. In CPython, when the count reaches zero, the object can normally be deallocated immediately. It is effective for ordinary acyclic object graphs, but it cannot reclaim a cycle whose members keep references to one another.

The cyclic garbage collector supplements reference counting. It examines supported container objects and identifies cycles that are unreachable from the program's roots. It can then reclaim those structures. The collector is not a replacement for reference counting; the two mechanisms solve different parts of the object-lifetime problem.

**Interview-Ready Answer (EN)**

“Reference counting handles the common case: when an object's last strong reference disappears, CPython can reclaim it. Cyclic GC handles a case reference counting cannot solve by itself—unreachable groups of objects that reference each other. CPython combines both mechanisms.”

---

## PY-009 / FU-2 — Reference cycles and reachability ![TYPE](https://img.shields.io/badge/TYPE-Reachability-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** Why can a reference cycle remain in memory even when the application no longer uses any of its objects?

**What the interviewer evaluates:** Ability to distinguish local reference counts from global reachability.

**Answer**

Consider two container objects that refer to each other. Even after the application drops every external reference to them, each object still has an incoming reference from the other. Their reference counts therefore remain non-zero, although the group is unreachable from the rest of the program.

CPython's cyclic collector detects supported unreachable cycles by examining tracked containers and their references. A cycle is not automatically a leak: if it remains reachable, it is still live by design. The important distinction is whether the object graph can be reached from program roots, not merely whether objects refer to one another.

**Interview-Ready Answer (EN)**

“A cycle can keep its members' reference counts above zero even after all external references disappear. Reference counting cannot reclaim that group on its own. CPython's cyclic collector identifies supported cycles that are unreachable from the program and can reclaim them. A reachable cycle is not garbage—it is still part of the live object graph.”

---

## PY-009 / FU-3 — del, finalizers, and deterministic cleanup ![TYPE](https://img.shields.io/badge/TYPE-Resource_lifecycle-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Does using del or defining __del__() guarantee that an object or its resources are released immediately?

**What the interviewer evaluates:** Understanding name binding, finalization semantics, and reliable resource management.

**Answer**

The del statement removes a name binding or an item reference; it does not directly command the runtime to destroy the object. The object may remain alive if other references exist. In CPython, releasing the final strong reference often triggers deallocation promptly, but this timing is not a portable Python language guarantee.

A __del__() finalizer is not a reliable resource-management mechanism. Its execution timing can be uncertain, finalization can be complicated by cycles or object resurrection, and interpreter shutdown introduces additional constraints. Use context managers (with) or try/finally to close files, sockets, and database connections deterministically.

**Interview-Ready Answer (EN)**

“del removes a reference; it does not guarantee object destruction. The object may still be referenced elsewhere, and prompt deallocation after the last reference is a CPython behavior rather than a portable timing guarantee. I use context managers or try/finally for deterministic resource cleanup and do not rely on __del__() for closing critical resources.”

---

## PY-009 / FU-4 — Diagnosing memory growth in production ![TYPE](https://img.shields.io/badge/TYPE-Production_diagnosis-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How would you investigate steadily increasing memory usage in a long-running Python service?

**What the interviewer evaluates:** Production debugging, measurement discipline, and the ability to distinguish Python heap retention from process and native memory.

**Answer**

First, clarify what is growing: process RSS, traced Python allocations, the number of live objects, or memory allocated by native extensions. Reproduce the workload and compare measurements over time rather than assuming every RSS increase is a Python object leak.

Use tracemalloc snapshots to identify Python allocation sites and compare retained allocations. Use gc statistics and carefully scoped object/referrer inspection to investigate cycles and retaining references. Correlate these findings with process-level metrics and, when necessary, native-memory profiling because C extensions and external libraries may allocate outside the Python object heap.

Also inspect caches, unbounded queues, global registries, task references, closures, and long-lived request state. Do not respond by blindly calling gc.collect() or disabling GC: first establish the cause and measure the effect of any change.

**Interview-Ready Answer (EN)**

“I start by distinguishing live Python allocations, process RSS, and native memory. I compare tracemalloc snapshots under a repeatable workload, inspect object retention and GC statistics, and correlate that with process metrics. I also check common retention sources such as unbounded caches, queues, background tasks, and global registries. I only tune or force garbage collection after identifying a specific GC-related cause and measuring the impact.”

# PY-010 — Main Question ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** What are weak references in Python, how do they differ from strong references, and when should they be used?

**What the interviewer evaluates**
- Understanding the difference between object reachability and ownership through strong references.
- Correct use of `weakref.ref`, proxies, weak containers, and weak references to bound methods.
- Awareness of weak-reference support limitations and the interaction with `__slots__`.
- Ability to design caches and observer registries without accidentally extending object lifetimes.
- Understanding that weak references do not guarantee immediate collection or deterministic resource cleanup.

**Short Answer**

A strong reference keeps an object reachable and therefore alive. A weak reference provides access to an object without keeping it alive. Python's `weakref` module exposes weak references and weak containers such as `WeakValueDictionary`, `WeakKeyDictionary`, and `WeakSet`. They are useful when a cache, registry, or relationship should not become the reason an object remains in memory. A weak reference must be treated as optional: its referent may disappear, so code should retrieve it once and check whether the result is `None`.

**Explanation**

A Python object can be referenced by variables, attributes, containers, closures, frames, and other runtime structures. An ordinary reference is strong: as long as a strong path keeps an object reachable, the object remains alive.

A weak reference does not contribute to keeping its referent alive. If no strong references remain, the runtime may reclaim the object. A weak reference does not force collection; it simply does not prevent it. The exact time of reclamation is not a portable language guarantee.

**The core weakref APIs**

- `weakref.ref(obj)` creates a weak reference. Calling it returns the referent if it is still alive, or `None` otherwise.
- `weakref.proxy(obj)` creates a proxy that forwards most operations to the referent. If the referent has disappeared, using the proxy raises `ReferenceError`. Proxies are not hashable.
- `WeakValueDictionary` stores values weakly. An entry disappears when its value is no longer strongly referenced elsewhere.
- `WeakKeyDictionary` stores keys weakly. It is useful for associating metadata with objects owned by other parts of an application.
- `WeakSet` stores its elements weakly.
- `WeakMethod` supports weak references to bound methods. A normal bound method object is ephemeral, so a plain weak reference to it is generally not the intended solution.

Most application code should prefer weak container abstractions over manually managing low-level weak references.

**Safe dereferencing**

Do not check a weak reference and then call it again later. In concurrent code, the referent could disappear between those operations. Retrieve it once into a local strong reference, check for `None`, and then use that local reference.

**When are weak references useful?**

- **Caches:** a cache should not necessarily own large objects merely because it indexes them. A weak-value cache allows an object to disappear when the rest of the application no longer needs it.
- **Observer and listener registries:** a publisher can avoid keeping subscribers alive solely because they registered for notifications.
- **Metadata registries:** a `WeakKeyDictionary` can associate metadata with objects without extending their lifetime.
- **Object relationships:** a weak back-reference can avoid an ownership path that would otherwise keep a parent or related object alive.

Weak references do not automatically fix memory leaks. If another strong reference remains—for example, in a global list, closure, task, queue, or ordinary dictionary—the object remains alive.

**Weak-reference support is not universal**

Not every Python object can be weakly referenced. Ordinary instances of user-defined classes generally support weak references. Built-in `list` and `dict` instances do not directly support them, although subclasses can. `int` and `tuple` do not support weak references, even when subclassed. If a class defines `__slots__`, it must include `'__weakref__'` to enable weak references unless support is inherited from a base class.

**Weak references and finalization**

A weakref callback can be notified when its referent is about to be finalized, but the referent is no longer available through that weak reference. `weakref.finalize` offers a higher-level finalization API and keeps the finalizer registration alive until the target is collected.

The finalizer callback, its arguments, or a closure must not hold a strong reference to the target, directly or indirectly. Otherwise, the target may never become collectible. Finalization is not deterministic resource management. Use context managers or `try/finally` for files, sockets, database connections, and transactions.

**Senior-Level Perspective**

Treat weak references as a lifetime and ownership tool, not as a general memory optimization switch. Define which component owns an object and which components merely observe or index it. Use weak references only when disappearance is valid behavior and callers can handle it. Test cleanup behavior, concurrency, callback lifetimes, and weak-reference support for the actual types involved. For caches, also define eviction, size limits, and consistency semantics; weak references alone are not a complete cache policy.

**Interview-Ready Answer (EN)**

“A strong reference keeps an object alive because it contributes to the object's reachability. A weak reference lets another component refer to the object without owning its lifetime. Python provides `weakref.ref`, proxies, and weak containers such as `WeakValueDictionary`, `WeakKeyDictionary`, and `WeakSet`.

I use them when a cache, observer registry, or metadata mapping should not keep an otherwise unused object alive. I dereference safely by retrieving the object once and checking for `None`, because the referent may disappear. I also verify that the target type supports weak references and avoid callbacks or finalizers that accidentally retain the target. Weak references do not replace explicit resource cleanup or solve leaks caused by other strong references.”

**References**
- [Python 3.15.2 Library Reference: weakref — Weak references](https://docs.python.org/3.15/library/weakref.html)
- [Python 3.15.2 Data Model: object.__del__()](https://docs.python.org/3.15/reference/datamodel.html#object.__del__)
- [Python 3.15.2 Data Model: __slots__](https://docs.python.org/3.15/reference/datamodel.html#slots)

---

## PY-010 / FU-1 — Strong references versus weak references ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What exactly changes in an object's lifetime when a strong reference is replaced by a weak reference?

**What the interviewer evaluates:** Understanding of reachability, object lifetime, and safe dereferencing.

**Answer**

A strong reference contributes to keeping an object reachable. A weak reference does not. Replacing the last strong reference with a weak reference means that the weak reference alone will not keep the object alive. Once no strong references remain, the runtime may reclaim the object, and calling the weak reference will then return `None`.

The weak reference does not destroy the object itself and does not specify when collection occurs. The important distinction is ownership: a strong reference participates in keeping the object alive; a weak reference provides conditional access without ownership.

Retrieve the referent once into a local variable and check for `None`. That local variable is then a strong reference for as long as it remains bound.

**Interview-Ready Answer (EN)**

“A strong reference contributes to object reachability and keeps the object alive. A weak reference does not. If all strong references disappear, the object may be collected even though weak references to it still exist. I dereference once, check for `None`, and use the resulting local strong reference.”

---

## PY-010 / FU-2 — Weak references in caches and observer registries ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** When would you choose a `WeakValueDictionary`, a `WeakKeyDictionary`, or a `WeakSet` in a real application?

**What the interviewer evaluates:** Practical API selection and the ability to avoid accidental object retention.

**Answer**

Choose based on which side should be weak:

- `WeakValueDictionary`: keys remain strongly held by the mapping, but values are weak. Use it when the mapping indexes objects that should be collectible when no other component needs them.
- `WeakKeyDictionary`: keys are weak and values are strong. Use it to attach metadata to objects owned elsewhere without making the mapping the owner of those objects.
- `WeakSet`: elements are weak. Use it for registries of live objects, such as subscribers, when the registry should not keep them alive.

For an observer system, a weak registry can prevent the publisher from retaining subscribers solely because they registered. The application must still define what happens when a subscriber disappears and manage callback and bound-method lifetimes correctly.

**Interview-Ready Answer (EN)**

“I choose the weak container according to which object should not be owned by the registry. WeakValueDictionary weakens values, WeakKeyDictionary weakens keys, and WeakSet weakens its elements. They are useful for caches, metadata, and observer registries, but they do not replace explicit cache policies or lifecycle design.”

---

## PY-010 / FU-3 — Weak-reference support and implementation edge cases ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Can every Python object be weakly referenced, and what should you check when a class uses `__slots__`?

**What the interviewer evaluates:** Knowledge of type capabilities and practical constraints of the weakref protocol.

**Answer**

No. Weak-reference support depends on the object's type. Most ordinary user-defined class instances support it, but built-in `list` and `dict` instances do not directly support weak references. Their subclasses can support weak references. Types such as `int` and `tuple` do not become weak-referenceable merely by subclassing.

When a class defines `__slots__`, weak-reference support is disabled unless `'__weakref__'` is included in the slots or inherited from a base class that already provides it.

Also distinguish `weakref.ref` from `weakref.proxy`: a dead reference returns `None`, while using a proxy after its referent is gone raises `ReferenceError`. For bound methods, use `WeakMethod` rather than assuming a plain weak reference will preserve the method binding.

**Interview-Ready Answer (EN)**

“Not every object supports weak references. I verify the target type rather than assuming the protocol is universal. With __slots__, I include __weakref__ when weak-reference support is required and is not inherited. I also account for the different failure behavior of refs and proxies, and use WeakMethod for bound methods.”

---

## PY-010 / FU-4 — Weak references, finalizers, and ownership design ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How would you design a weak-reference-based registry without introducing a new memory leak or unreliable cleanup behavior?

**What the interviewer evaluates:** Senior-level lifecycle design, callback safety, and deterministic resource management.

**Answer**

First, define ownership explicitly: the registry observes objects but should not own them. Select a weak container based on whether keys, values, or elements should be weak. Ensure that callbacks, closures, stored arguments, and bound methods do not retain the target strongly, directly or indirectly.

For bound-method subscriptions, use an approach designed for weak methods, such as `WeakMethod`, and remove stale entries safely. Treat object disappearance as a normal state and make notification or lookup code tolerate it.

Do not use weak references as a substitute for closing resources. Use context managers or `try/finally` for deterministic cleanup. If finalization is genuinely needed, `weakref.finalize` is usually a safer high-level tool than a custom `__del__`, but its callback must not retain the target.

**Interview-Ready Answer (EN)**

“I separate ownership from observation. The registry stores weak references so it does not keep subscribers alive, and I ensure callbacks and closures do not capture the target strongly. I handle expired references as a normal case and use WeakMethod for bound-method subscriptions where appropriate. For external resources, I still use context managers; weak references and finalizers are not deterministic resource-management mechanisms.”
---

## PY-011 — Context Managers, Resource Management & RAII ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question (EN):** How do Python context managers work, how do they provide deterministic resource management, and how do they compare with RAII?

**Question (RU):** Как работают контекстные менеджеры Python, как они обеспечивают детерминированное управление ресурсами и чем отличаются от RAII?

**Simple explanation**

A context manager defines what happens when execution enters and leaves a block. The `with` statement makes cleanup predictable: after successful entry, the exit protocol is invoked when the block finishes, including when an exception occurs inside it.

The key distinction is that resource cleanup is tied to the block boundary, not to when the garbage collector eventually destroys the object.

**Protocol and execution lifecycle**

A synchronous context manager implements:

- `__enter__()`: prepares or acquires the resource and returns the value bound by `as`.
- `__exit__(exc_type, exc_value, traceback)`: performs cleanup and receives exception details if the block exits because of an exception.

The order is: evaluate the context expression, resolve the special methods, call `__enter__()`, bind its return value to `as`, execute the body, then call `__exit__()`.

If `__enter__()` raises, that manager's `__exit__()` is not called. If `__enter__()` returns successfully, `__exit__()` is called when the suite exits. With multiple managers, entry is left-to-right and exit is right-to-left, as with nested `with` statements.

If the body raises, `__exit__()` receives the exception type, value, and traceback. A truthy return value suppresses the exception; a false value or `None` allows it to propagate. On normal exit, all three arguments are `None`, and the return value is ignored. An exception raised by `__exit__()` becomes the new propagating exception.

**Deterministic cleanup versus garbage collection**

Use context managers for resources that require timely release: files, sockets, database connections and transactions, locks, temporary directories, and sessions. Garbage collection and finalizers do not provide a reliable application-level schedule for releasing such resources.

A context manager does not necessarily destroy the Python object at block exit. It ends the managed context and performs the cleanup defined by that manager; the object itself may remain reachable.

**Asynchronous context managers**

An asynchronous context manager implements `__aenter__()` and `__aexit__()` and is used with `async with`. These methods are awaited, allowing asynchronous acquisition and cleanup, for example when managing network or database connections.

**The contextlib toolkit**

- `@contextmanager`: creates a synchronous context manager from a generator that yields exactly once. Code before `yield` enters the context; code after it performs exit/cleanup.
- `@asynccontextmanager`: asynchronous-generator counterpart for `async with`.
- `ExitStack`: manages a dynamic collection of synchronous context managers and cleanup callbacks; unwinds them in reverse registration order.
- `AsyncExitStack`: manages asynchronous contexts and cleanup, and can combine synchronous and asynchronous managers.

**RAII comparison**

RAII in C++ associates resource release with object destruction and scope-bound lifetime. Python's `with` offers a similar practical guarantee for a block, but it is an explicit context-management protocol rather than a guarantee that object destruction occurs at block exit. Python does not have Rust-style borrow checking or ownership guarantees.

**Senior-level design guidance**

Acquire resources as close as possible to the scope that owns them. Register cleanup immediately after acquisition, preserve exception propagation by default, and use `ExitStack` when acquisition is conditional or dynamic. Do not use `__del__` or garbage-collection timing as the primary cleanup strategy for external resources.

**Interview Answer (EN)**

“Python context managers provide deterministic setup and cleanup around a block through the `with` statement. A synchronous manager implements `__enter__` and `__exit__`; the asynchronous protocol uses `__aenter__` and `__aexit__` with `async with`. Once entry succeeds, the exit method is called whether the block completes normally or raises. It receives exception details and can suppress an exception only by returning a truthy value. I use context managers for files, locks, transactions, sockets, and other external resources rather than relying on garbage collection or finalizers. Compared with C++ RAII, Python provides explicit block-scoped cleanup through a protocol; it does not require the managed object itself to be destroyed when the block ends.”

**Official references (Python 3.15.2)**

- [The with statement](https://docs.python.org/3.15/reference/compound_stmts.html#the-with-statement)
- [With Statement Context Managers](https://docs.python.org/3.15/reference/datamodel.html#with-statement-context-managers)
- [contextlib](https://docs.python.org/3.15/library/contextlib.html)

### PY-011 / FU-1 — Mechanism: What exactly happens when a `with` block exits because of an exception? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What exactly happens when a `with` block exits because of an exception?

**Question (RU):** Что именно происходит, когда блок `with` завершается из-за исключения?

**Answer**

Python invokes `__exit__()` with the exception type, exception instance, and traceback. If the method returns a truthy value, the exception is suppressed and execution continues after the `with` statement. If it returns a false value or `None`, the exception propagates. If no exception occurred, `__exit__()` receives three `None` values and its return value is ignored. The method should normally not re-raise the supplied exception; propagation is controlled by its return value.

**Interview-Ready Answer (EN)**

“On exceptional exit, Python passes the exception details to `__exit__`. A truthy return value suppresses the exception; otherwise it propagates. On normal exit, the method receives three `None` values. I preserve propagation by default and suppress only explicitly expected exceptions.”

### PY-011 / FU-2 — Application: When should you use `ExitStack` instead of nested `with` statements? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** When should you use `ExitStack` instead of nested `with` statements?

**Question (RU):** Когда следует использовать `ExitStack` вместо вложенных операторов `with`?

**Answer**

Use `ExitStack` when the number of resources is dynamic, acquisition is conditional, or cleanup callbacks must be registered incrementally. Each successfully entered context or registered callback is unwound in reverse order. This also protects already-acquired resources if a later acquisition fails. For a small, fixed set of resources, ordinary nested or multi-item `with` statements are clearer.

**Interview-Ready Answer (EN)**

“I choose `ExitStack` when resource acquisition is dynamic or conditional. It lets me register cleanup immediately after each successful acquisition and unwinds the stack in reverse order, including when a later acquisition fails. For a fixed small set, regular `with` statements are simpler.”

### PY-011 / FU-3 — Edge cases: What happens if `__enter__()` fails, or if `__exit__()` itself raises? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What happens if `__enter__()` fails, or if `__exit__()` itself raises?

**Question (RU):** Что происходит, если `__enter__()` завершается ошибкой или если исключение возникает внутри самого `__exit__()`?

**Answer**

If `__enter__()` raises before returning, the context manager has not successfully entered, so its `__exit__()` is not invoked automatically. Therefore, an `__enter__()` implementation that acquires one resource and then performs another fallible operation must clean up the first resource itself if the later operation fails. `ExitStack` can help register cleanup during partial acquisition. If `__exit__()` raises while handling an exception from the body, the new exception propagates and the original exception is generally retained as its context.

**Interview-Ready Answer (EN)**

“Automatic exit is guaranteed only after `__enter__` returns successfully. Partial acquisition inside `__enter__` therefore needs its own rollback or an `ExitStack`. If `__exit__` raises, that new failure propagates, with the earlier exception available through exception chaining.”

### PY-011 / FU-4 — Senior judgment: How would you design reliable resource management in a synchronous and asynchronous backend? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How would you design reliable resource management in a synchronous and asynchronous backend?

**Question (RU):** Как спроектировать надёжное управление ресурсами в синхронном и асинхронном backend-приложении?

**Answer**

Define ownership and lifetime at the layer that acquires the resource. Use synchronous context managers for synchronous resources and asynchronous context managers for resources whose acquisition or cleanup requires awaiting. Keep transaction boundaries explicit, release locks in all exit paths, and register cleanup immediately after acquisition. Use `ExitStack` or `AsyncExitStack` for optional or variable resource sets. Preserve unexpected exceptions, make cleanup idempotent where practical, and do not rely on garbage collection or `__del__` for timely release. Also ensure that a resource is not used after its context has ended.

**Interview-Ready Answer (EN)**

“I make resource ownership and lifetime explicit. Synchronous resources use `with`; asynchronous resources use `async with`. I keep database transaction and lock scopes narrow, register cleanup immediately, and use the appropriate exit stack for dynamic acquisition. Unexpected exceptions propagate, cleanup is safe on every exit path, and no correctness property depends on garbage-collection timing.”
---

## PY-012 — Exception Handling, Exception Hierarchy & Exception Groups ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question (EN):** Explain Python's exception hierarchy and exception-handling model. How do propagation, exception chaining, and exception groups work?

**Question (RU):** Объясните иерархию исключений и модель обработки исключений в Python. Как работают распространение исключений, связывание причин и группы исключений?

**Simple explanation**

An exception is a control-flow mechanism used to report an error or another exceptional condition. Python raises it where the condition is detected and searches outward through the active call stack for a matching handler. If no handler is found, the exception remains unhandled and terminates the current execution path.

Senior-level exception handling is about choosing the correct boundary: handle errors where the application can recover or translate them meaningfully, preserve the original cause, and allow unexpected failures to propagate.

**Exception hierarchy**

All Python exceptions derive from `BaseException`. The two important branches are:

- `Exception`: ordinary application and runtime errors. Most application-specific exceptions should derive from this class.
- Direct `BaseException` branches include `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`. These represent process interruption, termination, or generator shutdown rather than ordinary application failures.

Do not normally catch `BaseException` in application code: doing so can intercept shutdown and interruption signals. Prefer specific exception classes; use `Exception` only at deliberate broad boundaries such as task supervision or a top-level request boundary.

**The try / except / else / finally model**

- `try`: contains the operations whose exceptions are being considered.
- `except`: handles a matching exception raised in the `try` suite, including one raised by a function called from it.
- `else`: runs only if the `try` suite completes without raising. It keeps success-only operations outside the protected region, avoiding accidental handling of their errors.
- `finally`: runs as the construct exits, whether an exception occurred or not; it is intended for cleanup.

An exception raised inside an `except` or `else` suite is not handled by another `except` clause belonging to the same `try`. It can be handled by an outer construct. A `finally` suite still runs during exit. Avoid `return`, `break`, or `continue` in `finally`: they can discard a pending exception or override a return value; Python 3.14+ emits a SyntaxWarning for these control-flow statements in `finally`.

**Propagation and the termination model**

If a function does not handle an exception, it propagates to its caller, then to the caller's caller, until a matching handler is found. Python uses termination-style exception handling: control leaves the failing operation and transfers to a handler. The handler does not automatically repair the failed operation or resume it at the exact failing instruction.

At an architectural level, a repository may raise a database-related exception, a service may translate it into a domain-level exception, and an API boundary may map that into an appropriate protocol response. Translate only when the new abstraction adds meaning; do not hide unexpected errors or erase useful diagnostics.

**Exception chaining**

When a new exception is raised while another is being handled, Python normally records the previous exception as `__context__`.

Use explicit chaining when translating an error and its direct cause matters:

- `raise NewError(...) from original_error` sets `__cause__`.
- `raise NewError(...) from None` suppresses the display of the implicit context in the traceback; the original context remains available for introspection.

Preserve causal information when crossing abstraction boundaries. It is valuable for debugging, observability, and incident analysis.

**ExceptionGroup and except***

Added in Python 3.11, exception groups represent multiple exceptions that need to be reported together, commonly when concurrent tasks fail independently.

- `ExceptionGroup` derives from `Exception` and contains only `Exception` instances.
- `BaseExceptionGroup` derives from `BaseException` and can contain any `BaseException`. Its constructor produces an `ExceptionGroup` automatically when all members are ordinary `Exception` instances.
- `except*` handles matching subgroups by exception type. Unmatched members remain in the group and continue propagating after the matching handlers run.

A single `try` statement cannot mix `except` and `except*` clauses. Unlike ordinary `except`, `except*` can execute more than one matching handler for different subgroups of the same group.

**User-defined exceptions**

Define application exceptions by deriving from `Exception` or a suitable application-specific subclass. Keep the hierarchy purposeful and stable. Exception types should communicate meaningful categories that callers can handle, while attributes can carry structured context such as an entity identifier or operation name. Prefer single inheritance from built-in exception types; multiple inheritance across built-in exception classes can cause layout conflicts.

**Senior-level design guidance**

1. Catch the narrowest useful exception type.
2. Catch an exception only where recovery, translation, or meaningful handling is possible.
3. Preserve the original exception using chaining when translating it.
4. Do not silently swallow unexpected failures.
5. Keep cleanup in `finally` or context managers, not in ad hoc exception handlers alone.
6. Use exception groups when multiple independent failures must be represented; use `except*` to handle their categories selectively.
7. At service/API boundaries, map domain failures to stable external errors without leaking internal stack traces or sensitive implementation details.

**Interview Answer (EN)**

“Python exceptions derive from `BaseException`, with `Exception` as the base for ordinary application errors. I normally catch specific exception types and avoid catching `BaseException`, because that can intercept signals such as `KeyboardInterrupt` and `SystemExit`. A `try` suite is handled by matching `except` clauses; `else` runs only on success, and `finally` is for cleanup. Unhandled exceptions propagate up the call stack. When translating an exception across architectural layers, I preserve its cause with `raise ... from ...`. For multiple independent failures, Python 3.11 introduced `ExceptionGroup` and `except*`, which allow selective handling of subgroups. My general rule is to handle errors where recovery or meaningful translation is possible and preserve unexpected failures and their diagnostic context.”

**Official references (Python 3.15.2)**

- [Built-in Exceptions and hierarchy](https://docs.python.org/3.15/library/exceptions.html)
- [Errors and Exceptions tutorial](https://docs.python.org/3.15/tutorial/errors.html)
- [The try statement and except*](https://docs.python.org/3.15/reference/compound_stmts.html#the-try-statement)
- [Execution model — Exceptions](https://docs.python.org/3.15/reference/executionmodel.html#exceptions)

### PY-012 / FU-1 — Mechanism: Why should application code usually catch `Exception` rather than `BaseException`? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** Why should application code usually catch `Exception` rather than `BaseException`?

**Question (RU):** Почему прикладной код обычно должен перехватывать `Exception`, а не `BaseException`?

**Answer**

`Exception` represents ordinary errors that application code may reasonably handle. `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` are direct branches of `BaseException`, not subclasses of `Exception`. Catching `BaseException` broadly can prevent normal interruption, process termination, or generator shutdown. Catch specific errors whenever possible; use a broad `Exception` handler only at a deliberate boundary, and re-raise when the failure cannot be handled.

**Interview-Ready Answer (EN)**

“I catch specific exceptions whenever possible. `Exception` covers ordinary application failures, while `BaseException` also includes control-flow signals such as `KeyboardInterrupt` and `SystemExit`. A broad `BaseException` handler can interfere with shutdown and interruption, so I avoid it in normal application code.”

### PY-012 / FU-2 — Application: How should a backend translate a low-level exception into a domain-level or API error? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How should a backend translate a low-level exception into a domain-level or API error?

**Question (RU):** Как backend должен преобразовывать низкоуровневое исключение в доменную ошибку или ошибку API?

**Answer**

Translate at an abstraction boundary where the new layer can add meaning. For example, a repository can expose a database failure as a domain-specific persistence error, and the API boundary can map a known domain error to a stable HTTP response. Use explicit exception chaining, such as `raise DomainError(...) from exc`, to preserve the underlying cause. Do not convert every unknown exception into a client error: unexpected failures should remain visible to logging and error monitoring and normally become a generic server error externally.

**Interview-Ready Answer (EN)**

“I translate exceptions at architectural boundaries where the new abstraction adds useful meaning. I preserve the original cause with explicit chaining, map known domain errors to stable API responses, and avoid exposing internal details or misclassifying unexpected failures as client errors.”

### PY-012 / FU-3 — Edge cases: What is the difference between `__cause__`, `__context__`, and `raise ... from None`? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What is the difference between `__cause__`, `__context__`, and `raise ... from None`?

**Question (RU):** В чём разница между `__cause__`, `__context__` и `raise ... from None`?

**Answer**

`__context__` is set automatically when a new exception is raised while another exception is being handled. `__cause__` is set explicitly by `raise new_error from original_error`, identifying the direct cause. `raise new_error from None` sets the context-suppression flag so the implicit context is not displayed in the traceback; it does not erase the original context from the exception object. Use explicit causes when translating errors; suppress context only when hiding it from the displayed traceback is intentional and safe.

**Interview-Ready Answer (EN)**

“`__context__` records an exception that was active when another exception was raised. `__cause__` records an explicit cause supplied with `raise ... from ...`. `from None` suppresses display of the implicit context but does not remove it from the exception object.”

### PY-012 / FU-4 — Senior judgment: When should you use `ExceptionGroup` and `except*` in concurrent systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** When should you use `ExceptionGroup` and `except*` in concurrent systems?

**Question (RU):** Когда в конкурентных системах следует использовать `ExceptionGroup` и `except*`?

**Answer**

Use exception groups when multiple independent operations can fail and the system needs to report more than one failure instead of discarding all but the first. This commonly occurs in structured concurrency and task groups. Use `except*` when different exception categories require different handling policies: matching subgroups are handled separately while unmatched exceptions continue propagating. Do not use groups merely to wrap a single ordinary failure; preserve cancellation and process-control semantics, and avoid suppressing failures that the caller needs to know about.

**Interview-Ready Answer (EN)**

“I use `ExceptionGroup` when several independent tasks can fail and all relevant failures need to be reported. I use `except*` to handle matching categories independently while allowing unmatched failures to propagate. This is particularly useful with structured concurrency, where a task group may surface multiple errors.”

## PY-013 — Iterators, Generators & Lazy Evaluation ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain Python's iteration model. What is the difference between an iterable, an iterator, and a generator, and how do generators enable lazy evaluation?

**Core explanation**

An **iterable** is an object that provides an iterator, normally through `__iter__()`. An **iterator** implements `__iter__()` (returning itself) and `__next__()` (returning the next item or raising `StopIteration`). An iterable is a source from which iteration can be requested; an iterator is the stateful object that performs the traversal. Reusable containers commonly create a fresh iterator on each call to `iter()`, while an iterator is normally consumed as it advances. Once exhausted, a conforming iterator must continue raising `StopIteration`.

A **generator** is a specialized iterator produced by a generator function or generator expression. A function containing `yield` is a generator function. Calling it creates a generator object without immediately executing the function body. Execution starts when the generator is advanced. At each `yield`, the generator produces a value and suspends while retaining its local bindings, instruction position, evaluation state, and exception-handling state. A later `next()` resumes it; the value of the suspended `yield` expression is `None` when resumed through `next()`.

**Lazy evaluation** computes values only when requested. A list comprehension eagerly creates a list; a generator expression produces values incrementally. This can reduce intermediate memory use and enable streaming pipelines, but does not guarantee bounded memory for the whole application: a consumer that stores every result still materializes the data. Laziness also changes when side effects and exceptions occur.

Generators support `send()`, `throw()`, and `close()`. `send(value)` resumes a started generator and makes the suspended `yield` expression evaluate to that value; a non-`None` value cannot be sent before the generator has started. `throw()` raises an exception at the suspension point. `close()` injects `GeneratorExit` to initiate cleanup. A generator should not yield another value while handling closure.

`yield from` delegates iteration and generator control operations to a subiterator. It forwards relevant `send()`, `throw()`, and close behavior and evaluates to the subgenerator's return value when that subgenerator terminates. A `return value` from a generator is conveyed through `StopIteration.value`. Under PEP 479, a `StopIteration` escaping from inside generator code is converted to `RuntimeError`, preventing accidental silent termination.

Asynchronous iteration is a separate protocol: `__aiter__()` returns an asynchronous iterator, `__anext__()` returns an awaitable for the next item, and `StopAsyncIteration` signals exhaustion. Asynchronous generators are defined with `async def` containing `yield` and are consumed with `async for`; they are not ordinary synchronous generators. If an asynchronous generator exits early, its asynchronous cleanup must be driven, normally through `aclose()` or the event loop's async-generator finalization machinery.

**Production considerations**

Generators are useful for large files, paginated APIs, ETL, database result streaming, and incremental transformations. Consider one-shot consumption, exception timing, side effects, cancellation, backpressure, and whether the consumer buffers results. If a generator owns a file, cursor, transaction, or network resource, use deterministic cleanup with context managers or explicit close semantics. Do not rely on garbage collection for timely release. For async generators, handle early exit and cancellation and ensure `aclose()` is awaited where required.

**Interview-Ready Answer (EN)**

“An iterable provides an iterator, while an iterator maintains traversal state and produces values through `__next__()`. A generator is a specialized iterator whose execution can suspend at `yield` and resume later, retaining its local state. Generator expressions enable lazy, incremental processing and can reduce intermediate memory use, which is useful for streaming and large datasets. However, laziness does not guarantee bounded memory or backpressure across the whole pipeline. In production I also account for one-shot consumption, exception and side-effect timing, cancellation, and deterministic cleanup of resources held by generators.”

**Follow-ups**

### PY-013 / FU-1 — Mechanism: What is the difference between an iterable and an iterator, and why is an iterator usually stateful? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What is the difference between an iterable and an iterator, and why is an iterator usually stateful?

**Question (RU):** В чём разница между iterable и iterator и почему итератор обычно хранит состояние?

**Answer**

An iterable provides a way to obtain an iterator through `__iter__()`. An iterator implements `__next__()` and maintains its current traversal state. A reusable iterable can commonly create multiple independent iterators, while a particular iterator is normally consumed as it advances. Once `StopIteration` has been raised, a conforming iterator continues to raise it.

**Interview-Ready Answer (EN)**

“An iterable provides an iterator, while an iterator produces values through `__next__()` and maintains traversal state. A reusable iterable can usually create multiple independent iterators, whereas a particular iterator is generally consumed as it advances.”

### PY-013 / FU-2 — Application: When would you choose a generator instead of a list in a backend data-processing pipeline? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** When would you choose a generator instead of a list in a backend data-processing pipeline?

**Question (RU):** Когда в backend-пайплайне обработки данных следует выбрать генератор вместо списка?

**Answer**

Choose a generator when data can be processed incrementally and the complete result does not need to be retained at once: large files, ETL, paginated API responses, or streaming transformations. It reduces intermediate materialization and lets a consumer process each item as it arrives. It does not automatically provide backpressure, bounded memory for the whole system, or repeatable traversal; those properties depend on the consumer and pipeline design.

**Interview-Ready Answer (EN)**

“I choose generators when data can be processed incrementally and the full result does not need to be retained. They reduce intermediate memory usage and support streaming pipelines, but I still design consumer behavior, backpressure, error handling, and resource cleanup explicitly.”

### PY-013 / FU-3 — Edge cases: What happens when `StopIteration` is raised inside a generator, and how does `yield from` handle delegation? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What happens when `StopIteration` is raised inside a generator, and how does `yield from` handle delegation?

**Question (RU):** Что происходит, если внутри генератора возникает `StopIteration`, и как `yield from` выполняет делегирование?

**Answer**

Under PEP 479, a `StopIteration` that escapes from generator code is transformed into `RuntimeError`, preventing an internal error from looking like normal exhaustion. `yield from` delegates iteration to a subiterator and forwards generator control operations. If the subgenerator returns a value, that value becomes the result of the `yield from` expression.

**Interview-Ready Answer (EN)**

“PEP 479 converts an escaping `StopIteration` raised inside a generator into `RuntimeError`, preventing accidental silent termination. `yield from` delegates iteration and generator control operations to a subiterator, and it can capture the subgenerator's return value.”

### PY-013 / FU-4 — Senior judgment: What production risks should you consider when using generators and asynchronous generators for resource-backed streams? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** What production risks should you consider when using generators and asynchronous generators for resource-backed streams?

**Question (RU):** Какие production-риски необходимо учитывать при использовании генераторов и асинхронных генераторов для потоков, связанных с ресурсами?

**Answer**

Account for early termination, exceptions, task cancellation, connection closure, and execution of `finally` blocks. A generator may retain a file descriptor, transaction, cursor, or network connection while suspended. Use context managers or explicit close semantics for deterministic synchronous cleanup. For asynchronous generators, ensure early-exit cleanup is driven with `aclose()` and awaited where required. Do not depend on nondeterministic garbage-collection finalization for timely resource release.

**Interview-Ready Answer (EN)**

“For resource-backed generators, I explicitly handle early termination, exceptions, cancellation, and cleanup. I use context managers for deterministic synchronous resource management and ensure asynchronous generators are closed with `aclose()` or an equivalent lifecycle mechanism. I never rely on garbage collection for timely resource release.”

## PY-014 — Decorators, Closures & Function Wrapping ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Main Question:** Explain how Python decorators work. How are decorators related to closures and function wrappers, and what production concerns should you consider?

**Core explanation**

A **decorator** is a callable that takes a function or another callable and returns a callable, often one that adds or changes behavior. The `@` syntax is syntactic sugar: applying `@decorator` to a function is broadly equivalent to defining the function and then binding `function_name = decorator(function_name)`. The returned object, not necessarily the original function, is bound to the function's name.

Decorator expressions are evaluated when the function definition executes, in the containing scope. With stacked decorators, application is nested: `@outer` above `@inner` is equivalent to `function = outer(inner(function))`. Thus the inner decorator is applied first, and the outer decorator receives its result. The wrapper logic normally runs when the decorated callable is invoked, not when the decorator is applied.

A **closure** is a function together with access to variables from an enclosing function scope. The inner function can continue using those bindings after the outer function has returned. A closure retains access to the binding, not merely an immutable snapshot of its value. `nonlocal` allows rebinding a name in the nearest enclosing function scope; `global` refers to the module-level namespace. Mutable closure state can persist across calls and can be shared by multiple invocations of the same wrapper.

A **wrapper** is the callable returned by a decorator. It commonly accepts `*args` and `**kwargs`, performs additional work, calls the wrapped callable, and returns or transforms its result. A well-designed wrapper should preserve the wrapped callable's observable behavior unless changing it is intentional. It should normally propagate exceptions unchanged unless the decorator has an explicit exception policy.

Use `functools.wraps` on the wrapper. It applies `update_wrapper()`, copying the standard metadata attributes (including name, qualified name, module, documentation, annotations and type parameters according to the current defaults), updating the wrapper's attribute dictionary, and adding `__wrapped__` pointing to the wrapped callable. This supports introspection, documentation tools, debugging, and access to the original callable. It does not make every arbitrary wrapper's runtime signature or behavior identical to the original.

A **decorator factory** is used when the decorator needs configuration. The outer function accepts configuration and returns the actual decorator; that decorator accepts the target callable and returns its wrapper. This pattern supports configurable retry limits, cache policies, timeouts, and authorization rules.

**Production considerations**

- Preserve arguments, return values, exceptions, and metadata intentionally.
- Be explicit about decorator stacking order. For example, authorization must not be bypassed by returning a protected cached result before checking the caller's permissions.
- For `async def` targets, use an async-aware wrapper when logic must surround completion: it should await the coroutine and handle its result, exceptions, or cancellation at the correct point. A synchronous wrapper that merely returns a coroutine may run its own post-call logic before the coroutine executes.
- Treat closure state as shared state when the same wrapper is called repeatedly. Define ownership, lifecycle, and synchronization where concurrent calls can overlap.
- Avoid expensive side effects during module import or function definition unless that timing is intentional.
- Document retry behavior and require idempotency or an explicit safety policy before automatically repeating operations.

**Interview-Ready Answer (EN)**

“A decorator is a callable transformation applied to a function when its definition executes. The returned callable is bound to the function's name and often uses a wrapper to add behavior such as logging, authorization, caching, or retries. Closures let wrappers retain access to configuration or state from an enclosing scope, while `nonlocal` can rebind that state. I use `functools.wraps` to preserve metadata and `__wrapped__`, and I carefully review decorator order, exception and return-value behavior, async handling, and concurrency around mutable closure state.”

**Follow-ups**

### PY-014 / FU-1 — Mechanism: How does Python apply a decorator, and when is the decorator executed? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** How does Python apply a decorator, and when is the decorator executed?

**Question (RU):** Как Python применяет декоратор и когда именно он выполняется?

**Answer**

When the function definition executes, Python evaluates the decorator expressions and applies them to the newly created function object. The result of the final application is bound to the function's name. Therefore, the decorator itself is applied at definition time, while the wrapper's operational logic normally runs on subsequent calls.

**Interview-Ready Answer (EN)**

“A decorator expression is evaluated when the function definition executes. The resulting callable is applied to the function object, and its return value is bound to the function name. The wrapper's runtime logic executes when the decorated callable is invoked.”

### PY-014 / FU-2 — Application: How would you implement a configurable decorator for logging, retries, or access control? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How would you implement a configurable decorator for logging, retries, or access control?

**Question (RU):** Как спроектировать настраиваемый декоратор для логирования, повторных попыток или контроля доступа?

**Answer**

Use a decorator factory: an outer function accepts configuration and returns a decorator; the decorator receives the target callable and creates a wrapper. The wrapper should use `functools.wraps`, forward arguments correctly, and preserve the intended return and exception behavior. Retry logic needs a bounded attempt policy and an idempotency strategy; access-control checks must happen before the protected operation or any protected cached result is returned.

**Interview-Ready Answer (EN)**

“I use a decorator factory when configuration is required. The returned decorator wraps the target callable, preserves metadata with `functools.wraps`, and forwards arguments, results, and exceptions correctly. I also define explicit policies for retry limits, idempotency, and authorization order.”

### PY-014 / FU-3 — Edge cases: What is a closure, how does `nonlocal` work, and what problems can mutable closure state introduce? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What is a closure, how does `nonlocal` work, and what problems can mutable closure state introduce?

**Question (RU):** Что такое замыкание, как работает `nonlocal` и какие проблемы может создавать изменяемое состояние замыкания?

**Answer**

A closure retains access to variables from an enclosing function scope. `nonlocal` allows rebinding a name in the nearest enclosing function scope. Mutable state can unexpectedly be shared across calls and wrapper instances that share the same closure. Under concurrent access it can introduce race conditions, so ownership, lifecycle, and synchronization must be explicit.

**Interview-Ready Answer (EN)**

“A closure retains access to variables from an enclosing function scope. `nonlocal` allows rebinding an existing variable in the nearest enclosing function scope. Mutable closure state can be shared across calls and may introduce race conditions, so I make its lifecycle and concurrency guarantees explicit.”

### PY-014 / FU-4 — Senior judgment: Why are `functools.wraps`, decorator order, and async-aware wrappers important in production systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** Why are `functools.wraps`, decorator order, and async-aware wrappers important in production systems?

**Question (RU):** Почему `functools.wraps`, порядок декораторов и поддержка async важны в production-системах?

**Answer**

`wraps` preserves important metadata and adds `__wrapped__`, supporting introspection and tooling. Decorator order determines behavior nesting and can affect security: for example, authorization should run before a protected cached result is returned. For an `async def` target, an async wrapper should await the coroutine if it needs to surround the operation's actual completion; otherwise post-call logic may run before the operation executes.

**Interview-Ready Answer (EN)**

“`functools.wraps` preserves metadata and exposes the wrapped callable for introspection. Decorator order defines execution nesting and can affect security and caching semantics. For asynchronous functions, the wrapper must await the coroutine when it needs to observe or control the operation's completion.”
---

# PY-015 — Scope, LEGB Rule & Name Resolution ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** Explain Python's scope rules, the LEGB rule, and how name resolution works.

## Understand the idea

A name is a binding to an object, not a box that contains a value. Name resolution is the process Python uses to determine which binding an expression refers to.

For ordinary name lookup in a function, the LEGB mnemonic describes the search order:

- **Local:** the current function's local scope.
- **Enclosing:** the local scopes of enclosing functions, from nearest to farthest.
- **Global:** the current module's global namespace.
- **Built-in:** the built-in namespace.

If no binding is found, Python raises `NameError`.

## How Python determines local names

Python determines the scope of names from the code block's binding operations. If a name is bound anywhere in a function block, it is treated as local throughout that block unless declared `global` or `nonlocal`. This is a compile-time scope decision, not a decision made only when the assignment line executes.

Consequently, reading that local name before its assignment raises `UnboundLocalError`. This is a subclass of `NameError`.

## global and nonlocal

- `global name` makes assignments to the name target the module's global namespace. A function can read a global name without declaring it global; the declaration is needed when rebinding it.
- `nonlocal name` makes the name refer to an existing binding in the nearest enclosing function scope. It cannot refer to a module-level global. If no suitable enclosing binding exists, compilation raises `SyntaxError`.

Both statements are parser directives applying to the current code block, not runtime commands that dynamically change another block's scope.

## Closures and late binding

A closure lets an inner function retain access to variables from an enclosing function after that outer function has returned. Conceptually, it retains access to the binding, not necessarily a snapshot of the value.

Free-variable lookup occurs when the inner function executes. Therefore, if the enclosing binding changes before that call, the inner function observes the updated value. This is called late binding and explains common loop-created-lambda surprises.

## Class scope and special cases

A class body's namespace becomes the class attribute namespace, but it is not an enclosing lexical scope for methods. A method does not resolve a bare name by searching the class namespace as though it were an enclosing function. Access class data through an instance or class attribute.

Python 3.12+ annotation scopes are a deliberate exception: they can access their enclosing class namespace. Comprehensions also have their own scope rules; their iteration variables do not normally leak into the containing scope.

The LEGB mnemonic is a useful model for ordinary function lookup, not a complete description of every construct. Class blocks, annotation scopes, and dynamic execution through `exec()` or `eval()` have special rules. In particular, `eval()` and `exec()` do not resolve free variables through the nearest enclosing function scope in the same way as a nested function.

## Interview-ready answer (EN)

“Python resolves ordinary function-level names using the LEGB model: Local, Enclosing, Global, and Built-in. The compiler determines whether a name is local by examining binding operations in the function block. Therefore, assigning to a name anywhere in a function normally makes it local throughout that function, unless it is declared global or nonlocal. Reading it before the assignment can raise UnboundLocalError.

The global statement directs rebinding to the module namespace, while nonlocal targets an existing binding in the nearest enclosing function scope. Closures preserve access to enclosing bindings, and free-variable lookup happens when the closure executes, which explains late binding. I also account for special cases such as class namespaces, annotation scopes, and dynamic execution rather than treating LEGB as a universal lookup algorithm.”

## What to remember

- LEGB is the normal function name-lookup model.
- A binding anywhere in a function block usually makes that name local throughout the block.
- `global` targets the module namespace; `nonlocal` targets the nearest enclosing function binding.
- Closures retain access to bindings; they do not necessarily capture value snapshots.
- Class namespaces are not ordinary enclosing scopes for methods.

## References

- Python 3.15.2 Language Reference: [Execution model](https://docs.python.org/3.15/reference/executionmodel.html)
- [global and nonlocal statements](https://docs.python.org/3.15/reference/simple_stmts.html#the-global-statement)
- [Compound statements](https://docs.python.org/3.15/reference/compound_stmts.html)

---

## PY-015 / FU-1 — How does Python apply LEGB, and how are local names determined? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** How does Python apply the LEGB lookup order, and how does it determine whether a name is local?

**Explanation**

For ordinary function lookup, Python checks the current local scope, enclosing function scopes, the module globals, and then built-ins. However, the compiler classifies names in a function block by examining binding operations such as assignment, import, function definition, and relevant binding constructs. A name assigned anywhere in that block is local throughout the block unless declared global or nonlocal.

**Interview answer (EN)**

“LEGB describes the ordinary lookup order: Local, Enclosing, Global, and Built-in. Local-variable classification is determined from the function block's binding operations, not from the runtime path taken. That is why a read before a conditional assignment can raise UnboundLocalError instead of falling back to a global binding.”

---

## PY-015 / FU-2 — How would you diagnose UnboundLocalError and choose local, global, or nonlocal? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How would you diagnose an UnboundLocalError, and when would you use a local variable, global, or nonlocal?

**Explanation**

First identify every binding operation for the name in the function. If the function assigns to it, Python classifies it as local unless a scope declaration changes that classification. Then determine the intended ownership:

- Prefer a local variable for per-call state.
- Use `nonlocal` when a nested function intentionally updates state owned by an enclosing function.
- Use `global` only when rebinding module-level state is genuinely part of the design.

In production code, explicit objects, dependency injection, or encapsulated state are often easier to test than mutable module globals.

**Interview answer (EN)**

“I diagnose UnboundLocalError by checking whether the function binds the name anywhere in its block and whether the read can occur before that binding. I then choose scope based on ownership: local for call-specific state, nonlocal for intentionally shared enclosing-function state, and global only for deliberate module-level rebinding. I generally avoid mutable globals because they complicate tests, concurrency, and lifecycle management.”

---

## PY-015 / FU-3 — Why do methods not close over class namespaces, and what is late binding? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Why is a class namespace not an enclosing scope for methods, and how does late binding affect closures?

**Explanation**

A class body executes in a namespace that becomes the class's attribute dictionary. That namespace is not an ordinary lexical enclosing function scope for methods. Methods should access class or instance data through attributes. Annotation scopes introduced with modern type-parameter and type-alias features are a specific exception and can access the enclosing class namespace.

A closure resolves its free-variable binding when it runs. If a loop repeatedly changes the enclosing variable, functions created in that loop may all observe the final binding when later invoked. A factory function can create a separate enclosing binding per function; a default argument can also capture the current object at definition time, though it changes the function's parameter defaults and should be used deliberately.

**Interview answer (EN)**

“Methods do not lexically close over the class body's namespace; the class namespace becomes attributes, which methods access through the class or instance. Annotation scopes are a documented exception. Late binding means a closure reads the current enclosing binding when it executes, not necessarily the value that existed when the closure was created. I avoid loop-capture bugs by creating a distinct scope per iteration or by deliberately binding the value at definition time.”

---

## PY-015 / FU-4 — How should senior engineers manage scope and dynamic name resolution in production? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How do you manage scope and dynamic name resolution in production systems?

**Explanation**

Prefer explicit dependencies and state ownership over hidden mutable globals. Keep function-local state isolated per invocation, use closures only when their retained state is intentional, and document shared mutable state and its synchronization requirements.

Treat `exec()` and `eval()` as dynamic execution boundaries. They complicate auditing, debugging, and security, and their namespace behavior is not identical to ordinary lexical closure lookup. Avoid using them for routine configuration or dispatch when explicit mappings, registries, or dependency injection provide clearer behavior.

**Interview answer (EN)**

“In production, I make state ownership explicit and minimize mutable module-level state. I use closures when encapsulated state is useful, but consider lifetime, concurrency, and test isolation. I avoid dynamic execution unless there is a compelling, controlled requirement, because exec and eval complicate security and name resolution. For extensibility, explicit registries and dependency injection are generally easier to reason about and test.”
---

# PY-016 — Mutable vs Immutable Objects, Aliasing & Object Sharing ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** Explain the difference between mutable and immutable objects in Python, and how aliasing and object sharing affect program behavior.

## Understand the idea

In Python, names refer to objects. Assignment creates a binding between a name and an object; it does not copy the object.

- **Mutable object:** its state can be changed after creation. Common examples include `list`, `dict`, `set`, and `bytearray`.
- **Immutable object:** its state cannot be changed after creation. Common examples include `int`, `float`, `bool`, `str`, `bytes`, and `tuple`.

Immutability does not prevent rebinding a variable. A name can be made to refer to another object; the original immutable object remains unchanged.

## Mutation vs rebinding

- **Mutation** changes the state of an existing object. Every name that refers to that same mutable object observes the change.
- **Rebinding** changes which object a particular name refers to. Other names are not automatically redirected.

This distinction is the basis of aliasing and many surprising side effects.

## Aliasing and object sharing

Aliasing means that multiple names or data structures hold references to the same object. If that object is mutable, a mutation through one alias is observable through the others.

Assignment such as `second = first` creates another reference; it does not create an independent copy. To isolate state, choose an appropriate copy strategy or construct a new object explicitly.

## Immutability is not necessarily deep

An immutable container cannot change its own collection of directly referenced objects. However, it may contain references to mutable objects. For example, a tuple can contain a list: the tuple's element reference cannot be replaced, but the referenced list can still be mutated.

Therefore, an immutable outer container is not automatically a deeply immutable object graph. A frozen dataclass also does not recursively freeze mutable objects stored in its fields.

## Shallow copy vs deep copy

- **Shallow copy** creates a new outer compound object but reuses references to its contained objects. Mutating a nested mutable object may therefore be visible through both structures.
- **Deep copy** recursively copies contained objects where supported, aiming to create a more independent object graph.

Deep copy is not always desirable: it can copy too much, has to handle cycles and shared references, and custom classes may control copying. The `copy.deepcopy()` implementation uses a memo to avoid repeatedly copying the same object and to handle recursive structures. Prefer explicit construction or shallow copying when that matches the required ownership semantics.

Python 3.13+ also provides `copy.replace()` for supported types such as dataclasses and named tuples; it creates a new object with selected fields replaced, rather than performing a general deep copy.

## Function arguments: object sharing

Python's argument passing is often described as **call by sharing** (or object sharing). The parameter becomes a new local name bound to the same object supplied by the caller.

- Mutating a passed mutable object can affect the caller's view of that object.
- Rebinding the parameter to another object does not rebind the caller's variable.
- Passing an immutable object does not make it mutable; operations that appear to change its value produce or return another object.

This is neither traditional call by reference nor a copy of every argument.

## Common production pitfalls

- **Mutable default arguments:** default values are evaluated once when the function is defined. A mutable default can therefore be shared across calls. Use a sentinel such as `None` and create per-call state inside the function when sharing is not intended.
- **Shared state:** caches, registries, and objects passed across components can introduce hidden coupling. Define ownership and mutation boundaries explicitly.
- **Concurrency:** shared mutable state can require synchronization even if individual interpreter operations appear safe. The GIL is not an application-level consistency guarantee.
- **Hashing:** objects used as dictionary keys or set elements must obey the hash/equality contract. Mutable value-based objects are generally unsuitable as keys because changing equality-relevant state while stored can break lookup assumptions.

## A subtle case: augmented assignment

The behavior of `+=` depends on the object's type and implementation. Lists typically mutate in place; integers and tuples produce a new value/object binding. Therefore, do not assume augmented assignment always mutates or always creates a new object.

## Interview-ready answer (EN)

“Mutable objects can change their state after creation, while immutable objects cannot. Assignment in Python creates a binding; it does not copy an object. If two names refer to the same mutable object, a mutation through either name is visible through both. Rebinding one name, however, does not redirect the other.

A shallow copy creates a new outer container but retains references to nested objects; a deep copy recursively copies the object graph where supported, which may be more expensive and can copy data that should remain shared. Python passes arguments by object sharing: a function parameter refers to the caller's object, so mutation can be observable by the caller, while rebinding the parameter is local. In production, I define ownership and mutation boundaries, avoid mutable defaults, and use copying only when independent state is actually required.”

## What to remember

- Assignment binds names; it does not copy objects.
- Mutation changes an object; rebinding changes a name's target.
- Aliases to one mutable object observe the same mutations.
- Shallow copy duplicates the outer container; deep copy recursively copies supported contents.
- Immutable containers can still reference mutable objects.
- Function parameters share object references with the caller.
- Avoid unintended shared mutable defaults and state.

## References

- Python 3.15.2 Language Reference: [Objects, values and types](https://docs.python.org/3.15/reference/datamodel.html#objects-values-and-types)
- [copy — Shallow and deep copy operations](https://docs.python.org/3.15/library/copy.html)
- [Programming FAQ](https://docs.python.org/3.15/faq/programming.html)
- [Expressions — Calls and argument binding](https://docs.python.org/3.15/reference/expressions.html#calls)

---

## PY-016 / FU-1 — What is the difference between mutation, rebinding, and aliasing? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** Explain mutation, rebinding, and aliasing. Why can changing an object through one name affect another name?

**Explanation**

A name is a binding to an object. Aliasing exists when multiple names refer to the same object. Mutation changes that shared object's state, so all aliases observe the changed state. Rebinding only changes one name's target and does not modify the original object or other names.

**Interview answer (EN)**

“Mutation changes an existing object's state; rebinding changes which object a name refers to. Assignment creates a binding rather than a copy. When two names alias the same mutable object, a mutation through either name is visible through both, but rebinding one name does not affect the other.”

---

## PY-016 / FU-2 — How do shallow copy and deep copy differ, and when would you use each? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How do shallow and deep copying differ, and how would you choose a copying strategy in a real application?

**Explanation**

A shallow copy creates a new outer container but reuses references to nested objects. A deep copy recursively copies nested objects where supported. Deep copying may be expensive, may copy objects that should remain shared, and needs special handling for cycles and custom objects.

Choose based on ownership requirements:
- Use no copy when shared identity is intentional.
- Use a shallow copy when only the outer container must be independent.
- Use a deep copy when an independent nested object graph is required and all contained objects support the intended semantics.
- Prefer explicit construction when only selected fields should be copied.

**Interview answer (EN)**

“I choose a copy strategy from the ownership contract. A shallow copy isolates the outer container but preserves nested references. A deep copy recursively duplicates supported contents and is appropriate only when an independent object graph is required. I avoid deep-copying indiscriminately because it can be costly and duplicate resources or state that should remain shared.”

---

## PY-016 / FU-3 — Why can a tuple contain mutable state, and what happens when mutable objects are passed to functions? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** How can an immutable tuple contain mutable state, and what does Python's call-by-sharing argument model imply for function calls?

**Explanation**

A tuple's structure—the identities of its directly referenced elements—cannot be changed, but one of those elements may itself be mutable. Mutating that nested object does not replace the tuple's element reference.

For function calls, a parameter is a local name bound to the same object passed by the caller. Mutating a mutable argument can be visible to the caller; rebinding the parameter is local and does not rebind the caller's variable.

**Interview answer (EN)**

“Immutability applies to the tuple's own structure, not recursively to every object it references. A tuple can contain a list, and that list can still be mutated. Python uses object sharing for arguments: the parameter and caller initially refer to the same object. Mutations can be observable by the caller, but rebinding the parameter does not change the caller's binding.”

---

## PY-016 / FU-4 — How do you prevent unintended shared mutable state in production systems? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How do you manage object ownership and prevent unintended shared mutable state in production systems?

**Explanation**

Make ownership and mutation boundaries explicit. Avoid mutable default arguments because defaults are evaluated once at function definition and reused across calls. Use per-call construction when independent state is required. For shared caches or registries, document lifecycle, consistency, and synchronization. Do not rely on the GIL as a substitute for application-level synchronization.

**Interview answer (EN)**

“I define which component owns an object and which components may mutate it. I avoid mutable defaults unless shared state is intentional, use explicit copying or immutable data structures at boundaries, and protect shared mutable state with an appropriate synchronization strategy. I also test aliasing and mutation behavior because accidental sharing often creates order-dependent bugs and cross-request state leakage.”
---

# PY-017 — Python Argument Passing, Parameter Semantics & Function Signatures ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** Explain Python's argument-passing model, parameter semantics, and function signatures. How does Python bind arguments to parameters?

## Core concepts

- A **parameter** is a name declared in a function definition.
- An **argument** is a value or expression supplied in a function call.
- **Argument binding** maps supplied arguments to the function's parameters.
- A **signature** describes the callable's accepted parameters, their kinds, defaults, and annotations.

Python uses **object sharing** (also called call by sharing): a parameter becomes a local name bound to the object supplied by the caller. Mutating a shared mutable object can be visible to the caller; rebinding the local parameter does not rebind the caller's variable.

## The five parameter kinds

1. **Positional-only:** must be supplied by position. The `/` marker separates these parameters from the rest.
2. **Positional-or-keyword:** can be supplied either by position or by keyword. This is the default parameter kind.
3. **Variadic positional:** `*args` collects extra positional arguments into a tuple.
4. **Keyword-only:** must be supplied by keyword. A bare `*` or a `*args` parameter marks the boundary.
5. **Variadic keyword:** `**kwargs` collects extra keyword arguments into a dictionary.

The `/` and `*` markers are syntax separators, not parameters themselves.

## Argument binding process

At a high level, Python:
1. Evaluates the callable and argument expressions.
2. Assigns positional arguments to the corresponding positional slots.
3. Matches keyword arguments by parameter name.
4. Detects duplicate assignments to the same parameter.
5. Fills remaining parameters from their default values.
6. Raises `TypeError` if required parameters remain missing, unexpected arguments are supplied, or the call otherwise violates the signature.

A parameter cannot receive a value twice. A supplied `None` is a value, not an indication that the argument was omitted. Keyword argument order is not generally significant for binding.

## Defaults and evaluation time

Default expressions are evaluated once when the function definition executes, not once per call. The resulting objects are reused by calls that omit those arguments. This is why mutable defaults can accidentally retain state across calls.

Use a sentinel such as `None` when a fresh mutable object is required for each invocation. Distinguish “argument omitted” from “argument explicitly supplied as None” when the API needs that distinction; a unique sentinel object is often appropriate.

## Argument unpacking

- `*iterable` in a call expands an iterable into positional arguments.
- `**mapping` expands a mapping into keyword arguments, whose keys must be strings matching accepted parameter names unless captured by `**kwargs`.
- During a call, positional arguments must precede explicit keyword arguments in the call syntax.
- Multiple unpackings are permitted when their resulting arguments do not cause duplicate bindings or other conflicts.

Unpacking changes how values are supplied; it does not change the target callable's signature.

## Annotations and runtime behavior

Parameter and return annotations are metadata. Python does not automatically enforce ordinary type annotations at function-call time. Static type checkers, IDEs, frameworks, and explicit validation libraries may interpret them.

Annotations therefore do not replace input validation at trust boundaries.

## Signature introspection

The `inspect` module exposes callable signatures:
- `inspect.signature(callable)` returns an `inspect.Signature`.
- Its `parameters` mapping describes each parameter and its kind/default/annotation.
- `Signature.bind(*args, **kwargs)` checks a proposed call against the signature and returns `BoundArguments`, or raises `TypeError`.
- `bind_partial()` permits required parameters to remain unbound, which is useful for partial-call construction.
- `apply_defaults()` fills defaults into a `BoundArguments` mapping.

Not every callable is introspectable, and some built-in or extension callables expose limited signature metadata. Treat introspection as a tool, not an absolute guarantee.

## API design guidance

Use positional-only parameters when parameter names should not become part of the public API or when positional calling is intentional. Use keyword-only parameters for configuration options where names improve readability and reduce call-site ambiguity. Avoid accepting arbitrary `**kwargs` unless extensibility or forwarding is a deliberate part of the API contract.

Keep defaults immutable where practical, document whether `None` means “not supplied” or is a valid value, and validate external input explicitly.

## Interview-ready answer (EN)

“Python functions define parameters in a signature, and callers provide arguments that are bound to those parameters. Python supports five parameter kinds: positional-only, positional-or-keyword, variadic positional, keyword-only, and variadic keyword. The slash marks positional-only parameters, while the star marks the keyword-only boundary; `*args` and `**kwargs` collect additional arguments.

During argument binding, positional values fill positional slots, keyword values are matched by name, defaults fill remaining optional slots, and invalid or duplicate assignments raise TypeError. Python uses object sharing: parameters refer to the objects supplied by the caller, so mutation can be observable while local rebinding is not. Defaults are evaluated once at function definition, and annotations are not automatically enforced at runtime. For API design and tooling, I use explicit parameter kinds and `inspect.Signature.bind()` when I need reliable signature-aware argument validation.”

## What to remember

- Parameters belong to definitions; arguments belong to calls.
- Python has five parameter kinds.
- `/` marks positional-only; `*` marks keyword-only.
- `*args` collects a tuple; `**kwargs` collects a dictionary.
- Binding errors such as missing, duplicate, or unexpected arguments raise `TypeError`.
- Defaults are evaluated once at function definition.
- Annotations do not automatically validate calls at runtime.
- `inspect.Signature.bind()` can validate argument binding.

## References

- [Python 3.15.2 — Function definitions](https://docs.python.org/3.15/reference/compound_stmts.html#function-definitions)
- [Python 3.15.2 — Calls](https://docs.python.org/3.15/reference/expressions.html#calls)
- [Python 3.15.2 — Special parameters](https://docs.python.org/3.15/tutorial/controlflow.html#special-parameters)
- [Python 3.15.2 — inspect.Signature](https://docs.python.org/3.15/library/inspect.html#introspecting-callables-with-the-signature-object)

---

## PY-017 / FU-1 — How does Python bind positional and keyword arguments, and which errors can occur? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** Explain the argument-binding process and the most common reasons a function call raises TypeError.

**Explanation**

Positional arguments fill positional parameter slots in order. Keyword arguments fill slots by name. Defaults fill unassigned optional parameters. A call fails when a required parameter is missing, a parameter receives multiple values, an unsupported keyword is supplied, or too many positional arguments are provided without a variadic positional parameter.

**Interview answer (EN)**

“Python first maps positional arguments to positional slots, then matches keyword arguments by name, and finally applies defaults to unfilled optional parameters. It raises TypeError for missing required parameters, duplicate values, unexpected keywords, or excess positional arguments. A parameter can be bound only once.”

---

## PY-017 / FU-2 — When should an API use positional-only and keyword-only parameters? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** How do positional-only and keyword-only parameters improve API design?

**Explanation**

Positional-only parameters prevent callers from depending on parameter names and can preserve flexibility to rename those parameters later. Keyword-only parameters make configuration explicit, improve readability, and prevent callers from accidentally relying on positional order for options.

**Interview answer (EN)**

“I use positional-only parameters when names are implementation details or positional calling is part of the intended interface. I use keyword-only parameters for options and configuration because named arguments make call sites clearer and more robust. I choose parameter kinds deliberately as part of the public API contract.”

---

## PY-017 / FU-3 — Why are mutable defaults dangerous, and what is the role of annotations? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** Why can mutable default arguments cause bugs, and do type annotations validate arguments at runtime?

**Explanation**

Default expressions are evaluated once when the function definition executes. A mutable object used as a default is therefore reused across calls that omit the argument. Use a sentinel and create fresh per-call state when needed.

Ordinary type annotations do not automatically enforce argument types at runtime. They provide metadata for static analysis and tools; runtime validation must be implemented explicitly or delegated to a validation framework.

**Interview answer (EN)**

“Mutable defaults are shared because defaults are evaluated once at function definition, not on every call. I use a sentinel and create a new object inside the function when each call needs independent state. Type annotations are not runtime enforcement by themselves, so external or untrusted inputs still require explicit validation.”

---

## PY-017 / FU-4 — How do you inspect and validate callable signatures in frameworks and production tooling? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How would you use `inspect.Signature` to validate or adapt arguments in a framework, and what limitations would you consider?

**Explanation**

Use `inspect.signature()` to obtain a callable's signature and `Signature.bind()` to validate positional and keyword arguments against it. `bind_partial()` is useful when constructing partially applied calls. Apply defaults explicitly if the framework needs a complete mapping.

Not every callable exposes complete introspection metadata. Decorators may affect the visible signature; `functools.wraps` and the `__wrapped__` chain help introspection tools discover the wrapped callable, but custom or extension callables may still be limited.

**Interview answer (EN)**

“I use inspect.signature() to obtain a callable's declared interface and Signature.bind() to validate argument mapping before dispatch. I use bind_partial() for staged or partial invocation and apply_defaults() when the framework needs defaulted values included. I account for decorated callables and incomplete metadata, and I avoid treating introspection as a substitute for domain validation or authorization.”
---

# PY-018 — Python Functions: First-Class Objects, Higher-Order Functions & Functional Programming ![TYPE](https://img.shields.io/badge/TYPE-MAIN_QUESTION-2563eb) ![LEVEL](https://img.shields.io/badge/LEVEL-L3-7c3aed) ![PRIORITY](https://img.shields.io/badge/PRIORITY-P0-d97706)

**Question (EN):** Explain why functions are first-class objects in Python. How do higher-order functions, closures, and functional programming relate to this concept?

## Core concepts

A Python function is an object that can be:
- assigned to a variable;
- passed as an argument;
- returned from another function;
- stored in a data structure;
- inspected and, for ordinary Python function objects, augmented with attributes.

This is the meaning of **first-class functions**: functions can be manipulated as values like other objects. A function reference and a function call are different: referring to a function does not execute it; calling it does.

A callable is broader than a function. Instances of classes implementing `__call__`, bound methods, built-in functions, and `functools.partial` objects can also be callable.

## Higher-order functions

A **higher-order function** accepts one or more functions/callables as arguments, returns a function/callable, or both.

Examples:
- `sorted(iterable, key=...)` accepts a callable used to derive sorting keys.
- `map()` applies a callable to items and returns an iterator.
- `filter()` uses a predicate to select items.
- `functools.reduce()` cumulatively combines iterable elements with a callable.
- `functools.partial()` creates a callable with some arguments pre-filled.
- Decorators accept a callable and commonly return a wrapped callable.

Do not confuse the concepts: first-class describes how the language treats functions; higher-order describes what a particular function does with callables.

## Closures and lexical scope

A **closure** is a function together with access to variables from its enclosing lexical scope. An inner function can continue to access enclosing-scope bindings after the outer function has returned.

A variable referenced from an enclosing scope rather than locally or globally is commonly called a free variable. The function's closure retains the necessary binding context.

Closures are useful for:
- function factories and configurable behavior;
- decorators;
- callbacks that need context;
- encapsulating small pieces of state without defining a class.

A closure does not automatically make captured state immutable or thread-safe. If multiple calls or threads mutate shared captured state, synchronization and lifecycle need deliberate design. Late binding also matters: a closure generally observes the current value of the captured binding when the inner function executes, not necessarily a snapshot taken when it was created.

## Functional programming in Python

Python supports functional programming but is multi-paradigm; it does not require a purely functional style.

Useful concepts include:
- **Pure functions:** same relevant inputs produce the same result, with no externally observable side effects.
- **Immutability:** prefer values that are not mutated, or create new values instead of changing shared state.
- **Higher-order functions:** compose behavior by passing functions as values.
- **Function composition:** combine smaller transformations into a larger operation.
- **Declarative transformations:** express the desired transformation rather than manually controlling every iteration step.

Purity is a design property, not something Python enforces. A function can read global state, perform I/O, mutate arguments, or raise exceptions.

## Practical trade-offs

Functional techniques can improve testability, reuse, and reasoning when transformations are isolated and side effects are explicit. However, excessive callbacks, nested closures, or chains of opaque transformations can make debugging and control flow harder.

Choose the simplest design that makes data flow and side effects clear. Use classes when state, invariants, and lifecycle are central; use functions when behavior is naturally composable and stateless or when a small closure is sufficient.

## Backend engineering applications

- Middleware and decorators that wrap request handling.
- Dependency injection through provider callables.
- Event callbacks and hooks.
- Validation predicates and filtering.
- Data-processing pipelines and transformations.
- Retry, caching, metrics, and tracing wrappers.
- Async schedulers and APIs that accept coroutine functions or other callables.

Remember that an async function is still a function object; calling it creates a coroutine object. A callable is not necessarily a synchronous function, so frameworks must understand whether the returned object needs to be awaited.

## Interview-ready answer (EN)

“Python functions are first-class objects: they can be assigned to variables, passed as arguments, returned from other functions, and stored in data structures. This enables higher-order functions, which accept or return callables. Examples include decorators, callbacks, map, filter, and functools.partial.

Closures allow inner functions to retain access to variables from their enclosing lexical scope. They are useful for function factories, decorators, callbacks, and encapsulated state, although shared mutable closure state requires careful lifecycle and concurrency design.

Python supports functional programming concepts such as pure functions, immutability, composition, and declarative transformations, but it remains a multi-paradigm language. I choose functional or object-oriented techniques based on clarity, testability, maintainability, and performance.”

## What to remember

- First-class means functions can be treated as values.
- Higher-order functions accept or return callables.
- A callable is not necessarily a Python function object.
- Closures retain access to enclosing-scope bindings.
- Captured mutable state is not automatically immutable or thread-safe.
- Python supports functional programming but does not enforce purity.
- Prefer clear data flow and explicit side effects over unnecessary abstraction.

## References

- [Python 3.15.2 — Functional Programming HOWTO](https://docs.python.org/3.15/howto/functional.html)
- [Python 3.15.2 — functools](https://docs.python.org/3.15/library/functools.html)
- [Python 3.15.2 — Built-in functions: map](https://docs.python.org/3.15/library/functions.html#map)
- [Python 3.15.2 — Execution model and name resolution](https://docs.python.org/3.15/reference/executionmodel.html)

---

## PY-018 / FU-1 — What makes a function a first-class object, and how is that different from a callable? ![TYPE](https://img.shields.io/badge/TYPE-Mechanism-0ea5e9) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-1_OF_4-64748b)

**Question (EN):** What does it mean that functions are first-class objects, and why is the term callable broader than function?

**Explanation**

First-class means a function can be treated as a value: assigned, passed, returned, and stored. A callable is any object that can be invoked. Ordinary functions, bound methods, built-ins, classes, and instances implementing `__call__` may be callable. Therefore, every ordinary function is callable, but not every callable is a function object.

**Interview answer (EN)**

“First-class describes the ability to manipulate functions as values. Callable describes the ability to invoke an object. A Python function is both, but callable objects also include instances with __call__, classes, bound methods, and partial objects. This distinction matters when designing APIs that accept behavior rather than only function objects.”

---

## PY-018 / FU-2 — How would you use higher-order functions in a backend application? ![TYPE](https://img.shields.io/badge/TYPE-Application-16a34a) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-2_OF_4-64748b)

**Question (EN):** Give practical backend examples of higher-order functions and explain when they improve a design.

**Explanation**

Examples include middleware wrappers, decorators for metrics or authorization, validation predicates, callbacks, dependency providers, and data transformations. They improve a design when behavior can be injected or composed without coupling the caller to a concrete implementation.

**Interview answer (EN)**

“I use higher-order functions when a component needs configurable behavior: middleware can wrap request handling, predicates can be injected into filtering, and decorators can add metrics or tracing. I keep the abstraction explicit and avoid deeply nested callback chains when they make execution order or error handling difficult to follow.”

---

## PY-018 / FU-3 — What are closure late binding and shared mutable state risks? ![TYPE](https://img.shields.io/badge/TYPE-Edge_Cases-d97706) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-3_OF_4-64748b)

**Question (EN):** What does a closure retain, and what problems can arise from late binding or mutable captured state?

**Explanation**

A closure retains access to bindings in an enclosing lexical scope. It does not necessarily capture an immutable snapshot of each value. If a captured binding changes before the inner function runs, the function observes the current binding. Multiple closures may also share the same mutable object. This can produce surprising results in loops, callbacks, and concurrent code.

**Interview answer (EN)**

“A closure retains access to enclosing-scope bindings, not necessarily a frozen copy of their values. Late binding means the inner function can observe a binding's later value. If closures share mutable state, calls can interfere with one another and concurrent execution may require synchronization. I make capture semantics and state ownership explicit, and avoid hidden shared mutation.”

---

## PY-018 / FU-4 — When should you choose functional composition over classes or imperative code? ![TYPE](https://img.shields.io/badge/TYPE-Senior_Judgment-dc2626) ![SEQUENCE](https://img.shields.io/badge/SEQUENCE-4_OF_4-64748b)

**Question (EN):** How do you decide between functional composition, object-oriented design, and imperative control flow in production Python?

**Explanation**

Functional composition is effective for isolated transformations, stateless behavior, and explicit pipelines. Classes are useful when state, invariants, identity, and lifecycle are central. Imperative code is often clearer for complex orchestration, resource management, and control flow. Python supports all three; no paradigm should be applied dogmatically.

**Interview answer (EN)**

“I choose the paradigm that makes state, dependencies, and side effects easiest to understand. I favor small composable functions for transformations and validation, classes when state and invariants have a meaningful lifecycle, and imperative orchestration when it makes control flow clearer. I evaluate testability, readability, operational behavior, and performance rather than maximizing functional purity.”
