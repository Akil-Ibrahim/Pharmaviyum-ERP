# Python Core — Банк вопросов

**Статус:** В работе  
**Охват:** 6 из 30 основных вопросов подготовлено  
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
