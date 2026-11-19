# Архитектурные решения (ADR)

[English](README.md) · **Русский**

ADR фиксируют решения, влияющие на границы системы, владение данными, безопасность, эксплуатацию и долгосрочное развитие Pharmaviyum.

## Индекс решений

| ID | Тема решения | Русская версия | Английский оригинал | Статус |
|---|---|---|---|---|
| ADR-0001 | WebSocket Gateway внутри FastAPI | [Русская версия](./ADR-0001-websocket-gateway.ru.md) | [WebSocket Gateway](./ADR-0001-websocket-gateway.md) | Принято; реализация пока development template |
| ADR-0002 | Offline-first Central + Pharmacy Edge | [Русская версия](./ADR-0002-offline-first-central-edge.ru.md) | [Central + Pharmacy Edge](./ADR-0002-offline-first-central-edge.md) | Предложено; rollout и production-валидация не завершены |
| ADR-0003 | Изоляция состояния Mortarium по пациенту | [Русская версия](./ADR-0003-patient-scoped-ai-state.ru.md) | [Patient-scoped AI state](./ADR-0003-patient-scoped-ai-state.md) | Принято; код влит PR #287, staged release gate ожидает подтверждения |
| ADR-0004 | Изолированная offline-оценка Ragas | [Русская версия](./ADR-0004-offline-ragas-evaluation.ru.md) | [Offline Ragas evaluation](./ADR-0004-offline-ragas-evaluation.md) | Принято; eval group в pyproject.toml, вне production request path |
| ADR-0005 | Цены в рамках аптечного tenant и операционные роли | [Русская версия](./ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.ru.md) | [Tenant-scoped pricing and pharmacy RBAC](./ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.md) | Предложено; требуется валютная политика, миграция и управление аптечными ролями |
| ADR-0006 | Неизменяемый журнал движений запасов | [Русская версия](./ADR-0006-inventory-movement-ledger.ru.md) | [Append-only Inventory Movement Ledger](./ADR-0006-inventory-movement-ledger.md) | Предложено; требуется перевести все пути изменения запасов и проверить сверку |
| ADR-0007 | Упорядоченный идемпотентный Central Inbox Consumer | [Русская версия](./ADR-0007-central-inbox-consumer.ru.md) | [Central Inbox Consumer](./ADR-0007-central-inbox-consumer.md) | Предложено; Inbox только принимает события, запуск Consumer блокируют исходные остатки/события и sale projection |
| ADR-0008 | Международный справочник лекарств и медицинских изделий | [Русская версия](./ADR-0008-international-medicine-and-device-reference-catalog.ru.md) | [International medicine and medical-device reference catalog](./ADR-0008-international-medicine-and-device-reference-catalog.md) | Принято; источники, адаптеры, миграции, тесты и rollout ещё предстоят |

## Значения статусов

- **Предложено (Proposed):** решение ещё не является утверждённым эксплуатационным контрактом; реализация и/или проверка могут быть неполными.
- **Принято (Accepted):** архитектурное направление одобрено, но реализация может оставаться частичной.
- **Реализовано (Implemented):** код, тесты и эксплуатационные меры соответствуют решению; должны быть приведены проверяемые доказательства.
- **Заменено (Superseded):** решение заменено более поздним ADR; исходная запись сохраняется для истории.

Статус Accepted сам по себе не доказывает Production readiness.

## Стандарт оформления ADR

Каждый ADR должен содержать статус и дату, контекст, ограничения, решение, альтернативы, последствия, влияние на безопасность и данные, план миграции, доказательства валидации и ссылки. Не переписывайте историческое решение незаметно; при изменении архитектуры создавайте новый ADR.
