# Python Core — Банк вопросов

**Статус:** В работе  
**Охват:** 1 из 30 основных вопросов подготовлен  
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
