# Python Core — Банк вопросов

**Статус:** В работе  
**Охват:** 4 из 30 основных вопросов подготовлено  
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
