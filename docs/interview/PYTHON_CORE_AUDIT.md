# Python Core Completeness Audit

**Status:** Remediation applied to both EN and RU question banks; final technical consistency review remains open.  
**Scope:** The 30-question bilingual bank in `PYTHON_CORE_QUESTIONS.md` and `PYTHON_CORE_QUESTIONS.ru.md`.  
**Reference baseline:** Official Python 3.14 Language Reference and Library Reference, with version-specific changes checked against the Python 3.14 What's New documentation.  
**Review principle:** Distinguish language guarantees from CPython implementation details and from backend-engineering practices.

---

## 1. Executive assessment

The current bank provides broad and useful preparation for a Senior Python Backend Engineer interview. It covers the object model, typing, functions, iteration, exceptions, resource management, imports, memory management, data structures, text handling, concurrency, descriptors, metaclasses, serialization, packaging, testing, observability, security, API design, architecture, performance, and CPython execution.

However, **30/30 questions drafted does not mean the curriculum is fully validated or that it exhaustively covers the Python language**. The bank currently combines three layers:

1. **Python language and runtime fundamentals** — the language semantics, object model, execution, built-ins and standard library.
2. **Advanced Python and CPython implementation knowledge** — descriptors, metaclasses, runtime internals, concurrency implementation details.
3. **Python backend engineering practices** — API contracts, architecture, security, testing, observability and production performance.

That combination is appropriate for the stated Senior Backend Engineer target, but it should be named and organized transparently rather than described as only the narrow Python language core.

## 2. Coverage map

| Area | Current coverage | Audit assessment |
|---|---|---|
| Objects, identity, mutability, argument passing | Q1–Q4 | Strong; Q1 and Q4 have some conceptual overlap and should be checked for unnecessary repetition |
| Type system, protocols, annotations | Q5, Q21 | Broad; add current-version annotation evaluation semantics |
| Data model, special methods, descriptors, metaclasses | Q6, Q18–Q19 | Strong advanced coverage |
| Scope, functions, decorators, closures | Q7–Q8 | Strong |
| Iteration, generators, lazy evaluation | Q9 | Strong iterator/generator coverage; comprehensions deserve explicit treatment |
| Exceptions and resource management | Q10–Q11 | Broad, including exception groups; verify edge cases and modern control-flow semantics |
| Modules, packages, imports | Q12, Q23 | Broad |
| Memory management and performance | Q13–Q14, Q29–Q30 | Broad but overlapping; distinguish memory lifecycle, profiling, and end-to-end performance |
| Built-in collections and complexity | Q15 | Strong |
| Strings, Unicode, encodings | Q16 | Strong |
| Concurrency, threads, processes, GIL | Q17 | Good foundation; add subinterpreters and InterpreterPoolExecutor as version-aware topics |
| Serialization and object state | Q20 | Strong, including security boundaries |
| Standard library | Q22 | Curated backend-relevant subset, not an exhaustive standard-library survey |
| Testing, logging, security | Q24–Q26 | Strong backend-engineering coverage |
| HTTP APIs, architecture, dependency injection | Q27–Q28 | Backend engineering extension, not narrow language core |
| CPython execution model | Q30 | Good foundation; retain explicit implementation/version boundaries |

## 3. Material gaps or topics needing explicit coverage

### G-01 — Expression semantics and evaluation order

The current bank discusses special methods and operators, but does not make the full expression model an explicit learning target. Add or verify coverage for:

- Operator precedence and associativity.
- Evaluation order and side effects in expressions.
- Short-circuit evaluation of `and` and `or`.
- Chained comparisons.
- Conditional expressions and assignment expressions (`:=`).
- Distinguishing syntax/precedence rules from operator overloading.

**Recommended placement:** Expand Q6 or add a dedicated follow-up there. Do not add another primary question unless the review finds the existing question cannot carry this material cleanly.

### G-02 — Comprehensions and scope semantics

Q9 covers generator expressions, but list, set and dictionary comprehensions should be explicitly compared with generator expressions:

- Eager versus lazy evaluation.
- Scope behaviour and variable leakage rules.
- Nested comprehensions and readability.
- Side effects and exception timing.
- Memory and execution trade-offs.

**Recommended placement:** Expand Q9.

### G-03 — Structural pattern matching and control-flow completeness

The bank covers common control flow indirectly, but structural pattern matching (`match`/`case`) is not an explicit topic. Add the semantics and practical limits of sequence, mapping, class, OR and guarded patterns, including the fact that matching is not a substitute for validation or authorization.

**Recommended placement:** Add a follow-up or a clearly scoped subsection to an existing language-semantics question.

### G-04 — Version-aware annotations (Python 3.14)

Q5 and Q21 correctly distinguish annotations from automatic runtime type enforcement, but they should explicitly describe deferred annotation evaluation introduced in Python 3.14 and the `annotationlib` inspection APIs. Avoid presenting one annotation-evaluation model as universal across supported Python versions.

**Recommended placement:** Expand Q21; add a compatibility note to Q5 if needed.

### G-05 — Modern CPython concurrency (Python 3.14)

Q17 already handles the conventional GIL and optional free-threaded builds accurately at a high level. Extend it to cover:

- Subinterpreters and their isolation model.
- `concurrent.interpreters` and `InterpreterPoolExecutor`.
- Extension-module compatibility and cross-interpreter data constraints.
- The distinction between free-threading and multiple interpreters.
- The fact that neither model removes the need to reason about synchronization, isolation, and workload measurements.

**Recommended placement:** Expand Q17, keeping claims tied to the target Python version and build.

### G-06 — Standard-library breadth and selection

Q22 is appropriately selective for backend work; it should not attempt to catalogue every standard-library module. Consider explicitly identifying high-value omissions where relevant to the target role:

- `decimal` and `fractions` for numeric semantics.
- `secrets` versus `random` for security-sensitive randomness.
- `contextvars` for context propagation across asynchronous execution.
- `memoryview` and the buffer protocol for binary data and zero-copy interfaces.

**Recommended placement:** Add a concise selection matrix or follow-up coverage to Q22. Do not turn Q22 into an exhaustive module inventory.

## 4. Duplication and scope findings

1. **Q1 vs Q4:** Both address identity, equality and object references. Keep Q1 focused on the object model and Q4 focused on comparison, aliasing and correctness implications; remove repeated explanations where they do not add depth.
2. **Q14 vs Q29:** Both cover performance. Keep Q14 focused on Python-level profiling and optimization concepts; keep Q29 focused on service-level performance engineering, load testing, latency distributions, capacity and regression control.
3. **Q13 vs Q29:** Keep Q13 focused on object lifetime, garbage collection and memory behaviour; keep Q29 focused on diagnosing process/container memory and system-level performance.
4. **Q27–Q29:** These are valuable for a Senior Python Backend Engineer, but they are backend engineering extensions rather than narrow Python language-core topics.
5. **Q25–Q26:** Logging/observability and secure coding are cross-cutting engineering competencies, not language semantics. They belong in the role-oriented curriculum but should be labelled accordingly.

## 5. Topics intentionally not required for the narrow Core baseline

The following are useful advanced or specialist subjects, but should not be treated as mandatory gaps in a general Senior Python Backend Engineer core unless the target role requires them:

- CPython C API and extension-module authoring.
- Detailed object memory layout and allocator internals.
- JIT/compiler implementation internals.
- Every standard-library module and every built-in function.
- Interpreter-specific bytecode details beyond diagnostic literacy.
- Platform-specific operating-system APIs.

These can be placed in an optional Advanced Python / CPython Internals track.

## 6. Version policy

The curriculum should state its supported Python baseline. Version-sensitive claims must be marked explicitly and reviewed against that baseline. The audit used Python 3.14 documentation as the current stable reference point for this pass.

At minimum, review these version-sensitive areas:

- Deferred annotation evaluation and `annotationlib` in Python 3.14.
- Free-threaded CPython availability and runtime configuration.
- Subinterpreters and `InterpreterPoolExecutor` in Python 3.14.
- Bytecode and frame implementation details, which are not stable language contracts.
- Deprecations and behavioural changes documented in each supported release's What's New and porting guides.

Do not silently rewrite general Python semantics to match one CPython version.

## 7. Initial remediation plan (completed in first pass)

| Order | Action | Target |
|---|---|---|
| 1 | Add expression evaluation, precedence and short-circuit semantics | Q6 |
| 2 | Make comprehensions and their scope/evaluation trade-offs explicit | Q9 |
| 3 | Add structural pattern matching coverage | Existing language-semantics question |
| 4 | Add Python 3.14 deferred annotation semantics | Q21, with Q5 compatibility note if needed |
| 5 | Add subinterpreters and InterpreterPoolExecutor | Q17 |
| 6 | Add a concise standard-library selection matrix | Q22 |
| 7 | Reduce overlap between Q1/Q4, Q13/Q29 and Q14/Q29 | Relevant questions |
| 8 | Label the curriculum as Python Core + Advanced Python + Backend Engineering competencies | Both question-bank introductions |
| 9 | Re-read both language versions and perform a technical consistency check | EN and RU files |

## 8. Remediation status

The first remediation pass has been applied to both bilingual question-bank files. The primary-question count remains **30**.

| Gap | Remediation | Target | Status |
|---|---|---|---|
| G-01 | Added precedence, associativity, evaluation-order, short-circuit, chained-comparison, conditional-expression and assignment-expression coverage | Q6 | Addressed; final review pending |
| G-02 | Added eager/lazy comprehension semantics, scope, nested evaluation, side effects and exception timing | Q9 | Addressed; final review pending |
| G-03 | Added sequence, mapping, class, OR and guarded structural patterns; clarified validation/authorization boundary | Q6 | Addressed; final review pending |
| G-04 | Added Python 3.14 deferred annotation semantics and annotationlib guidance | Q5, Q21 | Addressed; final review pending |
| G-05 | Added subinterpreters and InterpreterPoolExecutor, distinguished from free-threaded execution | Q17 | Addressed; final review pending |
| G-06 | Added a concise selection matrix for decimal, fractions, secrets, contextvars, memoryview and the buffer protocol | Q22 | Addressed; final review pending |

### Explicit boundaries for overlapping questions

- **Q1 vs Q4:** Q1 owns the foundational object model (identity, type, value, name binding and call-by-sharing). Q4 owns comparison semantics (is/==), the equality/hash contract and correctness consequences of aliasing. Avoid repeating the full object-model explanation in Q4.
- **Q13 vs Q29:** Q13 owns object lifetime, reference graphs, cyclic GC, weak references and Python-level retention. Q29 owns process/container memory signals, system capacity and memory as one dimension of service-level performance.
- **Q14 vs Q29:** Q14 owns local algorithmic reasoning, Python profiling tools and code-level optimization. Q29 owns end-to-end workload design, latency percentiles, load generation, saturation, capacity, performance SLOs and regression controls.

These boundaries are editorial guidance for the final pass; they do not imply that all overlap has already been removed from every paragraph.

## 9. Official references

- Python 3.14 Language Reference: https://docs.python.org/3.14/reference/
- Python 3.14 Execution Model: https://docs.python.org/3.14/reference/executionmodel.html
- Python 3.14 Data Model: https://docs.python.org/3.14/reference/datamodel.html
- Python 3.14 Expressions: https://docs.python.org/3.14/reference/expressions.html
- Python 3.14 Compound Statements: https://docs.python.org/3.14/reference/compound_stmts.html
- Python 3.14 Standard Library: https://docs.python.org/3.14/library/
- What's New in Python 3.14: https://docs.python.org/3.14/whatsnew/3.14.html
- Python free-threading HOWTO: https://docs.python.org/3.14/howto/free-threading-python.html
- PEP 734 — Multiple Interpreters in the Stdlib: https://peps.python.org/pep-0734/
- PEP 649 — Deferred Evaluation Of Annotations: https://peps.python.org/pep-0649/
- PEP 749 — Implementing PEP 649: https://peps.python.org/pep-0749/

---

## Русское резюме аудита

Текущий банк из 30 вопросов даёт широкую базу для Senior Python Backend Engineer, но пока не должен называться полностью проверенным или исчерпывающим Python Core.

**Основные пробелы для исправления:** семантика выражений и порядок вычисления; comprehensions и их scope; structural pattern matching; отложенное вычисление аннотаций в Python 3.14; subinterpreters и InterpreterPoolExecutor; отдельные важные модули стандартной библиотеки.

**Основные пересечения:** Q1/Q4 (identity и object references), Q14/Q29 (performance), Q13/Q29 (memory). Их нужно разграничить, а не механически удалять темы.

**Рекомендация:** сохранить 30 основных вопросов, исправить и расширить существующие, а саму программу позиционировать как три взаимосвязанных уровня: Python Core, Advanced Python/CPython и Senior Backend Engineering. После внесения исправлений провести повторную техническую проверку EN и RU версий. До этого аудит остаётся предварительным.
