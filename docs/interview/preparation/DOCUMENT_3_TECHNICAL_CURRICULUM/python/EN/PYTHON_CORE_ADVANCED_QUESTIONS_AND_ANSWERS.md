# Python Core & Advanced Python — Questions and Answers (EN)

**Language:** English  
**Domain:** Python Core & Advanced Python  
**Python baseline:** 3.15.2. Version-specific behavior is labelled; language guarantees are distinguished from CPython implementation details.  
**Question map:** [English Question Map](./PYTHON_CORE_ADVANCED.md)  
**Navigation:** [Python curriculum index](../README.md)

English study material for PY-001–PY-009 and FU-001–FU-036. Each topic explains the concept and provides an interview-ready answer. The Russian version uses the same question IDs.

**Review status:** Authored; independent technical and editorial review pending. Do not treat this material as finally approved until both reviews are complete.

# PY-001 — Main Question

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

## FU-001 — What does the GIL protect?

**Question (EN):** What does the GIL protect, and why does CPython use it?

**Explanation**

The GIL coordinates access to parts of CPython's internal state and Python objects. Historically, this simplified reference counting and runtime implementation. It does not protect every resource used by an application.

**Interview answer (EN)**

“The GIL coordinates access to interpreter-managed state and objects in the conventional CPython build. It historically simplified reference counting and runtime implementation. Its scope is limited, however: it does not protect arbitrary application data, database transactions, or external resources.”

---

## FU-002 — How does the GIL affect CPU-bound and I/O-bound work?

**Question (EN):** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads?

**Explanation**

CPU-bound work spends most of its time calculating. I/O-bound work spends much of its time waiting for external operations. The GIL limits parallel execution of pure-Python CPU work, but blocking I/O typically releases it so another thread can run.

**Interview answer (EN)**

“In a conventional CPython build, CPU-bound pure-Python threads compete for the GIL and generally do not execute Python bytecode in parallel across cores. I/O-bound threads can still be effective because blocking I/O typically releases the GIL, allowing other threads to run while one is waiting.”

---

## FU-003 — How do you choose between threading, multiprocessing, and asyncio?

**Question (EN):** How would you choose between threading, multiprocessing, and asyncio for a Python backend workload?

**Explanation**

- **Threading:** useful for blocking I/O and some native libraries.
- **Multiprocessing:** useful for CPU-bound Python work; separate processes can run on different CPU cores.
- **Asyncio:** useful for many concurrent I/O tasks when libraries support non-blocking operations. It does not make CPU-heavy code parallel by itself.

**Interview answer (EN)**

“I first identify whether the workload mainly waits for I/O or performs CPU-intensive Python work. I use threads for blocking I/O, multiprocessing for CPU-bound Python tasks when process overhead is justified, and asyncio for high-concurrency I/O when the call stack supports non-blocking operations. I also consider latency, memory, cancellation, backpressure, and operational complexity.”

---

## FU-004 — What changes in free-threaded CPython?

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

# PY-002 — Main Question

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

## FU-005 — Can concurrency exist without parallelism?

**Question (EN):** Can concurrency exist without parallelism?

**Explanation**

Yes. A single thread can make progress on multiple tasks by switching between them, for example while some tasks are waiting for I/O. Their execution overlaps in time, but they are not running simultaneously.

**Interview answer (EN)**

“Yes. Concurrency can exist without parallelism. A single thread can make progress on multiple tasks by switching between them, for example while some tasks are waiting for I/O. The tasks overlap in time but are not executed simultaneously.”

---

## FU-006 — What is the difference between I/O-bound and CPU-bound workloads?

**Question (EN):** What is the difference between I/O-bound and CPU-bound workloads?

**Explanation**

An **I/O-bound** workload spends much of its time waiting for external operations, such as network or database responses. A **CPU-bound** workload spends most of its time performing computations. Threading or asyncio can help with I/O-bound workloads; multiprocessing is often a better fit for CPU-bound Python workloads in conventional CPython.

**Interview answer (EN)**

“An I/O-bound workload spends most of its time waiting for external operations, such as network or database responses. A CPU-bound workload spends most of its time performing computations. Threading or asyncio can help with I/O-bound workloads, while multiprocessing is often a better choice for CPU-bound Python workloads.”

---

## FU-007 — How does the GIL affect concurrency and parallelism in CPython?

**Question (EN):** How does the GIL affect concurrency and parallelism in CPython?

**Explanation**

In conventional CPython builds, the GIL prevents multiple threads from executing Python bytecode simultaneously. Threads can still provide concurrency, especially for I/O-bound workloads, but generally do not provide parallel execution for CPU-bound Python code. Free-threaded builds change this limitation, although extension compatibility and synchronization still matter.

**Interview answer (EN)**

“In conventional CPython builds, the GIL prevents multiple threads from executing Python bytecode simultaneously. Threads can still provide concurrency, especially for I/O-bound workloads, but they generally do not provide parallel execution for CPU-bound Python code. Free-threaded builds change this limitation, although thread safety and extension compatibility still matter.”

---

## FU-008 — How do you decide whether a workload needs concurrency or parallelism?

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

# PY-003 — Main Question

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

## FU-009 — What are the main stages of Python execution?

**Question (EN):** What are the main stages between Python source code and the execution of its instructions in CPython?

**Explanation**

The usual CPython path is: read and decode source, parse it into an AST, compile it into code objects, and execute those objects in the runtime. Execution can create objects, resolve names, call functions, and interact with native libraries or the operating system.

**Interview answer (EN)**

“CPython reads and decodes the source, parses it into an AST, compiles it into code objects containing bytecode and metadata, and then executes those objects in its runtime. During execution, Python creates objects, resolves names, calls functions, and may interact with native libraries and operating-system services.”

---

## FU-010 — Why does running a module differ from importing it?

**Question (EN):** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?

**Explanation**

When a file is run directly, its `__name__` is normally `"__main__"`. When imported, its `__name__` is the module's import name. The package context, import path, working directory, and module-level side effects may also differ. Running a package module with `python -m package.module` often preserves the intended package context better than executing a file by path.

**Interview answer (EN)**

“I compare the execution context first: `__name__`, `__package__`, `sys.path`, the working directory, and the exact command. I then inspect relative imports and module-level side effects. Direct execution normally sets `__name__` to `__main__`, while importing uses the module's import name. For package applications, I prefer a consistent package-aware entry point, such as `python -m package.module`.”

---

## FU-011 — Which execution details are implementation-specific?

**Question (EN):** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?

**Explanation**

Python specifies language semantics, not one universal bytecode format or interpreter architecture. CPython opcodes, inline caches, adaptive specialization, and internal frame representations are implementation details that may change between releases. In particular, do not assume every function call must materialize a Python-visible `PyFrameObject`; CPython's internal execution-frame representation and the frame objects exposed for introspection are distinct concepts.

**Interview answer (EN)**

“Python defines language semantics, but it does not guarantee a particular bytecode format or interpreter implementation. CPython opcodes, specialization strategies, and internal frame representations can change between releases. I rely on documented language behavior for application correctness and use implementation-specific details only when needed for debugging or measured optimization.”

---

## FU-012 — How do you choose the diagnostic layer?

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


# PY-004 — Main Question

**Question (EN):** What happens during a function call in CPython?


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


**Follow-up Questions & Answers**

---

## FU-013 — Execution state during a function call

**Question (EN):** What execution state does CPython need to establish or maintain when entering and executing a Python function?


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


---

## FU-014 — Profiling function-call overhead

**Question (EN):** How can you use profiling and call-stack information to investigate excessive function-call overhead in a Python service?


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


---

## FU-015 — Different execution lifecycles

**Question (EN):** How do recursion, exceptions, generators, and asynchronous functions affect the execution lifecycle compared with an ordinary function call?


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


---

## FU-016 — When call mechanics matter for optimization

**Question (EN):** When would knowledge of CPython call mechanics materially change an optimization decision, and how would you validate that the optimization is worthwhile?


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



## PY-004 review checklist

- [x] Main question and FU-013–FU-016 included.
- [x] Argument binding, execution state, frames, closures, return and exception paths covered.
- [x] Ordinary functions distinguished from generators and coroutines.
- [x] Profiling methodology and optimization trade-offs covered.
- [ ] Independent technical review against supported CPython versions.
- [ ] Final editorial review.

**Completion rule:** Authored material is not finally approved until both review stages are complete.



---

# PY-005 — Main Question

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

Do not confuse Python object identity with domain identity. Two ORM instances may represent the same database row while being distinct Python objects. Use stable domain identifiers across persistence, serialization, and distributed boundaries. The id() value is lifetime-scoped, not a durable key or portable memory address.

**Interview-Ready Answer (EN)**

“Every Python object has an identity, a type, and a value. Identity tells us which particular object we refer to, type defines its behavior, and value represents its data or state. Names are bound to objects, so multiple names can refer to the same object. A mutable object's value can change without changing its identity or type; rebinding a name is different from mutating the object. I use is for identity checks such as None, and == for value equality. I generally prefer isinstance() when subclasses are valid, and protocols when the design should depend on behavior. For persistence and distributed systems, I use explicit domain identifiers rather than Python object identity.”

---

## FU-017 — Identity, type, and value over an object's lifetime

**Question (EN):** Which of an object's identity, type, and value can change during its lifetime?

**Explanation:** Identity and type remain stable throughout an object's lifetime. Its value may change if it is mutable. Mutation changes the existing object; rebinding changes which object a name refers to. Immutability is not necessarily deep: a tuple can contain a mutable list whose contents still change.

**Interview-Ready Answer (EN)**

“An object's identity and type remain constant during its lifetime, while its value may change if it is mutable. Mutation changes the state of the existing object; rebinding changes the object referenced by a name. These are different operations. An immutable container also does not guarantee that every object reachable through it is immutable.”

---

## FU-018 — Choosing identity, equality, and type checks

**Question (EN):** How would you choose between identity checks, equality checks, and type checks in a code review?

**Explanation:** Start with the contract being tested. Use is for object identity and singleton sentinels, == for value equality, and isinstance() when subclasses are accepted. An exact check such as type(value) is int deliberately rejects subclasses and should be used only when that restriction is part of the contract. Review custom __eq__ and __hash__ together when objects are dictionary keys or set members.

**Interview-Ready Answer (EN)**

“I first identify whether the code needs identity, value equality, or type compatibility. I use is for None and explicit sentinels, == for values, and isinstance() when subclasses should be accepted. Exact type checks are appropriate only for a deliberate strict contract. I also review custom equality and hashing because inconsistent implementations can break dictionary and set behavior.”

---

## FU-019 — Why is is not a value comparison?

**Question (EN):** Why can using is to compare strings, numbers, or other values produce unreliable results?

**Explanation:** is tests whether references designate the same object; it does not compare values. Equal values can belong to distinct objects. CPython may reuse or intern some immutable objects, making an incorrect identity comparison appear to work in one context. Such reuse is an implementation optimization, not a language guarantee.

**Interview-Ready Answer (EN)**

“is checks object identity, whereas == checks equality according to the type's comparison semantics. Two separately created values can be equal without being the same object. Interning or constant reuse may make identity comparisons appear to work for some strings or integers, but that behavior is implementation-dependent. I use is for sentinels and == for value comparisons.”

---

## FU-020 — Identity and mutability in API design

**Question (EN):** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types?

**Explanation:** Define whether an API mutates, retains, copies, or returns caller-owned objects. Use stable domain IDs when identity must survive database reloads or process boundaries. Prefer immutable value objects for value-based concepts, while accounting for nested mutability and hash stability. Expose required behavior through protocols or abstractions instead of requiring a concrete class without a clear reason. Validate and normalize external data at system boundaries.

**Interview-Ready Answer (EN)**

“I make ownership and mutation semantics explicit: callers should know whether an API changes an input, retains a reference, or returns shared state. I use stable domain identifiers rather than Python object identity across persistence and distributed boundaries. Immutable value objects are useful when equality is value-based, provided nested state and hashing are handled correctly. I expose required behavior through suitable abstractions or protocols so callers are not coupled to an unnecessary concrete implementation.”

**Status:** Authored; independent technical and editorial review pending.

# PY-006 — Main Question

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

A descriptor is an object whose type defines one or more of `__get__`, `__set__`, or `__delete__`. Descriptors are the foundation of properties, many methods, and several framework features. A function stored on a class is a non-data descriptor: accessing it through an instance creates a bound method by supplying the instance as the receiver. A `property` is a data descriptor and can control reads and writes even when an instance dictionary contains a same-named key.

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

## FU-021 — Attribute lookup precedence

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

## FU-022 — Data descriptors and non-data descriptors

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

## FU-023 — `__getattribute__` versus `__getattr__`

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

## FU-024 — Implicit special-method lookup

**Question (EN):** Why can assigning a special method to an instance fail to change the behavior of an implicit operation such as `len(obj)`?

**What the interviewer evaluates:** Special-method lookup, type-level protocol dispatch, and the distinction between explicit and implicit calls.

**Short Answer**

Implicit special-method operations generally look up the relevant method on the object's type, not through the instance's ordinary attribute namespace. Therefore, assigning `obj.__len__` does not normally change the result of `len(obj)`; the type must implement the corresponding protocol method.

**Detailed Answer**

Python's data model defines protocols through special methods such as `__len__`, `__iter__`, `__next__`, and arithmetic methods. When syntax or a built-in invokes one of these protocols, the interpreter generally performs special lookup on the type. This behavior avoids treating an arbitrary instance attribute as an implementation of a type-level protocol and permits optimized dispatch.

This is different from explicitly evaluating `obj.__len__()`, which is ordinary attribute access followed by a call and may observe an instance attribute. The two expressions are therefore not interchangeable in all circumstances.

**Interview-Ready Answer (EN)**

“Implicit protocol operations such as `len(obj)` generally resolve special methods on the object's type rather than through the instance dictionary. Assigning `obj.__len__` therefore does not normally affect `len(obj)`; the class must provide the protocol implementation. An explicit call to `obj.__len__()` is ordinary attribute lookup, so it can behave differently. This distinction is part of Python's data model and matters when implementing custom container and operator behavior.”



# PY-007 — Main Question

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

A shallow copy creates a new outer container but retains references to the same nested objects. Mutating a nested list or dictionary can therefore be visible through both containers. A tuple is not deeply immutable if it contains mutable objects. Dictionary keys and set elements must maintain stable hash and equality behavior while stored.

**Senior-Level Perspective**

Start with semantics and correctness, then profile representative data sizes and operation mixes. Consider memory per entry, allocation patterns, mutation frequency, iteration order, and whether a specialized structure is justified. Treat CPython layout and microbenchmark results as version- and workload-dependent evidence, not universal rules.

**Interview-Ready Answer (EN)**

“Lists and tuples are ordered sequences: lists are mutable, while tuples are immutable at the container level. Sets hold unique hashable elements and are useful for membership checks and set operations. Dictionaries map unique hashable keys to values and preserve insertion order. In CPython, lists and tuples are array-like containers of references, whereas sets and dictionaries use hash tables. Their common lookup and membership operations are typically average O(1), while list indexing is O(1) and middle insertion or deletion is O(n). I choose based on required semantics first, then benchmark realistic workloads and account for memory, mutation patterns, and hash behavior.”

**References**

- [Python 3.15 documentation: Built-in Types](https://docs.python.org/3.15/library/stdtypes.html)
- [Python 3.15 documentation: Data model](https://docs.python.org/3.15/reference/datamodel.html)

---

## FU-025 — Collection semantics and CPython representations

**Question (EN):** What are the key semantic and typical implementation differences between lists, tuples, sets, and dictionaries in CPython?

**Answer**

Lists and tuples are ordered sequences indexed by position; lists allow item replacement and resizing, while tuples do not. Sets contain unique hashable elements, and dictionaries associate hashable keys with values while preserving insertion order. CPython typically implements sequences as arrays of object references and sets/dictionaries with hash-table structures. The semantic contract should be separated from implementation: exact layouts, resizing policies, and memory costs may evolve.

**Interview-Ready Answer (EN)**

“Lists and tuples are ordered sequences, with mutability being the main semantic difference. Sets represent unique hashable members, while dictionaries represent key-value mappings with insertion-ordered iteration. In CPython, sequences use array-like reference storage, and sets and dictionaries use hash tables. I distinguish these implementation details from language-level guarantees.”

---

## FU-026 — Selecting a collection for a service

**Question (EN):** How would you choose a built-in collection for an ordered sequence, membership checks, deduplication, and keyed lookup in a real service?

**Answer**

Use a list for an ordered sequence that may change, a tuple for a fixed sequence, a set for uniqueness and membership, and a dictionary for lookup by key. A request pipeline might use a list to preserve processing order, a set to track processed identifiers, and a dictionary to retrieve records by identifier. Maintaining duplicate structures adds memory and consistency costs, so do it only when the access pattern justifies it.

**Interview-Ready Answer (EN)**

“I map the collection to the dominant operation: list or tuple for sequence semantics, set for uniqueness and membership, and dict for keyed retrieval. If both stable order and fast membership are required, I may use a list plus a set, but I make update ownership explicit and test consistency.”

---

## FU-027 — Ordering, copying, and complexity edge cases

**Question (EN):** What should you consider when relying on insertion order, shallow copying, nested mutable values, or average-case complexity?

**Answer**

Dictionary insertion order is guaranteed by the language, but set iteration order is not a stable ordering contract. Shallow copies retain references to nested objects. Average-case hash-table complexity is not a worst-case guarantee, and tuples are only shallowly immutable. Since Python 3.7, dictionary insertion order is guaranteed. Do not rely on set iteration order for deterministic presentation. A shallow list or dictionary copy duplicates only the outer container. Hash collisions and expensive equality methods can increase lookup cost; a tuple containing a list is unhashable.

**Interview-Ready Answer (EN)**

“I rely on dictionary insertion order because it is a language guarantee, but I do not rely on set iteration order. Shallow copies share nested objects, and tuple immutability does not make referenced objects immutable. Average O(1) hash-table operations are not worst-case guarantees, so I consider collision behavior and real data.”

---

## FU-028 — Collection choice under production constraints

**Question (EN):** How would workload shape, data volume, mutation patterns, and memory pressure influence your collection choice and benchmarking strategy?

**Answer**

Identify the operation mix, data volume, ordering requirements, mutation frequency, and memory budget, then benchmark representative workloads. Measure latency, throughput, and memory rather than extrapolating from small synthetic examples. Include realistic key distributions, hit/miss ratios, object sizes, and construction/update costs. Avoid redundant indexes unless their measured latency benefit outweighs memory and consistency costs.

**Interview-Ready Answer (EN)**

“I start from the production access pattern: reads versus writes, lookup versus iteration, ordering, data size, and memory limits. Then I benchmark representative distributions and measure latency and memory, including build and update costs. I avoid choosing from asymptotic complexity alone, and keep redundant indexes only when their measured benefit justifies their operational cost.”


# PY-008 — Main Question

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

## FU-029 — The hash and equality contract

**Question (EN):** What contract must __hash__() and __eq__() satisfy for objects used as dictionary keys?

**Answer**

The essential rule is: if a == b, then hash(a) == hash(b). The reverse is not required; unequal objects may have identical hashes. A key's hash and equality behavior must remain stable while it is stored. If a class overrides __eq__() but does not provide a compatible __hash__(), Python normally marks instances as unhashable. For value-based keys, compute equality and hashing from the same immutable state.

**Interview-Ready Answer (EN)**

“Equal objects must have equal hashes, but equal hashes do not imply equal objects. Hash collisions are valid and are resolved by equality checks. A key must also remain stable while stored, so I base custom hashing and equality on immutable fields.”

---

## FU-030 — Collision resolution and resizing

**Question (EN):** What happens when dictionary keys collide, and why can insertion or lookup become slower?

**Answer**

A collision means multiple keys compete for a candidate table position. CPython follows a probing strategy to find another slot and checks candidate keys for equality. As the table becomes more occupied, resizing allocates a larger table and redistributes entries. Typical operations remain average O(1), and insertion is amortized O(1), but pathological collision patterns or expensive equality checks can degrade performance. The exact probing algorithm is a CPython implementation detail.

**Interview-Ready Answer (EN)**

“Collisions are expected and do not break correctness: the table probes for candidate slots and equality determines whether a key matches. Resizing controls table occupancy as it grows. Average complexity is O(1), but worst-case behavior can be much slower, especially with pathological collisions or expensive equality methods.”

---

## FU-031 — Mutable custom keys and hash stability

**Question (EN):** Why is it dangerous to use a mutable object as a dictionary key, and how should a custom key type be designed?

**Answer**

If a key's hash changes after insertion, the dictionary may search for it using a different location from the one where it was stored. If equality-relevant state changes, lookup and uniqueness behavior can also become inconsistent. A custom key should derive __eq__() and __hash__() from the same immutable fields. If equality is based on mutable state, the type should generally be unhashable.

**Interview-Ready Answer (EN)**

“A dictionary relies on a key's hash and equality remaining stable. Mutating fields that participate in either operation after insertion can make the entry effectively unreachable or create surprising behavior. I use immutable value fields for hashable keys, or make mutable domain objects unhashable.”

---

## FU-032 — Hash randomization and production security

**Question (EN):** How does hash randomization help protect Python services, and why should hash() not be used as a persistent identifier?

**Answer**

Python salts the hashes of str and bytes with a process-specific unpredictable value by default. This makes precomputed collision attacks less practical and helps mitigate denial-of-service risks from adversarial dictionary keys. The resulting hash values can differ between process runs, so hash() is unsuitable for persistent IDs, database keys, cache keys shared across processes, or serialized identifiers. Use a stable, explicitly defined identifier or digest for those purposes.

**Interview-Ready Answer (EN)**

“Hash randomization makes collision attacks based on predictable string and bytes hashes harder. It is a mitigation, not a substitute for input limits and service-level protection. Since hashes are not stable across process runs, I never persist Python hash() results or use them as cross-process identifiers.”

---

# PY-009 — Main Question

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

## FU-033 — Reference counting versus cyclic garbage collection

**Question (EN):** What is the difference between reference counting and cyclic garbage collection in CPython?

**What the interviewer evaluates:** Understanding of object lifetime, unreachable cycles, and the complementary roles of the two mechanisms.

**Answer**

Reference counting tracks strong references to an object. In CPython, when the count reaches zero, the object can normally be deallocated immediately. It is effective for ordinary acyclic object graphs, but it cannot reclaim a cycle whose members keep references to one another.

The cyclic garbage collector supplements reference counting. It examines supported container objects and identifies cycles that are unreachable from the program's roots. It can then reclaim those structures. The collector is not a replacement for reference counting; the two mechanisms solve different parts of the object-lifetime problem.

**Interview-Ready Answer (EN)**

“Reference counting handles the common case: when an object's last strong reference disappears, CPython can reclaim it. Cyclic GC handles a case reference counting cannot solve by itself—unreachable groups of objects that reference each other. CPython combines both mechanisms.”

---

## FU-034 — Reference cycles and reachability

**Question (EN):** Why can a reference cycle remain in memory even when the application no longer uses any of its objects?

**What the interviewer evaluates:** Ability to distinguish local reference counts from global reachability.

**Answer**

Consider two container objects that refer to each other. Even after the application drops every external reference to them, each object still has an incoming reference from the other. Their reference counts therefore remain non-zero, although the group is unreachable from the rest of the program.

CPython's cyclic collector detects supported unreachable cycles by examining tracked containers and their references. A cycle is not automatically a leak: if it remains reachable, it is still live by design. The important distinction is whether the object graph can be reached from program roots, not merely whether objects refer to one another.

**Interview-Ready Answer (EN)**

“A cycle can keep its members' reference counts above zero even after all external references disappear. Reference counting cannot reclaim that group on its own. CPython's cyclic collector identifies supported cycles that are unreachable from the program and can reclaim them. A reachable cycle is not garbage—it is still part of the live object graph.”

---

## FU-035 — del, finalizers, and deterministic cleanup

**Question (EN):** Does using del or defining __del__() guarantee that an object or its resources are released immediately?

**What the interviewer evaluates:** Understanding name binding, finalization semantics, and reliable resource management.

**Answer**

The del statement removes a name binding or an item reference; it does not directly command the runtime to destroy the object. The object may remain alive if other references exist. In CPython, releasing the final strong reference often triggers deallocation promptly, but this timing is not a portable Python language guarantee.

A __del__() finalizer is not a reliable resource-management mechanism. Its execution timing can be uncertain, finalization can be complicated by cycles or object resurrection, and interpreter shutdown introduces additional constraints. Use context managers (with) or try/finally to close files, sockets, and database connections deterministically.

**Interview-Ready Answer (EN)**

“del removes a reference; it does not guarantee object destruction. The object may still be referenced elsewhere, and prompt deallocation after the last reference is a CPython behavior rather than a portable timing guarantee. I use context managers or try/finally for deterministic resource cleanup and do not rely on __del__() for closing critical resources.”

---

## FU-036 — Diagnosing memory growth in production

**Question (EN):** How would you investigate steadily increasing memory usage in a long-running Python service?

**What the interviewer evaluates:** Production debugging, measurement discipline, and the ability to distinguish Python heap retention from process and native memory.

**Answer**

First, clarify what is growing: process RSS, traced Python allocations, the number of live objects, or memory allocated by native extensions. Reproduce the workload and compare measurements over time rather than assuming every RSS increase is a Python object leak.

Use tracemalloc snapshots to identify Python allocation sites and compare retained allocations. Use gc statistics and carefully scoped object/referrer inspection to investigate cycles and retaining references. Correlate these findings with process-level metrics and, when necessary, native-memory profiling because C extensions and external libraries may allocate outside the Python object heap.

Also inspect caches, unbounded queues, global registries, task references, closures, and long-lived request state. Do not respond by blindly calling gc.collect() or disabling GC: first establish the cause and measure the effect of any change.

**Interview-Ready Answer (EN)**

“I start by distinguishing live Python allocations, process RSS, and native memory. I compare tracemalloc snapshots under a repeatable workload, inspect object retention and GC statistics, and correlate that with process metrics. I also check common retention sources such as unbounded caches, queues, background tasks, and global registries. I only tune or force garbage collection after identifying a specific GC-related cause and measuring the impact.”

