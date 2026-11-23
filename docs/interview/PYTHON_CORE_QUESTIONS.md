# Python Core — Question Bank

**Status:** In progress  
**Coverage:** 5 of 30 primary questions drafted  
**Review rule:** Draft answers must be technically reviewed before being marked validated.

---

## PY-CORE-001 — Python object model: identity, type and value

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

**EN:** What is the difference between is and ==?  
**RU:** В чём разница между is и ==?

**Answer (RU):** is проверяет идентичность — являются ли операнды одним объектом. == проверяет равенство значений в соответствии с методом сравнения типа, обычно __eq__. Два разных объекта могут быть равны по ==, но не идентичны по is.

**Answer (EN):** is checks object identity, while == checks value equality according to the object's equality implementation. Two distinct objects can compare equal without being the same object.

#### FU-2

**EN:** If you pass a list to a function and the function appends an item, what can the caller observe?  
**RU:** Если передать список в функцию и функция добавит в него элемент, что увидит вызывающий код?

**Answer (RU):** Если функция изменяет переданный список на месте, вызывающий код увидит изменение, потому что оба участка кода работают с одним объектом. Если функция лишь присвоит локальному параметру ссылку на новый список, исходная переменная вызывающего кода останется связанной с прежним объектом.

**Answer (EN):** An in-place mutation is visible to the caller because both the caller and the function refer to the same list object. Rebinding the function's local parameter to a new list does not change the caller's binding.

#### FU-3

**EN:** Why should you avoid using is to compare strings or integers?  
**RU:** Почему не следует использовать is для сравнения строк или целых чисел?

**Answer (RU):** Потому что is проверяет идентичность, а не равенство значений. Поведение может случайно казаться корректным из-за interning или оптимизаций конкретной реализации Python. Для сравнения содержимого нужно использовать ==. Проверки через is следует оставлять для случаев, где важна идентичность, например is None.

**Answer (EN):** Because is tests identity, not value equality. Interning and compiler optimisations may make some comparisons appear to work, but that behaviour is not a reliable language contract. Use == for values and reserve is for identity checks such as is None.

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
