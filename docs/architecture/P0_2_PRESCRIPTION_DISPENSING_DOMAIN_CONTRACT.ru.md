# P0.2 — Доменный контракт пациента, рецепта и отпуска

**Статус:** предлагаемый доменный контракт; реализация ещё не начата  
**Базовый исходный код:** `main`, commit `7a1534e0dd3442480a9956c16ff414a64310c41a` (2026-11-21)  
**Область:** каноническая связь пациента, рецепта и продажи; авторизация фармацевта; журнал отпуска; транзакционные гарантии и критерии приёмки.

Это проектный gate для P0.2. Документ не доказывает, что отпуск по рецепту реализован, клинически проверен, соответствует законодательству какой-либо страны или готов к Production.

[English version](./P0_2_PRESCRIPTION_DISPENSING_DOMAIN_CONTRACT.md)

## 1. Подтверждённое исходное состояние

Аудит исходников выявил:

- `Patient.pharmacy_id` допускает `NULL` и сам по себе не подтверждает право доступа.
- `Prescription` содержит пациента, необязательный product, глобально уникальный номер рецепта, текстовые dosage/instructions, status и даты выдачи/истечения. Нет pharmacy ownership, нормализованных строк рецепта, разрешённого количества, учёта повторных отпусков или dispense ledger.
- Модель рецепта использует `issued_at` и `expires_at`; MCP verification обращается к `date_issued` и `date_expires`, а также к отсутствующему в модели `prescriber_name`. Текущая коллекция prescription items намеренно пуста. Unit-тесты используют `SimpleNamespace` с ожидаемыми именами полей и не подтверждают интеграцию с реальной моделью БД.
- Привилегированный CRUD рецептов в `api/v1/pharmacy_entities.py` требует `CurrentSuperuser`; это не рабочий процесс фармацевта. Отдельный router `endpoints/prescriptions.py` является заглушкой.
- `Sale` содержит pharmacy и cashier ownership, но не patient reference. `SaleItem` связан с product и inventory allocations, но не со строкой рецепта.
- POS checkout уже использует PostgreSQL transactions, tenant membership checks, FEFO allocation, inventory movement journal, payment reservation/settlement, outbox и idempotency. P0.2 должен расширить эти механизмы, а не обходить их.
- Отмена продажи с ожидающим платежом существует. Полный процесс возврата/коррекции/reversal завершённой продажи не подтверждён текущим POS API.
- Текущая модель Pharmacy не предоставляет доверенную регуляторную юрисдикцию. Страну проживания пациента или вывод AI нельзя использовать вместо неё.

## 2. Обязательные доменные инварианты

1. Patient, prescription, prescription line, sale и dispense record должны относиться к одной авторизованной аптеке.
2. Переданный клиентом patient, prescription, product или pharmacy ID — только selector, а не доказательство доступа.
3. Обычный доступ фармацевта требует аутентифицированного активного членства в аптеке. Platform superuser не заменяет pharmacist dispensing workflow.
4. Новый рецепт создаётся только с явно заданной и проверенной сервером принадлежностью аптеке. Legacy-рецепты с неустановленной принадлежностью недоступны обычным фармацевтам до сверки.
5. Нельзя отпускать препарат, если не подтверждены пациент, статус, срок действия, medication identity, strength, dosage form, количество, refill allowance или применимая настроенная политика.
6. Сопоставление продукта детерминированное: нормализованная идентичность препарата, strength и dosage form. Совпадение со справочником препаратов само по себе не означает, что локальный продукт продаваем или юридически взаимозаменяем.
7. Override — действие фармацевта с отдельным permission, ограниченным reason code, обоснованием, если оно требуется политикой, и неизменяемым аудитом. AI не может выдать permission или разрешить отпуск.
8. Каждое отпущенное количество должно быть связано со строкой рецепта, sale item, lot allocation, фармацевтом, временем и результатом.
9. Повторные запросы, callbacks оплаты и параллельные экземпляры приложения не должны дважды учитывать одно количество.
10. Исторические клинические и dispense-записи нельзя терять из-за каскадного удаления пациента. Retention и anonymization должны быть явной политикой.

## 3. Предлагаемые канонические связи

### Prescription header

Сохранить `Prescription` как заголовок и добавить:

- pharmacy ownership (nullable только для legacy-записей на время миграции);
- сведения об issuer/prescriber и provenance;
- явные issue/expiry timestamps с согласованной timezone-семантикой;
- контролируемый lifecycle status: например draft, active, on_hold, cancelled, expired, exhausted;
- jurisdiction/policy reference только из доверенной конфигурации аптеки;
- actor и timestamps создания/проверки.

Существующий `product_id` сохранить как legacy compatibility field до миграции потребителей. Один product не должен представлять весь рецепт.

### Prescription lines

Добавить `PrescriptionLine` с полями:

- ссылка на prescription header;
- нормализованная medication identity (reference ID, если доступен) и неизменяемый name snapshot;
- необязательная ссылка на конкретный назначенный локальный product;
- snapshots strength и dosage form;
- quantity per authorized fill и unit of measure;
- authorized refill count и явная политика fill cycle;
- directions/instructions и клинически значимые route/frequency, если поддерживаются;
- line status и timestamps.

Разрешать product только детерминированной политикой. Не выводить возможность замены из сходства или ответа AI.

### Sale и sale items

- Добавить необязательную patient ownership в `Sale`; все prescription-backed lines одной продажи должны относиться к одному пациенту и одной аптеке.
- Добавить необязательную ссылку на prescription line в `SaleItem`. OTC-позиции могут оставаться без рецепта.
- Если передана prescription line, patient и pharmacy ownership должны быть получены/проверены по сохранённому рецепту, а не доверяться клиенту.
- Сохранить текущие FEFO lot allocations как inventory trace. Prescription dispense ссылается на sale item, чьи allocations определяют фактически отпущенные серии.
- Idempotency comparison должен учитывать patient и prescription-line associations, а не только product и quantity.

### Dispense ledger

Добавить долговечный `PrescriptionDispense` ledger, связывающий одну строку рецепта с одной строкой продажи и хранящий:

- количество и единицу измерения;
- номер fill cycle;
- pharmacy, pharmacist/actor и timestamps;
- idempotency key;
- lifecycle state: reserved, dispensed, released, reversed;
- reason code и ссылку на correction/reversal.

Ledger является источником истины для исполненного количества и использования повторных отпусков. Кэшированные счётчики в строках рецепта — только проекции, которые можно сверить с ledger. Историю отпуска нельзя удалять для отмены операции.

Отдельная append-only transition/audit запись должна фиксировать каждое изменение состояния, actor, reason и correlation reference. Не помещать клинические payloads в обычные логи или outbox events.

## 4. Состояния и транзакционные гарантии

| Событие | Inventory effect | Dispense ledger effect | Sale/payment effect |
|---|---|---|---|
| Cash checkout принят | FEFO stock decrement в транзакции | Создать dispensed entry | Sale completed; cash payment succeeded |
| External-payment checkout | FEFO stock reservation | Создать reserved entry | Sale awaiting payment; payment pending |
| Подписанный payment success | Зафиксировать списание резерва | reserved → dispensed | Sale completed; payment succeeded |
| Подписанный payment failure | Освободить резерв | reserved → released | Sale cancelled; payment failed |
| Отмена pending sale | Освободить резерв ровно один раз | reserved → released | Sale cancelled |
| Correction/reversal завершённой продажи | Только явно разрешённая inventory compensation, если политика допускает | Добавить reversal/correction evidence, не удаляя исходный отпуск | Отдельный аудируемый процесс correction/refund |

Перед расчётом остатка и refill availability необходимо блокировать строки prescription line в детерминированном порядке ID. Inventory rows также блокировать в детерминированном порядке. Sale, payment, dispense ledger, inventory movement journal и outbox event должны фиксироваться в одной PostgreSQL transaction при checkout и payment settlement.

Для dispense использовать pharmacy-scoped idempotency key и уникальное ограничение БД как последний барьер от дубликатов. При ошибке транзакции все связанные изменения откатываются вместе. Для будущих межсервисных операций нужно документировать и тестировать saga/compensation contract, а не заявлять атомарность БД между сервисами.

Partial dispensing представляется несколькими ledger entries в рамках одного разрешённого fill cycle. Следующий refill cycle нельзя начинать, пока настроенная политика не разрешает его и повторный отпуск не авторизован. Конкретное правило задаётся политикой; универсальные законодательные требования не предполагаются.

## 5. Граница авторизации и валидации

- Сервер проверяет активное pharmacy membership при каждом чтении и изменении.
- Перед загрузкой prescription или clinical context пациент проверяется SQL-предикатом с pharmacy scope.
- Prescription header и каждая line проверяются на одну аптеку и одного пациента.
- Проверяются status, issue/expiry, medication identity, strength, dosage form, remaining quantity, fill cycle, refill allowance и sellability продукта.
- При отсутствии, устаревании или неподдерживаемой юрисдикции/наборе правил система отказывает по принципу fail-closed.
- Результат MCP `verify_prescription` не является authorization token или командой на отпуск. Это advisory result; его необходимо отдельно исправить и проверить на канонической модели.
- Ответственным за решение остаётся фармацевт. AI может объяснять проверки и приводить источники, но не утверждать исключения, менять статус рецепта или выполнять отпуск.

## 6. Стратегия миграции и совместимости

1. Добавить nullable pharmacy ownership и нормализованные line/ledger tables без выдумывания принадлежности для исторических записей.
2. Заполнять pharmacy ownership рецепта только по однозначной существующей связи patient-to-pharmacy. Неоднозначные/непривязанные записи оставить unassigned и закрыть для обычного pharmacist access.
3. Сохранить существующие prescription number и текстовые поля; не интерпретировать старый dosage text как структурированные quantity, strength или form.
4. Заменять каскадное удаление patient на retention-safe restriction только после проверки путей удаления и retention policy. Исторические рецепты и dispense evidence не должны удаляться незаметно.
5. Временно сохранить старые privileged endpoints, но не открывать их ролям фармацевтов. Потребителей перевести на purpose-bound tenant-scoped contracts.
6. Не строить миграцию на предположениях о Production данных. Проверить upgrade/downgrade на чистом PostgreSQL и synthetic legacy dataset с привязанными и непривязанными пациентами.
7. Не изменять и не развёртывать Production database в рамках source-level реализации.

## 7. Требуемое поведение API

Нужны pharmacist-facing versioned contracts для:

- списка и чтения рецептов в пределах аутентифицированной аптеки и patient scope;
- создания/импорта рецепта с provenance и проверенной ownership;
- чтения строк рецепта и остатка разрешённого количества;
- проверки рецепта для предполагаемого отпуска (read-only advisory result);
- создания dispense через POS transaction boundary;
- permissioned reason-coded override;
- отмены/освобождения pending dispense;
- записи correction/reversal без удаления исторических доказательств.

POS checkout должен оставаться обратно совместимым для обычных OTC-продаж. Prescription-backed checkout должен быть явно обозначен и проверяться сервером. Нельзя включать отпуск по рецепту в браузере до прохождения API и database gates.

## 8. Критерии приёмки

Проверки выполняются на PostgreSQL с synthetic data, а не только на mocks:

- Рецепт пациента A нельзя использовать для пациента B.
- Pharmacy A не может читать или отпускать рецепты Pharmacy B при подмене ID, filters или pagination.
- Отсутствующая/unassigned legacy pharmacy ownership приводит к fail-closed.
- Неактивное membership и superuser-only пути отклоняются для pharmacist dispensing.
- Expired, cancelled, on-hold, exhausted и другие недействительные рецепты отклоняются.
- Несовпадение product, medication identity, strength или dosage form отклоняется.
- Количество выше оставшегося разрешённого количества отклоняется.
- Refill сверх разрешённого числа или до выполнения fill-cycle condition отклоняется.
- Partial dispense корректно обновляет остаток и не расходует лишний refill.
- Две параллельные операции не могут отпустить больше последнего разрешённого количества.
- Cash checkout создаёт ровно один dispense и одно списание inventory.
- External-payment checkout резервирует ровно один раз; signed success фиксирует один раз; failure/cancellation освобождает один раз.
- Повтор запроса и webhook идемпотентны; повторное использование ключа с другим payload возвращает conflict.
- Rollback не оставляет orphan sale, dispense, movement или outbox event.
- Override требует permission и reason и создаёт неизменяемое audit evidence.
- Reversal/correction сохраняет исходный ledger и создаёт compensating record.
- Prescription и dispense history переживают запрещённые пути удаления пациента.
- Ни один AI/MCP tool не может разрешить или выполнить отпуск.

## 9. Маркировка доказательств готовности

Каждая возможность отдельно отмечается как **Designed**, **Implemented**, **Tested**, **Staged-validated** или **Production-validated**. Успешные model tests или merge PR не доказывают завершённость pharmacist workflow или production readiness.

## 10. Явные ограничения

- Документ не утверждает конкретные юридические правила какой-либо страны.
- Нет автоматической терапевтической замены или AI clinical authorization.
- Нет миграции/исправления реальных данных пациентов без отдельного утверждённого плана сверки.
- Нет изменений Production database, настроек payment provider или деплоя.
