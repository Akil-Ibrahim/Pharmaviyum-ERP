# Трассировка реализации аптечных процессов Pharmaviyum

[English](./PHARMACY_WORKFLOW_TRACEABILITY.md) · [Русский](./PHARMACY_WORKFLOW_TRACEABILITY.ru.md)

**Тип аудита:** трассировка реализации по исходному коду  
**Проверенная базовая версия:** `main`, commit `2616b4209fc037b1e4f1899b876478bf72258641` (2026-11-22)  
**Ветка документации:** `docs/pharmacy-business-value-kpis`  
**Доступ к runtime / production:** не выполнялся

## 1. Назначение и правила доказательности

Матрица связывает 12 групп аптечных процессов с подтверждениями в репозитории: доменными моделями, API-контрактами, frontend-маршрутами/компонентами и автоматизированными тестами.

Наличие модели, endpoint, пункта навигации, макета экрана, RAG-документа или тестового плана само по себе не доказывает, что полный аптечный процесс можно выполнить.

Статусы:

- **Реализовано и протестировано (backend):** существует реальный API/domain transition и соответствующий автоматизированный тест. Это не означает наличие полноценного UI или production-подтверждения.
- **Частично:** часть доменной или API-функциональности существует, но отсутствует один или несколько обязательных переходов, контролей, UI-экранов либо тестов.
- **Не реализовано / не подтверждено:** по проверенному коду не удалось установить исполняемую сквозную возможность.
- **Только AI-поддержка:** Mortarium может объяснить процесс или прочитать разрешённые ERP-данные, но не выполняет бизнес-транзакцию.

## 2. Матрица трассировки процессов

| № | Аптечный процесс | Домен / API — подтверждения | Frontend — подтверждения | Тесты — подтверждения | Статус по исходному коду |
|---:|---|---|---|---|---|
| 1 | Подготовка к открытию и готовность смены | Не обнаружены сущность открытия смены, API открытия кассы, состояние opening checklist или транзакция готовности персонала. | Рабочий экран открытия смены не обнаружен. | Тест открытия смены не обнаружен. | **Не реализовано / не подтверждено.** |
| 2 | Консультация пациента и отпуск препарата | POS search, просмотр серий, checkout, FEFO, payment, receipt, inventory movement и outbox реализованы. Отдельные patient AI-profile и pharmacist purchase-history read APIs требуют purpose/pharmacy membership, проверяют ownership пациента и создают metadata-only PHI audit. Сам checkout по-прежнему не связан с patient или prescription. | Активный POS route импортирует `Pos`, но `frontend/shadcn-admin/src/features/pos/index.tsx` сейчас возвращает `null`. Маршрут пациентов также возвращает `null`. | `test_pos_checkout.py`, `test_ai_patient_profile_access.py` и `test_patient_history_tenant_scope.py` проверяют отдельные backend capabilities, но не интегрированный dispensing workflow. | **Частично.** Есть транзакционный POS и scoped patient-read APIs; patient-linked checkout, prescription linkage и рабочий POS UI не подтверждены. |
| 3 | Проверка рецепта и уточнение назначения | Модель `Prescription` и привилегированные list/create endpoints по `/api/v1/prescriptions`. Отдельный placeholder router возвращает пустой список / 404 и не является рабочей реализацией процесса. Checkout не принимает и не проверяет рецепт. | `prescriptions.tsx` возвращает `null`. | Интеграционный тест связи рецепта с отпуском не обнаружен. | **Частично.** Есть базовый CRUD для привилегированных пользователей; проверка назначения, клиническая валидация, review фармацевтом и связь с отпуском не подтверждены. |
| 4 | Онлайн-заказы и обратная связь с пациентом | Модель `Order` и endpoints `/orders/`, `/orders/{id}`, `/orders/{id}/status`. В модели нет товарных строк; завершение создаёт одну агрегированную запись `PatientPurchase`, а не item-level fulfillment. | `orders.tsx` возвращает `null`. | `tests/api/test_orders.py` проверяет API заказов и изоляцию между tenant. | **Частично.** Есть общие записи заказов пациента; приём онлайн-заказов, комплектация позиций, выдача, уведомления и follow-up не подтверждены. |
| 5 | Проверка наличия в других филиалах и перенаправление пациента | Inventory и POS lookup ограничены авторизованной аптекой. Агрегированный поиск наличия по филиалам и полный lifecycle отправки/приёмки transfer не обнаружены. | `transfers.tsx` возвращает `null`. | Тест сквозного межфилиального transfer не обнаружен. | **Не реализовано / не подтверждено** для межфилиального процесса. Поиск остатков в одной аптеке существует. |
| 6 | Заказы поставщикам, накладные и приёмка товара | Модель Supplier и привилегированные endpoints `/api/v1/suppliers` для list/create. `POST /api/v1/pos/inventory/receive` может создать серию и записать goods-receipt movement, но запрос не содержит supplier, purchase order, invoice, delivery note или discrepancy reference. Доменная модель и lifecycle purchase order не обнаружены. | `suppliers.tsx` и `procurement.tsx` возвращают `null`. | Интеграционный тест purchase order или supplier goods receipt не обнаружен. | **Частично.** Есть записи поставщиков и отдельная приёмка серии; сквозная трассировка закупки до приёмки отсутствует. |
| 7 | Пополнение полок и управление отсутствующими товарами | Inventory хранит reorder level; listing API поддерживает low-stock фильтр; Mortarium может читать inventory overview/low-stock. Workflow пополнения и заказа поставщику не обнаружен. | Inventory и procurement routes возвращают `null`. | Тест lifecycle пополнения не обнаружен. | **Частично.** Просмотр остатков есть; исполнение пополнения не подтверждено. |
| 8 | Контроль остатков, расхождения и подготовка инвентаризации | `Inventory` — баланс аптеки/серии; `InventoryMovement` — журнал движений. Privileged adjustment endpoint требует причину и idempotency key. | `inventory.tsx` и `batches.tsx` возвращают `null`. | `tests/integration/test_inventory_movement_ledger.py` проверяет atomicity/idempotency. Полный тест stocktake/count-and-reconciliation не обнаружен. | **Частично.** Примитивы движений и корректировки есть; контролируемая инвентаризация, двойной пересчёт, обработка расхождений и approval не подтверждены. |
| 9 | Документы, отчёты и сроки | `GET /api/v1/dashboard/summary` предоставляет операционные агрегаты. Общий реестр задач/deadlines и lifecycle отчёта закрытия смены не обнаружены. | Dashboard существует; специализированные экраны отчётности не подтверждены. | Есть тесты tenant scope dashboard; тест процесса end-of-day report не обнаружен. | **Частично.** Агрегаты dashboard доступны; управление операционными документами и сроками не подтверждено. |
| 10 | Координация команды и внешняя профессиональная коммуникация | User, pharmacy и membership records дают основу идентификации и доступа. Не обнаружены назначение задач сотрудникам, сообщения передачи смены, коммуникация с врачом, журнал звонков или контакты представителей. | Активный рабочий экран такого процесса не подтверждён. | Тест процесса координации/коммуникации не обнаружен. | **Не реализовано / не подтверждено.** |
| 11 | Сверка, закрытие смены и передача следующему фармацевту | POS sales/payments и inventory movements существуют, но не обнаружены модель кассовой смены, транзакция закрытия кассы, сверка наличных, запись handover или lifecycle владения нерешёнными задачами. | Рабочий экран закрытия/передачи смены не обнаружен. | Тест закрытия смены или handover не обнаружен. | **Не реализовано / не подтверждено.** |
| 12 | Поддержка аптечных процессов через Mortarium | Зарегистрированы пять read-only MCP tools: поиск препаратов, обзор остатков, контроль сроков годности, сводка продаж и workflow guide. Используются request-scoped identity и pharmacy context; инструменты не изменяют ERP-записи. Код изоляции patient-scoped API и LangGraph state объединён; staged end-to-end validation остаётся незакрытой. MCP `get_patient_history` пока не связан с выбранным patient/purpose и не пишет PHI access audit; он может запросить другого активного пациента в той же аптеке. | UI Mortarium существует как ограниченный decision-support интерфейс; это не выполнение транзакций. | `tests/unit/ai/test_pharmacy_operations_mcp.py` проверяет регистрацию/schema contracts. Patient-scoped API session HMAC v3 и Agent/RAG checkpoint namespaces объединены в main через PR #287 с regression tests; staged-проверка переключения пациентов на PostgreSQL checkpoint + Redis memory остаётся release gate. | **Read-only поддержка реализована; код patient-scoped state объединён, staged validation ожидается.** |

## 3. Важные уточнения после сверки

### 3.1 POS backend существует; часть старой документации устарела

В проверенном коде есть подключённый POS router:

- `GET /api/v1/pos/products/search`;
- `GET /api/v1/pos/products/{product_id}/lots`;
- `POST /api/v1/pos/checkout`;
- `POST /api/v1/pos/payments/webhook`;
- `POST /api/v1/pos/inventory/receive`.

Checkout сохраняет товарные строки продажи, состояние оплаты, идентификатор чека, FEFO allocations, inventory movements и outbox event. При оплате наличными остаток списывается; при безналичной оплате резервируется до получения подписанного payment webhook. Для idempotency и ключевых stock/payment инвариантов существуют интеграционные тесты.

Следовательно, утверждения в старых POS/load-test документах об отсутствии checkout/receipt/FEFO transaction в backend нужно обновить или уточнить. Но наличие backend-контракта ещё не означает завершённый аптечный процесс: активный POS React feature сейчас возвращает `null`, checkout не связан с пациентом/рецептом, а возвраты/refunds/закрытие кассовой смены этим аудитом не подтверждены.

### 3.2 Goods receipt не равен закупке и приёмке по накладной

Отдельный endpoint приёмки серии не реализует lifecycle purchase order. Он не подтверждает поставщика, не сопоставляет purchase order, invoice и delivery note, не поддерживает подтверждённую частичную приёмку, согласование расхождений или возврат поставщику.

### 3.3 История пациента теперь выделена в отдельную purpose-bound read-поверхность

Legacy `GET /patient-purchases/` остаётся доступен только `CurrentSuperuser` и требует явный `pharmacy_id`. Его query теперь соединяет `Patient` и фильтрует по `Patient.pharmacy_id`, но по-прежнему возвращает более широкий административный purchase projection и не создаёт новый PHI access audit event.

Отдельный pharmacist-facing `GET /api/v1/patient-purchases/{patient_id}/history` требует явные pharmacy и purpose, active `PharmacyMembership` и принадлежность активного пациента аптеке. Он запрещает superuser и пациентов с null/unassigned pharmacy ownership, возвращает только purchase ID/product name/category/quantity/timestamp и записывает metadata-only allowed/denied `PHIAccessAudit`. `tests/integration/test_patient_history_tenant_scope.py` покрывает allowed access, cross-pharmacy denial, missing membership, null-owner denial и superuser denial.

`GET /api/v1/patients/{patient_id}/ai-profile` имеет аналогичный explicit pharmacy/purpose/membership gate и metadata-only audit; тесты находятся в `tests/integration/test_ai_patient_profile_access.py`. Это защищённые read workflows, а не клинический dispensing: checkout всё ещё не связан с patient/prescription, а POS React feature возвращает null.

### 3.4 Пункт меню не означает готовый workflow

Несколько активных frontend routes сейчас возвращают `null`: POS, patients, prescriptions, inventory, batches, suppliers, orders, transfers и procurement. Sidebar entry или сгенерированный route не доказывает наличие рабочего процесса.

## 4. Приоритетная последовательность реализации

1. **P0 — Восстановить рабочие UI-поверхности** POS и Pharmacist Workspace, подключить существующие API-контракты и проверить browser-level journeys.
2. **P0 — Связать пациента и рецепт с отпуском:** определить patient/prescription association, server-side validation, профессиональную проверку и audit до отпуска.
3. **P0 — Закрыть доступ к данным пациентов:** устранить отсутствие tenant-scoped доступа к patient purchases и завершить staged-проверку LangGraph patient-session isolation; добавить negative cross-pharmacy и cross-patient tests.
4. **P1 — Реализовать procurement lifecycle:** purchase order, строки поставщика, ссылки на накладную/invoice, частичная приёмка, расхождения и аудируемое проведение серий.
5. **P1 — Возвраты, refunds, voids и обратные движения остатков** с idempotent compensating movements.
6. **P1 — Инвентаризация и межфилиальные transfers** с подтверждением отправки/приёмки, расхождениями и tenant-safe concurrency.
7. **P1 — Кассовые смены и end-of-day reconciliation:** кассир/касса, expected-vs-counted cash, согласование расхождений и ответственность при handover.
8. **P2 — Онлайн-заказы и коммуникации:** item-level order lifecycle, проверка личности при выдаче, уведомления и follow-up.
9. **P2 — Операционные задачи и отчётность:** opening/closing checklists, deadlines, ответственные и очередь исключений.

## 5. Границы проверки

Это аудит исходного кода репозитория, а не доказательство поведения развёрнутой системы. Production database, реальные записи пациентов, платёжный провайдер, работающая аптека и FastAPI Cloud runtime не проверялись. Успешный CI подтверждает только проверки, которые реально выполнил данный run; он не делает незавершённый UI или бизнес-процесс реализованным.

Перед изменением статуса реализации требуются доказательства на всех соответствующих уровнях: model/schema, авторизованный API, frontend behavior, automated tests, совместимость миграций и воспроизводимая runtime-проверка.

## Повторный аудит исходного кода — main 481a86aa

В актуальной main добавлены документы PHI governance и pharmacy-scope predicates в проверенных путях Patient Repository с регрессионными тестами. См. [аудит доступа к PHI](../architecture/PHI_ACCESS_GOVERNANCE_AUDIT.md), [инвентаризацию чтения PHI](../security/PHI_READ_SURFACE_INVENTORY.md) и `tests/unit/test_patient_repository_tenant_scope.py`. Workflow истории пациента остаётся частичным: эти repository predicates не создают API истории для фармацевта и не подтверждают минимизацию ответа, аудит чтений, пагинацию или API-level запрет межаптечного доступа. P0.3 остаётся открытым до реализации и тестирования этих контролей на уровне API. Только source audit; production validation не выполнялась.
