# Python Core — Question Bank

**Status:** In progress  
**Coverage:** 2 of 30 primary questions drafted  
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
