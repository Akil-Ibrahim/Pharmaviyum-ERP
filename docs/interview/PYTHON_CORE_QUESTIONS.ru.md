# Python Core — Банк вопросов

**Статус:** В работе  
**Охват:** 14 из 30 основных вопросов подготовлено  
**Правило проверки:** Эталонные ответы должны пройти техническую проверку, прежде чем получить статус validated.

---

## PY-CORE-001 — Объектная модель Python: идентичность, тип и значение

### Question (EN)

**Can you explain Python's object model and distinguish an object's identity, type and value?**

### Перевод (RU)

**Можете объяснить объектную модель Python и разграничить идентичность объекта, его тип и значение?**

### Что проверяет интервьюер

- Понимает ли кандидат, что переменные Python — это имена, связанные с объектами, а не типизированные контейнеры.
- Различает ли он идентичность (is) и равенство (==).
- Понимает ли изменяемость и aliasing.
- Может ли объяснить передачу аргументов и побочные эффекты.
- Знает ли, что interning и подобные оптимизации не являются гарантиями языка.

### Эталонный ответ (RU)

В Python объект — это сущность, у которой есть **идентичность, тип и значение**.

- **Идентичность (identity)** определяет, какой именно это объект. В течение жизненного цикла объекта она не меняется. Оператор **is** проверяет, ссылаются ли два имени на один и тот же объект.
- **Тип (type)** определяет поведение объекта и набор поддерживаемых операций. Его можно получить через **type()**. В обычной модели Python тип объекта не меняется в течение его жизни.
- **Значение (value)** — данные, которые представляет объект. Оператор **==** проверяет равенство согласно реализации сравнения типа, обычно **__eq__**, а не обязательно идентичность.

Переменная в Python — это имя, связанное с объектом. Присваивание обычно не копирует объект: оно связывает другое имя с тем же объектом. Поэтому два имени могут быть **алиасами** одного изменяемого объекта. Изменение объекта через одно имя будет наблюдаться и через другое.

Это важно при передаче аргументов в функции. Python использует модель передачи ссылок на объекты, часто описываемую как *call by sharing*: функция получает доступ к тому же объекту. Если объект изменяемый, функция может изменить его состояние, и вызывающий код увидит изменение. Но переназначение локального параметра на другой объект само по себе не переназначает переменную вызывающего кода.

Для сравнения значений используется **==**. Оператор **is** уместен, когда важна идентичность, например при проверке **value is None**.

Нельзя полагаться на то, что одинаковые литералы всегда будут одним объектом. CPython может применять interning и другие оптимизации, но это детали реализации, а не универсальный контракт языка.

### Эталонный ответ (EN)

Every Python object has an **identity, a type and a value**.

- **Identity** distinguishes a particular object. It remains stable during that object's lifetime, and **is** checks whether two references point to the same object.
- **Type** defines the object's behaviour and the operations it supports. It can be inspected with **type()**. In Python's normal object model, an object's type does not change during its lifetime.
- **Value** is the data represented by the object. **==** checks equality according to the type's equality implementation, typically **__eq__**; it does not necessarily check identity.

A variable in Python is a name bound to an object, not a typed container holding the object itself. Assignment generally binds another name to the same object rather than copying it. Consequently, two names can alias the same mutable object. A mutation performed through one alias is observable through the other.

This also matters for function calls. Python follows a *call-by-sharing* model: a function receives access to the same object. If that object is mutable, the function can mutate it and the caller can observe the change. Rebinding the local parameter, however, does not rebind the caller's variable.

I use **==** for value comparison and **is** for identity checks, commonly for singleton checks such as **value is None**. I do not rely on object interning or identity behaviour of literals: those may be implementation optimisations, not language-level guarantees.

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** What is the difference between is and ==?  
**RU:** В чём разница между is и ==?

**Ответ (RU):** is проверяет идентичность — являются ли операнды одним объектом. == проверяет равенство значений в соответствии с методом сравнения типа, обычно __eq__. Два разных объекта могут быть равны по ==, но не идентичны по is.

**Answer (EN):** is checks object identity, while == checks value equality according to the object's equality implementation. Two distinct objects can compare equal without being the same object.

#### FU-2

**EN:** If you pass a list to a function and the function appends an item, what can the caller observe?  
**RU:** Если передать список в функцию и функция добавит в него элемент, что увидит вызывающий код?

**Ответ (RU):** Если функция изменяет переданный список на месте, вызывающий код увидит изменение, потому что оба участка кода работают с одним объектом. Если функция лишь присвоит локальному параметру ссылку на новый список, исходная переменная вызывающего кода останется связанной с прежним объектом.

**Answer (EN):** An in-place mutation is visible to the caller because both the caller and the function refer to the same list object. Rebinding the function's local parameter to a new list does not change the caller's binding.

#### FU-3

**EN:** Why should you avoid using is to compare strings or integers?  
**RU:** Почему не следует использовать is для сравнения строк или целых чисел?

**Ответ (RU):** Потому что is проверяет идентичность, а не равенство значений. Поведение может случайно казаться корректным из-за interning или оптимизаций конкретной реализации Python. Для сравнения содержимого нужно использовать ==. Проверки через is следует оставлять для случаев, где важна идентичность, например is None.

**Answer (EN):** Because is tests identity, not value equality. Interning and compiler optimisations may make some comparisons appear to work, but that behaviour is not a reliable language contract. Use == for values and reserve is for identity checks such as is None.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о конкретной реализации:** представим, что сервис получает изменяемый список фильтров поиска лекарств. Если несколько слоёв используют один и тот же список, изменение на месте в одном слое может неожиданно повлиять на другой. Более безопасный контракт API может использовать immutable value objects, defensive copies на границах владения данными или явно описанные правила мутации.

Перед утверждением, что конкретный сервис Pharmaviyum уже использует один из этих подходов, необходимо проверить соответствующий код репозитория.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Считает переменную контейнером; путает identity и equality; утверждает, что аргументы автоматически копируются. |
| Компетентный | Корректно объясняет is, ==, mutability и aliasing на простом примере. |
| Strong Senior | Объясняет bindings объектов, call-by-sharing, различие мутации и переназначения, протокол равенства и отсутствие гарантий interning; связывает aliasing с владением данными и контролем побочных эффектов API. |

### Типичные ошибки

- Говорить, что Python передаёт аргументы строго по ссылке или строго по значению, не объясняя семантику совместного использования объектов.
- Считать is более быстрой или взаимозаменяемой версией ==.
- Предполагать, что изменяемые объекты автоматически копируются при вызове функции.
- Представлять interning в CPython как гарантию языка.
- Путать переназначение имени с изменением объекта, на который оно ссылается.

### Источники

- Python data model: https://docs.python.org/3/reference/datamodel.html
- Python expressions — identity comparisons: https://docs.python.org/3/reference/expressions.html#is-not
- Programming FAQ — identity and equality: https://docs.python.org/3/faq/programming.html#why-did-changing-list-y-also-change-list-x

---

## PY-CORE-002 — Изменяемость и неизменяемость объектов

### Question (EN)

**What is the difference between mutable and immutable objects in Python, and how does that distinction affect program design, hashing, and function behaviour?**

### Перевод (RU)

**В чём разница между изменяемыми и неизменяемыми объектами в Python и как это различие влияет на проектирование программ, хеширование и поведение функций?**

### Что проверяет интервьюер

- Различает ли кандидат изменение объекта и переназначение имени.
- Знает ли распространённые изменяемые и неизменяемые встроенные типы.
- Понимает ли hashability и требования словарей и множеств к ключам.
- Понимает ли shallow copy, deep copy и вложенное изменяемое состояние.
- Умеет ли проектировать API с явными контрактами владения данными и побочных эффектов.

### Эталонный ответ (RU)

**Изменяемость (mutability)** описывает, может ли состояние существующего объекта изменяться после его создания. Изменение объекта не обязательно означает создание нового объекта.

К типичным изменяемым встроенным типам относятся **list, dict, set и bytearray**. К типичным неизменяемым — **int, float, bool, str, bytes, tuple и frozenset**. Это классификация конкретных типов; пользовательские объекты не становятся автоматически неизменяемыми.

У неизменяемого объекта его значение нельзя изменить на месте. Операции, которые выглядят как изменение, обычно создают новый объект. Например, конкатенация строк создаёт новую строку. Напротив, **list.append()** изменяет существующий список, поэтому все имена-алиасы этого списка увидят изменение.

Важно различать **мутацию** и **переназначение**. Вызов **items.append(x)** меняет объект списка. Выражение **items = items + [x]** создаёт новый список и переназначает имя items; другие имена, ссылавшиеся на исходный список, продолжат ссылаться на него.

Изменяемость связана с **hashability**, но это не одно и то же. Хешируемый объект имеет хеш, который должен оставаться стабильным, пока объект находится в хеш-коллекции; равные объекты должны иметь одинаковые хеши. Встроенные изменяемые контейнеры list, dict и set не хешируются. Неизменяемые типы часто хешируемы, но не всегда: tuple хешируется только тогда, когда хешируемы все его элементы. Поэтому кортеж может содержать список, но такой кортеж нельзя использовать как ключ словаря.

При проектировании API я явно определяю, кто владеет переданными данными и разрешено ли функции изменять их на месте. Если функция не должна создавать побочные эффекты, можно принимать неизменяемые структуры, создавать копию на границе владения или возвращать новое значение. Копирование имеет стоимость. Поверхностная копия создаёт новый внешний контейнер, но сохраняет ссылки на вложенные объекты; глубокая копия рекурсивно копирует вложенные объекты, насколько это поддерживается протоколом, и может быть дороже или неприменима к некоторым ресурсам.

Неизменяемые значения упрощают reasoning, безопасное совместное использование и применение в качестве ключей. Изменяемые объекты полезны для эффективного обновления состояния, но требуют ясного контракта владения, контроля алиасов и побочных эффектов.

### Эталонный ответ (EN)

**Mutability** describes whether an object's state can be changed after creation. Mutating an object does not necessarily create a new object.

Common mutable built-in types include **list, dict, set, and bytearray**. Common immutable built-in types include **int, float, bool, str, bytes, tuple, and frozenset**. This is a property of particular types; user-defined objects are not automatically immutable.

An immutable object's value cannot be changed in place. An operation that appears to modify it generally creates a new object. String concatenation, for example, creates a new string. By contrast, **list.append()** mutates the existing list, so every alias to that list observes the change.

I distinguish **mutation** from **rebinding**. **items.append(x)** changes the list object. **items = items + [x]** creates a new list and rebinds the name items; other names referring to the original list remain bound to it.

Mutability is related to **hashability**, but the concepts are not identical. A hashable object's hash must remain stable while it is stored in a hash-based collection, and equal objects must have equal hashes. Mutable built-in containers such as lists, dictionaries, and sets are unhashable. Many immutable types are hashable, but not all: a tuple is hashable only if all its elements are hashable. A tuple can therefore contain a list, but that tuple cannot be used as a dictionary key.

When designing APIs, I make ownership and mutation contracts explicit. If a function must not cause side effects, I can accept immutable structures, copy data at an ownership boundary, or return a new value. Copying has a cost. A shallow copy creates a new outer container but retains references to nested objects; a deep copy recursively copies nested objects where supported and may be more expensive or unsuitable for certain resources.

Immutable values make reasoning, safe sharing, and use as mapping keys easier. Mutable objects are useful for efficient state updates, but they require clear ownership, aliasing, and side-effect contracts.

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** Why is a list unhashable, and why does a dictionary key need a stable hash?  
**RU:** Почему список не хешируется и зачем ключу словаря нужен стабильный хеш?

**Ответ (RU):** Содержимое списка может измениться, поэтому хеш мог бы измениться после помещения объекта в словарь или множество. Это нарушило бы поиск по хеш-таблице. Ключ должен сохранять хеш, согласованный с равенством, пока находится в коллекции.

**Answer (EN):** A list can change, so its hash could change after insertion into a dictionary or set, breaking hash-table lookup. A key must maintain a hash consistent with equality while stored in the collection.

#### FU-2

**EN:** Is every immutable object hashable? Explain the tuple case.  
**RU:** Каждый ли неизменяемый объект хешируем? Объясните случай с tuple.

**Ответ (RU):** Нет. Неизменяемость сама по себе не гарантирует hashability. Кортеж хешируется, только если хешируются все его элементы. Кортеж из целых чисел может быть ключом словаря, а кортеж со списком — нет.

**Answer (EN):** No. Immutability alone does not guarantee hashability. A tuple is hashable only when all its elements are hashable. A tuple of integers can be a dictionary key, while a tuple containing a list cannot.

#### FU-3

**EN:** What is the difference between a shallow copy and a deep copy?  
**RU:** Чем поверхностное копирование отличается от глубокого?

**Ответ (RU):** Поверхностная копия создаёт новый внешний объект, но сохраняет ссылки на вложенные объекты. Глубокая копия рекурсивно копирует вложенные объекты, насколько это поддерживается. Она может быть дороже и не всегда подходит для ресурсов вроде соединений или файловых дескрипторов.

**Answer (EN):** A shallow copy creates a new outer object but retains references to nested objects. A deep copy recursively copies nested objects where supported. It can be more expensive and may be inappropriate for resources such as connections or file descriptors.

#### FU-4

**EN:** Can an immutable tuple contain a mutable object? What does that imply?  
**RU:** Может ли неизменяемый tuple содержать изменяемый объект? К чему это приводит?

**Ответ (RU):** Да. Неизменяемость кортежа запрещает заменять его элементы, но не делает неизменяемыми объекты, на которые эти элементы ссылаются. Вложенный список можно изменить; кортеж с таким списком не будет хешируемым.

**Answer (EN):** Yes. Tuple immutability prevents replacing its elements, but it does not make referenced objects immutable. A nested list can still be mutated, and a tuple containing that list is unhashable.

#### FU-5

**EN:** How would you prevent a function from unexpectedly mutating caller-owned data?  
**RU:** Как предотвратить неожиданное изменение данных вызывающего кода внутри функции?

**Ответ (RU):** Сначала нужно определить контракт владения. Можно принимать неизменяемые структуры, копировать данные на границе владения, преобразовывать вход во внутреннее представление или возвращать новое значение. Не следует применять глубокое копирование автоматически: оно может быть дорогим и неподходящим для некоторых ресурсов.

**Answer (EN):** I would define the ownership contract first. Options include accepting immutable structures, copying at an ownership boundary, converting input into an internally owned representation, or returning a new value. I would not use deep copying indiscriminately because it can be expensive or unsuitable for certain resources.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** workflow поиска лекарств передаёт фильтры через слои валидации, retrieval и ranking. Если один слой изменит общий словарь или список, последующие слои могут получить неожиданное состояние. Надёжный дизайн определяет владение данными на каждой границе, по возможности использует неизменяемые request/value objects и явно обозначает намеренные мутации.

Не утверждайте, что конкретная модель Pharmaviyum является immutable или mutable, не проверив её реализацию.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Путает мутацию с переназначением и считает любой immutable-объект хешируемым. |
| Компетентный | Корректно классифицирует распространённые встроенные типы и объясняет поведение списков и ключей словаря. |
| Strong Senior | Объясняет инварианты hash/equality, вложенную изменяемость, компромиссы копирования, границы владения, aliasing, побочные эффекты API и влияние на производительность. |

### Типичные ошибки

- Считать, что неизменяемый контейнер делает неизменяемыми все объекты внутри него.
- Считать любой immutable-объект хешируемым.
- Изменять объект, используемый как ключ в hash-based коллекции.
- Предполагать, что shallow copy рекурсивно копирует вложенные объекты.
- Использовать deep copy как универсальное решение без учёта стоимости и семантики ресурсов.
- Игнорировать контракты владения и побочных эффектов в API.

### Источники

- Python glossary — hashable: https://docs.python.org/3/glossary.html#term-hashable
- Python data model: https://docs.python.org/3/reference/datamodel.html
- Built-in types: https://docs.python.org/3/library/stdtypes.html
- copy module: https://docs.python.org/3/library/copy.html

---

## PY-CORE-003 — Семантика передачи аргументов в Python

### Question (EN)

**How does Python pass arguments to functions? Explain object references, mutation, rebinding, and the risks of mutable default arguments.**

### Перевод (RU)

**Как Python передаёт аргументы в функции? Объясните ссылки на объекты, мутацию, переназначение и риски изменяемых аргументов по умолчанию.**

### Что проверяет интервьюер

- Понимание модели call by sharing, а не традиционной передачи переменной по ссылке.
- Различие между мутацией объекта аргумента и переназначением имени параметра.
- Знание назначения `*args` и `**kwargs`.
- Понимание того, что выражения значений по умолчанию вычисляются один раз при определении функции.
- Умение проектировать предсказуемые контракты функций без скрытого разделяемого состояния.

### Эталонный ответ (RU)

Python часто описывают как использующий **call by sharing** (также встречается формулировка *call by object sharing*). При вызове функции параметр становится локальным именем, связанным с тем же объектом, который передал вызывающий код. Python не копирует автоматически весь объект и не предоставляет обычную семантику передачи переменной по ссылке, как в некоторых других языках.

Из этого следуют два разных поведения:

- Если функция **изменяет объект на месте**, например вызывает `append()` у переданного списка, вызывающий код увидит изменение, потому что оба имени ссылаются на один объект.
- Если функция **переназначает параметр**, например присваивает ему новый список или целое число, меняется только локальная привязка параметра. Привязка имени в вызывающем коде не меняется.

Поэтому утверждение «изменяемые аргументы передаются по ссылке, а неизменяемые — по значению» некорректно. Механизм передачи один и тот же; различается возможность изменить сам объект. Неизменяемый объект нельзя изменить на месте, но локальное имя параметра всё равно можно переназначить.

Параметры `*args` собирают дополнительные позиционные аргументы в кортеж, а `**kwargs` — дополнительные именованные аргументы в словарь. Это новые контейнеры для собранных аргументов, но значения внутри них по-прежнему являются ссылками на соответствующие объекты. Сигнатура функции также может ограничивать способы передачи параметров с помощью маркеров `/` и `*`.

Отдельная важная ловушка — **изменяемые значения по умолчанию**. Выражения значений по умолчанию вычисляются один раз в момент определения функции, а не при каждом вызове. Если значением по умолчанию является список или словарь и функция изменяет его, состояние сохраняется между вызовами. Это может приводить к неожиданному совместному состоянию.

Обычный безопасный подход — использовать `None` как sentinel и создавать новый контейнер внутри функции. Если `None` является допустимым значением предметной области, следует использовать отдельный sentinel-объект. Значения по умолчанию также являются частью публичного контракта функции и должны выбираться осознанно.

На Senior-уровне я объясняю это через **binding, object identity, mutation и API contract**. Я документирую, изменяет ли функция входные объекты, избегаю скрытого разделяемого состояния и выбираю сигнатуры, которые делают допустимые способы вызова явными.

### Эталонный ответ (EN)

Python is commonly described as using **call by sharing**, also known as *call by object sharing*. When a function is called, each parameter name in the function's local scope is bound to the object supplied by the caller. Python does not automatically copy the entire object, nor does it use traditional variable-level call-by-reference semantics.

This leads to two distinct cases:

- If a function **mutates an object in place**, such as calling `append()` on a passed list, the caller can observe the change because both names refer to the same object.
- If a function **rebinds its parameter**, for example by assigning a new list or integer to it, only the local parameter binding changes. The caller's variable remains bound to its original object.

Therefore, it is inaccurate to say that mutable arguments are passed by reference while immutable arguments are passed by value. The argument-passing mechanism is the same; what differs is whether the object itself can be mutated. An immutable object cannot be changed in place, but the local parameter name can still be rebound.

Extra positional arguments collected by `*args` are placed in a tuple, while extra keyword arguments collected by `**kwargs` are placed in a dictionary. These are new collection containers, but their values are still references to the corresponding objects. Function signatures can also constrain positional and keyword usage with markers such as `/` and `*`.

A common pitfall is a **mutable default argument**. Default expressions are evaluated once, when the function is defined, rather than on every call. If a list or dictionary is used as a default and mutated by the function, that state is retained across calls and can cause surprising behaviour.

A common safe pattern is to use `None` as a sentinel and create a fresh container inside the function. If `None` is itself a valid domain value, use a dedicated sentinel object instead. Default values are also part of the function's public API contract and should be chosen deliberately.

At Senior level, I explain this in terms of **name binding, object identity, mutation, and API contracts**. I make it explicit whether a function mutates caller-owned objects, avoid hidden shared state, and design signatures that communicate valid calling conventions.

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** What happens if a function appends to a list argument and then reassigns the parameter to a new list?  
**RU:** Что произойдёт, если функция добавит элемент в переданный список, а затем переназначит параметр на новый список?

**Ответ (RU):** Изменение исходного списка через `append()` будет видно вызывающему коду. Последующее присваивание параметру нового списка изменит только локальную привязку имени параметра. Внешняя переменная продолжит ссылаться на исходный список, уже содержащий добавленный элемент.

**Answer (EN):** The append operation mutates the original list, so the caller observes that change. Reassigning the parameter to a new list only changes the local binding. The caller's variable still refers to the original list, including the appended item.

#### FU-2

**EN:** Why are mutable default arguments dangerous, and when are defaults evaluated?  
**RU:** Почему изменяемые значения по умолчанию опасны и когда вычисляются значения по умолчанию?

**Ответ (RU):** Выражение значения по умолчанию вычисляется один раз при определении функции. Поэтому один и тот же список или словарь может использоваться несколькими вызовами. Если функция изменяет его, состояние сохраняется между вызовами. Обычно используют sentinel и создают новый объект внутри функции.

**Answer (EN):** A default expression is evaluated once when the function is defined. The same list or dictionary can therefore be reused across calls. If the function mutates it, the state persists. A common solution is to use a sentinel and create a fresh object inside the function.

#### FU-3

**EN:** What exactly do `*args` and `**kwargs` collect, and are the contained objects copied?  
**RU:** Что именно собирают `*args` и `**kwargs` и копируются ли содержащиеся в них объекты?

**Ответ (RU):** `*args` собирает дополнительные позиционные аргументы в кортеж, а `**kwargs` — дополнительные именованные аргументы в словарь. Создаются контейнеры для сбора аргументов, но сами переданные объекты автоматически не копируются: элементы контейнеров ссылаются на исходные объекты.

**Answer (EN):** `*args` collects extra positional arguments into a tuple, and `**kwargs` collects extra keyword arguments into a dictionary. The collection containers are created, but the supplied objects are not automatically copied; the entries refer to the original objects.

#### FU-4

**EN:** How would you use a sentinel when `None` is a valid argument value?  
**RU:** Как использовать sentinel, если `None` является допустимым значением аргумента?

**Ответ (RU):** Нужно создать отдельный уникальный объект-сентинел и использовать его как значение по умолчанию. Внутри функции проверять идентичность через `is`, а не равенство. Тогда можно отличить отсутствие аргумента от явной передачи `None`.

**Answer (EN):** I would create a unique sentinel object and use it as the default. Inside the function, I would check it with `is`, not equality. This distinguishes an omitted argument from an explicit `None` value.

#### FU-5

**EN:** What is the difference between positional-only, positional-or-keyword, and keyword-only parameters?  
**RU:** Чем отличаются positional-only, positional-or-keyword и keyword-only параметры?

**Ответ (RU):** Positional-only параметры можно передать только позиционно и они располагаются до `/`. Positional-or-keyword параметры допускают оба способа передачи. Keyword-only параметры должны передаваться по имени и располагаются после отдельного `*` в сигнатуре функции. Эти ограничения помогают сделать API яснее и сохранить совместимость при развитии интерфейса.

**Answer (EN):** Positional-only parameters can be supplied only positionally and appear before `/`. Positional-or-keyword parameters support either calling style. Keyword-only parameters must be supplied by name and appear after a standalone `*` in the signature. These constraints make APIs clearer and can help preserve compatibility as interfaces evolve.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** сервисная функция получает поисковые фильтры или список идентификаторов лекарств. Если она изменяет входные данные вызывающего кода или хранит request-specific данные в изменяемом значении по умолчанию, один запрос может повлиять на последующие операции. Надёжная реализация использует состояние на каждый вызов, явные контракты владения и мутации, а также тесты повторных вызовов для обнаружения утечки состояния.

Не утверждайте, что конкретная функция Pharmaviyum содержит такой дефект, не проверив её реализацию.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Говорит, что mutable передаются по ссылке, а immutable — по значению; не может объяснить mutable defaults. |
| Компетентный | Объясняет мутацию и переназначение, корректно описывает `*args`, `**kwargs` и момент вычисления defaults. |
| Strong Senior | Точно объясняет call by sharing, выявляет aliasing и утечки состояния, проектирует API с sentinel, понимает маркеры видов параметров и обсуждает совместимость и стратегию тестирования. |

### Типичные ошибки

- Описывать передачу аргументов Python как разделение на pass-by-reference и pass-by-value в зависимости от изменяемости.
- Считать, что переназначение параметра меняет переменную вызывающего кода.
- Предполагать, что значения по умолчанию вычисляются при каждом вызове.
- Непреднамеренно использовать изменяемый список или словарь как общий аккумулятор по умолчанию.
- Считать, что `*args` или `**kwargs` глубоко копируют значения аргументов.
- Использовать `None` как sentinel, если `None` является допустимым значением предметной области.

### Источники

- Python tutorial — defining functions: https://docs.python.org/3/tutorial/controlflow.html#defining-functions
- Python FAQ — mutable default arguments: https://docs.python.org/3/faq/programming.html#why-are-default-values-shared-between-objects
- Python language reference — function definitions: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- Python glossary: https://docs.python.org/3/glossary.html

---

## PY-CORE-004 — Имена, идентичность, равенство и ссылки на объекты

### Question (EN)

**Explain the difference between object identity and equality in Python. How do name binding, aliasing, `is`, `==`, and the equality/hash contract interact?**

### Перевод (RU)

**Объясните разницу между идентичностью объекта и равенством в Python. Как связаны привязка имён, aliasing, операторы `is` и `==`, а также контракт равенства и хеширования?**

### Что проверяет интервьюер

- Понимание того, что имена являются привязками к объектам, а не контейнерами, хранящими значения.
- Различие между идентичностью объекта и равенством значений.
- Понимание того, когда применять `is`, а когда `==`.
- Понимание aliasing и его последствий для изменяемых объектов.
- Знание инварианта equality/hash и поведения пользовательского `__eq__`.
- Отсутствие зависимости от особенностей конкретной реализации Python.

### Эталонный ответ (RU)

В Python важно различать **имя, объект, идентичность и равенство**.

Имя — это привязка (binding) к объекту. Присваивание обычно не копирует объект, а связывает другое имя с тем же объектом. Если два имени ссылаются на один объект, возникает **aliasing**. Для изменяемых объектов это означает, что мутация через одно имя будет видна через другое.

**Идентичность (identity)** отвечает на вопрос: «Это один и тот же объект?». Оператор `is` проверяет идентичность. **Равенство (equality)** отвечает на вопрос: «Считаются ли эти объекты равными по смыслу?». Оператор `==` выполняет сравнение равенства, поведение которого может быть определено пользовательским классом через `__eq__`.

Два разных объекта могут быть равны, но не идентичны. Например, два отдельно созданных списка с одинаковыми элементами обычно удовлетворяют `a == b`, но `a is b` будет ложным. И наоборот, если `a` и `b` — два имени одного объекта, то они идентичны и обычно равны.

Практическое правило: используйте `is` для проверки идентичности с singleton-объектами, прежде всего `None`, например `value is None`. Для сравнения значений используйте `==`. Не следует использовать `is` для сравнения строк, чисел или других значений. Наблюдаемое совпадение идентичности некоторых литералов может быть следствием интернирования или оптимизаций реализации и не является корректным контрактом программы.

Встроенная функция `id()` возвращает целочисленный идентификатор, соответствующий идентичности объекта в течение времени его жизни. В CPython это обычно адрес объекта в памяти, но язык Python не гарантирует, что `id()` является адресом памяти. Идентификаторы могут повторно использоваться для объектов, время жизни которых не пересекается. Поэтому `id()` не следует применять как постоянный глобальный идентификатор или как механизм хранения ссылок.

**Контракт equality/hash** критически важен для словарей и множеств. Если два объекта сравниваются как равные, их хеши должны быть одинаковыми. Хеш объекта, находящегося в хеш-коллекции, должен оставаться стабильным. Поэтому класс, определяющий собственное равенство по изменяемым полям, должен осторожно относиться к хешированию. Если класс переопределяет `__eq__` без явного определения совместимого `__hash__`, Python обычно делает его экземпляры нехешируемыми. Нельзя проектировать `__hash__`, который зависит от состояния, меняющегося после помещения объекта в словарь или множество.

На Senior-уровне я проверяю, соответствует ли equality бизнес-семантике типа, стабильны ли поля, участвующие в сравнении и хешировании, и не создаёт ли aliasing скрытые побочные эффекты. Для идентичности использую `is`, для значения — `==`, а для ключей коллекций явно обеспечиваю контракт равенства и хеша.

### Эталонный ответ (EN)

In Python, it is important to distinguish **a name, an object, identity, and equality**.

A name is a binding to an object. Assignment usually does not copy the object; it binds another name to the same object. When two names refer to one object, we have **aliasing**. With mutable objects, a mutation made through one alias is visible through the other.

**Identity** answers: "Is this the very same object?" The `is` operator tests identity. **Equality** answers: "Are these objects considered equivalent in value or meaning?" The `==` operator performs an equality comparison, whose behaviour can be customized by a class through `__eq__`.

Two distinct objects can be equal without being identical. For example, two separately created lists with the same elements normally satisfy `a == b`, while `a is b` is false. Conversely, if `a` and `b` are two names bound to the same object, they are identical and normally equal.

As a practical rule, use `is` for identity checks against singletons, especially `None`, as in `value is None`. Use `==` for value comparisons. Do not use `is` to compare strings, numbers, or other values. Apparent identity between some literals may result from interning or implementation optimizations and is not a valid program-level guarantee.

The built-in `id()` function returns an integer identifying an object during its lifetime. In CPython, it is typically the object's memory address, but the Python language does not guarantee that `id()` is a memory address. IDs may be reused for objects whose lifetimes do not overlap. Therefore, `id()` should not be treated as a persistent global identifier or as a way to retain an object reference.

The **equality/hash contract** is essential for dictionaries and sets. If two objects compare equal, their hashes must be equal. An object's hash must remain stable while it is stored in a hash-based collection. A class that defines equality using mutable fields must therefore be careful about hashability. If a class overrides `__eq__` without explicitly providing a compatible `__hash__`, Python normally makes its instances unhashable. A hash implementation must not depend on state that can change while the object is used as a dictionary key or set member.

At Senior level, I check whether equality reflects the type's domain semantics, whether fields participating in equality and hashing are stable, and whether aliasing can introduce hidden side effects. I use `is` for identity, `==` for value equality, and enforce the equality/hash contract for objects used in hash-based collections.

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** Two lists contain the same elements. What do `==` and `is` tell you, and why?  
**RU:** Два списка содержат одинаковые элементы. Что покажут `==` и `is` и почему?

**Ответ (RU):** Если списки созданы отдельно, `==` обычно вернёт `True`, потому что сравнивается содержимое. `is` вернёт `False`, потому что это два разных объекта. Равенство не подразумевает идентичность.

**Answer (EN):** If the lists were created separately, `==` normally returns `True` because their contents are compared. `is` returns `False` because they are distinct objects. Equality does not imply identity.

#### FU-2

**EN:** Why should you write `value is None` instead of `value == None`?  
**RU:** Почему следует писать `value is None`, а не `value == None`?

**Ответ (RU):** `None` — singleton, поэтому проверка должна выражать именно идентичность с этим объектом. `==` может вызывать пользовательский `__eq__` и иметь переопределённую семантику. Идиоматичная и однозначная проверка — `is None` или `is not None`.

**Answer (EN):** `None` is a singleton, so the check should express identity with that exact object. `==` can invoke a custom `__eq__` implementation with different semantics. The idiomatic and unambiguous check is `is None` or `is not None`.

#### FU-3

**EN:** What is aliasing, and why can it create bugs with mutable objects?  
**RU:** Что такое aliasing и почему он может приводить к ошибкам при работе с изменяемыми объектами?

**Ответ (RU):** Aliasing возникает, когда несколько имён ссылаются на один объект. Мутация через любое из этих имён изменяет общий объект, поэтому другая часть программы может неожиданно увидеть изменение. Решения включают явное владение, копирование на границе владения или использование неизменяемых значений там, где это оправдано.

**Answer (EN):** Aliasing occurs when multiple names refer to the same object. A mutation through any of those names changes the shared object, so another part of the program may observe an unexpected change. Mitigations include explicit ownership, copying at ownership boundaries, or using immutable values where appropriate.

#### FU-4

**EN:** What invariant must hold between `__eq__` and `__hash__`?  
**RU:** Какой инвариант должен соблюдаться между `__eq__` и `__hash__`?

**Ответ (RU):** Если `a == b`, то `hash(a) == hash(b)` должно быть истинно. Обратное не обязательно: совпадение хешей не означает равенства из-за возможных коллизий. Хеш также должен оставаться стабильным, пока объект находится в словаре или множестве.

**Answer (EN):** If `a == b`, then `hash(a) == hash(b)` must hold. The reverse is not required because hash collisions are possible. The hash must also remain stable while the object is stored in a dictionary or set.

#### FU-5

**EN:** What happens to hashability when a class overrides `__eq__` but does not define `__hash__`?  
**RU:** Что происходит с хешируемостью класса, если он переопределяет `__eq__`, но не определяет `__hash__`?

**Ответ (RU):** По стандартному поведению Python такой класс становится нехешируемым: `__hash__` устанавливается в `None`. Это предотвращает случайное использование объектов с пользовательской семантикой равенства и потенциально несовместимым хешем в словарях и множествах. Если хеширование действительно требуется, нужно явно реализовать совместимый и стабильный `__hash__`.

**Answer (EN):** Under Python's standard behaviour, the class becomes unhashable: `__hash__` is set to `None`. This prevents objects with custom equality semantics and potentially incompatible hashing from being used accidentally in dictionaries and sets. If hashability is required, implement a compatible and stable `__hash__` explicitly.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** рассмотрим value objects, представляющие идентификаторы лекарств или нормализованные поисковые критерии. Equality должна отражать предполагаемую предметную идентичность, а не случайную идентичность объектов в памяти. Если такие объекты используются как ключи словарей или элементы множеств, поля equality и hash должны оставаться стабильными. Общие изменяемые фильтры также следует проверять на aliasing между этапами обработки запроса.

Не утверждайте, что конкретная модель Pharmaviyum реализует такую семантику, не проверив исходный код.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Использует `is` и `==` как взаимозаменяемые операторы; считает `id()` гарантированным адресом памяти. |
| Компетентный | Объясняет identity, equality, aliasing и причину проверки `None` через `is`. |
| Strong Senior | Объясняет пользовательское равенство, hash-инварианты, ограничения изменяемости, `__hash__ = None`, переносимость между реализациями и проектирование equality с учётом предметной области. |

### Типичные ошибки

- Использовать `is` для сравнения строк, чисел и произвольных значений.
- Считать, что равные объекты обязательно являются одним объектом.
- Считать `id()` постоянным адресом памяти или идентификатором.
- Игнорировать aliasing при передаче изменяемых объектов между слоями.
- Реализовывать `__hash__` несовместимо с `__eq__`.
- Хешировать изменяемое состояние, которое может измениться, пока объект используется как ключ словаря или элемент множества.

### Источники

- Python language reference — comparisons: https://docs.python.org/3/reference/expressions.html#comparisons
- Python data model — object identity and `id()`: https://docs.python.org/3/reference/datamodel.html
- Python data model — `__eq__` and `__hash__`: https://docs.python.org/3/reference/datamodel.html#object.__hash__
- Python glossary — hashable: https://docs.python.org/3/glossary.html#term-hashable

---

## PY-CORE-005 — Система типов Python и динамическая типизация

### Question (EN)

**Explain Python's type system. What do dynamic typing, strong typing, duck typing, type annotations, and structural subtyping mean, and how do you use them to build reliable backend services?**

### Перевод (RU)

**Объясните систему типов Python. Что означают динамическая типизация, строгая типизация, duck typing, аннотации типов и структурная подтипизация? Как применять эти концепции для создания надёжных backend-сервисов?**

### Что проверяет интервьюер

- Различие между динамической и строгой/слабой типизацией.
- Понимание того, что имена в Python связываются с объектами, типы которых определяются во время выполнения.
- Понимание duck typing и интерфейсов, основанных на поведении.
- Знание того, что аннотации типов автоматически не обеспечивают runtime-валидацию.
- Различие между статическим анализом, runtime-валидацией и runtime-интроспекцией.
- Понимание структурной типизации и `Protocol`.
- Умение выбирать EAFP или LBYL с учётом семантики операции и обработки ошибок.

### Эталонный ответ (RU)

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

В backend-сервисе я использую аннотации для контрактов между слоями, статический анализ в CI, runtime-валидацию на границах системы и тесты для проверки поведения. Например, FastAPI использует аннотации и модели для описания API, а Pydantic валидирует данные согласно объявленной схеме и конфигурации. Я не считаю аннотации безопасной границей или гарантией корректности входных данных: доверие к внешнему запросу должно устанавливаться явной runtime-валидацией и авторизацией.

### Эталонный ответ (EN)

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

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** Is Python dynamically typed, strongly typed, or both? Explain with an example.  
**RU:** Python — динамически типизированный, строго типизированный язык или и то и другое? Объясните на примере.

**Ответ (RU):** Обычно Python описывают как динамически и строго типизированный. Динамичность означает, что тип объекта определяется во время выполнения, а имя может быть связано с объектами разных типов. Строгость проявляется, например, в том, что операция сложения строки и целого числа без явного преобразования вызывает `TypeError`. Термины strong/weak требуют контекста, поэтому важнее объяснить фактическое поведение.

**Answer (EN):** Python is commonly described as both dynamically and strongly typed. Dynamic typing means an object's type is determined at runtime and a name can be rebound to objects of different types. Strong typing is illustrated by operations such as adding a string and an integer without explicit conversion raising `TypeError`. Since strong/weak terminology depends on context, explaining the actual behaviour is more useful than relying on the label.

#### FU-2

**EN:** Do Python type annotations validate untrusted HTTP request data at runtime?  
**RU:** Проверяют ли аннотации типов Python недоверенные данные HTTP-запроса во время выполнения?

**Ответ (RU):** Нет, сами по себе — нет. Аннотации в первую очередь служат описанием типов и входом для статических анализаторов и инструментов. Для внешних данных нужна runtime-валидация, например через Pydantic-модели в соответствующей точке приложения. Валидация также не заменяет авторизацию и проверку бизнес-правил.

**Answer (EN):** No, not by themselves. Annotations primarily describe types and provide input to static analyzers and tooling. External data requires runtime validation, for example through Pydantic models at the appropriate application boundary. Validation also does not replace authorization or business-rule checks.

#### FU-3

**EN:** What is the difference between duck typing and a typing `Protocol`?  
**RU:** В чём разница между duck typing и `Protocol` из модуля typing?

**Ответ (RU):** Duck typing — прежде всего runtime-подход: код использует объект на основании поддерживаемого поведения. `Protocol` формализует ожидаемую структуру для статической проверки типов и документирования интерфейса. Эти подходы совместимы: реализация может соответствовать протоколу структурно, без явного наследования. Обычная статическая совместимость с Protocol не означает автоматической runtime-валидации.

**Answer (EN):** Duck typing is primarily a runtime approach: code uses an object based on the behaviour it supports. A `Protocol` formalizes the expected structure for static type checking and interface documentation. The approaches are compatible: an implementation can satisfy a protocol structurally without explicit inheritance. Static compatibility with a Protocol does not imply automatic runtime validation.

#### FU-4

**EN:** When would you choose EAFP over LBYL, and what concurrency concern should you consider?  
**RU:** Когда вы выберете EAFP вместо LBYL и какой concurrency-риск нужно учитывать?

**Ответ (RU):** EAFP подходит, когда операция сама надёжно проверяет условие и ожидаемое исключение можно обработать локально, например при чтении ключа словаря. LBYL полезен для предварительной проверки и более понятного сообщения об ошибке. Но между проверкой и действием состояние может измениться: это TOCTOU race condition. Если операция должна быть атомарной, предпочтительнее использовать атомарную операцию или синхронизацию.

**Answer (EN):** EAFP is appropriate when the operation itself reliably tests the condition and the expected exception can be handled locally, such as dictionary key access. LBYL can help with precondition checks and clearer error messages. However, state may change between the check and the action, creating a time-of-check-to-time-of-use race. If the operation must be atomic, prefer an atomic operation or synchronization.

#### FU-5

**EN:** What does `@runtime_checkable` add to a `Protocol`, and what does it not guarantee?  
**RU:** Что даёт декоратор `@runtime_checkable` протоколу `Protocol` и чего он не гарантирует?

**Ответ (RU):** Он позволяет выполнять ограниченную проверку соответствия протоколу во время выполнения через `isinstance()`. Такая проверка ориентирована на наличие требуемых атрибутов, а не на полноценную проверку типов параметров, возвращаемых значений или семантики методов. Поэтому она не заменяет статический анализ, runtime-валидацию данных или тестирование контракта.

**Answer (EN):** It enables a limited runtime protocol check through `isinstance()`. The check focuses on the presence of required attributes rather than fully validating parameter types, return types, or method semantics. It therefore does not replace static analysis, runtime data validation, or contract testing.

### Связь с Pharmaviyum

**Подтверждённый контекст стека:** в документированном стеке Pharmaviyum используются FastAPI, Pydantic и SQLModel. Далее приведено архитектурное применение этих технологий, а не утверждение, что каждый пример уже реализован.

На границе API request-модели могут описывать и валидировать входные данные. Аннотации типов делают явными контракты сервисных слоёв, а статический анализ помогает находить несоответствия между модулями. Protocol может описывать порты для внешних сервисов или инфраструктурных адаптеров, не связывая бизнес-логику с конкретной реализацией. Авторизация и доменные инварианты должны оставаться явными: прохождение schema validation автоматически не означает, что операция разрешена или клинически корректна.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Утверждает, что аннотации обеспечивают runtime-проверку типов; путает динамическую типизацию с отсутствием типов. |
| Компетентный | Объясняет динамическую и строгую типизацию, duck typing и разницу между аннотациями и валидацией. |
| Strong Senior | Разделяет статический анализ, runtime-валидацию и интроспекцию; осознанно использует Protocol; анализирует EAFP/LBYL, race conditions и границы доверия. |

### Типичные ошибки

- Называть Python слабо типизированным только потому, что он динамически типизирован.
- Считать аннотации типов автоматической runtime-валидацией.
- Предполагать, что `isinstance()` или `@runtime_checkable` полностью проверяет контракт Protocol.
- Использовать проверки конкретного класса там, где интерфейс на основе поведения уменьшил бы связанность.
- Перехватывать слишком широкие исключения в EAFP и скрывать ошибки программирования.
- Считать, что LBYL-проверка гарантирует корректность последующей операции.
- Приравнивать schema validation к авторизации или проверке доменных правил.

### Источники

- Python typing documentation: https://docs.python.org/3/library/typing.html
- Python typing — Protocols: https://docs.python.org/3/library/typing.html#typing.Protocol
- Python function annotations: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- mypy documentation: https://mypy.readthedocs.io/
- Pyright documentation: https://github.com/microsoft/pyright
- Pydantic documentation: https://docs.pydantic.dev/
- Python glossary — duck typing: https://docs.python.org/3/glossary.html#term-duck-typing

---

## PY-CORE-006 — Модель данных Python и специальные методы

### Question (EN)

**Explain Python's data model and the role of special methods (dunder methods). How does Python use them to provide object construction, representation, iteration, operators, truth testing, and context management?**

### Перевод (RU)

**Объясните модель данных Python и роль специальных методов (dunder methods). Как Python использует их для создания объектов, представления, итерации, операторов, проверки истинности и управления контекстом?**

### Что проверяет интервьюер

- Понимание того, что специальные методы реализуют протоколы, встроенные в язык.
- Различие между созданием объекта через `__new__` и инициализацией через `__init__`.
- Знание того, почему поиск специальных методов может обходить обычный поиск атрибутов экземпляра.
- Умение проектировать полезные реализации `__repr__` и `__str__`.
- Понимание протоколов итерации и контейнеров.
- Понимание проверки истинности и перегрузки операторов.
- Корректная реализация очистки ресурсов и распространения исключений в context manager.
- Умение избегать неожиданного и противоречивого поведения пользовательских классов.

### Эталонный ответ (RU)

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

### Эталонный ответ (EN)

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

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** What is the difference between `__new__` and `__init__`?  
**RU:** В чём разница между `__new__` и `__init__`?

**Ответ (RU):** `__new__` создаёт и возвращает экземпляр, а `__init__` инициализирует уже созданный экземпляр и возвращает `None`. `__new__` особенно важен для неизменяемых типов и нестандартного контроля создания объектов. В обычных классах чаще достаточно `__init__`.

**Answer (EN):** `__new__` creates and returns an instance, while `__init__` initializes an already-created instance and returns `None`. `__new__` is particularly relevant for immutable types and specialized instance-creation control. For ordinary classes, `__init__` is usually sufficient.

#### FU-2

**EN:** Why might assigning `obj.__len__` not affect the result of `len(obj)`?  
**RU:** Почему присваивание `obj.__len__` может не повлиять на результат `len(obj)`?

**Ответ (RU):** Специальные методы для неявных языковых операций обычно ищутся на уровне типа, а не через обычный поиск атрибутов экземпляра. Поэтому изменение одноимённого атрибута конкретного экземпляра не обязано менять поведение встроенной операции. Протокол следует реализовывать в классе.

**Answer (EN):** Special methods used by implicit language operations are generally looked up on the type rather than through ordinary instance attribute lookup. Changing a same-named attribute on one instance therefore does not necessarily change the built-in operation. The protocol should be implemented on the class.

#### FU-3

**EN:** What is the difference between an iterable and an iterator?  
**RU:** Чем iterable отличается от iterator?

**Ответ (RU):** Iterable предоставляет итератор через `__iter__`. Iterator реализует `__next__`, хранит состояние обхода и обычно возвращает себя из `__iter__`. Один iterable может создавать несколько независимых итераторов, тогда как конкретный iterator обычно потребляется по мере обхода.

**Answer (EN):** An iterable provides an iterator through `__iter__`. An iterator implements `__next__`, maintains traversal state, and normally returns itself from `__iter__`. One iterable can create multiple independent iterators, while a particular iterator is usually consumed as it is traversed.

#### FU-4

**EN:** What is the difference between returning `NotImplemented` and raising `NotImplementedError` in an overloaded operator?  
**RU:** В чём разница между возвратом `NotImplemented` и выбрасыванием `NotImplementedError` в перегруженном операторе?

**Ответ (RU):** `NotImplemented` — специальное значение, сообщающее механизму диспетчеризации Python, что данный операнд не поддерживает эту операцию; интерпретатор может попробовать reflected-метод второго операнда. `NotImplementedError` — обычное исключение, сигнализирующее, что реализация не выполнена. Для неподдерживаемого сочетания типов в operator overloading обычно используют `NotImplemented`, а не исключение.

**Answer (EN):** `NotImplemented` is a special value telling Python's dispatch machinery that this operand does not support the operation; the interpreter may try the other operand's reflected method. `NotImplementedError` is an exception indicating that an implementation has not been provided. For an unsupported operand combination in operator overloading, returning `NotImplemented` is normally appropriate.

#### FU-5

**EN:** When does a context manager suppress an exception?  
**RU:** В каком случае context manager подавляет исключение?

**Ответ (RU):** Если исключение возникло внутри блока `with`, Python передаёт сведения о нём в `__exit__`. Если `__exit__` возвращает truthy value, исключение подавляется; если возвращает falsey value или `None`, исключение продолжает распространяться. Подавлять исключения следует только тогда, когда это явно соответствует контракту контекстного менеджера.

**Answer (EN):** If an exception occurs inside a `with` block, Python passes its details to `__exit__`. If `__exit__` returns a truthy value, the exception is suppressed; if it returns a falsey value or `None`, the exception propagates. Exceptions should be suppressed only when that behaviour is explicitly part of the context manager's contract.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** сессия базы данных или адаптер внешнего ресурса может предоставлять context-manager semantics, чтобы получение и освобождение ресурса были явными и безопасными при исключениях. Коллекция лекарств или объект результатов поиска могут реализовывать протоколы итерации и длины, если такое поведение входит в их публичный контракт. Представление объекта должно помогать диагностике, не раскрывая данные пациентов, учётные данные и другие чувствительные значения.

Не утверждайте, что конкретный класс Pharmaviyum реализует эти протоколы, не проверив исходный код.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Перечисляет dunder methods, но путает создание объекта с инициализацией или `NotImplemented` с `NotImplementedError`. |
| Компетентный | Корректно объясняет создание, представление, итерацию, truthiness, операторы и context managers. |
| Strong Senior | Объясняет dispatch протоколов, инварианты, состояние итератора, подавление исключений, безопасность ресурсов и безопасные представления; выбирает протоколы на основе явных API-контрактов. |

### Типичные ошибки

- Возвращать значение, отличное от `None`, из `__init__`.
- Использовать `__init__`, когда для нестандартного создания объекта нужен `__new__`.
- Считать, что поиск специальных методов всегда использует словарь атрибутов экземпляра.
- Возвращать отрицательное или нецелое значение из `__len__`.
- Путать iterable и iterator.
- Выбрасывать `StopIteration` до завершения итерации или не выбрасывать его после исчерпания.
- Выбрасывать `NotImplementedError` вместо возврата `NotImplemented` для неподдерживаемой перегрузки оператора.
- Случайно подавлять исключения в `__exit__`.
- Раскрывать секреты или персональные данные через `__repr__` или `__str__`.

### Источники

- Python data model: https://docs.python.org/3/reference/datamodel.html
- Python built-in functions — `len()`, `iter()`, `next()`: https://docs.python.org/3/library/functions.html
- Iterator types: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Context manager types: https://docs.python.org/3/library/stdtypes.html#typecontextmanager
- PEP 343 — The "with" statement: https://peps.python.org/pep-0343/

---

## PY-CORE-007 — Области видимости Python, правило LEGB, closures и namespaces

### Question (EN)

**Explain how Python resolves names. Describe the LEGB rule, the roles of `global` and `nonlocal`, how closures retain state, and why late binding can cause bugs.**

### Перевод (RU)

**Объясните, как Python разрешает имена. Расскажите о правиле LEGB, назначении `global` и `nonlocal`, о том, как closures сохраняют состояние, и почему late binding может приводить к ошибкам.**

### Что проверяет интервьюер

- Точное понимание различий между namespace и scope.
- Умение объяснить порядок поиска LEGB и обращение к built-ins.
- Понимание того, что присваивание влияет на классификацию имени как локального на этапе анализа функции.
- Корректное различие между `global` и `nonlocal`.
- Понимание closure cells и лексической области видимости.
- Умение диагностировать `UnboundLocalError` и late-binding behaviour.
- Понимание последствий для декораторов и вложенных функций.
- Умение проектировать предсказуемый и тестируемый код без случайно разделяемого состояния.

### Эталонный ответ (RU)

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

### Эталонный ответ (EN)

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

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** Why can reading a module-level variable inside a function raise `UnboundLocalError` if the function assigns to the same name later?  
**RU:** Почему чтение переменной уровня модуля внутри функции может вызвать `UnboundLocalError`, если позднее в этой функции выполняется присваивание тому же имени?

**Ответ (RU):** Наличие присваивания имени внутри функции обычно приводит к тому, что Python классифицирует это имя как локальное во всей функции на этапе анализа кода. Поэтому чтение до локального присваивания обращается к ещё не связанному локальному имени, а не к одноимённому имени модуля. Если намерение действительно состоит в изменении module-level binding, требуется декларация `global`; чаще лучше передать значение явно.

**Answer (EN):** An assignment to a name anywhere in a function generally causes Python to classify that name as local throughout the function during code analysis. A read before the local assignment therefore accesses an unbound local name rather than the same-named module variable. If changing the module-level binding is truly intended, `global` is required; explicit parameter passing is often a better design.

#### FU-2

**EN:** What is the difference between `global` and `nonlocal`?  
**RU:** В чём разница между `global` и `nonlocal`?

**Ответ (RU):** `global` направляет присваивание в namespace текущего модуля. `nonlocal` направляет его в ближайшую enclosing function scope, где имя уже связано. `nonlocal` применяется к вложенным функциям и не работает как способ изменить переменную модуля.

**Answer (EN):** `global` directs assignment to the current module namespace. `nonlocal` directs assignment to the nearest enclosing function scope where the name is already bound. It is used by nested functions and is not a way to modify a module variable.

#### FU-3

**EN:** Does a closure capture a value or a variable binding?  
**RU:** Closure захватывает значение или binding переменной?

**Ответ (RU):** Концептуально closure сохраняет доступ к binding в enclosing scope, а не обязательно копию значения на момент создания функции. Поэтому последующее изменение binding через `nonlocal` может быть видно при вызове closure. Если binding указывает на mutable object, изменения самого объекта также будут наблюдаемы.

**Answer (EN):** Conceptually, a closure retains access to a binding in an enclosing scope, not necessarily a copy of the value at function-creation time. Rebinding through `nonlocal` can therefore be observed when the closure is called. If the binding refers to a mutable object, mutations to that object are observable as well.

#### FU-4

**EN:** Why do functions created in a loop often exhibit late-binding behaviour, and how can you avoid it?  
**RU:** Почему функции, созданные в цикле, часто демонстрируют late binding и как этого избежать?

**Ответ (RU):** Вложенные функции обычно разрешают имя переменной цикла во время вызова. Если все функции замыкают одно и то же имя, они могут увидеть его итоговое значение. Можно использовать default argument для фиксации текущего binding, фабрику функций или отдельную enclosing scope. При использовании default argument нужно помнить, что значение по умолчанию вычисляется один раз при определении функции.

**Answer (EN):** Nested functions normally resolve the loop variable when they are called. If all functions close over the same name, they may observe its final value. A default argument can capture the current binding, or a function factory can create a separate enclosing scope. Remember that a default argument expression is evaluated once when the function is defined.

#### FU-5

**EN:** Why should mutable state captured by a decorator or closure be treated carefully in a web application?  
**RU:** Почему к изменяемому состоянию, захваченному декоратором или closure, нужно относиться осторожно в веб-приложении?

**Ответ (RU):** Wrapper, созданный декоратором, часто является одним объектом функции, который вызывается множеством запросов. Изменяемое состояние в его closure может разделяться между запросами, что создаёт риск утечки контекста, гонок данных и недетерминированного поведения. Состояние запроса следует хранить в request-scoped dependency или другом объекте с корректным жизненным циклом, а не в общем closure без синхронизации и чёткого контракта.

**Answer (EN):** A decorator-created wrapper is often a single function object invoked by many requests. Mutable state in its closure may therefore be shared across requests, creating risks of context leakage, race conditions, and nondeterministic behaviour. Request-specific state should live in a request-scoped dependency or another correctly scoped object, not in a shared closure without synchronization and an explicit contract.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** FastAPI dependency или декоратор могут замыкать неизменяемую конфигурацию приложения, тогда как request-specific identity, authorization context и состояние database session должны передаваться через зависимости с request scope. Общее closure с изменяемыми данными пациента или запроса было бы небезопасным решением: параллельные запросы могли бы наблюдать состояние друг друга.

Любое утверждение о том, что текущий компонент Pharmaviyum использует конкретный closure, decorator или dependency scope, должно быть подтверждено исходным кодом и тестами.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Повторяет LEGB, но не объясняет `UnboundLocalError` или считает `global` и `nonlocal` взаимозаменяемыми. |
| Компетентный | Корректно объясняет LEGB, rebinding, closures и late binding. |
| Strong Senior | Связывает lexical scope с closure cells, состоянием декораторов, жизненным циклом запросов, concurrency, изоляцией тестов и явным проектированием зависимостей. |

### Типичные ошибки

- Считать global областью всего процесса, а не namespace модуля.
- Полагать, что имя глобальное только потому, что объявлено вне функции.
- Забывать, что присваивание может сделать имя локальным во всей функции.
- Путать `NameError` с более конкретным `UnboundLocalError`.
- Использовать `nonlocal`, когда во внешней функциональной области нет соответствующего binding.
- Считать, что closures всегда захватывают неизменяемые снимки значений.
- Не замечать late binding в функциях, созданных внутри циклов.
- Хранить request-specific данные в общем изменяемом closure веб-сервера.
- Забывать, что default argument expressions вычисляются один раз при определении функции.
- Предполагать, что атрибуты класса автоматически становятся лексическими переменными методов.

### Источники

- Python execution model — naming and binding: https://docs.python.org/3/reference/executionmodel.html
- `global` statement: https://docs.python.org/3/reference/simple_stmts.html#the-global-statement
- `nonlocal` statement: https://docs.python.org/3/reference/simple_stmts.html#the-nonlocal-statement
- Function definitions and default parameter values: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- PEP 227 — Statically Nested Scopes: https://peps.python.org/pep-0227/
- `functools.wraps`: https://docs.python.org/3/library/functools.html#functools.wraps

---

## PY-CORE-008 — Функции Python, декораторы и функциональное программирование

### Question (EN)

**Explain Python's first-class functions and higher-order functions. How do decorators work, and what are the benefits and trade-offs of functional programming techniques such as pure functions, composition, `map`, `filter`, `reduce`, and caching?**

### Перевод (RU)

**Объясните концепции first-class functions и higher-order functions в Python. Как работают декораторы и каковы преимущества и компромиссы функционального программирования: pure functions, композиция, `map`, `filter`, `reduce` и caching?**

### Что проверяет интервьюер

- Понимание функций как объектов первого класса.
- Умение отличать first-class functions от higher-order functions.
- Понимание момента применения декораторов и порядка их вызова.
- Корректное использование decorator factories, сохранения метаданных и контрактов callable.
- Умение рассуждать о closures, композиции функций и partial application.
- Понимание ленивых итераторов, возвращаемых `map` и `filter`.
- Уместное использование `reduce`, а не его применение к любой агрегации.
- Понимание purity, side effects, referential transparency и тестируемости.
- Понимание ключей кеша, удержания памяти, инвалидации и concurrency.

### Эталонный ответ (RU)

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

### Эталонный ответ (EN)

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

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** What is the difference between a first-class function and a higher-order function?  
**RU:** В чём разница между first-class function и higher-order function?

**Ответ (RU):** First-class описывает свойства функций как объектов: их можно передавать, возвращать и сохранять как значения. Higher-order описывает конкретную функцию, которая принимает функцию аргументом или возвращает функцию. Это разные уровни описания: первое — свойство языка, второе — характеристика операции.

**Answer (EN):** First-class describes functions as values: they can be passed, returned, and stored. Higher-order describes a particular function that accepts a function as an argument or returns one. They are different levels of description: one is a language property, the other characterizes a function's behaviour.

#### FU-2

**EN:** When is a decorator evaluated, and how does stacking order work?  
**RU:** Когда выполняется декоратор и как работает порядок нескольких декораторов?

**Ответ (RU):** Декоратор применяется при выполнении определения функции. При записи нескольких декораторов ближайший к `def` применяется первым, затем его результат оборачивает следующий, внешний декоратор. Поэтому изменение порядка может менять семантику, например границы кеширования, логирования или транзакции.

**Answer (EN):** A decorator is applied when the function definition executes. With stacked decorators, the one closest to `def` is applied first, and each outer decorator then wraps the previous result. Changing the order can therefore change semantics, such as caching, logging, or transaction boundaries.

#### FU-3

**EN:** Why should a decorator usually use `functools.wraps`?  
**RU:** Почему декоратор обычно должен использовать `functools.wraps`?

**Ответ (RU):** `wraps` копирует важные метаданные исходной функции на wrapper и устанавливает `__wrapped__`. Это помогает документации, отладчикам, introspection и инструментам, которые исследуют исходную функцию. При этом `wraps` не делает wrapper автоматически идентичным исходной функции по поведению или реальной сигнатуре вызова.

**Answer (EN):** `wraps` copies important metadata from the wrapped function to the wrapper and sets `__wrapped__`. This helps documentation, debuggers, introspection, and tools that inspect the original callable. It does not make the wrapper automatically identical to the original function in behaviour or actual call signature.

#### FU-4

**EN:** When would you choose a comprehension over `map` and `filter`, or a built-in aggregation over `reduce`?  
**RU:** Когда предпочтительнее comprehension вместо `map` и `filter`, или встроенная агрегирующая функция вместо `reduce`?

**Ответ (RU):** Для простых преобразований comprehension часто читается естественнее и позволяет выразить фильтрацию и преобразование в одном месте. Для стандартных агрегатов вроде суммы, минимума или максимума специализированные built-ins яснее выражают намерение и обычно эффективнее. `map`, `filter` и `reduce` полезны, когда они делают преобразование или свёртку понятнее, а не просто заменяют более идиоматичный синтаксис.

**Answer (EN):** For simple transformations, comprehensions are often more readable and can express filtering and transformation together. Dedicated built-ins for common aggregates such as sum, minimum, or maximum communicate intent more clearly and are often more efficient. Use `map`, `filter`, and `reduce` when they make the transformation or fold clearer, not merely to replace more idiomatic syntax.

#### FU-5

**EN:** What risks arise when using `lru_cache` for functions that depend on mutable or external state?  
**RU:** Какие риски возникают при использовании `lru_cache` для функций, зависящих от изменяемого или внешнего состояния?

**Ответ (RU):** Кеш может вернуть устаревший результат, потому что изменение внешнего состояния не отражается в ключе. Аргументы должны быть hashable, а кеш удерживает ссылки на ключи и результаты до вытеснения или очистки. Нужно определить TTL или инвалидацию, ограничить размер и проверить, допустимо ли разделение результата между пользователями и запросами. Для нескольких процессов потребуется отдельное решение распределённого кеширования.

**Answer (EN):** The cache may return stale data because changes in external state are not represented in the key. Arguments must be hashable, and the cache retains references to keys and results until eviction or clearing. Define a TTL or invalidation strategy, bound the cache size, and verify whether sharing results across users and requests is safe. Multiple processes require a separate distributed-caching solution.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** pure functions могут нормализовать поисковый запрос лекарства или преобразовывать валидированные доменные данные; decorators могут добавлять structured logging или timing на границах сервисов; caching можно рассматривать для справочных данных только после определения tenant/user isolation, состава ключа, актуальности и инвалидации. Request-specific authorization и patient context не должны случайно разделяться через общий function cache или изменяемое closure декоратора.

Любое утверждение о том, что эти паттерны уже реализованы в Pharmaviyum, должно быть подтверждено репозиторием и тестами.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Знает синтаксис декораторов, но не может объяснить момент их выполнения, поведение wrapper или ленивую итерацию. |
| Компетентный | Объясняет first-class и higher-order functions, порядок декораторов, pure functions и базовое кеширование. |
| Strong Senior | Оценивает callable contracts, метаданные, границы side effects, корректность и инвалидацию кеша, async limitations, concurrency и изоляцию данных. |

### Типичные ошибки

- Считать first-class и higher-order functions синонимами.
- Предполагать, что декоратор выполняется при каждом вызове декорируемой функции.
- Перепутать порядок применения нескольких декораторов.
- Не использовать `functools.wraps` и нарушать introspection.
- Создавать wrapper, который случайно меняет семантику исключений или возвращаемых значений.
- Забывать, что `map` и `filter` в Python 3 возвращают ленивые итераторы.
- Использовать `reduce`, когда есть понятная встроенная функция.
- Называть функцию pure, хотя она читает скрытое состояние или выполняет side effects.
- Кешировать результаты, зависящие от времени, состояния БД, авторизации или tenant context, не учитывая эти измерения в ключе.
- Считать `lru_cache` распределённым кешем или механизмом общей инвалидации приложения.
- Применять обычный `lru_cache` к async-функциям, ожидая кеширования результата после await.

### Источники

- Python tutorial — functional programming tools: https://docs.python.org/3/howto/functional.html
- Function definitions and decorators: https://docs.python.org/3/reference/compound_stmts.html#function-definitions
- `functools`: https://docs.python.org/3/library/functools.html
- `functools.wraps`: https://docs.python.org/3/library/functools.html#functools.wraps
- `functools.partial`: https://docs.python.org/3/library/functools.html#functools.partial
- `functools.reduce`: https://docs.python.org/3/library/functools.html#functools.reduce
- `functools.lru_cache`: https://docs.python.org/3/library/functools.html#functools.lru_cache

---

## PY-CORE-009 — Итераторы Python, генераторы и ленивые вычисления

### Question (EN)

**Explain the iterable and iterator protocols in Python. How do generators work, what does lazy evaluation mean, and how do you use generator lifecycle controls and streaming safely in backend systems?**

### Перевод (RU)

**Объясните протоколы iterable и iterator в Python. Как работают генераторы, что означает lazy evaluation и как безопасно использовать управление жизненным циклом генератора и streaming в backend-системах?**

### Что проверяет интервьюер

- Точное различие между iterable и iterator.
- Понимание `iter()`, `next()`, `__iter__()` и `__next__()`.
- Семантика generator functions и generator expressions.
- Ленивое выполнение, приостановка и возобновление.
- Корректное применение `yield from`.
- Понимание `send()`, `throw()` и `close()`.
- Освобождение ресурсов и финализация генераторов.
- Характеристики памяти и одноразовое потребление.
- Streaming, backpressure, cancellation и обработка ошибок в backend-системах.

### Эталонный ответ (RU)

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

### Эталонный ответ (EN)

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

### Follow-up questions и эталонные ответы

#### FU-1

**EN:** What is the difference between an iterable and an iterator?  
**RU:** В чём разница между iterable и iterator?

**Ответ (RU):** Iterable предоставляет способ получить итератор через `iter()`. Iterator хранит состояние текущего обхода, реализует `__next__()` и возвращает себя из `__iter__()`. Коллекция обычно может создавать новые итераторы, тогда как конкретный iterator обычно продвигается вперёд и исчерпывается.

**Answer (EN):** An iterable provides a way to obtain an iterator through `iter()`. An iterator stores traversal state, implements `__next__()`, and returns itself from `__iter__()`. A collection can usually create new iterators, while a particular iterator normally advances and becomes exhausted.

#### FU-2

**EN:** When does a generator function execute, and what happens when it returns?  
**RU:** Когда выполняется generator function и что происходит при её завершении через return?

**Ответ (RU):** Вызов generator function создаёт generator iterator, но тело функции начинает выполняться при первом запросе элемента. Выполнение приостанавливается на `yield` и продолжается при следующем запросе. При завершении `return value` приводит к `StopIteration`, а возвращённое значение доступно как `StopIteration.value`; оно не становится элементом потока.

**Answer (EN):** Calling a generator function creates a generator iterator, but the body starts executing when an item is first requested. Execution suspends at `yield` and resumes on the next request. On completion, `return value` results in `StopIteration`, with the returned value available as `StopIteration.value`; it is not emitted as a stream item.

#### FU-3

**EN:** How do `send()`, `throw()`, and `close()` differ?  
**RU:** Чем отличаются `send()`, `throw()` и `close()`?

**Ответ (RU):** `send()` передаёт значение в приостановленное выражение `yield` и возобновляет выполнение. `throw()` внедряет исключение в точку приостановки. `close()` инициирует завершение через `GeneratorExit`, позволяя выполнить cleanup в `finally`. Новый генератор нельзя начинать с ненулевого значения в `send()`: сначала его нужно продвинуть через `next()` или `send(None)`.

**Answer (EN):** `send()` supplies a value to the suspended `yield` expression and resumes execution. `throw()` injects an exception at the suspension point. `close()` initiates termination through `GeneratorExit`, allowing cleanup in `finally`. A new generator cannot be started by sending a non-None value; advance it first with `next()` or `send(None)`.

#### FU-4

**EN:** Why is relying on garbage collection to close a generator's resources unsafe?  
**RU:** Почему небезопасно полагаться на garbage collection для закрытия ресурсов генератора?

**Ответ (RU):** Момент освобождения объекта зависит от реализации и жизненного цикла ссылок; он не должен быть контрактом управления ресурсами. Генератор может остаться удержанным ссылкой или завершиться позже ожидаемого. Используйте явное закрытие, context manager и `try/finally`, чтобы файл, cursor или другой ресурс освобождался даже при раннем выходе или исключении.

**Answer (EN):** Object finalization timing depends on implementation and reference lifetimes; it should not be the resource-management contract. A generator may remain referenced or be finalized later than expected. Use explicit closure, a context manager, and `try/finally` so a file, cursor, or other resource is released even on early exit or an exception.

#### FU-5

**EN:** Does using a generator guarantee bounded memory and end-to-end backpressure in an HTTP streaming endpoint?  
**RU:** Гарантирует ли генератор ограниченное потребление памяти и end-to-end backpressure в HTTP streaming endpoint?

**Ответ (RU):** Нет. Генератор выдаёт элементы постепенно, но другие слои могут буферизовать данные: драйвер БД, сериализатор, ASGI server, reverse proxy или сетевой стек. Нужно проверять поведение всей цепочки, ограничивать размер страниц и буферов, обрабатывать медленных клиентов, отмену и таймауты, а также гарантировать закрытие ресурсов.

**Answer (EN):** No. A generator yields incrementally, but other layers may buffer data: the database driver, serializer, ASGI server, reverse proxy, or network stack. Validate the entire pipeline, bound page and buffer sizes, handle slow clients, cancellation, and timeouts, and guarantee resource cleanup.

### Связь с Pharmaviyum

**Гипотетический сценарий для интервью — не утверждение о текущей реализации:** экспорт каталога лекарств или большой результат поиска можно обрабатывать постепенно, а не материализовать в один большой список. Если генератор передаёт строки из БД, database session и cursor должны оставаться действительными в течение жизни потока и закрываться при завершении, отключении клиента или ошибке. Production-дизайн также должен определять pagination или лимиты строк, проверки авторизации, поведение при отмене и буферизацию на HTTP-уровнях.

Любое утверждение о том, что Pharmaviyum уже использует streaming endpoints или generator-based доступ к БД, должно быть подтверждено исходным кодом и тестами.

### Критерии оценки уровня Senior

| Уровень | Ожидаемые признаки |
|---|---|
| Слабый | Путает iterable и iterator или считает, что тело генератора выполняется сразу при вызове. |
| Компетентный | Объясняет приостановку генератора, lazy evaluation, `StopIteration` и базовое освобождение ресурсов. |
| Strong Senior | Рассуждает о владении ресурсами, раннем завершении, cleanup async generators, буферизации, backpressure, cancellation и ограничении памяти во всём backend pipeline. |

### Типичные ошибки

- Считать любой iterable итератором.
- Предполагать, что генератор можно перезапустить после исчерпания.
- Считать, что выполнение generator function начинается при вызове.
- Забывать, что ошибки ленивого источника могут возникнуть во время итерации.
- Путать return-значение генератора с элементом, выданным через yield.
- Вызывать `send(value)` до первого продвижения нового генератора.
- Считать `close()` заменой ясному контракту владения ресурсом.
- Полагаться на garbage collection для закрытия файлов или database cursors.
- Предполагать, что использование генератора само по себе гарантирует bounded memory.
- Предполагать, что synchronous generator гарантирует end-to-end HTTP backpressure.
- Игнорировать cancellation, медленных потребителей, таймауты и отключение клиента.

### Источники

- Python glossary — iterable and iterator: https://docs.python.org/3/glossary.html
- Iterator Types: https://docs.python.org/3/library/stdtypes.html#iterator-types
- Generator-iterator methods: https://docs.python.org/3/reference/expressions.html#generator-iterator-methods
- Yield expressions and `yield from`: https://docs.python.org/3/reference/expressions.html#yield-expressions
- Generator expressions: https://docs.python.org/3/reference/expressions.html#generator-expressions
- `contextlib`: https://docs.python.org/3/library/contextlib.html
- Asynchronous generator functions: https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions


## PY-CORE-010 — Обработка исключений Python и пользовательские исключения

### Вопрос для собеседования

Объясните модель исключений Python и то, как вы проектируете обработку ошибок в production backend. Раскройте иерархию исключений, назначение `try`, `except`, `else` и `finally`, распространение и связывание исключений, собственные классы исключений, группы исключений и границу между domain errors и HTTP-ответами.

### What the interviewer evaluates / Что оценивает интервьюер

- Понимание иерархии исключений Python и различий между `BaseException` и `Exception`.
- Точное понимание control flow конструкции `try/except/else/finally`.
- Умение сохранять причинно-следственную информацию через exception chaining.
- Проектирование осмысленной и стабильной иерархии пользовательских исключений.
- Корректная обработка узких типов исключений и гарантии cleanup.
- Понимание `ExceptionGroup` и `except*` в concurrent/task-group сценариях.
- Разделение domain, application, infrastructure и transport concerns.
- Production-практики: безопасное логирование, observability, redaction, retries и стабильные клиентские ошибки.

### Эталонный ответ (RU)

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

### Follow-up Questions and Answers / Дополнительные вопросы и ответы

**FU-1 — Why is catching `BaseException` usually a design error? / Почему перехват `BaseException` обычно является ошибкой проектирования?**

RU: Потому что `BaseException` включает не только обычные ошибки приложения, но и управляющие сигналы вроде `KeyboardInterrupt` и `SystemExit`. Перехват такого базового класса может помешать остановке процесса. В обычном application code следует перехватывать `Exception` или конкретный подкласс. Узкое использование `BaseException` допустимо только в специализированном коде инфраструктуры, который действительно обязан выполнить cleanup и затем корректно повторно поднять исключение.

EN: Because `BaseException` also includes process-control signals such as `KeyboardInterrupt` and `SystemExit`. Catching it broadly can prevent normal process termination. Application code should generally catch `Exception` or a specific subclass. Specialized infrastructure code may need broader handling for cleanup, but it must preserve and re-raise control-flow signals correctly.

**FU-2 — What is the practical difference between `raise`, `raise exc`, and `raise NewError(...) from exc`? / В чём практическая разница между этими формами raise?**

RU: Голый `raise` внутри обработчика повторно поднимает текущее исключение, сохраняя исходный traceback. `raise exc` явно поднимает объект исключения заново и может изменить traceback, добавив текущую точку. `raise NewError(...) from exc` создаёт исключение более высокого уровня и явно сохраняет исходную ошибку как причину. Для прозрачного повторного проброса предпочтителен голый `raise`.

EN: A bare `raise` re-raises the active exception and preserves its traceback. `raise exc` raises the exception object explicitly and can alter the traceback by adding the current raise location. `raise NewError(...) from exc` translates the failure while explicitly retaining the original exception as its cause. Use bare `raise` when the intent is simply to propagate the same exception.

**FU-3 — When should an exception be translated, and when should it propagate unchanged? / Когда исключение следует преобразовать, а когда — передать без изменений?**

RU: Переводить исключение следует на границе абстракции, когда нижний слой сообщает детали реализации, которые не должны протекать выше. Например, ошибка драйвера PostgreSQL может быть преобразована в инфраструктурную или application-level ошибку с сохранением причины. Если текущий слой не может восстановиться, классифицировать или осмысленно преобразовать ошибку, лучше позволить ей распространиться. Нельзя превращать все ошибки в один общий тип и терять возможность различать retryable и permanent failures.

EN: Translate an exception at an abstraction boundary when a lower layer exposes implementation-specific details that should not leak upward. For example, a PostgreSQL driver error may become an infrastructure or application-level exception while retaining its cause. If a layer cannot recover from, classify, or meaningfully translate the failure, it should generally propagate unchanged. Do not collapse all failures into one generic type, because callers may need to distinguish transient from permanent errors.

**FU-4 — How do `ExceptionGroup` and `except*` differ from ordinary exception handling? / Чем `ExceptionGroup` и `except*` отличаются от обычной обработки исключений?**

RU: Обычный `except` выбирает обработчик для одного поднятого исключения по его типу. `ExceptionGroup` содержит несколько исключений, а `except*` выбирает совпадающие исключения внутри группы и позволяет обработать их отдельно, сохраняя неперехваченные элементы. Это важно при structured concurrency, когда несколько задач могут завершиться независимо и вернуть несколько ошибок. Если операция гарантирует только одну ошибку, обычная модель проще.

EN: An ordinary `except` matches the type of a raised exception. An `ExceptionGroup` contains multiple exceptions, while `except*` selects matching members for handling and leaves unmatched members in the group. This is useful with structured concurrency, where multiple tasks may fail independently. If an operation can produce only one failure, ordinary exception handling is simpler.

**FU-5 — How would you design error handling for a FastAPI endpoint without coupling the domain layer to HTTP? / Как спроектировать обработку ошибок FastAPI endpoint без зависимости domain layer от HTTP?**

RU: Domain layer определяет собственные ошибки предметной области, например отсутствие лекарства или конфликт остатка, и не импортирует FastAPI. Application service поднимает эти ошибки или преобразует ошибки портов/адаптеров на границах. FastAPI exception handlers в presentation layer отображают известные типы в стабильные HTTP-коды и публичную схему ошибки. Неизвестные ошибки остаются 500, логируются с correlation ID и traceback на серверной стороне, а клиент получает безопасное обобщённое сообщение. Контракт ответа не должен раскрывать внутренние детали.

EN: The domain layer defines domain-specific exceptions, such as a missing medication or an inventory conflict, without importing FastAPI. Application services propagate these errors or translate adapter failures at explicit boundaries. FastAPI exception handlers in the presentation layer map known types to stable HTTP status codes and public error schemas. Unknown failures remain 500 responses, are logged server-side with a correlation ID and traceback, and produce a safe generic client message. The response contract must not expose internal implementation details.

### Сценарий применения в Pharmaviyum (гипотетический)

**Статус: Hypothetical interview scenario — не утверждение о текущей реализации.**

Представим операцию поиска лекарства или изменения складского остатка в Pharmaviyum. Domain layer может поднять типизированную ошибку, например `MedicationNotFoundError` или `InventoryConflictError`. Repository adapter может преобразовать специфическую ошибку базы данных в инфраструктурное исключение с помощью exception chaining. Граница FastAPI может преобразовать известные domain errors в безопасные ответы 404 или 409, а неожиданные сбои оставить обобщёнными ответами 500. Логи и traces должны использовать request correlation identifiers и не содержать пациентские записи, credentials или чувствительный контекст рецептов.

Senior-level вопрос заключается не только в выборе HTTP status code. Важно определить, какому слою принадлежит ошибка, какой слой отвечает за её преобразование, безопасен ли retry, какая информация должна быть доступна для внутренней диагностики и какая информация может пересекать API boundary.

### Критерии оценки Senior

Сильный ответ Senior должен показывать, что кандидат:

1. Точно объясняет различие `BaseException` и `Exception` и избегает широких catch-all handlers.
2. Описывает точную семантику `else` и `finally`, включая propagation и cleanup.
3. Использует exception chaining для сохранения причинного контекста при переводе между слоями.
4. Проектирует custom exception hierarchy вокруг стабильной domain semantics, а не деталей реализации.
5. Понимает `ExceptionGroup` и `except*` как механизм обработки нескольких concurrent failures.
6. Разделяет domain errors и HTTP transport concerns, определяет стабильный публичный error contract.
7. Учитывает observability, redaction чувствительных данных, idempotency, retry classification и failure budgets.

**Сигналы уровня**
- Mid-level: знает `try/except/finally` и умеет определить собственное исключение.
- Strong Senior: объясняет propagation, chaining, abstraction boundaries и безопасное отображение ошибок API.
- Staff-level signal: проектирует согласованную error taxonomy и observability/retry policies для нескольких сервисов, сохраняя независимость domain layer и operational safety.

### Типичные ошибки

- Перехватывать `BaseException` или использовать широкий `except Exception` как обычный механизм управления потоком.
- Возвращать успешный результат после подавления исключения.
- Считать, что `else` выполняется при возникновении исключения.
- Использовать `finally` вместо context managers и явного управления ресурсами.
- Поднимать новое исключение без сохранения исходной причины, когда она важна.
- Разбирать текст сообщения исключения вместо использования типов и структурированных атрибутов.
- Раскрывать traceback, SQL, сообщения драйвера, секреты или пациентские данные в HTTP response.
- Отображать все ошибки в один status code или один общий domain exception.
- Повторять постоянные ошибки или неидемпотентные операции без защитных механизмов.
- Считать `except*` взаимозаменяемым с обычным `except`.

### Источники

- Python tutorial — Errors and Exceptions: https://docs.python.org/3/tutorial/errors.html
- Built-in Exceptions: https://docs.python.org/3/library/exceptions.html
- Compound statements — `try`: https://docs.python.org/3/reference/compound_stmts.html#the-try-statement
- Exception context and chaining: https://docs.python.org/3/library/exceptions.html#exception-context
- PEP 654 — Exception Groups and `except*`: https://peps.python.org/pep-0654/
- FastAPI — Handling Errors: https://fastapi.tiangolo.com/tutorial/handling-errors/


## PY-CORE-011 — Контекстные менеджеры Python и управление ресурсами

**Вопрос (EN):** Explain the context manager protocol and how Python guarantees resource cleanup with the `with` statement. Compare synchronous and asynchronous context managers, and discuss how you would manage database sessions, locks, files, and other resources in a production backend.

**Перевод (RU):** Объясните протокол context manager и то, как Python обеспечивает освобождение ресурсов с помощью оператора `with`. Сравните синхронные и асинхронные контекстные менеджеры и расскажите, как управлять DB sessions, locks, файлами и другими ресурсами в production backend.

### Что проверяет интервьюер

- Точное понимание протокола context manager и потока управления.
- Владение жизненным циклом ресурсов, детерминированным cleanup и распространением исключений.
- Корректное применение `contextlib`, `ExitStack` и асинхронных контекстных менеджеров.
- Понимание cancellation, concurrency, границ транзакций и ошибок при освобождении ресурсов.
- Умение отделять управление жизненным циклом ресурсов от бизнес-логики.

### Эталонный ответ (RU)

Context manager — объект, который задаёт ограниченную область управления ресурсом или временным состоянием. Синхронный протокол состоит из `__enter__()` и `__exit__(exc_type, exc_value, traceback)`. При входе в блок `with` Python вызывает `__enter__`; возвращаемое значение связывается с переменной после `as`. При выходе из блока `__exit__` вызывается как при нормальном завершении, так и при исключении, распространяющемся из блока.

Если исключения не было, три аргумента `__exit__` равны `None`. Если исключение было, метод получает его тип, объект и traceback. Возвращение truthy value означает подавление исключения; falsey value, включая `None`, позволяет ему распространяться дальше. Исключение, возникшее внутри `__exit__`, само становится результатом выхода и может заменить исходное исключение, поэтому cleanup-код должен быть предсказуемым и не скрывать первопричину.

Оператор `with` обеспечивает детерминированный вызов протокола выхода при нормальном управлении потоком и при распространении исключения через блок. Это не означает защиту от любого завершения процесса: например, принудительное завершение процесса или авария интерпретатора не дают универсальной гарантии cleanup.

Для простого случая протокол можно реализовать напрямую. Для генераторного стиля применяется `contextlib.contextmanager`: код до `yield` выполняет setup, код после — cleanup, а исключение из тела with при необходимости передаётся обратно в точку `yield`. Исключение нельзя случайно проглотить: если генератор перехватил его только для логирования и не поднял повторно, оно будет подавлено. Для асинхронного кода используются `async with`, `__aenter__`, `__aexit__` и `contextlib.asynccontextmanager`; операции setup/cleanup могут ожидать завершения async I/O.

`ExitStack` полезен, когда количество ресурсов или контекстных менеджеров определяется во время выполнения. Он регистрирует callbacks и exit handlers и закрывает ресурсы в обратном порядке — по принципу LIFO. Это помогает корректно откатывать частично выполненный setup, если получение следующего ресурса завершилось ошибкой.

В backend важно определить владельца каждого ресурса и его lifetime. Database session должна иметь ограниченную область действия, обычно одну операцию или транзакцию; commit/rollback должны быть явными и согласованными с unit-of-work. Не следует удерживать соединение или lock во время долгих внешних вызовов без необходимости. Файлы, временные каталоги и locks должны освобождаться в гарантированной точке. Для async ресурсов необходимо учитывать cancellation: cleanup может требовать await, поэтому он должен быть реализован в async exit path и не должен бесконтрольно подавлять cancellation. Контекстный менеджер сам по себе не делает операцию потокобезопасной, транзакционной или идемпотентной — он только задаёт lifecycle и правила выхода.

### Профессиональный ответ (EN)

A context manager defines a bounded execution scope for a resource or temporary state. The synchronous protocol consists of `__enter__()` and `__exit__(exc_type, exc_value, traceback)`. Entering a `with` block invokes `__enter__`, and its return value is assigned to the target after `as`. On leaving the block, Python invokes `__exit__` both after normal completion and when an exception propagates out of the block.

When no exception occurred, the three exception arguments are `None`. Otherwise, `__exit__` receives the exception type, instance, and traceback. A truthy return value suppresses the exception; a falsey value, including `None`, allows propagation. An exception raised by `__exit__` can replace the exception from the block, so cleanup code should be predictable and should not obscure the primary failure.

The `with` statement provides deterministic protocol exit for normal control flow and exceptions crossing the block. It is not a universal guarantee under process termination or interpreter failure.

A class can implement the protocol directly. `contextlib.contextmanager` offers a generator-based alternative: setup runs before `yield`, cleanup after it, and an exception from the with-body can be thrown back at the yield point. If the generator catches an exception only to log it and does not re-raise it, that exception is suppressed. Asynchronous code uses `async with`, `__aenter__`, `__aexit__`, and `contextlib.asynccontextmanager`, allowing setup and cleanup to await asynchronous operations.

`ExitStack` is useful when the number of resources or context managers is dynamic. It registers exit handlers and callbacks and unwinds them in reverse order (LIFO), including when later acquisition fails partway through setup.

In a backend, every resource needs an explicit owner and lifetime. A database session should be scoped narrowly—often to one operation or transaction—with deliberate commit/rollback semantics consistent with the unit-of-work boundary. Avoid holding connections or locks across slow external calls without a clear reason. Files, temporary directories, and locks need deterministic release. Async cleanup must account for cancellation and should not accidentally suppress it. A context manager does not by itself make an operation thread-safe, transactional, or idempotent; it defines lifecycle and exit behavior.

### Дополнительные вопросы и эталонные ответы

**FU-1 — What exactly happens when an exception leaves a `with` block? / Что именно происходит, когда исключение выходит из блока `with`?**

RU: Python вызывает `__exit__`, передавая тип, объект исключения и traceback. Если `__exit__` возвращает truthy value, исключение подавляется; иначе оно продолжает распространяться. Если `__exit__` само поднимает исключение, оно может заменить исходное, поэтому ошибки cleanup требуют аккуратной политики.

EN: Python calls `__exit__` with the exception type, instance, and traceback. A truthy return suppresses the exception; otherwise it propagates. If `__exit__` raises, that new exception can replace the original, so cleanup failures need an explicit policy.

**FU-2 — When would you choose `contextlib.contextmanager` over a class-based context manager? / Когда выбрать `contextlib.contextmanager`, а не классический context manager?**

RU: Генераторный вариант удобен для компактного setup/cleanup, когда не нужны сложное состояние и несколько методов. Класс предпочтительнее, если lifecycle сложный, состояние должно быть явно представлено, нужны дополнительные методы или объект должен поддерживать более богатый контракт. В обоих случаях важно корректно передавать исключения и не подавлять их случайно.

EN: The generator form is concise for straightforward setup and cleanup when no substantial object state is needed. A class is clearer when the lifecycle is complex, state must be explicit, additional methods are required, or the object has a richer contract. Both forms must preserve exception semantics and avoid accidental suppression.

**FU-3 — What problem does `ExitStack` solve? / Какую проблему решает `ExitStack`?**

RU: Он управляет переменным количеством ресурсов и позволяет регистрировать их по мере успешного получения. При выходе handlers выполняются в обратном порядке. Это особенно важно, если получение второго или третьего ресурса завершается ошибкой: ранее полученные ресурсы всё равно будут освобождены.

EN: It manages a dynamic number of resources and lets the program register them as acquisition succeeds. Exit handlers run in reverse order. If acquiring a later resource fails, previously acquired resources are still released.

**FU-4 — How should an async context manager behave during task cancellation? / Как async context manager должен вести себя при cancellation задачи?**

RU: `__aexit__` должен выполнить необходимый async cleanup, например закрыть ресурс или вернуть соединение в pool. Реализация должна учитывать, что cancellation — часть управления потоком, а не обычная бизнес-ошибка. Нельзя бездумно подавлять cancellation; при необходимости применяются ограниченные cleanup-процедуры и повторное распространение cancellation согласно контракту используемого async framework.

EN: `__aexit__` should perform required asynchronous cleanup, such as closing a resource or returning a connection to a pool. Cancellation is a control-flow signal, not an ordinary business error. Do not suppress it indiscriminately; use bounded cleanup and preserve cancellation according to the async framework's contract.

**FU-5 — How would you scope a database session in a FastAPI application? / Как определить scope database session в FastAPI application?**

RU: Session должна создаваться на ограниченный request или unit-of-work scope и гарантированно закрываться после завершения. Граница транзакции должна быть явной: application service либо unit-of-work отвечает за commit, а при ошибке выполняется rollback; закрытие session не следует путать с успешным commit. Для streaming response или фоновых задач lifecycle может выходить за пределы обычного request, поэтому ресурс нельзя закрывать раньше времени или неограниченно удерживать. Конкретная схема зависит от sync/async driver и выбранной архитектуры.

EN: Scope the session to a bounded request or unit-of-work lifetime and guarantee closure afterward. Make the transaction boundary explicit: the application service or unit of work owns commit, and failures trigger rollback; closing a session is not equivalent to a successful commit. Streaming responses and background tasks may outlive the ordinary request scope, so resources must neither be closed too early nor held indefinitely. The exact pattern depends on the sync/async driver and application architecture.

### Сценарий применения в Pharmaviyum (гипотетический)

**Статус: Hypothetical interview scenario — не утверждение о текущей реализации.**

Представим use case изменения складского остатка, которому нужны database transaction и краткоживущий distributed lock. Application boundary может получить оба ресурса через context managers, применить изменение, выполнить commit только после успешной валидации и освободить lock при любом нормальном или исключительном выходе. Архитектура должна определить lock timeout, владельца транзакции, поведение при cancellation и действия при ошибке самого cleanup. Context manager не должен скрывать неопределённый результат commit или создавать ложное обещание exactly-once execution.

### Критерии оценки Senior

Сильный ответ Senior должен показывать, что кандидат:

1. Объясняет точный протокол `__enter__` / `__exit__` и семантику подавления исключений.
2. Отличает детерминированный cleanup от гарантий при аварии или принудительном завершении процесса.
3. Умеет выбирать между class-based managers, generator-based managers и `ExitStack`.
4. Понимает async context managers и cleanup с учётом cancellation.
5. Определяет явные ownership, lifetime и transaction boundaries ресурсов.
6. Понимает, что context managers автоматически не обеспечивают thread safety, atomicity или idempotency.
7. Учитывает частичное получение ресурсов, обратный порядок cleanup и ошибки освобождения.

**Сигналы уровня**
- Mid-level: использует `with open(...)` и понимает базовый cleanup.
- Strong Senior: проектирует корректные resource scopes, transaction boundaries и exception behavior.
- Staff-level signal: задаёт согласованные lifecycle conventions и failure semantics для компонентов приложения.

### Типичные ошибки

- Считать, что `__exit__` вызывается при любом возможном отказе процесса.
- Возвращать truthy value и случайно подавлять исключение.
- Перехватывать исключение в generator context manager без повторного raise.
- Предполагать, что закрытие database session автоматически выполняет commit.
- Удерживать locks или database connections во время долгих сетевых вызовов.
- Игнорировать cancellation при асинхронном cleanup.
- Получать несколько ресурсов без обработки частичного сбоя setup.
- Считать context manager заменой проектированию транзакций, синхронизации или idempotency.

### Источники

- Python language reference — The `with` statement: https://docs.python.org/3/reference/compound_stmts.html#the-with-statement
- Python data model — With Statement Context Managers: https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers
- `contextlib`: https://docs.python.org/3/library/contextlib.html
- `contextlib.ExitStack`: https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
- Async context managers: https://docs.python.org/3/reference/datamodel.html#asynchronous-context-managers


## PY-CORE-012 — Модули, пакеты и система импорта Python

**Вопрос (EN):** Explain how Python resolves and loads imports. Discuss modules, regular and namespace packages, sys.path, sys.modules, import caching, relative imports, circular dependencies, and import-time side effects. How would you organize a maintainable FastAPI codebase?

**Перевод (RU):** Объясните, как Python разрешает и загружает импорты. Расскажите о модулях, обычных и namespace packages, sys.path, sys.modules, кешировании импортов, относительных импортах, циклических зависимостях и побочных эффектах во время импорта. Как организовать поддерживаемую кодовую базу FastAPI?

### Что проверяет интервьюер

- Понимание import machinery и идентичности объектов модулей.
- Умение различать пути поиска модулей, finders/loaders и cache импортов.
- Понимание рисков circular imports и import-time side effects.
- Знание package boundaries, направления зависимостей и startup приложения.
- Практические решения по packaging и testability.

### Эталонный ответ (RU)

Модуль Python — единица кода, обычно представленная файлом .py, которая при импорте становится объектом модуля. Package организует модули в иерархию. Обычный package традиционно содержит __init__.py; namespace package может объединять части одного логического package из нескольких каталогов и не требует __init__.py в соответствующих namespace-каталогах. Поэтому неверно утверждать, что каждый package обязан содержать __init__.py.

Оператор import запускает import machinery: finders находят модуль, а loaders создают и исполняют его. sys.path — список путей поиска верхнеуровневых модулей. На него влияют способ запуска Python, окружение и конфигурация интерпретатора. Текущая рабочая директория может участвовать в поиске, но production deployment не должен зависеть от случайного состояния sys.path или ручного изменения sys.path внутри приложения.

После загрузки модуль кешируется в sys.modules по имени. Повторный импорт обычно возвращает тот же объект модуля, а не выполняет тело заново. Важная деталь: модуль помещается в sys.modules до завершения исполнения его тела. Это поддерживает рекурсивные импорты, но при circular import другая сторона может увидеть частично инициализированный модуль. Удаление записей из sys.modules или принудительный reload не являются обычным способом обновления production-кода и могут привести к нескольким объектам модулей с неожиданной identity.

При импорте исполняются инструкции верхнего уровня. Import-time side effects — открытие соединений, чтение секретов, запуск фоновых задач, создание глобальных клиентов или выполнение миграций — делают импорт непредсказуемым и усложняют тестирование, reload и multiprocessing. На уровне модуля лучше оставлять определения и лёгкую декларативную конфигурацию. Инициализацию ресурсов следует выполнять в явной startup/lifespan фазе приложения, а освобождение — в соответствующей shutdown фазе.

Абсолютные импорты явно указывают путь от корня доступного import namespace и обычно удобны для навигации в крупных проектах. Относительные импорты разрешаются относительно текущего package; они полезны внутри связанного package, но могут усложнить перемещение модулей и прямой запуск отдельных файлов. Выбор должен быть последовательным. Запуск через python -m package.module обычно лучше сохраняет package context, чем прямой запуск файла.

Circular import возникает, когда модуль A импортирует B, а B прямо или косвенно импортирует A. Один модуль может быть ещё не полностью инициализирован, поэтому нужное имя может отсутствовать в момент обращения. Локальный импорт внутри функции иногда откладывает зависимость, но часто лишь маскирует архитектурную проблему. Предпочтительно устранить цикл через выделение общего контракта в третий модуль, dependency inversion, передачу зависимостей извне или пересмотр границ пакетов.

Для поддерживаемого FastAPI backend следует разделять API/router слой, application/use-case слой, domain слой и infrastructure adapters. Зависимости должны направляться к стабильным абстракциям, а не создавать взаимные импорты между router, service и repository. Создание приложения, регистрация routers и lifespan orchestration должны быть явными. pyproject.toml описывает metadata и настройки packaging/tooling; воспроизводимая установка должна опираться на объявленные зависимости и выбранный build backend, а не на неявную структуру локальной машины. Тесты должны импортировать приложение без подключения к production-сервисам и нежелательных внешних действий.

### Профессиональный ответ (EN)

A Python module is a unit of code, commonly represented by a .py file, which becomes a module object when imported. A package organizes modules hierarchically. A regular package traditionally contains __init__.py; a namespace package can combine portions of one logical package from multiple directories and does not require __init__.py in those namespace directories. Therefore, it is incorrect to claim that every package must contain __init__.py.

An import statement invokes Python's import machinery; it is not merely a file read. Finders locate a module and loaders create and execute it. sys.path is the search path used for top-level module discovery and is influenced by invocation mode, interpreter environment, and configuration. The current working directory may participate, but production applications should not rely on accidental path state or mutate sys.path as an architectural mechanism.

After loading, a module is cached in sys.modules under its import name. Subsequent imports normally return the cached module object rather than executing the module body again. The module is inserted into sys.modules before its body finishes executing, which supports recursive imports but also means a circular dependency can observe a partially initialized module. Deleting cache entries or forcing reload is not a normal production code-update strategy and can create multiple module objects with surprising identity behavior.

Importing executes module-level statements. Import-time side effects—opening connections, reading secrets, starting background tasks, creating global clients, or running migrations—make imports unpredictable and complicate tests, reloads, and multiprocessing. Module scope should generally contain definitions and lightweight declarative configuration. Resource initialization belongs in an explicit application startup/lifespan phase, with cleanup in the corresponding shutdown phase.

Absolute imports make paths explicit from the available import namespace and are often easier to navigate in large codebases. Relative imports are resolved from the current package and can be convenient within a cohesive package, but may complicate module relocation and direct file execution. Consistency matters. Running a module with python -m package.module often preserves package context more reliably than executing the file directly.

A circular import occurs when module A imports B and B directly or indirectly imports A. One side may observe the other before initialization has completed, so a requested name may not yet exist. A local import can defer a dependency, but is usually a workaround rather than an architectural fix. Prefer extracting shared contracts into a third module, applying dependency inversion, injecting dependencies, or revisiting package boundaries.

A maintainable FastAPI backend should separate API/router, application/use-case, domain, and infrastructure-adapter responsibilities. Dependencies should point toward stable abstractions rather than forming mutual imports between routers, services, and repositories. Application creation, router registration, and lifespan orchestration should be explicit. pyproject.toml declares project metadata and packaging/tool configuration; reproducible installation should use declared dependencies and a chosen build backend rather than relying on a developer's local path layout. Tests should import the application without connecting to production services or triggering unintended external actions.

### Дополнительные вопросы и эталонные ответы

**FU-1 — What is the difference between sys.path and sys.modules? / В чём разница между sys.path и sys.modules?**

RU: sys.path — список мест, где import machinery ищет верхнеуровневые модули. sys.modules — cache уже обнаруженных или загружаемых модулей, индексируемый по имени. Изменение sys.path влияет на поиск ещё не закешированных импортов; наличие имени в sys.modules обычно позволяет вернуть существующий объект без нового поиска и исполнения.

EN: sys.path is the list of locations used to search for top-level modules. sys.modules is the cache of modules that have been imported or are currently being initialized, keyed by module name. Changing sys.path affects discovery of modules not already satisfied by the cache; an entry in sys.modules normally lets Python reuse the existing module object.

**FU-2 — Why can circular imports fail even though Python caches modules? / Почему circular imports могут завершиться ошибкой, несмотря на кеширование модулей?**

RU: Python помещает объект модуля в sys.modules до полного исполнения его тела. Если второй модуль импортирует первый в этот момент, он может получить частично инициализированный объект, в котором нужное имя ещё не определено. Кеш предотвращает бесконечную повторную загрузку, но не делает циклическую зависимость безопасной.

EN: Python inserts a module object into sys.modules before its body has finished executing. If the second module imports the first at that point, it may receive a partially initialized object whose required name has not yet been defined. Caching prevents unbounded re-import, but it does not make a cyclic dependency safe.

**FU-3 — What is the difference between a regular package and a namespace package? / Чем regular package отличается от namespace package?**

RU: Обычный package обычно определяется каталогом с __init__.py. Namespace package может состоять из нескольких portions, расположенных в разных каталогах поиска, и не требует __init__.py в namespace-каталогах. Namespace packages полезны для распределения частей единого пространства имён между независимыми пакетами, но требуют осознанной структуры и понимания поиска модулей.

EN: A regular package is commonly identified by a directory containing __init__.py. A namespace package can consist of multiple portions located in different search locations and does not require __init__.py in those namespace directories. Namespace packages support distributing one logical namespace across independently installed packages, but require deliberate layout and import-path understanding.

**FU-4 — Why are import-time side effects harmful in a web application? / Почему import-time side effects вредны для web application?**

RU: Они связывают импорт кода с доступностью внешних сервисов и состоянием окружения. Это затрудняет unit tests, CLI usage, migrations, worker startup, application reload и multiprocessing. Создание соединений и запуск задач лучше выполнять в явной lifecycle фазе, где видны ownership, порядок и cleanup.

EN: They couple code import to external-service availability and environment state. This complicates unit tests, CLI use, migrations, worker startup, reloads, and multiprocessing. Connections and background tasks should be created in an explicit lifecycle phase where ownership, ordering, and cleanup are visible.

**FU-5 — How would you diagnose and fix a circular dependency between FastAPI routers, services, and repositories? / Как диагностировать и исправить циклическую зависимость между FastAPI routers, services и repositories?**

RU: Сначала построить фактический dependency graph и найти цикл, а не добавлять случайные local imports. Затем определить направление зависимостей: router вызывает application service; service зависит от repository port/interface; infrastructure реализует этот интерфейс. Общие схемы и контракты можно вынести в модуль, который не импортирует верхние слои. Конкретные реализации передаются через dependency injection или composition root. После реорганизации проверить importability, тесты и запуск приложения без подключения к production.

EN: First inspect the actual dependency graph and identify the cycle instead of adding arbitrary local imports. Establish a clear direction: routers call application services; services depend on repository ports or interfaces; infrastructure implements those interfaces. Shared contracts can live in a module that does not import higher layers. Concrete implementations are wired through dependency injection or a composition root. Then verify importability, tests, and application startup without production connections.

### Сценарий применения в Pharmaviyum (гипотетический)

**Статус: Hypothetical interview scenario — не утверждение о текущей реализации.**

Представим FastAPI application, в которой router импортирует service, service импортирует repository implementation, а repository импортирует schema из router layer. Это создаёт нежелательный dependency cycle. Более чистый дизайн размещает API schemas и routing в presentation layer, use cases — в application layer, domain contracts — в domain layer, а database implementations — в infrastructure. Application composition root связывает конкретные adapters. Database pools и внешние клиенты инициализируются через lifespan, а не как import-time globals. Это архитектурный пример, а не подтверждённое описание текущего кода Pharmaviyum.

### Критерии оценки Senior

Сильный ответ Senior должен показывать, что кандидат:

1. Объясняет import discovery, исполнение модулей и назначение sys.path и sys.modules.
2. Понимает частично инициализированные модули и причины, по которым cache не устраняет риски circular imports.
3. Корректно различает regular и namespace packages.
4. Выявляет import-time side effects и переносит инициализацию ресурсов в явное lifecycle управление.
5. Последовательно выбирает absolute или relative imports и понимает package execution context.
6. Проектирует направление зависимостей и package boundaries без циклов.
7. Понимает воспроизводимый packaging и тестируемый startup приложения.

**Сигналы уровня**
- Mid-level: понимает imports, packages и базовый поиск модулей.
- Strong Senior: диагностирует circular imports и проектирует чистые package boundaries.
- Staff-level signal: определяет общие правила dependency direction, packaging conventions и lifecycle для нескольких entry points и надёжных тестов.

### Типичные ошибки

- Утверждать, что каждый package обязан содержать __init__.py.
- Путать sys.path и sys.modules.
- Предполагать, что повторный import всегда заново выполняет тело модуля.
- Считать circular import исключительно проблемой отсутствующего пути.
- Использовать local imports, чтобы скрыть неразрешённый архитектурный цикл.
- Создавать database connections, clients или background tasks во время импорта.
- Зависеть от текущей рабочей директории или ручного изменения sys.path в production.
- Допускать взаимные импорты routers, services и repositories.
- Считать успешный локальный import доказательством корректной сборки и installability package.

### Источники

- Python tutorial — Modules: https://docs.python.org/3/tutorial/modules.html
- Python reference — The import system: https://docs.python.org/3/reference/import.html
- sys.path и sys.modules: https://docs.python.org/3/library/sys.html
- PEP 420 — Implicit Namespace Packages: https://peps.python.org/pep-0420/
- Packaging Python Projects: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- Python Packaging User Guide — pyproject.toml: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
- FastAPI — Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI — Lifespan Events: https://fastapi.tiangolo.com/advanced/events/


## PY-CORE-013 — Управление памятью и сборка мусора в Python

**Вопрос (EN):** Explain object lifetime and memory reclamation in Python. Discuss reference counting, cyclic garbage collection, reference cycles, weak references, finalization, common memory-retention causes, and how to investigate memory growth in a long-running backend.

**Перевод (RU):** Объясните время жизни объектов и освобождение памяти в Python. Расскажите о reference counting, cyclic garbage collection, reference cycles, weak references, финализации, распространённых причинах удержания памяти и диагностике её роста в долгоживущем backend.

### Что проверяет интервьюер
- Понимание времени жизни Python-объектов и потребления памяти процессом.
- Различение деталей CPython и гарантий языка.
- Понимание reference cycles, cyclic GC, weak references и финализации.
- Умение находить retention paths и отличать рост Python heap от RSS/native allocations.
- Безопасный для production подход к профилированию и устранению причин.

### Эталонный ответ (RU)

Объекты Python существуют, пока на них сохраняются достижимые сильные ссылки, но стратегия управления памятью зависит от реализации интерпретатора. В CPython для многих объектов основным механизмом является reference counting: счётчик сильных ссылок изменяется при создании и удалении ссылок. Когда он достигает нуля, объект обычно может быть освобождён. Это особенность CPython, а не гарантия языка Python для всех реализаций. Код не должен полагаться на точный момент уничтожения объекта.

Reference counting не освобождает изолированные циклы ссылок: два объекта могут ссылаться друг на друга, хотя из остальной программы они недостижимы. В CPython cyclic garbage collector обнаруживает определённые циклы среди отслеживаемых объектов-контейнеров и может освободить такие структуры. Не каждый объект обязательно отслеживается сборщиком. Generational collection использует возраст объектов как эвристику; внутренние детали поколений меняются между версиями CPython и не являются стабильным API приложения.

Сам по себе reference cycle не означает утечку. Если цикл достижим из global registry, cache, активной задачи или другого долгоживущего объекта, он остаётся живым. Важнее искать retention path — цепочку сильных ссылок от корня приложения к объекту, который больше не нужен. Типичные причины неконтролируемого удержания: неограниченные caches и collections, глобальные registries, накопление результатов задач, callbacks и closures, подписки без отписки, долгоживущие ссылки на request/session objects, сохранённые tracebacks и exception objects.

Weak reference позволяет ссылаться на объект, не продлевая его жизнь сильной ссылкой. Это полезно для некоторых вспомогательных mappings и caches, где связь не должна удерживать объект. Однако weak references поддерживаются не всеми типами; это зависит от конкретного типа. Слабая ссылка может перестать разрешаться, как только исчезнут сильные ссылки на объект, поэтому она не подходит, если cache обязан гарантированно удерживать значение. Модуль weakref предоставляет, в частности, WeakKeyDictionary и WeakValueDictionary.

Финализация требует осторожности. Нельзя строить корректность программы на точном времени вызова __del__. Финализаторы усложняют анализ циклов, а исключения из __del__ не распространяются вызывающему коду обычным образом. Для детерминированного управления ресурсами предпочтительны context managers и try/finally. weakref.finalize может помочь в отдельных сценариях cleanup, но не заменяет явное закрытие файлов, соединений и других внешних ресурсов. Освобождение внешнего ресурса и освобождение Python memory — разные задачи.

Рост RSS процесса сам по себе не доказывает утечку Python-объектов. Python allocator и системный allocator могут удерживать освобождённые арены для повторного использования, поэтому память не обязана немедленно возвращаться операционной системе. RSS также включает native allocations библиотек, stacks, memory mappings и другие компоненты. Следует разделять рост живых Python allocations, native memory growth и поведение allocator.

Диагностику начинают с воспроизводимого workload и baseline. Измеряют память во времени и сопоставляют её с количеством запросов, размером очередей, количеством задач и cardinality cache. tracemalloc позволяет сравнивать snapshots и находить места выделения Python-памяти; gc предоставляет средства наблюдения за циклическим сборщиком. Для native allocations могут потребоваться системные метрики или специализированные профилировщики. Сравнивать snapshots нужно после одинаковых фаз нагрузки, изучая retainers и проверяя, не объясняется ли рост ожидаемым cache warming или буферизацией. gc.collect() может быть диагностическим экспериментом, но не освобождает объекты, удерживаемые сильными ссылками, и не заменяет устранение причины.

В долгоживущем FastAPI backend следует ограничивать caches и очереди, завершать фоновые tasks, освобождать subscriptions, закрывать ресурсы через lifespan/context managers, не хранить request-scoped данные в глобальном состоянии и контролировать batch/stream buffers. Выводы должны подтверждаться профилем и нагрузочным тестом, а не одним графиком RSS.

### Профессиональный ответ (EN)

Python objects remain alive while reachable through strong references, but memory-management strategy depends on the interpreter. In CPython, reference counting is a primary mechanism for many objects: the strong-reference count changes as references are created and removed. When it reaches zero, an object can usually be deallocated. This is a CPython characteristic, not a language-wide guarantee. Code should not depend on the exact time an object is destroyed.

Reference counting cannot reclaim isolated reference cycles. Two objects may reference each other even though nothing else can reach them. CPython's cyclic garbage collector can detect certain cycles among tracked container objects and reclaim unreachable structures. Not every object is necessarily tracked. Generational collection uses object age as a heuristic; internal generation details can change between CPython releases and are not a stable application API.

A reference cycle is not automatically a leak. If it remains reachable from a global registry, cache, active task, or another long-lived object, it is still live. The key concept is a retention path: a chain of strong references from an application root to an object that is no longer needed. Common causes include unbounded caches and collections, global registries, accumulated task results, callbacks and closures, subscriptions that are never removed, long-lived references to request/session objects, and retained tracebacks or exception objects.

A weak reference does not keep its target alive. It is useful for auxiliary mappings or caches when the association should not extend the target's lifetime. However, not every type supports weak references. A weak reference may stop resolving once strong references disappear, so it is unsuitable when a cache must guarantee retention. The weakref module includes WeakKeyDictionary and WeakValueDictionary.

Finalization requires care. Program correctness should not depend on the exact time __del__ runs. Finalizers complicate cycle analysis, and exceptions raised by __del__ are not propagated to the caller normally. Prefer context managers and try/finally for deterministic resource management. weakref.finalize can help in limited cleanup scenarios, but it does not replace explicitly closing files, connections, and other external resources. Releasing an external resource and reclaiming Python memory are separate concerns.

Increasing process RSS does not by itself prove a Python-object leak. Python and system allocators may retain freed arenas for reuse, so memory does not necessarily return to the OS immediately. RSS also includes native allocations, stacks, memory mappings, and other process components. Distinguish growth in live Python allocations from native-memory growth and allocator behavior.

Start with a reproducible workload and baseline. Track memory over time and correlate it with request volume, queue sizes, task counts, and cache cardinality. tracemalloc compares snapshots and identifies Python allocation sites; gc provides visibility into cyclic collection. Native allocations may require system metrics or specialized profilers. Compare snapshots after equivalent workload phases, inspect retainers, and determine whether growth is expected cache warming or buffering. gc.collect() can be a diagnostic experiment, but it cannot reclaim objects retained by strong references and is not a substitute for fixing the cause.

In a long-running FastAPI backend, bound caches and queues, complete background tasks, remove subscriptions, close resources through lifespan/context managers, avoid storing request-scoped data globally, and control batch and stream buffers. Validate conclusions with profiling and load tests rather than a single RSS graph.

### Дополнительные вопросы и эталонные ответы

**FU-1 — Why is reference counting insufficient to reclaim every unreachable object? / Почему reference counting недостаточно для освобождения всех недостижимых объектов?**

RU: Изолированный цикл объектов сохраняет ненулевые reference counts, потому что объекты продолжают ссылаться друг на друга, хотя весь цикл недостижим извне. Поэтому CPython дополняет reference counting циклическим сборщиком для определённых отслеживаемых объектов.

EN: An isolated object cycle retains non-zero reference counts because its objects reference one another even though the cycle is unreachable externally. CPython therefore supplements reference counting with a cyclic collector for certain tracked objects.

**FU-2 — What is the difference between a reference cycle and a memory leak? / Чем reference cycle отличается от memory leak?**

RU: Reference cycle — структура взаимных ссылок, но не обязательно утечка. Если цикл остаётся достижимым из долгоживущего корня, он удерживается. Утечка возможна и без циклов, например при бесконечном добавлении объектов в global list. Нужно искать ненужные retention paths и неверное время жизни объектов.

EN: A reference cycle is a graph of mutual references, not necessarily a leak. If it remains reachable from a long-lived root, it is retained. A leak can also occur without cycles, such as continually appending objects to a global list. Look for unnecessary retention paths and unintended object lifetimes.

**FU-3 — When would you use weakref instead of a normal reference? / Когда использовать weakref вместо обычной ссылки?**

RU: Когда связь не должна продлевать жизнь объекта, например в некоторых auxiliary mappings или caches. Нужно проверить поддержку weak references конкретным типом и учитывать, что объект может исчезнуть после потери сильных ссылок. Если cache обязан удерживать значение, weak reference семантически не подходит.

EN: Use it when an association should not extend an object's lifetime, such as in certain auxiliary mappings or caches. Verify that the target type supports weak references and account for the target disappearing when strong references are gone. If a cache must retain its value, a weak reference has the wrong semantics.

**FU-4 — Why can RSS remain high after Python objects have been collected? / Почему RSS может оставаться высоким после сборки Python-объектов?**

RU: Allocator может удерживать освобождённые арены для повторного использования, а RSS включает native allocations и другие области памяти процесса. Поэтому RSS не равен объёму живых Python objects. Сопоставляйте RSS с tracemalloc snapshots и при необходимости исследуйте native memory.

EN: The allocator may retain freed arenas for reuse, and RSS includes native allocations and other process memory. RSS is therefore not equivalent to the size of live Python objects. Correlate it with tracemalloc snapshots and investigate native memory when needed.

**FU-5 — How would you investigate steadily increasing memory in a FastAPI worker? / Как исследовать постоянный рост памяти в FastAPI worker?**

RU: Зафиксировать воспроизводимый workload и baseline, измерять RSS и Python allocations на одинаковых этапах нагрузки, сравнивать tracemalloc snapshots и искать allocation sites и retention paths. Проверить caches, очереди, фоновые tasks, subscriptions и request-scoped objects. Если Python allocations стабильны, исследовать native extensions и allocator. После исправления повторить нагрузочный тест и подтвердить ограниченный рост. Не использовать gc.collect() как постоянную замену устранению удерживающих ссылок.

EN: Establish a reproducible workload and baseline, measure RSS and Python allocations at equivalent workload stages, compare tracemalloc snapshots, and inspect allocation sites and retention paths. Check caches, queues, background tasks, subscriptions, and request-scoped objects. If Python allocations are stable, investigate native extensions and allocator behavior. Rerun the load test after remediation and verify bounded growth. Do not use gc.collect() as a permanent substitute for removing retaining references.

### Сценарий применения в Pharmaviyum (гипотетический)

**Статус: Hypothetical interview scenario — не утверждение о текущей реализации.**

Представим долгоживущий API worker, потребление памяти которого увеличивается при повторных поисках по каталогу лекарств. Возможные причины: неограниченный result cache, сохранение request objects в диагностическом registry, накопление результатов фоновых tasks или native allocations одной из зависимостей. Исследование сравнивает tracemalloc snapshots, коррелирует их с нагрузкой, проверяет размеры cache и очередей и отдельно измеряет RSS процесса. Возможные меры — ограничение cache, явная очистка tasks/subscriptions и bounded buffering. Это гипотезы для расследования, а не подтверждённые дефекты или реализованные исправления Pharmaviyum.

### Критерии оценки Senior

Сильный ответ Senior должен:
1. Различать гарантии языка Python и детали реализации CPython.
2. Объяснять, почему reference counting не освобождает изолированные циклы и какова роль cyclic GC.
3. Понимать, что циклы не обязательно являются утечками, и рассуждать о strong-reference retention paths.
4. Использовать weak references только там, где их семантика времени жизни подходит.
5. Не полагаться на время вызова __del__ для детерминированного cleanup ресурсов.
6. Различать live Python allocations, native allocations, allocator retention и RSS.
7. Предлагать воспроизводимое профилирование, сравнение snapshots, корреляцию с workload и проверку после исправления.

**Сигналы уровня**
- Mid-level: понимает ссылки, базовую GC и распространённые причины удержания объектов.
- Strong Senior: диагностирует retention paths и отделяет рост Python heap от RSS процесса.
- Staff-level signal: определяет memory budgets, bounded-cache policies, практики профилирования и эксплуатационные safeguards для сервисов.

### Типичные ошибки
- Утверждать, что reference counting — гарантия языка для всех реализаций Python.
- Считать каждый reference cycle утечкой.
- Предполагать, что gc.collect() освобождает объекты, удерживаемые strong references.
- Рассматривать weak references как универсальное решение утечек.
- Полагаться на __del__ для детерминированного закрытия внешних ресурсов.
- Приравнивать RSS к размеру живой Python heap.
- Ожидать немедленного возврата памяти ОС после сборки мусора.
- Игнорировать native allocations extension modules.
- Перезапускать workers, не установив источник удержания.
- Профилировать один snapshot без воспроизводимого workload.

### Источники
- Python Data Model: https://docs.python.org/3/reference/datamodel.html
- gc — Garbage Collector interface: https://docs.python.org/3/library/gc.html
- weakref — Weak references: https://docs.python.org/3/library/weakref.html
- tracemalloc — Trace memory allocations: https://docs.python.org/3/library/tracemalloc.html
- Python C API — Reference Counting: https://docs.python.org/3/c-api/refcounting.html
- Python FAQ — Memory management: https://docs.python.org/3/faq/design.html#how-does-python-manage-memory
- FastAPI — Lifespan Events: https://fastapi.tiangolo.com/advanced/events/


## PY-CORE-014 — Оптимизация производительности и профилирование Python

### Что проверяет интервьюер
- Умение оптимизировать измеренные узкие места, а не предположения.
- Понимание алгоритмической сложности, константных факторов и компромиссов по памяти.
- Способность различать CPU-bound, I/O-bound и memory-bound нагрузки.
- Корректное применение profiling и benchmarking инструментов.
- Понимание overhead интерпретатора, рисков кеширования и production observability.
- Умение подтвердить, что оптимизация улучшает репрезентативный workload без нарушения корректности.

### Эталонный ответ (RU)
Оптимизацию производительности нужно начинать не с переписывания кода, а с измерения и поиска узкого места. Сначала следует описать целевой workload и SLO: например, latency percentiles, throughput, загрузку CPU, потребление памяти и error rate. Затем воспроизвести характерную нагрузку и зафиксировать baseline.

Big-O описывает асимптотический рост времени или памяти при увеличении входных данных, но не предсказывает абсолютное время выполнения. На практике важны константные множители, распределение данных, аллокации, локальность памяти, I/O и накладные расходы интерпретатора. Алгоритм с худшей асимптотикой может оказаться быстрее на небольших входах, поэтому решение необходимо подтверждать измерениями.

Для микробенчмарков небольших фрагментов подходит `timeit`; для анализа распределения времени по вызовам Python-функций — `cProfile` и анализ результата через `pstats`. Для анализа Python allocations можно использовать `tracemalloc`; для CPU и native-level проблем могут потребоваться системные профилировщики и метрики процесса. Один profiler не показывает всю картину: например, `cProfile` не является полноценным инструментом измерения ожидания внешнего I/O или native allocations.

Необходимо различать CPU-bound и I/O-bound работу. CPU-bound задачи тратят основное время на вычисления; I/O-bound задачи ожидают сеть, диск, базу данных или другие внешние системы. Асинхронность может повысить конкурентность I/O-bound сервиса, но сама по себе не ускоряет CPU-bound вычисления. Для CPU-bound нагрузки следует исследовать алгоритм, векторизацию, нативные библиотеки, multiprocessing или отдельные worker-процессы — учитывая стоимость сериализации и передачи данных.

Кеширование может уменьшить повторные вычисления или обращения к зависимостям, но добавляет требования к инвалидации, ограничению размера, согласованности, конкурентному доступу и изоляции данных. В многопользовательском backend нельзя допускать, чтобы ключ кеша игнорировал tenant или контекст авторизации. Кешировать следует только после определения корректной семантики и стратегии invalidation.

Корректный benchmark должен использовать репрезентативные входные данные, контролируемую среду, прогрев при необходимости, несколько повторов и статистически осмысленное сравнение. Нужно учитывать шум, cold-start, эффекты интерпретатора, конкурирующую нагрузку и различия между локальным тестом и production. После изменения следует повторить тот же workload, сравнить baseline и результат, проверить корректность и наблюдать за production-метриками. Оптимизация успешна только тогда, когда улучшение измеримо и не ухудшает другие SLO или надёжность.

### Профессиональный ответ (EN)
I start performance work by defining the representative workload, the user-visible objective, and a measurable baseline. I then profile the system to locate the dominant cost before changing the implementation. Optimizing code that is not on the critical path usually adds complexity without meaningful impact.

Big-O describes asymptotic growth in time or space as input size increases; it does not predict absolute runtime. Constant factors, input distribution, allocation behavior, memory locality, I/O, and interpreter overhead also matter. I use complexity analysis to identify scalability risks and measurements to decide what matters for the actual workload.

For small, isolated timing experiments I use `timeit`. For deterministic profiling of Python call activity I use `cProfile` and inspect results with `pstats`. I use `tracemalloc` to compare Python allocation snapshots. Process-level CPU, RSS, native allocations, database timings, and network waits may require additional system and application instrumentation; no single profiler explains every resource bottleneck.

I distinguish CPU-bound work from I/O-bound work. AsyncIO can improve concurrency when tasks spend substantial time awaiting non-blocking I/O, but it does not make CPU-heavy Python code execute faster. CPU-bound work may require algorithmic improvements, optimized native libraries, vectorization, process-based workers, or a dedicated compute service. Those choices must account for serialization, scheduling, and operational costs.

Caching is a trade-off, not a default optimization. It introduces invalidation, bounded capacity, consistency, concurrency, and authorization-isolation concerns. Cache keys must include every dimension that affects the result, including tenant or user scope where applicable. I only introduce caching when the access pattern and invalidation contract are understood.

A sound benchmark uses representative data, controlled conditions, repeated runs, and an explicit comparison against a baseline. I separate microbenchmarks from end-to-end load tests and evaluate latency percentiles, throughput, CPU, memory, and error rates together. After an optimization, I rerun the same workload, verify functional behavior, and observe the change under production-like conditions. The goal is a demonstrated improvement without regressions in correctness, reliability, or other service objectives.

### Дополнительные вопросы и эталонные ответы

**FU-1 — В чём разница между Big-O complexity и измеренным runtime?**  
**Ответ (RU):** Big-O описывает асимптотический порядок роста ресурсов при увеличении размера входа и обычно опускает константы и менее значимые члены. Измеренное время зависит также от реализации, размера входа, оборудования, кешей CPU, аллокаций, I/O и текущей нагрузки. Поэтому Big-O помогает оценить масштабируемость, а benchmark подтверждает поведение конкретной реализации на конкретном workload.  
**Answer (EN):** Big-O describes asymptotic growth and abstracts away constants and lower-order terms. Measured runtime also depends on implementation details, input distribution, hardware, CPU caches, allocations, I/O, and system load. Complexity analysis informs scalability; representative benchmarks validate a particular implementation and workload.

**FU-2 — Когда использовать `timeit`, а когда `cProfile`?**  
**Ответ (RU):** `timeit` подходит для изолированного сравнения небольших выражений или функций с минимизацией части измерительного overhead. `cProfile` нужен, чтобы понять, какие вызовы и функции в более крупном Python workload потребляют время и как распределяются вызовы. Нельзя использовать микробенчмарк как доказательство end-to-end улучшения сервиса.  
**Answer (EN):** I use `timeit` to compare small, isolated operations and `cProfile` to identify where a larger Python workload spends time across function calls. A microbenchmark does not establish an end-to-end service improvement; that requires a representative integration or load test.

**FU-3 — Улучшает ли AsyncIO производительность CPU-bound задач?**  
**Ответ (RU):** Нет, не автоматически. AsyncIO позволяет эффективно переключаться между задачами во время ожидания неблокирующего I/O. Длительное CPU-bound вычисление блокирует event loop, если его не вынести из него. Нужно рассмотреть оптимизацию алгоритма, native/vectorized implementation, process pool или отдельный compute worker, измерив overhead передачи данных.  
**Answer (EN):** No, not by itself. AsyncIO improves concurrency while tasks await non-blocking I/O. A long CPU-bound operation blocks the event loop unless it is moved elsewhere. Consider algorithmic improvements, native or vectorized code, a process pool, or dedicated compute workers, while measuring data-transfer and scheduling overhead.

**FU-4 — Какие риски создаёт кеширование в multi-tenant backend?**  
**Ответ (RU):** Основные риски — устаревшие данные, неограниченный рост памяти, stampede при одновременном истечении ключей, гонки, сложная инвалидация и утечка данных между tenants. Ключ должен учитывать все параметры результата и границу авторизации. Нужны TTL или явная invalidation policy, capacity limits, защита от stampede и тесты изоляции.  
**Answer (EN):** Risks include stale data, unbounded memory growth, cache stampedes, races, difficult invalidation, and cross-tenant data exposure. Keys must include all result-defining dimensions and authorization scope. A production cache needs an explicit invalidation policy, capacity limits, stampede protection where appropriate, and isolation tests.

**FU-5 — Как доказать, что оптимизация безопасна и эффективна?**  
**Ответ (RU):** Зафиксировать baseline и критерии успеха; использовать одинаковый репрезентативный workload и контролируемые условия; сравнить latency percentiles, throughput, CPU, memory и error rate; выполнить функциональные и regression tests; проверить поведение под concurrency и на production-like нагрузке. После rollout отслеживать метрики и иметь возможность отката. Улучшение одного показателя не должно скрывать регрессию другого.  
**Answer (EN):** Establish a baseline and success criteria, then run the same representative workload under controlled conditions. Compare latency percentiles, throughput, CPU, memory, and error rate; run functional and regression tests; and validate concurrency behavior under production-like load. Monitor after rollout and retain a rollback path. An improvement in one metric must not conceal a regression elsewhere.

### Сценарий применения в Pharmaviyum (гипотетический)
Гипотетическое интервью-задание может предложить исследовать медленный endpoint поиска лекарств. Сначала нужно определить репрезентативный набор запросов и измерить end-to-end latency, время базы данных, CPU и память. Затем профилировать приложение и изучить query plans до изменения кода. Следует оценить индексы, форму SQL-запроса, сериализацию payload и повторные обращения. При рассмотрении кеша нужно определить tenant-aware keys, поведение инвалидации и ограничение capacity. Это гипотетический сценарий интервью, а не утверждение о текущей реализации или измеренной производительности Pharmaviyum.

### Критерии оценки Senior
Сильный ответ уровня Senior должен:
1. Начинать с определения workload, измеримых целей и baseline.
2. Объяснять Big-O с учётом константных факторов и реальных условий.
3. Выбирать profiling tools в зависимости от предполагаемого ресурса и масштаба.
4. Различать CPU-bound, I/O-bound и memory-bound поведение.
5. Понимать, что AsyncIO повышает конкурентность I/O, но не скорость CPU-вычислений.
6. Рассматривать кеширование как компромисс между корректностью, изоляцией и эксплуатацией.
7. Использовать повторяемые benchmarks и проверять улучшения на регрессии.
8. Связывать локальное профилирование с production observability и планом rollback.

**Сигналы уровня**
- Mid-level: знает распространённые классы сложности и базовые инструменты измерения.
- Strong Senior: профилирует репрезентативные workloads, находит доминирующее узкое место и проверяет компромиссы по метрикам сервиса.
- Staff-level signal: определяет performance budgets, повторяемые benchmark-практики, capacity models и стандарты оптимизации между сервисами.

### Типичные ошибки
- Оптимизировать по интуиции без profiling.
- Рассматривать Big-O как прогноз абсолютного runtime.
- Использовать микробенчмарк как доказательство production-улучшения.
- Предполагать, что AsyncIO ускоряет CPU-bound код.
- Игнорировать стоимость базы данных, сети, сериализации или native code.
- Внедрять кеш без ограничения capacity или ясного invalidation contract.
- Не включать tenant или authorization scope в cache keys.
- Сравнивать benchmarks в существенно разных условиях.
- Показывать только среднюю latency и игнорировать tail latency.
- Улучшать latency, незаметно увеличивая memory, errors или эксплуатационную сложность.

### Источники
- Python `timeit`: https://docs.python.org/3/library/timeit.html
- Python `cProfile` and `profile`: https://docs.python.org/3/library/profile.html
- Python `pstats`: https://docs.python.org/3/library/pstats.html
- Python `tracemalloc`: https://docs.python.org/3/library/tracemalloc.html
- Python FAQ — Performance: https://docs.python.org/3/faq/programming.html#how-can-i-make-my-program-run-faster
- Python asyncio — Developing with asyncio: https://docs.python.org/3/library/asyncio-dev.html
- FastAPI — Async: https://fastapi.tiangolo.com/async/
