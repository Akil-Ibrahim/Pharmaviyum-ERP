# Python Core & Advanced Python — Questions and Answers

**Domain:** Python Core & Advanced Python  
**Question map and competency allocation:** [PYTHON_CORE_ADVANCED.md](./PYTHON_CORE_ADVANCED.md)  
**Standard:** [Document 1](../../DOCUMENT_1_INTERVIEW_STANDARD.md) · [Architecture](../../DOCUMENT_2_CURRICULUM_ARCHITECTURE.md)

This file contains detailed Main Question and Follow-up answers, including explanations, examples, trade-offs, and bilingual Interview-Ready Answers. The question wording and complete follow-up map are maintained in the linked question-map file. Authored material remains pending independent technical and editorial review until those checks are completed.

В этом файле собраны подробные ответы на основные вопросы (Main Questions) и дополнительные вопросы (Follow-ups), включая объяснения, примеры, компромиссы и готовые для технического собеседования ответы на английском и русском языках. Формулировки вопросов и полная карта дополнительных вопросов находятся в связанном файле Question Map. Подготовленные материалы остаются в статусе авторской версии до завершения независимой технической и редакторской проверки.

---

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


### FU-011 — Why identity is not value equality

**Parent Main Question:** PY-003 — Explain Python's object model: identity, type, and value.

**Question (EN):** Why can relying on object identity or the is operator for value comparisons produce incorrect or implementation-dependent results?

**Перевод (RU):** Почему использование идентичности объекта или оператора is для сравнения значений может приводить к ошибкам или зависеть от реализации?

**What the interviewer evaluates**

- Understanding of identity versus equality.
- Knowledge of object lifetime and the semantics of `is` and `==`.
- Awareness of CPython optimizations such as interning and constant folding without treating them as language guarantees.
- Ability to identify brittle tests and production defects caused by accidental object reuse.
- Correct reasoning about sentinels, caching, and stable identifiers.

**Short Answer**

The `is` operator checks whether two references designate the same object; it does not check whether their values are equal. Two separately created objects may have equal values but different identities. Conversely, an implementation may reuse or intern certain immutable objects, causing two expressions to refer to the same object in some circumstances. Such reuse is not a valid basis for value comparison and may vary with implementation, execution context, or version.

Use `==` for value equality and reserve `is` for identity-sensitive cases, especially singleton sentinels such as `None`.

**Detailed Answer**

**1. Identity and equality answer different questions**

The expression `a is b` asks whether both references point to the same object. The expression `a == b` asks whether the objects compare equal according to their equality semantics, typically involving `__eq__`.

~~~python
left = [1, 2]
right = [1, 2]

print(left == right)  # True: equal contents
print(left is right)  # False: distinct list objects
~~~

If application logic uses `is` where value equality is intended, it can reject values that are semantically equivalent.

**2. Object reuse can make incorrect code appear to work**

CPython may reuse certain immutable objects through implementation optimizations such as interning or constant reuse. The exact behavior depends on the implementation and context; it is not a language-level promise that equal values will share identity.

~~~python
a = 256
b = 256
print(a is b)  # May be True in a particular implementation/context.

x = int("1000")
y = int("1000")
print(x == y)  # True
print(x is y)  # Identity is not a value-comparison contract.
~~~

The first result must not be used to justify identity comparisons for integers. Code that appears correct in a small interactive test may behave differently when values are constructed dynamically, compiled in another context, or executed by another Python implementation.

**3. Strings and interning**

Some strings may be interned, allowing identical immutable string objects to be shared. Interning is an optimization and should not be relied upon for general string comparison.

~~~python
first = "status"
second = "".join(["sta", "tus"])

print(first == second)  # True
print(first is second)  # Do not rely on this result.
~~~

Even if identity happens to be shared in one environment, the application contract concerns string content, so `==` is the correct operator.

**4. Why the distinction matters in production**

An identity comparison can create defects that are difficult to reproduce:

- Tests pass because constants or objects happen to be reused.
- A production path constructs values dynamically and produces distinct objects.
- A different Python implementation or version changes an optimization.
- Serialization, deserialization, IPC, or database loading reconstructs an equivalent but distinct object.
- Caching or object pooling changes allocation and reuse patterns.

Identity is process-local and lifetime-scoped. It should not be used as a durable key for business entities or distributed messages.

**5. Correct use of identity**

Identity checks are appropriate when the contract explicitly concerns a unique object, for example:

~~~python
if result is None:
    handle_absence()

MISSING = object()

if value is MISSING:
    use_default()
~~~

Here the comparison is not asking whether two values are equivalent; it is checking whether the exact sentinel object was supplied.

**Best Practices**

- Use `==` for numeric, string, collection, and domain-value comparisons.
- Use `is None` for the `None` singleton.
- Use identity checks for explicit sentinel objects and deliberate aliasing checks.
- Never depend on integer or string interning for correctness.
- Do not infer identity guarantees from a single REPL experiment.
- Test behavior using dynamically constructed values and supported Python implementations where portability matters.
- Use stable domain identifiers for persistence and distributed communication.

**Trade-offs & Edge Cases**

- Identity checks are generally simple and direct, but only answer whether references designate the same object.
- Equality can express domain semantics, but custom `__eq__` implementations may be expensive, unusual, or return non-boolean results.
- Interning and constant reuse can reduce memory use or comparison work, but are implementation optimizations, not application contracts.
- A singleton sentinel is intentionally identity-based; an ordinary string or integer value is not.
- Object identity may be useful when tracking aliasing within one process and object lifetime, but not across process restarts or serialization boundaries.

**Common Mistakes**

- Using `is` to compare integers or strings.
- Assuming equal immutable values must have the same identity.
- Assuming an observed CPython optimization is guaranteed by the Python language.
- Treating `id()` as a persistent unique identifier.
- Using object identity to compare values loaded from separate database queries or deserialized messages.
- Replacing `==` with `is` as a supposed micro-optimization without a valid identity requirement.

**Senior-Level Perspective**

A senior engineer separates semantic correctness from runtime optimization. Whether two values are equivalent is a domain or data-model question; whether two references designate one object is a runtime identity question. Conflating them makes code fragile because it turns an incidental allocation decision into an application-level requirement.

In code review, I would search for identity comparisons involving literals, numbers, strings, enums, and domain objects, then verify the intended contract. I would retain identity comparisons for sentinels and deliberate alias checks. If performance is a concern, I would benchmark the actual workload rather than rely on object interning or assumed pointer comparisons.

**Interview-Ready Answer (EN)**

“Using `is` for value comparison is incorrect because it checks object identity, not equality. Two independently created objects can represent equal values while having different identities. For example, two lists with the same elements compare equal with `==`, but they are not the same object.

The opposite situation can also occur: CPython may reuse or intern some immutable objects, so two expressions can sometimes refer to the same object. However, these are implementation optimizations, not guarantees that application code should depend on. Their behavior can vary by Python implementation, version, and execution context.

I use `==` for value comparisons and reserve `is` for identity-sensitive cases such as checking `None`, private sentinels, or intentional aliasing. I also avoid using object identity as a persistent or distributed identifier.”

**Interview-Ready Answer (RU)**

«Использовать `is` для сравнения значений неправильно, потому что этот оператор проверяет идентичность объектов, а не их равенство. Два независимо созданных объекта могут представлять одинаковые значения, но иметь разную идентичность. Например, два списка с одинаковыми элементами равны при сравнении через `==`, но не являются одним и тем же объектом.

Возможна и обратная ситуация: CPython может повторно использовать или интернировать некоторые неизменяемые объекты, поэтому в определённых случаях два выражения могут ссылаться на один объект. Однако это оптимизации реализации, а не гарантии, на которых должно основываться прикладное программное обеспечение. Такое поведение может различаться между реализациями Python, версиями и контекстами выполнения.

Для сравнения значений я использую `==`, а `is` оставляю для случаев, когда важна идентичность: например, при проверке `None`, специальных sentinel-объектов или намеренного совместного использования одной ссылки. Также я не использую идентичность объекта в качестве постоянного или распределённого идентификатора.»

**Status:** Authored; independent technical and editorial review pending.

---

### FU-012 — Designing APIs and domain models around identity, mutability, and types

**Parent Main Question:** PY-003 — Explain Python's object model: identity, type, and value.

**Question (EN):** How should API and domain-model design avoid exposing accidental assumptions about object identity, mutability, or concrete implementation types?

**Перевод (RU):** Как при проектировании API и доменных моделей избежать случайных зависимостей от идентичности объектов, их изменяемости и конкретных типов реализации?

**What the interviewer evaluates**

- Distinguishing Python object identity from domain identity.
- Understanding ownership, aliasing, mutability, and API contracts.
- Appropriate use of stable identifiers and value objects.
- Awareness of polymorphism, protocols, abstraction boundaries, and substitutability.
- Senior-level judgment about persistence, concurrency, serialization, and distributed boundaries.

**Short Answer**

APIs should expose semantic contracts rather than incidental implementation details. Domain entities should be identified by stable domain identifiers, not by Python object identity or id(). APIs should make ownership and mutation behavior explicit: whether inputs are read, retained, mutated, copied, or returned as shared references. Immutable value objects and behavior-oriented interfaces can reduce accidental coupling. Type checks should enforce meaningful boundary contracts, while protocols and polymorphism should be preferred when callers need behavior rather than a specific concrete class.

**Detailed Answer**

1. **Separate object identity from domain identity.** Python object identity answers whether two references designate the same in-memory object. Domain identity answers whether two representations refer to the same logical entity. Two ORM instances loaded in separate sessions may represent the same database row while being distinct Python objects. Use stable identifiers such as customer_id or order_id when identity must survive database reloads, serialization, process restarts, or network communication. Do not use is, id(), or memory-address assumptions as persistence or distributed identity contracts.

2. **Define ownership and mutation semantics.** An API accepting a mutable object should make clear whether it reads the object without modifying it, mutates it in place, retains a reference, creates a shallow or deep copy, or transfers ownership under an explicit convention. Aliases observe mutations to the same object. Undocumented in-place changes can therefore create action-at-a-distance bugs, especially when collections are shared between components, tasks, or requests. Prefer narrow mutation boundaries. Defensive copying can protect boundaries, but it has allocation costs and may be invalid for resource-owning objects such as sessions, locks, or open handles.

3. **Use immutable value objects when their semantics fit.** Value objects are compared by the data they represent rather than by a unique lifecycle identity. Examples include a money amount with currency or a date range. Immutability makes such values easier to share, cache, compare, and reason about. However, a frozen outer object does not automatically make nested mutable members immutable. Equality and hashing must also be consistent: equal hashable objects must have compatible hash values, and fields participating in a hash must not change in a way that violates hash stability while the object is used as a dictionary key or set member.

4. **Expose behavior through abstractions, not accidental concrete types.** If callers need an object that can be read, stored, iterated, or processed, define the required behavior through an appropriate abstraction: a standard collection interface, an abstract base class, a Protocol, or a domain-specific interface. This allows multiple implementations to satisfy the same contract. Prefer isinstance() at validation boundaries when runtime classification is necessary. Avoid exact type(x) is SomeClass checks unless rejecting subclasses is an explicit requirement. A concrete type is appropriate when it is deliberately part of the public contract.

5. **Validate and normalize at system boundaries.** External inputs arrive as serialized data, primitive values, or third-party objects. Validate their shape and meaning at the boundary, then convert them into application-owned domain representations. This prevents internal business logic from depending unnecessarily on web frameworks, database drivers, ORMs, or external SDKs. It also creates a clear place to enforce invariants and reject invalid states.

6. **Consider concurrency and distributed execution.** Shared mutable objects can introduce race conditions when accessed by multiple threads or tasks. Clarify whether returned objects are shared, request-scoped, immutable, or safe for concurrent use. Across process and network boundaries, Python object identity is not a meaningful application contract. Serialize stable identifiers and explicit data, then reconstruct objects according to domain rules on the receiving side.

**Practical Design Example**

~~~python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str


@dataclass(frozen=True)
class CustomerId:
    value: str


class CustomerReader(Protocol):
    def get_name(self, customer_id: CustomerId) -> str:
        ...


def display_customer(
    reader: CustomerReader,
    customer_id: CustomerId,
) -> str:
    return reader.get_name(customer_id)
~~~

Here, CustomerId expresses domain identity explicitly; Money is a value object; and CustomerReader describes required behavior without coupling callers to one concrete repository. Production code would additionally validate invariants and define currency semantics.

**Best Practices**

- Use stable domain identifiers for entities crossing persistence or process boundaries.
- Treat Python object identity as an in-process concept, not a business key.
- Document whether APIs mutate, retain, copy, or inspect caller-owned objects.
- Prefer immutable value objects for concepts whose semantics are value-based.
- Keep mutable state behind clear ownership boundaries.
- Use protocols, abstract interfaces, or standard abstractions when callers need behavior rather than a specific implementation.
- Validate external data at boundaries and convert it into domain-owned representations.
- Ensure equality and hashing semantics are consistent for hashed objects.
- Define concurrency expectations for shared mutable state.
- Use defensive copying selectively, based on correctness requirements and measured costs.

**Trade-offs & Edge Cases**

- Stable identifiers support persistence and distributed references, but require explicit uniqueness and lifecycle rules.
- Immutable objects simplify reasoning and sharing, but updates require replacement values and may allocate.
- Shallow copies do not isolate nested mutable objects; deep copies may be expensive or invalid for resource-owning objects.
- Protocols improve substitutability, but overly broad interfaces can obscure the actual contract.
- Exact type checks enforce narrow requirements but reject subclasses and alternative implementations.
- ORM identity maps are useful within a unit of work, but should not define domain identity across sessions.
- Equality based on mutable fields can be dangerous when objects are used in hashed collections.
- Thread or task safety cannot be inferred merely from an object's type or an apparently read-only API.

**Common Mistakes**

- Using is or id() as a database or business identifier.
- Assuming two ORM objects representing the same row must be the same Python object.
- Returning an internal mutable collection and allowing callers to mutate it unintentionally.
- Mutating caller-provided arguments without documenting that behavior.
- Assuming a shallow copy isolates nested mutable state.
- Calling an object immutable merely because its outer container is frozen.
- Defining equality using mutable fields while also making the object hashable.
- Requiring an exact concrete class when any implementation satisfying the behavior would work.
- Leaking ORM, framework, or SDK types through domain interfaces without a deliberate reason.
- Assuming an object is safe to share between requests, threads, or tasks without a concurrency contract.

**Senior-Level Perspective**

A senior engineer treats identity, ownership, mutability, and type as architectural contract decisions. The question is not simply whether an implementation works today, but whether callers can use the API correctly without relying on undocumented runtime behavior.

At the domain level, distinguish entities, whose identity is stable across state changes, from value objects, whose meaning is defined by their values. At application boundaries, translate external representations into domain-owned types and expose only the behavior callers require. At persistence boundaries, avoid allowing ORM identity-map behavior to define business identity. At concurrency boundaries, define who may mutate shared state and under what synchronization or isolation guarantees.

These decisions should be proportionate. Immutability, copying, and abstraction are tools, not universal rules. Evaluate correctness, coupling, lifecycle, performance, and operational complexity, then choose the narrowest contract that safely supports the use case.

**Interview-Ready Answer (EN)**

“I design APIs around explicit semantic contracts rather than incidental object implementation details. First, I separate Python object identity from domain identity. Two ORM instances or deserialized objects may represent the same logical entity without being the same Python object, so I use stable domain identifiers when identity must survive persistence or process boundaries.

Second, I make ownership and mutation behavior explicit. Callers should know whether an API mutates an input, retains a reference, returns shared mutable state, or creates a copy. I use immutable value objects where value-based semantics are appropriate, while accounting for nested mutability and equality and hashing requirements.

Third, I expose required behavior through protocols or suitable abstractions instead of coupling callers to concrete implementation classes. I use runtime type checks at boundaries when they enforce a real contract, not as a substitute for polymorphism.

Finally, I consider concurrency and distributed execution: shared mutable state needs clear ownership and synchronization, while serialized communication should carry explicit data and stable identifiers rather than Python object identity. The objective is to make the API predictable, substitutable, and safe across lifecycle and system boundaries without adding unnecessary abstraction or copying costs.”

**Interview-Ready Answer (RU)**

«Я проектирую API на основе явных семантических контрактов, а не случайных особенностей реализации объектов. Прежде всего, я разделяю идентичность Python-объекта и идентичность сущности предметной области. Два экземпляра ORM или два десериализованных объекта могут представлять одну логическую сущность, не являясь одним и тем же Python-объектом. Поэтому, когда идентичность должна сохраняться после обращения к базе данных или между процессами, я использую устойчивые доменные идентификаторы.

Во-вторых, я явно определяю владение данными и поведение при изменении состояния. Вызывающий код должен понимать, изменяет ли API входной объект, сохраняет ли ссылку на него, возвращает ли общее изменяемое состояние или создаёт копию. Неизменяемые объекты-значения я использую там, где семантика действительно основана на значениях, учитывая при этом вложенную изменяемость, а также требования к равенству и хешированию.

В-третьих, я предоставляю необходимое поведение через протоколы или подходящие абстракции, вместо того чтобы связывать вызывающий код с конкретными классами реализации. Проверки типов на границах системы применяю тогда, когда они обеспечивают реальный контракт, а не заменяют полиморфизм.

Наконец, я учитываю конкурентное выполнение и распределённую архитектуру: для общего изменяемого состояния необходимы чёткие правила владения и синхронизации, а при передаче данных между системами следует использовать явные данные и устойчивые идентификаторы, а не идентичность Python-объектов. Цель — сделать API предсказуемым, расширяемым и безопасным на границах жизненного цикла и системы, не добавляя неоправданных абстракций или затрат на копирование».

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

## PY-004 — How do attribute lookup and special methods work in Python?

### FU-013 — Resolving an instance attribute

**Parent Main Question:** PY-004 — How do attribute lookup and special methods work in Python?

**Question (EN):** How does Python resolve an instance attribute, and where do the instance dictionary, class attributes, and descriptors participate?

**Перевод (RU):** Как Python разрешает обращение к атрибуту экземпляра и какую роль в этом процессе играют словарь экземпляра, атрибуты класса и дескрипторы?

**What the interviewer evaluates**

- Understanding the default instance attribute lookup protocol.
- Correctly distinguishing data descriptors, non-data descriptors, instance attributes, and ordinary class attributes.
- Knowing how functions become bound methods through the descriptor protocol.
- Understanding the role of __getattribute__ and __getattr__.
- Recognizing implementation details and avoiding oversimplified lookup rules.

**Short Answer**

For ordinary attribute access such as `obj.name`, Python normally delegates to `type(obj).__getattribute__(obj, "name")`. With the default `object.__getattribute__` behavior, lookup gives precedence to a data descriptor found on the class or its MRO, then checks the instance dictionary, and then considers a non-data descriptor or another class attribute. If normal lookup raises `AttributeError`, `__getattr__`, when defined, can provide a fallback. Descriptors customize attribute access through `__get__`, and data descriptors can additionally define `__set__` or `__delete__`.

**Detailed Answer**

1. **Attribute access begins with `__getattribute__`.** An expression such as `obj.name` invokes the attribute-access machinery. In the ordinary case, Python calls the implementation of `__getattribute__` selected for the object's type. A custom override can change the behavior, so the familiar precedence rules describe the default `object.__getattribute__` implementation rather than every possible user-defined implementation.

2. **Python searches the type and its method resolution order for a class attribute.** The default lookup needs to determine whether the class provides a descriptor named `name`. The class hierarchy is searched according to the type's MRO. Descriptor behavior is determined by special methods on the descriptor's type, not simply by arbitrary attributes stored on the descriptor instance.

3. **Data descriptors have the highest precedence.** A descriptor is a data descriptor when its type provides `__set__` or `__delete__` in addition to the descriptor access protocol. If such a descriptor is found on the class, its `__get__` is invoked before the instance dictionary is consulted. A `property` is a common example; even a read-only property participates as a data descriptor because its descriptor implementation handles assignment and may raise `AttributeError`.

4. **The instance dictionary is checked next.** If no applicable data descriptor takes precedence, Python checks the instance's attribute storage, commonly `obj.__dict__`. An attribute stored there can shadow an ordinary class attribute or a non-data descriptor. Not every instance has a dictionary: classes using `__slots__` may omit it unless a dictionary slot is explicitly provided, and extension types can use other layouts.

5. **Non-data descriptors and ordinary class attributes are considered after the instance dictionary.** A non-data descriptor provides `__get__` but does not define `__set__` or `__delete__` on its type. Functions stored on a class are non-data descriptors. Accessing a function through an instance invokes its descriptor behavior and produces a bound method, associating the instance with the function. If an instance attribute with the same name exists, it can shadow that function for ordinary instance lookup.

6. **`__getattr__` is a fallback, not the first lookup stage.** If `__getattribute__` raises `AttributeError`, the normal attribute access machinery may call `__getattr__(self, name)`, if the class defines it. This is useful for computed attributes, proxies, and dynamic interfaces. It should be implemented carefully to avoid recursion and to preserve meaningful missing-attribute behavior.

7. **Custom `__getattribute__` changes the analysis.** An override intercepts every ordinary attribute access and can delegate to `super().__getattribute__(name)` or `object.__getattribute__(self, name)`. Accessing the same attribute carelessly from inside the override can recursively invoke itself. Debugging should therefore distinguish the default lookup algorithm from custom interception.

**Lookup Precedence Under Default `object.__getattribute__`**

1. Data descriptor found on the class or its MRO.
2. Instance attribute storage, typically `__dict__`.
3. Non-data descriptor or ordinary class attribute.
4. If lookup raises `AttributeError`, `__getattr__` may provide a fallback.

This is a useful operational model for normal instance attribute access. Custom `__getattribute__`, metaclass behavior, and special-method lookup require separate consideration.

**Practical Example**

~~~python
class DataDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return "value from data descriptor"

    def __set__(self, instance, value):
        instance._stored = value


class NonDataDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return "value from non-data descriptor"


class Example:
    data = DataDescriptor()
    non_data = NonDataDescriptor()
    ordinary = "class value"

    def method(self):
        return "bound method"


obj = Example()
obj.__dict__["data"] = "instance value"
obj.__dict__["non_data"] = "instance value"
obj.ordinary = "instance override"

assert obj.data == "value from data descriptor"
assert obj.non_data == "instance value"
assert obj.ordinary == "instance override"

bound = obj.method
assert bound.__self__ is obj
assert bound.__func__ is Example.method
~~~

The instance dictionary entry named `data` does not override the data descriptor. The instance entries for `non_data` and `ordinary` do shadow their class-level counterparts. Accessing `obj.method` invokes the function descriptor and returns a bound method.

**Best Practices**

- Explain lookup in terms of data descriptors, instance storage, and non-data descriptors rather than saying that instance attributes always win.
- Use `property` when a managed attribute is a clear part of the public object contract.
- Use descriptors when the same reusable attribute-management behavior is needed across multiple classes.
- Keep custom `__getattribute__` implementations narrow and delegate to the standard implementation when appropriate.
- Raise `AttributeError` only when an attribute is genuinely unavailable; other exceptions can have different effects on introspection and fallback behavior.
- Test interactions with inheritance, instance shadowing, descriptors, and `__slots__` when these features are part of a library's design.
- Avoid relying on `obj.__dict__` as a universal representation of instance state.

**Trade-offs & Edge Cases**

- Data descriptors provide strong control over an attribute but can make debugging and introspection less straightforward.
- Non-data descriptors allow instance-level shadowing, which is useful for methods and some caching patterns but may permit accidental overrides.
- Properties are concise for one class; reusable descriptors can centralize validation or storage behavior but add protocol complexity.
- `__slots__` can reduce per-instance storage overhead and constrain attributes, but changes storage assumptions and inheritance behavior.
- A custom `__getattribute__` can implement proxies or instrumentation, but it affects every ordinary attribute read and can introduce recursion or performance overhead.
- `__getattr__` is called after an `AttributeError`; code inside it should not accidentally mask unrelated failures as missing attributes.
- Attribute access and special-method lookup are related to Python's data model but are not identical; many implicit special-method operations look up methods on the type rather than through ordinary instance attribute access.

**Common Mistakes**

- Assuming the instance dictionary always takes precedence over class attributes.
- Treating every descriptor as a data descriptor.
- Defining `__set__` or `__delete__` on an object and assuming that alone determines descriptor classification, instead of checking the descriptor type's protocol.
- Assuming every instance has a `__dict__`.
- Forgetting that functions on classes are descriptors and become bound methods through instance access.
- Implementing `__getattribute__` by accessing attributes through `self.name`, causing infinite recursion.
- Using `__getattr__` to hide programming errors or unrelated exceptions.
- Assuming special-method lookup always follows the same path as `obj.attribute`.

**Senior-Level Perspective**

A senior engineer treats attribute lookup as part of an object's public behavioral contract, not merely as a memorized precedence list. When debugging, I first establish whether the class uses the default lookup implementation, then inspect the MRO, descriptor types, instance storage, and any fallback behavior. I also distinguish ordinary attribute access from implicit special-method dispatch.

For framework and library design, descriptors are appropriate when they provide a consistent reusable mechanism, such as validation, managed fields, or ORM instrumentation. They are not automatically preferable to explicit methods or properties. The choice should balance clarity, introspection, inheritance behavior, performance, and the complexity imposed on users of the API.

**Interview-Ready Answer (EN)**

"With normal instance attribute access, Python uses the attribute lookup machinery implemented by the object's type, usually the default `object.__getattribute__`. In that default algorithm, a data descriptor found on the class or its MRO has the highest precedence. Python then checks the instance's attribute storage, typically `__dict__`, and afterward considers a non-data descriptor or an ordinary class attribute. If lookup raises `AttributeError`, `__getattr__`, when defined, can provide a fallback.

Descriptors explain much of this behavior. A data descriptor defines `__get__` and also `__set__` or `__delete__`; a non-data descriptor defines `__get__` without the latter methods. Functions stored on classes are non-data descriptors, which is why accessing a method through an instance creates a bound method.

There are important qualifications: not every instance has a dictionary, custom `__getattribute__` can change normal lookup, and implicit special-method lookup is not always the same as ordinary attribute access. When debugging, I inspect the type's MRO, descriptors, instance storage, and custom lookup hooks rather than assuming a simple instance-before-class rule."

**Interview-Ready Answer (RU)**

«При обычном обращении к атрибуту экземпляра Python использует механизм поиска атрибутов, реализованный типом объекта, обычно стандартный `object.__getattribute__`. В этом алгоритме наивысший приоритет имеет data descriptor, найденный в классе или его MRO. Затем Python проверяет хранилище атрибутов экземпляра, обычно `__dict__`, и после этого рассматривает non-data descriptor или обычный атрибут класса. Если поиск завершается `AttributeError`, определённый в классе `__getattr__` может предоставить резервное значение.

Дескрипторы объясняют значительную часть этого поведения. Data descriptor определяет `__get__`, а также `__set__` или `__delete__`. Non-data descriptor определяет `__get__`, но не определяет методы установки или удаления. Функции, размещённые в классах, являются non-data descriptors, поэтому при обращении к методу через экземпляр Python создаёт связанный метод.

Есть важные уточнения: не каждый экземпляр имеет словарь `__dict__`, пользовательский `__getattribute__` может изменить стандартный поиск, а неявный поиск специальных методов не всегда совпадает с обычным доступом к атрибутам. При диагностике я проверяю MRO типа, дескрипторы, хранилище экземпляра и пользовательские механизмы поиска, а не полагаюсь на упрощённое правило «сначала экземпляр, затем класс»».

**Status:** Authored; independent technical and editorial review pending.

---

### FU-014 — Investigating unexpected instance attribute behavior

**Parent Main Question:** PY-004 — How do attribute lookup and special methods work in Python?

**Question (EN):** How would you investigate an attribute that appears to exist on a class but is unexpectedly missing or different on an instance?

**Перевод (RU):** Как бы ты исследовал ситуацию, когда атрибут, который, по-видимому, существует у класса, неожиданно отсутствует у экземпляра или имеет у него другое значение?

**What the interviewer evaluates**

- A systematic debugging approach to Python's attribute access protocol.
- Understanding of inheritance, MRO, descriptors, instance storage, and attribute interception.
- Ability to distinguish a missing attribute from an exception raised while computing its value.
- Appropriate use of introspection tools and awareness of their side effects.
- Awareness of dynamic mutation, slots, proxies, and framework-managed attributes.

**Short Answer**

I would reproduce the exact operation and capture the complete exception and traceback. Then I would inspect the runtime type and MRO, compare class-level definitions with instance storage, and check descriptors, properties, slots, and custom `__getattribute__` or `__getattr__` methods. I would distinguish failure to locate an attribute from an exception raised inside its descriptor or property getter. For non-invasive inspection, `inspect.getattr_static` can retrieve the raw attribute without invoking descriptor logic.

**Detailed Answer**

A key distinction is between "the name is defined somewhere in the class hierarchy" and "normal access through this particular instance successfully returns a value." They are not equivalent.

1. **Reproduce the exact operation.** Determine whether the failure occurs during `obj.name`, `Class.name`, `getattr`, `hasattr`, assignment, deletion, or an implicit operation. These may follow different paths. Capture the complete exception type, message, and traceback. An `AttributeError` can indicate failed lookup, but it can also originate inside a property or descriptor after the attribute was found.

2. **Identify the actual runtime type and MRO.** Inspect `type(obj)` and `type(obj).__mro__`. The object may be a subclass, proxy, dynamically generated class, or framework wrapper different from the class expected by the caller. A name may be inherited, overridden, or shadowed by another class earlier in the MRO.

3. **Compare class definitions with instance storage.** Inspect class dictionaries using `vars(cls)` or `cls.__dict__`. Inspect `vars(obj)` or `obj.__dict__` only if the instance supports a dictionary. Instances using `__slots__` and some extension types may not have one. A class dictionary exposes the raw object stored on the class, not necessarily the value returned by normal instance access.

4. **Check descriptor precedence.** Determine whether the class attribute is a data descriptor, non-data descriptor, property, or ordinary value. Data descriptors take precedence over an instance dictionary entry. Non-data descriptors can be shadowed by instance attributes. A property is a data descriptor; its getter may compute a value, access other state, or raise an exception. A descriptor can also behave differently on class access because its `__get__` receives `instance=None`.

5. **Inspect custom attribute hooks.** `__getattribute__` intercepts ordinary attribute reads. Check whether an override delegates correctly to the standard implementation and whether it conditionally hides attributes or causes recursion. Then inspect `__getattr__`, which is a fallback after an `AttributeError`. Proxies and lazy-loading objects often use these hooks to synthesize or forward attributes.

6. **Check slots and initialization.** Verify that initialization assigns the expected state on every relevant code path. With `__slots__`, storage is represented by slot descriptors rather than necessarily appearing in `__dict__`. A declared slot can remain unset on a particular object, and reading it can raise `AttributeError`. Consider alternate constructors, deserialization, partially initialized objects, and lifecycle timing.

7. **Choose introspection tools carefully.** `hasattr(obj, "name")` performs normal attribute access and returns `False` when that access raises `AttributeError`. It can execute a property or descriptor and can conceal an `AttributeError` raised inside it. `getattr` also invokes normal lookup. `dir` is a convenience listing and can be customized by `__dir__`; it does not guarantee that reading a listed attribute will succeed. `inspect.getattr_static(obj, "name")` avoids dynamic descriptor lookup and custom `__getattribute__` behavior, so it is useful for examining the raw definition without triggering normal access side effects.

8. **Investigate mutation and environment.** Check for monkey-patching, decorators, metaclasses, import mismatches, test fixtures, and runtime class transformation. In concurrent or asynchronous code, verify initialization and access ordering. Framework objects may use generated models, ORM instrumentation, proxy layers, or lazy-loaded fields.

9. **Reduce the case and verify the hypothesis.** Create a minimal reproduction that isolates inheritance, instance storage, descriptors, and custom hooks. Test class-level and instance-level access separately. Fix the underlying contract or lifecycle issue rather than adding broad exception handling that hides the defect.

**Diagnostic Checklist**

- What exact expression is failing, and what is the full traceback?
- What are the runtime type and its MRO?
- Where is the name defined or overridden?
- Is the class attribute a data descriptor, non-data descriptor, property, or ordinary value?
- Does the instance have `__dict__`, or does it use `__slots__`?
- Do custom `__getattribute__`, `__getattr__`, or `__dir__` methods participate?
- Does a property or descriptor getter itself raise an exception?
- Was the object fully initialized, and could it have been mutated?
- Does static inspection differ from normal attribute access?

**Practical Example**

~~~python
import inspect


class Model:
    @property
    def status(self):
        return self._status.upper()


class Proxy(Model):
    def __getattribute__(self, name):
        if name == "status":
            return "hidden by proxy"
        return super().__getattribute__(name)


model = Model()
model._status = "ready"

proxy = Proxy()
proxy._status = "ready"

assert model.status == "READY"
assert proxy.status == "hidden by proxy"

# Static inspection returns the property without invoking its getter.
raw_status = inspect.getattr_static(model, "status")
assert isinstance(raw_status, property)
assert isinstance(Model.status, property)
~~~

The property exists on the class, but the subclass's `__getattribute__` changes the value observed through an instance. Static inspection reveals the raw property object without invoking the getter or the proxy's normal lookup path.

A separate failure can occur when the property exists but its backing state has not been initialized:

~~~python
class Incomplete:
    @property
    def value(self):
        return self._value


item = Incomplete()

try:
    item.value
except AttributeError as exc:
    # The property exists; its getter fails because _value is absent.
    print(type(exc).__name__, exc)
~~~

The correct diagnosis is not that `Incomplete.value` is missing. The property exists, but evaluating it fails because the backing state is absent.

**Best Practices**

- Diagnose the runtime object, not only the source-level class declaration.
- Preserve full tracebacks; do not equate every `AttributeError` with failed name lookup.
- Use `inspect.getattr_static` when raw inspection must avoid descriptor side effects.
- Use `vars(obj)` only when the object exposes an instance dictionary.
- Keep `__getattribute__` overrides narrow and carefully tested.
- Maintain consistent initialization invariants across constructors, factories, and deserialization.
- Avoid broad exception handling that hides failures inside properties or descriptors.
- Understand framework instrumentation and lifecycle before changing framework-managed objects.

**Trade-offs & Edge Cases**

- `getattr` and `hasattr` may execute user-defined behavior. Static inspection avoids some side effects but does not reveal the final value normal access would return.
- A descriptor may intentionally raise `AttributeError` to signal an unavailable value; this can trigger `__getattr__` and make a defined attribute appear absent.
- `hasattr` suppresses `AttributeError`, including one raised inside a property getter.
- `__slots__` changes storage assumptions; a slot may exist but remain unset.
- Proxies and lazy loading can make access dependent on external state, initialization order, or I/O.
- Monkey-patching may make runtime behavior differ from checked-in source and complicate diagnosis.
- `inspect.getattr_static` is intentionally static: it may return a descriptor object rather than the value ordinary access would produce.

**Common Mistakes**

- Inspecting only the class source and ignoring the runtime type and MRO.
- Assuming every instance has `__dict__`.
- Treating `hasattr` as a side-effect-free declaration check.
- Assuming an exception from a property getter proves that the property is absent.
- Forgetting that data descriptors override instance dictionary entries.
- Assuming `dir(obj)` guarantees every listed attribute can be read.
- Ignoring custom attribute hooks, slots, and incomplete initialization.
- Catching `AttributeError` broadly and silently substituting a default value.

**Senior-Level Perspective**

At senior level, I treat unexpected attribute behavior as a runtime contract and observability problem. I establish the exact operation and exception, then inspect the runtime type, MRO, raw class definitions, instance storage, descriptors, and custom lookup hooks. I deliberately distinguish attribute discovery from attribute evaluation: a property or descriptor can be present while its getter fails, performs I/O, or returns a computed value different from the raw class-level object.

For production systems, I also investigate object lifecycle and concurrency. Partially initialized models, lazy ORM attributes, proxies, deserialization, monkey-patching, and generated classes can produce behavior that is not obvious from the source declaration. The durable fix is usually to make initialization and the attribute contract explicit, improve diagnostics, and add a focused regression test—not to suppress `AttributeError` indiscriminately.

**Interview-Ready Answer (EN)**

"I would start by reproducing the exact operation and examining the complete exception and traceback. An attribute can exist on the class while access through an instance behaves differently because Python's lookup protocol includes the runtime type's MRO, instance storage, descriptors, and custom attribute hooks.

I would inspect `type(obj)` and its MRO, then compare the class dictionaries with the instance's storage, if it has a `__dict__`. I would determine whether the class attribute is a data descriptor, a non-data descriptor, a property, or an ordinary value. Data descriptors take precedence over instance dictionary entries, while non-data descriptors can be shadowed by instance attributes. I would also inspect `__getattribute__` and `__getattr__`, and check whether slots or incomplete initialization explain the behavior.

I would not rely on `hasattr` or `dir` as definitive proof. `hasattr` performs normal access and suppresses `AttributeError`, including one raised inside a property getter. For non-invasive inspection, I can use `inspect.getattr_static` to retrieve the raw attribute without invoking descriptor logic. Finally, I would isolate the cause in a minimal reproduction and fix the underlying lookup, descriptor, or lifecycle issue rather than masking the exception."

**Interview-Ready Answer (RU)**

«Сначала я бы воспроизвёл точную операцию и изучил полное исключение вместе с traceback. Атрибут может существовать в классе, но вести себя иначе при обращении через экземпляр, поскольку протокол поиска Python учитывает фактический тип объекта и его MRO, хранилище экземпляра, дескрипторы и пользовательские механизмы доступа к атрибутам.

Я бы проверил `type(obj)` и его MRO, затем сравнил словари классов с хранилищем экземпляра, если у него есть `__dict__`. Далее определил бы, является ли атрибут data descriptor, non-data descriptor, property или обычным значением. Data descriptors имеют приоритет над записями в словаре экземпляра, тогда как non-data descriptors могут быть перекрыты атрибутами экземпляра. Также я проверил бы `__getattribute__`, `__getattr__`, использование `__slots__` и полноту инициализации объекта.

Я бы не считал `hasattr` или `dir` окончательным доказательством существования доступного атрибута. `hasattr` выполняет обычное обращение и подавляет `AttributeError`, в том числе исключение, возникшее внутри getter свойства. Для неинвазивной проверки можно использовать `inspect.getattr_static`, который получает исходный атрибут, не запуская логику дескриптора. В завершение я бы изолировал причину в минимальном примере и исправил проблему в механизме поиска, дескрипторе или жизненном цикле объекта, а не маскировал исключение».

**Status:** Authored; independent technical and editorial review pending.


