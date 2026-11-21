# P0 Pharmacist Workspace — аудит контрактов реализации

**Базовая версия аудита:** `main`, commit `d6aaeb5ce1c1ed7d39d2c13ac05abb55e0bb5a23` (2026-11-21).  
**Область:** проверка исходного кода POS, prescriptions, истории покупок пациентов, generated API client и browser tests. Код приложения не изменялся. Production DB, данные пациентов, платёжный провайдер и runtime развёрнутого приложения не использовались.

Документ дополняет [критерии приёмки P0](./PHARMACIST_WORKSPACE_P0_ACCEPTANCE.ru.md) и фиксирует реально существующие контракты, чтобы реализация опиралась на API, а не на названия моделей или предполагаемые экраны.

## 1. Текущее состояние

| Область | Подтверждённое состояние исходного кода | Следствие для P0 |
|---|---|---|
| POS route | `/_authenticated/pos` подключает `Pos`, но `src/features/pos/index.tsx` возвращает `null`. | Маршрут существует, интерфейса рабочего места нет. |
| Поиск товаров | `GET /api/v1/pos/products/search?q=&pharmacy_id=&limit=`; аутентифицированный пользователь; сервер вызывает `require_pharmacy_tenant`; ответ — `POSProductResponse[]`. | Backend-контракт поиска каталога существует; нужны generated client и интеграция UI. |
| Поиск партий | `GET /api/v1/pos/products/{product_id}/lots?pharmacy_id=`; аутентификация и tenant-проверка; возвращает lot number, expiry, on-hand/reserved/available и флаг отсутствующей даты expiry. | UI обязан показывать остатки и неопределённость срока годности на уровне партии. |
| Checkout | `POST /api/v1/pos/checkout`; `SaleCreate` → `SaleResponse`; аутентификация и tenant-проверка. | Существующий транзакционный endpoint поддерживает cash и создание внешнего платежа. |
| Чтение продажи | `GET /api/v1/pos/sales/{sale_id}`; аутентифицированный пользователь; tenant проверяется по аптеке продажи. | Получение конкретного чека/статуса есть; endpoint списка продаж в этом POS router не найден. |
| Отмена ожидающего платежа | `POST /api/v1/pos/sales/{sale_id}/cancel`; tenant-scoped; отменять можно только `awaiting_payment`. | Это не процесс возврата/refund завершённой продажи. |
| Внешний платёж | `POST /api/v1/pos/payments/webhook`; HMAC-SHA256 по raw body с `PAYMENT_WEBHOOK_SECRET`; pending payment переводится в succeeded/failed, резерв товара списывается или освобождается. | Адаптер провайдера, подпись, retry и staging contract tests остаются интеграционными зависимостями. |
| Приёмка товара | `POST /api/v1/pos/inventory/receive`; tenant-scoped, идемпотентная приёмка одной партии. | Это не полный цикл supplier purchase order, delivery note, invoice и discrepancy handling. |
| Рецепт | Модель `Prescription` существует. `GET/POST /api/v1/prescriptions` в `pharmacy_entities.py` требуют `CurrentSuperuser`. | Эти endpoints не являются pharmacist prescription workflow. |
| История покупок пациента | `GET /api/v1/patient-purchases/` требует `CurrentSuperuser` и выбирает покупки глобально, без фильтрации по пациенту/аптеке. | Нельзя подключать endpoint к истории пациента в интерфейсе фармацевта. |
| Generated POS client | Скрипт `scripts/generate-api-client.sh` генерирует клиент в `frontend/shadcn-admin/src/client`; этот каталог и POS service/model файлы отсутствовали в проверенной ветке. В package manifest frontend не объявлен `openapi-typescript-codegen`. | Нужен воспроизводимый и закреплённый по версии процесс генерации, затем интеграция UI с generated contract. |
| Browser E2E | Playwright config использует `frontend/shadcn-admin/e2e`, Chromium и mobile Chromium. В проверенной E2E suite найдены сценарии authentication; POS E2E сценарий не найден. | Нужны POS journey tests; успешный общий E2E CI не доказывает приёмку POS. |

## 2. Контракт POS API

### Поиск товаров

`GET /api/v1/pos/products/search`

- Query: `q` (2–100 символов), обязательный положительный `pharmacy_id`, `limit` (1–100, по умолчанию 20).
- Авторизация: `CurrentUser` и `require_pharmacy_tenant(pharmacy_id, user, db)`.
- Поля поиска: название, SKU, INN, производитель, regulatory ID, GTIN, barcode, dosage strength и dosage form.
- Ответ содержит идентификаторы товара, strength/form, units per pack, производителя, INN, идентификаторы, цену, доступный остаток и medicinal-product ID.

### Партии и сроки годности

`GET /api/v1/pos/products/{product_id}/lots?pharmacy_id={id}`

- Возвращает inventory ID, lot number, expiry date, quantity, reserved quantity, available quantity и `expiry_date_missing`.
- Сначала идут партии с известной датой expiry, затем партии без неё.
- **Важный пробел политики:** текущие search и checkout допускают партии с `expires_at IS NULL`. UI не должен незаметно показывать остаток без даты срока годности как проверенный безопасный остаток. До dispensing владелец бизнес-процесса должен определить: блокировать такие партии, требовать разрешённое исключение или применять документированную политику для legacy-данных.

### Checkout

`POST /api/v1/pos/checkout`

Request schema:
- `pharmacy_id`
- `idempotency_key` (8–100 символов)
- `items[]`: уникальный `product_id` и положительный `quantity`
- необязательный неотрицательный `discount_total`
- `payment_method`: `cash | card_terminal | online`
- `cash_received` обязателен только для cash

Поведение сервера:
- Повторно проверяет membership пользователя в аптеке и активность продаваемых товаров.
- Сам рассчитывает цены и итог; отклоняет некорректную скидку и недостаточную сумму наличных.
- Блокирует строки inventory и распределяет партии по FEFO: `expires_at ASC NULLS LAST`.
- Использует tenant-scoped idempotency key и PostgreSQL transaction advisory lock.
- Cash checkout списывает остаток и завершает продажу; card_terminal/online резервирует остаток и создаёт продажу `awaiting_payment`.
- В одной транзакции сохраняет sale items, lot allocations, payment state и outbox event.
- При нехватке доступного остатка не фиксирует частичную продажу.

Response содержит receipt number, pharmacy, totals, sale status, timestamps, позиции с lot allocations, payments и cash change.

**Frontend обязан считать ответ сервера authoritative.** Не доверять клиентским расчётам итоговой цены, остатков, FEFO allocation, payment state или идентификатора чека.

## 3. Пробел в связке Prescription и Patient

Текущая модель `Sale` содержит pharmacy и cashier ownership, но не имеет `patient_id` или `prescription_id`. `SaleItem` связан с product и lot allocations, но не с prescription lines. Модель `Prescription` хранит patient, необязательный product, prescription number, dosage, instructions, status, issue/expiry dates, но не предоставляет dispense ledger и учёт оставшегося количества/refills.

Текущие generic list/create routes для prescriptions доступны только `CurrentSuperuser` и используют базовую схему. Они не реализуют pharmacist-level проверку принадлежности пациента аптеке, валидности рецепта, совпадения medication/strength/form/quantity, partial dispensing, авторизацию override или audit reason.

Следовательно, P0.2 требует согласованного domain/API design и миграции. Его нельзя реализовать простым добавлением выбора рецепта на текущий POS экран.

## 4. Граница доступа к истории пациента

`GET /api/v1/patient-purchases/`:
- Требует `CurrentSuperuser`.
- Применяет только pagination.
- Напрямую запрашивает `PatientPurchase`, не присоединяет `Patient` и не ограничивает данные через `Patient.pharmacy_id`.
- Возвращает patient identifiers и сведения о покупках.

Это глобальный административный endpoint, а не API истории пациента для фармацевта. Новый pharmacist-facing endpoint должен получать pharmacy membership из authenticated principal, проверять выбранного пациента относительно этой аптеки, определить обработку legacy `Patient.pharmacy_id = NULL`, минимизировать поля ответа, записывать audit event и иметь cross-tenant negative tests. Неопределённые legacy-записи должны работать по fail-closed до reconciliation.

## 5. Рекомендуемая последовательность реализации

1. **P0.3 — Граница Patient History API:** сначала определить и протестировать server-derived pharmacy/patient scope.
2. **P0.2 — Prescription и dispensing domain:** определить связи sale/patient/prescription/dispense, проверки рецепта, partial dispensing, разрешённые overrides, reversals и audit semantics.
3. **P0.1 — POS workspace:** реализовать UI на основе закреплённых/generated API contracts; обработать loading, empty, error, stock, lot, expiry, payment и receipt states. Prescription dispensing оставить отключённым до завершения P0.2.
4. **P0.4 — Staged Mortarium isolation:** проверить переключение пациентов, no-patient scope, sync/streaming, Redis memory, PostgreSQL checkpoints, caches, multi-instance behavior и secret rotation в контролируемой synthetic-среде.

## 6. Минимальная приёмка через browser и integration tests

- Фармацевт не может искать, читать или выполнять транзакции в неразрешённой аптеке.
- Поиск поддерживает название, INN, SKU/barcode, strength и form; результаты показывают остаток и оговорки по expiry.
- FEFO allocation в чеке точно совпадает с ответом сервера.
- Cash checkout завершается один раз; повтор с тем же key возвращает ту же продажу без повторного списания.
- Card-terminal/online checkout остаётся pending до валидного подписанного webhook.
- Ошибка платежа и отмена освобождают точные резервы ровно один раз.
- Для недостаточного остатка, expired lots, политики missing expiry, устаревшей цены, повторной отправки и конкурентной продажи последней единицы есть явное UI/error behavior.
- Последовательность Patient A → Patient B → no patient не допускает утечки history, prescription, cache или AI state.
- Dispensing по рецепту заблокирован, пока серверная проверка рецепта и dispense accounting не завершились успешно.
- Cross-tenant negative tests выполняются на PostgreSQL; browser E2E использует только synthetic data.

## 7. Ограничения доказательств

Последний проверенный head PR — `01e9220c43b5e7f8d3de5f28f117a771f7600b9c`; базовая версия исходного аудита — текущий `main` на `d6aaeb5ce1c1ed7d39d2c13ac05abb55e0bb5a23`. Проверенные POS API файлы на main совпадают с исходниками ветки PR. CI для head документационного PR завершился успешно, включая integration tests, unit tests, RAG Safety Regression, frontend build/tests и Playwright E2E. Однако Playwright suite не подтверждает POS browser acceptance.

Production runtime, database, реальные данные пациентов и внешний payment provider не использовались. Это аудит исходного кода и контрактов, а не production validation или клиническая/регуляторная сертификация.

## Повторный аудит исходного кода — main 481a86aa

В актуальном `main` присутствуют изменения PHI governance и tenant-scope Patient Repository. См. [аудит доступа к PHI](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [инвентаризацию чтения PHI](../security/PHI_READ_SURFACE_INVENTORY.md) и регрессионное покрытие `tests/unit/test_patient_repository_tenant_scope.py`. В проверенных путях Patient Repository теперь применяются pharmacy-scope predicates. Это не создаёт API истории пациента для фармацевта и не подтверждает минимизацию ответа/аудит чтений. P0.3 сохраняется: server-resolved pharmacy membership, fail-closed для legacy-пациентов без назначения аптеки, минимальные поля ответа, аудит чтений, пагинация и PostgreSQL negative tests для межаптечного доступа. Это подтверждение по исходному коду, не production validation.
