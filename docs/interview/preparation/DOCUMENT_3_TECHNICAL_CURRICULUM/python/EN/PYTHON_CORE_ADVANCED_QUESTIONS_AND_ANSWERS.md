# Python Core & Advanced Python — Questions and Answers (EN)

**Language:** English  
**Domain:** Python Core & Advanced Python  
**Python baseline:** 3.15.2. Version-specific behavior is labelled; language guarantees are distinguished from CPython implementation details.  
**Question map:** [English Question Map](./PYTHON_CORE_ADVANCED.md)  
**Navigation:** [Python curriculum index](../README.md)

English study material for PY-001–PY-004 and FU-001–FU-016. Each topic explains the concept and provides an interview-ready answer. The Russian version uses the same question IDs.

**Review status:** Authored; independent technical and editorial review pending. Do not treat this material as finally approved until both reviews are complete.

# PY-001 — Main Question

**Question (EN):** What is the Global Interpreter Lock (GIL) in CPython, and how does it affect concurrency and parallelism?

**What the interviewer evaluates**

- Understanding of the GIL's role in traditional CPython builds.
- Ability to distinguish concurrency, parallelism, and thread safety.
- Practical choice of threads, processes, and asynchronous I/O.
- Awareness of free-threaded CPython and its compatibility trade-offs.

**Short Answer**

The Global Interpreter Lock is a synchronization mechanism used by the conventional CPython build. It ensures that, at a given moment, only one thread executes Python bytecode while holding the GIL. This simplifies coordination around interpreter state and object management, but it limits CPU-bound pure-Python threads from executing Python code in parallel across multiple cores. Threads can still provide concurrency, especially for I/O-bound work, and some native extensions release the GIL while performing work outside the Python runtime.

The GIL is a CPython implementation detail, not a guarantee of the Python language. Since Python 3.13, CPython has also provided an optional free-threaded build; it became an officially supported, still-optional build configuration in Python 3.14. It is not the default, and extension compatibility and workload performance must be evaluated.

**Explanation**

The GIL is a process-wide lock in a conventional CPython interpreter. A thread generally needs to hold it to execute Python bytecode and interact with interpreter-managed objects through the usual C API. The lock coordinates access to interpreter state and historically made memory management, especially reference counting, and C-extension integration simpler.

The GIL does not mean that a Python process can have only one thread, nor does it prevent threads from overlapping their work. The operating system schedules threads, and CPython switches which thread holds the GIL. Blocking I/O commonly releases the GIL, allowing another thread to run. Native extensions can also release it around suitable CPU-intensive native operations. Therefore, multiple threads can make progress concurrently, even though conventional CPython does not execute multiple threads' Python bytecode in parallel while the GIL is held.

**Concurrency is not the same as parallelism.** Concurrency means multiple tasks make progress during overlapping periods; parallelism means work is executed at the same time, for example on separate CPU cores. With the conventional GIL-enabled CPython build, threads are useful for overlapping I/O, but pure-Python CPU-bound threads generally do not scale across cores through simultaneous bytecode execution.

**Thread safety is a separate concern.** The GIL does not make application-level operations or multi-step invariants automatically safe. A thread switch can occur between operations, and native code may run without the GIL. Shared mutable state still requires appropriate synchronization, such as locks, queues, or ownership-based designs. Do not rely on incidental atomicity of individual operations as a substitute for an explicit concurrency contract.

**How to choose a concurrency model**

- **Threading:** useful when tasks spend substantial time waiting for network, disk, or other blocking I/O, or when native libraries release the GIL. Use synchronization for shared state.
- **Multiprocessing:** useful for CPU-bound Python work when process isolation and parallel execution justify the extra memory, serialization, startup, and coordination costs.
- **Asyncio:** useful for large numbers of I/O-bound tasks when the libraries support non-blocking operations. It provides cooperative concurrency, not CPU parallelism by itself.
- **Native code:** numerical, compression, cryptographic, and other libraries may perform work outside the interpreter and may release the GIL. Measure the actual library and workload.

**Free-threaded CPython**

PEP 703 introduced an optional CPython build configuration in which the GIL can be disabled. Free-threaded builds were introduced experimentally in Python 3.13 and became officially supported as an optional configuration in Python 3.14. They are not the default interpreter build. In Python 3.15, the official macOS installer installs a separate free-threaded build by default; the conventional GIL-enabled build remains available. Removing the GIL requires additional interpreter-level synchronization and changes to memory-management and extension APIs. Some C extensions are not ready for free-threading and may cause the GIL to be enabled. A free-threaded build can improve CPU parallelism for suitable workloads, but it does not guarantee a speedup: single-thread performance, memory use, extension compatibility, contention, and application-level data races must be considered.

**Practical Example**

A web service that makes many independent HTTP requests may benefit from threads because each worker often waits for network I/O. A CPU-heavy pure-Python image transformation is unlikely to become faster merely by adding threads under the conventional GIL-enabled build; a process pool or an optimized native implementation may be more appropriate.

**Senior-Level Perspective**

Do not answer “Python is single-threaded.” Explain which interpreter build is in use, what work is performed while the GIL is held, and whether native code releases it. Choose a concurrency model from measured workload characteristics, not from a blanket rule. For free-threaded deployment, verify the exact interpreter build, dependencies and C-extension support, then benchmark representative workloads and audit shared mutable state for races.

**Interview-Ready Answer (EN)**

“The GIL, or Global Interpreter Lock, is a synchronization mechanism in the conventional CPython build. It allows only one thread at a time to execute Python bytecode while holding the lock. This simplifies coordination around interpreter state and object management, but it limits parallel execution of CPU-bound pure-Python threads across multiple cores.

It does not prevent concurrency. Threads can overlap I/O because blocking operations commonly release the GIL, and native extensions may release it while doing work outside the interpreter. For CPU-bound Python code, multiprocessing is often a better fit; for high-volume I/O, threading or asyncio may be appropriate depending on the libraries and architecture.

The GIL also does not make shared application state automatically thread-safe, so synchronization is still necessary. Finally, free-threaded CPython is available as an optional build: it was introduced experimentally in 3.13 and became officially supported, but remains optional, in 3.14. I would validate dependency compatibility and benchmark the real workload before adopting it.”

**References**

- [Python 3.15.2 documentation: Global Interpreter Lock FAQ](https://docs.python.org/3.15/faq/library.html#can-t-we-get-rid-of-the-global-interpreter-lock)
- [Python 3.15.2 documentation: Support for free threading](https://docs.python.org/3.15/howto/free-threading-python.html)
- [Python 3.15.2 documentation: C API extension support for free threading](https://docs.python.org/3.15/howto/free-threading-extensions.html)
- [What's New in Python 3.15: Stable ABI for free-threaded builds (`abi3t`)](https://docs.python.org/3.15/whatsnew/3.15.html#pep-803-stable-abi-for-free-threaded-builds)
- [Python 3.15.2 C API: Thread states and the GIL](https://docs.python.org/3.15/c-api/threads.html)
- [PEP 703 — Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)

---

## FU-001 — Purpose and scope of the GIL

**Question (EN):** Why does the conventional CPython build use the GIL, and what does the lock actually protect?

**What the interviewer evaluates:** Understanding of interpreter-state coordination, reference counting, and the limits of the GIL's guarantees.

**Short Answer**

The GIL provides a central synchronization mechanism for parts of CPython's runtime and object-management machinery. Historically, it simplified safe access to interpreter state and reference-counted objects, and reduced the need for fine-grained locking throughout the runtime and many C extensions. It is not a universal application lock and does not protect arbitrary external resources or multi-step business invariants.

**Detailed Answer**

CPython manages Python objects and runtime state internally. In the conventional build, the GIL ensures that only one thread at a time executes Python bytecode while holding the lock. This makes many internal operations easier to coordinate, including updates to reference counts and access to interpreter data structures.

The historical design trade-off was implementation simplicity and lower synchronization overhead in a single-threaded execution model, at the cost of limiting parallel execution of Python bytecode across threads. The GIL is not part of Python's language specification, and other Python implementations may use different execution and synchronization models.

The lock's protection must not be generalized to all state. It does not automatically serialize a sequence of application operations, make a check-then-act sequence safe, protect a database transaction, or guarantee the thread safety of a third-party native library. Extensions that release the GIL must provide their own synchronization for native shared state.

**Senior-Level Judgment**

Describe the GIL as a runtime synchronization mechanism with a specific scope. Avoid saying that it makes Python thread-safe or that it locks every operation in an application. When investigating a race, identify the shared state and the synchronization boundary rather than assuming the GIL is sufficient.

**Interview-Ready Answer (EN)**

“The GIL is a CPython runtime lock that coordinates execution of Python bytecode and access to interpreter-managed state in the conventional build. It historically simplified reference counting, object management, and C-extension integration by avoiding fine-grained locking across much of the runtime. However, its scope is limited: it does not protect arbitrary application invariants, external resources, or native code that runs after releasing the lock. I treat thread safety as an explicit property of the data structure and operation, not as something guaranteed by the GIL.”

---

## FU-002 — GIL, threads, and workload type

**Question (EN):** How does the GIL affect CPU-bound and I/O-bound multithreaded workloads in conventional CPython?

**What the interviewer evaluates:** Ability to reason about scheduling, blocking I/O, CPU utilization, and actual workload behavior.

**Short Answer**

For CPU-bound pure-Python work, threads generally cannot execute Python bytecode in parallel across cores while sharing a conventional GIL-enabled CPython interpreter. For I/O-bound work, threads can overlap waiting because blocking operations commonly release the GIL, allowing another thread to run. The benefit depends on the workload, libraries, contention, and coordination overhead.

**Detailed Answer**

When a thread holds the GIL and executes Python bytecode, another thread in the same interpreter must wait to acquire it before executing Python bytecode. CPython periodically gives other threads an opportunity to run, so threads can interleave rather than execute Python bytecode simultaneously.

Blocking operations such as socket or file I/O commonly release the GIL while waiting. Other threads can then execute Python code. Some native libraries also release the GIL around long-running native computations. Therefore, the effect cannot be determined from the label “CPU-bound” or “I/O-bound” alone: inspect where the time is spent and whether the relevant native code releases the lock.

**Common Mistakes**

- Saying that threads are useless in Python.
- Assuming the GIL prevents all parallel work, including native code that releases it.
- Assuming I/O-bound automatically means threads are the best choice; asynchronous I/O may be more suitable.
- Treating the GIL as a guarantee that compound operations are race-free.

**Interview-Ready Answer (EN)**

“In conventional CPython, CPU-bound pure-Python threads contend for the GIL, so they generally do not execute Python bytecode in parallel across cores. They may add scheduling and synchronization overhead without improving throughput. I/O-bound threads can still be effective because blocking I/O commonly releases the GIL, allowing other threads to run while one waits. Native extensions may also release the GIL during computation. I choose based on profiling and the behavior of the libraries involved, not simply on whether the task is described as CPU-bound or I/O-bound.”

---

## FU-003 — Choosing threads, processes, or asyncio

**Question (EN):** How would you choose between threading, multiprocessing, and asyncio for a Python backend workload?

**What the interviewer evaluates:** Concurrency-model selection, operational trade-offs, and understanding that asyncio does not remove the GIL.

**Short Answer**

Use threading when blocking I/O or GIL-releasing native operations make threads effective; multiprocessing when CPU-bound Python work needs parallel execution and process overhead is acceptable; and asyncio when many I/O-bound tasks can use non-blocking libraries. Asyncio provides cooperative concurrency, not CPU parallelism by itself.

**Detailed Answer**

The decision starts with the workload and its dependencies:

- **Threading** shares one process's memory and is often straightforward for blocking I/O. Shared mutable state needs explicit synchronization. Under the conventional GIL, pure-Python CPU work does not gain multi-core bytecode parallelism.
- **Multiprocessing** uses separate processes, each with its own interpreter and GIL in the conventional configuration. This enables CPU parallelism but introduces process startup, memory use, data transfer, serialization, failure handling, and coordination costs.
- **Asyncio** runs cooperative tasks on an event loop. It scales well for many concurrent I/O operations when code uses non-blocking APIs and avoids blocking the event-loop thread. CPU-heavy synchronous work can stall the loop and should be offloaded appropriately.

A backend may combine these models, but complexity should be justified by measured throughput, latency, resource use, and operational requirements.

**Senior-Level Judgment**

Choose the simplest model that satisfies throughput and latency objectives. Account for cancellation, backpressure, bounded queues, failure isolation, resource limits, and observability—not only raw execution speed.

**Interview-Ready Answer (EN)**

“I first profile the workload and inspect whether it spends time waiting for I/O or executing CPU-heavy Python code. I use threads for blocking I/O or libraries that release the GIL, multiprocessing for CPU-bound Python work when process overhead is justified, and asyncio for high-concurrency I/O when the full call path supports non-blocking operations. Asyncio does not make CPU work parallel. In production, I also consider cancellation, backpressure, memory use, failure isolation, and operational complexity.”

---

## FU-004 — Free-threaded CPython and migration trade-offs

**Question (EN):** What changes in free-threaded CPython, and what should an engineering team verify before adopting it?

**What the interviewer evaluates:** Current Python runtime knowledge, compatibility assessment, performance validation, and race-condition analysis.

**Short Answer**

Free-threaded CPython provides an optional build that can execute Python threads in parallel without the traditional GIL. It was introduced experimentally in Python 3.13 and became officially supported as an optional build configuration in Python 3.14. It is not the default. Teams must verify C-extension compatibility, runtime configuration, synchronization correctness, and real workload performance.

**Detailed Answer**

PEP 703 describes the changes needed to make the GIL optional in CPython. Free-threaded builds use additional synchronization and memory-management techniques so that multiple threads can safely access interpreter-managed objects without relying on one global lock.

The feature does not mean that existing multithreaded applications automatically become faster or race-free. Code that relied on the GIL for accidental serialization may expose data races. C extensions must explicitly support free-threaded execution; an incompatible extension can cause the GIL to be enabled at runtime. The free-threaded build may also have different single-thread performance and memory characteristics. In the documented pyperformance results, its single-threaded overhead varies by platform (approximately 1% to 8%); memory use is typically higher. Built-in containers such as dict, list, and set use internal locks for some concurrent operations, but application code should still use explicit synchronization for shared invariants rather than rely on those implementation details.

A practical adoption process includes:

1. Confirm the build configuration with `sysconfig.get_config_var("Py_GIL_DISABLED")` and check the runtime state with `sys._is_gil_enabled()`; `python -VV` also identifies a free-threading build.
2. Check whether `PYTHON_GIL` or `-X gil` enables the GIL, and whether importing an unsupported C extension automatically re-enables it.
3. Audit dependencies, especially C extensions, wheels, and native libraries. For C extensions, verify explicit free-threading support; Python 3.15 also introduces the `abi3t` Stable ABI, although adopting it can require C API and module-initialization changes.
4. Test shared mutable state, compound operations, caches, registries, and extension boundaries.
5. Run correctness and stress tests under realistic concurrency.
6. Benchmark representative production workloads, including single-thread and multi-thread cases.
7. Roll out gradually with observability and a rollback path.

**Senior-Level Judgment**

Treat free-threading as a deployment and compatibility decision, not a switch that guarantees performance. Measure the target workload and verify the whole dependency graph. Keep explicit synchronization around shared invariants even when the GIL is disabled.

**Interview-Ready Answer (EN)**

“Free-threaded CPython is an optional build that allows Python threads to execute in parallel without the traditional GIL. It was introduced experimentally in Python 3.13 and became officially supported, while remaining optional, in Python 3.14. The interpreter needs additional synchronization and memory-management mechanisms, and C extensions must explicitly support the free-threaded model; otherwise, an extension may cause the GIL to be enabled.

Before adopting it, I would verify the build and runtime state: `sysconfig.get_config_var("Py_GIL_DISABLED")` indicates whether the build supports free-threading, while `sys._is_gil_enabled()` tells me whether the GIL is currently enabled. I would also check `PYTHON_GIL` / `-X gil`, audit C-extension compatibility, and account for the possibility that an unsupported extension re-enables the GIL. Python 3.15 adds the `abi3t` Stable ABI for compatible extensions, but migration may require C API and module-initialization changes. Finally, I would audit shared state, stress-test concurrency, and benchmark representative workloads rather than assume a universal speedup.”

---
---

# PY-002 — Main Question

**Question (EN):** How does Python execute a program from source code to runtime behavior?


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

## FU-005 — Execution stages in CPython

**Question (EN):** What are the main stages between Python source code and the execution of its instructions in CPython?


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

## FU-006 — Script execution versus module import

**Question (EN):** How would you investigate a case where a Python module behaves differently when run as a script versus imported by another module?


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

## FU-007 — Language guarantees versus implementation details

**Question (EN):** Which aspects of bytecode and interpreter behavior are implementation details rather than language guarantees, and why does that distinction matter?


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

## FU-008 — Choosing the diagnostic layer in production

**Question (EN):** When diagnosing a production issue, how would you decide whether to inspect Python-level behavior, CPython internals, or the operating-system/runtime environment?


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

## PY-002 answer review checklist

- [x] Main question has an English answer and Russian explanation.
- [x] Short and detailed answers are present.
- [x] Internal mechanics are explained.
- [x] Practical examples and a relevant code example are included.
- [x] Best practices, trade-offs, common mistakes, and senior-level judgment are covered.
- [x] Interview-ready English answer is included.
- [x] FU-005–FU-008 each have substantive answers.
- [x] CPython-specific behavior is distinguished from language guarantees.
- [ ] Independent technical review against the target Python/CPython version.
- [ ] Final editorial review and mastery assessment.

**Completion rule:** This record is authored, but not finally approved, until the technical and editorial review items above are completed.

## Answer Development — PY-003

**Status:** Initial complete answer set authored; technical and editorial review remain pending.  
**Scope:** PY-003 and FU-009–FU-012. CPython call mechanics are described conceptually; internal structures and optimizations are version-dependent.

---



---

# PY-003 — Main Question

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

## FU-009 — Execution state during a function call

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

## FU-010 — Profiling function-call overhead

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

## FU-011 — Different execution lifecycles

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

## FU-012 — When call mechanics matter for optimization

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



## PY-003 review checklist

- [x] Main question and FU-009–FU-012 included.
- [x] Argument binding, execution state, frames, closures, return and exception paths covered.
- [x] Ordinary functions distinguished from generators and coroutines.
- [x] Profiling methodology and optimization trade-offs covered.
- [ ] Independent technical review against supported CPython versions.
- [ ] Final editorial review.

**Completion rule:** Authored material is not finally approved until both review stages are complete.



---

# PY-004 — Main Question

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

## FU-013 — Identity, type, and value over an object's lifetime

**Question (EN):** Which of an object's identity, type, and value can change during its lifetime?

**Explanation:** Identity and type remain stable throughout an object's lifetime. Its value may change if it is mutable. Mutation changes the existing object; rebinding changes which object a name refers to. Immutability is not necessarily deep: a tuple can contain a mutable list whose contents still change.

**Interview-Ready Answer (EN)**

“An object's identity and type remain constant during its lifetime, while its value may change if it is mutable. Mutation changes the state of the existing object; rebinding changes the object referenced by a name. These are different operations. An immutable container also does not guarantee that every object reachable through it is immutable.”

---

## FU-014 — Choosing identity, equality, and type checks

**Question (EN):** How would you choose between identity checks, equality checks, and type checks in a code review?

**Explanation:** Start with the contract being tested. Use is for object identity and singleton sentinels, == for value equality, and isinstance() when subclasses are accepted. An exact check such as type(value) is int deliberately rejects subclasses and should be used only when that restriction is part of the contract. Review custom __eq__ and __hash__ together when objects are dictionary keys or set members.

**Interview-Ready Answer (EN)**

“I first identify whether the code needs identity, value equality, or type compatibility. I use is for None and explicit sentinels, == for values, and isinstance() when subclasses should be accepted. Exact type checks are appropriate only for a deliberate strict contract. I also review custom equality and hashing because inconsistent implementations can break dictionary and set behavior.”

---

## FU-015 — Why is is not a value comparison?

**Question (EN):** Why can using is to compare strings, numbers, or other values produce unreliable results?

**Explanation:** is tests whether references designate the same object; it does not compare values. Equal values can belong to distinct objects. CPython may reuse or intern some immutable objects, making an incorrect identity comparison appear to work in one context. Such reuse is an implementation optimization, not a language guarantee.

**Interview-Ready Answer (EN)**

“is checks object identity, whereas == checks equality according to the type's comparison semantics. Two separately created values can be equal without being the same object. Interning or constant reuse may make identity comparisons appear to work for some strings or integers, but that behavior is implementation-dependent. I use is for sentinels and == for value comparisons.”

---

## FU-016 — Identity and mutability in API design

**Question (EN):** How should API design avoid accidental dependencies on object identity, mutability, or concrete implementation types?

**Explanation:** Define whether an API mutates, retains, copies, or returns caller-owned objects. Use stable domain IDs when identity must survive database reloads or process boundaries. Prefer immutable value objects for value-based concepts, while accounting for nested mutability and hash stability. Expose required behavior through protocols or abstractions instead of requiring a concrete class without a clear reason. Validate and normalize external data at system boundaries.

**Interview-Ready Answer (EN)**

“I make ownership and mutation semantics explicit: callers should know whether an API changes an input, retains a reference, or returns shared state. I use stable domain identifiers rather than Python object identity across persistence and distributed boundaries. Immutable value objects are useful when equality is value-based, provided nested state and hashing are handled correctly. I expose required behavior through suitable abstractions or protocols so callers are not coupled to an unnecessary concrete implementation.”

**Status:** Authored; independent technical and editorial review pending.
