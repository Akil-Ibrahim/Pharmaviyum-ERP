# Python Core — Question Bank

**Status:** In progress  
**Coverage:** 30 of 30 primary questions drafted  
**Review rule:** Draft answers must be technically reviewed before being marked validated.

---

## PY-CORE-001 — Python object model: identity, type and value

> **Scope boundary:** This question establishes the Python object model: identity, type, value, name binding, aliasing, and mutation versus rebinding. Detailed equality/identity operators, `id()` semantics, and the equality/hash contract belong to Q4. References to `is` and `==` here are introductory only.
>
> **Граница темы:** вопрос вводит модель объектов Python: identity, type, value, привязку имён, aliasing и различие мутации и переназначения. Подробная семантика `is` / `==`, `id()` и контракт equality/hash рассматриваются в Q4.

### Question (EN)

**Can you explain Python's object model and distinguish an object's identity, type and value?**

### Перевод (RU)

**Можете объяснить объектную модель Python и разграничить идентичность объекта, его тип и значение?**

### What the interviewer evaluates

- Understanding that Python variables are names bound to objects, not typed storage boxes.
- Correct distinction between identity (is) and equality (==).
- Understanding of mutability and aliasing.
- Ability to reason about function arguments and side effects.
- Awareness that object interning is an implementation detail, not a language guarantee.

### Model answer (RU)

В Python объект — это сущность, у которой есть **идентичность, тип и значение**.

- **Идентичность (identity)** определяет, какой именно это объект. В течение жизненного цикла объекта она не меняется. Оператор **is** проверяет, ссылаются ли два имени на один и тот же объект.
- **Тип (type)** определяет поведение объекта и набор поддерживаемых операций. Его можно получить через **type()**. В обычной модели Python тип объекта не меняется в течение его жизни.
- **Значение (value)** — данные, которые представляет объект. Оператор **==** проверяет равенство согласно реализации сравнения типа, обычно **__eq__**, а не обязательно идентичность.

Переменная в Python — это имя, связанное с объектом. Присваивание обычно не копирует объект: оно связывает другое имя с тем же объектом. Поэтому два имени могут быть **алиасами** одного изменяемого объекта. Изменение объекта через одно имя будет наблюдаться и через другое.

Это важно при передаче аргументов в функции. Python использует модель передачи ссылок на объекты, часто описываемую как *call by sharing*: функция получает доступ к тому же объекту. Если объект изменяемый, функция может изменить его состояние, и вызывающий код увидит изменение. Но переназначение локального параметра на другой объект само по себе не переназначает переменную вызывающего кода.

Для сравнения значений используется **==**. Оператор **is** уместен, когда важна идентичность, например при проверке **value is None**.

Нельзя полагаться на то, что одинаковые литералы всегда будут одним объектом. CPython может применять interning и другие оптимизации, но это детали реализации, а не универсальный контракт языка.

### Model answer (EN)

Every Python object has an **identity, a type and a value**.

- **Identity** distinguishes a particular object. It remains stable during that object's lifetime, and **is** checks whether two references point to the same object.
- **Type** defines the object's behaviour and the operations it supports. It can be inspected with **type()**. In Python's normal object model, an object's type does not change during its lifetime.
- **Value** is the data represented by the object. **==** checks equality according to the type's equality implementation, typically **__eq__**; it does not necessarily check identity.

A variable in Python is a name bound to an object, not a typed container holding the object itself. Assignment generally binds another name to the same object rather than copying it. Consequently, two names can alias the same mutable object. A mutation performed through one alias is observable through the other.

This also matters for function calls. Python follows a *call-by-sharing* model: a function receives access to the same object. If that object is mutable, the function can mutate it and the caller can observe the change. Rebinding the local parameter, however, does not rebind the caller's variable.

I use **==** for value comparison and **is** for identity checks, commonly for singleton checks such as **value is None**. I do not rely on object interning or identity behaviour of literals: those may be implementation optimisations, not language-level guarantees.

### Follow-up questions and model answers

#### FU-1

**EN:** Can an object's value change while its identity and type remain the same? Explain with a mutable object.  
**RU:** Может ли значение объекта измениться, если его идентичность и тип остаются прежними? Объясните на примере изменяемого объекта.

**Answer (RU):** Да. Например, вызов append() изменяет существующий список на месте: объект сохраняет свою идентичность и тип list, но его содержимое меняется. Это отличает мутацию от переназначения имени или создания нового объекта. Для неизменяемого объекта изменение значения на месте невозможно; операция, формирующая новое значение, приводит к использованию другого объекта и переназначению имени.

**Answer (EN):** Yes. For example, calling append() mutates an existing list in place: the object retains its identity and list type while its contents change. This is different from rebinding a name or creating a new object. An immutable object cannot be changed in place; an operation that produces a different value results in another object being used and the name being rebound.

#### FU-2

**EN:** If you pass a list to a function and the function appends an item, what can the caller observe?  
**RU:** Если передать список в функцию и функция добавит в него элемент, что увидит вызывающий код?

**Answer (RU):** Если функция изменяет переданный список на месте, вызывающий код увидит изменение, потому что оба участка кода работают с одним объектом. Если функция лишь присвоит локальному параметру ссылку на новый список, исходная переменная вызывающего кода останется связанной с прежним объектом.

**Answer (EN):** An in-place mutation is visible to the caller because both the caller and the function refer to the same list object. Rebinding the function's local parameter to a new list does not change the caller's binding.

#### FU-3

**EN:** Why does assignment not necessarily create a copy of an object?  
**RU:** Почему присваивание не обязательно создаёт копию объекта?

**Answer (RU):** Обычное присваивание связывает имя с объектом, а не копирует его. Поэтому после присваивания second = first оба имени обычно указывают на один объект. Если нужна независимая копия, её следует создать явно и выбрать поверхностное или глубокое копирование в зависимости от структуры данных и требуемой семантики.

**Answer (EN):** Ordinary assignment binds a name to an object; it does not copy the object. After assigning second = first, both names therefore usually refer to the same object. If an independent copy is required, create it explicitly and choose shallow or deep copying according to the data structure and required semantics.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about a specific implementation:** imagine a service receives a mutable list of medication search filters. If multiple layers share that list, an in-place mutation in one layer can unexpectedly affect another layer. A safer API design may use immutable value objects, defensive copies at ownership boundaries, or explicit mutation contracts.

The candidate should inspect the actual repository before claiming that a particular Pharmaviyum service currently uses one of these approaches.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Treats variables as boxes; confuses identity and equality; says arguments are copied automatically. |
| Competent | Correctly explains is, ==, mutability and aliasing with a simple example. |
| Strong Senior | Explains object bindings, call-by-sharing, mutation versus rebinding, equality protocol and why interning is not a correctness guarantee; connects aliasing to API ownership and side-effect control. |

### Common pitfalls

- Saying Python passes arguments strictly by reference or strictly by value without explaining object-sharing semantics.
- Claiming is is a faster or interchangeable version of ==.
- Assuming mutable objects are automatically copied on function calls.
- Treating CPython interning as a language guarantee.
- Confusing reassignment of a name with mutation of the referenced object.

### References

- Python data model: https://docs.python.org/3/reference/datamodel.html
- Python expressions — identity comparisons: https://docs.python.org/3/reference/expressions.html#is-not
- Programming FAQ — identity and equality: https://docs.python.org/3/faq/programming.html#why-did-changing-list-y-also-change-list-x

---

## PY-CORE-002 — Mutability and immutability

### Question (EN)

**What is the difference between mutable and immutable objects in Python, and how does that distinction affect program design, hashing, and function behaviour?**

### Перевод (RU)

**В чём разница между изменяемыми и неизменяемыми объектами в Python и как это различие влияет на проектирование программ, хеширование и поведение функций?**

### What the interviewer evaluates

- Distinguishing mutation of an object from rebinding a name.
- Knowing common mutable and immutable built-in types.
- Understanding hashability and dictionary/set key requirements.
- Understanding shallow versus deep copying and nested mutable state.
- Designing APIs with explicit ownership and side-effect contracts.

### Model answer (RU)

**Изменяемость (mutability)** описывает, может ли состояние существующего объекта изменяться после его создания. Изменение объекта не обязательно означает создание нового объекта.

К типичным изменяемым встроенным типам относятся **list, dict, set и bytearray**. К типичным неизменяемым — **int, float, bool, str, bytes, tuple и frozenset**. Это классификация конкретных типов; пользовательские объекты не становятся автоматически неизменяемыми.

У неизменяемого объекта его значение нельзя изменить на месте. Операции, которые выглядят как изменение, обычно создают новый объект. Например, конкатенация строк создаёт новую строку. Напротив, **list.append()** изменяет существующий список, поэтому все имена-алиасы этого списка увидят изменение.

Важно различать **мутацию** и **переназначение**. Вызов **items.append(x)** меняет объект списка. Выражение **items = items + [x]** создаёт новый список и переназначает имя items; другие имена, ссылавшиеся на исходный список, продолжат ссылаться на него.

Изменяемость связана с **hashability**, но это не одно и то же. Хешируемый объект имеет хеш, который должен оставаться стабильным, пока объект находится в хеш-коллекции; равные объекты должны иметь одинаковые хеши. Встроенные изменяемые контейнеры list, dict и set не хешируются. Неизменяемые типы часто хешируемы, но не всегда: tuple хешируется только тогда, когда хешируемы все его элементы. Поэтому кортеж может содержать список, но такой кортеж нельзя использовать как ключ словаря.

При проектировании API я явно определяю, кто владеет переданными данными и разрешено ли функции изменять их на месте. Если функция не должна создавать побочные эффекты, можно принимать неизменяемые структуры, создавать копию на границе владения или возвращать новое значение. Копирование имеет стоимость. Поверхностная копия создаёт новый внешний контейнер, но сохраняет ссылки на вложенные объекты; глубокая копия рекурсивно копирует вложенные объекты, насколько это поддерживается протоколом, и может быть дороже или неприменима к некоторым ресурсам.

Неизменяемые значения упрощают reasoning, безопасное совместное использование и применение в качестве ключей. Изменяемые объекты полезны для эффективного обновления состояния, но требуют ясного контракта владения, контроля алиасов и побочных эффектов.

### Model answer (EN)

**Mutability** describes whether an object's state can be changed after creation. Mutating an object does not necessarily create a new object.

Common mutable built-in types include **list, dict, set, and bytearray**. Common immutable built-in types include **int, float, bool, str, bytes, tuple, and frozenset**. This is a property of particular types; user-defined objects are not automatically immutable.

An immutable object's value cannot be changed in place. An operation that appears to modify it generally creates a new object. String concatenation, for example, creates a new string. By contrast, **list.append()** mutates the existing list, so every alias to that list observes the change.

I distinguish **mutation** from **rebinding**. **items.append(x)** changes the list object. **items = items + [x]** creates a new list and rebinds the name items; other names referring to the original list remain bound to it.

Mutability is related to **hashability**, but the concepts are not identical. A hashable object's hash must remain stable while it is stored in a hash-based collection, and equal objects must have equal hashes. Mutable built-in containers such as lists, dictionaries, and sets are unhashable. Many immutable types are hashable, but not all: a tuple is hashable only if all its elements are hashable. A tuple can therefore contain a list, but that tuple cannot be used as a dictionary key.

When designing APIs, I make ownership and mutation contracts explicit. If a function must not cause side effects, I can accept immutable structures, copy data at an ownership boundary, or return a new value. Copying has a cost. A shallow copy creates a new outer container but retains references to nested objects; a deep copy recursively copies nested objects where supported and may be more expensive or unsuitable for certain resources.

Immutable values make reasoning, safe sharing, and use as mapping keys easier. Mutable objects are useful for efficient state updates, but they require clear ownership, aliasing, and side-effect contracts.

### Follow-up questions and model answers

#### FU-1

**EN:** Why is a list unhashable, and why does a dictionary key need a stable hash?  
**RU:** Почему список не хешируется и зачем ключу словаря нужен стабильный хеш?

**Answer (RU):** Содержимое списка может измениться, поэтому хеш мог бы измениться после помещения объекта в словарь или множество. Это нарушило бы поиск по хеш-таблице. Ключ должен сохранять хеш, согласованный с равенством, пока находится в коллекции.

**Answer (EN):** A list can change, so its hash could change after insertion into a dictionary or set, breaking hash-table lookup. A key must maintain a hash consistent with equality while stored in the collection.

#### FU-2

**EN:** Is every immutable object hashable? Explain the tuple case.  
**RU:** Каждый ли неизменяемый объект хешируем? Объясните случай с tuple.

**Answer (RU):** Нет. Неизменяемость сама по себе не гарантирует hashability. Кортеж хешируется, только если хешируются все его элементы. Кортеж из целых чисел может быть ключом словаря, а кортеж со списком — нет.

**Answer (EN):** No. Immutability alone does not guarantee hashability. A tuple is hashable only when all its elements are hashable. A tuple of integers can be a dictionary key, while a tuple containing a list cannot.

#### FU-3

**EN:** What is the difference between a shallow copy and a deep copy?  
**RU:** Чем поверхностное копирование отличается от глубокого?

**Answer (RU):** Поверхностная копия создаёт новый внешний объект, но сохраняет ссылки на вложенные объекты. Глубокая копия рекурсивно копирует вложенные объекты, насколько это поддерживается. Она может быть дороже и не всегда подходит для ресурсов вроде соединений или файловых дескрипторов.

**Answer (EN):** A shallow copy creates a new outer object but retains references to nested objects. A deep copy recursively copies nested objects where supported. It can be more expensive and may be inappropriate for resources such as connections or file descriptors.

#### FU-4

**EN:** Can an immutable tuple contain a mutable object? What does that imply?  
**RU:** Может ли неизменяемый tuple содержать изменяемый объект? К чему это приводит?

**Answer (RU):** Да. Неизменяемость кортежа запрещает заменять его элементы, но не делает неизменяемыми объекты, на которые эти элементы ссылаются. Вложенный список можно изменить; кортеж с таким списком не будет хешируемым.

**Answer (EN):** Yes. Tuple immutability prevents replacing its elements, but it does not make referenced objects immutable. A nested list can still be mutated, and a tuple containing that list is unhashable.

#### FU-5

**EN:** How would you prevent a function from unexpectedly mutating caller-owned data?  
**RU:** Как предотвратить неожиданное изменение данных вызывающего кода внутри функции?

**Answer (RU):** Сначала нужно определить контракт владения. Можно принимать неизменяемые структуры, копировать данные на границе владения, преобразовывать вход во внутреннее представление или возвращать новое значение. Не следует применять глубокое копирование автоматически: оно может быть дорогим и неподходящим для некоторых ресурсов.

**Answer (EN):** I would define the ownership contract first. Options include accepting immutable structures, copying at an ownership boundary, converting input into an internally owned representation, or returning a new value. I would not use deep copying indiscriminately because it can be expensive or unsuitable for certain resources.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a medication-search workflow passes filters through validation, retrieval, and ranking layers. If one layer mutates a shared dictionary or list, later layers may observe unexpected state. A robust design defines ownership at each boundary, uses immutable request/value objects where practical, and makes intentional mutations explicit.

Do not claim that a specific Pharmaviyum model is immutable or mutable without checking its actual implementation.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Confuses mutation with rebinding and assumes every immutable object is hashable. |
| Competent | Correctly classifies common built-in types and explains list/dictionary key behaviour. |
| Strong Senior | Explains hash/equality invariants, nested mutability, copy trade-offs, ownership boundaries, aliasing, API side effects, and performance implications. |

### Common pitfalls

- Assuming an immutable container makes its contents immutable.
- Assuming every immutable object is hashable.
- Mutating an object used as a key in a hash-based collection.
- Assuming a shallow copy recursively copies nested objects.
- Using deep copy as a universal solution without considering cost and resource semantics.
- Ignoring ownership and side-effect contracts in APIs.

### References

- Python glossary — hashable: https://docs.python.org/3/glossary.html#term-hashable
- Python data model: https://docs.python.org/3/reference/datamodel.html
- Built-in types: https://docs.python.org/3/library/stdtypes.html
- copy module: https://docs.python.org/3/library/copy.html

---

## PY-CORE-003 — Python's argument passing semantics

### Question (EN)

**How does Python pass arguments to functions? Explain object references, mutation, rebinding, and the risks of mutable default arguments.**

### Перевод (RU)

**Как Python передаёт аргументы в функции? Объясните ссылки на объекты, мутацию, переназначение и риски изменяемых аргументов по умолчанию.**

### What the interviewer evaluates

- Understanding that Python uses object references / call by sharing, not traditional call-by-reference.
- Distinguishing mutation of an argument object from rebinding a parameter name.
- Knowing how `*args` and `**kwargs` collect arguments.
- Understanding that default argument expressions are evaluated once, when the function is defined.
- Designing predictable function contracts and avoiding hidden shared state.

### Model answer (RU)

Python часто описывают как использующий **call by sharing** (также встречается формулировка *call by object sharing*). При вызове функции параметр становится локальным именем, связанным с тем же объектом, который передал вызывающий код. Python не копирует автоматически весь объект и не предоставляет обычную семантику C++-подобной передачи переменной по ссылке.

Из этого следуют два разных поведения:

- Если функция **изменяет объект на месте**, например вызывает `append()` у переданного списка, вызывающий код увидит изменение, потому что оба имени ссылаются на один объект.
- Если функция **переназначает параметр**, например присваивает ему новый список или целое число, меняется только локальная привязка параметра. Привязка имени в вызывающем коде не меняется.

Поэтому утверждение «изменяемые аргументы передаются по ссылке, а неизменяемые — по значению» некорректно. Механизм передачи один и тот же; различается возможность изменить сам объект. Неизменяемый объект нельзя изменить на месте, но локальное имя параметра всё равно можно переназначить.

Параметры `*args` собирают дополнительные позиционные аргументы в кортеж, а `**kwargs` — дополнительные именованные аргументы в словарь. Это новые контейнеры для собранных аргументов, но значения внутри них по-прежнему являются ссылками на соответствующие объекты. Параметры можно ограничивать позиционным или именованным способом, например с помощью `/` и `*` в сигнатуре функции.

Отдельная важная ловушка — **изменяемые значения по умолчанию**. Выражения значений по умолчанию вычисляются один раз в момент определения функции, а не при каждом вызове. Если значением по умолчанию является список или словарь и функция изменяет его, состояние сохраняется между вызовами. Это может приводить к неожиданному совместному состоянию.

Обычный безопасный подход — использовать `None` как sentinel и создавать новый контейнер внутри функции. Если `None` является допустимым значением предметной области, следует использовать отдельный sentinel-объект. Важно помнить, что `None` и другие значения по умолчанию также могут быть частью публичного контракта функции.

На Senior-уровне я объясняю это через **binding, object identity, mutation и API contract**. Я документирую, изменяет ли функция входные объекты, избегаю скрытого разделяемого состояния и выбираю сигнатуры, которые делают допустимые способы вызова явными.

### Model answer (EN)

Python is commonly described as using **call by sharing**, also known as *call by object sharing*. When a function is called, each parameter name in the function's local scope is bound to the object supplied by the caller. Python does not automatically copy the entire object, nor does it use traditional variable-level call-by-reference semantics.

This leads to two distinct cases:

- If a function **mutates an object in place**, such as calling `append()` on a passed list, the caller can observe the change because both names refer to the same object.
- If a function **rebinds its parameter**, for example by assigning a new list or integer to it, only the local parameter binding changes. The caller's variable remains bound to its original object.

Therefore, it is inaccurate to say that mutable arguments are passed by reference while immutable arguments are passed by value. The argument-passing mechanism is the same; what differs is whether the object itself can be mutated. An immutable object cannot be changed in place, but the local parameter name can still be rebound.

Extra positional arguments collected by `*args` are placed in a tuple, while extra keyword arguments collected by `**kwargs` are placed in a dictionary. These are new collection containers, but their values are still references to the corresponding objects. Function signatures can also constrain positional and keyword usage with markers such as `/` and `*`.

A common pitfall is a **mutable default argument**. Default expressions are evaluated once, when the function is defined, rather than on every call. If a list or dictionary is used as a default and mutated by the function, that state is retained across calls and can cause surprising behaviour.

A common safe pattern is to use `None` as a sentinel and create a fresh container inside the function. If `None` is itself a valid domain value, use a dedicated sentinel object instead. Default values are also part of the function's public API contract and should be chosen deliberately.

At Senior level, I explain this in terms of **name binding, object identity, mutation, and API contracts**. I make it explicit whether a function mutates caller-owned objects, avoid hidden shared state, and design signatures that communicate valid calling conventions.

### Follow-up questions and model answers

#### FU-1

**EN:** What happens if a function appends to a list argument and then reassigns the parameter to a new list?  
**RU:** Что произойдёт, если функция добавит элемент в переданный список, а затем переназначит параметр на новый список?

**Answer (RU):** Изменение исходного списка через `append()` будет видно вызывающему коду. Последующее присваивание параметру нового списка изменит только локальную привязку имени параметра. Внешняя переменная продолжит ссылаться на исходный список, уже содержащий добавленный элемент.

**Answer (EN):** The append operation mutates the original list, so the caller observes that change. Reassigning the parameter to a new list only changes the local binding. The caller's variable still refers to the original list, including the appended item.

#### FU-2

**EN:** Why are mutable default arguments dangerous, and when are defaults evaluated?  
**RU:** Почему изменяемые значения по умолчанию опасны и когда вычисляются значения по умолчанию?

**Answer (RU):** Выражение значения по умолчанию вычисляется один раз при определении функции. Поэтому один и тот же список или словарь может использоваться несколькими вызовами. Если функция изменяет его, состояние сохраняется между вызовами. Обычно используют sentinel и создают новый объект внутри функции.

**Answer (EN):** A default expression is evaluated once when the function is defined. The same list or dictionary can therefore be reused across calls. If the function mutates it, the state persists. A common solution is to use a sentinel and create a fresh object inside the function.

#### FU-3

**EN:** What exactly do `*args` and `**kwargs` collect, and are the contained objects copied?  
**RU:** Что именно собирают `*args` и `**kwargs` и копируются ли содержащиеся в них объекты?

**Answer (RU):** `*args` собирает дополнительные позиционные аргументы в кортеж, а `**kwargs` — дополнительные именованные аргументы в словарь. Создаются контейнеры для сбора аргументов, но сами переданные объекты автоматически не копируются: элементы контейнеров ссылаются на исходные объекты.

**Answer (EN):** `*args` collects extra positional arguments into a tuple, and `**kwargs` collects extra keyword arguments into a dictionary. The collection containers are created, but the supplied objects are not automatically copied; the entries refer to the original objects.

#### FU-4

**EN:** How would you use a sentinel when `None` is a valid argument value?  
**RU:** Как использовать sentinel, если `None` является допустимым значением аргумента?

**Answer (RU):** Нужно создать отдельный уникальный объект-сентинел и использовать его как значение по умолчанию. Внутри функции проверять идентичность через `is`, а не равенство. Тогда можно отличить отсутствие аргумента от явной передачи `None`.

**Answer (EN):** I would create a unique sentinel object and use it as the default. Inside the function, I would check it with `is`, not equality. This distinguishes an omitted argument from an explicit `None` value.

#### FU-5

**EN:** What is the difference between positional-only, positional-or-keyword, and keyword-only parameters?  
**RU:** Чем отличаются positional-only, positional-or-keyword и keyword-only параметры?

**Answer (RU):** Positional-only параметры можно передать только позиционно и они располагаются до `/`. Positional-or-keyword параметры допускают оба способа передачи. Keyword-only параметры должны передаваться по имени и располагаются после отдельного `*` в сигнатуре. Эти ограничения помогают сделать API яснее и сохранить совместимость при эволюции интерфейса.

**Answer (EN):** Positional-only parameters can be supplied only positionally and appear before `/`. Positional-or-keyword parameters support either calling style. Keyword-only parameters must be supplied by name and appear after a standalone `*` in the signature. These constraints make APIs clearer and can help preserve compatibility as interfaces evolve.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a service function receives search filters or a list of medication identifiers. If it mutates caller-owned input or stores request-specific data in a mutable default, one request may affect later operations. A robust implementation uses per-call state, explicit ownership and mutation contracts, and tests repeated calls to detect state leakage.

Do not claim that a particular Pharmaviyum function has this defect without inspecting its implementation.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Says Python passes mutable values by reference and immutable values by value; cannot explain mutable defaults. |
| Competent | Explains mutation versus rebinding and correctly describes `*args`, `**kwargs`, and default evaluation. |
| Strong Senior | Explains call by sharing precisely, identifies aliasing and state-leak risks, designs sentinel-based APIs, understands parameter-kind markers, and discusses compatibility and test strategy. |

### Common pitfalls

- Describing Python argument passing as a split between pass-by-reference and pass-by-value based on mutability.
- Assuming parameter reassignment changes the caller's variable.
- Assuming default expressions are evaluated on every call.
- Using a mutable list or dictionary as a default accumulator unintentionally.
- Assuming `*args` or `**kwargs` deep-copy argument values.
- Using `None` as a sentinel when `None` is a valid domain value.

### References

- Python tutorial — defining functions: https://docs.python.org/3/tutorial/controlflow.html#defining-functions
- Python FAQ — mutable default arguments: https://docs.python.org/3/faq/programming.html#why-are-default-values-shared-between-objects
- Python language reference — function definitions: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- Python glossary — call by sharing / object reference concepts: https://docs.python.org/3/glossary.html

---

## PY-CORE-004 — Names, identity, equality, and object references

> **Scope boundary:** This question owns comparison semantics: `is` versus `==`, `id()`, custom equality, and the equality/hash contract. Basic name binding and call-by-sharing are introduced in Q1 and should not be re-explained here beyond what is needed for the examples.
>
> **Граница темы:** вопрос отвечает за семантику сравнений: `is` и `==`, `id()`, пользовательское равенство и контракт equality/hash. Базовая привязка имён и call-by-sharing вводятся в Q1; здесь не нужно повторять их полностью.

### Question (EN)

**Explain the difference between object identity and equality in Python. How do name binding, aliasing, `is`, `==`, and the equality/hash contract interact?**

### Перевод (RU)

**Объясните разницу между идентичностью объекта и равенством в Python. Как связаны привязка имён, aliasing, операторы `is` и `==`, а также контракт равенства и хеширования?**

### What the interviewer evaluates

- Understanding that names are bindings to objects, not boxes that contain values.
- Distinguishing identity from value equality.
- Knowing when to use `is` and when to use `==`.
- Understanding aliasing and its consequences for mutable objects.
- Explaining the equality/hash invariant and custom `__eq__` behaviour.
- Avoiding reliance on implementation-specific identity observations.

### Model answer (RU)

В Python важно различать **имя, объект, идентичность и равенство**.

Имя — это привязка (binding) к объекту. Присваивание обычно не копирует объект, а связывает другое имя с тем же объектом. Если два имени ссылаются на один объект, возникает **aliasing**. Для изменяемых объектов это означает, что мутация через одно имя будет видна через другое.

**Идентичность (identity)** отвечает на вопрос: «Это один и тот же объект?». Оператор `is` проверяет идентичность. **Равенство (equality)** отвечает на вопрос: «Считаются ли эти объекты равными по смыслу?». Оператор `==` выполняет сравнение равенства, поведение которого может быть определено пользовательским классом через `__eq__`.

Два разных объекта могут быть равны, но не идентичны. Например, два отдельно созданных списка с одинаковыми элементами обычно удовлетворяют `a == b`, но `a is b` будет ложным. И наоборот, если `a` и `b` — два имени одного объекта, то они идентичны и обычно равны.

Практическое правило: используйте `is` для проверки идентичности с singleton-объектами, прежде всего `None`, например `value is None`. Для сравнения значений используйте `==`. Не следует использовать `is` для сравнения строк, чисел или других значений. Наблюдаемое совпадение идентичности некоторых литералов может быть следствием интернирования или оптимизаций реализации и не является корректным контрактом программы.

Встроенная функция `id()` возвращает целочисленный идентификатор, соответствующий идентичности объекта в течение времени его жизни. В CPython это обычно адрес объекта в памяти, но язык Python не гарантирует, что `id()` является адресом памяти. Идентификаторы могут повторно использоваться для объектов, время жизни которых не пересекается. Поэтому `id()` не следует применять как постоянный глобальный идентификатор или как механизм хранения ссылок.

**Контракт equality/hash** критически важен для словарей и множеств. Если два объекта сравниваются как равные, их хеши должны быть одинаковыми. Хеш объекта, находящегося в хеш-коллекции, должен оставаться стабильным. Поэтому класс, определяющий собственное равенство по изменяемым полям, должен осторожно относиться к хешированию. Если класс переопределяет `__eq__` без явного определения совместимого `__hash__`, Python обычно делает его экземпляры нехешируемыми. Нельзя проектировать `__hash__`, который зависит от состояния, меняющегося после помещения объекта в словарь или множество.

На Senior-уровне я проверяю, соответствует ли equality бизнес-семантике типа, стабильны ли поля, участвующие в сравнении и хешировании, и не создаёт ли aliasing скрытые побочные эффекты. Для идентичности использую `is`, для значения — `==`, а для ключей коллекций явно обеспечиваю контракт равенства и хеша.

### Model answer (EN)

In Python, it is important to distinguish **a name, an object, identity, and equality**.

A name is a binding to an object. Assignment usually does not copy the object; it binds another name to the same object. When two names refer to one object, we have **aliasing**. With mutable objects, a mutation made through one alias is visible through the other.

**Identity** answers: "Is this the very same object?" The `is` operator tests identity. **Equality** answers: "Are these objects considered equivalent in value or meaning?" The `==` operator performs an equality comparison, whose behaviour can be customized by a class through `__eq__`.

Two distinct objects can be equal without being identical. For example, two separately created lists with the same elements normally satisfy `a == b`, while `a is b` is false. Conversely, if `a` and `b` are two names bound to the same object, they are identical and normally equal.

As a practical rule, use `is` for identity checks against singletons, especially `None`, as in `value is None`. Use `==` for value comparisons. Do not use `is` to compare strings, numbers, or other values. Apparent identity between some literals may result from interning or implementation optimizations and is not a valid program-level guarantee.

The built-in `id()` function returns an integer identifying an object during its lifetime. In CPython, it is typically the object's memory address, but the Python language does not guarantee that `id()` is a memory address. IDs may be reused for objects whose lifetimes do not overlap. Therefore, `id()` should not be treated as a persistent global identifier or as a way to retain an object reference.

The **equality/hash contract** is essential for dictionaries and sets. If two objects compare equal, their hashes must be equal. An object's hash must remain stable while it is stored in a hash-based collection. A class that defines equality using mutable fields must therefore be careful about hashability. If a class overrides `__eq__` without explicitly providing a compatible `__hash__`, Python normally makes its instances unhashable. A hash implementation must not depend on state that can change while the object is used as a dictionary key or set member.

At Senior level, I check whether equality reflects the type's domain semantics, whether fields participating in equality and hashing are stable, and whether aliasing can introduce hidden side effects. I use `is` for identity, `==` for value equality, and enforce the equality/hash contract for objects used in hash-based collections.

### Follow-up questions and model answers

#### FU-1

**EN:** Two lists contain the same elements. What do `==` and `is` tell you, and why?  
**RU:** Два списка содержат одинаковые элементы. Что покажут `==` и `is` и почему?

**Answer (RU):** Если списки созданы отдельно, `==` обычно вернёт `True`, потому что сравнивается содержимое. `is` вернёт `False`, потому что это два разных объекта. Равенство не подразумевает идентичность.

**Answer (EN):** If the lists were created separately, `==` normally returns `True` because their contents are compared. `is` returns `False` because they are distinct objects. Equality does not imply identity.

#### FU-2

**EN:** Why should you write `value is None` instead of `value == None`?  
**RU:** Почему следует писать `value is None`, а не `value == None`?

**Answer (RU):** `None` — singleton, поэтому проверка должна выражать именно идентичность с этим объектом. `==` может вызывать пользовательский `__eq__` и иметь переопределённую семантику. Идиоматичная и однозначная проверка — `is None` или `is not None`.

**Answer (EN):** `None` is a singleton, so the check should express identity with that exact object. `==` can invoke a custom `__eq__` implementation with different semantics. The idiomatic and unambiguous check is `is None` or `is not None`.

#### FU-3

**EN:** What is aliasing, and why can it create bugs with mutable objects?  
**RU:** Что такое aliasing и почему он может приводить к ошибкам при работе с изменяемыми объектами?

**Answer (RU):** Aliasing возникает, когда несколько имён ссылаются на один объект. Мутация через любое из этих имён изменяет общий объект, поэтому другая часть программы может неожиданно увидеть изменение. Решения включают явное владение, копирование на границе владения или использование неизменяемых значений там, где это оправдано.

**Answer (EN):** Aliasing occurs when multiple names refer to the same object. A mutation through any of those names changes the shared object, so another part of the program may observe an unexpected change. Mitigations include explicit ownership, copying at ownership boundaries, or using immutable values where appropriate.

#### FU-4

**EN:** What invariant must hold between `__eq__` and `__hash__`?  
**RU:** Какой инвариант должен соблюдаться между `__eq__` и `__hash__`?

**Answer (RU):** Если `a == b`, то `hash(a) == hash(b)` должно быть истинно. Обратное не обязательно: совпадение хешей не означает равенства из-за возможных коллизий. Хеш также должен оставаться стабильным, пока объект находится в словаре или множестве.

**Answer (EN):** If `a == b`, then `hash(a) == hash(b)` must hold. The reverse is not required because hash collisions are possible. The hash must also remain stable while the object is stored in a dictionary or set.

#### FU-5

**EN:** What happens to hashability when a class overrides `__eq__` but does not define `__hash__`?  
**RU:** Что происходит с хешируемостью класса, если он переопределяет `__eq__`, но не определяет `__hash__`?

**Answer (RU):** По стандартному поведению Python такой класс становится нехешируемым: `__hash__` устанавливается в `None`. Это предотвращает случайное использование объектов с пользовательской семантикой равенства и потенциально несовместимым хешем в словарях и множествах. Если хеширование действительно требуется, нужно явно реализовать совместимый и стабильный `__hash__`.

**Answer (EN):** Under Python's standard behaviour, the class becomes unhashable: `__hash__` is set to `None`. This prevents objects with custom equality semantics and potentially incompatible hashing from being used accidentally in dictionaries and sets. If hashability is required, implement a compatible and stable `__hash__` explicitly.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** consider value objects representing medication identifiers or normalized search criteria. Equality should reflect the intended domain identity, not accidental object identity. If such objects are dictionary keys or set members, their equality and hash fields must remain stable. Shared mutable filters should also be reviewed for aliasing between request-processing stages.

Do not claim that a specific Pharmaviyum model implements these semantics without inspecting its source.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Uses `is` and `==` interchangeably; treats `id()` as a guaranteed memory address. |
| Competent | Explains identity, equality, aliasing, and why `None` is checked with `is`. |
| Strong Senior | Explains custom equality, hash invariants, mutability constraints, `__hash__ = None`, implementation portability, and domain-driven equality design. |

### Common pitfalls

- Using `is` for string, integer, or general value comparison.
- Assuming equal objects must be the same object.
- Assuming `id()` is always a memory address or a persistent identifier.
- Ignoring aliasing when sharing mutable objects across layers.
- Implementing `__hash__` inconsistently with `__eq__`.
- Hashing mutable state that can change while an object is a dictionary key or set member.

### References

- Python language reference — comparisons: https://docs.python.org/3/reference/expressions.html#comparisons
- Python data model — object identity and `id()`: https://docs.python.org/3/reference/datamodel.html
- Python data model — `__eq__` and `__hash__`: https://docs.python.org/3/reference/datamodel.html#object.__hash__
- Python glossary — hashable: https://docs.python.org/3/glossary.html#term-hashable

---

## PY-CORE-005 — Python's type system and dynamic typing

### Question (EN)

**Explain Python's type system. What do dynamic typing, strong typing, duck typing, type annotations, and structural subtyping mean, and how do you use them to build reliable backend services?**

### Перевод (RU)

**Объясните систему типов Python. Что означают динамическая типизация, строгая типизация, duck typing, аннотации типов и структурная подтипизация? Как применять эти концепции для создания надёжных backend-сервисов?**

### What the interviewer evaluates

- Distinguishing dynamic typing from strong/weak typing.
- Understanding that Python variables are names bound to objects whose types are determined at runtime.
- Understanding duck typing and behaviour-based interfaces.
- Knowing that annotations do not automatically enforce runtime validation.
- Distinguishing static analysis, runtime validation, and runtime type introspection.
- Understanding structural typing and `Protocol`.
- Choosing EAFP or LBYL based on the operation and failure semantics.

### Model answer (RU)

Python обычно характеризуют как язык с **динамической и сильной типизацией**.

**Динамическая типизация** означает, что тип относится к объекту и определяется во время выполнения. Имя переменной не имеет фиксированного типа: в разные моменты оно может быть связано с объектами разных типов. Например, имя может сначала ссылаться на строку, а позднее — на целое число. Это не означает, что типы отсутствуют или что Python автоматически преобразует любые несовместимые значения.

**Строгая типизация** означает, что Python не выполняет произвольные неявные преобразования между несовместимыми типами. Например, сложение строки и целого числа без явного преобразования приводит к `TypeError`. Термины strong и weak typing не имеют единственного формального определения для всех языков, поэтому на интервью важно приводить конкретное поведение, а не полагаться только на ярлык.

**Duck typing** — подход, при котором код ориентируется на поддерживаемое объектом поведение, а не обязательно на его конкретный класс или место в иерархии наследования. Если объект предоставляет нужный метод или операцию с ожидаемым контрактом, он может быть использован. Это способствует слабой связанности, но требует чётко определять ожидаемое поведение и корректно обрабатывать ошибки.

**Аннотации типов** (type annotations) описывают предполагаемые типы параметров, возвращаемых значений и переменных. Сами по себе они обычно не обеспечивают проверку типов во время выполнения. Их используют IDE, инструменты статического анализа, такие как mypy и Pyright, и другие инструменты экосистемы. Аннотации улучшают читаемость, навигацию и раннее обнаружение ошибок, но не заменяют тесты и проверку входных данных.

Нужно различать три механизма:

1. **Static type checking** анализирует код до выполнения и выявляет несоответствия в рамках возможностей выбранного анализатора и конфигурации.
2. **Runtime validation** проверяет реальные данные во время выполнения. Например, Pydantic может валидировать и, в зависимости от конфигурации и режима, преобразовывать входные данные при создании модели.
3. **Runtime introspection** позволяет исследовать фактические типы и объекты во время выполнения, например через `type()` или `isinstance()`. Само наличие аннотации не означает, что такая проверка автоматически происходит.

**Structural subtyping** означает совместимость по структуре и поведению, а не только по явному наследованию. В Python typing для этого предоставляет `Protocol`. Тип может соответствовать протоколу, если реализует требуемые атрибуты и методы, даже без прямого наследования от этого протокола. Это позволяет описывать интерфейсы и зависимости без жёсткой связи с конкретными реализациями. `@runtime_checkable` позволяет ограниченные runtime-проверки через `isinstance()`, но не превращает Protocol в полноценный runtime-валидатор сигнатур и семантики методов.

**EAFP** (Easier to Ask Forgiveness than Permission) — сначала выполнить операцию, затем обработать ожидаемое исключение. **LBYL** (Look Before You Leap) — предварительно проверить условие перед операцией. EAFP часто уместен при работе со словарями, файлами и ресурсами, когда сама операция является надёжной проверкой и исключение имеет понятную семантику. LBYL полезен, когда предварительная проверка необходима для понятного пользовательского сообщения или предотвращает дорогостоящую операцию. При этом проверка, а затем действие могут создавать race condition, если состояние меняется между ними.

В backend-сервисе я использую аннотации для контрактов между слоями, статический анализ в CI, runtime-валидацию на границах системы и тесты для проверки поведения. Например, FastAPI использует аннотации и модели для описания API, а Pydantic валидирует данные согласно объявленной схеме и конфигурации. Я не считаю аннотации безопасности или гарантией корректности входных данных: доверие к внешнему запросу должно устанавливаться явной runtime-валидацией и авторизацией.

### Model answer (EN)

Python is commonly described as a **dynamically and strongly typed** language.

**Dynamic typing** means that types belong to objects and are determined at runtime. A variable name does not have a permanently fixed type; it can be bound to objects of different types at different points in the program. For example, a name may refer to a string and later be rebound to an integer. This does not mean that types are absent or that Python freely converts incompatible values.

**Strong typing** means that Python does not perform arbitrary implicit conversions between incompatible types. For example, adding a string to an integer without an explicit conversion raises `TypeError`. The terms strong and weak typing do not have one universally accepted formal definition across all languages, so a good interview answer should explain concrete behaviour rather than rely only on labels.

**Duck typing** is an approach in which code depends on the behaviour an object provides rather than necessarily on its concrete class or inheritance hierarchy. If an object supports the required operation or method with the expected contract, it can be used. This can reduce coupling, but the expected behaviour must be well defined and failures must be handled deliberately.

**Type annotations** describe the intended types of parameters, return values, and variables. By themselves, annotations generally do not enforce type checking at runtime. They are consumed by IDEs, static analysis tools such as mypy and Pyright, and other ecosystem tooling. Annotations improve readability, navigation, and early error detection, but they do not replace tests or input validation.

It is important to distinguish three mechanisms:

1. **Static type checking** analyses code before execution and detects inconsistencies within the capabilities and configuration of the selected checker.
2. **Runtime validation** checks actual data while the program is running. For example, Pydantic can validate and, depending on configuration and mode, coerce input data when a model is created.
3. **Runtime introspection** examines actual objects and types at runtime, for example with `type()` or `isinstance()`. The presence of an annotation does not itself trigger such a check.

**Structural subtyping** means compatibility based on structure and behaviour rather than explicit inheritance alone. Python's typing system provides `Protocol` for this purpose. A type can satisfy a protocol by implementing its required attributes and methods without explicitly inheriting from that protocol. This lets us describe interfaces and dependencies without coupling consumers to concrete implementations. `@runtime_checkable` enables limited runtime checks through `isinstance()`, but it does not turn a Protocol into a full runtime validator of method signatures and semantics.

**EAFP** (Easier to Ask Forgiveness than Permission) means attempting an operation and handling an expected exception. **LBYL** (Look Before You Leap) means checking a condition before performing the operation. EAFP is often appropriate for dictionary access, files, and resources when the operation itself is a reliable check and the exception has clear semantics. LBYL can be useful when a precondition is needed to produce a clear user-facing error or avoid an expensive operation. However, a check followed by an action can introduce a race condition if the state changes between the two.

In a backend service, I use annotations to express contracts between layers, static analysis in CI, runtime validation at system boundaries, and tests to verify behaviour. For example, FastAPI uses annotations and models to describe API contracts, while Pydantic validates data according to the declared schema and configuration. I do not treat annotations as a security boundary or a guarantee that incoming data is valid: external input must be explicitly validated at runtime and separately authorized.

### Version-aware annotation semantics (Python 3.14+)

**RU:** Аннотации не являются runtime-валидацией, однако способ их вычисления зависит от версии Python. В Python 3.13 и более ранних версиях стандартное поведение вычисляло аннотации при определении объекта; `from __future__ import annotations` сохранял их как строки. Начиная с Python 3.14, стандартное поведение — отложенное вычисление аннотаций (PEP 649/749). Это меняет момент возможного разрешения имён и поведение кода, который читает `__annotations__`. Для совместимого кода, который интроспектирует аннотации, следует использовать документированный API `annotationlib` и явно учитывать минимальную поддерживаемую версию Python. Ни один из этих режимов не заставляет интерпретатор проверять фактические аргументы функции.

**EN:** Annotation evaluation is version-dependent even though annotations are not runtime validation. Python 3.13 and earlier use eager evaluation by default; `from __future__ import annotations` stores them as strings. Starting with Python 3.14, deferred evaluation is the default (PEP 649/749). This changes when names may be resolved and affects code that reads `__annotations__`. Cross-version introspection should use the documented `annotationlib` API where available and account for the project's minimum Python version. None of these modes makes the interpreter validate actual function arguments.

### Follow-up questions and model answers

#### FU-1

**EN:** Is Python dynamically typed, strongly typed, or both? Explain with an example.  
**RU:** Python — динамически типизированный, строго типизированный язык или и то и другое? Объясните на примере.

**Answer (RU):** Обычно Python описывают как динамически и строго типизированный. Динамичность означает, что тип объекта определяется во время выполнения, а имя может быть связано с объектами разных типов. Строгость проявляется, например, в том, что операция сложения строки и целого числа без явного преобразования вызывает `TypeError`. Термины strong/weak требуют контекста, поэтому важнее объяснить фактическое поведение.

**Answer (EN):** Python is commonly described as both dynamically and strongly typed. Dynamic typing means an object's type is determined at runtime and a name can be rebound to objects of different types. Strong typing is illustrated by operations such as adding a string and an integer without explicit conversion raising `TypeError`. Since strong/weak terminology depends on context, explaining the actual behaviour is more useful than relying on the label.

#### FU-2

**EN:** Do Python type annotations validate untrusted HTTP request data at runtime?  
**RU:** Проверяют ли аннотации типов Python недоверенные данные HTTP-запроса во время выполнения?

**Answer (RU):** Нет, сами по себе — нет. Аннотации в первую очередь служат описанием типов и входом для статических анализаторов и инструментов. Для внешних данных нужна runtime-валидация, например через Pydantic-модели в соответствующей точке приложения. Валидация также не заменяет авторизацию и проверку бизнес-правил.

**Answer (EN):** No, not by themselves. Annotations primarily describe types and provide input to static analyzers and tooling. External data requires runtime validation, for example through Pydantic models at the appropriate application boundary. Validation also does not replace authorization or business-rule checks.

#### FU-3

**EN:** What is the difference between duck typing and a typing `Protocol`?  
**RU:** В чём разница между duck typing и `Protocol` из модуля typing?

**Answer (RU):** Duck typing — прежде всего runtime-подход: код использует объект на основании поддерживаемого поведения. `Protocol` формализует ожидаемую структуру для статической проверки типов и документирования интерфейса. Эти подходы совместимы: реализация может соответствовать протоколу структурно, без явного наследования. Обычная статическая совместимость с Protocol не означает автоматической runtime-валидации.

**Answer (EN):** Duck typing is primarily a runtime approach: code uses an object based on the behaviour it supports. A `Protocol` formalizes the expected structure for static type checking and interface documentation. The approaches are compatible: an implementation can satisfy a protocol structurally without explicit inheritance. Static compatibility with a Protocol does not imply automatic runtime validation.

#### FU-4

**EN:** When would you choose EAFP over LBYL, and what concurrency concern should you consider?  
**RU:** Когда вы выберете EAFP вместо LBYL и какой concurrency-риск нужно учитывать?

**Answer (RU):** EAFP подходит, когда операция сама надёжно проверяет условие и ожидаемое исключение можно обработать локально, например при чтении ключа словаря. LBYL полезен для предварительной проверки и более понятного сообщения об ошибке. Но между проверкой и действием состояние может измениться: это TOCTOU race condition. Если операция должна быть атомарной, предпочтительнее использовать атомарную операцию или синхронизацию.

**Answer (EN):** EAFP is appropriate when the operation itself reliably tests the condition and the expected exception can be handled locally, such as dictionary key access. LBYL can help with precondition checks and clearer error messages. However, state may change between the check and the action, creating a time-of-check-to-time-of-use race. If the operation must be atomic, prefer an atomic operation or synchronization.

#### FU-5

**EN:** What does `@runtime_checkable` add to a `Protocol`, and what does it not guarantee?  
**RU:** Что даёт декоратор `@runtime_checkable` протоколу `Protocol` и чего он не гарантирует?

**Answer (RU):** Он позволяет выполнять ограниченную проверку соответствия протоколу во время выполнения через `isinstance()`. Такая проверка ориентирована на наличие требуемых атрибутов, а не на полноценную проверку типов параметров, возвращаемых значений или семантики методов. Поэтому она не заменяет статический анализ, runtime-валидацию данных или тестирование контракта.

**Answer (EN):** It enables a limited runtime protocol check through `isinstance()`. The check focuses on the presence of required attributes rather than fully validating parameter types, return types, or method semantics. It therefore does not replace static analysis, runtime data validation, or contract testing.

### Pharmaviyum connection

**Implemented stack context:** Pharmaviyum uses FastAPI, Pydantic, and SQLModel in its documented application stack. The following is an architectural application of those technologies, not a claim that every example is already implemented.

At an API boundary, request models can define and validate incoming data. Type annotations can make service contracts explicit, while static analysis can detect mismatches across modules. Protocols can help define ports for external services or infrastructure adapters without binding business logic to one concrete implementation. Authorization and domain invariants must remain explicit; a value passing schema validation does not automatically make the operation permitted or clinically valid.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Claims annotations enforce runtime types; confuses dynamic typing with absence of types. |
| Competent | Explains dynamic and strong typing, duck typing, and the distinction between annotations and validation. |
| Strong Senior | Separates static analysis, runtime validation, and introspection; uses Protocols deliberately; evaluates EAFP/LBYL, race conditions, and trust boundaries. |

### Common pitfalls

- Saying Python is weakly typed merely because it is dynamically typed.
- Treating type annotations as automatic runtime validation.
- Assuming `isinstance()` or `@runtime_checkable` fully verifies a protocol contract.
- Using concrete inheritance checks where behaviour-based contracts would reduce coupling.
- Catching broad exceptions in EAFP and hiding programming errors.
- Assuming an LBYL check guarantees that the subsequent operation will still be valid.
- Treating schema validation as authorization or domain-level validation.

### References

- Python typing documentation: https://docs.python.org/3/library/typing.html
- Python typing — Protocols: https://docs.python.org/3/library/typing.html#typing.Protocol
- Python function annotations: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- mypy documentation: https://mypy.readthedocs.io/
- Pyright documentation: https://github.com/microsoft/pyright
- Pydantic documentation: https://docs.pydantic.dev/
- Python glossary — duck typing: https://docs.python.org/3/glossary.html#term-duck-typing

---

## PY-CORE-006 — Python's data model and special methods

### Question (EN)

**Explain Python's data model and the role of special methods (dunder methods). How does Python use them to provide object construction, representation, iteration, operators, truth testing, and context management?**

### Перевод (RU)

**Объясните модель данных Python и роль специальных методов (dunder methods). Как Python использует их для создания объектов, представления, итерации, операторов, проверки истинности и управления контекстом?**

### What the interviewer evaluates

- Understanding that special methods implement protocols integrated into the language.
- Distinguishing object creation via `__new__` from initialization via `__init__`.
- Knowing why special-method lookup may bypass ordinary instance attribute lookup.
- Designing useful `__repr__` and `__str__` implementations.
- Understanding iteration and container protocols.
- Understanding truth-value testing and operator overloading.
- Correctly implementing context-manager cleanup and exception propagation.
- Avoiding surprising or inconsistent behaviour in custom classes.

### Model answer (RU)

**Python Data Model** — это набор соглашений и протоколов, через которые пользовательские объекты интегрируются с синтаксисом и встроенными операциями языка. Специальные методы, обычно называемые dunder methods из-за двойного подчёркивания в именах, позволяют объектам вести себя как последовательности, итераторы, контекстные менеджеры, числовые типы и другие встроенные абстракции.

Эти методы не следует воспринимать как произвольные callback-функции. Интерпретатор вызывает их в определённых ситуациях: например, `len(obj)` связан с `__len__`, оператор `+` — с протоколом арифметических операций, а конструкция `with` — с протоколом context manager. Для специальных операций поиск специальных методов обычно выполняется на уровне типа, а не как обычный поиск атрибута экземпляра. Поэтому присваивание `obj.__len__` не является надёжным способом изменить поведение `len(obj)`.

**Создание и инициализация объекта:**

- `__new__(cls, ...)` отвечает за создание и возвращение экземпляра. Это метод уровня класса, который обычно нужен при наследовании от неизменяемых типов, контроле создания экземпляров или реализации специальных паттернов.
- `__init__(self, ...)` инициализирует уже созданный экземпляр и должен вернуть `None`. Он не создаёт объект и не может заменить его другим объектом.

Обычный вызов класса проходит через механизм создания экземпляра, который вызывает `__new__`, а затем, если возвращён экземпляр соответствующего класса, вызывает `__init__`. В повседневном коде чаще всего достаточно определить `__init__`.

**Представление объекта:**

- `__repr__` предназначен прежде всего для разработчика: полезное, однозначное представление для отладки. В идеале оно позволяет восстановить объект, если это разумно и возможно.
- `__str__` предназначен для удобного отображения пользователю.
- Если `__str__` не определён, Python обычно использует `__repr__` как fallback.

Представления должны быть информативными и не должны раскрывать секреты, токены или персональные данные.

**Протоколы контейнеров и итерации:**

- `__len__` возвращает неотрицательное целое число, описывающее размер объекта.
- `__iter__` возвращает итератор.
- `__next__` возвращает следующий элемент, а при завершении итерации выбрасывает `StopIteration`.
- `__getitem__` может реализовать доступ по индексу или ключу и участвовать в поведении пользовательского контейнера.

Итерируемый объект и итератор — не одно и то же. Iterable предоставляет итератор через `iter(obj)`; iterator хранит состояние обхода, возвращает себя из `__iter__` и реализует `__next__`. Итератор обычно исчерпывается после завершения. Реализация `__getitem__` с последовательной индексацией исторически может позволить итерацию как fallback, но для ясного контракта лучше явно реализовать соответствующий протокол.

**Truth-value testing** использует `__bool__`, если он определён; иначе для пользовательского объекта может использоваться `__len__`. Если оба отсутствуют, экземпляр по умолчанию считается истинным. `__bool__` должен возвращать именно `True` или `False`. Не следует делать truthiness неоднозначной, например для объектов, представляющих набор значений, где «истинность» не имеет очевидного смысла.

**Operator overloading** позволяет определить поведение операций через специальные методы, например `__add__`, `__eq__` и их reflected/in-place варианты. Если операция для данного типа не поддерживается, метод может вернуть `NotImplemented`, чтобы Python мог попробовать альтернативный dispatch, например reflected method другого операнда. Это отличается от выбрасывания `NotImplementedError`, который является исключением. Операторы должны соответствовать ожидаемой математической или доменной семантике, а не удивлять потребителей.

**Context managers** реализуют `__enter__` и `__exit__`. `__enter__` возвращает значение, которое связывается с переменной после `as`. `__exit__` вызывается при нормальном завершении блока и при исключении; при исключении он получает сведения об исключении. Если `__exit__` возвращает truthy value, исключение подавляется; иначе оно распространяется дальше. Очистка ресурсов должна быть надёжной и выполняться даже при ошибках внутри блока. Для асинхронного управления контекстом существуют `__aenter__` и `__aexit__`.

На Senior-уровне важно не просто перечислить dunder methods, а объяснить, какой протокол нужен типу, какие инварианты он обязан соблюдать и как избежать неожиданного поведения. Я реализую только те протоколы, которые отражают реальный контракт объекта, и тестирую их граничные случаи: пустое значение, исчерпание итератора, неподдерживаемые операции и исключения при освобождении ресурсов.

### Model answer (EN)

The **Python Data Model** is a set of conventions and protocols through which user-defined objects integrate with the language's syntax and built-in operations. Special methods, commonly called dunder methods because of their double-underscore names, allow objects to behave like sequences, iterators, context managers, numeric types, and other built-in abstractions.

These methods are not arbitrary callbacks. The interpreter invokes them in defined situations: for example, `len(obj)` is associated with `__len__`, the `+` operator uses the arithmetic protocol, and the `with` statement uses the context-manager protocol. For special operations, special-method lookup generally happens on the type rather than through ordinary instance attribute lookup. Therefore, assigning `obj.__len__` is not a reliable way to change the behaviour of `len(obj)`.

**Object creation and initialization:**

- `__new__(cls, ...)` is responsible for creating and returning an instance. It is a class-level method and is commonly relevant when subclassing immutable types, controlling instance creation, or implementing specialized construction patterns.
- `__init__(self, ...)` initializes an instance that has already been created and must return `None`. It does not create the object and cannot replace it with another object.

A normal class call goes through the instance-creation machinery, which calls `__new__` and then, if an instance of the appropriate class is returned, calls `__init__`. In everyday code, defining `__init__` is usually sufficient.

**Object representation:**

- `__repr__` is primarily for developers: a useful, ideally unambiguous representation for debugging. Where reasonable and possible, it may be designed so that it can recreate the object.
- `__str__` is intended for a user-friendly display.
- If `__str__` is not defined, Python normally falls back to `__repr__`.

Representations should be informative and must not expose secrets, tokens, or personal data.

**Container and iteration protocols:**

- `__len__` returns a non-negative integer describing the object's size.
- `__iter__` returns an iterator.
- `__next__` returns the next item and raises `StopIteration` when iteration is exhausted.
- `__getitem__` can implement indexed or keyed access and can participate in the behaviour of a custom container.

An iterable and an iterator are not the same thing. An iterable provides an iterator through `iter(obj)`; an iterator maintains traversal state, returns itself from `__iter__`, and implements `__next__`. An iterator is normally exhausted after completion. A legacy sequence-style `__getitem__` implementation can also enable iteration as a fallback, but explicitly implementing the intended protocol gives a clearer contract.

**Truth-value testing** uses `__bool__` when it is defined; otherwise, for a user-defined object, Python may use `__len__`. If neither exists, an instance is true by default. `__bool__` must return exactly `True` or `False`. Avoid ambiguous truthiness for objects such as multi-value containers when there is no obvious meaning of "truth".

**Operator overloading** defines operation behaviour through special methods such as `__add__`, `__eq__`, and their reflected or in-place variants. If an operation is unsupported for a particular type, a method can return `NotImplemented`, allowing Python to try alternative dispatch, such as the other operand's reflected method. This is different from raising `NotImplementedError`, which is an exception. Operators should follow expected mathematical or domain semantics rather than surprise callers.

**Context managers** implement `__enter__` and `__exit__`. `__enter__` returns the value bound to the variable after `as`. `__exit__` is called when the block finishes normally and when an exception occurs; in the latter case it receives exception information. If `__exit__` returns a truthy value, the exception is suppressed; otherwise, it propagates. Resource cleanup must be reliable even when the block fails. Asynchronous context management uses `__aenter__` and `__aexit__`.

At Senior level, it is not enough to list dunder methods. I explain which protocol a type needs, which invariants it must preserve, and how to avoid surprising behaviour. I implement only protocols that reflect the object's actual contract and test edge cases such as empty values, exhausted iterators, unsupported operations, and exceptions during resource cleanup.

### Additional language semantics: expressions and structural pattern matching

**RU:** Корректная работа с выражениями требует понимать precedence и associativity операторов, порядок вычисления операндов, short-circuit поведение `and` и `or`, chained comparisons и conditional expressions. `and` и `or` возвращают один из операндов, а не обязательно `bool`. Вызовы функций и другие выражения с побочными эффектами нельзя переставлять, не проверив порядок вычисления. Assignment expression `:=` связывает результат выражения с именем, но не отменяет правила области видимости. Structural pattern matching через `match`/`case` поддерживает sequence, mapping, class, OR и guarded patterns; guard выполняется после успешного сопоставления шаблона. Pattern matching выбирает ветвь управления потоком, но не является полной проверкой схемы, доверия к данным или прав доступа.

**EN:** Reliable expression reasoning requires understanding operator precedence and associativity, operand evaluation order, short-circuit behaviour of `and` and `or`, chained comparisons, and conditional expressions. `and` and `or` return one of their operands, not necessarily a `bool`. Expressions with side effects must not be reordered without considering evaluation order. The assignment expression `:=` binds an expression result to a name but does not remove scope rules. Structural pattern matching with `match`/`case` supports sequence, mapping, class, OR, and guarded patterns; a guard runs after its pattern succeeds. Pattern matching selects control flow; it is not a complete schema validator, trust boundary, or authorization check.

**References:** Python Expressions — https://docs.python.org/3.14/reference/expressions.html ; Compound Statements — https://docs.python.org/3.14/reference/compound_stmts.html

### Follow-up questions and model answers

#### FU-1

**EN:** What is the difference between `__new__` and `__init__`?  
**RU:** В чём разница между `__new__` и `__init__`?

**Answer (RU):** `__new__` создаёт и возвращает экземпляр, а `__init__` инициализирует уже созданный экземпляр и возвращает `None`. `__new__` особенно важен для неизменяемых типов и нестандартного контроля создания объектов. В обычных классах чаще достаточно `__init__`.

**Answer (EN):** `__new__` creates and returns an instance, while `__init__` initializes an already-created instance and returns `None`. `__new__` is particularly relevant for immutable types and specialized instance-creation control. For ordinary classes, `__init__` is usually sufficient.

#### FU-2

**EN:** Why might assigning `obj.__len__` not affect the result of `len(obj)`?  
**RU:** Почему присваивание `obj.__len__` может не повлиять на результат `len(obj)`?

**Answer (RU):** Специальные методы для неявных языковых операций обычно ищутся на уровне типа, а не через обычный поиск атрибутов экземпляра. Поэтому изменение одноимённого атрибута конкретного экземпляра не обязано менять поведение встроенной операции. Протокол следует реализовывать в классе.

**Answer (EN):** Special methods used by implicit language operations are generally looked up on the type rather than through ordinary instance attribute lookup. Changing a same-named attribute on one instance therefore does not necessarily change the built-in operation. The protocol should be implemented on the class.

#### FU-3

**EN:** What is the difference between an iterable and an iterator?  
**RU:** Чем iterable отличается от iterator?

**Answer (RU):** Iterable предоставляет итератор через `__iter__`. Iterator реализует `__next__`, хранит состояние обхода и обычно возвращает себя из `__iter__`. Один iterable может создавать несколько независимых итераторов, тогда как конкретный iterator обычно потребляется по мере обхода.

**Answer (EN):** An iterable provides an iterator through `__iter__`. An iterator implements `__next__`, maintains traversal state, and normally returns itself from `__iter__`. One iterable can create multiple independent iterators, while a particular iterator is usually consumed as it is traversed.

#### FU-4

**EN:** What is the difference between returning `NotImplemented` and raising `NotImplementedError` in an overloaded operator?  
**RU:** В чём разница между возвратом `NotImplemented` и выбрасыванием `NotImplementedError` в перегруженном операторе?

**Answer (RU):** `NotImplemented` — специальное значение, сообщающее механизму диспетчеризации Python, что данный операнд не поддерживает эту операцию; интерпретатор может попробовать reflected-метод второго операнда. `NotImplementedError` — обычное исключение, сигнализирующее, что реализация не выполнена. Для неподдерживаемого сочетания типов в operator overloading обычно используют `NotImplemented`, а не исключение.

**Answer (EN):** `NotImplemented` is a special value telling Python's dispatch machinery that this operand does not support the operation; the interpreter may try the other operand's reflected method. `NotImplementedError` is an exception indicating that an implementation has not been provided. For an unsupported operand combination in operator overloading, returning `NotImplemented` is normally appropriate.

#### FU-5

**EN:** When does a context manager suppress an exception?  
**RU:** В каком случае context manager подавляет исключение?

**Answer (RU):** Если исключение возникло внутри блока `with`, Python передаёт сведения о нём в `__exit__`. Если `__exit__` возвращает truthy value, исключение подавляется; если возвращает falsey value или `None`, исключение продолжает распространяться. Подавлять исключения следует только тогда, когда это явно соответствует контракту контекстного менеджера.

**Answer (EN):** If an exception occurs inside a `with` block, Python passes its details to `__exit__`. If `__exit__` returns a truthy value, the exception is suppressed; if it returns a falsey value or `None`, the exception propagates. Exceptions should be suppressed only when that behaviour is explicitly part of the context manager's contract.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a database session or external-resource adapter may expose context-manager semantics so that acquisition and cleanup are explicit and exception-safe. A medication collection or search-result object may implement iteration and length protocols if those behaviours are part of its public contract. Its representation should be useful for diagnostics while excluding patient information, credentials, and other sensitive values.

Do not claim that a particular Pharmaviyum class implements these protocols without inspecting its source.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Lists dunder methods but confuses object creation with initialization or `NotImplemented` with `NotImplementedError`. |
| Competent | Explains construction, representation, iteration, truthiness, operators, and context managers correctly. |
| Strong Senior | Explains protocol dispatch, invariants, iterator state, exception suppression, resource safety, and secure representations; chooses protocols based on explicit API contracts. |

### Common pitfalls

- Returning a non-`None` value from `__init__`.
- Using `__init__` when custom object creation requires `__new__`.
- Assuming special-method lookup always uses the instance dictionary.
- Returning a negative or non-integer value from `__len__`.
- Confusing an iterable with its iterator.
- Raising `StopIteration` before the iterator is exhausted or failing to raise it at exhaustion.
- Raising `NotImplementedError` instead of returning `NotImplemented` for unsupported operator dispatch.
- Accidentally suppressing exceptions in `__exit__`.
- Exposing secrets or personal data in `__repr__` or `__str__`.

### References

- Python data model: https://docs.python.org/3/reference/datamodel.html
- Python built-in functions — `len()`, `iter()`, `next()`: https://docs.python.org/3/library/functions.html
- Iterator types: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Context manager types: https://docs.python.org/3/library/stdtypes.html#typecontextmanager
- PEP 343 — The "with" statement: https://peps.python.org/pep-0343/

---

## PY-CORE-007 — Python scope, the LEGB rule, closures, and namespaces

### Question (EN)

**Explain how Python resolves names. Describe the LEGB rule, the roles of `global` and `nonlocal`, how closures retain state, and why late binding can cause bugs.**

### Перевод (RU)

**Объясните, как Python разрешает имена. Расскажите о правиле LEGB, назначении `global` и `nonlocal`, о том, как closures сохраняют состояние, и почему late binding может приводить к ошибкам.**

### What the interviewer evaluates

- Accurate understanding of namespaces versus scopes.
- Ability to explain LEGB lookup order and built-in fallback.
- Understanding that assignment affects compile-time scope classification within a function.
- Correct distinction between `global` and `nonlocal`.
- Understanding closure cells and lexical scoping.
- Ability to diagnose `UnboundLocalError` and late-binding behaviour.
- Awareness of decorator and nested-function implications.
- Ability to design predictable, testable code without accidental shared state.

### Model answer (RU)

В Python **namespace** — это отображение имён на объекты, а **scope** — область программы, в которой имя доступно при разрешении. Эти понятия связаны, но не тождественны: namespace хранит bindings, а scope определяет правила доступа к ним.

Для обычного разрешения имён в функции используется правило **LEGB**:

1. **Local** — локальные имена текущей функции.
2. **Enclosing** — имена во внешних охватывающих функциях, если функция вложенная.
3. **Global** — имена на уровне модуля, в котором определена функция.
4. **Built-in** — встроенные имена, например `len`, `str`, `Exception`.

Поиск идёт от ближайшей области к более внешней. Global здесь означает namespace модуля, а не глобальное пространство всего процесса. Если имя не найдено ни в одной области, возникает `NameError`.

**Важная особенность: локальная классификация имён.** Внутри функции, если имя где-либо связывается присваиванием, Python обычно классифицирует его как локальное во всей функции, если не указаны `global` или `nonlocal`. Поэтому попытка сначала прочитать такое имя до присваивания приводит к `UnboundLocalError`, даже если существует одноимённое имя на уровне модуля. Это не обычный случай отсутствующего имени: `UnboundLocalError` является подклассом `NameError` и указывает на проблему доступа к локальной переменной до её связывания.

`global` сообщает, что присваивание имени внутри функции должно относиться к namespace текущего модуля. Это не означает, что значение становится глобальным для всех модулей или потоков.

`nonlocal` указывает, что имя относится к ближайшей охватывающей функциональной области, в которой оно уже существует. Оно используется во вложенных функциях для изменения binding во внешней функции. `nonlocal` не обращается к namespace модуля и не создаёт имя в enclosing scope, если подходящего binding там нет.

**Closures** возникают, когда вложенная функция использует имя из enclosing scope и сохраняет доступ к этому binding после завершения внешнего вызова. Python сохраняет необходимое состояние через closure cells. Closure захватывает не обязательно неизменяемую копию значения, а доступ к binding. Поэтому изменение binding через `nonlocal` может быть видно последующим вызовам замыкания. Если захваченный объект mutable, его внутреннее состояние также может изменяться.

**Late binding** означает, что замыкание обычно разрешает захваченное имя при выполнении функции, а не фиксирует текущее значение в момент создания функции. Классический случай — создание функций в цикле: все функции могут обратиться к одному и тому же имени цикла и увидеть его итоговое значение при последующем вызове. Один из вариантов решения — явно передать значение через аргумент функции с default value, но это нужно применять осознанно: default expressions вычисляются один раз при определении функции. Другие варианты — фабрика функций или отдельная функция-обёртка, создающая собственную enclosing scope для каждой итерации.

**Decorators** используют те же правила областей видимости. Функция-декоратор часто возвращает вложенную wrapper-функцию, которая замыкает исходную функцию и параметры конфигурации. Нужно следить за тем, какие bindings разделяются между вызовами, и сохранять метаданные обёрнутой функции, обычно через `functools.wraps`. Если wrapper хранит изменяемое состояние в closure, это состояние может разделяться между всеми вызовами данного wrapper.

Также важно не путать правила scope функций с особенностями других конструкций. Например, comprehension в Python 3 имеет собственную область видимости для переменной цикла, а тело класса не является обычной enclosing function scope для методов: имя, объявленное в теле класса, не становится автоматически лексической переменной метода.

На Senior-уровне я объясняю не только порядок LEGB, но и последствия для состояния, конкурентного выполнения, тестируемости и API. Я избегаю неявных глобальных зависимостей, делаю конфигурацию явной, а изменяемое состояние храню в объекте с понятным жизненным циклом или передаю через зависимости. Для closure и decorator пишу тесты на повторные вызовы, независимость экземпляров и поведение при изменении захваченного состояния.

### Model answer (EN)

In Python, a **namespace** is a mapping from names to objects, while a **scope** is the region of a program where a name can be accessed through name resolution. They are related but not identical: a namespace stores bindings, while scope determines the rules used to access them.

For ordinary name resolution inside a function, Python follows **LEGB**:

1. **Local** — names in the current function.
2. **Enclosing** — names in surrounding function scopes when functions are nested.
3. **Global** — names in the module where the function was defined.
4. **Built-in** — built-in names such as `len`, `str`, and `Exception`.

Lookup proceeds from the nearest applicable scope outward. Here, global means the module namespace, not a process-wide global namespace. If a name cannot be found, Python raises `NameError`.

**An important detail is local-name classification.** If a name is bound by an assignment anywhere in a function, Python generally classifies it as local throughout that function unless `global` or `nonlocal` declares otherwise. Reading that name before the assignment therefore raises `UnboundLocalError`, even if a module-level name with the same spelling exists. This is not simply a missing-name case: `UnboundLocalError` is a subclass of `NameError` and indicates access to a local variable before it has been bound.

`global` declares that assignments to a name in the function refer to the current module's namespace. It does not make the value global to every module or thread in the process.

`nonlocal` declares that a name refers to the nearest enclosing function scope where that name is already bound. It allows a nested function to rebind a name in an outer function. It does not refer to the module namespace, and it cannot create a name in an enclosing scope where no suitable binding exists.

A **closure** occurs when a nested function uses a name from an enclosing scope and retains access to that binding after the outer call has returned. Python preserves the required state through closure cells. A closure does not necessarily capture an immutable snapshot of a value; it retains access to a binding. Rebinding it through `nonlocal` can therefore be observed by later calls. If the captured object is mutable, its internal state can also change.

**Late binding** means that a closure normally resolves a captured name when the function executes, rather than freezing its current value when the function is created. A classic example is creating functions in a loop: all functions may refer to the same loop variable and observe its final value when called later. One solution is to pass the current value through a function parameter with a default value, but this should be used deliberately because default expressions are evaluated once when the function is defined. Other solutions include a function factory or wrapper that creates a separate enclosing scope for each iteration.

**Decorators** follow the same scope rules. A decorator often returns a nested wrapper function that closes over the original function and configuration parameters. It is important to understand which bindings are shared across calls and to preserve wrapped-function metadata, commonly with `functools.wraps`. If a wrapper stores mutable state in a closure, that state may be shared by every call to that wrapper.

Do not confuse function-scope rules with the behaviour of other constructs. For example, in Python 3 a comprehension has its own scope for its iteration variable. A class body is also not an ordinary enclosing function scope for methods: a name defined in a class body does not automatically become a lexical variable inside a method.

At Senior level, I explain not only LEGB lookup but also its consequences for state, concurrent execution, testability, and API design. I avoid implicit global dependencies, make configuration explicit, and keep mutable state in objects with clear lifecycles or pass it through dependencies. For closures and decorators, I test repeated calls, instance independence, and behaviour when captured state changes.

### Follow-up questions and model answers

#### FU-1

**EN:** Why can reading a module-level variable inside a function raise `UnboundLocalError` if the function assigns to the same name later?  
**RU:** Почему чтение переменной уровня модуля внутри функции может вызвать `UnboundLocalError`, если позднее в этой функции выполняется присваивание тому же имени?

**Answer (RU):** Наличие присваивания имени внутри функции обычно приводит к тому, что Python классифицирует это имя как локальное во всей функции на этапе анализа кода. Поэтому чтение до локального присваивания обращается к ещё не связанному локальному имени, а не к одноимённому имени модуля. Если намерение действительно состоит в изменении module-level binding, требуется декларация `global`; чаще лучше передать значение явно.

**Answer (EN):** An assignment to a name anywhere in a function generally causes Python to classify that name as local throughout the function during code analysis. A read before the local assignment therefore accesses an unbound local name rather than the same-named module variable. If changing the module-level binding is truly intended, `global` is required; explicit parameter passing is often a better design.

#### FU-2

**EN:** What is the difference between `global` and `nonlocal`?  
**RU:** В чём разница между `global` и `nonlocal`?

**Answer (RU):** `global` направляет присваивание в namespace текущего модуля. `nonlocal` направляет его в ближайшую enclosing function scope, где имя уже связано. `nonlocal` применяется к вложенным функциям и не работает как способ изменить переменную модуля.

**Answer (EN):** `global` directs assignment to the current module namespace. `nonlocal` directs assignment to the nearest enclosing function scope where the name is already bound. It is used by nested functions and is not a way to modify a module variable.

#### FU-3

**EN:** Does a closure capture a value or a variable binding?  
**RU:** Closure захватывает значение или binding переменной?

**Answer (RU):** Концептуально closure сохраняет доступ к binding в enclosing scope, а не обязательно копию значения на момент создания функции. Поэтому последующее изменение binding через `nonlocal` может быть видно при вызове closure. Если binding указывает на mutable object, изменения самого объекта также будут наблюдаемы.

**Answer (EN):** Conceptually, a closure retains access to a binding in an enclosing scope, not necessarily a copy of the value at function-creation time. Rebinding through `nonlocal` can therefore be observed when the closure is called. If the binding refers to a mutable object, mutations to that object are observable as well.

#### FU-4

**EN:** Why do functions created in a loop often exhibit late-binding behaviour, and how can you avoid it?  
**RU:** Почему функции, созданные в цикле, часто демонстрируют late binding и как этого избежать?

**Answer (RU):** Вложенные функции обычно разрешают имя переменной цикла во время вызова. Если все функции замыкают одно и то же имя, они могут увидеть его итоговое значение. Можно использовать default argument для фиксации текущего binding, фабрику функций или отдельную enclosing scope. При использовании default argument нужно помнить, что значение по умолчанию вычисляется один раз при определении функции.

**Answer (EN):** Nested functions normally resolve the loop variable when they are called. If all functions close over the same name, they may observe its final value. A default argument can capture the current binding, or a function factory can create a separate enclosing scope. Remember that a default argument expression is evaluated once when the function is defined.

#### FU-5

**EN:** Why should mutable state captured by a decorator or closure be treated carefully in a web application?  
**RU:** Почему к изменяемому состоянию, захваченному декоратором или closure, нужно относиться осторожно в веб-приложении?

**Answer (RU):** Wrapper, созданный декоратором, часто является одним объектом функции, который вызывается множеством запросов. Изменяемое состояние в его closure может разделяться между запросами, что создаёт риск утечки контекста, гонок данных и недетерминированного поведения. Состояние запроса следует хранить в request-scoped dependency или другом объекте с корректным жизненным циклом, а не в общем closure без синхронизации и чёткого контракта.

**Answer (EN):** A decorator-created wrapper is often a single function object invoked by many requests. Mutable state in its closure may therefore be shared across requests, creating risks of context leakage, race conditions, and nondeterministic behaviour. Request-specific state should live in a request-scoped dependency or another correctly scoped object, not in a shared closure without synchronization and an explicit contract.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a FastAPI dependency or decorator could close over immutable application configuration, while request-specific identity, authorization context, and database-session state should be supplied through request-scoped dependencies. A shared closure containing mutable patient or request data would be an unsafe design because concurrent requests could observe each other's state.

Any claim that a current Pharmaviyum component uses a particular closure, decorator, or dependency scope must be verified against the source code and tests.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Recites LEGB but cannot explain `UnboundLocalError`, or treats `global` and `nonlocal` as interchangeable. |
| Competent | Correctly explains LEGB, rebinding, closures, and late binding. |
| Strong Senior | Connects lexical scope to closure cells, decorator state, request lifecycles, concurrency, test isolation, and explicit dependency design. |

### Common pitfalls

- Treating global scope as a process-wide namespace rather than a module namespace.
- Assuming a name is global merely because it was declared outside the function.
- Forgetting that assignment can make a name local throughout a function.
- Confusing `NameError` with the more specific `UnboundLocalError`.
- Using `nonlocal` when no binding exists in an enclosing function scope.
- Assuming closures always capture immutable snapshots.
- Missing late binding in functions created in loops.
- Using mutable closure state for request-specific data in a concurrent server.
- Forgetting that default argument expressions are evaluated once at function definition.
- Assuming class attributes are automatically lexical variables inside methods.

### References

- Python execution model — naming and binding: https://docs.python.org/3/reference/executionmodel.html
- `global` statement: https://docs.python.org/3/reference/simple_stmts.html#the-global-statement
- `nonlocal` statement: https://docs.python.org/3/reference/simple_stmts.html#the-nonlocal-statement
- Function definitions and default parameter values: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- PEP 227 — Statically Nested Scopes: https://peps.python.org/pep-0227/
- `functools.wraps`: https://docs.python.org/3/library/functools.html#functools.wraps

---

## PY-CORE-008 — Python functions, decorators, and functional programming

### Question (EN)

**Explain Python's first-class functions and higher-order functions. How do decorators work, and what are the benefits and trade-offs of functional programming techniques such as pure functions, composition, `map`, `filter`, `reduce`, and caching?**

### Перевод (RU)

**Объясните концепции first-class functions и higher-order functions в Python. Как работают декораторы и каковы преимущества и компромиссы функционального программирования: pure functions, композиция, `map`, `filter`, `reduce` и caching?**

### What the interviewer evaluates

- Understanding that functions are first-class objects.
- Ability to distinguish first-class functions from higher-order functions.
- Understanding decorator evaluation and invocation order.
- Correct use of decorator factories, metadata preservation, and callable contracts.
- Ability to reason about closures, function composition, and partial application.
- Understanding lazy iterators returned by `map` and `filter`.
- Appropriate use of `reduce` rather than forcing it onto every aggregation.
- Understanding purity, side effects, referential transparency, and testability.
- Awareness of cache key semantics, memory retention, invalidation, and concurrency concerns.

### Model answer (RU)

В Python функции являются **объектами первого класса (first-class objects)**. Их можно присваивать переменным, передавать как аргументы, возвращать из других функций, хранить в структурах данных и создавать во время выполнения. Это свойство позволяет строить callback-based API, стратегии поведения, dependency injection и декораторы.

**Higher-order function** — функция, которая принимает другую функцию в качестве аргумента и/или возвращает функцию. Следовательно, каждая higher-order function использует функции как значения, но не каждая функция первого класса обязательно является higher-order function.

**Декоратор** — callable, который получает другой callable и обычно возвращает callable, расширяющий или изменяющий его поведение. Синтаксис `@decorator` является удобной формой переназначения имени функции результатом применения декоратора во время определения функции. Вызов декоратора происходит при выполнении определения функции, а не при каждом вызове декорируемой функции.

Декоратор часто создаёт wrapper. Wrapper должен сохранять контракт исходной функции: принимать совместимые аргументы, возвращать ожидаемый результат и корректно передавать исключения. `functools.wraps` помогает сохранить метаданные и устанавливает `__wrapped__`, что полезно для introspection и tooling. Для сложных сигнатур важно учитывать introspection и аннотации, а не полагаться на то, что wrapper автоматически сохраняет исходную сигнатуру на уровне Python bytecode.

**Decorator factory** — функция, которая принимает конфигурацию и возвращает собственно декоратор. Это позволяет параметризовать поведение, например выбрать политику retry или logging. Нужно контролировать, какие значения замыкаются в closure, и не хранить там request-specific mutable state.

Декораторы применяются снизу вверх: при нескольких декораторах ближайший к определению функции применяется первым, а внешний декоратор оборачивает результат внутреннего. Порядок имеет значение, если декораторы управляют транзакциями, авторизацией, кешированием или логированием.

**Function composition** — построение новой функции из последовательного применения других функций. Композиция полезна, когда операции небольшие, имеют ясные входы и выходы и порядок преобразований очевиден. Но чрезмерная композиция может ухудшить читаемость и трассировку ошибок. **Partial application** фиксирует часть аргументов callable; в Python для этого есть `functools.partial`. Это удобно для конфигурирования callback или адаптации интерфейсов без создания лишних wrapper-функций.

Функции `map` и `filter` возвращают итераторы, вычисления выполняются лениво при обходе. Это может снижать необходимость создавать промежуточные коллекции, но значения будут вычислены только при потреблении итератора. В Python часто яснее использовать generator expressions или comprehensions, особенно если преобразование простое. `functools.reduce` сводит последовательность к одному значению, последовательно применяя бинарную функцию; для суммирования, минимума, максимума и других стандартных операций предпочтительнее специализированные встроенные функции, поскольку они обычно понятнее и эффективнее.

**Pure function** при одинаковых входах возвращает одинаковый результат и не вызывает наблюдаемых внешних side effects. Чистые функции проще тестировать, повторно использовать, кешировать и рассуждать о них. Однако реальные backend-системы взаимодействуют с базой данных, сетью, часами, файловой системой и очередями. Практический подход — изолировать side effects на границах системы, а бизнес-преобразования по возможности оставлять чистыми. Это не требует превращать весь проект в функциональную архитектуру.

**Caching** может быть реализован, например, через `functools.lru_cache`. Он хранит результаты вызовов по ключам, сформированным из аргументов. Кеширование корректно только тогда, когда результат действительно зависит от этих аргументов и не меняется из-за скрытого состояния. Нужно учитывать hashability аргументов, ограничение размера кеша, удержание ссылок на ключи и результаты, устаревание данных, многопоточность и безопасность контекста. `lru_cache` не является распределённым кешем и сам по себе не обеспечивает согласованность между процессами или экземплярами приложения. Для асинхронных функций обычный `lru_cache` также не превращает coroutine в кешированный результат: он кеширует возвращаемый объект coroutine, что обычно не является требуемой семантикой.

На Senior-уровне выбор функционального приёма определяется ясностью контракта, тестируемостью и стоимостью сопровождения. Я использую декоратор, если он действительно добавляет сквозное поведение с понятным порядком и границами, pure functions — для детерминированной бизнес-логики, а caching — только при явной стратегии ключей, срока жизни и инвалидации.

### Model answer (EN)

In Python, functions are **first-class objects**. They can be assigned to variables, passed as arguments, returned from other functions, stored in data structures, and created at runtime. This enables callback-based APIs, behavioural strategies, dependency injection, and decorators.

A **higher-order function** is a function that accepts another function as an argument and/or returns a function. Thus, every higher-order function uses functions as values, but not every first-class function is necessarily a higher-order function.

A **decorator** is a callable that receives another callable and usually returns a callable that extends or changes its behaviour. The `@decorator` syntax is shorthand for rebinding the function name to the result of applying the decorator when the function definition executes. The decorator is applied at function-definition time, not on every call to the decorated function.

A decorator often creates a wrapper. The wrapper should preserve the original callable's contract: accept compatible arguments, return the expected result, and propagate exceptions appropriately. `functools.wraps` helps preserve metadata and sets `__wrapped__`, which supports introspection and tooling. With complex signatures, consider introspection and annotations rather than assuming a wrapper automatically preserves the original signature at the Python bytecode level.

A **decorator factory** is a function that accepts configuration and returns a decorator. This makes behaviour configurable, for example a retry or logging policy. Be deliberate about values captured in closures, and do not put request-specific mutable state there.

When decorators are stacked, they are applied from the definition outward: the decorator closest to the function is applied first, and the outer decorator wraps the result. Order matters when decorators manage transactions, authorization, caching, or logging.

**Function composition** builds a function by applying several functions in sequence. It is useful when operations are small, have clear inputs and outputs, and the transformation order is obvious. Excessive composition, however, can make code harder to read and debug. **Partial application** fixes some arguments of a callable; Python provides `functools.partial` for this purpose. It can configure callbacks or adapt interfaces without introducing unnecessary wrapper functions.

`map` and `filter` return iterators and evaluate lazily as they are consumed. This can avoid intermediate collections, but values are not computed until iteration. In Python, generator expressions or comprehensions are often clearer, especially for simple transformations. `functools.reduce` folds an iterable into a single value by repeatedly applying a binary function. For common operations such as summation, minimum, and maximum, dedicated built-ins are usually clearer and often more efficient.

A **pure function** returns the same result for the same inputs and causes no observable external side effects. Pure functions are easier to test, reuse, cache, and reason about. Real backend systems nevertheless interact with databases, networks, clocks, filesystems, and queues. A practical design isolates side effects at system boundaries and keeps business transformations pure where feasible. This does not require making the entire application purely functional.

**Caching** can be implemented with tools such as `functools.lru_cache`. It stores call results under keys derived from arguments. Caching is correct only when the result truly depends on those arguments and is not affected by hidden mutable state. Consider argument hashability, cache size limits, references retained to keys and results, data staleness, concurrency, and context isolation. `lru_cache` is not a distributed cache and does not provide consistency across processes or application instances. For asynchronous functions, ordinary `lru_cache` does not cache the awaited result: it caches the coroutine object returned by the function, which is generally not the desired semantics.

At Senior level, I choose functional techniques based on contract clarity, testability, and maintenance cost. I use decorators when they add cross-cutting behaviour with clear boundaries and ordering, pure functions for deterministic business logic, and caching only with an explicit key, lifetime, and invalidation strategy.

### Follow-up questions and model answers

#### FU-1

**EN:** What is the difference between a first-class function and a higher-order function?  
**RU:** В чём разница между first-class function и higher-order function?

**Answer (RU):** First-class описывает свойства функций как объектов: их можно передавать, возвращать и сохранять как значения. Higher-order описывает конкретную функцию, которая принимает функцию аргументом или возвращает функцию. Это разные уровни описания: первое — свойство языка, второе — характеристика операции.

**Answer (EN):** First-class describes functions as values: they can be passed, returned, and stored. Higher-order describes a particular function that accepts a function as an argument or returns one. They are different levels of description: one is a language property, the other characterizes a function's behaviour.

#### FU-2

**EN:** When is a decorator evaluated, and how does stacking order work?  
**RU:** Когда выполняется декоратор и как работает порядок нескольких декораторов?

**Answer (RU):** Декоратор применяется при выполнении определения функции. При записи нескольких декораторов ближайший к `def` применяется первым, затем его результат оборачивает следующий, внешний декоратор. Поэтому изменение порядка может менять семантику, например границы кеширования, логирования или транзакции.

**Answer (EN):** A decorator is applied when the function definition executes. With stacked decorators, the one closest to `def` is applied first, and each outer decorator then wraps the previous result. Changing the order can therefore change semantics, such as caching, logging, or transaction boundaries.

#### FU-3

**EN:** Why should a decorator usually use `functools.wraps`?  
**RU:** Почему декоратор обычно должен использовать `functools.wraps`?

**Answer (RU):** `wraps` копирует важные метаданные исходной функции на wrapper и устанавливает `__wrapped__`. Это помогает документации, отладчикам, introspection и инструментам, которые исследуют исходную функцию. При этом `wraps` не делает wrapper автоматически идентичным исходной функции по поведению или реальной сигнатуре вызова.

**Answer (EN):** `wraps` copies important metadata from the wrapped function to the wrapper and sets `__wrapped__`. This helps documentation, debuggers, introspection, and tools that inspect the original callable. It does not make the wrapper automatically identical to the original function in behaviour or actual call signature.

#### FU-4

**EN:** When would you choose a comprehension over `map` and `filter`, or a built-in aggregation over `reduce`?  
**RU:** Когда предпочтительнее comprehension вместо `map` и `filter`, или встроенная агрегирующая функция вместо `reduce`?

**Answer (RU):** Для простых преобразований comprehension часто читается естественнее и позволяет выразить фильтрацию и преобразование в одном месте. Для стандартных агрегатов вроде суммы, минимума или максимума специализированные built-ins яснее выражают намерение и обычно эффективнее. `map`, `filter` и `reduce` полезны, когда они делают преобразование или свёртку понятнее, а не просто заменяют более идиоматичный синтаксис.

**Answer (EN):** For simple transformations, comprehensions are often more readable and can express filtering and transformation together. Dedicated built-ins for common aggregates such as sum, minimum, or maximum communicate intent more clearly and are often more efficient. Use `map`, `filter`, and `reduce` when they make the transformation or fold clearer, not merely to replace more idiomatic syntax.

#### FU-5

**EN:** What risks arise when using `lru_cache` for functions that depend on mutable or external state?  
**RU:** Какие риски возникают при использовании `lru_cache` для функций, зависящих от изменяемого или внешнего состояния?

**Answer (RU):** Кеш может вернуть устаревший результат, потому что изменение внешнего состояния не отражается в ключе. Аргументы должны быть hashable, а кеш удерживает ссылки на ключи и результаты до вытеснения или очистки. Нужно определить TTL или инвалидацию, ограничить размер и проверить, допустимо ли разделение результата между пользователями и запросами. Для нескольких процессов потребуется отдельное решение распределённого кеширования.

**Answer (EN):** The cache may return stale data because changes in external state are not represented in the key. Arguments must be hashable, and the cache retains references to keys and results until eviction or clearing. Define a TTL or invalidation strategy, bound the cache size, and verify whether sharing results across users and requests is safe. Multiple processes require a separate distributed-caching solution.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** pure functions could normalize medicine search input or transform validated domain data; decorators could add structured logging or timing around service boundaries; and caching could be considered for reference data only after defining tenant/user isolation, key composition, freshness, and invalidation. Request-specific authorization and patient context must not be accidentally shared through a process-wide function cache or mutable decorator closure.

Any statement that these patterns are currently implemented in Pharmaviyum must be verified against the repository and tests.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Knows decorator syntax but cannot explain when it executes, wrapper behaviour, or lazy iteration. |
| Competent | Explains first-class and higher-order functions, decorator order, pure functions, and basic caching. |
| Strong Senior | Evaluates callable contracts, metadata, side-effect boundaries, cache correctness/invalidation, async limitations, concurrency, and data isolation. |

### Common pitfalls

- Treating first-class and higher-order functions as synonyms.
- Assuming a decorator runs on every invocation of the wrapped function.
- Reversing stacked decorator application order.
- Omitting `functools.wraps` and breaking introspection.
- Writing wrappers that accidentally change exception or return semantics.
- Forgetting that `map` and `filter` are lazy iterators in Python 3.
- Using `reduce` where a clear built-in is available.
- Calling a function pure when it reads hidden state or performs side effects.
- Caching results that depend on time, database state, authorization, or tenant context without including those dimensions in the key.
- Assuming `lru_cache` is distributed or provides application-wide invalidation.
- Applying ordinary `lru_cache` to async functions expecting awaited results to be cached.

### References

- Python tutorial — functional programming tools: https://docs.python.org/3/howto/functional.html
- Function definitions and decorators: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- `functools`: https://docs.python.org/3/library/functools.html
- `functools.wraps`: https://docs.python.org/3/library/functools.html#functools.wraps
- `functools.partial`: https://docs.python.org/3/library/functools.html#functools.partial
- `functools.reduce`: https://docs.python.org/3/library/functools.html#functools.reduce
- `functools.lru_cache`: https://docs.python.org/3/library/functools.html#functools.lru_cache

---

## PY-CORE-009 — Python iterators, generators, and lazy evaluation

### Question (EN)

**Explain the iterable and iterator protocols in Python. How do generators work, what does lazy evaluation mean, and how do you use generator lifecycle controls and streaming safely in backend systems?**

### Перевод (RU)

**Объясните протоколы iterable и iterator в Python. Как работают генераторы, что означает lazy evaluation и как безопасно использовать управление жизненным циклом генератора и streaming в backend-системах?**

### What the interviewer evaluates

- Precise distinction between iterable and iterator.
- Understanding of `iter()`, `next()`, `__iter__()`, and `__next__()`.
- Generator function and generator expression semantics.
- Lazy execution, suspension, and resumption.
- Correct use of `yield from`.
- Understanding of `send()`, `throw()`, and `close()`.
- Resource cleanup and generator finalization.
- Memory characteristics and single-pass consumption.
- Streaming, backpressure, cancellation, and failure handling in backend systems.

### Model answer (RU)

**Iterable** — объект, от которого можно получить итератор. Обычно это означает, что объект реализует `__iter__()`, возвращающий iterator. **Iterator** — объект, представляющий поток значений и реализующий `__next__()`; его `__iter__()` возвращает сам итератор. Вызов `next(iterator)` получает следующий элемент, а после исчерпания итератор поднимает `StopIteration`.

Коллекция, например список, обычно является iterable и позволяет создавать несколько независимых итераторов. Сам итератор обычно является одноразовым состоянием обхода: он продвигается вперёд и после исчерпания не начинает обход заново автоматически. Поэтому iterable и iterator — разные роли, даже если один объект может выполнять обе.

**Generator function** — функция, в теле которой присутствует `yield`. Вызов такой функции не выполняет тело до первого `yield`, а возвращает generator iterator. При запросе следующего значения выполнение начинается или продолжается с сохранённого места. Локальные переменные, позиция выполнения и состояние генератора сохраняются между возобновлениями. Когда функция завершается или выполняет `return`, генератор становится исчерпанным; значение `return` передаётся как значение атрибута `value` исключения `StopIteration`, а не как обычный элемент последовательности.

**Generator expression** создаёт генератор через компактный синтаксис, похожий на comprehension, но вычисляет элементы по мере потребления. Это отличается от list comprehension, который сразу строит список. Ленивость снижает необходимость хранить всю последовательность в памяти, но не означает, что источник бесплатен или что любая операция становится быстрее.

**Lazy evaluation** означает, что значение вычисляется по требованию. Это полезно для больших наборов данных, конвейеров преобразования и streaming. Но ленивый pipeline может быть исчерпан только один раз, а ошибки чтения источника могут проявиться не при создании генератора, а позже — во время итерации. Если потребитель не прочитал поток полностью, часть операций может вообще не выполниться.

`yield from iterable` делегирует выдачу элементов другому iterable/iterator и прозрачно поддерживает передачу значений и исключений в делегируемый генератор в соответствии с протоколом. Это удобнее и точнее, чем вручную писать цикл для простого делегирования.

Генератор поддерживает дополнительные операции:

- `send(value)` возобновляет генератор и передаёт значение в выражение `yield`. Для только что созданного генератора сначала требуется `next()` или `send(None)`.
- `throw(exception)` возобновляет генератор, внедряя исключение в точке приостановки.
- `close()` сигнализирует генератору о завершении, внедряя `GeneratorExit`. Генератор может выполнить cleanup в `finally`; он не должен продолжать выдавать значения после получения `GeneratorExit`.

Генераторы могут управлять ресурсами, но ресурс должен закрываться надёжно. Предпочтительно использовать context manager или `try/finally`, а не полагаться исключительно на сборщик мусора или момент уничтожения объекта генератора. Если генератор владеет файлом, курсором БД или сетевым ресурсом, вызывающий код должен иметь ясный контракт завершения и закрытия. Для async generators используются `async for`, `yield`, `aclose()` и async context management; их жизненный цикл также требует корректного завершения при отмене.

В backend streaming важно учитывать **backpressure**: производитель не должен бесконтрольно создавать данные быстрее, чем потребитель способен их обработать. Синхронный генератор при обычном обходе естественным образом выдаёт следующий элемент по запросу потребителя, но это не гарантирует end-to-end backpressure через HTTP server, reverse proxy, buffers и сеть. Нужно учитывать буферизацию, таймауты, медленных клиентов, отмену запроса и освобождение ресурсов.

Генератор экономит память, если данные действительно обрабатываются постепенно. Однако он не делает автоматически bounded memory весь pipeline: промежуточное накопление в списке, буферы драйвера, сериализация ответа или сторонний слой могут снова потребовать значительную память. Аналогично streaming не заменяет pagination, лимиты, контроль доступа и защиту от чрезмерного потребления ресурсов.

На Senior-уровне я оцениваю полный жизненный цикл потока: кто владеет ресурсом, кто отвечает за закрытие, что происходит при исключении или отмене, может ли поток быть повторно использован, где возникает buffering и как ограничивается скорость производства данных.

### Model answer (EN)

An **iterable** is an object from which an iterator can be obtained. Typically, it implements `__iter__()`, returning an iterator. An **iterator** represents a stream of values and implements `__next__()`; its `__iter__()` returns itself. Calling `next(iterator)` retrieves the next item, and an exhausted iterator raises `StopIteration`.

A collection such as a list is usually iterable and can create multiple independent iterators. An iterator is generally a single traversal state: it advances and does not automatically restart after exhaustion. Iterable and iterator are therefore distinct roles, even though one object can implement both.

A **generator function** is a function whose body contains `yield`. Calling it does not execute the body up to the first `yield`; it returns a generator iterator. When the next value is requested, execution starts or resumes from the saved suspension point. Local variables, the instruction position, and generator state are retained between resumptions. When the function finishes or executes `return`, the generator becomes exhausted; the return value is carried as the `value` attribute of `StopIteration`, not emitted as an ordinary item.

A **generator expression** creates a generator using compact syntax similar to a comprehension, but computes items as they are consumed. This differs from a list comprehension, which eagerly builds a list. Laziness reduces the need to hold an entire sequence in memory, but it does not make the source free or every operation faster.

**Lazy evaluation** means computing values on demand. It is useful for large datasets, transformation pipelines, and streaming. However, a lazy pipeline may be consumed only once, and source errors may occur during iteration rather than when the generator is created. If the consumer does not exhaust the stream, some operations may never run.

`yield from iterable` delegates item production to another iterable or iterator and supports forwarding values and exceptions to a delegated generator according to the protocol. It is clearer and more complete than manually writing a loop for simple delegation.

A generator supports additional control operations:

- `send(value)` resumes the generator and supplies a value to the suspended `yield` expression. A newly created generator must first be advanced with `next()` or `send(None)`.
- `throw(exception)` resumes the generator by raising an exception at the suspension point.
- `close()` signals termination by injecting `GeneratorExit`. The generator can perform cleanup in `finally`; it must not yield another value after receiving `GeneratorExit`.

Generators can manage resources, but resources must be closed reliably. Prefer a context manager or `try/finally` rather than relying solely on garbage collection or generator destruction timing. If a generator owns a file, database cursor, or network resource, the caller needs a clear completion and closure contract. Async generators use `async for`, `yield`, `aclose()`, and async context management; their lifecycle also requires correct cleanup on cancellation.

For backend streaming, consider **backpressure**: a producer should not generate data uncontrollably faster than the consumer can process it. A synchronous generator naturally yields the next item when the consumer requests it, but that does not guarantee end-to-end backpressure across an HTTP server, reverse proxy, buffers, and the network. Account for buffering, timeouts, slow clients, request cancellation, and resource cleanup.

A generator saves memory when data is genuinely processed incrementally. It does not automatically make the entire pipeline memory-bounded: intermediate list accumulation, driver buffers, response serialization, or another layer may still consume substantial memory. Similarly, streaming does not replace pagination, limits, access control, or resource-consumption safeguards.

At Senior level, I evaluate the complete stream lifecycle: who owns the resource, who closes it, what happens on exceptions or cancellation, whether the stream can be reused, where buffering occurs, and how production rate is controlled.

### Comprehensions: evaluation, scope, and trade-offs

**RU:** List, set и dict comprehensions вычисляются eagerly и создают соответствующую коллекцию; generator expression вычисляет значения лениво по мере потребления. В Python 3 переменная цикла comprehension не «утекает» во внешнюю область видимости, но comprehension может ссылаться на внешние имена и выполнять выражения с побочными эффектами. Вложенные comprehensions выполняют вложенные циклы в порядке, заданном синтаксисом. Исключения и побочные эффекты возникают в момент вычисления соответствующего элемента, поэтому eager и lazy формы могут отличаться не только памятью, но и временем наблюдаемого поведения. Выбирайте comprehension ради ясного преобразования/фильтрации; не помещайте туда сложную бизнес-логику или скрытые побочные эффекты.

**EN:** List, set, and dictionary comprehensions are eager and construct their respective collections; a generator expression evaluates values lazily as they are consumed. In Python 3, a comprehension's iteration variable does not leak into the surrounding scope, although the comprehension can read outer names and execute expressions with side effects. Nested comprehensions run nested loops in the order expressed by the syntax. Exceptions and side effects occur when the corresponding element is evaluated, so eager and lazy forms can differ in observable timing as well as memory use. Use comprehensions for clear transformations and filtering; avoid hiding complex business logic or side effects inside them.

**References:** Python Expressions — https://docs.python.org/3.14/reference/expressions.html ; Python Data Structures — https://docs.python.org/3.14/tutorial/datastructures.html#list-comprehensions

### Follow-up questions and model answers

#### FU-1

**EN:** What is the difference between an iterable and an iterator?  
**RU:** В чём разница между iterable и iterator?

**Answer (RU):** Iterable предоставляет способ получить итератор через `iter()`. Iterator хранит состояние текущего обхода, реализует `__next__()` и возвращает себя из `__iter__()`. Коллекция обычно может создавать новые итераторы, тогда как конкретный iterator обычно продвигается вперёд и исчерпывается.

**Answer (EN):** An iterable provides a way to obtain an iterator through `iter()`. An iterator stores traversal state, implements `__next__()`, and returns itself from `__iter__()`. A collection can usually create new iterators, while a particular iterator normally advances and becomes exhausted.

#### FU-2

**EN:** When does a generator function execute, and what happens when it returns?  
**RU:** Когда выполняется generator function и что происходит при её завершении через return?

**Answer (RU):** Вызов generator function создаёт generator iterator, но тело функции начинает выполняться при первом запросе элемента. Выполнение приостанавливается на `yield` и продолжается при следующем запросе. При завершении `return value` приводит к `StopIteration`, а возвращённое значение доступно как `StopIteration.value`; оно не становится элементом потока.

**Answer (EN):** Calling a generator function creates a generator iterator, but the body starts executing when an item is first requested. Execution suspends at `yield` and resumes on the next request. On completion, `return value` results in `StopIteration`, with the returned value available as `StopIteration.value`; it is not emitted as a stream item.

#### FU-3

**EN:** How do `send()`, `throw()`, and `close()` differ?  
**RU:** Чем отличаются `send()`, `throw()` и `close()`?

**Answer (RU):** `send()` передаёт значение в приостановленное выражение `yield` и возобновляет выполнение. `throw()` внедряет исключение в точку приостановки. `close()` инициирует завершение через `GeneratorExit`, позволяя выполнить cleanup в `finally`. Новый генератор нельзя начинать с ненулевого значения в `send()`: сначала его нужно продвинуть через `next()` или `send(None)`.

**Answer (EN):** `send()` supplies a value to the suspended `yield` expression and resumes execution. `throw()` injects an exception at the suspension point. `close()` initiates termination through `GeneratorExit`, allowing cleanup in `finally`. A new generator cannot be started by sending a non-None value; advance it first with `next()` or `send(None)`.

#### FU-4

**EN:** Why is relying on garbage collection to close a generator's resources unsafe?  
**RU:** Почему небезопасно полагаться на garbage collection для закрытия ресурсов генератора?

**Answer (RU):** Момент освобождения объекта зависит от реализации и жизненного цикла ссылок; он не должен быть контрактом управления ресурсами. Генератор может остаться удержанным ссылкой или завершиться позже ожидаемого. Используйте явное закрытие, context manager и `try/finally`, чтобы файл, cursor или другой ресурс освобождался даже при раннем выходе или исключении.

**Answer (EN):** Object finalization timing depends on implementation and reference lifetimes; it should not be the resource-management contract. A generator may remain referenced or be finalized later than expected. Use explicit closure, a context manager, and `try/finally` so a file, cursor, or other resource is released even on early exit or an exception.

#### FU-5

**EN:** Does using a generator guarantee bounded memory and end-to-end backpressure in an HTTP streaming endpoint?  
**RU:** Гарантирует ли генератор ограниченное потребление памяти и end-to-end backpressure в HTTP streaming endpoint?

**Answer (RU):** Нет. Генератор выдаёт элементы постепенно, но другие слои могут буферизовать данные: драйвер БД, сериализатор, ASGI server, reverse proxy или сетевой стек. Нужно проверять поведение всей цепочки, ограничивать размер страниц и буферов, обрабатывать медленных клиентов, отмену и таймауты, а также гарантировать закрытие ресурсов.

**Answer (EN):** No. A generator yields incrementally, but other layers may buffer data: the database driver, serializer, ASGI server, reverse proxy, or network stack. Validate the entire pipeline, bound page and buffer sizes, handle slow clients, cancellation, and timeouts, and guarantee resource cleanup.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a medicine catalogue export or large search result could be processed incrementally rather than materialized as one large list. If a generator streams database rows, the database session and cursor must remain valid for the stream's lifetime and be closed on completion, client disconnect, or error. A production design should also define pagination or row limits, authorization checks, cancellation behaviour, and buffering across the HTTP stack.

Any claim that Pharmaviyum currently implements streaming endpoints or generator-based database access must be verified against source code and tests.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Confuses iterable and iterator, or assumes generator body runs immediately when called. |
| Competent | Explains generator suspension, lazy evaluation, `StopIteration`, and basic cleanup. |
| Strong Senior | Reasons about resource ownership, early termination, async-generator cleanup, buffering, backpressure, cancellation, and memory bounds across the complete backend pipeline. |

### Common pitfalls

- Treating every iterable as an iterator.
- Assuming a generator can be restarted after exhaustion.
- Assuming generator function execution begins at the function call.
- Forgetting that lazy errors may occur during iteration.
- Confusing a generator's `return` value with a yielded item.
- Using `send(value)` before first advancing a new generator.
- Treating `close()` as a substitute for a clear resource ownership contract.
- Relying on garbage collection to close files or database cursors.
- Assuming generator use alone guarantees bounded memory.
- Assuming a synchronous generator guarantees end-to-end HTTP backpressure.
- Ignoring cancellation, slow consumers, timeouts, and client disconnects.

### References

- Python glossary — iterable and iterator: https://docs.python.org/3/glossary.html
- Iterator Types: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Generator-iterator methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
- Yield expressions and `yield from`: https://docs.python.org/3/reference/expressions.html#yield-expressions
- Generator expressions: https://docs.python.org/3/reference/expressions.html#generator-expressions
- `contextlib`: https://docs.python.org/3/library/contextlib.html
- Asynchronous generator functions: https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions


## PY-CORE-010 — Python exception handling and custom exceptions

### Interview question

Explain Python's exception model and how you design exception handling in a production backend. Cover the exception hierarchy, the roles of `try`, `except`, `else`, and `finally`, exception propagation and chaining, custom exception classes, exception groups, and the boundary between domain errors and HTTP responses.

### Русский перевод вопроса

Объясните модель исключений Python и то, как вы проектируете обработку ошибок в production backend. Раскройте иерархию исключений, назначение `try`, `except`, `else` и `finally`, распространение и связывание исключений, собственные классы исключений, группы исключений и границу между domain errors и HTTP-ответами.

### What the interviewer evaluates

- Understanding of Python's exception hierarchy and the distinction between `BaseException` and `Exception`.
- Precise control-flow semantics of `try/except/else/finally`.
- Ability to preserve causal information with exception chaining.
- Design of meaningful, stable custom exception taxonomies.
- Correct use of narrow exception handling and cleanup guarantees.
- Awareness of `ExceptionGroup` and `except*` in concurrent or task-group code.
- Separation of domain, application, infrastructure, and transport concerns.
- Production practices: safe logging, observability, redaction, retries, and stable client-facing errors.

### Model answer (RU)

В Python исключение — это объект, представляющий ошибочную или особую ситуацию во время выполнения. Исключение прерывает обычный поток выполнения и распространяется вверх по стеку вызовов, пока не будет обработано подходящим обработчиком. Если обработчика нет, выполнение завершается с traceback.

**Иерархия исключений.** В верхней части находятся `BaseException` и его подклассы. `Exception` — базовый класс для большинства обычных ошибок приложения: `ValueError`, `TypeError`, `RuntimeError`, `OSError` и многих других. Системные сигналы завершения, например `KeyboardInterrupt` и `SystemExit`, наследуются непосредственно от `BaseException`, а не от `Exception`. Поэтому прикладной код почти всегда должен перехватывать `Exception` или более узкий тип, а не `BaseException`: иначе можно случайно подавить сигналы завершения процесса.

**Семантика конструкции.**
- `try` содержит код, для которого ожидается обработка исключений.
- `except` выбирает подходящий обработчик по типу исключения. Следует перехватывать наиболее узкий тип, который код действительно умеет обработать.
- `else` выполняется только тогда, когда блок `try` завершился без исключения. Он полезен для отделения успешного пути от кода, который должен находиться под защитой `except`.
- `finally` выполняется при обычном выходе из конструкции, включая выход через исключение или `return`. Его используют для гарантированного cleanup, но для владения ресурсами обычно предпочтительнее context manager.

Исключение, которое не обработано в текущем кадре, распространяется к вызывающему коду. Обработчик не должен просто поглощать ошибку: он должен либо восстановить корректное состояние, либо преобразовать ошибку на подходящем уровне, либо позволить ей распространиться дальше.

**Exception chaining.** Если низкоуровневая ошибка преобразуется в ошибку более высокого уровня, `raise DomainError(...) from exc` сохраняет исходную причину в `__cause__`. Это помогает сохранить диагностический контекст, не заставляя верхние слои зависеть от деталей драйвера или библиотеки. Конструкция `raise NewError(...) from None` подавляет отображение неявного контекста в traceback; её следует использовать осознанно, поскольку она скрывает причинную цепочку от стандартного отображения.

**Пользовательские исключения.** Обычно собственные исключения наследуются от `Exception`. Их иерархия должна отражать стабильные категории ошибок предметной области или приложения, а не дублировать каждый внутренний сбой отдельным классом. Например, можно определить `MedicationNotFoundError` или `InventoryConflictError`, если эти состояния имеют отдельную семантику для вызывающего слоя. Полезно сохранять структурированные атрибуты, необходимые для обработки, а не анализировать текст сообщения. Сообщение исключения не является стабильным API-контрактом.

**Exception groups.** Начиная с Python 3.11, `ExceptionGroup` позволяет представить несколько исключений как одну группу, например когда несколько concurrent tasks завершаются ошибками. `except*` обрабатывает совпадающие подмножества группы, сохраняя структуру оставшихся исключений. Это не замена обычному `except`; механизм предназначен для сценариев, где несколько ошибок могут возникнуть независимо в одной операции.

**Архитектура backend.** Domain layer должен выражать ошибки в терминах предметной области и не зависеть от FastAPI или HTTP. Application layer координирует use cases и решает, какие ошибки преобразовать или передать выше. Infrastructure layer может преобразовывать ошибки драйвера в инфраструктурные исключения, сохраняя причину через `raise ... from exc`. На границе FastAPI exception handlers преобразуют известные application/domain errors в стабильные HTTP status codes и безопасные response bodies.

В production нельзя возвращать клиенту traceback, SQL, внутренние пути, секреты или необработанные сообщения драйвера. Логи и traces должны содержать correlation/request ID и достаточный диагностический контекст, но не секреты и персональные/медицинские данные. Повторять операцию следует только при классифицированной временной ошибке и с учётом идемпотентности, deadline и retry budget. Не следует автоматически повторять validation errors или постоянные domain conflicts.

### Professional answer (EN)

Python exceptions are objects that represent abnormal or exceptional conditions during execution. Raising an exception interrupts the normal control flow. The exception propagates through the call stack until a compatible handler catches it; if it remains unhandled, the operation terminates and Python reports a traceback.

**Hierarchy.** `BaseException` is the root of the built-in exception hierarchy. `Exception` is the base class for most application-level errors, including `ValueError`, `TypeError`, `RuntimeError`, and `OSError`. Process-control exceptions such as `KeyboardInterrupt` and `SystemExit` inherit directly from `BaseException`. Application code should generally catch `Exception` or a narrower subclass, not `BaseException`, so that process-control signals are not accidentally swallowed.

**Control flow.** The `try` suite contains operations whose failures may be handled. An `except` clause handles a matching exception type. An `else` clause runs only if the `try` suite completes without raising, which keeps success-path code outside the protected region. A `finally` clause runs as the construct is left, including during exception propagation and returns, and is useful for cleanup. Context managers are usually the clearer abstraction for deterministic resource management.

Exceptions propagate to callers unless handled. A handler should recover, translate the failure at an appropriate abstraction boundary, or re-raise it; silently swallowing an error usually hides a broken invariant.

**Exception chaining** preserves causality when translating low-level failures. `raise HigherLevelError(...) from exc` explicitly sets the original exception as `__cause__`, retaining diagnostic context while decoupling upper layers from implementation details. `raise ... from None` suppresses display of the implicit context and should be used sparingly because it can make diagnosis harder.

**Custom exceptions** should normally inherit from `Exception`. A useful taxonomy models stable domain or application conditions rather than every implementation detail. Structured attributes are preferable to parsing exception-message strings. Exception messages are not a reliable machine-readable contract.

**Exception groups.** Python 3.11 introduced `ExceptionGroup` and `except*` to represent and selectively handle multiple failures, especially when concurrent tasks can fail independently. `except*` handles matching portions of a group while preserving unmatched failures. It complements rather than replaces ordinary exception handling.

**Backend boundaries.** Domain exceptions should express business semantics without depending on FastAPI or HTTP. Application services coordinate use cases; infrastructure adapters may translate driver-specific failures while preserving their cause. FastAPI exception handlers then map known application/domain failures to stable HTTP status codes and safe response schemas.

In production, never expose tracebacks, SQL statements, internal paths, credentials, or raw driver messages to clients. Logs and traces should carry correlation identifiers and useful diagnostic context while excluding secrets and sensitive patient/customer data. Retries must be limited to classified transient failures and must respect idempotency, deadlines, and retry budgets. Validation failures and permanent domain conflicts should not be blindly retried.

### Follow-up questions and model answers

**FU-1 — Why is catching `BaseException` usually a design error?**

RU: Потому что `BaseException` включает не только обычные ошибки приложения, но и управляющие сигналы вроде `KeyboardInterrupt` и `SystemExit`. Перехват такого базового класса может помешать остановке процесса. В обычном application code следует перехватывать `Exception` или конкретный подкласс. Узкое использование `BaseException` допустимо только в специализированном коде инфраструктуры, который действительно обязан выполнить cleanup и затем корректно повторно поднять исключение.

EN: Because `BaseException` also includes process-control signals such as `KeyboardInterrupt` and `SystemExit`. Catching it broadly can prevent normal process termination. Application code should generally catch `Exception` or a specific subclass. Specialized infrastructure code may need broader handling for cleanup, but it must preserve and re-raise control-flow signals correctly.

**FU-2 — What is the practical difference between `raise`, `raise exc`, and `raise NewError(...) from exc`?**

RU: Голый `raise` внутри обработчика повторно поднимает текущее исключение, сохраняя исходный traceback. `raise exc` явно поднимает объект исключения заново и может изменить traceback, добавив текущую точку. `raise NewError(...) from exc` создаёт исключение более высокого уровня и явно сохраняет исходную ошибку как причину. Для прозрачного повторного проброса предпочтителен голый `raise`.

EN: A bare `raise` re-raises the active exception and preserves its traceback. `raise exc` raises the exception object explicitly and can alter the traceback by adding the current raise location. `raise NewError(...) from exc` translates the failure while explicitly retaining the original exception as its cause. Use bare `raise` when the intent is simply to propagate the same exception.

**FU-3 — When should an exception be translated, and when should it propagate unchanged?**

RU: Переводить исключение следует на границе абстракции, когда нижний слой сообщает детали реализации, которые не должны протекать выше. Например, ошибка драйвера PostgreSQL может быть преобразована в инфраструктурную или application-level ошибку с сохранением причины. Если текущий слой не может восстановиться, классифицировать или осмысленно преобразовать ошибку, лучше позволить ей распространиться. Нельзя превращать все ошибки в один общий тип и терять возможность различать retryable и permanent failures.

EN: Translate an exception at an abstraction boundary when a lower layer exposes implementation-specific details that should not leak upward. For example, a PostgreSQL driver error may become an infrastructure or application-level exception while retaining its cause. If a layer cannot recover from, classify, or meaningfully translate the failure, it should generally propagate unchanged. Do not collapse all failures into one generic type, because callers may need to distinguish transient from permanent errors.

**FU-4 — How do `ExceptionGroup` and `except*` differ from ordinary exception handling?**

RU: Обычный `except` выбирает обработчик для одного поднятого исключения по его типу. `ExceptionGroup` содержит несколько исключений, а `except*` выбирает совпадающие исключения внутри группы и позволяет обработать их отдельно, сохраняя неперехваченные элементы. Это важно при structured concurrency, когда несколько задач могут завершиться независимо и вернуть несколько ошибок. Если операция гарантирует только одну ошибку, обычная модель проще.

EN: An ordinary `except` matches the type of a raised exception. An `ExceptionGroup` contains multiple exceptions, while `except*` selects matching members for handling and leaves unmatched members in the group. This is useful with structured concurrency, where multiple tasks may fail independently. If an operation can produce only one failure, ordinary exception handling is simpler.

**FU-5 — How would you design error handling for a FastAPI endpoint without coupling the domain layer to HTTP?**

RU: Domain layer определяет собственные ошибки предметной области, например отсутствие лекарства или конфликт остатка, и не импортирует FastAPI. Application service поднимает эти ошибки или преобразует ошибки портов/адаптеров на границах. FastAPI exception handlers в presentation layer отображают известные типы в стабильные HTTP-коды и публичную схему ошибки. Неизвестные ошибки остаются 500, логируются с correlation ID и traceback на серверной стороне, а клиент получает безопасное обобщённое сообщение. Контракт ответа не должен раскрывать внутренние детали.

EN: The domain layer defines domain-specific exceptions, such as a missing medication or an inventory conflict, without importing FastAPI. Application services propagate these errors or translate adapter failures at explicit boundaries. FastAPI exception handlers in the presentation layer map known types to stable HTTP status codes and public error schemas. Unknown failures remain 500 responses, are logged server-side with a correlation ID and traceback, and produce a safe generic client message. The response contract must not expose internal implementation details.

### Pharmaviyum application scenario (hypothetical)

**Status: Hypothetical interview scenario — not a claim about the current implementation.**

Imagine a medication lookup or inventory operation in Pharmaviyum. The domain layer could raise a typed error such as `MedicationNotFoundError` or `InventoryConflictError`. A repository adapter could translate a database-specific failure into an infrastructure exception using exception chaining. The FastAPI boundary could map known domain errors to safe 404 or 409 responses, while unexpected failures remain generic 500 responses. Logs and traces should use request correlation identifiers and must not include patient records, credentials, or sensitive medication/prescription context.

The senior-level design question is not merely which status code to return. It is where the error belongs, which layer owns its translation, whether a retry is safe, what information is observable internally, and what information is allowed to cross the API boundary.

### Senior-level evaluation rubric

A strong Senior answer should demonstrate that the candidate:

1. Explains the `BaseException` / `Exception` distinction accurately and avoids broad catch-all handlers.
2. Describes the exact semantics of `else` and `finally`, including exception propagation and cleanup.
3. Uses exception chaining to preserve causal context during abstraction-boundary translation.
4. Designs custom exception hierarchies around stable domain semantics, not implementation details.
5. Understands `ExceptionGroup` and `except*` as mechanisms for handling multiple concurrent failures.
6. Separates domain errors from HTTP transport concerns and defines stable public error contracts.
7. Covers observability, sensitive-data redaction, idempotency, retry classification, and failure budgets.

**Evaluation signals**
- Mid-level: knows `try/except/finally` and can define custom exceptions.
- Strong Senior: explains propagation, chaining, abstraction boundaries, and safe API mapping.
- Staff-level signal: designs consistent error taxonomy and observability/retry policies across services while preserving domain independence and operational safety.

### Common pitfalls

- Catching `BaseException` or using a broad `except Exception` as routine control flow.
- Returning success after swallowing an exception.
- Using `else` as if it ran when an exception occurred.
- Treating `finally` as a substitute for context managers and explicit resource ownership.
- Raising a new exception without preserving the original cause when that cause matters.
- Parsing exception-message text instead of using types and structured attributes.
- Exposing tracebacks, SQL, driver messages, secrets, or patient data in HTTP responses.
- Mapping every failure to the same status code or one generic domain exception.
- Retrying permanent failures or non-idempotent operations without safeguards.
- Assuming `except*` is interchangeable with ordinary `except`.

### References

- Python tutorial — Errors and Exceptions: https://docs.python.org/3/tutorial/errors.html
- Built-in Exceptions: https://docs.python.org/3/library/exceptions.html
- Compound statements — `try`: https://docs.python.org/3/reference/compound_stmts.html#the-try-statement
- Exception context and chaining: https://docs.python.org/3/library/exceptions.html#exception-context
- PEP 654 — Exception Groups and `except*`: https://peps.python.org/pep-0654/
- FastAPI — Handling Errors: https://fastapi.tiangolo.com/tutorial/handling-errors/


## PY-CORE-011 — Python context managers and resource management

**Question (EN):** Explain the context manager protocol and how Python guarantees resource cleanup with the `with` statement. Compare synchronous and asynchronous context managers, and discuss how you would manage database sessions, locks, files, and other resources in a production backend.

**Перевод (RU):** Объясните протокол context manager и то, как Python обеспечивает освобождение ресурсов с помощью оператора `with`. Сравните синхронные и асинхронные контекстные менеджеры и расскажите, как управлять DB sessions, locks, файлами и другими ресурсами в production backend.

### What the interviewer is evaluating

- Accurate understanding of the context manager protocol and control flow.
- Resource ownership, deterministic cleanup, and exception propagation.
- Correct use of `contextlib`, `ExitStack`, and asynchronous context managers.
- Awareness of cancellation, concurrency, transaction boundaries, and cleanup failures.
- Ability to separate resource lifecycle management from business logic.

### Model answer (RU)

Context manager — это объект, который задаёт границу управления ресурсом или временным контекстом. Синхронный протокол состоит из `__enter__()` и `__exit__(exc_type, exc_value, traceback)`. При входе в блок `with` Python вызывает `__enter__`; возвращаемое значение связывается с переменной после `as`. При выходе из блока `__exit__` вызывается как при нормальном завершении, так и при исключении, возникшем внутри блока.

Если исключения не было, аргументы `__exit__` равны `None`. Если исключение было, метод получает его тип, объект и traceback. Возвращение truthy value означает подавление исключения; falsey value, включая `None`, позволяет ему распространяться дальше. Исключение, возникшее внутри `__exit__`, само становится результатом выхода и может заменить исходное исключение, поэтому cleanup-код должен быть предсказуемым и не скрывать первопричину.

`with` обеспечивает детерминированный вызов протокола выхода при обычном выходе из блока и при распространении исключения через блок. Это не означает защиту от любого завершения процесса: например, принудительное завершение процесса или авария интерпретатора не дают универсальной гарантии cleanup.

Для простого случая можно реализовать протокол напрямую. Для генераторного стиля применяется `contextlib.contextmanager`: код до `yield` выполняет setup, код после — cleanup, а исключение из тела with при необходимости инжектируется в точку `yield`. Исключение нельзя случайно проглотить: если генератор перехватил его только для логирования и не поднял повторно, оно будет подавлено. Для асинхронного кода используются `async with`, `__aenter__`, `__aexit__` и `contextlib.asynccontextmanager`; операции setup/cleanup могут ожидать завершения async I/O.

`ExitStack` полезен, когда количество ресурсов или контекстных менеджеров определяется во время выполнения. Он регистрирует callbacks и exit handlers и закрывает ресурсы в обратном порядке — по принципу LIFO. Это помогает корректно откатывать частично выполненный setup, если получение следующего ресурса завершилось ошибкой.

В backend важно определить владельца каждого ресурса и его lifetime. Database session должна иметь ограниченную область действия, обычно одну операцию или транзакцию; commit/rollback должны быть явными и согласованными с unit-of-work. Нельзя держать соединение или lock во время долгих внешних вызовов без необходимости. Файлы, временные каталоги и locks должны освобождаться в гарантированной точке. Для async ресурсов следует учитывать cancellation: cleanup может требовать await, поэтому он должен быть реализован в async exit path и не должен бесконтрольно подавлять cancellation. Контекстный менеджер сам по себе не делает операцию потокобезопасной, транзакционной или идемпотентной — он только задаёт lifecycle и правила выхода.

### Professional answer (EN)

A context manager defines a bounded execution scope for a resource or temporary state. The synchronous protocol consists of `__enter__()` and `__exit__(exc_type, exc_value, traceback)`. Entering a `with` block invokes `__enter__`, and its return value is assigned to the target after `as`. On leaving the block, Python invokes `__exit__` both after normal completion and when an exception propagates out of the block.

When no exception occurred, the three exception arguments are `None`. Otherwise, `__exit__` receives the exception type, instance, and traceback. A truthy return value suppresses the exception; a falsey value, including `None`, allows propagation. An exception raised by `__exit__` can replace the exception from the block, so cleanup code should be predictable and should not obscure the primary failure.

The `with` statement provides deterministic protocol exit for normal control flow and exceptions crossing the block. It is not a universal guarantee under process termination or interpreter failure.

A class can implement the protocol directly. `contextlib.contextmanager` offers a generator-based alternative: setup runs before `yield`, cleanup after it, and an exception from the with-body can be thrown back at the yield point. If the generator catches an exception only to log it and does not re-raise it, that exception is suppressed. Asynchronous code uses `async with`, `__aenter__`, `__aexit__`, and `contextlib.asynccontextmanager`, allowing setup and cleanup to await asynchronous operations.

`ExitStack` is useful when the number of resources or context managers is dynamic. It registers exit handlers and callbacks and unwinds them in reverse order (LIFO), including when later acquisition fails partway through setup.

In a backend, every resource needs an explicit owner and lifetime. A database session should be scoped narrowly—often to one operation or transaction—with deliberate commit/rollback semantics consistent with the unit-of-work boundary. Avoid holding connections or locks across slow external calls without a clear reason. Files, temporary directories, and locks need deterministic release. Async cleanup must account for cancellation and should not accidentally suppress it. A context manager does not by itself make an operation thread-safe, transactional, or idempotent; it defines lifecycle and exit behavior.

### Follow-up questions and model answers

**FU-1 — What exactly happens when an exception leaves a `with` block?**

RU: Python вызывает `__exit__`, передавая тип, объект исключения и traceback. Если `__exit__` возвращает truthy value, исключение подавляется; иначе оно продолжает распространяться. Если `__exit__` само поднимает исключение, оно может заменить исходное, поэтому ошибки cleanup требуют аккуратной политики.

EN: Python calls `__exit__` with the exception type, instance, and traceback. A truthy return suppresses the exception; otherwise it propagates. If `__exit__` raises, that new exception can replace the original, so cleanup failures need an explicit policy.

**FU-2 — When would you choose `contextlib.contextmanager` over a class-based context manager?**

RU: Генераторный вариант удобен для компактного setup/cleanup, когда не нужны сложное состояние и несколько методов. Класс предпочтительнее, если lifecycle сложный, состояние должно быть явно представлено, нужны дополнительные методы или объект должен поддерживать более богатый контракт. В обоих случаях важно корректно передавать исключения и не подавлять их случайно.

EN: The generator form is concise for straightforward setup and cleanup when no substantial object state is needed. A class is clearer when the lifecycle is complex, state must be explicit, additional methods are required, or the object has a richer contract. Both forms must preserve exception semantics and avoid accidental suppression.

**FU-3 — What problem does `ExitStack` solve?**

RU: Он управляет переменным количеством ресурсов и позволяет регистрировать их по мере успешного получения. При выходе handlers выполняются в обратном порядке. Это особенно важно, если получение второго или третьего ресурса завершается ошибкой: ранее полученные ресурсы всё равно будут освобождены.

EN: It manages a dynamic number of resources and lets the program register them as acquisition succeeds. Exit handlers run in reverse order. If acquiring a later resource fails, previously acquired resources are still released.

**FU-4 — How should an async context manager behave during task cancellation?**

RU: `__aexit__` должен выполнить необходимый async cleanup, например закрыть ресурс или вернуть соединение в pool. Реализация должна учитывать, что cancellation — часть управления потоком, а не обычная бизнес-ошибка. Нельзя бездумно подавлять cancellation; при необходимости применяются ограниченные cleanup-процедуры и повторное распространение cancellation согласно контракту используемого async framework.

EN: `__aexit__` should perform required asynchronous cleanup, such as closing a resource or returning a connection to a pool. Cancellation is a control-flow signal, not an ordinary business error. Do not suppress it indiscriminately; use bounded cleanup and preserve cancellation according to the async framework's contract.

**FU-5 — How would you scope a database session in a FastAPI application?**

RU: Session должна создаваться на ограниченный request или unit-of-work scope и гарантированно закрываться после завершения. Граница транзакции должна быть явной: application service либо unit-of-work отвечает за commit, а при ошибке выполняется rollback; закрытие session не следует путать с успешным commit. Для streaming response или фоновых задач lifecycle может выходить за пределы обычного request, поэтому ресурс нельзя закрывать раньше времени или неограниченно удерживать. Конкретная схема зависит от sync/async driver и выбранной архитектуры.

EN: Scope the session to a bounded request or unit-of-work lifetime and guarantee closure afterward. Make the transaction boundary explicit: the application service or unit of work owns commit, and failures trigger rollback; closing a session is not equivalent to a successful commit. Streaming responses and background tasks may outlive the ordinary request scope, so resources must neither be closed too early nor held indefinitely. The exact pattern depends on the sync/async driver and application architecture.

### Pharmaviyum application scenario (hypothetical)

**Status: Hypothetical interview scenario — not a claim about the current implementation.**

Imagine an inventory adjustment use case that needs a database transaction and a short-lived distributed lock. The application boundary could acquire both resources with context managers, apply the adjustment, commit only after validation succeeds, and release the lock on every normal or exceptional exit. The design must define lock timeout, transaction ownership, cancellation behavior, and what happens if cleanup itself fails. A context manager should not be used to hide an uncertain commit outcome or to claim exactly-once execution.

### Senior-level evaluation rubric

A strong Senior answer should demonstrate that the candidate:

1. Explains the exact `__enter__` / `__exit__` protocol and exception-suppression semantics.
2. Distinguishes deterministic cleanup from guarantees under process crashes or forced termination.
3. Chooses appropriately between class-based managers, generator-based managers, and `ExitStack`.
4. Understands async context managers and cancellation-sensitive cleanup.
5. Defines explicit resource ownership, lifetime, and transaction boundaries.
6. Recognizes that context managers do not automatically provide thread safety, atomicity, or idempotency.
7. Addresses partial acquisition, reverse-order cleanup, and cleanup failures.

**Evaluation signals**
- Mid-level: uses `with open(...)` and understands basic cleanup.
- Strong Senior: designs correct resource scopes, transaction boundaries, and exception behavior.
- Staff-level signal: establishes consistent lifecycle conventions and failure semantics across application components.

### Common pitfalls

- Assuming `__exit__` is called after every possible process failure.
- Returning a truthy value and unintentionally suppressing an exception.
- Catching an exception in a generator context manager without re-raising it.
- Assuming closing a database session automatically commits a transaction.
- Holding locks or database connections across slow network calls.
- Ignoring cancellation during asynchronous cleanup.
- Acquiring several resources without handling partial setup failure.
- Treating a context manager as a substitute for transaction design, synchronization, or idempotency.

### References

- Python language reference — The `with` statement: https://docs.python.org/3/reference/compound_stmts.html#the-with-statement
- Python data model — With Statement Context Managers: https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers
- `contextlib`: https://docs.python.org/3/library/contextlib.html
- `contextlib.ExitStack`: https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
- Async context managers: https://docs.python.org/3/reference/datamodel.html#asynchronous-context-managers


## PY-CORE-012 — Python modules, packages, and the import system

**Question (EN):** Explain how Python resolves and loads imports. Discuss modules, regular and namespace packages, sys.path, sys.modules, import caching, relative imports, circular dependencies, and import-time side effects. How would you organize a maintainable FastAPI codebase?

**Перевод (RU):** Объясните, как Python разрешает и загружает импорты. Расскажите о модулях, обычных и namespace packages, sys.path, sys.modules, кешировании импортов, относительных импортах, циклических зависимостях и побочных эффектах во время импорта. Как организовать поддерживаемую кодовую базу FastAPI?

### What the interviewer is evaluating

- Understanding of Python import machinery and module identity.
- Ability to distinguish module search paths, finders/loaders, and the module cache.
- Recognition of circular-import and import-time side-effect risks.
- Knowledge of package boundaries, dependency direction, and application startup.
- Practical packaging and testability decisions.

### Model answer (RU)

Модуль Python — единица кода, обычно представленная файлом .py, которая при импорте становится объектом модуля. Package организует модули в иерархию. Обычный package традиционно содержит __init__.py; namespace package может объединять части одного логического package из нескольких каталогов и не требует __init__.py в соответствующих namespace-каталогах. Поэтому неверно утверждать, что каждый package обязан содержать __init__.py.

Оператор import запускает import machinery: finders находят модуль, а loaders создают и исполняют его. sys.path — список путей поиска верхнеуровневых модулей. На него влияют способ запуска Python, окружение и конфигурация интерпретатора. Текущая рабочая директория может участвовать в поиске, но production deployment не должен зависеть от случайного состояния sys.path или ручного изменения sys.path внутри приложения.

После загрузки модуль кешируется в sys.modules по имени. Повторный импорт обычно возвращает тот же объект модуля, а не выполняет тело заново. Важная деталь: модуль помещается в sys.modules до завершения исполнения его тела. Это поддерживает рекурсивные импорты, но при circular import другая сторона может увидеть частично инициализированный модуль. Удаление записей из sys.modules или принудительный reload не являются обычным способом обновления production-кода и могут привести к нескольким объектам модулей с неожиданной identity.

При импорте исполняются инструкции верхнего уровня. Import-time side effects — открытие соединений, чтение секретов, запуск фоновых задач, создание глобальных клиентов или выполнение миграций — делают импорт непредсказуемым и усложняют тестирование, reload и multiprocessing. На уровне модуля лучше оставлять определения и лёгкую декларативную конфигурацию. Инициализацию ресурсов следует выполнять в явной startup/lifespan фазе приложения, а освобождение — в соответствующей shutdown фазе.

Абсолютные импорты явно указывают путь от корня доступного import namespace и обычно удобны для навигации в крупных проектах. Относительные импорты разрешаются относительно текущего package; они полезны внутри связанного package, но могут усложнить перемещение модулей и прямой запуск отдельных файлов. Выбор должен быть последовательным. Запуск через python -m package.module обычно лучше сохраняет package context, чем прямой запуск файла.

Circular import возникает, когда модуль A импортирует B, а B прямо или косвенно импортирует A. Один модуль может быть ещё не полностью инициализирован, поэтому нужное имя может отсутствовать в момент обращения. Локальный импорт внутри функции иногда откладывает зависимость, но часто лишь маскирует архитектурную проблему. Предпочтительно устранить цикл через выделение общего контракта в третий модуль, dependency inversion, передачу зависимостей извне или пересмотр границ пакетов.

Для поддерживаемого FastAPI backend следует разделять API/router слой, application/use-case слой, domain слой и infrastructure adapters. Зависимости должны направляться к стабильным абстракциям, а не создавать взаимные импорты между router, service и repository. Создание приложения, регистрация routers и lifespan orchestration должны быть явными. pyproject.toml описывает metadata и настройки packaging/tooling; воспроизводимая установка должна опираться на объявленные зависимости и выбранный build backend, а не на неявную структуру локальной машины. Тесты должны импортировать приложение без подключения к production-сервисам и нежелательных внешних действий.

### Professional answer (EN)

A Python module is a unit of code, commonly represented by a .py file, which becomes a module object when imported. A package organizes modules hierarchically. A regular package traditionally contains __init__.py; a namespace package can combine portions of one logical package from multiple directories and does not require __init__.py in those namespace directories. Therefore, it is incorrect to claim that every package must contain __init__.py.

An import statement invokes Python's import machinery; it is not merely a file read. Finders locate a module and loaders create and execute it. sys.path is the search path used for top-level module discovery and is influenced by invocation mode, interpreter environment, and configuration. The current working directory may participate, but production applications should not rely on accidental path state or mutate sys.path as an architectural mechanism.

After loading, a module is cached in sys.modules under its import name. Subsequent imports normally return the cached module object rather than executing the module body again. The module is inserted into sys.modules before its body finishes executing, which supports recursive imports but also means a circular dependency can observe a partially initialized module. Deleting cache entries or forcing reload is not a normal production code-update strategy and can create multiple module objects with surprising identity behavior.

Importing executes module-level statements. Import-time side effects—opening connections, reading secrets, starting background tasks, creating global clients, or running migrations—make imports unpredictable and complicate tests, reloads, and multiprocessing. Module scope should generally contain definitions and lightweight declarative configuration. Resource initialization belongs in an explicit application startup/lifespan phase, with cleanup in the corresponding shutdown phase.

Absolute imports make paths explicit from the available import namespace and are often easier to navigate in large codebases. Relative imports are resolved from the current package and can be convenient within a cohesive package, but may complicate module relocation and direct file execution. Consistency matters. Running a module with python -m package.module often preserves package context more reliably than executing the file directly.

A circular import occurs when module A imports B and B directly or indirectly imports A. One side may observe the other before initialization has completed, so a requested name may not yet exist. A local import can defer a dependency, but is usually a workaround rather than an architectural fix. Prefer extracting shared contracts into a third module, applying dependency inversion, injecting dependencies, or revisiting package boundaries.

A maintainable FastAPI backend should separate API/router, application/use-case, domain, and infrastructure-adapter responsibilities. Dependencies should point toward stable abstractions rather than forming mutual imports between routers, services, and repositories. Application creation, router registration, and lifespan orchestration should be explicit. pyproject.toml declares project metadata and packaging/tool configuration; reproducible installation should use declared dependencies and a chosen build backend rather than relying on a developer's local path layout. Tests should import the application without connecting to production services or triggering unintended external actions.

### Follow-up questions and model answers

**FU-1 — What is the difference between sys.path and sys.modules?**

RU: sys.path — список мест, где import machinery ищет верхнеуровневые модули. sys.modules — cache уже обнаруженных или загружаемых модулей, индексируемый по имени. Изменение sys.path влияет на поиск ещё не закешированных импортов; наличие имени в sys.modules обычно позволяет вернуть существующий объект без нового поиска и исполнения.

EN: sys.path is the list of locations used to search for top-level modules. sys.modules is the cache of modules that have been imported or are currently being initialized, keyed by module name. Changing sys.path affects discovery of modules not already satisfied by the cache; an entry in sys.modules normally lets Python reuse the existing module object.

**FU-2 — Why can circular imports fail even though Python caches modules?**

RU: Python помещает объект модуля в sys.modules до полного исполнения его тела. Если второй модуль импортирует первый в этот момент, он может получить частично инициализированный объект, в котором нужное имя ещё не определено. Кеш предотвращает бесконечную повторную загрузку, но не делает циклическую зависимость безопасной.

EN: Python inserts a module object into sys.modules before its body has finished executing. If the second module imports the first at that point, it may receive a partially initialized object whose required name has not yet been defined. Caching prevents unbounded re-import, but it does not make a cyclic dependency safe.

**FU-3 — What is the difference between a regular package and a namespace package?**

RU: Обычный package обычно определяется каталогом с __init__.py. Namespace package может состоять из нескольких portions, расположенных в разных каталогах поиска, и не требует __init__.py в namespace-каталогах. Namespace packages полезны для распределения частей единого пространства имён между независимыми пакетами, но требуют осознанной структуры и понимания поиска модулей.

EN: A regular package is commonly identified by a directory containing __init__.py. A namespace package can consist of multiple portions located in different search locations and does not require __init__.py in those namespace directories. Namespace packages support distributing one logical namespace across independently installed packages, but require deliberate layout and import-path understanding.

**FU-4 — Why are import-time side effects harmful in a web application?**

RU: Они связывают импорт кода с доступностью внешних сервисов и состоянием окружения. Это затрудняет unit tests, CLI usage, migrations, worker startup, application reload и multiprocessing. Создание соединений и запуск задач лучше выполнять в явной lifecycle фазе, где видны ownership, порядок и cleanup.

EN: They couple code import to external-service availability and environment state. This complicates unit tests, CLI use, migrations, worker startup, reloads, and multiprocessing. Connections and background tasks should be created in an explicit lifecycle phase where ownership, ordering, and cleanup are visible.

**FU-5 — How would you diagnose and fix a circular dependency between FastAPI routers, services, and repositories?**

RU: Сначала построить фактический dependency graph и найти цикл, а не добавлять случайные local imports. Затем определить направление зависимостей: router вызывает application service; service зависит от repository port/interface; infrastructure реализует этот интерфейс. Общие схемы и контракты можно вынести в модуль, который не импортирует верхние слои. Конкретные реализации передаются через dependency injection или composition root. После реорганизации проверить importability, тесты и запуск приложения без подключения к production.

EN: First inspect the actual dependency graph and identify the cycle instead of adding arbitrary local imports. Establish a clear direction: routers call application services; services depend on repository ports or interfaces; infrastructure implements those interfaces. Shared contracts can live in a module that does not import higher layers. Concrete implementations are wired through dependency injection or a composition root. Then verify importability, tests, and application startup without production connections.

### Pharmaviyum application scenario (hypothetical)

**Status: Hypothetical interview scenario — not a claim about the current implementation.**

Imagine a FastAPI application where a router imports a service, the service imports a repository implementation, and that repository imports a schema from the router layer. This creates an undesirable dependency cycle. A cleaner design places API schemas and routing in the presentation layer, use cases in the application layer, domain contracts in the domain layer, and database implementations in infrastructure. The application composition root wires concrete adapters. Database pools and external clients are initialized through lifespan rather than as import-time globals. This is an architectural example, not a verified description of the current Pharmaviyum codebase.

### Senior-level evaluation rubric

A strong Senior answer should demonstrate that the candidate:

1. Explains import discovery, module execution, and the roles of sys.path and sys.modules.
2. Understands partially initialized modules and why caching does not eliminate circular-import hazards.
3. Distinguishes regular and namespace packages accurately.
4. Identifies import-time side effects and moves resource initialization into explicit lifecycle management.
5. Chooses absolute or relative imports consistently and understands package execution context.
6. Designs dependency direction and package boundaries that prevent cycles.
7. Understands reproducible packaging and testable application startup.

**Evaluation signals**
- Mid-level: understands imports, packages, and basic module search.
- Strong Senior: diagnoses circular imports and designs clean package boundaries.
- Staff-level signal: defines repository-wide dependency direction, packaging conventions, and lifecycle rules that support multiple entry points and reliable tests.

### Common pitfalls

- Claiming every package must contain __init__.py.
- Confusing sys.path with sys.modules.
- Assuming imports always execute a module body again.
- Treating a circular import as merely a missing-path problem.
- Using local imports to hide an unresolved architectural cycle.
- Creating database connections, clients, or background tasks at import time.
- Depending on the current working directory or manual sys.path mutation in production.
- Making routers, services, and repositories import one another.
- Assuming successful local imports prove a package is correctly built and installable.

### References

- Python tutorial — Modules: https://docs.python.org/3/tutorial/modules.html
- Python reference — The import system: https://docs.python.org/3/reference/import.html
- sys.path and sys.modules: https://docs.python.org/3/library/sys.html
- PEP 420 — Implicit Namespace Packages: https://peps.python.org/pep-0420/
- Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- Python Packaging User Guide — pyproject.toml: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- FastAPI — Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI — Lifespan Events: https://fastapi.tiangolo.com/advanced/events/


## PY-CORE-013 — Python memory management and garbage collection

> **Scope boundary:** Focus on object lifetime, reachability, reference counting as a CPython detail, cyclic GC, weak references, and Python-level retention paths. Process/container memory, RSS interpretation as a service signal, and performance-capacity decisions are handled in Q29.
>
> **Граница темы:** фокус — время жизни объектов, достижимость, reference counting как деталь CPython, cyclic GC, weak references и Python-level retention paths. Память процесса/контейнера, RSS как сигнал состояния сервиса и решения о capacity рассматриваются в Q29.

**Question (EN):** Explain object lifetime and memory reclamation in Python. Discuss reference counting, cyclic garbage collection, reference cycles, weak references, finalization, common memory-retention causes, and how to investigate memory growth in a long-running backend.

**Перевод (RU):** Объясните время жизни объектов и освобождение памяти в Python. Расскажите о reference counting, cyclic garbage collection, reference cycles, weak references, финализации, распространённых причинах удержания памяти и диагностике её роста в долгоживущем backend.

### What the interviewer is evaluating
- Python object lifetime versus process memory usage.
- CPython implementation details versus language guarantees.
- Reference cycles, cyclic GC, weak references, and finalization.
- Ability to identify retention paths and distinguish Python heap growth from RSS/native allocations.
- Production-safe profiling and remediation.

### Model answer (RU)

Объекты Python существуют, пока на них сохраняются достижимые сильные ссылки, но стратегия управления памятью зависит от реализации интерпретатора. В CPython для многих объектов основным механизмом является reference counting: счётчик сильных ссылок изменяется при создании и удалении ссылок. Когда он достигает нуля, объект обычно может быть освобождён. Это особенность CPython, а не гарантия языка Python для всех реализаций. Код не должен полагаться на точный момент уничтожения объекта.

Reference counting не освобождает изолированные циклы ссылок: два объекта могут ссылаться друг на друга, хотя из остальной программы они недостижимы. В CPython cyclic garbage collector обнаруживает определённые циклы среди отслеживаемых объектов-контейнеров и может освободить такие структуры. Не каждый объект обязательно отслеживается сборщиком. Generational collection использует возраст объектов как эвристику; внутренние детали поколений меняются между версиями CPython и не являются стабильным API приложения.

Сам по себе reference cycle не означает утечку. Если цикл достижим из global registry, cache, активной задачи или другого долгоживущего объекта, он остаётся живым. Важнее искать retention path — цепочку сильных ссылок от корня приложения к объекту, который больше не нужен. Типичные причины неконтролируемого удержания: неограниченные caches и collections, глобальные registries, накопление результатов задач, callbacks и closures, подписки без отписки, долгоживущие ссылки на request/session objects, сохранённые tracebacks и exception objects.

Weak reference позволяет ссылаться на объект, не продлевая его жизнь сильной ссылкой. Это полезно для некоторых вспомогательных mappings и caches, где связь не должна удерживать объект. Однако weak references поддерживаются не всеми типами; это зависит от конкретного типа. Слабая ссылка может перестать разрешаться, как только исчезнут сильные ссылки на объект, поэтому она не подходит, если cache обязан гарантированно удерживать значение. Модуль weakref предоставляет, в частности, WeakKeyDictionary и WeakValueDictionary.

Финализация требует осторожности. Нельзя строить корректность программы на точном времени вызова __del__. Финализаторы усложняют анализ циклов, а исключения из __del__ не распространяются вызывающему коду обычным образом. Для детерминированного управления ресурсами предпочтительны context managers и try/finally. weakref.finalize может помочь в отдельных сценариях cleanup, но не заменяет явное закрытие файлов, соединений и других внешних ресурсов. Освобождение внешнего ресурса и освобождение Python memory — разные задачи.

Рост RSS процесса сам по себе не доказывает утечку Python-объектов. Python allocator и системный allocator могут удерживать освобождённые арены для повторного использования, поэтому память не обязана немедленно возвращаться операционной системе. RSS также включает native allocations библиотек, stacks, memory mappings и другие компоненты. Следует разделять рост живых Python allocations, native memory growth и поведение allocator.

Диагностику начинают с воспроизводимого workload и baseline. Измеряют память во времени и сопоставляют её с количеством запросов, размером очередей, количеством задач и cardinality cache. tracemalloc позволяет сравнивать snapshots и находить места выделения Python-памяти; gc предоставляет средства наблюдения за циклическим сборщиком. Для native allocations могут потребоваться системные метрики или специализированные профилировщики. Сравнивать snapshots нужно после одинаковых фаз нагрузки, изучая retainers и проверяя, не объясняется ли рост ожидаемым cache warming или буферизацией. gc.collect() может быть диагностическим экспериментом, но не освобождает объекты, удерживаемые сильными ссылками, и не заменяет устранение причины.

В долгоживущем FastAPI backend следует ограничивать caches и очереди, завершать фоновые tasks, освобождать subscriptions, закрывать ресурсы через lifespan/context managers, не хранить request-scoped данные в глобальном состоянии и контролировать batch/stream buffers. Выводы должны подтверждаться профилем и нагрузочным тестом, а не одним графиком RSS.

### Professional answer (EN)

Python objects remain alive while reachable through strong references, but memory-management strategy depends on the interpreter. In CPython, reference counting is a primary mechanism for many objects: the strong-reference count changes as references are created and removed. When it reaches zero, an object can usually be deallocated. This is a CPython characteristic, not a language-wide guarantee. Code should not depend on the exact time an object is destroyed.

Reference counting cannot reclaim isolated reference cycles. Two objects may reference each other even though nothing else can reach them. CPython's cyclic garbage collector can detect certain cycles among tracked container objects and reclaim unreachable structures. Not every object is necessarily tracked. Generational collection uses object age as a heuristic; internal generation details can change between CPython releases and are not a stable application API.

A reference cycle is not automatically a leak. If it remains reachable from a global registry, cache, active task, or another long-lived object, it is still live. The key concept is a retention path: a chain of strong references from an application root to an object that is no longer needed. Common causes include unbounded caches and collections, global registries, accumulated task results, callbacks and closures, subscriptions that are never removed, long-lived references to request/session objects, and retained tracebacks or exception objects.

A weak reference does not keep its target alive. It is useful for auxiliary mappings or caches when the association should not extend the target's lifetime. However, not every type supports weak references. A weak reference may stop resolving once strong references disappear, so it is unsuitable when a cache must guarantee retention. The weakref module includes WeakKeyDictionary and WeakValueDictionary.

Finalization requires care. Program correctness should not depend on the exact time __del__ runs. Finalizers complicate cycle analysis, and exceptions raised by __del__ are not propagated to the caller normally. Prefer context managers and try/finally for deterministic resource management. weakref.finalize can help in limited cleanup scenarios, but it does not replace explicitly closing files, connections, and other external resources. Releasing an external resource and reclaiming Python memory are separate concerns.

Increasing process RSS does not by itself prove a Python-object leak. Python and system allocators may retain freed arenas for reuse, so memory does not necessarily return to the OS immediately. RSS also includes native allocations, stacks, memory mappings, and other process components. Distinguish growth in live Python allocations from native-memory growth and allocator behavior.

Start with a reproducible workload and baseline. Track memory over time and correlate it with request volume, queue sizes, task counts, and cache cardinality. tracemalloc compares snapshots and identifies Python allocation sites; gc provides visibility into cyclic collection. Native allocations may require system metrics or specialized profilers. Compare snapshots after equivalent workload phases, inspect retainers, and determine whether growth is expected cache warming or buffering. gc.collect() can be a diagnostic experiment, but it cannot reclaim objects retained by strong references and is not a substitute for fixing the cause.

In a long-running FastAPI backend, bound caches and queues, complete background tasks, remove subscriptions, close resources through lifespan/context managers, avoid storing request-scoped data globally, and control batch and stream buffers. Validate conclusions with profiling and load tests rather than a single RSS graph.

### Follow-up questions and model answers

**FU-1 — Why is reference counting insufficient to reclaim every unreachable object?**

RU: Изолированный цикл объектов сохраняет ненулевые reference counts, потому что объекты продолжают ссылаться друг на друга, хотя весь цикл недостижим извне. Поэтому CPython дополняет reference counting циклическим сборщиком для определённых отслеживаемых объектов.

EN: An isolated object cycle retains non-zero reference counts because its objects reference one another even though the cycle is unreachable externally. CPython therefore supplements reference counting with a cyclic collector for certain tracked objects.

**FU-2 — What is the difference between a reference cycle and a memory leak?**

RU: Reference cycle — структура взаимных ссылок, но не обязательно утечка. Если цикл остаётся достижимым из долгоживущего корня, он удерживается. Утечка возможна и без циклов, например при бесконечном добавлении объектов в global list. Нужно искать ненужные retention paths и неверное время жизни объектов.

EN: A reference cycle is a graph of mutual references, not necessarily a leak. If it remains reachable from a long-lived root, it is retained. A leak can also occur without cycles, such as continually appending objects to a global list. Look for unnecessary retention paths and unintended object lifetimes.

**FU-3 — When would you use weakref instead of a normal reference?**

RU: Когда связь не должна продлевать жизнь объекта, например в некоторых auxiliary mappings или caches. Нужно проверить поддержку weak references конкретным типом и учитывать, что объект может исчезнуть после потери сильных ссылок. Если cache обязан удерживать значение, weak reference семантически не подходит.

EN: Use it when an association should not extend an object's lifetime, such as in certain auxiliary mappings or caches. Verify that the target type supports weak references and account for the target disappearing when strong references are gone. If a cache must retain its value, a weak reference has the wrong semantics.

**FU-4 — Why can RSS remain high after Python objects have been collected?**

RU: Allocator может удерживать освобождённые арены для повторного использования, а RSS включает native allocations и другие области памяти процесса. Поэтому RSS не равен объёму живых Python objects. Сопоставляйте RSS с tracemalloc snapshots и при необходимости исследуйте native memory.

EN: The allocator may retain freed arenas for reuse, and RSS includes native allocations and other process memory. RSS is therefore not equivalent to the size of live Python objects. Correlate it with tracemalloc snapshots and investigate native memory when needed.

**FU-5 — How would you investigate steadily increasing memory in a FastAPI worker?**

RU: Зафиксировать воспроизводимый workload и baseline, измерять RSS и Python allocations на одинаковых этапах нагрузки, сравнивать tracemalloc snapshots и искать allocation sites и retention paths. Проверить caches, очереди, фоновые tasks, subscriptions и request-scoped objects. Если Python allocations стабильны, исследовать native extensions и allocator. После исправления повторить нагрузочный тест и подтвердить ограниченный рост. Не использовать gc.collect() как постоянную замену устранению удерживающих ссылок.

EN: Establish a reproducible workload and baseline, measure RSS and Python allocations at equivalent workload stages, compare tracemalloc snapshots, and inspect allocation sites and retention paths. Check caches, queues, background tasks, subscriptions, and request-scoped objects. If Python allocations are stable, investigate native extensions and allocator behavior. Rerun the load test after remediation and verify bounded growth. Do not use gc.collect() as a permanent substitute for removing retaining references.

### Pharmaviyum application scenario (hypothetical)

**Status: Hypothetical interview scenario — not a claim about the current implementation.**

Imagine a long-running API worker whose memory rises during repeated medication-catalog searches. Possible causes include an unbounded result cache, request objects retained in a diagnostic registry, accumulated background-task results, or native allocations in a dependency. Investigate by correlating workload with tracemalloc snapshots, checking cache and queue cardinality, and measuring RSS separately. Potential design measures include bounded caches, explicit task/subscription cleanup, and bounded buffering. These are investigation hypotheses, not verified defects or implemented fixes in Pharmaviyum.

### Senior-level evaluation rubric

A strong Senior answer should:
1. Distinguish Python language guarantees from CPython implementation details.
2. Explain why reference counting cannot reclaim isolated cycles and the role of cyclic GC.
3. Understand that cycles are not automatically leaks and reason about strong-reference retention paths.
4. Use weak references only where their lifetime semantics are appropriate.
5. Avoid relying on __del__ timing for deterministic resource cleanup.
6. Distinguish live Python allocations, native allocations, allocator retention, and RSS.
7. Propose reproducible profiling, snapshot comparison, workload correlation, and post-fix verification.

**Evaluation signals**
- Mid-level: understands references, basic GC, and common object-retention causes.
- Strong Senior: diagnoses retention paths and separates Python heap growth from process RSS.
- Staff-level signal: defines memory budgets, bounded-cache policies, profiling practices, and operational safeguards across services.

### Common pitfalls
- Claiming reference counting is a language-wide guarantee.
- Assuming every reference cycle is a leak.
- Assuming gc.collect() frees objects retained by strong references.
- Treating weak references as a universal leak solution.
- Depending on __del__ for deterministic external-resource cleanup.
- Equating RSS with live Python heap size.
- Expecting memory to return immediately to the OS after collection.
- Ignoring native allocations in extension modules.
- Restarting workers without identifying the retention source.
- Profiling one snapshot without a repeatable workload.

### References
- Python Data Model: https://docs.python.org/3/reference/datamodel.html
- gc — Garbage Collector interface: https://docs.python.org/3/library/gc.html
- weakref — Weak references: https://docs.python.org/3/library/weakref.html
- tracemalloc — Trace memory allocations: https://docs.python.org/3.14/library/tracemalloc.html
- Python C API — Reference Counting: https://docs.python.org/3/c-api/refcounting.html
- Python FAQ — Memory management: https://docs.python.org/3/faq/design.html#how-does-python-manage-memory
- FastAPI — Lifespan Events: https://fastapi.tiangolo.com/advanced/events/


## PY-CORE-014 — Python performance optimization and profiling

> **Scope boundary:** Focus on local Python performance: algorithmic complexity, allocation patterns, `timeit`, `cProfile`, `pstats`, and `tracemalloc`. End-to-end latency percentiles, load generation, saturation, service capacity, scaling, and performance SLOs belong to Q29. Use Q29 rather than duplicating a full service-level performance investigation here.
>
> **Граница темы:** фокус — производительность кода Python: алгоритмическая сложность, аллокации, `timeit`, `cProfile`, `pstats` и `tracemalloc`. End-to-end latency percentiles, нагрузочное тестирование, saturation, capacity сервиса, масштабирование и performance SLO относятся к Q29.

### What the interviewer is evaluating
- Whether the candidate optimizes measured bottlenecks rather than guessing.
- Understanding of algorithmic complexity, constant factors, and memory trade-offs.
- Ability to distinguish CPU-bound, I/O-bound, and memory-bound workloads.
- Correct use of profiling and benchmarking tools.
- Awareness of interpreter overhead, caching risks, and production observability.
- Ability to validate that an optimization improves representative workloads without changing correctness.

### Model answer (RU)
Оптимизация производительности должна начинаться не с переписывания кода, а с измерения и определения узкого места. Сначала нужно описать целевой workload и SLO: например, latency percentiles, throughput, CPU utilization, memory consumption и error rate. Затем воспроизвести характерную нагрузку и собрать baseline.

Big-O описывает асимптотический рост времени или памяти при увеличении входных данных, но не предсказывает абсолютное время выполнения. На практике важны константные множители, распределение данных, аллокации, локальность памяти, I/O и накладные расходы интерпретатора. Алгоритм с худшей асимптотикой может быть быстрее на малых входах, поэтому решение следует подтверждать измерениями.

Для микробенчмарков небольших фрагментов подходит `timeit`; для анализа распределения времени по вызовам Python-функций — `cProfile` и анализ результата через `pstats`. Для памяти Python allocations можно использовать `tracemalloc`; для CPU и native-level проблем могут потребоваться системные профилировщики и метрики процесса. Один profiler не показывает всю картину: например, `cProfile` не является полноценным инструментом измерения ожидания внешнего I/O или native allocations.

Нужно разделять CPU-bound и I/O-bound работу. CPU-bound задачи тратят основное время на вычисления; I/O-bound задачи ожидают сеть, диск, базу данных или другие внешние системы. Асинхронность может повысить конкурентность I/O-bound сервиса, но сама по себе не ускоряет CPU-bound вычисления. Для CPU-bound нагрузки следует исследовать алгоритм, векторизацию, нативные библиотеки, multiprocessing или отдельные worker-процессы — с учётом стоимости сериализации и передачи данных.

Кеширование может уменьшить повторные вычисления или обращения к зависимостям, но добавляет требования к инвалидации, ограничению размера, согласованности, конкурентному доступу и изоляции данных. В многопользовательском backend нельзя допускать, чтобы ключ кеша игнорировал tenant или контекст авторизации. Кешировать следует только после определения корректной семантики и стратегии invalidation.

Корректный benchmark должен использовать репрезентативные входные данные, контролируемую среду, прогрев при необходимости, несколько повторов и статистически осмысленное сравнение. Нужно учитывать шум, cold-start, JIT/интерпретаторные эффекты, конкурирующую нагрузку и различия между локальным тестом и production. После изменения следует повторить тот же workload, сравнить baseline и результат, проверить корректность и наблюдать за production-метриками. Оптимизация считается успешной только если улучшение измеримо и не ухудшает другие SLO или надёжность.

### Professional answer (EN)
I start performance work by defining the representative workload, the user-visible objective, and a measurable baseline. I then profile the system to locate the dominant cost before changing the implementation. Optimizing code that is not on the critical path usually adds complexity without meaningful impact.

Big-O describes asymptotic growth in time or space as input size increases; it does not predict absolute runtime. Constant factors, input distribution, allocation behavior, memory locality, I/O, and interpreter overhead also matter. I use complexity analysis to identify scalability risks and measurements to decide what matters for the actual workload.

For small, isolated timing experiments I use `timeit`. For deterministic profiling of Python call activity I use `cProfile` and inspect results with `pstats`. I use `tracemalloc` to compare Python allocation snapshots. Process-level CPU, RSS, native allocations, database timings, and network waits may require additional system and application instrumentation; no single profiler explains every resource bottleneck.

I distinguish CPU-bound work from I/O-bound work. AsyncIO can improve concurrency when tasks spend substantial time awaiting non-blocking I/O, but it does not make CPU-heavy Python code execute faster. CPU-bound work may require algorithmic improvements, optimized native libraries, vectorization, process-based workers, or a dedicated compute service. Those choices must account for serialization, scheduling, and operational costs.

Caching is a trade-off, not a default optimization. It introduces invalidation, bounded capacity, consistency, concurrency, and authorization-isolation concerns. Cache keys must include every dimension that affects the result, including tenant or user scope where applicable. I only introduce caching when the access pattern and invalidation contract are understood.

A sound benchmark uses representative data, controlled conditions, repeated runs, and an explicit comparison against a baseline. I separate microbenchmarks from end-to-end load tests and evaluate latency percentiles, throughput, CPU, memory, and error rates together. After an optimization, I rerun the same workload, verify functional behavior, and observe the change under production-like conditions. The goal is a demonstrated improvement without regressions in correctness, reliability, or other service objectives.

### Follow-up questions and model answers

**FU-1 — What is the difference between Big-O complexity and measured runtime?**  
**Answer (RU):** Big-O описывает асимптотический порядок роста ресурсов при увеличении размера входа и обычно опускает константы и менее значимые члены. Измеренное время зависит также от реализации, размера входа, оборудования, кешей CPU, аллокаций, I/O и текущей нагрузки. Поэтому Big-O помогает оценить масштабируемость, а benchmark подтверждает поведение конкретной реализации на конкретном workload.  
**Answer (EN):** Big-O describes asymptotic growth and abstracts away constants and lower-order terms. Measured runtime also depends on implementation details, input distribution, hardware, CPU caches, allocations, I/O, and system load. Complexity analysis informs scalability; representative benchmarks validate a particular implementation and workload.

**FU-2 — When would you use `timeit` instead of `cProfile`?**  
**Answer (RU):** `timeit` подходит для изолированного сравнения небольших выражений или функций с минимизацией части измерительного overhead. `cProfile` нужен, чтобы понять, какие вызовы и функции в более крупном Python workload потребляют время и как распределяются вызовы. Нельзя использовать микробенчмарк как доказательство end-to-end улучшения сервиса.  
**Answer (EN):** I use `timeit` to compare small, isolated operations and `cProfile` to identify where a larger Python workload spends time across function calls. A microbenchmark does not establish an end-to-end service improvement; that requires a representative integration or load test.

**FU-3 — Does AsyncIO improve CPU-bound performance?**  
**Answer (RU):** Нет, не автоматически. AsyncIO позволяет эффективно переключаться между задачами во время ожидания неблокирующего I/O. Длительное CPU-bound вычисление блокирует event loop, если его не вынести из него. Нужно рассмотреть оптимизацию алгоритма, native/vectorized implementation, process pool или отдельный compute worker, измерив overhead передачи данных.  
**Answer (EN):** No, not by itself. AsyncIO improves concurrency while tasks await non-blocking I/O. A long CPU-bound operation blocks the event loop unless it is moved elsewhere. Consider algorithmic improvements, native or vectorized code, a process pool, or dedicated compute workers, while measuring data-transfer and scheduling overhead.

**FU-4 — How do you interpret total time and cumulative time in a cProfile/pstats report?**  
**Answer (RU):** total time (internal time) measures time spent directly in a function, excluding its subcalls. cumulative time includes the function and all calls made beneath it. High cumulative time helps identify an important part of the call graph, while high total time points to expensive work inside the function itself. Interpret both alongside call counts and the call-graph structure.  
**Answer (EN):** total time (internal time) показывает время, затраченное непосредственно в функции, без времени её подчинённых вызовов. cumulative time включает время функции и всех вызовов, выполненных из неё. Высокое cumulative time помогает найти важный участок call graph, а высокое total time указывает на дорогую работу внутри самой функции. Эти показатели нужно читать с учётом числа вызовов и структуры call graph.

**FU-5 — Why should profiler output not be treated as an exact benchmark of runtime?**  
**Answer (RU):** Профилировщик добавляет измерительный overhead, который может непропорционально влиять на короткие функции и частые вызовы. Детальный deterministic profiler регистрирует события вызовов и возвратов, поэтому меняет временные характеристики программы. Для сравнения небольших операций используйте timeit, а profiler применяйте для поиска горячих участков; итоговую производительность проверяйте отдельным benchmark без profiler и на репрезентативных условиях.  
**Answer (EN):** A profiler adds measurement overhead, which can disproportionately affect short functions and frequent calls. A detailed deterministic profiler records call and return events, changing the program's timing characteristics. Use timeit to compare small operations and a profiler to locate hot paths; validate runtime separately with an unprofiled benchmark under representative conditions.

### Pharmaviyum application scenario (hypothetical)
A hypothetical interview exercise could ask the candidate to profile a local Python function that normalizes search terms or transforms medicine-catalog results into DTOs. The candidate should define representative inputs and expected semantics, use cProfile/pstats to locate expensive calls, and use timeit to compare isolated alternatives. They should examine algorithmic complexity, redundant passes, and intermediate allocations without changing Unicode handling or medication-attribute correctness. This is an interview scenario, not a claim about the current implementation or measured performance of Pharmaviyum.

### Senior-level evaluation rubric
A strong Senior answer should:
1. Explain asymptotic complexity and the limits of Big-O as a predictor of actual runtime.
2. Choose between timeit, cProfile, and pstats based on the diagnostic question.
3. Distinguish internal time, cumulative time, call counts, and per-call cost.
4. Account for profiler overhead and avoid confusing profiling with benchmarking.
5. Identify algorithmic inefficiencies, redundant passes, excessive calls, and unnecessary intermediate objects.
6. Use tracemalloc to inspect Python allocations without equating its data with total process memory.
7. Validate local optimizations with a separate benchmark and correctness tests.
8. Preserve code readability and semantics while documenting measured trade-offs.

**Evaluation signals**
- Mid-level: knows Big-O and basic timing/profiling tools.
- Strong Senior: interprets profiler output, identifies hot paths, and validates local changes with measurements.
- Staff-level signal: establishes repeatable profiling practices, benchmark methodology, and codebase-level performance regression standards.

### Common pitfalls
- Optimizing based on intuition without profiling.
- Treating Big-O as a prediction of absolute runtime.
- Using a microbenchmark as proof of production improvement.
- Assuming AsyncIO makes CPU-bound code faster.
- Ignoring database, network, serialization, or native-code costs.
- Caching without bounded capacity or a clear invalidation contract.
- Omitting tenant or authorization scope from cache keys.
- Comparing benchmarks under materially different conditions.
- Reporting averages while ignoring tail latency.
- Improving latency while silently increasing memory, errors, or operational complexity.

### References
- Python `timeit`: https://docs.python.org/3.14/library/timeit.html
- Python `cProfile` and `profile`: https://docs.python.org/3.14/library/profile.html
- Python `pstats`: https://docs.python.org/3.14/library/pstats.html
- Python `tracemalloc`: https://docs.python.org/3.14/library/tracemalloc.html
- Python FAQ — Performance: https://docs.python.org/3.14/faq/programming.html#how-can-i-make-my-program-run-faster
- Python asyncio — Developing with asyncio: https://docs.python.org/3.14/library/asyncio-dev.html
- FastAPI — Async: https://fastapi.tiangolo.com/async/


## PY-CORE-015 — Python built-in data structures and collection complexity

### What the interviewer is evaluating
- Knowledge of the operational characteristics of Python's core collection types.
- Ability to choose a data structure based on access patterns, ordering, mutation, and memory requirements.
- Understanding of hash tables, collisions, resizing, and average-case versus worst-case complexity.
- Awareness that complexity guarantees and implementation details can differ across Python implementations.
- Ability to reason about algorithmic trade-offs in real backend workloads.

### Model answer (RU)
Выбор структуры данных должен определяться частыми операциями, требованиями к порядку, уникальности, изменяемости и объёму памяти. Нельзя выбирать коллекцию только по привычке или по одной оценке Big-O.

**List** — изменяемая последовательность с индексированным доступом O(1). Добавление в конец обычно амортизированно O(1), но вставка или удаление в начале и середине требует сдвига элементов и обычно стоит O(n). Поиск по значению — O(n). В CPython список реализован как динамический массив ссылок на объекты; это деталь реализации, а не гарантия языка.

**Tuple** — неизменяемая последовательность. Доступ по индексу — O(1), поиск — O(n). Неизменяемость контейнера не означает, что вложенные объекты неизменяемы. Tuple hashable только если все его элементы hashable.

**Dict** — отображение на основе hash table. Поиск, вставка и удаление в среднем обычно O(1), но в худшем случае могут деградировать до O(n). Равные ключи обязаны иметь одинаковый hash, а hash ключа должен оставаться стабильным, пока ключ находится в словаре. Порядок вставки dict гарантирован языком начиная с Python 3.7; это не означает сортировку ключей.

**Set** хранит уникальные hashable элементы и удобен для membership, дедупликации и операций над множествами. Проверка membership в среднем O(1), worst case — O(n). Set не предназначен для индексированного доступа и не гарантирует порядок элементов.

**Deque** из collections оптимизирован для добавления и удаления с обоих концов: эти операции имеют приблизительно O(1) стоимость. Индексный доступ эффективен у концов, но замедляется ближе к середине; для произвольной индексации обычно лучше list. Bounded deque с maxlen может автоматически вытеснять элементы с противоположного конца — это полезно для rolling windows, но должно быть ожидаемым поведением.

Амортизированное O(1) для append не означает, что каждая операция всегда занимает одинаковое время: resize может потребовать O(n). Среднее O(1) для dict/set не является worst-case гарантией. Big-O также не отражает полностью memory overhead, аллокации, CPU caches и стоимость вычисления hash и equality.

В backend list подходит для упорядоченной коллекции с частым обходом; dict — для поиска по стабильному ключу; set — для membership и дедупликации; deque — для очереди или скользящего окна. Неограниченный рост in-memory коллекции создаёт риск памяти. Для больших или персистентных наборов данных следует рассмотреть базу данных или специализированное хранилище, а не копию в каждом worker.

Senior-инженер должен объяснить ожидаемые и худшие случаи, контракт ключей, стоимость памяти и влияние границ процессов. Практический выбор нужно проверять на репрезентативном workload.

### Professional answer (EN)
I choose a collection based on the operations the application performs most often, together with requirements for ordering, uniqueness, mutability, and memory usage. Big-O is important, but it is not the only decision criterion.

A **list** is a mutable sequence with O(1) indexed access. Appending is amortized O(1), while inserting or deleting near the beginning or middle usually costs O(n) because elements must be shifted. Searching by value is O(n). In CPython, a list is a resizable array of object references; this is an implementation detail, not a language-wide guarantee.

A **tuple** is an immutable sequence with O(1) indexed access and O(n) search. Container immutability does not make nested objects immutable. A tuple is hashable only if all its elements are hashable.

A **dict** is a hash-table-based mapping. Lookup, insertion, and deletion are average-case O(1), but worst-case behavior can degrade to O(n). Equal keys must have equal hashes, and a key's hash must remain stable while it is stored in the mapping. Dictionary insertion order is a language guarantee starting with Python 3.7; it does not mean keys are sorted.

A **set** stores unique hashable elements and is useful for membership checks, deduplication, and set algebra. Membership is average-case O(1), with O(n) worst-case behavior. A set does not provide indexed access or a guaranteed iteration order.

A **deque** from collections is designed for efficient appends and pops at both ends, with approximately O(1) performance for those operations. Indexed access is efficient near the ends and slower toward the middle, so a list is generally preferable for arbitrary indexing. A bounded deque may discard items from the opposite end when new items are appended; that behavior is useful for rolling windows but must be intentional.

Amortized O(1) append does not mean every append has identical cost: a resize can take O(n). Average-case O(1) for dict and set is not a worst-case guarantee. Big-O also does not fully capture memory overhead, allocations, CPU cache behavior, or the cost of hashing and equality comparisons.

For backend design, I map structures to access patterns: lists for ordered iteration, dictionaries for key-based lookup, sets for membership and deduplication, and deques for queues or rolling windows. Unbounded in-memory collections can create memory and consistency problems, especially when each worker maintains its own copy. Large or persistent datasets may belong in a database or dedicated storage instead.

A Senior engineer should explain expected and worst-case behavior, key-contract constraints, memory costs, and process boundaries, then validate the choice against a representative workload.

### Follow-up questions and model answers

**FU-1 — Why is list append amortized O(1), and when can an individual append be O(n)?**  
**Answer (RU):** Динамический массив резервирует дополнительную ёмкость, поэтому большинство append не требует перемещения элементов. Когда место заканчивается, массив расширяется и ссылки могут копироваться в новое хранилище; отдельная операция стоит O(n). Амортизированный анализ распределяет стоимость редких расширений по последовательности append, поэтому средняя стоимость остаётся O(1).  
**Answer (EN):** A dynamic array keeps spare capacity, so most appends do not move existing elements. When capacity is exhausted, it may allocate a larger buffer and copy references, making that operation O(n). Amortized analysis spreads these occasional costs across a sequence of appends, yielding O(1) amortized cost per append.

**FU-2 — What happens when dictionary keys have colliding hashes?**  
**Answer (RU):** Коллизия означает, что разные ключи имеют одинаковый hash, но не обязательно равны. Dict разрешает коллизию и использует equality comparison для определения нужного ключа. Много коллизий может ухудшить производительность вплоть до O(n). Пользовательские ключи должны иметь корректные и стабильные __hash__ и __eq__; hash не должен зависеть от изменяемого состояния ключа.  
**Answer (EN):** A collision means distinct keys produce the same hash; it does not mean they are equal. The dictionary resolves collisions and uses equality comparisons to identify the requested key. Excessive collisions can degrade operations, potentially to O(n). Custom keys need correct, stable __hash__ and __eq__ behavior, and their hash must not depend on mutable state while stored.

**FU-3 — When would you choose deque instead of list?**  
**Answer (RU):** Deque подходит, когда часто добавляют и удаляют элементы с обоих концов: например FIFO queue или bounded rolling window. Операции list.pop(0) и insert(0, item) требуют сдвига элементов и стоят O(n). Для произвольного индексного доступа и последовательного обхода обычно лучше list.  
**Answer (EN):** I choose deque when the workload frequently appends and removes items at both ends, such as a FIFO queue or bounded rolling window. list.pop(0) and insertion at index zero require shifting elements and cost O(n). A list is generally preferable when arbitrary indexed access and sequential iteration dominate.

**FU-4 — Does Python guarantee dictionary and set iteration order?**  
**Answer (RU):** Порядок вставки dict гарантирован языком начиная с Python 3.7. Обновление существующего ключа не перемещает его, а удаление и повторная вставка помещает его в новую позицию. Set не предоставляет аналогичной гарантии. Порядок вставки dict — не сортировка; для отсортированного результата нужна явная сортировка.  
**Answer (EN):** Dictionary insertion order is a language guarantee starting with Python 3.7. Updating an existing key does not move it, while deleting and reinserting it places it at a new position. Sets do not provide the same ordering guarantee. Dictionary insertion order is not sorting; explicit sorting is required when sorted output is needed.

**FU-5 — What collection-related risks matter in a multi-worker backend?**  
**Answer (RU):** In-memory коллекции принадлежат процессу и не являются общим хранилищем между workers. У каждого worker может быть собственная копия, что создаёт расхождение состояния, дублирование памяти и сложности инвалидации. Локальный dict или set не является механизмом межпроцессной синхронизации или distributed locking. Для общего состояния нужны внешние системы, транзакции и определённая модель согласованности; рост коллекций также нужно ограничивать.  
**Answer (EN):** In-memory collections belong to a process; they are not shared storage across workers. Each worker may hold a separate copy, causing divergent state, duplicated memory, and difficult invalidation. A local dict or set is not a cross-process coordination or distributed-locking mechanism. Shared state requires an external system, transactions, and an explicit consistency model; collection growth must also be bounded.

### Pharmaviyum application scenario (hypothetical)
A hypothetical interview exercise could ask how to represent a batch of medicine search results, deduplicate identifiers, and maintain a bounded recent-query window. A list could preserve result order, a set could track identifiers already seen, a dict could map stable identifiers to result objects, and a bounded deque could retain recent events. Discuss memory limits, worker-local state, and whether data must be shared or persisted. This is an interview scenario, not a claim about the current implementation of Pharmaviyum.

### Senior-level evaluation rubric
A strong Senior answer should:
1. Select collections from concrete access patterns and correctness requirements.
2. Explain average, worst-case, and amortized complexity accurately.
3. Understand hash collisions and the __eq__ / __hash__ contract.
4. Distinguish dictionary insertion order from sorting and set iteration order.
5. Explain why deque suits operations at both ends but not arbitrary indexing.
6. Account for memory overhead, bounded growth, and process-local state.
7. Avoid treating in-memory collections as distributed coordination or persistence.
8. Validate performance claims with representative workloads.

**Evaluation signals**
- Mid-level: identifies common collection types and basic operation costs.
- Strong Senior: selects structures based on access patterns, collision behavior, memory constraints, and process boundaries.
- Staff-level signal: establishes data-structure and memory policies for high-volume services and recognizes when state belongs in shared infrastructure.

### Common pitfalls
- Claiming list append is always worst-case O(1).
- Treating average-case dict/set O(1) as a worst-case guarantee.
- Assuming different keys cannot have the same hash.
- Mutating hash-relevant state while an object is used as a dict or set key.
- Assuming tuple is always hashable.
- Assuming set iteration order is stable or meaningful.
- Using list.pop(0) for a high-volume queue.
- Choosing deque when arbitrary indexing dominates.
- Treating per-process collections as shared state across workers.
- Allowing caches, queues, or registries to grow without bounds.

### References
- Python Tutorial — Data Structures: https://docs.python.org/3/tutorial/datastructures.html
- Python Built-in Types — Sequence Types: https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range
- Python Built-in Types — Mapping Types: https://docs.python.org/3/library/stdtypes.html#mapping-types-dict
- Python Built-in Types — Set Types: https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset
- Python collections.deque: https://docs.python.org/3/library/collections.html#collections.deque
- Python Data Model — __hash__: https://docs.python.org/3/reference/datamodel.html#object.__hash__


## PY-CORE-016 — Python strings, Unicode, encoding, and text processing

### What the interviewer is evaluating
- Python's Unicode text model and the distinction between text and encoded bytes.
- Code points, grapheme clusters, normalization, and display length.
- Correct encoding and decoding at system boundaries.
- Security and correctness risks in multilingual input processing.
- Robust text-processing APIs and tests.

### Model answer (RU)
В Python 3 тип str представляет текст как последовательность Unicode code points, а не байтов. Строки неизменяемы: операции, которые концептуально изменяют строку, создают новый объект. len(str) возвращает количество code points, а не байтов и не обязательно количество видимых пользователю символов. Визуально один символ может состоять из нескольких code points, например базовой буквы и комбинируемого диакритического знака; такая последовательность может образовывать один grapheme cluster.

Нужно различать три уровня:
- **Code point** — числовая позиция Unicode, например U+0065.
- **Grapheme cluster** — последовательность code points, воспринимаемая пользователем как один графический символ.
- **Encoded bytes** — байтовое представление текста в конкретной кодировке, например UTF-8.

Python str не предоставляет универсального встроенного метода подсчёта grapheme clusters. Если приложению нужно ограничивать длину текста по количеству символов, воспринимаемых пользователем, следует использовать библиотеку с поддержкой Unicode grapheme segmentation, а не полагаться только на len().

bytes — неизменяемая последовательность байтов, bytearray — изменяемая. Индексация bytes возвращает целое число от 0 до 255, а индексация str возвращает строку длиной один code point. Преобразование должно быть явным: text.encode("utf-8") кодирует str в bytes, а data.decode("utf-8") декодирует bytes в str. Не любой набор байтов является корректным UTF-8.

Стандартный режим обработки ошибок encoding/decoding — strict, который поднимает UnicodeEncodeError или UnicodeDecodeError. Режимы replace и ignore могут подходить для отдельных recovery workflows, но ignore способен незаметно уничтожить данные. Для медицинских, идентификационных и иных критичных полей молчаливая потеря символов особенно опасна. Нужно явно определить ожидаемую кодировку на границе системы, а не угадывать её без надёжного протокола.

Unicode normalization решает проблему канонически эквивалентных представлений. Символ с диакритикой может быть представлен одним предварительно составленным code point или базовым символом плюс combining mark. unicodedata.normalize() поддерживает NFC, NFD, NFKC и NFKD. NFC часто полезна для канонической нормализации. NFKC дополнительно применяет compatibility transformations, которые могут менять различия, значимые для домена; её нельзя бездумно применять ко всем пользовательским данным, идентификаторам или медицинским обозначениям. Нормализацию выбирают под конкретную задачу и сохраняют исходный ввод, если его точное воспроизведение важно.

F-strings, str.format() и оператор % используются для форматирования. F-strings удобны для интерполяции выражений, но произвольный пользовательский шаблон нельзя считать безопасным исполняемым шаблоном. Нельзя выполнять eval() над пользовательскими строками форматирования. Для SQL, shell-команд, HTML и URL нужны контекстно-специфичные параметризованные API или escaping, а не обычное форматирование строк.

Модуль re поддерживает регулярные выражения; Unicode-зависимые классы и флаги нужно оценивать в контексте задачи. Например, Unicode-класс \w не эквивалентен строгому определению латинских букв или доменного идентификатора. Regex не заменяет полноценный парсер сложных форматов. Нужно учитывать ReDoS: неудачный шаблон на специально подобранном вводе может вызвать чрезмерное время выполнения. Для недоверенного ввода нужны ограничения размера, осторожные шаблоны и подходящие механизмы таймаута либо альтернативный парсер.

String interning — оптимизация реализации, при которой некоторые строки могут разделять один объект. Нельзя использовать is для сравнения содержимого строк и полагаться на интернирование. Для сравнения значений используется ==. Внутреннее представление строк CPython — деталь реализации, а не гарантия языка.

В production backend текст обрабатывают на чётко определённых границах: декодируют входные байты с известной кодировкой, валидируют допустимые символы и длины, нормализуют только при обосновании доменом, сохраняют корректное Unicode-представление и правильно кодируют выход. Тесты должны включать кириллицу, латиницу, combining marks, emoji, некорректные byte sequences, смешанные письменности и визуально похожие символы. Для multilingual retrieval важно не терять исходный текст и не применять преобразования, меняющие медицинские термины или идентификаторы.

### Professional answer (EN)
In Python 3, str represents text as a sequence of Unicode code points, not bytes. Strings are immutable, so operations that conceptually modify a string create a new object. len(str) counts code points; it does not count encoded bytes and does not necessarily count user-perceived characters. A visible character can consist of multiple code points, such as a base letter followed by a combining mark, forming one grapheme cluster.

Distinguish three levels:
- **Code point**: a numbered Unicode value, such as U+0065.
- **Grapheme cluster**: a sequence of code points perceived as one user-facing character.
- **Encoded bytes**: text represented in a specific encoding, such as UTF-8.

Python str does not provide a universal built-in grapheme-cluster counter. If an application must enforce user-perceived character limits, use a library implementing the relevant Unicode grapheme segmentation rules rather than relying on len() alone.

bytes is immutable, while bytearray is mutable. Indexing bytes returns an integer from 0 to 255; indexing str returns a one-code-point string. Conversion should be explicit: text.encode("utf-8") encodes a string, and data.decode("utf-8") decodes bytes. Not every arbitrary byte sequence is valid UTF-8.

Encoding and decoding default to strict error handling, raising UnicodeEncodeError or UnicodeDecodeError. Modes such as replace and ignore can be appropriate for specific recovery workflows, but ignore can silently destroy information. For medical, identity, or other critical fields, silent character loss is especially risky. Define the expected encoding at system boundaries instead of guessing without a reliable protocol.

Unicode normalization addresses canonically equivalent representations. A character with a diacritic may be represented as one precomposed code point or as a base character plus a combining mark. unicodedata.normalize() supports NFC, NFD, NFKC, and NFKD. NFC is often useful for canonical normalization. NFKC also applies compatibility transformations and may erase distinctions meaningful to a domain, so it should not be applied indiscriminately to user data, identifiers, or medication terminology. Choose normalization according to domain requirements and preserve original input when exact reproduction matters.

Python supports formatting through f-strings, str.format(), and the % operator. F-strings are convenient, but arbitrary user-provided format strings must not be treated as safe executable templates. Never use eval() on untrusted formatting input. SQL, shell commands, HTML, and URLs require context-specific parameterized APIs or escaping; ordinary string formatting is not a substitute.

The re module supports regular expressions, but Unicode-sensitive character classes and flags must be understood in context. Unicode \w is not equivalent to a strict definition of Latin letters or a domain-specific identifier. Regular expressions are not a replacement for proper parsers for complex formats. Also consider regular-expression denial of service (ReDoS): a poorly designed pattern may take excessive time on crafted input. Bound untrusted input, use safe patterns, and choose timeout-capable mechanisms or another parser when appropriate.

String interning is an implementation optimization under which some strings may share an object. Do not compare string values with is or rely on interning behavior. Use == for value equality. CPython's internal string representation is also an implementation detail, not a language guarantee.

In a production backend, process text at explicit boundaries: decode incoming bytes using a known encoding, validate allowed characters and lengths, normalize only when the domain justifies it, preserve valid Unicode text, and encode output correctly. Tests should include Cyrillic, Latin text, combining marks, emoji, malformed byte sequences, mixed scripts, and visually confusable characters. For multilingual retrieval, preserve original text and avoid transformations that alter medication terminology or identifiers.

### Follow-up questions and model answers

**FU-1 — Why can len("é") differ from the number of bytes or user-perceived characters?**  
**Answer (RU):** len() для str считает Unicode code points. В UTF-8 один code point может занимать несколько байтов. Визуально один символ также может состоять из нескольких code points, например буквы и combining mark, образующих один grapheme cluster. Поэтому длина в code points, байтах и grapheme clusters — разные метрики.  
**Answer (EN):** len() on a string counts Unicode code points. A code point may occupy multiple bytes in UTF-8. One visible character may also consist of multiple code points, such as a letter and combining mark forming one grapheme cluster. Code-point length, byte length, and grapheme-cluster count are different measurements.

**FU-2 — When should you use str, bytes, and bytearray?**  
**Answer (RU):** str используют для декодированного текста. bytes подходит для неизменяемых бинарных данных и результатов encoding. bytearray нужен, когда бинарный буфер требуется изменять на месте. Кодирование и декодирование должны происходить на явных границах протокола, а не произвольно внутри бизнес-логики.  
**Answer (EN):** Use str for decoded text, bytes for immutable binary data and encoded payloads, and bytearray when a mutable binary buffer is required. Encoding and decoding should happen at explicit protocol boundaries rather than being scattered throughout business logic.

**FU-3 — What is the difference between NFC and NFKC, and why does it matter?**  
**Answer (RU):** NFC приводит канонически эквивалентные последовательности к канонической форме композиции. NFKC дополнительно применяет compatibility mappings, которые могут устранить различия между некоторыми символами. Это помогает отдельным задачам поиска, но может изменить значимые различия в идентификаторах, названиях и медицинских терминах. Выбор формы должен быть частью доменного контракта; исходный ввод следует сохранять для аудита или отображения.  
**Answer (EN):** NFC normalizes canonically equivalent sequences toward composed canonical forms. NFKC additionally applies compatibility mappings that can remove distinctions between some characters. This can help selected search tasks but may alter distinctions meaningful in identifiers, names, and medication terminology. Normalization should be part of the domain contract, and original input should be retained when needed for audit or display.

**FU-4 — Why is is incorrect for comparing string values, and what is string interning?**  
**Answer (RU):** is проверяет identity объектов, а == — равенство значений. Интернирование позволяет реализации повторно использовать один объект для некоторых строк, но это оптимизация, а не контракт сравнения. Поведение зависит от реализации и контекста. Сравнивать текст нужно через ==.  
**Answer (EN):** is tests object identity, whereas == tests value equality. Interning allows an implementation to reuse an object for some strings, but it is an optimization rather than a comparison contract. Its behavior can vary by implementation and context. Compare string content with ==.

**FU-5 — What text-processing risks should a multilingual healthcare backend address?**  
**Answer (RU):** Нужно явно определять encoding на границах системы, контролируемо обрабатывать некорректные byte sequences, сохранять исходный текст и применять normalization только по обоснованным правилам. Валидация должна учитывать code points, grapheme clusters, смешанные письменности и визуально похожие символы. Для поиска лекарств нельзя без тестирования менять регистр, удалять диакритические знаки или применять compatibility normalization: это может объединить разные термины. Также нужны защита от ReDoS, контекстное escaping и параметризованные запросы.  
**Answer (EN):** Define encodings explicitly at system boundaries, handle malformed byte sequences deliberately, preserve original text, and normalize only under justified rules. Validation should account for code points, grapheme clusters, mixed scripts, and visually confusable characters. Medication search must not blindly case-fold, strip diacritics, or apply compatibility normalization because these transformations can collapse distinct terms. Also address ReDoS, context-specific escaping, and parameterized queries.

### Pharmaviyum application scenario (hypothetical)
A hypothetical interview scenario could involve medicine names and search queries entered in Cyrillic and Latin scripts, with diacritics or visually similar characters. Explain how to preserve the original query, define normalization and case-folding rules for retrieval, validate encoding at API boundaries, and test that distinct medication names are not accidentally merged. This is an interview scenario, not a claim about the current implementation of Pharmaviyum.

### Senior-level evaluation rubric
A strong Senior answer should:
1. Distinguish Unicode code points, grapheme clusters, and encoded bytes.
2. Explain str, bytes, bytearray and place encoding/decoding at explicit boundaries.
3. Handle malformed input deliberately rather than silently discarding characters.
4. Select normalization according to domain semantics and preserve source text when needed.
5. Use == for string values and treat interning as an implementation optimization.
6. Understand Unicode behavior and limitations of regular expressions and recognize ReDoS risks.
7. Avoid unsafe interpolation for SQL, shell, HTML, and other structured contexts.
8. Design multilingual tests with combining marks, emoji, mixed scripts, and confusables.

**Evaluation signals**
- Mid-level: understands Unicode strings and basic encode/decode operations.
- Strong Senior: designs explicit text boundaries, normalization policies, and multilingual validation.
- Staff-level signal: defines shared text-handling contracts that preserve domain semantics, auditability, and security across services.

### Common pitfalls
- Assuming len(str) counts visible characters.
- Treating str as UTF-8 bytes.
- Decoding arbitrary bytes without knowing the encoding.
- Using errors="ignore" on critical data.
- Applying NFKC indiscriminately to identifiers or domain terminology.
- Comparing strings with is.
- Depending on string interning or CPython representation details.
- Treating Unicode \w as a universal definition of valid letters or identifiers.
- Using regex as a parser for complex formats.
- Building unsafe SQL or shell commands with f-strings.
- Ignoring ReDoS and Unicode confusable-character risks.

### References
- Python Standard Types — Text Sequence Type str: https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str
- Python Standard Types — Binary Sequence Types: https://docs.python.org/3/library/stdtypes.html#binary-sequence-types-bytes-bytearray-memoryview
- Python str.encode and bytes.decode: https://docs.python.org/3/library/stdtypes.html#str.encode
- Python unicodedata: https://docs.python.org/3/library/unicodedata.html
- Python Regular Expression HOWTO: https://docs.python.org/3/howto/regex.html
- Python re documentation: https://docs.python.org/3/library/re.html
- Unicode Standard Annex #29 — Text Segmentation: https://www.unicode.org/reports/tr29/
- Unicode Technical Standard #15 — Normalization: https://www.unicode.org/reports/tr15/


## PY-CORE-017 — Python Concurrency Fundamentals: Threads, Processes and the GIL

### Interview question
**Explain concurrency and parallelism in Python. Compare threads and processes, describe the Global Interpreter Lock (GIL), and explain how you would choose an execution model for a production backend.**

### Перевод вопроса
Объясните concurrency и parallelism в Python. Сравните потоки и процессы, опишите Global Interpreter Lock (GIL) и расскажите, как выбрать модель выполнения для production backend.

### What the interviewer evaluates
- Distinguishing concurrency from parallel execution.
- Understanding CPython's GIL without treating it as a universal Python-language guarantee.
- Selecting threads, processes, or asynchronous I/O based on workload characteristics.
- Understanding shared-state hazards, synchronization, and process isolation.
- Accounting for serialization, memory, startup, scheduling, cancellation, and observability.
- Awareness of evolving CPython builds, including optional free-threaded builds.

### Model answer (RU)
**Concurrency** — способность системы организовывать выполнение нескольких задач так, чтобы их прогресс перекрывался во времени. **Parallelism** означает фактическое одновременное выполнение нескольких вычислений, например на разных CPU cores. Concurrency не обязательно требует нескольких ядер: event loop может переключаться между I/O-bound задачами на одном потоке, пока они ожидают завершения операций ввода-вывода.

В традиционной GIL-enabled сборке CPython Global Interpreter Lock ограничивает выполнение Python bytecode одним потоком одновременно в рамках одного interpreter. Поэтому дополнительные threads обычно не дают линейного ускорения для CPU-bound Python-кода. Однако потоки полезны для I/O-bound операций: пока один поток ожидает сеть, диск или блокирующий системный вызов, другой может продвигаться. Некоторые native extensions освобождают GIL во время отдельных операций, поэтому фактическое поведение зависит от используемой библиотеки.

**Threads** используют общее адресное пространство процесса. Совместное использование объектов удобно, но shared mutable state создаёт риск race conditions. Наличие GIL не делает составные операции или бизнес-инварианты автоматически атомарными. Для синхронизации применяют Lock, RLock, Semaphore, Condition и потокобезопасные структуры. Критические секции должны быть небольшими; порядок захвата блокировок следует проектировать так, чтобы снижать contention и риск deadlock.

**Processes** имеют отдельные адресные пространства и позволяют выполнять CPU-bound работу параллельно на нескольких ядрах. Цена — более высокие затраты на запуск и память, IPC, сериализацию/десериализацию и управление жизненным циклом. Передача больших объёмов данных между процессами может оказаться дороже самой работы. Для независимых CPU-bound задач подходит process pool; его размер следует ограничивать и согласовывать с количеством доступных CPU, лимитами контейнера и общей нагрузкой сервиса.

Для backend я выбираю модель по характеру работы:
- Для большого числа сетевых операций и поддерживаемых async-библиотек — asyncio и async I/O.
- Для блокирующих I/O-библиотек — ограниченный thread pool или перенос вызова в подходящий worker.
- Для CPU-bound Python-кода — process pool или отдельный worker service; threads в обычной GIL-enabled сборке обычно не обеспечивают параллельное исполнение Python bytecode.
- Для тяжёлой или длительной фоновой работы — очередь задач и отдельные workers, а не выполнение внутри HTTP request lifecycle.

GIL — деталь реализации конкретного runtime, прежде всего традиционного CPython, а не гарантия языка Python. Начиная с Python 3.13 доступны optional free-threaded builds, в которых GIL может быть отключён; это не означает, что любая установка Python автоматически работает без GIL. Совместимость расширений, внутренние блокировки runtime и реальная производительность требуют проверки на целевой сборке. Даже без GIL остаются race conditions и необходимость корректной синхронизации.

В production решение нужно подтверждать profiling и нагрузочными тестами. Следует измерять throughput, latency (включая p95/p99), CPU, memory, queue depth, context switching, lock contention и ошибки. Также необходимо учитывать graceful shutdown, cancellation, timeouts, backpressure и ограничение параллелизма. Нельзя выбирать threads или processes только по общему правилу без измерения конкретной нагрузки.

### Professional answer (EN)
**Concurrency** is the ability to structure multiple tasks so that their progress overlaps in time. **Parallelism** is the simultaneous execution of multiple computations, for example on separate CPU cores. A system can be concurrent without executing work in parallel: a single-threaded event loop can interleave I/O-bound tasks while they wait.

In a traditional GIL-enabled CPython build, the Global Interpreter Lock allows only one thread at a time to execute Python bytecode within an interpreter. Consequently, adding threads generally does not scale CPU-bound pure-Python code across cores. Threads are still useful for I/O-bound workloads because another thread can make progress while one is blocked on network, disk, or a blocking system call. Some native extensions release the GIL around selected operations, so library behavior matters.

**Threads** share a process address space. Sharing data is convenient, but shared mutable state introduces race conditions. The GIL does not make compound application-level operations or business invariants automatically atomic. Use synchronization primitives such as Lock, RLock, Semaphore, and Condition, or prefer message passing and immutable data where practical. Keep critical sections small and define lock ordering to reduce contention and deadlock risk.

**Processes** have separate address spaces and can execute CPU-bound work in parallel across cores. They introduce additional costs: process startup, memory, inter-process communication, serialization, and lifecycle management. Large payload transfer can outweigh the computation itself. A bounded process pool is appropriate for independent CPU-bound tasks, with capacity chosen against available CPU resources, container limits, and overall service load.

For a backend, choose based on the workload:
- Use asyncio and async I/O for high-concurrency network workloads when the libraries support non-blocking operation.
- Use a bounded thread pool for blocking I/O libraries that cannot be made asynchronous.
- Use a process pool or separate worker service for CPU-bound Python workloads on a conventional GIL-enabled build.
- Use a task queue and dedicated workers for long-running or resource-intensive background jobs rather than tying them to an HTTP request lifecycle.

The GIL is a runtime implementation detail, primarily associated with conventional CPython builds, not a universal Python language guarantee. Optional free-threaded CPython builds have been available since Python 3.13; a normal Python installation should not be assumed to be free-threaded. Extension compatibility, runtime synchronization, and actual performance must be validated on the target build. Removing the GIL does not remove data races or the need for synchronization.

Validate the design with profiling and representative load tests. Measure throughput, p95/p99 latency, CPU and memory usage, queue depth, context switching, lock contention, and errors. Account for graceful shutdown, cancellation, timeouts, backpressure, and bounded concurrency. Do not select threads or processes by slogan; select them from measured workload behavior.

### Subinterpreters and modern CPython concurrency (Python 3.14+)

**RU:** Начиная с Python 3.14, стандартная библиотека предоставляет `concurrent.interpreters` и `concurrent.futures.InterpreterPoolExecutor`. Subinterpreters — отдельные изолированные interpreter instances с ограниченным совместным использованием объектов; это не то же самое, что free-threaded build, где несколько потоков могут выполнять Python-код параллельно в одном interpreter без традиционного GIL. Важно различать API управления интерпретаторами и механизм конкурентного выполнения: `concurrent.interpreters` сам по себе не запускает дополнительные потоки; для параллельной работы используются threads, например `InterpreterPoolExecutor`, где каждый worker thread работает в собственном interpreter. Изоляция уменьшает часть рисков shared mutable state, но не является security boundary: интерпретаторы работают в одном процессе, а native extensions могут нарушить предположения об изоляции. Совместимость сторонних C-extension модулей нельзя предполагать: её нужно проверять. Выбор между threads, processes, interpreters и free-threaded runtime должен опираться на workload, поддержку зависимостей, memory overhead и измерения, а не на обещание автоматического ускорения.

**EN:** Starting with Python 3.14, the standard library provides `concurrent.interpreters` and `concurrent.futures.InterpreterPoolExecutor`. Subinterpreters are separate, isolated interpreter instances with constrained object sharing; they are not the same as a free-threaded build, where multiple threads can execute Python code in parallel within one interpreter without the traditional GIL. Distinguish the interpreter-management API from concurrent execution: `concurrent.interpreters` does not start additional threads by itself; parallel work uses threads, for example `InterpreterPoolExecutor`, where each worker thread runs in its own interpreter. Isolation reduces some shared-mutable-state risks but is not a security boundary: interpreters run in the same process, and native extensions may violate isolation assumptions. Third-party C-extension compatibility must be verified rather than assumed. Choose among threads, processes, interpreters, and a free-threaded runtime based on workload, dependency support, memory overhead, and measurements—not an assumption of automatic speedup.

**References:** What's New in Python 3.14 — https://docs.python.org/3.14/whatsnew/3.14.html ; concurrent.interpreters — https://docs.python.org/3.14/library/concurrent.interpreters.html ; concurrent.futures — https://docs.python.org/3.14/library/concurrent.futures.html

### Follow-up questions and model answers

**FU-1 — Why does adding more threads usually not speed up CPU-bound pure-Python code in a traditional CPython build?**  
**Answer (RU):** В GIL-enabled CPython потоки конкурируют за GIL, поэтому в каждый момент Python bytecode исполняет один поток на interpreter. Дополнительные потоки добавляют переключения контекста и синхронизацию, но обычно не дают параллельного исполнения Python bytecode на нескольких ядрах. Исключения возможны, когда вычисления выполняются в native code, освобождающем GIL.  
**Answer (EN):** In a GIL-enabled CPython build, threads contend for the GIL, so only one thread executes Python bytecode in an interpreter at a time. Additional threads add scheduling and synchronization overhead without usually providing multi-core parallel execution of Python bytecode. Native code that releases the GIL is an important exception.

**FU-2 — If the GIL exists, why can a threaded program still have race conditions?**  
**Answer (RU):** GIL не является application-level mutex и не защищает бизнес-инварианты. Между отдельными операциями поток может уступить управление; операции над общим состоянием могут состоять из нескольких шагов, а native code может освобождать GIL. Нужны явная синхронизация, thread-safe abstractions или передача сообщений.  
**Answer (EN):** The GIL is not an application-level mutex and does not protect business invariants. Threads can interleave between operations, compound state changes involve multiple steps, and native code may release the GIL. Use explicit synchronization, thread-safe abstractions, or message passing.

**FU-3 — When would you choose asyncio, threads, or processes for a FastAPI endpoint?**  
**Answer (RU):** Asyncio подходит для большого числа I/O-bound операций, если весь путь использует неблокирующие библиотеки. Thread pool уместен для ограниченного числа блокирующих I/O-вызовов. Process pool или отдельный worker нужен для CPU-bound Python-вычислений. Выбор зависит также от latency budget, отмены, размера payload, лимитов ресурсов и измерений под нагрузкой.  
**Answer (EN):** Use asyncio for high-concurrency I/O when the full call path uses non-blocking libraries. Use a bounded thread pool for blocking I/O calls. Use a process pool or dedicated worker for CPU-bound Python computation. Also consider latency budgets, cancellation, payload size, resource limits, and load-test results.

**FU-4 — What are the main costs and failure modes of multiprocessing?**  
**Answer (RU):** Основные затраты — запуск процессов, дополнительная память, serialization, IPC и управление жизненным циклом. Типичные проблемы: слишком большой pool, исчерпание памяти/CPU, дорогая передача больших объектов, зависшие workers, некорректная обработка ошибок и shutdown. Нужны ограниченные очереди и pool, timeouts, мониторинг и идемпотентная обработка задач там, где возможны повторы.  
**Answer (EN):** The main costs are process startup, additional memory, serialization, IPC, and lifecycle management. Failure modes include oversized pools, resource exhaustion, expensive large-payload transfers, stuck workers, and incorrect error or shutdown handling. Use bounded pools and queues, timeouts, monitoring, and idempotent task handling where retries are possible.

**FU-5 — What changes with free-threaded CPython, and what does not change?**  
**Answer (RU):** Free-threaded build может позволить нескольким потокам выполнять Python code параллельно, но это не гарантирует ускорение каждого приложения. Возможны дополнительные затраты синхронизации, а C extensions должны быть совместимы с free-threaded runtime. Race conditions, deadlocks и необходимость защиты shared mutable state остаются. Нужно проверять фактическую конфигурацию runtime и измерять приложение на ней.  
**Answer (EN):** A free-threaded build can allow multiple threads to execute Python code in parallel, but it does not guarantee that every application becomes faster. Synchronization overhead may remain, and C extensions must support the free-threaded runtime. Race conditions, deadlocks, and the need to protect shared mutable state remain. Verify the actual runtime configuration and benchmark the application on it.

### Pharmaviyum application scenario (hypothetical)
A hypothetical Pharmaviyum API endpoint retrieves medicine and customer data from PostgreSQL, calls an external service, and performs CPU-intensive document processing. Explain which parts could use async I/O, which blocking library calls might require a bounded thread pool, and which CPU-intensive tasks should be moved to a process pool or background worker. Include limits, timeouts, cancellation, tenant/patient data isolation, and metrics. This is an interview scenario, not a claim about the current implementation.

### Senior-level evaluation rubric
A strong Senior answer should:
1. Clearly distinguish concurrency from parallelism.
2. Explain the GIL accurately and scope the claim to the relevant CPython build/runtime.
3. Select async I/O, threads, and processes based on workload characteristics.
4. Recognize that the GIL does not eliminate race conditions or protect business invariants.
5. Discuss synchronization, deadlocks, contention, and message-passing alternatives.
6. Account for process startup, memory, serialization, IPC, and worker lifecycle.
7. Understand optional free-threaded builds without assuming universal compatibility or speedup.
8. Define operational limits and validate decisions with representative profiling and load tests.

**Evaluation signals**
- Mid-level: knows the basic differences between threads and processes and the conventional GIL limitation.
- Strong Senior: chooses execution models from workload evidence and designs safe, bounded concurrency.
- Staff-level signal: establishes service-wide concurrency budgets, isolation boundaries, worker topology, and observability standards.

### Common pitfalls
- Claiming that Python threads can never run in parallel under any circumstances.
- Treating the GIL as a language-level guarantee or as a lock protecting application data.
- Assuming the GIL makes compound operations thread-safe.
- Using threads for CPU-bound pure-Python work without benchmarking.
- Moving large objects between processes without considering serialization and IPC cost.
- Creating unbounded threads, tasks, queues, or process pools.
- Calling blocking I/O directly from an async event loop.
- Assuming free-threaded builds are the default or automatically faster.
- Ignoring cancellation, timeouts, graceful shutdown, and backpressure.
- Making architecture decisions without representative load tests.

### References
- Python threading documentation: https://docs.python.org/3/library/threading.html
- Python multiprocessing documentation: https://docs.python.org/3/library/multiprocessing.html
- Python concurrent.futures documentation: https://docs.python.org/3/library/concurrent.futures.html
- Python asyncio documentation: https://docs.python.org/3/library/asyncio.html
- Python FAQ — Global Interpreter Lock: https://docs.python.org/3/faq/library.html#what-kinds-of-global-value-mutation-are-thread-safe
- Python free-threading guide: https://docs.python.org/3/howto/free-threading-python.html
- PEP 703 — Making the Global Interpreter Lock Optional in CPython: https://peps.python.org/pep-0703/


## PY-CORE-018 — Python Attribute Access, Descriptors, Properties and Lookup

### Interview question
**Explain how attribute access works in Python. Discuss the descriptor protocol, data and non-data descriptors, properties, method binding, and the roles of __getattribute__ and __getattr__.**

### Перевод вопроса
Объясните, как в Python работает доступ к атрибутам. Расскажите о протоколе дескрипторов, data и non-data descriptors, свойствах, связывании методов и роли __getattribute__ и __getattr__.

### What the interviewer evaluates
- Understanding Python's attribute lookup model rather than memorized syntax.
- Ability to explain descriptors and precedence in instance/class lookup.
- Correct distinction between data and non-data descriptors.
- Understanding of function descriptors and bound methods.
- Safe use of properties and custom attribute interception.
- Awareness of ORM, validation, and framework abstractions built on descriptors.

### Model answer (RU)
Доступ к атрибуту через выражение obj.name — это не просто чтение словаря экземпляра. Python использует механизм attribute lookup, который учитывает тип объекта, его MRO, instance namespace, class namespace и descriptor protocol. Точная последовательность зависит от того, является ли найденный объект data descriptor, non-data descriptor или обычным атрибутом.

**Descriptor** — объект, определяющий один или несколько методов протокола: __get__, __set__ и/или __delete__. Если атрибут класса является descriptor, Python может делегировать ему чтение, присваивание или удаление атрибута. Descriptor обычно реализуется как атрибут класса, а не экземпляра.

**Data descriptor** определяет __set__ и/или __delete__. При обычном доступе к атрибуту экземпляра data descriptor имеет приоритет над записью в instance.__dict__. **Non-data descriptor** определяет только __get__; значение из instance namespace может перекрыть его. Если descriptor не участвует, поиск учитывает атрибуты экземпляра и класса согласно правилам lookup и MRO. В частности, функции, размещённые в классе, являются non-data descriptors.

Функция, полученная через экземпляр, обычно превращается в **bound method**: механизм функции __get__ связывает функцию с экземпляром, и экземпляр автоматически передаётся как первый аргумент при вызове. При обращении через класс функция обычно остаётся несвязанной. Это объясняет поведение self без необходимости считать его специальным синтаксисом языка.

**property** — встроенный descriptor, предоставляющий управляемый доступ к атрибуту через getter, setter и deleter. Он позволяет сохранить стабильный публичный API, добавив валидацию, вычисление или совместимость с прежним интерфейсом. Property не следует превращать в место для скрытого I/O, дорогих запросов или неожиданного изменения состояния: чтение атрибута должно оставаться предсказуемым.

__getattribute__ вызывается для обычного доступа к атрибутам и может перехватить практически каждое такое чтение. Переопределение требует осторожности: прямое обращение к self.name внутри него может вызвать рекурсию. Для стандартного поведения обычно делегируют в object.__getattribute__(self, name). __getattr__ вызывается как fallback, когда обычный поиск атрибута завершился AttributeError. Он подходит для вычисляемых или динамических fallback-атрибутов, но не заменяет понимание основного lookup.

При проектировании descriptor важно учитывать повторное использование одного descriptor-объекта всеми экземплярами класса, хранение per-instance state, наследование, thread safety и поведение при class access. Состояние конкретного экземпляра обычно хранится в его namespace либо в другом подходящем хранилище, а не в единственном поле descriptor, иначе значения разных экземпляров могут смешиваться.

### Professional answer (EN)
Attribute access through obj.name is not merely a lookup in the instance dictionary. Python's attribute machinery considers the object's type, its method resolution order, instance and class namespaces, and the descriptor protocol. Lookup precedence depends in particular on whether a class attribute is a data descriptor, a non-data descriptor, or an ordinary attribute.

A **descriptor** is an object that defines one or more of __get__, __set__, and __delete__. When a descriptor is placed on a class, Python can delegate attribute reads, assignments, and deletions to it. Descriptors are typically installed as class attributes.

A **data descriptor** defines __set__ and/or __delete__. During ordinary instance attribute lookup, a data descriptor takes precedence over an entry in the instance dictionary. A **non-data descriptor** defines only __get__; an instance attribute can shadow it. If no descriptor takes precedence, lookup proceeds through the instance and class namespaces according to Python's lookup and MRO rules. Functions stored on classes are non-data descriptors.

A function retrieved through an instance is normally transformed into a **bound method**: the function descriptor's __get__ binds the instance, which is then supplied as the first argument when the method is called. Access through the class normally returns the function without an instance bound. This explains self without treating it as special syntax.

property is a built-in descriptor that exposes controlled attribute access through getter, setter, and deleter methods. It can preserve a stable public API while adding validation, computation, or backward compatibility. A property should not hide surprising I/O, expensive database work, or unexpected state changes; attribute reads should remain predictable.

__getattribute__ participates in every ordinary attribute access and can intercept nearly all such reads. Overriding it requires care: accessing self.name inside the override can recurse. Delegate to object.__getattribute__(self, name) for standard lookup behavior. __getattr__ is a fallback invoked when normal lookup raises AttributeError. It can provide computed or dynamic fallback attributes, but it is not a replacement for understanding the primary lookup process.

When designing descriptors, consider that one descriptor object is shared by all instances of its owner class, how per-instance state is stored, inheritance, thread safety, and class-level access. Per-instance values should normally live in the instance namespace or another appropriate store; putting them in a single mutable descriptor field can accidentally mix state between instances.

### Follow-up questions and model answers

**FU-1 — What is the precedence between data descriptors, instance attributes, and non-data descriptors?**  
**Answer (RU):** При стандартном lookup атрибута экземпляра data descriptor, найденный в классе, имеет приоритет над записью в instance dictionary. Затем учитывается instance attribute. Non-data descriptor и обычные атрибуты класса используются позже, если значение экземпляра не перекрывает non-data descriptor. Детали class-level lookup отличаются, поэтому важно уточнять, идёт ли речь об экземпляре или самом классе.  
**Answer (EN):** In standard instance lookup, a class-level data descriptor takes precedence over the instance dictionary. The instance attribute is considered before a non-data descriptor or ordinary class attribute, so it can shadow a non-data descriptor. Class-level lookup has different details, so specify whether the access is through an instance or the class.

**FU-2 — Why can an instance attribute shadow a method defined on its class?**  
**Answer (RU):** Функции в class namespace являются non-data descriptors: они реализуют __get__, но не __set__. Поэтому значение с тем же именем в instance namespace может перекрыть функцию при доступе через экземпляр. Присваивание obj.method = value может затенить метод класса для данного экземпляра.  
**Answer (EN):** Functions in a class namespace are non-data descriptors: they implement __get__ but not __set__. An instance attribute with the same name can therefore shadow the function during instance lookup. Assigning obj.method = value can shadow the class method for that instance.

**FU-3 — What is the difference between __getattribute__ and __getattr__?**  
**Answer (RU):** __getattribute__ участвует в каждом обычном обращении к атрибуту и отвечает за основной механизм доступа. __getattr__ вызывается как fallback, только если обычный lookup завершился AttributeError. Переопределяя __getattribute__, нужно избегать рекурсии и делегировать стандартный поиск через object.__getattribute__.  
**Answer (EN):** __getattribute__ participates in every ordinary attribute access and implements the primary access hook. __getattr__ is a fallback called only when normal lookup raises AttributeError. When overriding __getattribute__, avoid recursion and delegate standard lookup through object.__getattribute__.

**FU-4 — How does Python bind an instance method, and why is self not a keyword?**  
**Answer (RU):** Функция в классе является descriptor. При чтении через экземпляр её __get__ возвращает bound method, связанный с этим экземпляром; при вызове экземпляр автоматически передаётся первым аргументом. Имя self — обычное соглашение об имени параметра, а не ключевое слово.  
**Answer (EN):** A function stored on a class is a descriptor. Access through an instance invokes its __get__ and produces a bound method; calling it supplies that instance as the first argument. self is a conventional parameter name, not a keyword.

**FU-5 — What descriptor design mistakes can cause bugs in an ORM or validation framework?**  
**Answer (RU):** Типичные ошибки — хранить значение экземпляра в общем поле descriptor и смешивать данные разных объектов; не учитывать class access и наследование; некорректно реализовать __set_name__; создавать рекурсивный lookup; не учитывать thread safety и lifecycle объекта. В ORM также важно отличать чтение уже загруженного значения от lazy loading, который может неожиданно выполнять I/O.  
**Answer (EN):** Common mistakes include storing per-instance values in one shared descriptor field, mishandling class access or inheritance, incorrectly implementing __set_name__, causing recursive lookup, and ignoring thread safety or object lifecycle. In an ORM, also distinguish reading an already-loaded value from lazy loading that may unexpectedly perform I/O.

### Pharmaviyum application scenario (hypothetical)
A hypothetical ORM or validation layer for Pharmaviyum exposes typed fields such as medication strength or product status through descriptors. Explain how the descriptor would validate assignment, keep values isolated per model instance, interact with inheritance, and avoid hidden database queries during ordinary attribute access. This is an interview scenario, not a claim about the current implementation.

### Senior-level evaluation rubric
A strong Senior answer should:
1. Explain descriptor protocol methods and class-level placement.
2. Correctly distinguish data and non-data descriptors and their lookup precedence.
3. Explain function binding and why self is conventional.
4. Distinguish __getattribute__ from fallback __getattr__ and avoid recursion.
5. Use properties to preserve encapsulation without hiding surprising side effects.
6. Design per-instance descriptor storage safely across multiple objects and inheritance.
7. Recognize descriptor-based framework behavior, including ORM lazy-loading trade-offs.

**Evaluation signals**
- Mid-level: uses properties and understands basic attribute access.
- Strong Senior: reasons accurately about descriptor precedence, binding, and safe custom attribute behavior.
- Staff-level signal: designs reusable descriptor abstractions with clear lifecycle, isolation, compatibility, and observability contracts.

### Common pitfalls
- Assuming all attributes are read directly from obj.__dict__.
- Confusing data descriptors with non-data descriptors.
- Assuming methods are special syntax rather than functions using the descriptor protocol.
- Treating self as a Python keyword.
- Causing infinite recursion inside __getattribute__.
- Storing per-instance values in shared descriptor state.
- Assuming a property should perform arbitrary I/O or expensive work.
- Ignoring descriptor inheritance and class-level access behavior.

### References
- Python Descriptor HowTo Guide: https://docs.python.org/3/howto/descriptor.html
- Python Data Model — Implementing Descriptors: https://docs.python.org/3/reference/datamodel.html#implementing-descriptors
- Python Data Model — Customizing Attribute Access: https://docs.python.org/3/reference/datamodel.html#customizing-attribute-access
- Python Built-in Functions — property: https://docs.python.org/3/library/functions.html#property
- Python Classes Tutorial: https://docs.python.org/3/tutorial/classes.html

---

## PY-CORE-019 — Python metaclasses and class creation

### Question (EN)
**How does Python create a class, what is a metaclass, and when would you choose a metaclass over a class decorator or __init_subclass__?**

### Перевод (RU)
**Как Python создаёт класс, что такое метакласс и когда следует выбрать метакласс вместо декоратора класса или __init_subclass__?**

### What the interviewer evaluates
- Understanding that classes are objects and ordinary classes are instances of `type`.
- Knowledge of class creation, namespace preparation, and metaclass selection.
- Correct distinction between metaclass `__new__` and `__init__`.
- Understanding of `__prepare__`, `__init_subclass__`, class decorators, and descriptor hooks.
- Ability to reason about multiple inheritance and metaclass conflicts.
- Engineering judgement about complexity, testability, and maintainability.

### Model answer (RU)
В Python **классы сами являются объектами**. Обычный класс, объявленный через `class MyClass:`, обычно является экземпляром метакласса `type`. Метакласс — это класс, экземплярами которого являются другие классы. Обычный класс создаёт экземпляры, а метакласс создаёт объекты-классы.

Упрощённо процесс создания класса выглядит так:

1. Python определяет базовые классы и выбирает метакласс. Если он явно не указан, выбор выводится из метаклассов базовых классов. При множественном наследовании должен существовать совместимый наиболее производный метакласс.
2. Метакласс может предоставить пространство имён через `__prepare__(name, bases, **kwargs)`. Стандартный `type.__prepare__` возвращает подходящий namespace. Пользовательский metaclass может предоставить другой mapping, если требуется контролировать сборку namespace.
3. Python выполняет тело класса в этом namespace. Это реальное выполнение кода: выражения и присваивания на уровне класса могут иметь побочные эффекты.
4. Выбранный метакласс вызывается для создания объекта-класса. Для стандартного `type` создание выполняет `type.__new__`, после чего `type.__init__` выполняет инициализацию.

При наследовании от `type` метакласс обычно переопределяет **свой `__new__`**, чтобы изменить создание объекта-класса: проверить или преобразовать namespace, добавить атрибуты либо метаданные. **`__init__` метакласса** инициализирует уже созданный объект-класс. Это не методы создания обычного экземпляра: в данном случае объектом является сам класс.

Функция `type(name, bases, namespace)` позволяет динамически создать класс. Однако динамическое создание класса само по себе не означает, что обязательно нужен пользовательский метакласс.

Есть более простые механизмы расширения. **`__init_subclass__`** позволяет базовому классу реагировать на создание подклассов, например проверять или регистрировать их. **Декоратор класса** получает уже созданный класс и может изменить его либо вернуть другой объект. Следовательно, декоратор применяется после процесса создания класса. Эти механизмы обычно предпочтительнее, если не требуется управлять самим процессом создания или поведением классов как объектов.

Метакласс оправдан, когда общая политика должна применяться на уровне создания многих классов: например, при построении декларативной модели framework, контроле namespace или согласованной регистрации типов. ORM и validation frameworks могут собирать поля, схемы и метаданные с помощью metaprogramming. Но конкретная библиотека может использовать descriptors, decorators, `__init_subclass__` или комбинацию механизмов — нельзя утверждать, что она использует metaclass, не проверив исходный код.

Важны и соседние hooks. Во время создания класса `type.__new__` обрабатывает descriptors в namespace и вызывает их `__set_name__(owner, name)`. Механизм создания подкласса вызывает `__init_subclass__` базового класса. Эти возможности часто позволяют обойтись без собственного метакласса. Если пользовательский metaclass переопределяет создание класса, он должен корректно делегировать в `super().__new__`, чтобы сохранить стандартное поведение. В сложных сценариях нельзя нарушать обработку специальных элементов namespace, например `__classcell__`.

**Metaclass conflict** возникает, когда метаклассы базовых классов несовместимы: итоговый метакласс должен быть подклассом метаклассов всех базовых классов. Возможные решения — создать совместимый общий метакласс, пересмотреть иерархию наследования или удалить ненужную зависимость от metaclass. Простое указание одного из конфликтующих метаклассов не устраняет причину конфликта.

Мой принцип на уровне Senior: сначала рассмотреть обычные классы, композицию, class decorators и `__init_subclass__`. Метакласс следует выбирать только при доказанной необходимости управлять созданием классов и при наличии тестов на наследование, namespace, descriptors и интеграцию. Это мощный механизм, но он увеличивает когнитивную нагрузку и стоимость сопровождения.

### Model answer (EN)
In Python, **classes are objects**. A class declared with `class MyClass:` is normally an instance of the metaclass `type`. A metaclass is a class whose instances are classes: ordinary classes create instances, while metaclasses create class objects.

At a high level, class creation proceeds as follows:

1. Python determines the base classes and selects a metaclass. If no metaclass is explicitly specified, it is derived from the metaclasses of the bases. With multiple inheritance, a compatible most-derived metaclass must exist.
2. The metaclass may provide a namespace through `__prepare__(name, bases, **kwargs)`. The standard `type.__prepare__` supplies a suitable namespace. A custom metaclass can return another mapping when namespace construction genuinely needs to be controlled.
3. Python executes the class body in that namespace. This is actual code execution: class-level expressions and assignments can have side effects.
4. Python calls the selected metaclass to create the class object. With the standard `type` metaclass, `type.__new__` creates the class and `type.__init__` performs initialization.

When subclassing `type`, a metaclass typically overrides **its `__new__`** to customize class-object creation: it can validate or transform the namespace, add attributes, or attach metadata. **The metaclass's `__init__`** initializes the already-created class object. These are not the methods that create an ordinary instance; the object being created here is the class itself.

`type(name, bases, namespace)` can create a class dynamically. Dynamic class creation, however, does not by itself require a custom metaclass.

Python provides simpler extension points. **`__init_subclass__`** lets a base class react when subclasses are created, for example to validate or register them. A **class decorator** receives a class after it has been created and can modify it or return another object. A decorator therefore runs after class creation. These mechanisms are usually preferable when there is no need to control the class-creation process or the behaviour of classes as objects.

A metaclass is justified when a common policy must operate at class-creation level across many classes—for example, declarative framework model construction, namespace control, or coordinated type registration. ORMs and validation frameworks may collect fields, schemas, and metadata through metaprogramming. A particular library may instead use descriptors, decorators, `__init_subclass__`, or a combination; do not claim it uses a metaclass without inspecting its implementation.

Related hooks matter. During class creation, `type.__new__` processes descriptors in the namespace and calls `__set_name__(owner, name)`. The subclass creation mechanism invokes the base class's `__init_subclass__`. These hooks often eliminate the need for a custom metaclass. A custom metaclass overriding class creation should delegate correctly to `super().__new__` to preserve standard behaviour. Advanced implementations must also preserve special namespace entries such as `__classcell__`.

A **metaclass conflict** occurs when the metaclasses of base classes are incompatible. The resulting metaclass must be a subclass of the metaclasses of all bases. Solutions include defining a compatible combined metaclass, revisiting the inheritance hierarchy, or removing an unnecessary metaclass dependency. Simply choosing one conflicting metaclass does not resolve the underlying incompatibility.

My Senior-level approach is to consider ordinary classes, composition, class decorators, and `__init_subclass__` first. I choose a metaclass only when there is a demonstrated need to control class creation and when inheritance, namespace handling, descriptors, and integration are tested. Metaclasses are powerful, but they increase cognitive load and maintenance cost.

### Follow-up questions and model answers

#### FU-1
**EN:** What is the difference between a class and a metaclass in Python?  
**RU:** В чём разница между классом и метаклассом в Python?

**Answer (RU):** Класс обычно создаёт экземпляры, а метакласс создаёт объекты-классы. Сам класс тоже является объектом. У обычного класса метакласс — `type`, поэтому `type(MyClass)` обычно возвращает `type`. Пользовательский метакласс обычно наследуется от `type`.

**Answer (EN):** A class normally creates instances, while a metaclass creates class objects. A class is itself an object. An ordinary class has `type` as its metaclass, so `type(MyClass)` normally returns `type`. A custom metaclass usually subclasses `type`.

#### FU-2
**EN:** What are `__prepare__`, metaclass `__new__`, and metaclass `__init__` responsible for?  
**RU:** За что отвечают `__prepare__`, `__new__` и `__init__` метакласса?

**Answer (RU):** `__prepare__` предоставляет namespace для выполнения тела класса. Метаклассный `__new__` создаёт объект-класс и может преобразовать namespace или добавить метаданные. Метаклассный `__init__` инициализирует уже созданный объект-класс. Их нельзя путать с методами создания обычных экземпляров.

**Answer (EN):** `__prepare__` supplies the namespace in which the class body executes. Metaclass `__new__` creates the class object and may transform its namespace or attach metadata. Metaclass `__init__` initializes the already-created class object. These must not be confused with the methods that create ordinary instances.

#### FU-3
**EN:** When would you prefer `__init_subclass__` or a class decorator over a metaclass?  
**RU:** Когда вы предпочтёте `__init_subclass__` или декоратор класса метаклассу?

**Answer (RU):** `__init_subclass__` подходит, если базовому классу нужно проверять, настраивать или регистрировать подклассы. Декоратор класса обрабатывает уже созданный класс. Метакласс нужен, когда требуется управлять самим созданием классов или поведением class objects. Следует выбирать наименее сложный механизм, решающий задачу.

**Answer (EN):** Use `__init_subclass__` when a base class needs to validate, configure, or register subclasses. A class decorator processes a class after creation. A metaclass is appropriate when class creation itself or class-object behaviour must be controlled. Choose the least complex mechanism that meets the requirement.

#### FU-4
**EN:** What causes a metaclass conflict with multiple inheritance, and how can it be resolved?  
**RU:** Что вызывает конфликт метаклассов при множественном наследовании и как его устранить?

**Answer (RU):** Конфликт возникает, если Python не может выбрать итоговый метакласс, который является подклассом метаклассов всех базовых классов. Решения: создать совместимый общий метакласс, пересмотреть иерархию или отказаться от ненужной зависимости от metaclass. Необходимо учитывать MRO и совместимость поведения.

**Answer (EN):** A conflict occurs when Python cannot select a resulting metaclass that is a subclass of the metaclasses of all base classes. Solutions include defining a compatible combined metaclass, revisiting the hierarchy, or removing an unnecessary metaclass dependency. MRO and behavioural compatibility must be considered.

#### FU-5
**EN:** How can a metaclass-based model framework collect fields, and what risks should a Senior engineer consider?  
**RU:** Как framework моделей на основе метакласса может собирать поля и какие риски должен учитывать Senior-инженер?

**Answer (RU):** Метакласс может анализировать namespace при создании класса, находить поля и descriptors, объединять унаследованные метаданные и строить схему модели. Риски: сложное наследование, metaclass conflicts, неожиданный порядок выполнения class body, import-time side effects, скрытая логика, проблемы с type checkers и сложная отладка. Сначала нужно оценить descriptors, `__set_name__`, `__init_subclass__` и decorators, затем покрыть выбранное поведение тестами.

**Answer (EN):** A metaclass can inspect the namespace during class creation, identify fields and descriptors, merge inherited metadata, and construct a model schema. Risks include complex inheritance, metaclass conflicts, surprising class-body execution order, import-time side effects, hidden behaviour, typing-tool compatibility, and difficult debugging. First evaluate descriptors, `__set_name__`, `__init_subclass__`, and decorators, then test the chosen design.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** imagine a declarative medication-catalogue model framework that collects field metadata, validation declarations, and index hints from model classes. Explain whether descriptors with `__init_subclass__`, a class decorator, or a metaclass would be the simplest reliable design. Discuss inherited fields, duplicate declarations, import-time work, type-checker support, and tests for the resulting metadata.

Inspect the repository before claiming that Pharmaviyum currently uses a custom metaclass or a particular ORM field-registration mechanism.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Calls a metaclass merely a class factory; cannot describe class creation or confuses metaclass hooks with instance hooks. |
| Competent | Explains `type`, basic metaclass creation, and an alternative such as a class decorator. |
| Strong Senior | Explains namespace preparation, metaclass selection, `__new__` versus `__init__`, alternative hooks, descriptor interaction, and metaclass conflicts; chooses the least complex viable design. |
| Staff-level signal | Defines framework-wide metaprogramming conventions, compatibility constraints, migration strategy, testability, and safeguards for class-creation behaviour. |

### Common pitfalls
- Claiming every class needs a custom metaclass; ordinary classes normally use `type`.
- Describing a metaclass only as a function returning a class.
- Confusing metaclass `__new__` and `__init__` with ordinary instance methods.
- Assuming a class decorator runs during the class body; it receives the created class.
- Using a metaclass when `__init_subclass__`, descriptors, or a decorator would suffice.
- Ignoring metaclass compatibility under multiple inheritance.
- Overriding class creation without delegating to `super().__new__` and preserving standard behaviour.
- Performing expensive or external I/O during import-time class creation.
- Claiming a particular ORM uses a metaclass without verifying its implementation.

### References
- Python Data Model — Customizing class creation: https://docs.python.org/3/reference/datamodel.html#customizing-class-creation
- Python Data Model — Metaclasses: https://docs.python.org/3/reference/datamodel.html#metaclasses
- Python built-in `type`: https://docs.python.org/3/library/functions.html#type
- Python Classes Tutorial: https://docs.python.org/3/tutorial/classes.html
- PEP 3115 — Metaclasses in Python 3000: https://peps.python.org/pep-3115/
- PEP 487 — Simpler customization of class creation: https://peps.python.org/pep-0487/

---

## PY-CORE-020 — Python serialization, pickling, and object state

### Question (EN)
**How does Python object serialization work, what are the capabilities and risks of `pickle`, and how would you design a safe, version-tolerant serialization boundary in a backend system?**

### Перевод (RU)
**Как работает сериализация объектов в Python, каковы возможности и риски `pickle`, и как спроектировать безопасную и устойчивую к версиям границу сериализации в backend-системе?**

### What the interviewer evaluates
- Understanding serialization versus deserialization and representation formats.
- Knowledge of the `pickle` protocol and its Python-specific object reconstruction model.
- Correct understanding of `__getstate__`, `__setstate__`, `__reduce__`, and `__reduce_ex__`.
- Recognition that unpickling untrusted input can execute arbitrary code.
- Ability to distinguish data interchange formats from Python object persistence.
- Design judgement around schema evolution, compatibility, validation, and operational boundaries.

### Model answer (RU)
**Сериализация** преобразует состояние или структуру данных в представление, которое можно сохранить или передать. **Десериализация** восстанавливает данные или объект из этого представления. Формат определяет, что именно сохраняется, насколько результат переносим между языками и версиями, и какие риски возникают при восстановлении.

Модуль Python **`pickle`** предназначен для сериализации и восстановления Python-объектов, включая многие встроенные типы и пользовательские классы. Он сохраняет не просто универсальную структуру данных: pickle-поток содержит инструкции и ссылки, необходимые для реконструкции объектов Python. Поддерживаются разные протоколы; более новые протоколы могут эффективнее представлять некоторые объекты, но их совместимость зависит от версии Python и потребителей. При выборе протокола нужно учитывать минимальную поддерживаемую версию и реальные требования к обмену.

Критическое правило безопасности: **никогда не выполнять `pickle.loads()` или аналогичную десериализацию над недоверенными или подменяемыми данными**. Восстановление pickle может привести к вызову функций и выполнению произвольного кода. Проверка подписи или MAC может помочь установить целостность и подлинность данных, если ключи защищены и проверка выполняется до unpickling, но это не делает безопасным произвольный pickle от недоверенного источника. Не следует считать pickle безопасным только потому, что файл находится в кеше, очереди или внутреннем хранилище: нужно анализировать, кто может записывать или изменять эти данные.

Для управления состоянием пользовательского объекта существуют специальные hooks. **`__getstate__`** определяет состояние, которое нужно сериализовать; **`__setstate__`** восстанавливает это состояние после создания объекта. **`__reduce__`** и **`__reduce_ex__`** задают более низкоуровневый рецепт восстановления: обычно callable, аргументы, а при необходимости состояние и дополнительные элементы восстановления. `__reduce_ex__` получает номер протокола и может учитывать его при выборе формата. Эти hooks полезны для сложных объектов, но увеличивают связанность с механизмом pickle и требуют тестирования совместимости. Их нельзя использовать как способ сериализовать любой runtime resource: открытые sockets, database connections, locks и активные event loops обычно нужно исключать из состояния и восстанавливать через отдельный lifecycle.

**JSON** обычно предпочтительнее на внешних API и межсервисных границах, если достаточно ограниченного набора структур данных. Он широко поддерживается и не восстанавливает произвольные Python-объекты автоматически. Однако JSON не является схемой сам по себе: нужно определить допустимую структуру, типы, обязательные поля, ограничения и правила обработки неизвестных полей. Для строгих контрактов можно применять явную schema validation и версии схем.

Устойчивость к версиям не возникает автоматически ни у pickle, ни у JSON. Для долговременного хранения следует проектировать явную схему: поле версии, стабильные идентификаторы полей, defaults, правила миграции, поведение при неизвестных или удалённых полях и стратегию отката. Нельзя полагаться на то, что импортируемый Python-класс всегда будет иметь прежнее имя или путь модуля. Переименование класса или модуля может сломать восстановление старых pickle. Также следует тестировать fixtures, созданные предыдущими версиями приложения, и определять срок поддержки старых форматов.

В backend-системе я разделяю **внутренний краткоживущий кеш** и **долговременный или внешний контракт**. Для внутреннего кеша допустимы ограниченные Python-specific решения, если writer и reader контролируются, версия окружения совместима, данные имеют ограниченный TTL и предусмотрен безопасный cache miss. Для API, очередей между независимыми сервисами, файлового обмена и долговременных данных я предпочитаю JSON или schema-based формат с явной валидацией и правилами эволюции. Конкретный выбор зависит от требований к типам, размеру, производительности и interoperability.

Для проверки сериализации нужны round-trip tests, тесты совместимости со старыми fixtures, проверки неизвестных/отсутствующих полей, лимиты размера и глубины входных данных, а также негативные тесты. Round-trip тест сам по себе не доказывает безопасность или совместимость. Секреты, персональные и чувствительные данные нельзя включать в сериализуемое состояние без явной необходимости, минимизации и защиты.

### Model answer (EN)
**Serialization** transforms data or object state into a representation that can be stored or transmitted. **Deserialization** reconstructs data or an object from that representation. The chosen format determines what is preserved, how portable the representation is across languages and versions, and what risks arise during reconstruction.

Python's **`pickle`** module serializes and reconstructs Python objects, including many built-in types and user-defined classes. It is not merely a generic data structure format: a pickle stream contains instructions and references used to reconstruct Python objects. Pickle supports multiple protocols. Newer protocols may represent some objects more efficiently, but compatibility depends on the Python versions and consumers involved. Select a protocol based on the minimum supported runtime and actual interoperability requirements.

The critical security rule is: **never call `pickle.loads()` or equivalent deserialization on untrusted or tamperable data**. Unpickling can invoke callables and execute arbitrary code. A signature or MAC can help establish data authenticity and integrity when keys are protected and verification occurs before unpickling, but it does not make arbitrary untrusted pickle safe. Do not assume a pickle is safe merely because it comes from a cache, queue, or internal store; identify every principal that can write or modify it.

Python provides hooks for controlling object state. **`__getstate__`** defines the state to serialize; **`__setstate__`** restores that state after object creation. **`__reduce__`** and **`__reduce_ex__`** provide a lower-level reconstruction recipe, typically involving a callable and arguments, with optional state and additional reconstruction elements. `__reduce_ex__` receives the protocol number and can adapt its result accordingly. These hooks are useful for complex objects, but they couple the class to pickle's reconstruction mechanism and require compatibility tests. They are not a general solution for serializing runtime resources: open sockets, database connections, locks, and active event loops should normally be excluded and re-established through a separate lifecycle.

**JSON** is generally a better choice for external APIs and service boundaries when a constrained data model is sufficient. It is widely supported and does not automatically reconstruct arbitrary Python objects. However, JSON is not a schema by itself: define the permitted structure, types, required fields, constraints, and handling of unknown fields. Explicit schema validation and schema versions can provide stronger contracts.

Version tolerance is not automatic with either pickle or JSON. For durable storage, design an explicit schema: include a version, use stable field identifiers, define defaults and migrations, specify how unknown or removed fields are handled, and plan rollback behaviour. Do not assume an importable Python class will always retain the same name or module path. Renaming a class or module can break old pickle payloads. Test fixtures produced by previous application versions and define how long old formats remain supported.

In a backend system, I distinguish a **short-lived internal cache** from a **durable or externally consumed contract**. A constrained Python-specific format may be acceptable for an internal cache when writers and readers are controlled, runtime compatibility is known, entries have a bounded TTL, and cache misses are safe. For APIs, queues between independently deployed services, file exchange, and durable data, I prefer JSON or a schema-based format with explicit validation and evolution rules. The choice depends on type requirements, payload size, performance, and interoperability.

Serialization testing should include round-trip tests, compatibility tests using old fixtures, missing/unknown-field cases, input size and depth limits, and negative tests. A round-trip test alone does not prove safety or backward compatibility. Secrets, personal data, and other sensitive information should not be included in serialized state without a clear need, minimization, and appropriate protection.

### Follow-up questions and model answers

#### FU-1
**EN:** Why is unpickling untrusted data dangerous, and what does signing a pickle actually protect?  
**RU:** Почему десериализация недоверенного pickle опасна и от чего фактически защищает подпись pickle?

**Answer (RU):** Unpickling может вызывать функции, указанные в pickle-потоке, и тем самым выполнять произвольный код. Поэтому нельзя загружать pickle от недоверенного источника. Подпись или MAC могут подтвердить целостность и подлинность данных, если ключ защищён, а проверка выполняется до unpickling. Это не защищает от вредоносного содержимого, созданного доверенным, но скомпрометированным источником, и не заменяет контроль доступа и управление ключами.

**Answer (EN):** Unpickling can invoke callables encoded in the pickle stream and therefore execute arbitrary code. Never load pickle from an untrusted source. A signature or MAC can establish integrity and authenticity when the key is protected and verification happens before unpickling. It does not protect against malicious content produced by a trusted but compromised source, and it does not replace access control or key management.

#### FU-2
**EN:** What is the difference between `__getstate__`, `__setstate__`, `__reduce__`, and `__reduce_ex__`?  
**RU:** В чём разница между `__getstate__`, `__setstate__`, `__reduce__` и `__reduce_ex__`?

**Answer (RU):** `__getstate__` определяет сериализуемое состояние объекта, а `__setstate__` применяет сохранённое состояние при восстановлении. `__reduce__` задаёт рецепт реконструкции объекта на более низком уровне. `__reduce_ex__` получает версию pickle protocol и может возвращать рецепт с учётом выбранного протокола. Это hooks для pickle, а не универсальный механизм persistence для ресурсов операционной системы.

**Answer (EN):** `__getstate__` defines the object's serialized state, while `__setstate__` applies saved state during reconstruction. `__reduce__` defines a lower-level reconstruction recipe. `__reduce_ex__` receives the pickle protocol version and can return a protocol-aware recipe. These are pickle hooks, not a general persistence mechanism for operating-system resources.

#### FU-3
**EN:** Why might a pickle created by an older application version fail to load after a refactor?  
**RU:** Почему pickle, созданный старой версией приложения, может перестать загружаться после рефакторинга?

**Answer (RU):** Pickle может ссылаться на класс или функцию через модуль и имя. Переименование, перенос или удаление символа меняет путь импорта, необходимый для восстановления. Может измениться и формат состояния класса. Поэтому для долговременной совместимости нужны migration strategy, versioned schemas, сохранённые fixtures и тесты восстановления после обновления. Не следует считать pickle стабильным независимым форматом хранения.

**Answer (EN):** Pickle may refer to a class or function by its module and name. Renaming, moving, or removing that symbol changes the import path needed for reconstruction. The class state format may also change. Durable compatibility therefore requires a migration strategy, versioned schemas, retained fixtures, and tests across upgrades. Pickle should not be assumed to be a stable, implementation-independent storage format.

#### FU-4
**EN:** When would you choose JSON over pickle for a backend service boundary?  
**RU:** Когда для границы backend-сервиса вы выберете JSON вместо pickle?

**Answer (RU):** JSON предпочтительнее, когда важны interoperability, прозрачность данных, поддержка разных языков и отсутствие автоматического восстановления произвольных Python-объектов. Но нужно отдельно валидировать схему и контролировать размер, типы и неизвестные поля. Pickle может быть приемлем для строго контролируемого внутреннего сценария, но не для недоверенных API payloads или независимых межсервисных контрактов.

**Answer (EN):** JSON is preferable when interoperability, inspectable data, multi-language support, and avoiding automatic reconstruction of arbitrary Python objects matter. The schema, payload size, types, and unknown fields still need explicit validation. Pickle may be acceptable in a tightly controlled internal use case, but not for untrusted API payloads or independent service contracts.

#### FU-5
**EN:** How would you evolve a serialized payload without breaking existing consumers?  
**RU:** Как развивать сериализуемый payload, не ломая существующих потребителей?

**Answer (RU):** Я бы ввёл явную версию схемы и правила совместимости: добавление optional fields с безопасными defaults, сохранение семантики существующих полей, контролируемое удаление через deprecation period, миграцию старых payloads и обработку неизвестных полей. Развёртывание должно учитывать порядок обновления producers и consumers. Проверки должны включать fixtures предыдущих версий и сценарии mixed-version deployment. При несовместимых изменениях лучше создать новую версию контракта, а не пытаться скрыть breaking change.

**Answer (EN):** I would introduce an explicit schema version and compatibility rules: add optional fields with safe defaults, preserve existing field semantics, remove fields only through a deprecation period, migrate old payloads, and define unknown-field handling. Deployment must account for producer and consumer upgrade order. Tests should include previous-version fixtures and mixed-version deployment scenarios. For incompatible changes, introduce a new contract version rather than hiding a breaking change.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** imagine a background job that stores a serialized task payload containing a medication-catalogue import identifier, processing options, and schema version. Explain why the payload should contain stable identifiers and validated data rather than live ORM objects, database sessions, or credentials. Compare JSON with pickle, describe how a worker running a newer release handles older queued messages, and specify how you would test compatibility and reject malformed payloads.

Do not claim that Pharmaviyum currently uses pickle, JSON task payloads, or a particular queue serialization format without inspecting the implementation.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Treats serialization as a safe byte conversion; recommends unpickling arbitrary data or assumes pickle is portable. |
| Competent | Explains pickle versus JSON and identifies the untrusted-input risk. |
| Strong Senior | Explains reconstruction hooks, import-path coupling, schema evolution, trust boundaries, validation, and compatibility testing; chooses formats according to the boundary. |
| Staff-level signal | Defines versioning and migration policy across independently deployed producers and consumers, threat model, rollout/rollback strategy, and operational controls for payload size, retention, and sensitive data. |

### Common pitfalls
- Unpickling untrusted or user-controlled data.
- Treating a signed pickle as inherently safe without verifying authenticity before unpickling and protecting signing keys.
- Assuming pickle is a language-neutral or long-term stable interchange format.
- Serializing live connections, locks, sessions, event loops, or other runtime resources.
- Assuming `__getstate__` and `__setstate__` alone guarantee compatibility across code changes.
- Ignoring module and class import paths referenced during reconstruction.
- Assuming JSON automatically validates data or provides schema evolution.
- Testing only round trips using the same code version.
- Including secrets or unnecessary personal data in serialized payloads.
- Failing to bound payload size, nesting depth, or deserialization work.

### References
- Python `pickle` documentation — security warning and protocols: https://docs.python.org/3/library/pickle.html
- Python `pickle` — object state and customization: https://docs.python.org/3/library/pickle.html#pickling-class-instances
- Python `pickle` — what can be pickled and unpickled: https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled
- Python `json` documentation: https://docs.python.org/3/library/json.html
- Python Security Considerations: https://docs.python.org/3/library/security_warnings.html


## PY-CORE-021 — Python Typing, Generics and Advanced Type Annotations

### Interview question
How does Python's static typing system support generic APIs, and how would you design precise, reusable type contracts for a production backend? Explain TypeVar, Generic, ParamSpec, TypeVarTuple, variance, TypedDict, Literal, Annotated, Any, object, Never, and NoReturn. Distinguish static analysis from runtime validation.

### Что проверяет интервьюер
- Понимание того, что annotations не превращают Python в runtime-enforced статически типизированный язык.
- Способность проектировать reusable generic functions and classes without erasing useful type information.
- Понимание variance and substitutability across generic types.
- Умение выбирать между Any, object, Protocol, TypedDict, Literal and Annotated.
- Понимание границы между static type checking and runtime validation.
- Способность применять typing как архитектурный контракт, а не как декоративные комментарии.

### Эталонный ответ (RU)
Python использует динамическую модель выполнения, а type annotations в основном предоставляют метаданные для статических анализаторов, IDE и инструментов. Сам интерпретатор обычно не проверяет соответствие аргументов и возвращаемых значений аннотациям. Runtime validation должна выполняться отдельным механизмом, например Pydantic, явными проверками или валидатором на границе системы.

Generics позволяют описывать алгоритм или контейнер, который работает с разными типами, сохраняя связь между входом и выходом. TypeVar обозначает параметр типа. Например, generic-функция identity может принимать значение типа T и возвращать T: анализатор сохраняет конкретный тип вызова. Generic-класс параметризуется аналогично, чтобы его методы могли выражать отношения между типами. Современный синтаксис параметров типов зависит от версии Python; в проектах с поддержкой нескольких версий следует выбирать совместимый стиль и явно задавать минимальную версию.

TypeVar может иметь bound или constraints. Bound задаёт верхнюю границу, которой должен соответствовать тип; constraints перечисляют допустимые варианты и обычно приводят к одному из этих вариантов, а не к произвольному подтипу. Это разные модели и их нельзя использовать взаимозаменяемо. ParamSpec сохраняет сигнатуру параметров callable, что особенно важно для decorators и higher-order functions: декоратор может принимать функцию с параметрами P и возвращать callable с теми же параметрами. TypeVarTuple представляет вариативную последовательность параметров типов и полезен для API, где типовая форма зависит от переменного количества типов, например для типизированных tuple или библиотек массивов.

Variance описывает допустимое отношение подтипов между параметризованными типами. Invariant означает отсутствие автоматической подстановки между Generic[Derived] и Generic[Base]. Covariant параметр допускает направление от более конкретного типа к более общему; это безопасно для read-only producer-подобных интерфейсов. Contravariant допускает обратное направление и уместен для consumer-подобных интерфейсов, которые принимают значения. Mutable containers обычно invariant: если бы список Dog можно было считать списком Animal, в него можно было бы добавить Cat и нарушить гарантию списка Dog. Variance следует выбирать исходя из того, как параметр типа используется, а не ради удобства аннотации.

Any отключает значительную часть статической проверки для соответствующего значения и распространяет динамическую неопределённость. object, напротив, означает любой объект, но разрешает только операции, безопасные для всех объектов, пока тип не будет уточнён. Поэтому object часто предпочтительнее Any на границах, где неизвестное значение должно быть проверено или сужено. Never обозначает тип, у которого нет возможных значений, и полезен для недостижимых ветвей и исчерпывающих проверок. NoReturn традиционно описывает функцию, которая не возвращает управление обычным образом, например всегда выбрасывает исключение; в современных аннотациях Never также используется для такого смысла. Нужно учитывать версию и договорённости выбранного type checker.

TypedDict описывает структуру словаря с известными ключами и типами значений. Это статический контракт формы mapping, а не runtime validator. Required/NotRequired позволяют выражать обязательные и необязательные ключи; total=False меняет обязательность по умолчанию. Literal ограничивает значение конкретным набором литералов и помогает моделировать discriminators и конечные варианты. Annotated добавляет метаданные к базовому типу. Сам по себе Python не придаёт этим метаданным универсальную runtime-семантику; библиотеки и фреймворки могут интерпретировать их по своим правилам. FastAPI и Pydantic используют аннотации для построения схем и обработки данных, но точное поведение зависит от версии и конфигурации.

В production backend я разделяю три уровня: статические контракты между компонентами, runtime validation недоверенных данных и бизнес-инварианты. Type checker проверяет согласованность кода до выполнения; Pydantic или другой валидатор проверяет входящие данные во время выполнения; доменный слой проверяет правила, которые нельзя выразить одной структурой данных. Для внешнего JSON API TypedDict может быть удобен как статическое описание уже проверенной структуры, но не заменяет parsing и validation. Для расширяемых интерфейсов часто лучше Protocol, чем жёсткая зависимость от конкретного класса.

При проектировании generic API я избегаю чрезмерного усложнения типов. Типовая система должна делать некорректные состояния труднее выразимыми, сохранять полезную информацию и оставаться читаемой. Сложные overloads, cast или Any должны иметь обоснование и узкую область применения. Я запускаю выбранный checker в CI, фиксирую его конфигурацию, проверяю типы публичных интерфейсов и добавляю runtime tests для входов, которые могут быть некорректными независимо от статической проверки.

### Professional answer (EN)
Python remains dynamically executed. Type annotations primarily provide metadata for static analyzers, IDEs, and tooling; the interpreter does not generally enforce argument or return annotations. Runtime validation must be implemented separately, for example with Pydantic, explicit checks, or a validation layer at a system boundary.

Generics let an API operate over multiple types while preserving relationships between inputs and outputs. A TypeVar represents a type parameter. A generic identity function can accept a value of T and return T, allowing a checker to retain the concrete type at each call site. Generic classes use the same principle to express relationships across attributes and methods. The newer type-parameter syntax is version-dependent, so a library supporting multiple Python versions must select syntax compatible with its declared minimum version.

A TypeVar can have a bound or constraints. A bound specifies an upper bound that a type argument must satisfy; constraints enumerate permitted alternatives and generally resolve to one of those alternatives rather than an arbitrary subtype. They model different requirements. ParamSpec captures a callable's parameter specification and is particularly useful for decorators and higher-order functions that must preserve the wrapped callable's signature. TypeVarTuple represents a variadic sequence of type parameters, useful when an API's type shape depends on a variable number of types, such as typed tuples or array-like abstractions.

Variance defines how subtyping relationships apply to parameterized types. Invariant parameters do not allow automatic substitution between Generic[Derived] and Generic[Base]. Covariance permits substitution from a more specific type to a more general one and is appropriate for read-only producer interfaces. Contravariance permits the reverse direction and is appropriate for consumer interfaces. Mutable containers are commonly invariant: treating a list of Dog as a list of Animal would allow a Cat to be inserted, violating the original list's guarantee. Variance should follow the parameter's usage, not annotation convenience.

Any opts out of substantial static checking and can spread uncertainty through an expression. object accepts any Python object but permits only operations valid for all objects until the value is narrowed. Therefore object is often safer than Any when an unknown value must be validated or narrowed. Never represents an uninhabited type and supports unreachable branches and exhaustiveness checks. NoReturn traditionally describes a function that does not return normally, such as one that always raises; Never is also used for this meaning in modern typing. Check the supported Python version and type-checker conventions.

TypedDict describes a dictionary shape with known keys and value types. It is a static structural contract, not a runtime validator. Required and NotRequired express key presence, while total=False changes the default requiredness. Literal restricts a value to a finite set of literal values and is useful for discriminators and finite modes. Annotated attaches metadata to an underlying type. Python itself does not assign universal runtime behavior to that metadata; frameworks may interpret it according to their own rules. FastAPI and Pydantic use annotations for schema generation and data processing, but exact behavior depends on their versions and configuration.

For a production backend, I separate static contracts between components, runtime validation of untrusted input, and domain invariants. A type checker verifies code consistency before execution. Pydantic or another validator checks incoming data at runtime. The domain layer enforces business rules that cannot be represented by a data shape alone. TypedDict can describe a validated mapping for static analysis, but it does not replace parsing or validation of external JSON. Protocol is often preferable to coupling an abstraction to a concrete class.

I avoid making generic APIs unnecessarily complex. The type system should make invalid states harder to express, preserve useful information, and remain understandable. Complex overloads, casts, and Any should have a clear justification and narrow scope. I run the selected checker in CI, pin its configuration, check public interfaces, and add runtime tests for malformed inputs that static analysis cannot prevent.

### Deferred annotation evaluation and introspection (Python 3.14+)

**RU:** В Python 3.14 стандартное поведение для аннотаций функций, классов и модулей стало deferred: они вычисляются по запросу, а не обязательно в момент определения. `annotationlib` предоставляет `get_annotations()` и форматы `VALUE`, `FORWARDREF` и `STRING` для разных сценариев интроспекции. `VALUE` пытается получить реальные значения и может завершиться ошибкой, если имя не разрешается; `FORWARDREF` позволяет представить неразрешённые ссылки; `STRING` возвращает строковое представление. Если библиотека читает `__annotations__` напрямую или зависит от прежнего момента вычисления, её поведение следует проверить на поддерживаемых версиях Python. При наличии `from __future__ import annotations` в Python 3.14 сохраняется строковый режим. Отложенное вычисление не превращает аннотации в runtime type enforcement. При этом интроспекция аннотаций не всегда является пассивным чтением метаданных: `annotationlib` может вызвать код вычисления аннотаций, а `ForwardRef` может использовать `eval()`. Не следует передавать API интроспекции аннотаций данные или объекты из недоверенного источника; учитывайте возможное выполнение произвольного кода и стоимость вычисления.

**EN:** In Python 3.14, annotations on functions, classes, and modules are deferred by default: they are evaluated on demand rather than necessarily when the object is defined. `annotationlib` provides `get_annotations()` and the `VALUE`, `FORWARDREF`, and `STRING` formats for different introspection needs. `VALUE` attempts to produce runtime values and may fail when a name cannot be resolved; `FORWARDREF` represents unresolved references; `STRING` returns string representations. Libraries that read `__annotations__` directly or depend on the former evaluation timing should be tested across supported Python versions. In Python 3.14, `from __future__ import annotations` retains stringified behavior. Deferred evaluation does not turn annotations into runtime type enforcement. Annotation introspection is not always passive metadata access: `annotationlib` may invoke annotation evaluation code, and `ForwardRef` evaluation may use `eval()`. Do not pass untrusted data or objects into annotation-introspection APIs; account for possible arbitrary code execution and evaluation cost.

**References:** annotationlib — https://docs.python.org/3.14/library/annotationlib.html ; What's New in Python 3.14 — https://docs.python.org/3.14/whatsnew/3.14.html

### Follow-up questions and model answers

#### FU-1. What is the difference between TypeVar bounds and constraints?
**Answer (RU):** Bound требует, чтобы аргумент типа был подтипом указанного верхнего типа или соответствовал ему по правилам checker. Constraints задают конечный набор допустимых типов. Bound сохраняет возможность использовать подходящий подтип; constraints ограничивают выбор перечисленными альтернативами. Выбор зависит от того, нужен ли открытый контракт подтипов или закрытый набор типов.

**Answer (EN):** A bound requires a type argument to satisfy an upper-bound type. Constraints define a finite set of permitted alternatives. A bound allows suitable subtypes, whereas constraints restrict the choice to the declared alternatives. Choose based on whether the API needs an open subtype contract or a closed set of types.

#### FU-2. Why is a mutable generic container usually invariant?
**Answer (RU):** Потому что контейнер одновременно читает и записывает значения. Если MutableBox[Dog] считать MutableBox[Animal], вызывающий код сможет записать Cat, после чего потребитель, ожидающий Dog, получит значение другого типа. Covariance обычно подходит read-only producer, contravariance — consumer, а mutable producer/consumer требует invariance.

**Answer (EN):** A mutable container both produces and consumes values. If MutableBox[Dog] were accepted as MutableBox[Animal], a caller could insert a Cat and violate the original Dog guarantee. Covariance generally fits read-only producers, contravariance fits consumers, and a mutable producer/consumer is typically invariant.

#### FU-3. When should a decorator use ParamSpec instead of Callable[..., Any]?
**Answer (RU):** Когда декоратор должен сохранить сигнатуру исходной функции: типы параметров, их структуру и возможность корректно проверить вызовы. Callable[..., Any] стирает информацию о параметрах и ослабляет проверку. ParamSpec позволяет связать параметры входной функции с параметрами возвращаемого callable; отдельно нужно корректно выразить тип результата, например через TypeVar.

**Answer (EN):** Use ParamSpec when a decorator must preserve the wrapped callable's parameter specification so callers retain useful checking of arguments. Callable[..., Any] erases parameter information and weakens checking. ParamSpec connects the input callable's parameters to the returned callable; a separate TypeVar can represent the return value.

#### FU-4. How do Any and object differ at an untrusted data boundary?
**Answer (RU):** Any фактически отключает проверки для операций над значением и может распространить небезопасную неопределённость дальше по коду. object требует сначала сузить тип или проверить значение, прежде чем выполнять специфичные операции. Но ни Any, ни object не валидируют входные данные во время выполнения: для этого нужны parsing и runtime validation.

**Answer (EN):** Any effectively disables checking for operations on the value and can propagate unchecked uncertainty. object requires narrowing or validation before type-specific operations are used. Neither Any nor object performs runtime validation; parsing and an explicit validation layer are still required.

#### FU-5. Does Annotated or TypedDict validate data at runtime?
**Answer (RU):** Нет, сами по себе — нет. TypedDict предназначен прежде всего для статического описания ключей и значений словаря. Annotated прикрепляет метаданные, которые могут интерпретировать сторонние инструменты. Runtime-поведение появляется только если конкретная библиотека явно реализует его, например валидатор, использующий эти метаданные. Нужно тестировать фактическую конфигурацию и версию библиотеки.

**Answer (EN):** No, not by themselves. TypedDict primarily describes dictionary keys and value types for static analysis. Annotated attaches metadata that external tools may interpret. Runtime behavior exists only when a specific library implements it, such as a validator consuming that metadata. Test the actual library version and configuration.

### Pharmaviyum connection — hypothetical interview scenario
Suppose a backend module exposes a generic repository or service interface and receives medication-catalog payloads from an external source. Generics could preserve the relationship between a repository's entity type and its returned values. TypedDict could describe a normalized mapping after parsing, Literal could represent a finite processing state, and Annotated could carry framework-specific metadata. Pydantic or an equivalent runtime validator would still need to validate untrusted payloads, while domain rules would separately verify medication-specific invariants. This is a hypothetical design exercise, not a claim that these exact abstractions are implemented in Pharmaviyum.

### Senior-level evaluation rubric
| Level | Expected evidence |
|---|---|
| Mid-level | Explains annotations, TypeVar, Generic, TypedDict, and the difference between static checking and runtime validation. |
| Senior | Correctly explains bounds versus constraints, ParamSpec, variance, Any versus object, and chooses abstractions based on API behavior. |
| Staff-level signal | Defines a repository-wide typing policy, checker/version compatibility, gradual-typing boundaries, migration strategy, and CI enforcement while balancing precision, maintainability, and runtime safety. |

### Common pitfalls
- Claiming that Python enforces annotations automatically at runtime.
- Treating TypeVar bounds and constraints as equivalent.
- Using Any where object plus narrowing would preserve safety.
- Assuming generic mutable containers are safely covariant.
- Using Callable[..., Any] in decorators when preserving the callable signature matters.
- Treating TypedDict as input validation.
- Assuming Annotated metadata has universal interpreter behavior.
- Confusing Never with a value that can actually be instantiated.
- Adding complex types that obscure rather than clarify the public API.
- Relying on static typing to validate untrusted external payloads.

### References
- Python typing documentation: https://docs.python.org/3/library/typing.html
- Python typing — generics: https://docs.python.org/3/library/typing.html#generics
- Python typing — ParamSpec: https://docs.python.org/3/library/typing.html#typing.ParamSpec
- Python typing — TypeVarTuple: https://docs.python.org/3/library/typing.html#typing.TypeVarTuple
- Python typing — TypedDict: https://docs.python.org/3/library/typing.html#typing.TypedDict
- Python typing — Annotated: https://docs.python.org/3/library/typing.html#typing.Annotated
- Python typing specification: https://typing.readthedocs.io/en/latest/spec/index.html
- Mypy documentation: https://mypy.readthedocs.io/
- Pyright documentation: https://microsoft.github.io/pyright/


## PY-CORE-022 — Python Standard Library and Essential Built-in Modules

### Interview question
Which parts of Python's standard library do you consider essential for production backend engineering? Explain when you would use collections, itertools, functools, contextlib, dataclasses, enum, datetime/zoneinfo, pathlib, logging, and subprocess. Discuss correctness, resource management, portability, and operational risks.

### Что проверяет интервьюер
- Умение выбирать стандартные abstractions вместо самописных решений.
- Понимание семантики и trade-offs ключевых модулей стандартной библиотеки.
- Способность писать предсказуемый, переносимый и тестируемый backend-код.
- Понимание временных зон, локального времени и UTC.
- Безопасную работу с файловой системой, логированием и subprocess.
- Умение контролировать ресурсы, ошибки, memory usage и operational behavior.

### Эталонный ответ (RU)
Стандартная библиотека Python предоставляет зрелые примитивы для типичных задач backend-разработки. Senior-инженер должен знать не только API модулей, но и их семантику, ограничения и последствия для безопасности и эксплуатации. Я предпочитаю стандартную библиотеку, когда она решает задачу ясно и надёжно, но не предполагаю, что любой её модуль автоматически безопасен для любого входа или production-нагрузки.

**collections.** Counter подходит для подсчёта элементов; defaultdict — для группировки и накопления по ключу; deque — для эффективных операций с обоих концов очереди; ChainMap — для объединения нескольких mapping с приоритетом первого. Важно помнить, что deque не является полноценной thread-safe очередью для сложного producer/consumer протокола; для синхронизации потоков есть queue.Queue, а для asyncio — asyncio.Queue. defaultdict может неожиданно создавать значение при обращении через отсутствующий ключ, поэтому его поведение нужно учитывать в коде и тестах.

**itertools.** Модуль предоставляет ленивые итераторные building blocks: chain, islice, pairwise, groupby, product, combinations и другие. Они позволяют избежать промежуточных коллекций и выражать потоковую обработку. Однако lazy iterator может быть одноразовым, может удерживать исходные объекты и не гарантирует bounded memory во всей цепочке. itertools.groupby группирует последовательные соседние элементы с одинаковым ключом; он не выполняет глобальную группировку. Обычно вход предварительно сортируют по тому же ключу, если нужна группировка всех одинаковых значений.

**functools.** partial фиксирует часть аргументов callable; wraps сохраняет метаданные декорируемой функции; reduce сворачивает последовательность, хотя для простых операций часто яснее обычный цикл или специализированная функция; lru_cache кеширует результаты вызовов по аргументам. Кеширование требует hashable arguments и корректной модели invalidation. Кеш не должен случайно смешивать данные разных пользователей или tenants. lru_cache не является универсальным distributed cache, не предоставляет бизнес-ориентированную invalidation и не превращает async-функцию в корректно кешируемый результат автоматически. Для coroutine functions обычный lru_cache может кешировать coroutine object, а не ожидаемый результат, поэтому нужен специализированный async-aware подход с чёткими правилами concurrency и lifecycle.

**contextlib.** contextmanager и asynccontextmanager позволяют выразить setup/cleanup через генератор, а ExitStack и AsyncExitStack управляют динамическим набором ресурсов. suppress подавляет только явно указанные исключения и должен использоваться узко. closing и aclosing помогают закрывать объекты с соответствующим методом. Контекстный менеджер задаёт границу владения ресурсом: acquire, use, release. Важно не скрывать ошибки cleanup и не подавлять исключения без ясного контракта.

**dataclasses.** Декоратор dataclass генерирует стандартные методы для классов данных: например __init__, __repr__ и __eq__ в зависимости от параметров. field(default_factory=...) нужен для per-instance mutable defaults; прямой изменяемый default нельзя разделять между экземплярами. frozen=True запрещает обычное переназначение полей, но не делает вложенные mutable objects глубоко immutable. slots=True может уменьшить overhead экземпляров и запретить произвольные атрибуты, но имеет последствия для наследования, weak references и совместимости. Dataclass не является автоматически валидатором входных данных и не заменяет Pydantic там, где нужна parsing/validation.

**enum.** Enum задаёт конечный набор символических значений, улучшая читаемость и контроль состояний. StrEnum доступен начиная с Python 3.11. auto() генерирует значения по правилам конкретного enum. Для внешнего API или сохранённых данных значения enum становятся частью контракта: их изменение требует совместимого versioning/migration. Не следует полагаться на случайные числовые значения auto() как на долговечный внешний идентификатор.

**datetime и zoneinfo.** Для абсолютных моментов времени обычно используют timezone-aware datetime в UTC. Naive datetime не содержит достаточной информации, чтобы однозначно определить момент времени. zoneinfo.ZoneInfo использует IANA time zone database и позволяет корректно работать с региональными правилами. Локальное гражданское время может быть неоднозначным при переходе на зимнее время или несуществующим при переходе на летнее время. Нельзя считать, что прибавление календарного дня всегда эквивалентно прибавлению 24 часов в UTC. Для бизнес-правил нужно различать instant, local date/time, timezone и календарную дату. В API следует явно определять формат, timezone policy и поведение для ambiguous/nonexistent local times.

**pathlib и файловая система.** pathlib предоставляет объектную модель путей и обычно предпочтительнее ручной конкатенации строк. Но нормализация пути не является защитой от path traversal сама по себе. При работе с пользовательским именем файла нужно ограничивать допустимые каталоги, проверять разрешённый путь после разрешения ссылок и учитывать symlink/race conditions. Проверка resolve() и последующее открытие могут быть уязвимы к TOCTOU, если атакующий способен менять файловую систему между операциями. Для чувствительных операций нужны подходящие OS-level механизмы, права доступа и безопасное открытие относительно доверенного directory descriptor там, где это поддерживается.

**logging.** Модуль logging предоставляет уровни, handlers, formatters, filters и logger hierarchy. В приложении обычно настраивают logging централизованно на entrypoint, а модули получают logger через getLogger(__name__). Библиотечные модули не должны бесконтрольно конфигурировать root logger. В production полезны структурированные поля, correlation/request IDs и согласованный формат логов. Нельзя записывать пароли, токены, секреты, полные платёжные или медицинские данные. Нужно учитывать log injection, redaction, retention, access control и объём логов. Исключения следует логировать на подходящей границе, избегая повторного логирования одного события на каждом уровне.

**subprocess.** subprocess позволяет запускать внешние процессы и контролировать stdin/stdout/stderr, return code, timeout и environment. Для простого вызова предпочтителен subprocess.run с явным timeout и проверкой результата, например check=True, если ненулевой exit code должен быть ошибкой. Не следует использовать shell=True с данными, контролируемыми пользователем: это создаёт риск command injection. Передача аргументов списком снижает риск shell injection, но всё равно требует проверки допустимых команд и аргументов. Нужно ограничивать время выполнения, объём вывода, права процесса и переменные окружения. Для долгоживущих или большого числа процессов необходима явная модель управления lifecycle и concurrency.

В production я выбираю модуль по контракту задачи, а не по краткости кода. Я проверяю поддерживаемую версию Python, поведение на граничных случаях, обработку ошибок, потокобезопасность и ресурсные ограничения. Для внешних данных стандартная библиотека часто предоставляет инструменты обработки, но validation, authorization и domain invariants остаются отдельными обязанностями. Ключевые решения закрепляются тестами, документацией и наблюдаемостью.

### Professional answer (EN)
Python's standard library provides mature building blocks for common backend tasks. A senior engineer should understand not only the APIs but also their semantics, limitations, and security and operational consequences. I prefer standard-library solutions when they solve the problem clearly and reliably, but I do not assume that every module is automatically safe for every input or production workload.

**collections.** Counter is useful for counting; defaultdict for grouping and accumulation; deque for efficient operations at both ends; ChainMap for layered mappings where the first mapping has precedence. A deque is not a full thread-safe producer/consumer protocol. Use queue.Queue for synchronized threaded communication and asyncio.Queue for async tasks. defaultdict can create a value as a side effect of accessing a missing key, which should be considered in code and tests.

**itertools.** It provides lazy iterator building blocks such as chain, islice, pairwise, groupby, product, and combinations. These can avoid intermediate collections and support streaming transformations. However, a lazy iterator may be single-use, may retain references to source objects, and does not guarantee bounded memory across an entire processing pipeline. itertools.groupby groups consecutive runs with equal keys; it does not globally group all matching values. Sort by the same key first when global grouping is required.

**functools.** partial fixes some callable arguments; wraps preserves metadata when writing decorators; reduce folds an iterable, although a loop or specialized function is often clearer; lru_cache caches call results by arguments. Caching requires hashable arguments and a correct invalidation model. It must not accidentally mix data across users or tenants. lru_cache is not a distributed cache and does not provide domain-aware invalidation. It also does not automatically cache the awaited result of an async function: ordinary lru_cache may cache a coroutine object. Use an async-aware design with explicit concurrency and lifecycle semantics.

**contextlib.** contextmanager and asynccontextmanager express setup and cleanup around a generator. ExitStack and AsyncExitStack manage a dynamic collection of resources. suppress catches only explicitly listed exception types and should be narrow. closing and aclosing help close compatible resources. A context manager defines a resource ownership boundary: acquire, use, release. Cleanup failures and exception suppression must follow an explicit contract.

**dataclasses.** The dataclass decorator generates common methods such as __init__, __repr__, and __eq__ depending on its options. field(default_factory=...) creates a fresh mutable default per instance; a direct mutable default must not be shared. frozen=True prevents ordinary field reassignment but does not make nested mutable objects deeply immutable. slots=True can reduce instance overhead and prevent arbitrary attributes, with implications for inheritance, weak references, and compatibility. A dataclass is not automatically an input validator and does not replace Pydantic when parsing and validation are required.

**enum.** Enum defines a finite set of symbolic values, improving readability and state modeling. StrEnum is available from Python 3.11. auto() generates values according to the enum's rules. Once enum values are exposed through an API or persisted, they become part of a contract; changing them may require versioning or migration. Do not treat incidental auto-generated numeric values as durable external identifiers.

**datetime and zoneinfo.** For absolute points in time, use timezone-aware datetimes, commonly normalized to UTC. A naive datetime lacks enough information to identify an unambiguous instant. zoneinfo.ZoneInfo uses the IANA time zone database and supports regional rules. Local civil times can be ambiguous during a fall-back transition or nonexistent during a spring-forward transition. Adding one calendar day is not always equivalent to adding 24 hours in UTC. Domain logic should distinguish an instant, local date/time, time zone, and calendar date. APIs need an explicit format, time-zone policy, and behavior for ambiguous or nonexistent local times.

**pathlib and the filesystem.** pathlib provides an object-oriented path API and is generally clearer than manual string concatenation. Path normalization alone does not prevent path traversal. When handling user-supplied filenames, constrain access to approved directories, validate the resolved target, and account for symlinks and race conditions. A resolve-then-open sequence can have a TOCTOU weakness if an attacker can change the filesystem between operations. Sensitive operations require appropriate OS-level permissions and, where supported, safe operations relative to a trusted directory descriptor.

**logging.** The logging module provides levels, handlers, formatters, filters, and logger hierarchy. Applications should generally configure logging centrally at the entrypoint; modules should obtain loggers with getLogger(__name__). Libraries should not unexpectedly configure the root logger. Production logging benefits from structured fields, correlation/request IDs, and a consistent schema. Never log passwords, tokens, secrets, or unnecessary payment or medical data. Account for log injection, redaction, retention, access control, and volume. Log exceptions at the appropriate boundary rather than repeatedly logging the same failure at every layer.

**subprocess.** subprocess launches external processes and controls stdin/stdout/stderr, return codes, timeouts, and environment. For a simple invocation, subprocess.run with an explicit timeout and result checking (for example check=True when a non-zero exit is an error) is usually appropriate. Avoid shell=True with user-controlled data because it creates command-injection risk. Passing an argument list avoids shell parsing, but commands and arguments still require allowlisting and validation. Bound execution time and output, restrict process permissions, and control environment variables. Long-lived or high-volume process execution requires an explicit lifecycle and concurrency model.

In production, I choose a module based on the task's contract rather than code brevity. I check the supported Python version, edge-case semantics, error handling, thread safety, and resource limits. The standard library can help process external data, but validation, authorization, and domain invariants remain separate responsibilities. Important decisions should be captured in tests, documentation, and observability.

### Additional standard-library selection matrix

| Requirement | Prefer | Engineering note |
|---|---|---|
| Decimal arithmetic with explicit decimal semantics (for example, monetary calculations) | `decimal.Decimal` | Define precision, rounding, and quantization rules; do not assume binary float is exact decimal arithmetic. |
| Rational arithmetic | `fractions.Fraction` | Exact numerator/denominator arithmetic can cause numerator and denominator growth; assess cost and domain fit. |
| Security-sensitive tokens and secrets | `secrets` | Use cryptographically strong randomness; `random` is for simulation and non-security use. |
| Request/task-local context across async execution | `contextvars` | Prefer over manually threading request context through every call; understand propagation boundaries when using threads/processes. |
| Binary data views without an unconditional copy | `memoryview` and the buffer protocol | A view may share and expose mutable backing storage; lifetime and mutation ownership still matter. |

**RU:** Это не исчерпывающий каталог. `Decimal` подходит для десятичной арифметики с явно заданными правилами точности и округления; `Fraction` — для рациональной арифметики, но дроби могут увеличиваться. Для токенов и секретов используйте `secrets`, а не `random`. `contextvars` помогает переносить request/task-local context через async-вызовы. `memoryview` и buffer protocol позволяют работать с бинарными данными без обязательного копирования, но требуют внимания к владению, изменяемости backing buffer и времени жизни view.

**EN:** This is a selection guide, not an exhaustive catalogue. Use `Decimal` for decimal arithmetic with explicit precision and rounding rules; use `Fraction` for rational arithmetic while accounting for potentially growing numerators and denominators. Use `secrets` rather than `random` for tokens and security-sensitive values. `contextvars` helps propagate request/task-local context across asynchronous calls. `memoryview` and the buffer protocol enable binary access without an unconditional copy, but require care around backing-buffer ownership, mutability, and view lifetime.

**References:** decimal — https://docs.python.org/3.14/library/decimal.html ; fractions — https://docs.python.org/3.14/library/fractions.html ; secrets — https://docs.python.org/3.14/library/secrets.html ; contextvars — https://docs.python.org/3.14/library/contextvars.html ; memoryview — https://docs.python.org/3.14/library/stdtypes.html#memory-views

### Follow-up questions and model answers

#### FU-1. What is the difference between deque, queue.Queue, and asyncio.Queue?
**Answer (RU):** deque — контейнер с эффективными операциями с обоих концов, но сам по себе не предоставляет полноценный blocking producer/consumer protocol. queue.Queue предназначен для синхронизации потоков и поддерживает блокирующие операции и ограничения размера. asyncio.Queue предназначен для координации asyncio tasks и использует awaitable операции; он не является thread-safe. Выбор зависит от модели concurrency.

**Answer (EN):** deque is a container with efficient operations at both ends, but it does not provide a complete blocking producer/consumer protocol. queue.Queue supports synchronized threaded communication, blocking operations, and optional capacity limits. asyncio.Queue coordinates asyncio tasks through awaitable operations and is not thread-safe. Choose based on the concurrency model.

#### FU-2. Why can itertools.groupby produce surprising results?
**Answer (RU):** Потому что groupby объединяет только соседние последовательные элементы с одинаковым ключом. Если одинаковые ключи встречаются в разных частях входа, они попадут в разные группы. Для глобальной группировки вход обычно предварительно сортируют по тому же ключу либо используют mapping/SQL GROUP BY, если это лучше соответствует задаче.

**Answer (EN):** groupby combines only consecutive elements with equal keys. If the same key appears in separate parts of the input, it produces separate groups. For global grouping, sort by the same key first or use a mapping or SQL GROUP BY when that better fits the task.

#### FU-3. Why is lru_cache not a drop-in solution for caching async service calls?
**Answer (RU):** Обычный lru_cache кеширует результат непосредственного вызова функции. Для async-функции этим результатом является coroutine object, а не автоматически вычисленное значение. Повторное ожидание одного coroutine object некорректно. Кроме того, нужны TTL/invalidation, защита от cross-tenant leakage, concurrency control и обработка ошибок. Требуется async-aware cache с явно заданным lifecycle.

**Answer (EN):** Ordinary lru_cache caches the immediate function-call result. For an async function, that result is a coroutine object, not the awaited value. Re-awaiting the same coroutine object is invalid. A real service cache also needs TTL/invalidation, tenant isolation, concurrency control, and error handling. Use an async-aware cache with an explicit lifecycle.

#### FU-4. What is the difference between a timezone-aware datetime and a naive datetime?
**Answer (RU):** Aware datetime содержит информацию о timezone/UTC offset, позволяющую интерпретировать момент времени; naive datetime такой информации не содержит. Naive значение нельзя безопасно трактовать как UTC или локальное время без внешнего контракта. Для production API нужно явно определить timezone semantics и отдельно обработать ambiguous/nonexistent local times при DST transitions.

**Answer (EN):** An aware datetime contains time-zone or UTC-offset information that allows an instant to be interpreted; a naive datetime does not. A naive value must not be silently assumed to be UTC or local time without an external contract. Production APIs should define time-zone semantics and handle ambiguous or nonexistent local times around DST transitions.

#### FU-5. Why is pathlib.resolve() not, by itself, a complete defense against path traversal?
**Answer (RU):** Потому что проверка разрешённого пути и последующее открытие — отдельные операции. Между ними symlink или файловая структура могут измениться, создавая TOCTOU race. Кроме того, проверка должна учитывать доверенный root directory и корректные границы пути. Для чувствительных сценариев нужны OS-level permissions и безопасные операции открытия относительно доверенного directory descriptor, где это доступно.

**Answer (EN):** Because resolving and validating a path and opening it are separate operations. A symlink or filesystem change between them can create a TOCTOU race. Validation must also enforce a trusted root boundary. Sensitive cases require OS-level permissions and safe open operations relative to a trusted directory descriptor where available.

### Pharmaviyum connection — hypothetical interview scenario
Suppose a backend worker processes catalog import files and emits structured operational logs. pathlib could make path handling clearer, contextlib could scope temporary files or resources, dataclasses could model internal immutable-ish records, and enum could represent explicit import states. datetime/zoneinfo could support correctly defined scheduling semantics. subprocess should be introduced only if an external executable is genuinely required and must be constrained with an allowlist, timeout, and restricted environment. This is a hypothetical design exercise, not a claim that these exact modules or patterns are implemented in Pharmaviyum.

### Senior-level evaluation rubric
| Level | Expected evidence |
|---|---|
| Mid-level | Selects common standard-library modules and explains their basic APIs. |
| Senior | Explains iterator laziness, queue concurrency semantics, cache limitations, resource cleanup, DST edge cases, filesystem risks, logging hygiene, and subprocess safety. |
| Staff-level signal | Establishes reusable engineering conventions for resource ownership, time handling, logging and redaction, subprocess policy, portability, and operational limits across services. |

### Common pitfalls
- Treating deque as interchangeable with a synchronized queue.
- Assuming itertools.groupby performs global grouping.
- Applying lru_cache to async functions without understanding coroutine semantics.
- Using mutable dataclass defaults instead of default_factory.
- Assuming frozen dataclasses are deeply immutable.
- Persisting auto-generated enum values as stable external identifiers without a policy.
- Mixing naive and aware datetimes or assuming every local time exists exactly once.
- Treating pathlib normalization as a complete path traversal defense.
- Logging secrets or sensitive payloads.
- Using shell=True with untrusted input.
- Omitting timeouts and output/resource limits for subprocesses.
- Assuming standard-library APIs remove the need for validation and domain rules.

### References
- Python standard library: https://docs.python.org/3/library/
- collections: https://docs.python.org/3/library/collections.html
- itertools: https://docs.python.org/3/library/itertools.html
- functools: https://docs.python.org/3/library/functools.html
- contextlib: https://docs.python.org/3/library/contextlib.html
- dataclasses: https://docs.python.org/3/library/dataclasses.html
- enum: https://docs.python.org/3/library/enum.html
- datetime and zoneinfo: https://docs.python.org/3/library/datetime.html and https://docs.python.org/3/library/zoneinfo.html
- pathlib: https://docs.python.org/3/library/pathlib.html
- logging: https://docs.python.org/3/library/logging.html
- subprocess: https://docs.python.org/3/library/subprocess.html


## PY-CORE-023 — Python Packaging, Dependency Management and Virtual Environments

### Interview question
How would you package and distribute a Python application or library, manage its dependencies, and make builds reproducible across developer machines and CI/CD? Explain virtual environments, pip, pyproject.toml, build backends, wheels and source distributions, editable installs, dependency constraints and lockfiles, and software supply-chain risks.

### Что проверяет интервьюер
- Понимание различий между environment isolation, dependency resolution, packaging и deployment.
- Знание современного Python packaging workflow вокруг pyproject.toml, PEP 517/518/621 and PEP 660.
- Умение выбирать версии и фиксировать транзитивные зависимости для воспроизводимых установок.
- Понимание различий wheel и source distribution.
- Способность организовать production/dev/test dependency groups и CI build pipeline.
- Осознание supply-chain risks и безопасной конфигурации package indexes.

### Эталонный ответ (RU)
Управление зависимостями, упаковка и изоляция окружения — связанные, но разные задачи. Virtual environment изолирует установленный набор пакетов для конкретного проекта. Dependency resolver выбирает совместимые версии зависимостей. Packaging описывает проект как устанавливаемый distribution artifact. Deployment определяет, как этот artifact и его runtime dependencies попадают в целевую среду. Нельзя считать, что создание venv само по себе фиксирует версии или обеспечивает воспроизводимую сборку.

**Virtual environments.** venv создаёт изолированное окружение с отдельным site-packages и связанным с ним interpreter entrypoint. Окружение обычно не следует переносить между машинами или коммитить в репозиторий: оно содержит machine- и path-specific данные. Вместо этого в репозитории фиксируют инструкции и metadata зависимостей, а окружение создают заново. Нужно явно выбирать Python version и учитывать platform-specific dependencies. Активировать окружение удобно для интерактивной работы, но в CI надёжнее вызывать нужный interpreter или tool по явному пути.

**pip и dependency resolution.** pip устанавливает distributions и разрешает зависимости согласно version specifiers, environment markers и доступным package indexes. Ограничение вида >= задаёт допустимый диапазон, но не фиксирует точный набор транзитивных зависимостей. Верхние границы и точные pins имеют trade-offs: чрезмерно широкие диапазоны могут приводить к неожиданным обновлениям, а жёсткие pins требуют регулярного обновления и проверки безопасности. Constraints files ограничивают версии при разрешении, но сами по себе не являются полным lockfile и не обязательно перечисляют весь граф зависимостей.

**pyproject.toml.** Это современный стандартный файл конфигурации Python-проекта. Секция [build-system] объявляет build requirements и backend, [project] может содержать metadata, dependencies, optional-dependencies, scripts и другие сведения согласно PEP 621. Инструменты могут добавлять собственные секции, например для тестирования, linting или управления окружениями. pyproject.toml не является автоматически lockfile: он описывает декларативные требования и конфигурацию, а точный resolved graph обычно фиксируется отдельным lock artifact, если выбранный workflow его поддерживает.

**Build backends и стандарты.** PEP 517 определяет интерфейс между frontend-инструментом сборки и backend. PEP 518 описывает build-system requirements, необходимые для запуска backend. Backend, например setuptools, hatchling или flit, строит distributions. PEP 621 стандартизирует проектные metadata в pyproject.toml. Это разделение позволяет frontend-инструменту вызывать разные backend без привязки к внутренним деталям конкретного инструмента. Build isolation помогает не зависеть случайно от пакетов, установленных в глобальном окружении разработчика, но build dependencies также должны быть контролируемыми и воспроизводимыми.

**Wheel и source distribution.** Wheel (.whl) — готовый distribution artifact, который обычно устанавливается без повторной сборки исходников. Wheel может быть pure Python или platform-specific; его tags отражают совместимость по Python implementation/version, ABI и platform. Source distribution (sdist) содержит исходные файлы и metadata, из которых build backend может построить wheel. Установка из sdist требует build toolchain и build dependencies и может вести себя по-разному на разных системах. Для production deployment часто предпочтительно сначала собрать и протестировать wheel в CI, затем продвигать тот же artifact между окружениями.

**Editable installs.** Editable installation, стандартизованная PEP 660 для современных build backends, позволяет использовать исходный код из рабочей директории без обычного копирования package в site-packages. Это удобно для разработки, но не доказывает, что построенный wheel содержит все необходимые файлы и metadata. Поэтому CI должен отдельно собирать wheel и тестировать установку именно собранного artifact в чистом окружении.

**Dependency groups, extras и lockfiles.** Runtime dependencies — то, что требуется приложению при запуске. Optional dependencies/extras — дополнительные возможности package, которые потребитель устанавливает по явному запросу. Development/test/lint dependencies нужны для разработки и CI, но не должны автоматически попадать в runtime image, если они там не нужны. Стандартные project optional-dependencies описывают extras; управление development groups и lockfiles зависит от выбранного инструмента и его версии. Не существует единственного универсального lockfile формата, обязательного для всех Python tools. Команда должна выбрать инструмент и документировать его workflow.

Lockfile обычно фиксирует разрешённые версии транзитивных зависимостей, а в зависимости от формата — hashes, markers и сведения о source. Для воспроизводимости важны также Python version, OS/architecture, package index configuration и build dependencies. Некоторые lockfiles являются platform-aware или содержат несколько допустимых вариантов; одинаковый lockfile не гарантирует побитово идентичный build на разных системах, если toolchain и build inputs различаются. Нужно различать reproducible dependency resolution, repeatable installation и bit-for-bit reproducible artifact builds.

**Version policy.** Semantic Versioning полезен как ожидание совместимости, но не является доказательством качества release. Совместимость зависит от реальных контрактов package. Я задаю диапазоны для библиотечных зависимостей осознанно, обновляю lockfile контролируемыми изменениями, тестирую обновления и планирую регулярное patch/minor обновление. Для приложения можно использовать более строгую фиксацию resolved graph, чтобы деплой не менялся неожиданно. Не следует бесконтрольно смешивать package indexes: при использовании private index нужно явно определить доверенный источник и политику приоритета, чтобы избежать dependency confusion.

**Supply-chain security.** Установка package означает выполнение доверия к distribution и часто к его build/install behavior. Риски включают typosquatting, dependency confusion, compromised maintainer accounts, malicious releases, уязвимые версии и подмену артефактов. Практики защиты: доверенные package indexes, ограничение публикации и доступа, проверка package names и sources, hash checking там, где поддерживается, vulnerability scanning (например, pip-audit), обновления по review, SBOM и provenance/attestation для зрелого pipeline. Hash подтверждает соответствие конкретным bytes, но сам по себе не доказывает, что package безопасен или что источник заслуживает доверия. Build isolation тоже не является sandbox для недоверенного build code.

В production я строю pipeline так: определить поддерживаемую версию Python и платформы; описать package metadata и build backend; зафиксировать выбранный dependency workflow; создать чистое окружение; установить зависимости в контролируемом режиме; выполнить type checks, tests и security checks; собрать wheel; установить wheel в чистое окружение; выполнить smoke/integration tests; опубликовать artifact с traceable version и продвигать тот же artifact через deployment stages. Не следует выполнять новую независимую сборку на каждом окружении, если требование — продвигать один и тот же проверенный artifact.

### Professional answer (EN)
Dependency management, packaging, and environment isolation are related but distinct concerns. A virtual environment isolates installed packages for a project. A dependency resolver selects compatible versions. Packaging describes an installable distribution artifact. Deployment determines how that artifact and its runtime dependencies reach the target environment. Creating a venv does not by itself pin versions or make a build reproducible.

**Virtual environments.** venv creates an isolated environment with its own site-packages and interpreter entry point. Environments should generally not be moved between machines or committed to source control because they contain path- and machine-specific state. Store dependency metadata and setup instructions instead, then recreate the environment. Select the Python version explicitly and account for platform-specific dependencies. Activation is convenient for interactive work; in CI, invoking the intended interpreter or tool by an explicit path is often more deterministic.

**pip and dependency resolution.** pip installs distributions and resolves requirements using version specifiers, environment markers, and available package indexes. A range such as >= defines an allowed set but does not pin the complete transitive dependency graph. Upper bounds and exact pins have trade-offs: broad ranges can introduce unexpected upgrades, while strict pins require regular maintenance and security review. A constraints file influences version selection but is not, by itself, a complete lockfile and need not enumerate the entire dependency graph.

**pyproject.toml.** This is the modern standard configuration file for Python projects. The [build-system] table declares build requirements and the backend; [project] can declare metadata, dependencies, optional-dependencies, scripts, and related fields under PEP 621. Tools may add their own sections for testing, linting, or environment management. pyproject.toml is not automatically a lockfile: it describes declared requirements and configuration, while an exact resolved graph is usually captured in a separate lock artifact when the chosen workflow supports one.

**Build backends and standards.** PEP 517 defines the interface between a build frontend and a backend. PEP 518 specifies the build-system requirements needed to start the backend. A backend such as setuptools, hatchling, or flit builds distribution artifacts. PEP 621 standardizes project metadata in pyproject.toml. This separation lets frontends invoke different backends without depending on each backend's internal implementation. Build isolation reduces accidental reliance on globally installed developer packages, but build dependencies must also be controlled and reproducible.

**Wheels and source distributions.** A wheel (.whl) is a built distribution that can generally be installed without rebuilding the source. A wheel may be pure Python or platform-specific; its tags express compatibility across Python implementation/version, ABI, and platform. A source distribution (sdist) contains source files and metadata from which a backend can build a wheel. Installing from an sdist requires build tooling and build dependencies and may vary across systems. For production, it is often preferable to build and test a wheel in CI, then promote that same artifact through environments.

**Editable installs.** Editable installation, standardized by PEP 660 for modern build backends, exposes source code from the working tree during development rather than performing a conventional copy into site-packages. This is convenient but does not prove that a built wheel contains all required files and metadata. CI should separately build a wheel and test installing that artifact into a clean environment.

**Dependency groups, extras, and lockfiles.** Runtime dependencies are required by the application at runtime. Optional dependencies or extras expose additional package features that consumers install explicitly. Development, test, and lint dependencies support engineering workflows and should not automatically enter a runtime image when they are not needed there. Project optional-dependencies describe extras; development groups and lockfile behavior depend on the selected tool and its version. There is no single universal lockfile format mandated for every Python toolchain. A team should choose and document its workflow.

A lockfile commonly records resolved transitive versions and, depending on the format, hashes, markers, and source information. Reproducibility also depends on Python version, OS/architecture, package-index configuration, and build dependencies. Some lockfiles are platform-aware or include multiple permitted variants; the same lockfile does not guarantee a bit-for-bit identical build across systems if toolchains and build inputs differ. Distinguish reproducible dependency resolution, repeatable installation, and bit-for-bit reproducible artifact builds.

**Version policy.** Semantic Versioning is a useful compatibility expectation, not proof that a release is safe or compatible. Compatibility depends on the package's actual contracts. I choose dependency ranges deliberately, update lockfiles through reviewed changes, test upgrades, and schedule regular patch/minor updates. An application may use stricter resolved-version locking to avoid unexpected deployment changes. Avoid mixing package indexes without a clear trust and priority policy; private-index configuration must account for dependency-confusion risk.

**Supply-chain security.** Installing a package means trusting its distribution and often its build/install behavior. Risks include typosquatting, dependency confusion, compromised maintainer accounts, malicious releases, vulnerable versions, and artifact substitution. Controls include trusted package indexes, restricted publishing and access, validation of package names and sources, hash checking where supported, vulnerability scanning (for example pip-audit), reviewed upgrades, SBOMs, and provenance/attestations in a mature pipeline. A hash confirms that bytes match a reference; it does not prove that a package is benign or that its publisher is trustworthy. Build isolation is not a sandbox for untrusted build code.

For production, I define supported Python versions and platforms, declare project metadata and a build backend, choose and document a dependency workflow, create a clean environment, install dependencies under controlled conditions, run type checks, tests, and security checks, build a wheel, install that wheel into a clean environment, run smoke/integration tests, and publish a traceable artifact. The same tested artifact should be promoted through deployment stages rather than independently rebuilt in each environment when artifact promotion is the requirement.

### Follow-up questions and model answers

#### FU-1. What is the difference between pyproject.toml, a constraints file, and a lockfile?
**Answer (RU):** pyproject.toml описывает metadata проекта, build configuration и заявленные зависимости. Constraints file ограничивает версии, которые resolver может выбрать, но не обязательно описывает полный граф. Lockfile фиксирует конкретное разрешённое дерево зависимостей и дополнительные сведения, зависящие от формата. Это разные роли; наличие pyproject.toml не означает, что зависимости полностью locked.

**Answer (EN):** pyproject.toml describes project metadata, build configuration, and declared requirements. A constraints file limits versions the resolver may select but does not necessarily describe the complete graph. A lockfile records a resolved dependency graph and format-specific details. These serve different purposes; having pyproject.toml does not mean dependencies are fully locked.

#### FU-2. Why should CI test the built wheel instead of relying only on an editable install?
**Answer (RU):** Editable install использует исходную рабочую директорию и может скрыть ошибки packaging: отсутствующие package data, неверную конфигурацию включения файлов или metadata. Wheel — тот artifact, который обычно устанавливается потребителем. Поэтому CI должен собрать wheel, установить его в чистое окружение и протестировать импорт и поведение уже установленного distribution.

**Answer (EN):** An editable install uses the source working tree and can hide packaging defects such as missing package data, incorrect file inclusion, or metadata problems. The wheel is the artifact consumers generally install. CI should build the wheel, install it into a clean environment, and test imports and behavior from the installed distribution.

#### FU-3. Does a lockfile guarantee a bit-for-bit reproducible build?
**Answer (RU):** Не обязательно. Lockfile помогает зафиксировать dependency resolution, но результат может зависеть от Python version, OS/architecture, environment markers, build backend, build dependencies, compiler и системных библиотек. Нужно различать повторяемую установку зависимостей и побитово идентичный artifact. Для последнего фиксируют и проверяют весь build environment и inputs.

**Answer (EN):** Not necessarily. A lockfile helps pin dependency resolution, but results may also depend on Python version, OS/architecture, environment markers, build backend, build dependencies, compiler, and system libraries. Repeatable dependency installation is different from a bit-for-bit identical artifact. The latter requires controlling and verifying the complete build environment and inputs.

#### FU-4. How would you separate runtime and development dependencies?
**Answer (RU):** Runtime dependencies должны содержать только то, что нужно приложению при запуске. Test, lint, type-checking и build tools относятся к development/CI workflow и не должны попадать в production image без необходимости. Extras предназначены для опциональных функций package, которые потребитель выбирает явно. Конкретный механизм групп зависит от выбранного packaging tool, поэтому policy нужно документировать и проверять состав итогового artifact/image.

**Answer (EN):** Runtime dependencies should include only what the application needs to execute. Test, lint, type-checking, and build tools belong to development/CI workflows and should not enter the production image unnecessarily. Extras expose optional package features selected explicitly by consumers. The exact grouping mechanism depends on the chosen packaging tool, so document the policy and verify the final artifact/image contents.

#### FU-5. What is dependency confusion, and how can a team reduce the risk?
**Answer (RU):** Dependency confusion возникает, когда package manager получает одноимённый package из неожиданного или менее доверенного index вместо intended private package. Снижение риска требует явной конфигурации trusted indexes и приоритетов, уникальных имён внутренних packages, ограничений на публикацию, проверки источника и review dependency changes. Нельзя считать простое наличие private index достаточной защитой.

**Answer (EN):** Dependency confusion occurs when a package manager resolves a package name from an unexpected or less-trusted index instead of the intended private package. Mitigations include explicit trusted-index and priority configuration, unique internal package names, restricted publishing, source verification, and review of dependency changes. Merely configuring a private index is not sufficient protection.

### Pharmaviyum connection — hypothetical interview scenario
Suppose a team needs to build a Python backend artifact for deployment to a pharmacy server while maintaining a separate demo environment. A disciplined workflow could declare runtime and development dependencies separately, pin the supported Python version, resolve dependencies in CI, build a wheel or application artifact, test it in a clean environment, and promote the same verified artifact through deployment stages. The exact packaging tool and artifact format must be selected to match the repository and deployment design. This is a hypothetical engineering scenario, not a claim that this exact packaging pipeline is already implemented in Pharmaviyum.

### Senior-level evaluation rubric
| Level | Expected evidence |
|---|---|
| Mid-level | Explains venv, pip requirements, pyproject.toml, and the basic purpose of wheels. |
| Senior | Distinguishes declarations, constraints, and lockfiles; explains build isolation, PEP 517/518/621/660, wheel testing, runtime/dev separation, and dependency security. |
| Staff-level signal | Defines a reproducible artifact-promotion strategy, trusted-index policy, dependency update governance, build provenance, and cross-platform compatibility controls for multiple services. |

### Common pitfalls
- Committing or copying a virtual environment as the dependency-management strategy.
- Assuming a version range pins the complete transitive dependency graph.
- Treating pyproject.toml as a universal lockfile.
- Confusing constraints files with lockfiles.
- Assuming build isolation makes builds fully reproducible or safe.
- Testing only editable installs and never installing the built wheel.
- Assuming every wheel is platform-independent.
- Mixing runtime, development, and optional dependencies without a clear policy.
- Treating Semantic Versioning as a guarantee of compatibility.
- Trusting package names or hashes without validating package source and provenance.
- Assuming a lockfile alone guarantees bit-for-bit reproducible builds.
- Promoting independently rebuilt artifacts instead of the artifact that passed CI.

### References
- Python Packaging User Guide: https://packaging.python.org/
- pyproject.toml specification: https://packaging.python.org/en/latest/specifications/pyproject-toml/
- PEP 517 — Build system interface: https://peps.python.org/pep-0517/
- PEP 518 — Build system requirements: https://peps.python.org/pep-0518/
- PEP 621 — Project metadata: https://peps.python.org/pep-0621/
- PEP 660 — Editable installs: https://peps.python.org/pep-0660/
- Python venv documentation: https://docs.python.org/3/library/venv.html
- pip user guide: https://pip.pypa.io/en/stable/user_guide/
- pip dependency resolution: https://pip.pypa.io/en/stable/topics/dependency-resolution/
- pip-audit: https://github.com/pypa/pip-audit


---

## PY-CORE-024 — Python Testing Fundamentals, pytest and Test Architecture

### Question (EN)

**How would you design a reliable Python test strategy, and how do pytest fixtures, parametrization, test doubles, and different testing levels fit into it?**

### Перевод (RU)

**Как спроектировать надёжную стратегию тестирования Python-приложения и какую роль в ней играют уровни тестирования, fixtures, параметризация и тестовые двойники pytest?**

### What the interviewer evaluates

- Selecting a test level based on the contract and failure mode being verified.
- Understanding pytest collection, fixtures, scopes, parametrization, and teardown.
- Using mocks and other test doubles without coupling tests to implementation details.
- Test isolation, deterministic behaviour, async testing, and external-resource management.
- Understanding coverage limitations, property-based testing, mutation testing, and contract testing.
- Designing maintainable test architecture rather than maximising test count.

### Model answer (RU)

Надёжная стратегия тестирования начинается не с выбора инструмента, а с определения **контрактов, рисков и границ системы**. Я выбираю самый узкий уровень, который способен достоверно проверить требуемое поведение, и дополняю его интеграционными и сквозными тестами там, где важны реальные взаимодействия компонентов.

**Уровни тестирования.** Unit-тест проверяет небольшую единицу поведения изолированно — например, доменное правило или функцию нормализации. Integration-тест проверяет взаимодействие нескольких реальных компонентов: repository с PostgreSQL, endpoint с dependency injection или обработчик с брокером сообщений. Functional/API-тест проверяет поведение через публичный интерфейс с точки зрения сценария. E2E-тест проходит через максимально близкий к реальному пользовательский путь и обычно дороже, медленнее и чувствительнее к инфраструктуре. Термины functional и integration в командах могут пересекаться, поэтому важнее явно определить границы каждого набора.

**pytest.** pytest обнаруживает тесты, собирает их до выполнения, применяет marks и parametrization, разрешает зависимости fixtures и запускает тестовые функции. Обычные assert сопровождаются полезным introspection. Файл conftest.py позволяет организовать общие fixtures на уровне каталогов без прямого импорта. Плагины расширяют runner, но их следует добавлять осознанно, учитывая совместимость и сложность.

**Fixtures и lifecycle.** Fixture — управляемая pytest зависимость для подготовки состояния или ресурса. Зависимости fixtures выражаются через аргументы функций; pytest строит граф setup и выполняет teardown в обратном порядке. Scope бывает function (по умолчанию), class, module, package и session. Более широкий scope уменьшает стоимость setup, но увеличивает риск общего изменяемого состояния и межтестовой зависимости. Для ресурса с cleanup удобно использовать yield fixture или context manager. Setup должен быть минимальным, teardown — гарантированным, а fixture не должна скрывать существенные действия теста. Autouse следует применять ограниченно: неявные зависимости усложняют понимание теста.

**Parametrization.** pytest.mark.parametrize запускает один тестовый контракт на нескольких наборах входных данных. Это полезно для boundary values, вариантов ошибок, локалей, форматов и комбинаций параметров. Идентификаторы параметров должны помогать диагностике. Не следует превращать параметризацию в огромный непрозрачный Cartesian product; разделяйте независимые измерения и используйте targeted pairwise или property-based подход там, где пространство комбинаций велико.

**Test doubles.** Stub возвращает заранее заданный ответ; fake имеет упрощённую рабочую реализацию (например, in-memory repository); spy записывает вызовы; mock задаёт ожидания и проверяет взаимодействия. В Python применяются unittest.mock, Mock, MagicMock, AsyncMock и pytest monkeypatch. Я предпочитаю fake или реальный компонент, когда это остаётся быстро и надёжно, а mock использую на внешней границе — например, для проверки контракта стороннего API. Чрезмерное mocking внутренних методов связывает тест с текущей реализацией и делает рефакторинг болезненным. Патчить нужно имя там, где код его lookup-ит, а не обязательно исходное место определения объекта.

**Isolation и determinism.** Каждый тест должен контролировать данные, время, случайность, environment variables, filesystem и сеть, от которых зависит результат. Избегайте зависимости от порядка запуска, общего изменяемого состояния, реального времени, нестабильных внешних API и случайно разделяемых database records. Используйте уникальные тестовые данные, транзакционные или disposable database стратегии, временные каталоги, контролируемые часы и фиксированные seeds там, где это уместно. Не маскируйте race conditions простыми sleep. Параллельный запуск допустим только при доказанной изоляции ресурсов.

**Async и API testing.** Async-код нужно тестировать в event loop с инструментами, совместимыми с используемым async framework; для pytest обычно используют pytest-asyncio или соответствующий plugin и явно определяют режим владения loop. Проверяйте результат, исключения, timeout, cancellation и cleanup tasks. Для FastAPI отдельно проверяйте dependency overrides и HTTP-контракты через тестовый client. Integration tests должны при необходимости использовать реальный PostgreSQL совместимой версии: mocking всех зависимостей не проверит SQL, транзакции, constraints или сериализацию.

**Property-based, coverage и mutation testing.** Property-based testing с Hypothesis генерирует множество входов и проверяет инварианты, а не только заранее перечисленные примеры; shrinking помогает получить минимальный failing case. Coverage показывает, какой код был выполнен, но высокий line coverage не доказывает, что assertions проверяют правильное поведение. Branch coverage даёт дополнительный сигнал, но также не измеряет качество спецификации. Mutation testing вносит контролируемые изменения в код и проверяет, обнаруживает ли их тестовый набор; выжившие мутации могут указывать на слабые assertions или непроверенные ветви. Mutation testing дорог, поэтому его применяют выборочно к критичным модулям.

**Contract tests и test pyramid.** Contract tests фиксируют ожидания между потребителем и поставщиком API или event schema, включая совместимость и ошибки. Они дополняют, но не заменяют интеграционные тесты. Практическая пирамида обычно содержит много быстрых unit-тестов, меньше интеграционных и ограниченное число E2E-тестов. Это не жёсткий закон: распределение определяется архитектурой и рисками. Я оцениваю suite по скорости обратной связи, диагностируемости, стабильности, покрытию критических контрактов и стоимости поддержки, а не только по количеству тестов.

На Senior-позиции я ожидаю, что тесты проверяют наблюдаемое поведение, корректно изолируют побочные эффекты, воспроизводятся локально и в CI, а flaky tests расследуются как дефект тестовой системы, а не бесконечно ретраятся.

### Professional answer (EN)

A reliable test strategy starts with **system contracts, risks, and boundaries**, not with a tool choice. I select the narrowest test level that can credibly verify the behaviour and add integration and end-to-end coverage where real component interactions matter.

**Testing levels.** A unit test verifies a small unit of behaviour in isolation, such as a domain rule. An integration test verifies collaboration between components, for example a repository against PostgreSQL or an endpoint with its dependency graph. A functional or API test verifies a user- or consumer-visible capability through an application interface. An end-to-end test exercises a realistic user journey across much of the system; it is typically slower, more expensive, and more infrastructure-sensitive. Teams sometimes use “functional” and “integration” differently, so the suite should document its boundaries rather than rely on labels alone.

**pytest execution model.** pytest discovers and collects tests before execution, applies marks and parametrization, resolves fixture dependencies, and invokes test functions. Plain assert statements provide useful assertion introspection. conftest.py provides directory-level fixtures and hooks without importing them into every test module. Plugins extend the runner, but each adds compatibility and maintenance considerations.

**Fixtures and lifecycle.** A fixture is a managed dependency used to prepare state or resources. Fixture dependencies are declared as function arguments; pytest resolves the dependency graph and tears fixtures down in reverse setup order. Scopes include function (the default), class, module, package, and session. Broader scopes reduce setup cost but increase the risk of shared mutable state and order-dependent tests. Use yield fixtures or context managers for resources requiring cleanup. Keep setup small, teardown reliable, and important test actions visible. Use autouse sparingly because implicit dependencies make tests harder to understand.

**Parametrization.** pytest.mark.parametrize runs the same contract against multiple input sets. It is useful for boundary values, error cases, locales, formats, and option combinations. Give cases readable IDs. Avoid an opaque Cartesian explosion; separate independent dimensions and consider targeted pairwise or property-based testing when the input space is large.

**Test doubles.** A stub returns predefined data; a fake is a simplified working implementation such as an in-memory repository; a spy records interactions; a mock defines expectations and verifies calls. Python provides unittest.mock, Mock, MagicMock, AsyncMock, and pytest monkeypatch. I prefer a fake or real component when it remains fast and reliable, and use mocks at external boundaries—for example, to verify a third-party API contract. Excessive mocking of internal methods couples tests to implementation details and makes refactoring difficult. Patch the name where the system under test looks it up, which is not necessarily the object's original definition site.

**Isolation and determinism.** Tests should control data, time, randomness, environment variables, filesystem state, and network dependencies. Avoid order dependence, shared mutable state, wall-clock assumptions, unstable external APIs, and colliding database records. Use unique test data, transactional or disposable database strategies, temporary directories, controlled clocks, and fixed random seeds where appropriate. Do not hide races with arbitrary sleeps. Parallel execution is safe only when resource isolation is established.

**Async and API testing.** Test async code under an event loop using tooling compatible with the chosen async framework. With pytest, this commonly means pytest-asyncio or another framework-specific plugin, with explicit loop ownership and configuration. Verify results, exceptions, timeouts, cancellation, and task cleanup. For FastAPI, test dependency overrides and HTTP contracts through a test client. Integration tests should use a real PostgreSQL instance when SQL semantics, transactions, constraints, or serialization are part of the contract; mocking every dependency cannot verify those behaviours.

**Property-based testing, coverage, and mutation testing.** Hypothesis generates many inputs and checks invariants rather than relying only on hand-picked examples; shrinking helps reduce a failing input to a simpler counterexample. Coverage reports which code executed, but high line coverage does not prove that assertions verify correct behaviour. Branch coverage adds information but still cannot measure specification quality. Mutation testing makes controlled changes to code and checks whether tests detect them; surviving mutants can reveal weak assertions or untested decisions. Because mutation testing is expensive, apply it selectively to critical modules.

**Contract tests and the test pyramid.** Contract tests capture expectations between API or event-schema consumers and providers, including compatibility and error behaviour. They complement rather than replace integration tests. A practical pyramid often has many fast unit tests, fewer integration tests, and a limited number of E2E tests. It is a heuristic, not a law; architecture and risk determine the right balance. I evaluate a suite by feedback time, diagnosability, stability, critical-contract coverage, and maintenance cost—not just test count.

At Senior level, I expect tests to assert observable behaviour, isolate side effects correctly, run reproducibly in local development and CI, and treat flaky tests as defects in the test system rather than problems to conceal with repeated retries.

### Follow-up questions and model answers

#### FU-1 — How do pytest fixture scopes affect isolation and reliability?

**RU:** Как scope pytest fixtures влияет на изоляцию и надёжность тестов?

**Answer (RU):** Function scope создаёт отдельный экземпляр для каждого теста и обычно является наиболее безопасным вариантом для изменяемого состояния. Class, module, package и session scopes позволяют переиспользовать дорогие ресурсы, но разделяют состояние между большим числом тестов. Это повышает риск утечек состояния, зависимости от порядка и проблем параллельного запуска. Я расширяю scope только после измерения стоимости setup, делаю shared state неизменяемым либо явно сбрасываемым и обеспечиваю надёжный teardown. Параметризованная fixture может вызываться несколько раз в пределах scope для разных параметров.

**Answer (EN):** Function scope creates a fresh fixture instance per test and is usually the safest choice for mutable state. Class, module, package, and session scopes reuse expensive resources but share them across more tests, increasing the risk of state leakage, order dependence, and parallel-execution conflicts. I broaden scope only after measuring setup cost, keep shared state immutable or explicitly resettable, and provide reliable teardown. A parametrized fixture may be invoked more than once within its scope for different parameters.

#### FU-2 — When should you use a mock, a fake, or a real dependency?

**RU:** Когда следует использовать mock, fake или реальную зависимость?

**Answer (RU):** Реальную зависимость использую, если она достаточно быстрая, детерминированная и доступна в тестовом окружении; это особенно важно для проверки SQL и интеграционных контрактов. Fake подходит, когда нужна упрощённая, но рабочая модель зависимости. Mock полезен на границе с внешним или дорогим сервисом, чтобы проверить конкретное взаимодействие, ошибки и timeout. Mock внутреннего метода часто проверяет структуру реализации, а не поведение. Для patch важно подменять символ в namespace, где тестируемый код его использует.

**Answer (EN):** I use a real dependency when it is sufficiently fast, deterministic, and available in the test environment—especially when SQL semantics or integration contracts matter. A fake provides a simplified but working implementation. A mock is useful at an external or expensive boundary when verifying a specific interaction, error, or timeout. Mocking an internal method often verifies implementation structure rather than behaviour. A patch should replace the symbol in the namespace where the code under test looks it up.

#### FU-3 — Why is high code coverage not proof of a high-quality test suite?

**RU:** Почему высокий code coverage не доказывает высокое качество тестового набора?

**Answer (RU):** Coverage показывает выполнение строк или ветвей, но не гарантирует, что assertions проверяют существенные результаты. Тест может выполнить код и ничего значимого не проверить либо проверять только happy path. Качество оценивается по контрактам, граничным условиям, негативным сценариям, изоляции и способности обнаруживать регрессии. Mutation testing даёт дополнительный сигнал: если очевидные мутации выживают, assertions могут быть недостаточными. Но mutation score также не является абсолютной метрикой качества.

**Answer (EN):** Coverage shows which lines or branches executed; it does not guarantee that assertions checked meaningful outcomes. A test may execute code without verifying anything important or may cover only the happy path. Quality depends on the contracts, boundaries, negative cases, isolation, and regression-detection ability being tested. Mutation testing adds a useful signal: if obvious mutations survive, assertions may be weak. However, mutation score is not an absolute quality metric either.

#### FU-4 — How would you test asynchronous code and cancellation safely?

**RU:** Как безопасно тестировать асинхронный код и cancellation?

**Answer (RU):** Тест запускается в управляемом event loop, совместимом с framework и pytest plugin. Я проверяю успешный результат, исключения, timeout, отмену задачи, освобождение ресурсов и отсутствие фоновых задач после завершения теста. Для конкурентных сценариев использую явные synchronization primitives или контролируемые события, а не произвольные sleep. Внешние async-клиенты подменяю AsyncMock только там, где тест проверяет взаимодействие; integration test при необходимости использует реальный тестовый сервис. Настройки loop scope и fixture scope должны быть согласованы.

**Answer (EN):** Run the test in a controlled event loop compatible with the framework and pytest plugin. Verify successful results, exceptions, timeouts, task cancellation, resource cleanup, and the absence of leaked background tasks after the test. For concurrency scenarios, use explicit synchronization primitives or controlled events rather than arbitrary sleeps. Replace external async clients with AsyncMock only when the test is about the interaction; an integration test should use a real test service when required. Event-loop and fixture scopes must be configured consistently.

#### FU-5 — How would you build a test strategy for a FastAPI service backed by PostgreSQL?

**RU:** Как построить стратегию тестирования FastAPI-сервиса с PostgreSQL?

**Answer (RU):** Доменную логику проверяю быстрыми unit-тестами без HTTP и БД. Для API проверяю status codes, response schemas, validation, authentication/authorization и dependency overrides через test client. Repository и transaction behaviour проверяю интеграционными тестами на реальном PostgreSQL с изолированной схемой или disposable database, включая constraints, migrations, rollback и конкурентные сценарии, если они входят в контракт. E2E-тесты оставляю для нескольких критичных пользовательских потоков. Тестовые данные должны быть уникальными, очистка — надёжной, secrets — тестовыми, а CI должен запускать существенные проверки на поддерживаемых версиях Python и PostgreSQL. Для async endpoints учитываю event-loop и client lifecycle.

**Answer (EN):** I test domain logic with fast unit tests that do not require HTTP or a database. API tests cover status codes, response schemas, validation, authentication/authorization, and dependency overrides through a test client. Repository and transaction behaviour is verified with integration tests against real PostgreSQL using an isolated schema or disposable database, including constraints, migrations, rollback, and concurrency cases when they are part of the contract. I reserve E2E tests for a small number of critical user journeys. Test data must be unique, cleanup reliable, secrets non-production, and CI should run essential checks against supported Python and PostgreSQL versions. For async endpoints, I account for event-loop and client lifecycle.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a pharmacy workflow API may need tests for medication-search validation, inventory updates, authentication boundaries, and persistence. Unit tests could verify domain rules; API tests could verify HTTP contracts and authorization; PostgreSQL integration tests could verify transaction and constraint behaviour; a small E2E set could cover a critical workflow. If an AI/RAG component is involved, separate deterministic retrieval/evaluation tests from nondeterministic live-model checks and assert measurable contracts such as citation presence, entity preservation, and patient-context isolation. Inspect the actual repository and test configuration before claiming that any of these tests already exist.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Mid-level | Writes unit tests, uses pytest assertions and basic fixtures, understands mocks and parametrization. |
| Senior | Designs balanced test architecture; controls fixture lifecycle and isolation; deliberately chooses real dependencies or test doubles; tests async, persistence, API contracts, and failure paths; understands coverage limitations. |
| Staff-level signal | Establishes test reliability standards, CI feedback strategy, contract ownership, flaky-test governance, risk-based mutation/property testing, and cross-service compatibility practices. |

### Common pitfalls

- Treating line coverage as a proxy for correctness.
- Using broad-scoped fixtures with mutable state without reset and cleanup.
- Mocking every dependency and never testing real database or framework behaviour.
- Patching the definition site instead of the lookup site.
- Asserting private method calls instead of externally observable behaviour.
- Depending on test order, shared records, wall-clock timing, or arbitrary sleeps.
- Ignoring cancellation and leaked tasks in async tests.
- Building a brittle E2E-heavy suite while leaving domain contracts untested.
- Retrying flaky tests indefinitely instead of finding the source of nondeterminism.
- Assuming Hypothesis, coverage, or mutation score alone proves test quality.

### References

- pytest fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html
- pytest parametrization: https://docs.pytest.org/en/stable/how-to/parametrize.html
- pytest monkeypatch: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- pytest fixture reference: https://docs.pytest.org/en/stable/reference/fixtures.html
- Python unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Hypothesis documentation: https://hypothesis.readthedocs.io/
- pytest-asyncio documentation: https://pytest-asyncio.readthedocs.io/
- Coverage.py: https://coverage.readthedocs.io/
- mutmut documentation: https://mutmut.readthedocs.io/


---

## PY-CORE-025 — Python Logging, Diagnostics and Observability

### Question (EN)

**How would you design production-grade logging and observability for a Python backend, including structured logs, correlation context, exception handling, and distributed tracing?**

### Перевод (RU)

**Как спроектировать production-ready логирование и наблюдаемость Python backend, включая структурированные логи, correlation context, обработку исключений и распределённую трассировку?**

### What the interviewer evaluates

- Python logger hierarchy and the roles of loggers, handlers, filters, and formatters.
- Useful log levels and structured, machine-queryable event fields.
- Safe propagation of request and trace context across async execution and service boundaries.
- Exception logging with useful stack traces and no sensitive-data exposure.
- Differences between logs, metrics, and traces; OpenTelemetry instrumentation.
- Operational diagnostics, incident response, telemetry overhead, and cost control.

### Model answer (RU)

Production observability — это не просто запись строк в файл. Это способность понять **что произошло, где, когда, с каким запросом и каким влиянием на систему**, используя согласованные logs, metrics и traces. Начинаю с operational questions и SLO/SLI, затем выбираю сигналы и контекст, позволяющие проверять гипотезы при инциденте.

**Python logging architecture.** Стандартный модуль logging разделяет создание события и его обработку. Logger создаёт LogRecord; Handler направляет запись в output; Formatter формирует представление; Filter может отбирать или обогащать записи. Имена logger обычно следуют иерархии модулей, например service.api.orders. Записи могут распространяться к ancestor loggers через propagation. Конфигурацию следует централизовать на уровне приложения, избегать дублирующих handlers и понимать взаимодействие logger levels, handler levels и propagate. Библиотеки обычно получают logger через logging.getLogger(__name__), но не должны самостоятельно перенастраивать root logger.

**Log levels и события.** DEBUG предназначен для диагностических деталей, INFO — для значимых событий нормального выполнения, WARNING — для неожиданной ситуации, не остановившей операцию, ERROR — для неуспешной операции, требующей внимания, CRITICAL — для серьёзного отказа. Уровень выбирается по операционному смыслу, а не только по классу исключения. Не следует логировать каждый успешный шаг: высокочастотные события увеличивают стоимость, шум и риск раскрытия данных. Rate limiting, sampling и агрегированные метрики помогают с повторяющимися событиями, но sampling не должен удалять обязательные security/audit records.

**Structured logging.** Вместо одного свободного текста событие должно содержать стабильные поля: timestamp, severity, event_name, service.name, environment, request_id, trace_id, span_id, route, duration_ms, outcome и безопасные доменные атрибуты. Значения должны иметь стабильные типы и ограниченную cardinality. Request ID полезен как поле поиска в логах, но обычно является плохим высококардинальным metric label. Не включайте целые request bodies, headers, access tokens, passwords, secrets, медицинские данные или полные персональные записи. Используйте allowlist безопасных полей, redaction до отправки в sink и тесты на отсутствие секретов. Логи не должны превращаться в копию базы данных.

**Correlation context и asyncio.** Для связывания событий одного запроса подходит contextvars.ContextVar. Middleware или instrumentation устанавливает request/correlation ID на входе и сбрасывает token в finally. Context variables предназначены для контекста выполнения и обычно распространяются при создании asyncio tasks; при ручном создании threads, processes, очередей или внешних сообщений правила propagation отличаются и могут требовать явной передачи контекста. Не храните request-specific данные в глобальных изменяемых переменных. Для межсервисной трассировки используйте стандартный propagation format, например W3C Trace Context и traceparent. Проверяйте формат и длину входящего correlation ID.

**Exception logging.** Логируйте исключение на том уровне, где есть контекст для решения или где ошибка становится наблюдаемым отказом. logger.exception(...) вызывается внутри обработчика исключения и добавляет traceback. Не логируйте одно исключение на каждом слое: это создаёт дублирование. Сохраняйте причинную цепочку через raise ... from ... и различайте бизнес-ошибки, validation failures, временные инфраструктурные сбои и программные дефекты. HTTP API должен возвращать безопасную ошибку и correlation/trace reference; stack trace остаётся в защищённой системе диагностики. Не раскрывайте внутренние exception messages клиенту.

**Logs, metrics и traces.** Logs описывают дискретные события и их контекст. Metrics агрегируют числовые измерения во времени: request rate, error rate, latency histogram, queue depth и resource saturation. Traces показывают путь запроса через spans и сервисы, помогая локализовать задержки и зависимости. Метрика обнаруживает аномалию, trace показывает путь и узкий участок, logs объясняют конкретное событие. Для latency используйте histograms и percentiles, а не только среднее. Контролируйте cardinality: user ID, request ID и произвольные URL не должны становиться metric labels.

**OpenTelemetry.** OpenTelemetry предоставляет vendor-neutral APIs, SDKs, semantic conventions и exporters для traces, metrics и logs; поддержка конкретных signal pipelines зависит от SDK и backend. Instrumentation бывает automatic и manual. Automatic instrumentation даёт базовые spans для поддерживаемых библиотек; manual instrumentation добавляет доменный контекст и важные границы. Не создавайте span для каждой тривиальной функции: span должен отражать meaningful operation. Настраивайте sampling, exporter timeouts, batching, resource attributes и flush/shutdown при завершении приложения. Сбой exporter не должен ломать пользовательский request path. Не записывайте sensitive attributes. В async services проверяйте передачу context между tasks и инструментированными клиентами.

**Production diagnostics.** Логи должны быть структурированными, централизованными, ограниченными по retention и доступу. Нужны синхронизация времени, health signals, dashboards, alerts с привязкой к SLO, runbooks и связи между alert, trace и logs. При инциденте определяйте временной интервал, affected service/version, недавние deployment changes, распределения ошибок и latency, representative trace samples. Затем коррелируйте логи по trace/request ID и проверяйте saturation, database pool, queues и внешние зависимости. Не включайте DEBUG глобально в production без ограниченного по времени и scope решения. Учитывайте backpressure: logging pipeline может блокироваться или терять записи при недоступности sink. Queueing, bounded buffers, drop policy и fallback выбираются с учётом критичности событий.

На Senior-уровне важен не максимальный объём логов, а наблюдаемость с понятной семантикой, низким overhead, контролем cardinality и конфиденциальности, а также возможностью восстановить причинно-следственную картину инцидента.

### Professional answer (EN)

Production observability is more than writing strings to a file. It is the ability to understand **what happened, where, when, for which request, and with what system impact** using coherent logs, metrics, and traces. I start with operational questions and SLOs/SLIs, then select signals and context that help validate incident hypotheses.

**Python logging architecture.** The standard logging module separates event creation from event handling. A Logger creates a LogRecord; a Handler routes it to an output; a Formatter renders it; and a Filter can select or enrich records. Logger names commonly follow module hierarchy, such as service.api.orders. Records may propagate to ancestor loggers. Centralize configuration at application startup, avoid duplicate handlers, and understand logger levels, handler levels, and propagation. Libraries should obtain a logger with logging.getLogger(__name__) and should not configure the root logger themselves.

**Levels and event semantics.** DEBUG is for diagnostic detail, INFO for meaningful normal-operation events, WARNING for unexpected conditions that did not prevent the operation, ERROR for failed operations requiring attention, and CRITICAL for severe failures. Choose levels based on operational meaning, not merely exception class. Avoid logging every successful step: high-volume events increase cost, noise, and exposure risk. Rate limiting, sampling, or aggregated metrics can help with repetitive events, but sampling must not discard required security or audit records.

**Structured logging.** Prefer stable fields over a free-form string: timestamp, severity, event_name, service.name, environment, request_id, trace_id, span_id, route, duration_ms, outcome, and safe domain attributes. Keep types stable and cardinality bounded. A request ID is useful as a searchable log field but is usually a poor high-cardinality metric label. Do not include entire request bodies, headers, access tokens, passwords, secrets, medical data, or complete personal records. Use allowlisted fields, redact before exporting to a sink, and test that secrets are absent. Logs should not become a copy of the database.

**Correlation context and asyncio.** contextvars.ContextVar can carry request-scoped context. Middleware or instrumentation sets a request/correlation ID at ingress and resets its token in a finally block. Context variables are designed for execution context and are generally propagated across asyncio task creation; manually created threads, processes, queues, or external messages have different propagation semantics and may require explicit context transfer. Do not store request-specific state in global mutable variables. Across services, use a standard propagation format such as W3C Trace Context and traceparent. Validate and length-limit inbound correlation IDs.

**Exception logging.** Log an exception at the layer that has enough context to make a decision or where the failure becomes observable. Call logger.exception(...) inside an exception handler to include the traceback. Do not log the same exception at every layer. Preserve causal chains with raise ... from ... and distinguish expected business errors, validation failures, transient infrastructure failures, and programming defects. An HTTP API should return a safe error and a correlation/trace reference; the stack trace belongs in a protected diagnostic system. Never expose internal exception messages to clients.

**Logs, metrics, and traces.** Logs describe discrete events and context. Metrics aggregate measurements over time, such as request rate, error rate, latency histograms, queue depth, and resource saturation. Traces show a request path through spans and services. A metric detects an anomaly, a trace identifies the path and bottleneck, and logs explain specific events. Use histograms and percentiles for latency rather than relying only on averages. Control cardinality: do not use user IDs, request IDs, or arbitrary URLs as metric labels.

**OpenTelemetry.** OpenTelemetry provides vendor-neutral APIs, SDKs, semantic conventions, and exporters for traces, metrics, and logs; support for individual signal pipelines depends on the SDK and backend. Instrumentation can be automatic or manual. Automatic instrumentation provides baseline spans for supported libraries; manual instrumentation adds domain context and meaningful boundaries. Do not create a span for every trivial function. Configure sampling, exporter timeouts, batching, resource attributes, and flush/shutdown during application termination. Exporter failures should not break the user request path. Avoid sensitive span attributes. Verify context propagation across async tasks and instrumented clients.

**Production diagnostics.** Logs should be structured, centralized, access-controlled, and subject to retention limits. Provide clock synchronization, health signals, dashboards, SLO-based alerts, runbooks, and links between alerts, traces, and logs. During an incident, establish the time window, affected service/version, recent deployment changes, error and latency distributions, and representative trace samples. Correlate logs by trace/request ID and inspect saturation, database pools, queues, and external dependencies. Do not enable DEBUG globally in production without a time-bounded, scoped reason. Account for backpressure: a logging pipeline can block or drop records when a sink is unavailable. Choose queueing, bounded buffers, drop policy, and fallback behaviour according to event criticality.

At Senior level, the goal is not maximum log volume. It is observability with clear semantics, low overhead, controlled cardinality and privacy, and enough causal context to reconstruct an incident.

### Follow-up questions and model answers

#### FU-1 — Explain the roles of Logger, Handler, Formatter, and Filter in Python logging.

**RU:** Объясните роли Logger, Handler, Formatter и Filter в Python logging?

**Answer (RU):** Logger создаёт и передаёт LogRecord, Handler определяет destination и способ доставки, Formatter формирует представление записи, а Filter может отбрасывать или обогащать записи. Уровни logger и handler влияют на обработку записи. Propagation направляет запись к ancestor loggers, поэтому handlers на нескольких уровнях могут привести к дублированию. Конфигурацию выполняет приложение при старте; библиотечный код не должен самовольно перенастраивать root logger.

**Answer (EN):** A Logger creates and passes a LogRecord, a Handler determines the destination and delivery mechanism, a Formatter renders the record, and a Filter can reject or enrich records. Logger and handler levels both affect processing. Propagation sends records to ancestor loggers, so handlers at multiple levels can cause duplicates. The application owns startup configuration; library code should not reconfigure the root logger.

#### FU-2 — How do you propagate request context safely across async tasks?

**RU:** Как безопасно передавать request context между async tasks?

**Answer (RU):** Для request-scoped значений использую ContextVar, устанавливаю token в middleware и обязательно сбрасываю его через reset(token) в finally. asyncio поддерживает context propagation при создании tasks, но нельзя предполагать такую же семантику для threads, processes, внешних очередей и сообщений. На границах сервисов передаю trace context через W3C Trace Context. Не использую глобальные mutable variables и не помещаю чувствительные данные в context.

**Answer (EN):** I use a ContextVar for request-scoped values, set its token in middleware, and always reset it in a finally block. asyncio propagates context when tasks are created, but the same semantics should not be assumed for threads, processes, external queues, or messages. Across services, propagate trace context through W3C Trace Context. Avoid global mutable variables and sensitive context values.

#### FU-3 — What is the difference between logs, metrics, and distributed traces?

**RU:** В чём разница между logs, metrics и distributed traces?

**Answer (RU):** Logs содержат отдельные события с контекстом; metrics агрегируют измерения и подходят для трендов, alerting и SLO; traces показывают причинный путь операции через spans и сервисы. Рост latency metric обнаруживает проблему, trace локализует медленный downstream call, а связанные logs объясняют конкретную ошибку. Сигналы коррелируются через trace/span IDs, но каждый должен оставаться полезным самостоятельно. Для metrics особенно важен контроль cardinality.

**Answer (EN):** Logs contain individual contextual events; metrics aggregate measurements and support trends, alerting, and SLOs; traces show an operation's causal path through spans and services. A latency metric detects a problem, a trace locates a slow downstream call, and correlated logs explain a specific failure. Signals correlate through trace and span IDs but should remain useful independently. Cardinality control is especially important for metrics.

#### FU-4 — How would you prevent sensitive information from leaking into logs and traces?

**RU:** Как предотвратить утечку чувствительной информации в logs и traces?

**Answer (RU):** Использую allowlist безопасных полей вместо логирования произвольных объектов. Secrets, credentials, access tokens, персональные и медицинские данные исключаются или редактируются до отправки в sink/exporter. Redaction централизуется, но не считается единственной защитой: тесты ищут известные secret patterns, доступ к хранилищу ограничивается, retention минимизируется, а security audit events проектируются отдельно. Не возвращаю stack traces и внутренние exception messages клиенту. Контролирую span attributes и baggage, поскольку trace context пересекает границы доверия.

**Answer (EN):** I use an allowlist of safe fields rather than logging arbitrary objects. Secrets, credentials, access tokens, personal data, and medical data must be excluded or redacted before reaching a sink or exporter. Centralize redaction but do not treat it as the only safeguard: test for known secret patterns, restrict storage access, minimize retention, and design security audit events separately. Do not return stack traces or internal exception messages to clients. Control span attributes and baggage because trace context can cross trust boundaries.

#### FU-5 — How would you instrument a FastAPI service with OpenTelemetry without harming request reliability?

**RU:** Как инструментировать FastAPI-сервис с OpenTelemetry, не ухудшая надёжность обработки запросов?

**Answer (RU):** Начинаю с поддерживаемой automatic instrumentation для ASGI/FastAPI и используемых HTTP/database clients, затем добавляю manual spans только для важных доменных операций. Конфигурирую service/resource attributes, W3C propagation, sampling, batching и exporter timeout. Недоступность telemetry backend не должна превращаться в ошибку пользовательского запроса. При shutdown выполняю flush/shutdown SDK с ограниченным timeout. Исключаю sensitive attributes, контролирую cardinality и проверяю propagation через async tasks и downstream calls интеграционными тестами.

**Answer (EN):** I start with supported automatic instrumentation for ASGI/FastAPI and the HTTP/database clients in use, then add manual spans only for meaningful domain operations. I configure service/resource attributes, W3C propagation, sampling, batching, and exporter timeouts. Telemetry backend unavailability must not become a user-request failure. On shutdown, flush and shut down the SDK with a bounded timeout. Exclude sensitive attributes, control cardinality, and verify propagation across async tasks and downstream calls with integration tests.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a pharmacy workflow API could use structured events to correlate a medicine search, inventory read, and sale persistence without logging patient-identifying or prescription details. A trace could show time spent in the API, database, and an external AI/RAG dependency; metrics could track latency, error rate, queue depth, and dependency availability. If OpenTelemetry is adopted, instrumentation should preserve trace context across async operations and redact clinical/personal data before export. Inspect the actual repository, telemetry configuration, retention policy, and production deployment before claiming any of this is implemented or verified.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Mid-level | Uses Python logging, selects basic log levels, records exceptions, and understands handlers and formatters. |
| Senior | Designs structured logs and correlation context; understands async propagation; distinguishes logs, metrics, and traces; instruments services with OpenTelemetry; controls sensitive data, cardinality, overhead, and exporter failure modes. |
| Staff-level signal | Defines cross-service telemetry conventions, SLO-aligned alerting, retention/access policies, sampling strategy, incident workflows, and observability cost governance. |

### Common pitfalls

- Calling basicConfig independently in multiple modules or attaching duplicate handlers.
- Confusing logger levels with handler levels and overlooking propagation.
- Logging arbitrary request objects, headers, tokens, or clinical/personal data.
- Using request IDs, user IDs, or unbounded values as metric labels.
- Storing request context in global mutable state.
- Assuming context propagation is identical across asyncio tasks, threads, processes, and message queues.
- Logging the same exception at every layer and generating duplicate tracebacks.
- Returning internal exception details or stack traces to API clients.
- Treating logs as a replacement for metrics and distributed traces.
- Creating spans for trivial functions or attaching sensitive attributes.
- Allowing telemetry exporter failures or unbounded queues to block application requests.
- Enabling verbose production logging indefinitely without assessing cost and exposure.

### References

- Python logging HOWTO: https://docs.python.org/3/howto/logging.html
- Python logging reference: https://docs.python.org/3/library/logging.html
- Python contextvars: https://docs.python.org/3/library/contextvars.html
- asyncio task context: https://docs.python.org/3/library/asyncio-task.html
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- OpenTelemetry context propagation: https://opentelemetry.io/docs/concepts/context-propagation/
- W3C Trace Context: https://www.w3.org/TR/trace-context/
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/specs/semconv/


---

## PY-CORE-026 — Python Security, Secure Coding and Common Vulnerabilities

### Question (EN)

**How do you design and review a secure Python backend? Explain how you prevent injection, SSRF, path traversal, insecure deserialization, broken access control, and secret exposure.**

### Перевод (RU)

**Как проектировать и проверять безопасность Python backend? Объясните, как предотвращать injection, SSRF, path traversal, небезопасную десериализацию, ошибки контроля доступа и утечки секретов.**

### What the interviewer evaluates

- Threat modeling, trust boundaries, attack surface, and secure-by-default design.
- Safe database queries and subprocess execution.
- Defense against SSRF, path traversal, unsafe file handling, and insecure deserialization.
- Authentication versus authorization, object-level access control, and least privilege.
- Secret management, password hashing, cryptographic hygiene, and key rotation.
- Input validation, output encoding, dependency security, and security testing.
- Risk-based prioritization, incident response, and residual-risk reasoning.

### Model answer (RU)

Безопасность backend начинается с определения **активов, угроз, границ доверия и последствий компрометации**, а не с выбора отдельной библиотеки. Я строю threat model: какие данные и операции критичны, кто контролирует входные данные, какие компоненты доступны из сети и где проходят границы между пользователем, API, БД, очередями и внешними сервисами. Затем применяю defense in depth: least privilege, secure defaults, явные контракты, изоляцию, мониторинг и тестирование.

**Injection.** Для SQL использую parameterized queries или ORM expressions, где значения передаются отдельно от SQL syntax. Не конкатенирую пользовательские значения в SQL. Имена колонок, сортировка и другие SQL identifiers обычно не параметризуются как обычные значения, поэтому выбираю их из строгого allowlist. Для shell-команд предпочитаю subprocess с массивом аргументов и shell=False; не формирую команду из пользовательской строки. Parameterization не отменяет необходимость ограниченных DB permissions и лимитов ресурсов.

**Input validation и output encoding.** На границе системы проверяю форму, тип, длину, диапазон, формат и бизнес-инварианты. Pydantic помогает валидировать структуру входных данных, но сам по себе не обеспечивает authorization, безопасный SQL или output encoding. Для HTML применяю контекстно-зависимое escaping и безопасные шаблоны; для JSON — корректную сериализацию. Blacklist validation недостаточна. Normalization и canonicalization должны соответствовать конкретному формату и выполняться до security-sensitive проверок, чтобы избежать разных интерпретаций одних данных.

**Path traversal и файловые операции.** Не строю filesystem path напрямую из пользовательского имени. Использую allowlist идентификаторов, ограничиваю доступ выделенной директорией и проверяю resolved canonical path. Простая проверка строкового префикса небезопасна: /safe/root-evil начинается с /safe/root, но не является дочерним каталогом. Учитываю symlinks, race conditions и TOCTOU между проверкой и открытием. Для строгой защиты применяю directory file descriptors и операции относительно доверенного directory handle, где это поддерживает платформа. Ограничиваю размер и permissions файлов и не доверяю расширению или MIME type, заявленному клиентом.

**SSRF.** Если backend загружает URL, предоставленный пользователем, злоумышленник может обратиться к loopback, private network, cloud metadata endpoint или внутреннему сервису. По возможности не принимаю произвольные URLs, а использую resource IDs или allowlisted hosts. Иначе проверяю scheme, hostname и порты; разрешаю DNS и проверяю все полученные IP-адреса; блокирую loopback, private, link-local, multicast и reserved ranges; контролирую redirects и повторно валидирую каждый redirect target. Проверки только hostname недостаточно из-за DNS rebinding и изменения адреса после проверки. Network egress policy должна запрещать доступ к чувствительным внутренним сегментам. Учитываю proxy configuration и IPv4/IPv6.

**Insecure deserialization.** Не использую pickle для данных из недоверенных источников: unpickling может выполнять произвольный код. Предпочитаю ограниченные форматы данных, например JSON, и валидирую результат по явной схеме. JSON тоже требует ограничений на размер, глубину, типы и business invariants; он не защищает автоматически от DoS или logic flaws. Для подписанных payload проверяю подпись/MAC до доверия содержимому и корректно управляю key rotation. Подпись не делает небезопасный формат безопасным, если ключ или источник скомпрометирован.

**Authentication и authorization.** Authentication отвечает «кто пользователь?», authorization — «какие действия и над какими объектами ему разрешены?». Проверки доступа выполняются на сервере для каждого чувствительного действия и объекта, а не только через скрытие UI controls. Проверяю tenant/owner scope в запросах, предотвращаю IDOR/BOLA, применяю least privilege и deny-by-default. JWT проверяю по ожидаемому algorithm, issuer, audience, expiration, not-before и доверенному ключу; не принимаю algorithm или key material из недоверенного token header. Проектирую revocation/session lifecycle, refresh-token rotation и безопасное хранение credentials. Роли не заменяют object-level authorization.

**Passwords и cryptography.** Пароли храню только с помощью специализированного password-hashing algorithm с уникальной солью и настроенной стоимостью, например Argon2id или подходящего поддерживаемого варианта scrypt/bcrypt. Не использую plain SHA-256/MD5 как password hash. Параметры cost выбираются по актуальным рекомендациям и измерениям на целевой инфраструктуре. Секреты и ключи хранятся вне репозитория и application image, выдаются через secret manager или защищённую runtime configuration, имеют ограниченный доступ и регулярно ротируются. Шифрование требует управления ключами, nonce/IV, алгоритмами и lifecycle; собственную криптографию не проектирую. Для сравнения MAC/signature использую constant-time comparison, где применимо.

**Secrets и конфигурация.** Не коммичу .env, private keys, tokens или production credentials. Не помещаю секреты в Docker image, build logs, exception messages, telemetry или клиентские bundles. При утечке отзываю и ротирую секрет, оцениваю scope доступа и проверяю audit logs; удаления из последнего commit недостаточно, если секрет остался в истории или артефактах. Разделяю credentials по средам и сервисам, использую отдельные DB roles и минимальные permissions.

**Dependency и supply-chain security.** Фиксирую и регулярно обновляю зависимости, проверяю advisories, версии и происхождение пакетов. Использую lock/constraints policy выбранного инструментария, hash verification там, где поддерживается, vulnerability scanning и SBOM при необходимости. Учитываю typosquatting, dependency confusion, compromised maintainers и вредоносные release artifacts. Scanner — сигнал для triage, а не доказательство безопасности. Build isolation не является security sandbox.

**Security testing и operations.** Добавляю негативные тесты для boundary conditions, object-level authorization, injection payloads, traversal, redirect/SSRF handling и malformed inputs. Использую static analysis, dependency scanning, secret scanning, fuzz/property-based tests и risk-based penetration testing. В production нужны безопасные error responses, rate limits, audit trails критичных действий, ограниченные permissions, security monitoring и проверенный incident response. Логи не должны раскрывать токены, пароли или медицинские/персональные данные. При инциденте сохраняю evidence, ограничиваю доступ, ротирую credentials и следую процедуре восстановления.

Senior-инженер должен объяснять не только конкретную защиту, но и **какую угрозу она устраняет, на каких предположениях основана и какие остаточные риски остаются**.

### Professional answer (EN)

Backend security starts with identifying **assets, threats, trust boundaries, and the impact of compromise**, not with selecting a library. I build a threat model: which data and operations are critical, who controls inputs, which components are network-reachable, and where trust boundaries exist between users, APIs, databases, queues, and external services. I then apply defense in depth: least privilege, secure defaults, explicit contracts, isolation, monitoring, and testing.

**Injection.** For SQL, I use parameterized queries or ORM expressions that keep values separate from SQL syntax. I never concatenate user-controlled values into SQL. Identifiers such as column names and sort directions generally cannot be bound as ordinary values, so I select them from a strict allowlist. For shell execution, I prefer subprocess with an argument array and shell=False; I do not construct shell commands from user input. Parameterization does not remove the need for restricted database privileges and resource limits.

**Input validation and output encoding.** Validate shape, type, length, range, format, and business invariants at system boundaries. Pydantic can validate input structure, but it does not provide authorization, safe SQL, or output encoding by itself. For HTML, use context-aware escaping and safe templating; for JSON, use correct serialization. A blacklist is not sufficient. Normalization and canonicalization must match the relevant format and occur before security-sensitive checks to avoid inconsistent interpretations.

**Path traversal and file handling.** Do not build filesystem paths directly from user-supplied names. Use allowlisted identifiers, constrain access to a dedicated directory, and validate the resolved canonical path. A simple string-prefix check is unsafe: /safe/root-evil starts with /safe/root but is not a child directory. Account for symlinks, race conditions, and TOCTOU between validation and opening. For stronger guarantees, use directory file descriptors and operations relative to a trusted directory handle where supported. Enforce restrictive permissions and size limits; do not trust a client-provided extension or MIME type.

**SSRF.** If a backend fetches user-supplied URLs, an attacker may target loopback, private networks, cloud metadata endpoints, or internal services. Avoid arbitrary URLs when resource IDs or allowlisted hosts meet the use case. Otherwise validate scheme, hostname, and allowed ports; resolve DNS and inspect every resulting IP address; block loopback, private, link-local, multicast, and reserved ranges; control redirects and revalidate every redirect target. Hostname-only checks are insufficient because of DNS rebinding and address changes after validation. Network egress policy should also deny access to sensitive internal segments. Consider proxy configuration and IPv4/IPv6.

**Insecure deserialization.** Never use pickle with untrusted data: unpickling can execute arbitrary code. Prefer constrained data formats such as JSON and validate the result against an explicit schema. JSON still requires limits on size, nesting depth, types, and business invariants; it is not automatically immune to denial-of-service or logic flaws. For signed payloads, verify the signature or MAC before trusting the contents and manage key rotation correctly. A signature does not make an unsafe format safe if the key or producer is compromised.

**Authentication and authorization.** Authentication answers “who is the user?”; authorization answers “which actions may this user perform on which objects?” Enforce access checks server-side for every sensitive action and object, not merely by hiding UI controls. Scope data queries by tenant and ownership, prevent IDOR/BOLA, apply least privilege, and default to deny. Validate JWTs against the expected algorithm, issuer, audience, expiration, not-before claim, and trusted key; do not accept an algorithm or key material from an untrusted token header. Design revocation and session lifecycle, refresh-token rotation, and credential storage deliberately. Roles alone do not replace object-level authorization.

**Passwords and cryptography.** Store passwords only using a dedicated password-hashing algorithm with a unique salt and calibrated work factor, such as Argon2id or an appropriately supported scrypt/bcrypt configuration. Do not use plain SHA-256 or MD5 as a password hash. Choose parameters using current guidance and measurements on target infrastructure. Keep secrets and keys outside source control and application images; deliver them through a secret manager or protected runtime configuration, restrict access, and rotate them. Encryption requires key, nonce/IV, algorithm, and lifecycle management; do not invent cryptography. Use constant-time comparison for MACs or signatures where applicable.

**Secrets and configuration.** Never commit .env files, private keys, tokens, or production credentials. Do not place secrets in Docker images, build logs, exception messages, telemetry, or client bundles. If a secret leaks, revoke and rotate it, assess access scope, and inspect audit logs; deleting it from the latest commit is insufficient if it remains in history or artifacts. Separate credentials by environment and service, use distinct database roles, and grant minimum permissions.

**Dependency and supply-chain security.** Pin and regularly update dependencies, review advisories, versions, and package provenance. Apply the lock/constraints policy supported by the chosen toolchain, hash verification where available, vulnerability scanning, and an SBOM when appropriate. Consider typosquatting, dependency confusion, compromised maintainers, and malicious release artifacts. A scanner finding is a triage signal, not proof that an application is vulnerable or safe. Build isolation is not a security sandbox.

**Security testing and operations.** Add negative tests for boundary conditions, object-level authorization, injection payloads, traversal, redirect/SSRF handling, and malformed inputs. Use static analysis, dependency and secret scanning, fuzz/property-based tests, and risk-based penetration testing. Production needs safe error responses, rate limits, audit trails for critical actions, restricted permissions, security monitoring, and a rehearsed incident response process. Logs must not expose tokens, passwords, or medical/personal data. During an incident, preserve evidence, contain access, rotate credentials, and follow recovery procedures.

A Senior engineer should explain not only the control, but **which threat it mitigates, what assumptions it relies on, and what residual risks remain**.

### Follow-up questions and model answers

#### FU-1 — Why are parameterized queries necessary, and when do allowlists still matter?

**RU:** Почему необходимы параметризованные запросы и в каких случаях всё равно нужны allowlists?

**Answer (RU):** Параметризованный запрос отделяет SQL syntax от данных, поэтому пользовательское значение интерпретируется как значение, а не как часть команды. Но bind parameters обычно не заменяют имена таблиц/колонок, направления сортировки или SQL keywords. Такие динамические identifiers нужно выбирать из строгого allowlist, а не вставлять произвольный ввод. Дополнительно применяю DB least privilege, ограничения ресурсов и тесты на injection.

**Answer (EN):** Parameterized queries separate SQL syntax from data, so user input is treated as a value rather than executable SQL. However, bind parameters generally do not substitute table or column identifiers, sort directions, or SQL keywords. Select such dynamic identifiers from a strict allowlist instead of interpolating arbitrary input. Also apply database least privilege, resource limits, and injection-focused tests.

#### FU-2 — How do you defend a URL-fetching feature against SSRF?

**RU:** Как защитить функцию загрузки по URL от SSRF?

**Answer (RU):** Предпочитаю allowlisted destinations или идентификаторы ресурсов вместо произвольных URLs. Если URL необходим, разрешаю только ожидаемые schemes/ports, валидирую hostname и DNS results, блокирую private, loopback, link-local и reserved IP ranges, контролирую redirects и повторяю проверку для каждого target. Учитываю DNS rebinding, IPv4/IPv6, proxy и egress firewall. Одной проверки hostname до HTTP-запроса недостаточно; проверка и фактическое соединение должны быть согласованы, а доступ к внутренним сетям ограничен на сетевом уровне.

**Answer (EN):** Prefer allowlisted destinations or resource identifiers over arbitrary URLs. If URLs are required, allow only expected schemes and ports, validate the hostname and DNS results, block private, loopback, link-local, and reserved IP ranges, control redirects, and revalidate every target. Account for DNS rebinding, IPv4/IPv6, proxies, and egress firewalls. A hostname check before the HTTP request is not sufficient; validation must be consistent with the actual connection, and network-level controls must restrict internal access.

#### FU-3 — Why is a string-prefix check insufficient for preventing path traversal?

**RU:** Почему проверки строкового префикса недостаточно для защиты от path traversal?

**Answer (RU):** Строковый префикс не доказывает принадлежность пути каталогу: /srv/app-data-evil имеет префикс /srv/app-data, но не является его дочерним путём. Нужно разрешить путь относительно доверенного base directory и проверить component-aware containment после canonicalization. Symlinks и TOCTOU могут изменить объект между проверкой и открытием. Для строгой модели применяю операции относительно directory file descriptor и минимальные filesystem permissions, где это поддерживается.

**Answer (EN):** A string prefix does not prove directory containment: /srv/app-data-evil starts with /srv/app-data but is not a descendant. Resolve the path against a trusted base directory and check component-aware containment after canonicalization. Symlinks and TOCTOU can still change the target between checking and opening. For a stronger model, use operations relative to a directory file descriptor and restrictive filesystem permissions where supported.

#### FU-4 — Why should untrusted pickle data never be deserialized, and is JSON automatically safe?

**RU:** Почему нельзя десериализовать недоверенные pickle-данные и является ли JSON автоматически безопасным?

**Answer (RU):** Pickle reconstruction может вызывать callable и выполнять произвольный код, поэтому unpickling недоверенного payload создаёт риск code execution. JSON не имеет той же модели произвольного восстановления объектов, но не становится автоматически безопасным: нужны schema validation, ограничения размера и глубины, контроль типов, business invariants и защита от resource exhaustion. Формат сериализации не заменяет проверку доверия к источнику и авторизацию.

**Answer (EN):** Pickle reconstruction can invoke callables and execute arbitrary code, so unpickling an untrusted payload creates a code-execution risk. JSON does not have the same arbitrary object-reconstruction model, but it is not automatically safe: apply schema validation, size and depth limits, type checks, business invariants, and resource-exhaustion controls. A serialization format does not replace source trust and authorization checks.

#### FU-5 — How do authentication and authorization differ, and how do you prevent IDOR/BOLA?

**RU:** Чем authentication отличается от authorization и как предотвращать IDOR/BOLA?

**Answer (RU):** Authentication подтверждает личность субъекта; authorization проверяет, разрешено ли этому субъекту конкретное действие над конкретным объектом в данном контексте. Для защиты от IDOR/BOLA сервер проверяет ownership/tenant scope при каждом доступе к объекту, а не полагается на непредсказуемость ID или UI. Запросы к данным должны включать проверенный scope, доступ по умолчанию запрещён, а привилегии минимальны. Тестирую попытки доступа к чужим объектам с разными ролями и tenant contexts.

**Answer (EN):** Authentication establishes a subject's identity; authorization determines whether that subject may perform a specific action on a specific object in context. To prevent IDOR/BOLA, the server checks ownership and tenant scope on every object access instead of relying on unpredictable IDs or UI restrictions. Data queries must include the verified scope, access defaults to deny, and privileges are minimized. Test cross-user and cross-tenant object access under different roles.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a pharmacy backend may process medicine catalog searches, stock operations, sales, prescription-related workflows, and AI/RAG requests. A security review should verify that each tenant/user can access only authorized records; SQL uses parameterized statements; uploaded/imported files are constrained and validated; outbound URL fetching cannot reach internal services; and logs, prompts, traces, and error responses do not expose patient or prescription data. Any statement that a specific control is implemented or test-verified requires repository and deployment evidence.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Mid-level | Recognizes common injection risks, uses parameterized queries, validates input, and avoids committing secrets. |
| Senior | Threat-models trust boundaries; addresses SSRF, traversal, deserialization, object-level authorization, secret lifecycle, dependency risks, and secure operations; explains residual risk and test strategy. |
| Staff-level signal | Establishes security architecture, risk acceptance, secure SDLC controls, incident response, identity boundaries, and organization-wide security standards. |

### Common pitfalls

- Treating input validation as a substitute for parameterized SQL or authorization.
- Concatenating user-controlled data into SQL or shell commands.
- Assuming ORM use makes every query safe.
- Checking only URL hostnames and ignoring DNS resolution, redirects, and egress controls.
- Using string-prefix checks for filesystem containment.
- Ignoring symlinks and TOCTOU in file operations.
- Unpickling untrusted data or assuming JSON removes all parsing/DoS risks.
- Confusing authentication with authorization or checking permissions only in the UI.
- Trusting JWT headers, accepting unintended algorithms, or omitting issuer/audience/expiry validation.
- Storing passwords with fast general-purpose hashes.
- Committing secrets or assuming deleting a secret from the latest commit revokes it.
- Treating dependency scanners, SBOMs, or build isolation as complete security guarantees.
- Logging sensitive payloads, credentials, tokens, or patient data.
- Failing to plan secret rotation, incident containment, and auditability.

### References

- OWASP Top 10: https://owasp.org/Top10/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- OWASP SQL Injection Prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP SSRF Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- Python subprocess documentation: https://docs.python.org/3/library/subprocess.html
- Python pickle security warning: https://docs.python.org/3/library/pickle.html
- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html
- NIST Digital Identity Guidelines: https://pages.nist.gov/800-63-4/
- OWASP Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html


## PY-CORE-027 — Python API Design, HTTP Semantics and Backend Contracts

**Question (EN):** How do you design a reliable, evolvable HTTP API in Python, and which HTTP semantics and contract guarantees must a Senior backend engineer preserve?

**Вопрос (RU):** Как проектировать надёжный и развиваемый HTTP API на Python и какие HTTP-семантики и гарантии контракта должен обеспечивать Senior backend engineer?

### What the interviewer evaluates

- Whether the candidate understands HTTP semantics rather than treating REST as CRUD naming.
- Correct use of methods, status codes, idempotency, conditional requests, and caching.
- Ability to design explicit request/response contracts and evolve them safely.
- Pagination, filtering, sorting, validation, and stable error semantics.
- Separation of transport, application, and domain concerns in a Python backend.
- OpenAPI quality, compatibility strategy, and contract/integration testing.
- Operational concerns: timeouts, rate limits, retries, observability, and resource bounds.

### Эталонный ответ (RU)

Надёжный API начинается с **контракта и семантики ресурса**, а не с выбора URL или FastAPI decorator. Сначала определяю ресурсы, допустимые операции, инварианты предметной области, субъектов доступа и ожидаемое поведение при ошибках. Затем фиксирую request/response schemas, HTTP semantics, правила совместимости и тестируемые гарантии.

**Ресурсы и методы HTTP.** URL обычно идентифицирует ресурс или коллекцию, а HTTP method задаёт семантику операции. GET предназначен для безопасного чтения и не должен иметь намеренных побочных эффектов; HEAD возвращает метаданные без тела; POST обычно инициирует обработку или создание подчинённого ресурса; PUT заменяет представление ресурса и по семантике идемпотентен; PATCH частично изменяет ресурс, но идемпотентность зависит от формата и конкретной операции; DELETE идемпотентен по требуемому эффекту, даже если повторный ответ может отличаться. Не выбираю метод только по названию функции.

**Идемпотентность и повторы.** Idempotency означает, что повтор одного и того же запроса приводит к тому же целевому эффекту, что и один запрос. Это особенно важно при сетевых сбоях, когда клиент не знает, был ли запрос обработан. Для повторяемых команд, например создания продажи или проведения платежа, можно определить idempotency key, область уникальности, срок хранения результата и правила обработки одновременных повторов. Запись ключа и бизнес-операции должна быть согласована транзакционно; иначе дублирование всё ещё возможно. Не обещаю exactly-once delivery на уровне HTTP: обычно проектирую at-least-once retries вместе с идемпотентной обработкой и дедупликацией.

**Status codes и ошибки.** Использую коды по смыслу: 200 для успешного ответа с представлением, 201 для созданного ресурса (часто с Location), 202 для принятой асинхронной обработки, 204 для успеха без тела, 400 для некорректного запроса, 401 для отсутствующей/недействительной аутентификации, 403 для запрещённого действия, 404 когда ресурс не найден или его существование намеренно скрывается, 409 для конфликта состояния, 412 при невыполненном условии precondition, 422 для синтаксически корректного, но семантически невалидного содержимого в принятой API-конвенции, 429 для rate limit и 5xx для серверных ошибок. Не использую 200 с полем success=false для обычных ошибок. Единый error envelope должен иметь стабильный machine-readable code, безопасное сообщение, при необходимости field-level details и correlation/request ID. Внутренние stack traces, SQL, credentials и чувствительные данные клиенту не возвращаются.

**Request и response contracts.** Входные данные валидируются на границе API: типы, обязательность, диапазоны, длины, форматы и cross-field constraints. Валидация формы не заменяет domain validation, authorization или проверку конкурентных инвариантов в базе данных. Response schema — явная проекция публичного контракта, а не автоматическая сериализация ORM-модели: это снижает риск утечки внутренних полей и связывания API с persistence model. Для денежных значений, дат/времени, timezone и decimal precision определяю однозначные представления. Различаю omitted field, explicit null и default, если это имеет смысл в контракте.

**Pagination, filtering и sorting.** Для небольших или изменяемых наборов offset/limit может быть приемлем, но большие смещения дороги, а concurrent inserts/deletes способны приводить к пропускам и повторам между страницами. Для больших или активно меняющихся коллекций предпочитаю cursor/keyset pagination с детерминированной сортировкой и уникальным tie-breaker, например (created_at, id). Cursor следует считать непрозрачным контрактным токеном, валидировать и при необходимости подписывать; он не должен раскрывать секреты. Ограничиваю максимальный page size, allowlist-ю поля сортировки и фильтров, валидирую комбинации и индексирую реальные query patterns. Порядок сортировки обязан быть стабильным.

**Versioning и backward compatibility.** Сначала стараюсь расширять контракт обратно совместимым способом: добавлять optional поля, новые endpoints или новые значения только после оценки поведения старых клиентов. Удаление/переименование полей, изменение типов, обязательности, значения по умолчанию или семантики существующего поля может быть breaking change. Версионирование может быть path-based, header-based или media-type-based; важнее единая политика, documented deprecation window, telemetry использования старых версий и migration plan. Не считаю добавление поля автоматически безопасным: строгие клиенты, enum parsing и generated SDK могут ломаться на неизвестных значениях или полях.

**Concurrency и conditional requests.** Для предотвращения lost updates использую optimistic concurrency control: version column, ETag/If-Match или эквивалентную проверку. Сервер сравнивает версию, которую видел клиент, с текущей и отклоняет устаревшее изменение, обычно через 412 или согласованный 409. Проверка должна быть атомарной с update, иначе остаётся race condition. Для кэширования применимы Cache-Control, ETag и Last-Modified; приватные или персональные ответы не должны случайно попадать в shared cache.

**Python/FastAPI architecture.** Router отвечает за HTTP binding, parsing, status codes и serialization. Application/use-case layer координирует сценарий и транзакционные границы; domain layer содержит бизнес-правила; repositories/adapters изолируют persistence и внешние системы. Pydantic schemas задают transport contract, но не должны автоматически становиться domain entities. Dependencies FastAPI подходят для request-scoped concerns (authenticated principal, session, services), однако скрытая магия dependency graph не должна заменять явные границы и управление жизненным циклом ресурсов. DB session и транзакции должны иметь предсказуемый scope; не держу транзакцию открытой во время медленных внешних HTTP-вызовов без веской причины.

**OpenAPI и тестирование контракта.** OpenAPI должен отражать реальные schemas, status codes, authentication, error responses, pagination и operation semantics. Проверяю generated schema в CI и не допускаю случайного breaking change без review. Тестирую не только happy path, но и authorization, validation boundaries, concurrency, idempotency, pagination stability, error shape и backward compatibility. Contract tests полезны для проверки ожиданий между producer и consumer; интеграционные тесты с реальной СУБД нужны для транзакций, constraints и конкурентного поведения. Snapshot OpenAPI сам по себе не доказывает корректность runtime.

**Надёжность и эксплуатация.** Задаю request/body/page-size limits, timeouts, rate limits и понятную retry policy. Не повторяю автоматически неидемпотентные операции без idempotency mechanism. Отделяю client errors от server errors, логирую correlation ID и метрики latency/error rate, но не записываю токены, медицинские данные или полный чувствительный payload. Для длительных задач возвращаю 202 и ресурс статуса, а не удерживаю HTTP connection неопределённо долго. API должен иметь наблюдаемое поведение при перегрузке и деградации зависимостей.

Senior-инженер должен уметь обосновать каждую гарантию: **какая семантика обещана клиенту, где она обеспечивается технически, как проверяется и что происходит при timeout, retry, race condition или частичном отказе**.

### Professional answer (EN)

A reliable API starts with **resource semantics and an explicit contract**, not with choosing a URL or a FastAPI decorator. I identify resources, permitted operations, domain invariants, access boundaries, and failure behavior. Then I define request/response schemas, HTTP semantics, compatibility rules, and verifiable guarantees.

**Resources and HTTP methods.** A URI identifies a resource or collection; the method defines the operation's semantics. GET is safe and intended for retrieval, without intentional state-changing side effects. HEAD returns metadata without a response body. POST commonly creates a subordinate resource or initiates processing. PUT replaces a resource representation and is idempotent by semantics. PATCH applies a partial modification; whether a particular patch is idempotent depends on its format and operation. DELETE is idempotent in its intended effect, although repeated responses may differ. I do not choose methods merely to mirror function names.

**Idempotency and retries.** An operation is idempotent when applying the same request repeatedly has the same intended effect as applying it once. This matters when a network failure leaves the client uncertain whether the server processed the request. For retryable commands such as creating a sale or initiating a payment, I can define an idempotency key, its uniqueness scope, retention period, response replay behavior, and concurrent-duplicate handling. Persisting the key and business operation must be transactionally coordinated; otherwise duplicates remain possible. I do not promise HTTP-level exactly-once delivery. I generally design at-least-once retries around idempotent processing and deduplication.

**Status codes and errors.** I use status codes according to their meaning: 200 for a successful representation, 201 for resource creation (often with Location), 202 for accepted asynchronous work, 204 for success without a body, 400 for a malformed request, 401 for missing or invalid authentication, 403 for a forbidden action, 404 when a resource is absent or its existence is intentionally concealed, 409 for a state conflict, 412 for a failed precondition, 422 for semantically invalid content under the API's chosen convention, 429 for rate limiting, and 5xx for server failures. I avoid returning 200 with success=false for ordinary errors. A stable error envelope should expose a machine-readable code, safe message, optional field-level details, and a correlation/request ID. It must not disclose stack traces, SQL, credentials, or sensitive data.

**Request and response contracts.** Validate input at the API boundary: types, required fields, ranges, lengths, formats, and cross-field constraints. Structural validation is not a substitute for domain validation, authorization, or database-enforced concurrency invariants. A response schema should be an explicit projection of the public contract, not an automatic dump of an ORM model; this prevents accidental exposure of internal fields and decouples the API from persistence. Define unambiguous representations for money, dates, timestamps, time zones, and decimal precision. Where relevant, distinguish an omitted field from explicit null and from a default value.

**Pagination, filtering, and sorting.** Offset/limit pagination can be adequate for small or relatively static collections. Large offsets can be expensive, and concurrent inserts or deletes may cause duplicates or omissions across pages. For large or frequently changing collections, I prefer cursor/keyset pagination with deterministic ordering and a unique tie-breaker, such as (created_at, id). Treat cursors as opaque contract tokens; validate and, where appropriate, sign them without exposing secrets. Enforce a maximum page size, allowlist sortable/filterable fields, validate combinations, and index actual query patterns. Ordering must be stable.

**Versioning and compatibility.** Prefer backward-compatible evolution where possible: add optional fields, new endpoints, or new capabilities only after considering old clients. Removing or renaming fields, changing types or requiredness, altering defaults, or changing existing field semantics can be breaking changes. Versioning may use paths, headers, or media types; consistency matters more than the mechanism. Define a deprecation window, observe old-version usage, and provide a migration plan. Adding a field is not universally safe: strict clients, enum parsing, and generated SDKs may fail on unknown fields or values.

**Concurrency and conditional requests.** Prevent lost updates with optimistic concurrency control, for example a version column or ETag/If-Match. The server compares the version observed by the client with the current version and rejects stale writes, commonly with 412 or a documented 409 convention. The comparison and update must be atomic; otherwise a race remains. For caching, use Cache-Control, ETag, and Last-Modified deliberately. Private or personalized responses must not accidentally enter a shared cache.

**Python/FastAPI architecture.** The router handles HTTP binding, parsing, status codes, and serialization. An application/use-case layer coordinates workflows and transaction boundaries; the domain layer owns business rules; repositories and adapters isolate persistence and external systems. Pydantic schemas define transport contracts but should not automatically become domain entities. FastAPI dependencies are useful for request-scoped concerns such as the authenticated principal, database session, and services, but an implicit dependency graph must not replace explicit boundaries or resource lifecycle management. Database sessions and transactions need predictable scopes; I avoid holding a transaction open across slow external HTTP calls without a strong reason.

**OpenAPI and contract testing.** OpenAPI should accurately describe schemas, status codes, authentication, error responses, pagination, and operation semantics. Validate the generated schema in CI and review accidental breaking changes. Test more than the happy path: authorization, validation boundaries, concurrency, idempotency, pagination stability, error shape, and backward compatibility. Consumer/provider contract tests verify assumptions between services; integration tests against the real database are needed for transaction, constraint, and concurrency behavior. An OpenAPI snapshot alone does not prove runtime correctness.

**Reliability and operations.** Set request/body/page-size limits, timeouts, rate limits, and a deliberate retry policy. Do not automatically retry non-idempotent operations without an idempotency mechanism. Distinguish client errors from server failures, record correlation IDs and latency/error metrics, and avoid logging tokens, medical data, or complete sensitive payloads. For long-running work, return 202 with a status resource rather than holding an HTTP connection indefinitely. The API should have observable behavior under overload and dependency degradation.

A Senior engineer should justify every guarantee: **what semantics are promised to clients, where they are enforced, how they are tested, and what happens under timeouts, retries, races, or partial failures**.

### Follow-up questions and model answers

#### FU-1 — What is the difference between safe and idempotent HTTP methods?

**RU:** Чем отличаются safe и idempotent HTTP methods?

**Answer (RU):** Safe означает, что клиент не запрашивает изменение состояния ресурса; GET и HEAD должны быть safe. Idempotent означает, что повторение одного и того же запроса имеет тот же предполагаемый эффект, что и однократное выполнение. PUT и DELETE идемпотентны, но не safe: они изменяют состояние. POST обычно не идемпотентен, хотя конкретный API может добавить idempotency key. Safe не означает отсутствие логов, метрик или иных побочных эффектов реализации — речь о семантике запрошенной операции.

**Answer (EN):** Safe means the client is not requesting a state change; GET and HEAD are expected to be safe. Idempotent means repeating the same request has the same intended effect as performing it once. PUT and DELETE are idempotent but not safe because they change state. POST is generally not idempotent, although an API can add an idempotency-key mechanism. Safe does not prohibit incidental implementation effects such as logging or metrics; it describes the requested operation's semantics.

#### FU-2 — How would you make a POST operation safe to retry after a client timeout?

**RU:** Как сделать POST-операцию безопасной для повторения после client timeout?

**Answer (RU):** Определяю idempotency key и его scope, например tenant + authenticated client + operation. На сервере атомарно резервирую ключ с уникальным ограничением, связываю его с хешем значимых параметров и результатом операции. Повтор с тем же ключом и тем же payload получает сохранённый результат; тот же ключ с другим payload отклоняется. Конкурентные запросы обрабатываются через транзакцию/уникальный constraint и определённое состояние in-progress. Устанавливаю retention policy и не полагаюсь только на Redis cache, если бизнес-эффект хранится в PostgreSQL.

**Answer (EN):** Define an idempotency key and its scope, such as tenant, authenticated client, and operation. Atomically reserve the key with a uniqueness constraint and associate it with a hash of the relevant request parameters and the operation result. A retry with the same key and payload replays the stored result; reuse with a different payload is rejected. Handle concurrent requests through a transaction/unique constraint and an explicit in-progress state. Define retention, and do not rely solely on a Redis cache when the business effect is persisted in PostgreSQL.

#### FU-3 — When would you choose cursor pagination over offset pagination?

**RU:** Когда cursor pagination предпочтительнее offset pagination?

**Answer (RU):** Cursor/keyset pagination предпочтительна для больших или часто изменяющихся коллекций, когда важны стабильное продвижение и предсказуемая стоимость запроса. Cursor должен опираться на уникальный детерминированный порядок, обычно с tie-breaker. Offset проще для произвольного перехода на страницу и небольших наборов, но большие offsets могут быть дорогими, а изменения набора между запросами приводят к пропускам или повторам. Cursor не даёт автоматически snapshot consistency: это зависит от модели данных и транзакций.

**Answer (EN):** Cursor/keyset pagination is preferable for large or frequently changing collections when stable traversal and predictable query cost matter. The cursor must use a deterministic ordering with a unique tie-breaker. Offset pagination is simpler for jumping to an arbitrary page and for small collections, but large offsets can be expensive and concurrent changes can cause omissions or duplicates. Cursor pagination does not automatically provide snapshot consistency; that depends on the data and transaction model.

#### FU-4 — How do you evolve an API without breaking existing clients?

**RU:** Как развивать API без поломки существующих клиентов?

**Answer (RU):** Сначала классифицирую изменения по совместимости и проверяю реальные consumer assumptions. Добавление optional field обычно безопаснее удаления или изменения типа, но строгие parsers и generated clients могут ломаться даже на неизвестных полях/enum values. Использую contract tests, schema diff в CI, telemetry версий и deprecation policy с migration window. Breaking change оформляю как новую версию или отдельный endpoint, документирую rollout и rollback. Не считаю OpenAPI diff единственным источником истины: важны runtime semantics и поведение клиентов.

**Answer (EN):** Classify changes by compatibility and verify actual consumer assumptions first. Adding an optional field is usually safer than removing a field or changing its type, but strict parsers and generated clients may still fail on unknown fields or enum values. Use contract tests, schema diffs in CI, version-usage telemetry, and a deprecation policy with a migration window. Introduce breaking changes through a new version or endpoint, and document rollout and rollback. An OpenAPI diff is not the only source of truth; runtime semantics and client behavior matter.

#### FU-5 — How do ETag/If-Match and database transactions help prevent lost updates?

**RU:** Как ETag/If-Match и транзакции помогают предотвращать lost updates?

**Answer (RU):** Сервер возвращает ETag, отражающий версию представления или ресурса. Клиент отправляет If-Match при изменении; сервер выполняет compare-and-update так, чтобы проверка версии и запись были атомарны. Если версия устарела, сервер не перезаписывает чужое изменение и возвращает 412 Precondition Failed либо документированный конфликтный код. Реализация может использовать SQL UPDATE ... WHERE id = ? AND version = ?, затем проверять affected rows. Простая проверка версии отдельным SELECT перед UPDATE без атомарной защиты подвержена race condition.

**Answer (EN):** The server returns an ETag representing a resource or representation version. The client sends If-Match on modification; the server performs an atomic compare-and-update. If the version is stale, it does not overwrite another client's change and returns 412 Precondition Failed or a documented conflict response. One implementation is an UPDATE ... WHERE id = ? AND version = ? followed by checking the affected-row count. A separate version SELECT followed by an unguarded UPDATE is vulnerable to a race condition.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a pharmacy API might expose medicine catalog search, inventory adjustments, sales, and prescription-related workflows. The candidate should explain stable pagination for catalog results, explicit response DTOs that do not leak internal or patient fields, object-level authorization for tenant-scoped resources, idempotency for retryable sale commands, and optimistic concurrency for stock updates. Any claim that these controls exist in Pharmaviyum must be verified against source code and tests before being described as implemented.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Mid-level | Uses appropriate methods and status codes, validates requests, defines schemas, and implements basic pagination and error handling. |
| Senior | Reasons about safe/idempotent semantics, retry ambiguity, atomic idempotency, cursor stability, conditional updates, compatibility, transaction boundaries, and contract testing. |
| Staff-level signal | Establishes API governance, version/deprecation policy, cross-service contract strategy, reliability SLOs, and migration practices across teams. |

### Common pitfalls

- Treating REST as merely pluralized CRUD routes.
- Using GET for state-changing operations or assuming every POST is safely retryable.
- Claiming exactly-once processing without defining transactional deduplication.
- Returning 200 for all outcomes or exposing internal exception details.
- Serializing ORM models directly as public response contracts.
- Allowing unbounded page sizes, arbitrary sort fields, or unstable pagination order.
- Assuming cursor pagination automatically provides snapshot consistency.
- Making breaking schema changes without observing consumer behavior.
- Checking a version in a separate query and then updating without atomic concurrency control.
- Holding database transactions open during slow external calls.
- Treating generated OpenAPI or schema snapshots as proof of runtime correctness.
- Logging sensitive request/response payloads while adding observability.

### References

- RFC 9110 — HTTP Semantics: https://www.rfc-editor.org/rfc/rfc9110
- RFC 9111 — HTTP Caching: https://www.rfc-editor.org/rfc/rfc9111
- RFC 9457 — Problem Details for HTTP APIs: https://www.rfc-editor.org/rfc/rfc9457
- RFC 6585 — Additional HTTP Status Codes (including 429): https://www.rfc-editor.org/rfc/rfc6585
- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- FastAPI documentation: https://fastapi.tiangolo.com/
- Pydantic documentation: https://docs.pydantic.dev/
- Microsoft REST API Guidelines: https://github.com/microsoft/api-guidelines


## PY-CORE-028 — Python Backend Architecture, Clean Architecture and Dependency Injection

**Question (EN):** How do you structure a maintainable Python backend using architectural boundaries and dependency injection, and how do you avoid both tight coupling and unnecessary abstraction?

**Вопрос (RU):** Как построить поддерживаемый Python backend с помощью архитектурных границ и dependency injection, избегая как сильной связанности, так и ненужных абстракций?

### What the interviewer evaluates

- Separation of concerns, dependency direction, and architectural boundaries.
- Domain, application/use-case, infrastructure, and delivery layers.
- Dependency injection, composition roots, and lifecycle scopes.
- Ports/adapters, Protocols, ABCs, and testing seams.
- Transaction ownership, resource lifecycle, and error propagation.
- Prevention of circular dependencies, Service Locator misuse, and overengineering.
- Pragmatic architecture decisions tied to actual change patterns and system complexity.

### Эталонный ответ (RU)

Я начинаю не с названия архитектурного паттерна, а с **границ ответственности, направления зависимостей и ожидаемых изменений системы**. Цель архитектуры — локализовать изменения, сделать бизнес-правила понятными и обеспечить проверяемость поведения. Clean Architecture, Hexagonal Architecture и layered architecture — полезные модели, но не обязательный набор каталогов или интерфейсов для каждого проекта.

**Разделение слоёв.** Delivery layer (HTTP routers, CLI, consumers) преобразует внешний протокол в вызов application use case и обратно. Application layer координирует сценарий: загружает данные через порты, вызывает доменную логику, управляет последовательностью действий и транзакционной границей. Domain layer содержит бизнес-понятия, правила и инварианты и не должен зависеть от FastAPI, SQLAlchemy, Redis или конкретного HTTP клиента. Infrastructure layer реализует порты: repositories, message publishers, external API clients, clocks и storage adapters. Границы нужны для изоляции причин изменения, а не ради механического разделения каждого класса.

**Dependency Rule.** В Clean/Hexagonal подходах зависимости исходного кода направляются внутрь: внешние детали зависят от внутренних политик, а не наоборот. Например, use case может зависеть от абстракции repository, а SQLAlchemy adapter реализует её. В Python это можно выразить через typing.Protocol (structural typing) или abc.ABC (nominal contract). Не требуется создавать интерфейс для каждой функции: абстракция оправдана, когда она выражает стабильную границу, несколько реализаций, тестовую замену или независимость домена от инфраструктуры.

**Dependency Injection и Composition Root.** Dependency injection означает, что компонент получает зависимости извне, а не создаёт их самостоятельно и не ищет глобально. Composition root — контролируемое место, где приложение собирает конкретный object graph: конфигурацию, DB engine, session factory, repositories, services и transport adapters. В небольшом FastAPI приложении это может быть app factory и lifespan setup; request-scoped зависимости могут передаваться через FastAPI Depends. Важно, чтобы сборка была явной, предсказуемой и проверяемой. Dependency injection — принцип, а FastAPI Depends — один из механизмов, не вся архитектура.

**Scopes и lifecycle.** Различаю application-scoped ресурсы (например, connection pool или HTTP client), request-scoped ресурсы (например, DB session) и transient/stateless компоненты. Engine и connection pool обычно создаются один раз на процесс и корректно закрываются при shutdown; session создаётся в подходящем request/use-case scope и закрывается после него. Нельзя случайно делить одну SQLAlchemy Session между конкурентными запросами или задачами: Session не является универсально thread-safe/async-task-safe объектом. Не создаю тяжёлые клиенты на каждый запрос без необходимости и не оставляю фоновые задачи с зависимостями, чей scope уже завершился.

**Транзакции и application use cases.** Транзакционная граница должна соответствовать бизнес-операции и быть видимой. Часто application service начинает транзакцию, вызывает repositories и фиксирует commit/rollback в одном месте; repositories отвечают за persistence operations, но не должны незаметно коммитить каждое изменение отдельно. Точная модель зависит от unit of work и выбранной ORM. Внешние сетевые вызовы не следует без необходимости выполнять внутри долгой DB transaction: это увеличивает lock duration и риск contention. Для согласования DB и message broker рассматриваю outbox/inbox или другие consistency patterns, а не предполагаю общую атомарную транзакцию между независимыми системами.

**Ports and Adapters.** Порт описывает нужную внутренней политике возможность, например MedicineRepository, Clock или NotificationGateway; адаптер реализует её для PostgreSQL, системного времени или конкретного провайдера. Это облегчает замену инфраструктуры и тестирование, но не означает, что всё нужно скрывать за generic repository. ORM уже предоставляет unit-of-work и query capabilities; дополнительная абстракция может ухудшить выразительность сложных запросов. Проектирую узкие порты вокруг use-case needs, а не копирую весь API ORM.

**Тестируемость.** Domain logic тестирую без сети и базы, application use cases — с fake/mock ports и отдельными интеграционными тестами adapters. Контрактные тесты проверяют, что реальные adapters соблюдают портовые ожидания. Для критичных транзакций, SQL semantics, constraints и locking нужны integration tests с реальной СУБД. Не подменяю все зависимости mocks: тест, в котором каждый компонент замокан, может подтвердить только внутренние ожидания самого теста. Тесты должны проверять поведение и бизнес-инварианты, а не только вызов методов.

**FastAPI и границы приложения.** Router должен быть тонким: HTTP parsing, authentication context, вызов use case, response mapping. Он не должен содержать длинные бизнес-сценарии и прямую orchestration нескольких таблиц. Pydantic request/response models — транспортные схемы; domain entities и persistence models могут иметь другие формы и lifecycle. Depends хорошо подходит для сборки request context и передачи зависимостей, но глобальный mutable state и скрытый Service Locator затрудняют reasoning. Lifespan управляет application resources; request dependencies управляют request-level resources.

**Конфигурация, ошибки и наблюдаемость.** Конфигурацию валидирую на старте и передаю в компоненты явно; не читаю произвольные environment variables из бизнес-логики. Ошибки переводятся на правильной границе: domain/application errors отображаются в transport-level responses, а infrastructure failures логируются с контекстом и обрабатываются согласно retry/transaction policy. Correlation context и tracing проходят через границы без передачи глобального изменяемого состояния. Чувствительные данные и секреты не должны попадать в логи.

**Как не переусложнить.** Не создаю десятки слоёв, generic base repositories, абстрактные фабрики и интерфейсы без конкретной причины. Для CRUD-oriented сервиса может быть достаточно модульного layered design. Для домена со сложными инвариантами полезно более явное разделение domain/application. Критерий — не число паттернов, а локализация изменений, понятность transaction boundaries, возможность тестировать важные правила и отсутствие инфраструктурных деталей в домене.

Senior-инженер должен уметь нарисовать dependency graph, назвать composition root, объяснить lifecycle каждого ресурса и показать, где проходит транзакционная граница. Также он должен обосновать, почему конкретная абстракция существует — и почему другая не нужна.

### Professional answer (EN)

I start with **responsibility boundaries, dependency direction, and expected change patterns**, not with the name of an architectural style. The goal is to localize change, make business rules explicit, and keep behavior verifiable. Clean Architecture, Hexagonal Architecture, and layered architecture are useful models, not mandatory directory structures or a requirement to introduce an interface for every class.

**Layer responsibilities.** The delivery layer (HTTP routers, CLI handlers, message consumers) translates an external protocol into an application use-case call and maps the result back. The application layer coordinates a workflow: it obtains data through ports, invokes domain behavior, orders operations, and owns or coordinates the transaction boundary. The domain layer contains business concepts, rules, and invariants; it should not depend on FastAPI, SQLAlchemy, Redis, or a particular HTTP client. The infrastructure layer implements ports through repositories, message publishers, external API clients, clocks, and storage adapters. These boundaries isolate reasons for change; they are not a reason to split every class mechanically.

**Dependency Rule.** In Clean/Hexagonal approaches, source-code dependencies point inward: external details depend on internal policies, not the reverse. A use case may depend on a repository abstraction while a SQLAlchemy adapter implements it. Python can express contracts with typing.Protocol (structural typing) or abc.ABC (nominal contracts). An interface is not needed for every function. It is justified when it represents a stable boundary, multiple implementations, a meaningful testing seam, or domain independence from infrastructure.

**Dependency Injection and the Composition Root.** Dependency injection means a component receives dependencies from outside instead of constructing them internally or locating them globally. The composition root is the controlled place where the application assembles its concrete object graph: configuration, DB engine, session factory, repositories, services, and delivery adapters. In a small FastAPI application, this may be an app factory plus lifespan setup; request-scoped dependencies can be supplied through FastAPI Depends. Assembly should be explicit, predictable, and testable. Dependency injection is a principle; FastAPI Depends is one mechanism, not the architecture itself.

**Scopes and lifecycle.** Distinguish application-scoped resources (for example, a connection pool or HTTP client), request-scoped resources (for example, a DB session), and transient/stateless components. An engine and connection pool are generally created once per process and closed during shutdown; a session is created within an appropriate request/use-case scope and closed afterward. Do not share one SQLAlchemy Session across concurrent requests or tasks: a Session is not a universally thread-safe or async-task-safe object. Avoid constructing expensive clients on every request without reason, and do not let background tasks retain dependencies whose scope has ended.

**Transactions and application use cases.** A transaction boundary should correspond to a business operation and be visible. Often an application service starts a transaction, invokes repositories, and coordinates commit/rollback in one place; repositories perform persistence operations rather than silently committing each change. The exact model depends on the unit-of-work design and ORM. Avoid slow external network calls inside long-running database transactions unless there is a compelling reason, because they increase lock duration and contention risk. To coordinate a database write with message publication, consider an outbox/inbox or another explicit consistency pattern; do not assume independent systems share an atomic transaction.

**Ports and Adapters.** A port describes a capability required by an inner policy, such as MedicineRepository, Clock, or NotificationGateway; an adapter implements it for PostgreSQL, system time, or a specific provider. This supports infrastructure replacement and testing, but does not mean every operation should be hidden behind a generic repository. An ORM already provides unit-of-work and query capabilities; an extra abstraction can reduce the expressiveness of complex queries. Design narrow ports around use-case needs instead of mirroring the entire ORM API.

**Testability.** Test domain logic without network or database dependencies, application use cases with fake/mock ports, and adapters with integration tests. Contract tests verify that real adapters satisfy their port expectations. Critical transactions, SQL semantics, constraints, and locking require integration tests against the real database. Do not mock every dependency: a test in which every component is mocked may only confirm the test's own assumptions. Tests should verify behavior and business invariants, not merely method calls.

**FastAPI and application boundaries.** Keep routers thin: HTTP parsing, authentication context, use-case invocation, and response mapping. They should not contain long business workflows or orchestrate multiple tables directly. Pydantic request/response models are transport schemas; domain entities and persistence models may have different shapes and lifecycles. Depends is useful for assembling request context and supplying dependencies, but global mutable state and a hidden Service Locator make reasoning harder. Lifespan manages application resources; request dependencies manage request-level resources.

**Configuration, errors, and observability.** Validate configuration at startup and pass it explicitly to components; do not read arbitrary environment variables from domain logic. Translate errors at the correct boundary: domain/application errors map to transport responses, while infrastructure failures are logged with context and handled according to retry and transaction policy. Correlation context and tracing should cross boundaries without relying on global mutable state. Secrets and sensitive data must not enter logs.

**Avoiding overengineering.** Do not introduce dozens of layers, generic base repositories, abstract factories, and interfaces without a concrete reason. A CRUD-oriented service may need only a modular layered design. A domain with complex invariants may benefit from explicit domain/application separation. The measure is not the number of patterns; it is change isolation, clear transaction boundaries, testability of important rules, and keeping infrastructure details out of the domain.

A Senior engineer should be able to draw the dependency graph, identify the composition root, explain each resource's lifecycle, and locate the transaction boundary. They should also justify why each abstraction exists—and why another one is unnecessary.

### Follow-up questions and model answers

#### FU-1 — What is the Dependency Rule in Clean Architecture, and how can Python enforce it?

**RU:** Что означает Dependency Rule в Clean Architecture и как его можно обеспечить в Python?

**Answer (RU):** Внутренние policy/domain layers не должны импортировать внешние infrastructure или framework modules. Внешний adapter реализует контракт, определённый ближе к внутреннему слою. В Python это можно поддержать структурой пакетов, Protocol или ABC, dependency direction checks и code review. Type hints сами по себе не гарантируют архитектурную границу: модуль всё ещё может импортировать infrastructure напрямую. Нужны явные правила импортов и тесты/линтеры архитектуры, если риск оправдывает их стоимость.

**Answer (EN):** Inner policy/domain layers should not import outer infrastructure or framework modules. An outer adapter implements a contract defined closer to the inner layer. In Python, package structure, Protocol or ABC, dependency-direction checks, and code review can support this. Type hints alone do not enforce the boundary: a module can still import infrastructure directly. Use explicit import rules and architecture tests or linters when the risk justifies their cost.

#### FU-2 — What is a composition root, and how is it different from a Service Locator?

**RU:** Что такое composition root и чем он отличается от Service Locator?

**Answer (RU):** Composition root — ограниченное место, где приложение создаёт и связывает concrete implementations в object graph. После сборки компоненты получают нужные зависимости явно. Service Locator предоставляет глобальный или скрытый API, через который компонент самостоятельно запрашивает зависимости во время работы. Это скрывает реальные зависимости, затрудняет тестирование и может создавать runtime failures. Composition root централизует wiring; Service Locator переносит поиск зависимостей внутрь потребителей.

**Answer (EN):** A composition root is a constrained place where the application creates and wires concrete implementations into an object graph. Components then receive their dependencies explicitly. A Service Locator exposes a global or hidden API through which a component looks up dependencies at runtime. This hides real dependencies, complicates testing, and can defer failures until runtime. The composition root centralizes wiring; a Service Locator moves dependency lookup into consumers.

#### FU-3 — How would you manage SQLAlchemy engine and session lifecycles in a FastAPI application?

**RU:** Как управлять lifecycle SQLAlchemy engine и session в FastAPI application?

**Answer (RU):** Engine и connection pool обычно создаются на уровне application/process и закрываются в lifespan shutdown. Session factory создаётся из engine; отдельная Session выдаётся на подходящий request/use-case scope и гарантированно закрывается после завершения. Для async stack применяю соответствующие AsyncEngine/AsyncSession и async lifecycle. Session не разделяется между параллельными requests/tasks. Commit/rollback выполняются в ясно определённой транзакционной границе, а не случайно в нескольких слоях одновременно.

**Answer (EN):** The engine and connection pool are generally created at application/process scope and disposed during lifespan shutdown. A session factory is created from the engine; an individual Session is provided for an appropriate request/use-case scope and reliably closed afterward. For an async stack, use the corresponding AsyncEngine/AsyncSession and async lifecycle. Do not share a Session across concurrent requests or tasks. Commit/rollback belongs to a clearly defined transaction boundary rather than being scattered unpredictably across layers.

#### FU-4 — When is a repository abstraction useful, and when does it become harmful?

**RU:** Когда repository abstraction полезна, а когда начинает вредить?

**Answer (RU):** Она полезна, если выражает понятный domain/application port, изолирует инфраструктуру, поддерживает несколько adapters или делает use case тестируемым. Она вредна, если превращается в generic CRUD wrapper над ORM, скрывает важные query capabilities, дублирует unit-of-work или создаёт много boilerplate без реальной вариативности. Решение принимаю по изменчивости границы и сложности предметной области, а не по правилу «repository обязателен для каждого проекта».

**Answer (EN):** It is useful when it expresses a meaningful domain/application port, isolates infrastructure, supports multiple adapters, or makes a use case testable. It becomes harmful when it is merely a generic CRUD wrapper over an ORM, hides important query capabilities, duplicates the unit of work, or adds boilerplate without real variability. Decide based on boundary volatility and domain complexity, not on a rule that every project must have a repository.

#### FU-5 — How do you keep a database transaction consistent with publishing an event to a message broker?

**RU:** Как согласовать database transaction с публикацией event в message broker?

**Answer (RU):** Нельзя предполагать атомарность между независимыми PostgreSQL и broker transactions. Если сначала commit DB, а затем publish, процесс может упасть между шагами; если сначала publish, а затем commit, consumer может увидеть событие о незафиксированном изменении. Transactional outbox записывает бизнес-изменение и event record в одной DB transaction; отдельный publisher доставляет outbox events с retry. Consumer использует idempotency/inbox deduplication, потому что доставка обычно at-least-once. Нужно также определить мониторинг backlog, retry limits и dead-letter/recovery policy.

**Answer (EN):** Do not assume atomicity across independent PostgreSQL and broker transactions. If the database commits before publishing, the process may fail between the steps; if it publishes first, a consumer may observe an event for a change that never committed. A transactional outbox stores the business change and event record in one database transaction; a separate publisher delivers outbox events with retries. Consumers use idempotency or inbox deduplication because delivery is generally at least once. Define backlog monitoring, retry limits, and dead-letter/recovery policy as well.

### Pharmaviyum connection

**Hypothetical interview scenario — not a claim about the current implementation:** a pharmacy backend could separate HTTP delivery, application workflows for sales and inventory, domain rules for stock invariants, and infrastructure adapters for PostgreSQL, Redis, and external AI services. A candidate should describe which layer owns a stock-adjustment transaction, how a request-scoped database session is provided, how external AI calls are isolated from database transactions, and how events are published reliably. Actual architecture and implementation status must be verified from repository code, tests, and deployment evidence.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Mid-level | Separates routing from business logic, injects basic dependencies, and understands module responsibilities. |
| Senior | Explains dependency direction, composition root, resource scopes, transaction ownership, ports/adapters, and testing boundaries; avoids hidden global lookup and unnecessary abstractions. |
| Staff-level signal | Defines architecture standards across teams, migration paths, cross-service boundaries, consistency patterns, and governance while keeping the design proportional to system needs. |

### Common pitfalls

- Treating Clean Architecture as a mandatory folder template.
- Allowing domain modules to import FastAPI, ORM, or vendor SDK types directly.
- Confusing dependency injection with a framework-specific Depends call.
- Using a global Service Locator or mutable singleton for hidden dependencies.
- Sharing one SQLAlchemy Session across concurrent requests or tasks.
- Creating engines, pools, or expensive clients repeatedly without lifecycle control.
- Allowing repositories to commit independently and fragment a business transaction.
- Holding database transactions open across slow external calls.
- Assuming a database write and broker publish are one atomic operation.
- Mocking every dependency and never testing adapters against real infrastructure.
- Building generic repositories and interfaces that obscure rather than clarify behavior.
- Claiming that type hints alone enforce architectural boundaries.

### References

- Python typing — Protocol: https://docs.python.org/3/library/typing.html#typing.Protocol
- Python abc module: https://docs.python.org/3/library/abc.html
- FastAPI Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- FastAPI Lifespan Events: https://fastapi.tiangolo.com/advanced/events/
- SQLAlchemy Session Basics: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- SQLAlchemy asyncio: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Martin Fowler — Dependency Injection: https://martinfowler.com/articles/injection.html
- Microsoft — Transactional Outbox pattern: https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-outbox

 
## PY-CORE-029 — Python Performance Engineering, Profiling, Optimization and Scalability

> **Scope boundary:** This question owns end-to-end service performance engineering: workload models, latency distributions, throughput, load tests, saturation, capacity, scaling, caching strategy, and regression controls. Use Q13 for object-lifecycle/GC mechanics and Q14 for local Python profiling tools; do not repeat their foundational explanations.
>
> **Граница темы:** вопрос отвечает за end-to-end performance engineering сервиса: workload, latency distributions, throughput, load tests, saturation, capacity, scaling, caching strategy и контроль регрессий. Механику жизненного цикла объектов и GC см. в Q13, локальное профилирование Python — в Q14; не повторяйте их базовые объяснения.

### What the interviewer evaluates

Whether the candidate can approach performance as an evidence-driven engineering discipline rather than a collection of micro-optimizations. A Senior engineer should define measurable service-level objectives, establish representative workloads, distinguish CPU, memory, I/O, database, network, queueing, and contention bottlenecks, select appropriate profiling and load-testing tools, interpret latency distributions, and validate that a change improves the target outcome without weakening correctness, reliability, or maintainability.

This question deliberately extends the earlier Python optimization and profiling fundamentals (PY-CORE-014) into end-to-end backend performance engineering: workload characterization, measurement design, service-level indicators, scalability limits, regression control, and operational trade-offs.

### Эталонный ответ (RU)

Производительность backend-системы я рассматриваю как измеряемое свойство всей системы, а не только скорость отдельной функции Python. Сначала определяю пользовательский сценарий и целевую характеристику: например, p95 latency для критичного API, throughput при заданной конкурентности, допустимую долю ошибок и потребление ресурсов. Затем фиксирую базовую линию на репрезентативной нагрузке и только после этого выбираю оптимизацию.

Первый шаг — классифицировать workload и найти узкое место. CPU-bound задача тратит значительную часть времени на вычисления; I/O-bound — ожидает базу данных, сеть, файловую систему или другой сервис. В реальном backend часто встречается смешанный профиль: медленный SQL-запрос, блокирующий вызов внутри async endpoint, нехватка соединений в pool, сериализация больших объектов, lock contention, чрезмерное число запросов или очередь фоновых задач. Нельзя выбирать asyncio, multiprocessing или кэширование только по общему ощущению медленной работы — сначала нужны измерения.

Для CPU profiling в Python подходят cProfile и sampling-профайлеры, например py-spy. Они помогают понять, где расходуется CPU и какие вызовы доминируют. Для памяти применяю tracemalloc, сравнение snapshots и, при необходимости, специализированные memory profilers. Tracemalloc отслеживает Python allocations, но не обязан объяснять весь RSS процесса: память native extensions, allocator arenas и поведение ОС могут отличаться. Поэтому сопоставляю Python-level данные с RSS/container metrics и профилем нагрузки. Рост RSS сам по себе ещё не доказывает memory leak: allocator может удерживать освобождённую память для повторного использования.

Для backend отдельно исследую внешние зависимости. Проверяю планы выполнения SQL через EXPLAIN (ANALYZE, BUFFERS) на безопасной и репрезентативной среде, индексы, селективность, N+1, объём возвращаемых строк, pagination, транзакции и connection-pool saturation. Измеряю сетевые вызовы, таймауты, retries и fan-out. Для async-приложения ищу блокирующий I/O в event loop, долгие участки CPU, неограниченное создание tasks и отсутствие backpressure. Асинхронность повышает эффективность ожидания I/O, но не ускоряет CPU-bound код автоматически.

Измерения должны включать не только среднее значение. Анализирую p50, p95, p99 latency, throughput, error rate, saturation и распределение по endpoint/операции. Среднее скрывает длинный хвост. При росте concurrency задержки могут резко увеличиваться из-за очередей, lock contention, исчерпания DB pool или downstream capacity. Поэтому load test должен отражать реалистичные данные, mix запросов, прогрев, concurrency, ramp-up, длительность и поведение зависимостей. Отдельно учитываю coordinated omission и влияние самого генератора нагрузки: если load generator не способен выдавать запланированный поток запросов, результат вводит в заблуждение.

Оптимизацию выполняю по циклу: сформулировать гипотезу → определить метрику и контрольные условия → измерить baseline → изменить один существенный фактор → повторить benchmark/load test → проверить корректность и побочные эффекты → сохранить результат. Микробенчмарки полезны для изолированных участков, но не заменяют end-to-end измерения. Сравнение требует одинаковых условий, достаточного числа повторов, контроля шума, прогрева и стабильной среды. Benchmark должен измерять именно интересующую операцию, а не случайные затраты setup/teardown.

Кэширование оправдано, когда повторное вычисление или чтение действительно дорого, данные допускают определённую свежесть, а cache hit rate и стоимость invalidation измеримы. Нужно определить ключи, TTL, границы tenant/user, поведение при cache miss, stampede protection, eviction и отказ кэша. Кэш может скрыть проблему источника данных, создать stale reads или привести к утечке данных между пользователями при неверном ключе. Он не является универсальным решением.

Масштабирование бывает vertical и horizontal. Увеличение числа workers/replicas помогает только до ограничения общего ресурса: базы данных, connection pool, внешнего API, очереди, CPU или сетевого канала. Нужно оценивать capacity каждого критического звена, а не только web workers. Для stateful компонентов важны shared state, idempotency, distributed coordination и graceful degradation. Увеличение concurrency без контроля может ухудшить tail latency и усилить перегрузку.

Для предотвращения регрессий использую performance budgets, стабильные benchmark suites, нагрузочные тесты для критичных сценариев и мониторинг production SLI/SLO. В CI микробенчмарки могут быть шумными, поэтому пороги и окружение должны быть обоснованы; более тяжёлые load tests можно запускать отдельно или перед релизом. В production отслеживаю latency distributions, throughput, errors, saturation, queue depth, DB pool utilization и downstream timings с безопасной корреляцией trace/log/metric. Любая оптимизация должна сохранять функциональную корректность, безопасность, изоляцию данных и предсказуемость отказов.

Senior-level подход — не «сделать быстрее любой ценой», а определить, какая задержка важна пользователю, доказать источник проблемы, выбрать минимально сложное изменение, количественно подтвердить эффект и зафиксировать trade-offs. Если система уже удовлетворяет требованиям, дополнительная сложность может быть хуже небольшой экономии времени.

### Professional answer (EN)

I treat backend performance as an end-to-end, measurable system property—not merely the execution speed of an individual Python function. I first define the user-visible workload and target: for example, p95 latency for a critical API, throughput at a specified concurrency, an acceptable error rate, and resource limits. I establish a baseline under representative conditions before changing the implementation.

The first task is bottleneck classification. CPU-bound work spends most of its time executing instructions; I/O-bound work waits for a database, network, filesystem, or another service. Real services often have mixed bottlenecks: inefficient SQL, blocking calls inside async endpoints, connection-pool exhaustion, expensive serialization, lock contention, excessive query counts, or overloaded background queues. I do not choose asyncio, multiprocessing, or caching based on intuition; I gather evidence first.

For Python CPU profiling, cProfile and sampling profilers such as py-spy help identify expensive call paths. For memory investigations, I use tracemalloc snapshots and, where appropriate, dedicated memory profilers. Tracemalloc observes Python allocations but does not necessarily explain total process RSS: native extensions, allocator arenas, and operating-system behavior may contribute. I correlate Python-level findings with process/container metrics. An increase in RSS alone does not prove a leak because an allocator may retain freed memory for reuse.

I profile external dependencies separately. For PostgreSQL, I inspect query plans with EXPLAIN (ANALYZE, BUFFERS) in a safe representative environment, along with indexes, selectivity, N+1 queries, result size, pagination, transaction duration, and connection-pool saturation. I measure network calls, timeouts, retries, and fan-out. In async services, I look for blocking I/O on the event loop, long CPU sections, unbounded task creation, and missing backpressure. Async improves I/O concurrency; it does not automatically accelerate CPU-bound work.

Measurements must go beyond averages. I examine p50, p95, and p99 latency, throughput, error rate, saturation, and per-operation distributions. Averages hide tail behavior. As concurrency rises, queueing, lock contention, exhausted database pools, or downstream capacity can cause latency to increase sharply. A load test should use realistic data and request mix, warm-up, concurrency, ramp-up, duration, and dependency behavior. I also account for coordinated omission and load-generator limitations: a generator that cannot sustain the intended arrival rate can produce misleading results.

I optimize through a controlled loop: state a hypothesis, define the metric and controls, measure the baseline, change one material factor, rerun the benchmark or load test, verify correctness and side effects, and record the result. Microbenchmarks are useful for isolated code paths but do not replace end-to-end measurements. Comparisons require consistent conditions, repeated runs, noise control, warm-up, and a stable environment. The benchmark must measure the operation of interest rather than accidental setup or teardown work.

Caching is appropriate when repeated computation or reads are demonstrably expensive, the data has an acceptable freshness model, and hit rate and invalidation costs can be measured. I define keys, TTL, tenant/user boundaries, cache-miss behavior, stampede protection, eviction, and failure behavior. A cache can conceal source-system problems, introduce stale reads, or leak data across users when keys are incorrectly scoped. It is not a universal optimization.

Scaling can be vertical or horizontal. More workers or replicas help only until a shared resource becomes the limit: the database, connection pool, external API, queue, CPU, or network. I assess the capacity of every critical tier rather than only the web tier. Stateful components require deliberate shared-state handling, idempotency, distributed coordination, and graceful degradation. Increasing concurrency without admission control can worsen tail latency and amplify overload.

To prevent regressions, I use performance budgets, stable benchmark suites, load tests for critical scenarios, and production SLI/SLO monitoring. CI microbenchmarks can be noisy, so thresholds and environments must be justified; heavier load tests may run separately or before release. In production I monitor latency distributions, throughput, errors, saturation, queue depth, database-pool utilization, and downstream timings, with safe correlation across traces, logs, and metrics. Every optimization must preserve functional correctness, security, data isolation, and predictable failure behavior.

A Senior-level approach is not to make everything faster at any cost. It is to identify the latency that matters to users, prove the bottleneck, choose the least complex effective change, quantify its impact, and document the trade-offs. If the system already meets its requirements, added complexity may be worse than a marginal speed improvement.

### Follow-up questions and model answers

**FU-1. How would you investigate an API whose p95 latency increased while its average latency remained almost unchanged?**

- **RU — Вопрос:** Как расследовать ситуацию, когда p95 latency API выросла, а средняя задержка почти не изменилась?
- **Answer (RU):** Сначала проверю распределение latency по endpoint, версии приложения, региону, tenant и типу запроса, а также сравню p50, p90, p95 и p99 до и после изменения. Рост только хвоста часто указывает на небольшую долю медленных запросов: lock contention, очереди, редкие медленные SQL-планы, cache misses, retries, downstream timeouts или нехватку соединений. Затем сопоставлю traces и метрики отдельных этапов запроса, проверю deployment/configuration changes и нагрузочный профиль. Не буду оптимизировать средний путь, пока не локализую источник tail latency. После исправления повторю нагрузочный тест и проверю, что улучшились нужные percentiles без роста ошибок.
- **Answer (EN):** I would compare latency distributions by endpoint, application version, region, tenant, and request class, including p50, p90, p95, and p99 before and after the change. A tail-only regression often points to a minority of slow requests: lock contention, queueing, occasional slow query plans, cache misses, retries, downstream timeouts, or connection scarcity. I would correlate traces with per-stage metrics, inspect deployment and configuration changes, and verify the workload profile. I would not optimize the average path until the tail-latency source is identified. After the fix, I would rerun a representative load test and confirm that the target percentiles improve without increasing errors.

**FU-2. What is the difference between CPU profiling, memory profiling, and distributed tracing, and when would you use each?**

- **RU — Вопрос:** Чем отличаются CPU profiling, memory profiling и distributed tracing и когда применять каждый инструмент?
- **Answer (RU):** CPU profiling показывает, какие функции и call paths потребляют процессорное время; использую его при высокой CPU utilization или подозрении на дорогие вычисления. Memory profiling помогает понять allocation patterns, удержание объектов и возможный рост Python heap; сопоставляю snapshots и учитываю, что tracemalloc не покрывает всю native memory и RSS. Distributed tracing показывает путь запроса через процессы и внешние зависимости, включая длительность spans и межсервисные задержки; применяю его, когда проблема может находиться в БД, сети или downstream service. Эти инструменты дополняют друг друга: trace локализует медленный компонент, profiler объясняет его внутреннюю стоимость.
- **Answer (EN):** CPU profiling identifies functions and call paths consuming processor time; I use it when CPU utilization is high or computation appears expensive. Memory profiling helps explain allocation patterns, retained objects, and possible Python-heap growth; I compare snapshots while remembering that tracemalloc does not cover all native memory or total RSS. Distributed tracing follows a request across processes and dependencies, exposing span durations and cross-service delays; I use it when the database, network, or a downstream service may be responsible. The tools complement one another: tracing locates the slow component, while a profiler explains its internal cost.

**FU-3. Why can adding more workers or async concurrency make a service slower?**

- **RU — Вопрос:** Почему увеличение числа workers или async concurrency может замедлить сервис?
- **Answer (RU):** Конкурентность увеличивает давление на общие ресурсы. Дополнительные workers могут исчерпать DB connection pool, увеличить число конкурирующих SQL-запросов, усилить lock contention, context switching и memory pressure. В async-сервисе создание неограниченного числа tasks может породить очереди и нагрузить downstream dependencies. Когда arrival rate превышает capacity самого медленного звена, растёт queueing delay и tail latency. Решение — измерить saturation, ввести bounded concurrency, backpressure, admission control и разумные pool limits, а затем подобрать concurrency экспериментально. Больше workers не означает автоматически больше throughput.
- **Answer (EN):** More concurrency increases pressure on shared resources. Additional workers can exhaust the database connection pool, increase competing SQL queries, and amplify lock contention, context switching, and memory pressure. In an async service, unbounded task creation can create queues and overload downstream dependencies. When the arrival rate exceeds the capacity of the slowest tier, queueing delay and tail latency rise. I would measure saturation, introduce bounded concurrency, backpressure, admission control, and appropriate pool limits, then tune concurrency experimentally. More workers do not automatically mean more throughput.

**FU-4. How would you design a reliable performance benchmark and prevent misleading conclusions?**

- **RU — Вопрос:** Как спроектировать надёжный performance benchmark и избежать ошибочных выводов?
- **Answer (RU):** Определю измеряемую операцию, реалистичный dataset и профиль нагрузки, зафиксирую версию кода, конфигурацию, hardware/container limits и состояние зависимостей. Разделю setup, warm-up и измеряемую фазу; выполню несколько повторов и буду сравнивать распределения, а не одно число. Проверю, что load generator способен поддерживать целевую интенсивность и не создаёт coordinated omission. Изолирую шумные фоновые процессы, контролирую cache state и не сравниваю результаты из существенно разных сред без нормализации. Для regression gate использую устойчивые пороги и достаточный объём наблюдений; микробенчмарк подтверждаю интеграционным или нагрузочным измерением.
- **Answer (EN):** I would define the operation, representative dataset, and workload profile, then record the code version, configuration, hardware or container limits, and dependency state. I would separate setup, warm-up, and measurement phases, run repeated trials, and compare distributions rather than a single number. I would verify that the load generator can sustain the target arrival rate and does not introduce coordinated omission. I would control background noise and cache state, and avoid comparing materially different environments without normalization. Regression gates need stable thresholds and sufficient observations; I would validate microbenchmark findings with integration or load measurements.

**FU-5. When is caching an unsafe or ineffective performance optimization in a multi-tenant backend?**

- **RU — Вопрос:** Когда кэширование является небезопасной или неэффективной оптимизацией в multi-tenant backend?
- **Answer (RU):** Кэш может быть небезопасен, если ключ не включает tenant/user scope или authorization context: тогда возможна выдача данных другому клиенту. Он неэффективен, если низкий hit rate, высокая стоимость invalidation, данные быстро меняются или cache lookup дороже исходной операции. Нужно определить freshness contract, TTL, invalidation strategy, защиту от stampede, ограничение размера и поведение при отказе. Для чувствительных данных кэширование требует явного threat model и тестов изоляции. Я измеряю hit/miss ratio, latency, memory footprint и влияние на источник данных; не считаю сам факт добавления Redis доказательством ускорения.
- **Answer (EN):** Caching is unsafe when a key omits tenant/user scope or relevant authorization context, potentially returning one customer's data to another. It is ineffective when the hit rate is low, invalidation is expensive, data changes rapidly, or cache lookup costs more than the original operation. I define a freshness contract, TTL, invalidation strategy, stampede protection, size limits, and failure behavior. Caching sensitive data requires an explicit threat model and isolation tests. I measure hit/miss ratio, latency, memory footprint, and impact on the source system; adding Redis is not itself evidence of a performance improvement.

### Pharmaviyum connection

**Status: hypothetical interview scenario; not a claim about measured or implemented production performance.**

For a pharmacy ERP workflow, a useful investigation could follow a medicine-search or customer-history API from the React client through FastAPI, SQLAlchemy, PostgreSQL, and any downstream service. Define a representative request mix and measure p50/p95/p99 latency, throughput, error rate, DB query count, pool wait time, and process resource use. Use tracing to locate slow spans, SQL query plans to investigate database work, and Python profiling only after the responsible component is narrowed down. If evaluating a cache, test tenant/customer isolation and freshness requirements explicitly. Do not claim a performance gain until a repeatable before/after test demonstrates it.

### Senior-level evaluation

A strong Senior answer should demonstrate that the candidate can:

1. Translate user experience and SLO requirements into measurable performance targets.
2. Design representative benchmarks and load tests, including warm-up, concurrency, arrival rate, and generator capacity.
3. Interpret latency percentiles and distinguish latency, throughput, error rate, and saturation.
4. Select CPU, memory, tracing, database, and infrastructure tools for the right diagnostic question.
5. Identify bottlenecks across Python, event loops, database pools, SQL, network, queues, and downstream services.
6. Explain why concurrency and caching can create contention, stale data, isolation failures, or overload.
7. Quantify changes with repeatable evidence and account for measurement noise.
8. Prevent regressions through performance budgets, monitoring, and release gates.
9. Preserve correctness, security, tenant isolation, and maintainability while optimizing.
10. State limitations and trade-offs instead of presenting a tool or architecture as a universal solution.

**Red flags:** optimizing before measuring; relying only on averages; assuming async makes CPU work faster; treating RSS growth as proof of a Python leak; increasing workers without examining shared bottlenecks; trusting a single benchmark run; caching tenant data without scoped keys; and claiming improvements without a reproducible baseline.

### Common pitfalls

- Optimizing a function that is not on the critical path.
- Treating average latency as sufficient while p95/p99 regress.
- Confusing latency with throughput or concurrency with capacity.
- Running benchmarks with unrealistic data, request mix, warm-up, or arrival rates.
- Ignoring coordinated omission or a saturated load generator.
- Treating cProfile, tracemalloc, RSS, and distributed tracing as interchangeable.
- Assuming tracemalloc accounts for every native allocation or all process memory.
- Calling allocator-retained memory a leak without checking object reachability and trends.
- Adding workers until the database pool or downstream service is overloaded.
- Using unbounded asyncio task creation instead of backpressure.
- Adding caching without freshness, invalidation, tenant isolation, and failure semantics.
- Accepting a microbenchmark result without validating end-to-end impact.
- Making performance gates so noisy that teams ignore them.
- Trading away authorization, correctness, or maintainability for an unproven speedup.

### References

- Python Profilers — cProfile: https://docs.python.org/3.14/library/profile.html
- Python tracemalloc: https://docs.python.org/3.14/library/tracemalloc.html
- py-spy: https://github.com/benfred/py-spy
- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/using-explain.html
- PostgreSQL Monitoring Statistics: https://www.postgresql.org/docs/current/monitoring-stats.html
- OpenTelemetry — Signals: https://opentelemetry.io/docs/concepts/signals/
- Google SRE Book — Monitoring Distributed Systems: https://sre.google/sre-book/monitoring-distributed-systems/
- Locust documentation: https://docs.locust.io/
- Python asyncio — Developing with asyncio: https://docs.python.org/3.14/library/asyncio-dev.html


## PY-CORE-030 — Python execution model, runtime semantics and CPython internals

### Question (EN)

**Walk me through how Python source code is executed. What are code objects, frames and bytecode, and which parts of this model are Python language semantics versus CPython implementation details?**

### Перевод (RU)

**Объясните путь выполнения исходного кода Python. Что такое code objects, frames и bytecode, и какие части этой модели относятся к семантике языка Python, а какие являются деталями реализации CPython?**

### What the interviewer evaluates

- Understanding the distinction between the Python language, its execution model and a particular interpreter implementation.
- Ability to describe the source-to-execution pipeline without claiming that every implementation uses the same bytecode or virtual machine.
- Understanding code objects, function objects, execution frames, namespaces and instruction execution.
- Awareness of compilation, module execution, imports and runtime name resolution.
- Ability to reason about tracebacks, stack frames, debugging and profiling.
- Awareness that CPython bytecode and adaptive interpreter details are version-specific implementation details.
- Ability to discuss runtime trade-offs without relying on folklore or unstable internals.

### Model answer (RU)

Сначала важно разделить три понятия: **язык Python**, его **модель выполнения** и конкретную реализацию интерпретатора, например **CPython**. Язык определяет наблюдаемую семантику программы. CPython — наиболее распространённая реализация, но её внутреннее устройство не следует автоматически считать обязательной частью языка: альтернативные реализации могут выполнять ту же программу другим способом.

В CPython исходный текст обычно проходит этапы разбора и компиляции. Текст преобразуется в синтаксическое представление, проверяется и компилируется в **code object**. Code object содержит инструкции байткода и метаданные, необходимые для выполнения: информацию о константах, именах, локальных переменных, аргументах и других свойствах блока кода. Сам code object не является обычной функцией и не хранит конкретные значения замыканий или привязку функции к глобальному namespace.

**Function object** связывает code object с контекстом вызова функции: в частности, с глобальным namespace, defaults, keyword defaults и closure cells, если они есть. Поэтому один code object в принципе может быть связан с разными function objects и разными окружениями.

При выполнении CPython создаёт **frame** для активного блока кода. Frame хранит состояние конкретного выполнения: ссылки на code object и namespaces, локальное состояние, стек вычислений и позицию выполнения. Вызов функции создаёт новый контекст выполнения; вложенные вызовы формируют цепочку активных frames. Эта структура лежит в основе traceback и помогает отладчикам и профилировщикам показывать путь выполнения. Детали внутреннего представления frames менялись между версиями CPython, поэтому нельзя проектировать приложение на предположении о неизменности их внутренней структуры.

**Bytecode** — низкоуровневое представление инструкций, которое исполняет виртуальная машина CPython. Интерпретатор последовательно обрабатывает инструкции, выполняя операции, переходы, вызовы и работу с объектами. Байткод не является машинным кодом процессора и не представляет собой стабильный формат для хранения или передачи между произвольными версиями Python. Набор инструкций и их поведение могут меняться между релизами.

Современный CPython использует оптимизации интерпретатора, в том числе специализацию инструкций и адаптацию горячих участков к наблюдаемым типам и операциям. Это детали реализации, которые могут улучшать производительность конкретных сценариев, но не меняют контракт языка. Нельзя полагаться на конкретную последовательность байткода или на то, что определённая оптимизация обязательно произойдёт.

При выполнении модуля его верхнеуровневый код исполняется в namespace модуля. Импорт связывает модуль с механизмом импорта и кэшированием в `sys.modules`; повторный импорт обычно использует уже загруженный объект модуля, хотя детали повторного выполнения зависят от механизма загрузки и явных действий приложения. Поиск имён во время выполнения зависит от области видимости и правил разрешения имён, а не от простого текстового поиска по файлу.

Практическая ценность этих знаний — диагностика. Traceback отражает цепочку активных контекстов выполнения и указывает места, связанные с исключением. Debugger может исследовать frame и локальное состояние; profiler может связывать затраты с функциями и call paths. Однако introspection и tracing могут иметь overhead, а доступ к внутренним деталям интерпретатора должен быть оправдан конкретной диагностической задачей.

На Senior-уровне важно чётко обозначать границы переносимости: семантика Python — контракт для программы; байткод, layout объектов, frame internals, reference counting и конкретные оптимизации — детали выбранной реализации и версии. Если приложение зависит от таких деталей, зависимость должна быть локализована, протестирована на целевых версиях и иметь обоснование. Для обычной прикладной разработки предпочтительны публичные API языка и стандартной библиотеки.

### Model answer (EN)

I first distinguish three things: the **Python language**, its **execution model**, and a particular interpreter implementation such as **CPython**. The language defines the observable semantics of a program. CPython is the most widely used implementation, but its internals are not automatically language guarantees; another implementation may execute the same program differently.

In CPython, source code normally goes through parsing and compilation. The source is transformed into a syntactic representation, validated, and compiled into a **code object**. A code object contains bytecode instructions and metadata needed to execute a block, including information about constants, names, local variables, arguments, and other code properties. A code object is not itself an ordinary function: it does not contain a particular closure's values or a function's binding to a global namespace.

A **function object** associates a code object with its execution context, including its global namespace, defaults, keyword defaults, and closure cells where applicable. Consequently, the same code object can in principle be associated with different function objects and environments.

When CPython executes a block of code, it creates a **frame** for that active execution. A frame represents the state of a particular execution: references to the code object and namespaces, local execution state, an evaluation stack, and the current instruction position. A function call creates a new execution context; nested calls form a chain of active frames. This model underpins tracebacks and allows debuggers and profilers to expose execution paths. CPython's internal frame representation has changed across releases, so application code should not assume a permanently stable internal layout.

**Bytecode** is a lower-level instruction representation executed by the CPython virtual machine. The interpreter processes instructions to perform operations, control flow, calls, and object interactions. Bytecode is not processor machine code and is not a stable interchange or persistence format across arbitrary Python versions. The instruction set and its behaviour can change between releases.

Modern CPython includes interpreter optimisations such as instruction specialisation and adaptation of frequently executed operations to observed types and patterns. These are implementation details that can improve particular workloads without changing the language contract. I would not depend on a specific bytecode sequence or assume that a particular optimisation must occur.

When a module is executed, its top-level code runs in the module namespace. Importing interacts with the import machinery and the `sys.modules` cache; a subsequent import normally reuses the loaded module object, while re-execution depends on the loader mechanism and explicit application actions. Runtime name resolution follows Python's scope rules rather than a simple textual search through a file.

These concepts are useful for diagnostics. A traceback represents the chain of execution contexts associated with an exception and identifies relevant source locations. A debugger can inspect frames and local state; a profiler can attribute costs to functions and call paths. Introspection and tracing can add overhead, however, and access to interpreter internals should be justified by a concrete diagnostic need.

At Senior level, I make portability boundaries explicit: Python semantics are the program's language contract; bytecode, object layouts, frame internals, reference counting, and specific optimisations belong to a particular implementation and version. If an application depends on such details, the dependency should be isolated, justified, and tested against supported interpreter versions. Ordinary application code should prefer public language and standard-library APIs.

### Follow-up questions and model answers

#### FU-1

**EN:** What is the difference between a code object and a function object?  
**RU:** Чем code object отличается от function object?

**Answer (RU):** Code object описывает скомпилированный блок кода: инструкции и метаданные, например имена, константы и сведения о локальных переменных. Function object связывает этот code object с конкретным окружением выполнения — globals, defaults и closure cells. Поэтому code object сам по себе не равен вызываемой функции и не содержит все значения, необходимые для конкретного вызова.

**Answer (EN):** A code object describes a compiled block: its instructions and metadata such as names, constants, and local-variable information. A function object associates that code object with a particular execution environment, including globals, defaults, and closure cells. A code object is therefore not itself the callable function and does not contain every value needed for a particular call.

#### FU-2

**EN:** Is Python bytecode a stable format that can safely be stored and reused across Python versions?  
**RU:** Является ли байткод Python стабильным форматом, который можно безопасно сохранять и повторно использовать между версиями Python?

**Answer (RU):** Нет. Байткод CPython — деталь реализации, и набор инструкций, их аргументы и семантика могут меняться между версиями. Файлы `.pyc` предназначены для механизма кэширования импорта в совместимом окружении, а не как универсальный долговременный формат обмена. Для переносимости следует распространять исходный код или стандартные артефакты упаковки, а не строить контракт на внутреннем байткоде.

**Answer (EN):** No. CPython bytecode is an implementation detail; its instructions, arguments, and semantics can change between releases. `.pyc` files support import caching in compatible environments, not a universal long-term interchange format. For portability, distribute source code or standard packaging artifacts rather than making internal bytecode part of an application contract.

#### FU-3

**EN:** How are frames useful when debugging an exception, and what should you avoid assuming about them?  
**RU:** Чем frames полезны при отладке исключения и какие предположения о них опасны?

**Answer (RU):** Frame представляет состояние активного блока выполнения: code object, namespaces и позицию исполнения. Цепочка frames помогает traceback показать путь вызовов, а debugger — исследовать локальный контекст. Но внутреннее представление frame в CPython менялось; не следует зависеть от приватного layout, удерживать frames без необходимости или считать introspection бесплатной. Для диагностики лучше использовать публичные интерфейсы traceback, inspect и debugger tooling.

**Answer (EN):** A frame represents the state of an active execution block, including its code object, namespaces, and execution position. The frame chain lets a traceback show the call path and allows a debugger to inspect local context. CPython's internal frame representation has changed, however. Avoid depending on private layouts, retaining frames unnecessarily, or assuming introspection is free. Prefer public traceback, inspect, and debugger interfaces for diagnostics.

#### FU-4

**EN:** Does CPython's adaptive interpreter change the semantics of Python code?  
**RU:** Меняет ли адаптивный интерпретатор CPython семантику программы Python?

**Answer (RU):** Нет, оптимизации интерпретатора должны сохранять наблюдаемую семантику программы. Специализация может менять способ исполнения конкретных инструкций ради производительности, но не должна менять результат согласно контракту языка. Конкретные механизмы, пороги и представление специализированных инструкций являются деталями реализации и могут меняться. Корректность программы не должна зависеть от того, активировалась ли определённая оптимизация.

**Answer (EN):** No. Interpreter optimisations must preserve the observable semantics of the program. Specialisation may change how particular instructions are executed for performance, but it must not change the result under the language contract. The mechanisms, thresholds, and representation of specialised instructions are implementation details and may change. Program correctness must not depend on whether a particular optimisation is activated.

#### FU-5

**EN:** How would you investigate a production issue using Python runtime introspection without making the issue worse?  
**RU:** Как расследовать production-проблему с помощью introspection Python, не усугубив её?

**Answer (RU):** Сначала определю симптом и выберу минимально инвазивный инструмент: структурированные логи и correlation IDs, метрики, sampling traces, профилирование или traceback capture. Проверю overhead, объём собираемых данных и влияние на latency, память и event loop. Не буду массово сериализовать locals или сохранять frames: там могут находиться секреты, персональные данные и большие графы объектов, а удержание frame может продлить жизнь объектов. Сбор данных ограничу по времени, доступу и объёму, отредактирую чувствительные поля и проверю гипотезу на воспроизводимом сценарии.

**Answer (EN):** I would start from the symptom and choose the least invasive tool: structured logs and correlation IDs, metrics, sampled traces, profiling, or traceback capture. I would assess overhead, data volume, and effects on latency, memory, and the event loop. I would not indiscriminately serialize locals or retain frames: they may contain secrets, personal data, and large object graphs, and retaining a frame can extend object lifetimes. I would bound collection by time, access, and volume, redact sensitive fields, and validate the hypothesis with a reproducible scenario.

### Pharmaviyum connection

**Status: hypothetical interview scenario — not a claim about the current implementation.**

Imagine investigating an intermittent latency spike in a FastAPI request path. An engineer could correlate request logs and traces, then use a sampled profiler or targeted traceback capture to determine whether time is spent in Python application code, a blocking call, or a dependency. Runtime introspection must be bounded and must not expose patient/customer data or secrets. The repository and deployed runtime should be inspected before making claims about the interpreter version, profiling setup, or observed bottleneck.

### Senior-level evaluation

| Level | Expected evidence |
|---|---|
| Weak | Treats CPython internals as universal Python guarantees; confuses bytecode with machine code; cannot distinguish code and function objects. |
| Competent | Describes compilation, bytecode execution, frames, and the purpose of tracebacks; recognises that bytecode varies by version. |
| Strong Senior | Separates language semantics from implementation details; explains code/function/frame relationships accurately; understands diagnostic value and overhead; avoids depending on unstable internals and protects sensitive runtime state. |

### Common pitfalls

- Saying that every Python implementation executes CPython bytecode.
- Treating bytecode as processor machine code or a stable public ABI.
- Confusing a code object with a function object.
- Claiming that a code object contains a function's globals and closure values.
- Treating CPython frame internals or object layouts as stable across releases.
- Assuming interpreter specialisation changes language-level semantics.
- Depending on a particular disassembly output for application correctness.
- Treating tracebacks or frame inspection as cost-free.
- Capturing locals indiscriminately and leaking credentials, tokens, or customer/patient data.
- Retaining frames and unintentionally extending the lifetime of large object graphs.
- Assuming implementation-specific optimisations are guaranteed on every workload.

### References

- Python Language Reference — Execution model: https://docs.python.org/3/reference/executionmodel.html
- Python Data Model — Code objects: https://docs.python.org/3/reference/datamodel.html#code-objects
- Python `dis` module: https://docs.python.org/3/library/dis.html
- Python `inspect` module: https://docs.python.org/3/library/inspect.html
- Python `traceback` module: https://docs.python.org/3/library/traceback.html
- CPython Developer Guide: https://devguide.python.org/
- CPython Internals documentation: https://github.com/python/cpython
