# Python Core & Advanced Python — Questions and Answers (EN)

**Language:** English  
**Domain:** Python Core & Advanced Python  
**Question map:** [English Question Map](./PYTHON_CORE_ADVANCED.md)  
**Navigation:** [Python curriculum index](../README.md)

This is the English-language authoring version for international technical interviews. It contains the complete authored answer for PY-001 and FU-001–FU-004, including explanations, examples, trade-offs, and Interview-Ready Answers. The Russian version is maintained separately and linked from the Python curriculum index.

**Review status:** Authored; independent technical and editorial review pending. Do not treat this material as finally approved until both reviews are complete.

---

# PY-001 — Main Question

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

## FU-001 — Execution stages in CPython

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

## FU-002 — Script execution versus module import

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

## FU-003 — Language guarantees versus implementation details

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

## FU-004 — Choosing the diagnostic layer in production

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

