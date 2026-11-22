# Системный контекст и архитектура Pharmaviyum

**Статус:** справочник текущей архитектуры.

## Назначение

Pharmaviyum — ERP/CRM-платформа для аптек. Детерминированное приложение и транзакционная база данных являются system of record. Mortarium — AI-помощник фармацевта; он не является источником полномочий для отпуска лекарств, ценообразования, изменения остатков, платежей, прав доступа или регуляторных решений.

## Логический контекст

Система включает React/TypeScript frontend, FastAPI modular monolith, authentication и tenant authorization, аптечные domain modules, PostgreSQL, Redis-compatible cache/memory, Celery workers, LangGraph agent/RAG workflows Mortarium, MCP tools и OpenTelemetry.

Это логические компоненты; они не обязательно являются отдельными deployable services.

## Границы runtime

| Граница | Ответственность | Полномочия |
|---|---|---|
| React frontend | Взаимодействие, формы, навигация и отображение | Не имеет бизнес-полномочий; client input недоверенный |
| FastAPI API | Authentication dependencies, request validation, tenant context и API contracts | Проверяет доступ до защищённых операций |
| Domain modules | Pharmacy, patient, catalog, inventory, procurement, POS и audit rules | Авторитетная бизнес-логика приложения |
| PostgreSQL | Транзакционные записи, constraints и durable state | System of record |
| Redis | Ограниченный cache и dialogue memory | Производное/временное состояние, не бизнес-ledger |
| Celery workers | Асинхронные задачи, например document ingestion | Должны сохранять authorization и tenant metadata |
| Mortarium | Retrieval, synthesis и orchestration разрешённых tools | Только рекомендательная роль |
| External providers | LLM, embeddings, payment и regulatory integrations | Отдельные границы доверия и доступности |

## Инварианты request/data flow

1. Аутентифицируйте вызывающего до выполнения защищённых операций.
2. Определяйте pharmacy membership из server-side identity; tenant ID от клиента не доказывает наличие прав.
3. До работы с пациентом проверяйте его принадлежность авторизованной аптеке.
4. Применяйте tenant и patient filters внутри data access и retrieval, а не только в UI.
5. Детерминированно проверяйте business commands до записи в БД.
6. Сохраняйте транзакционные изменения и обязательные audit/outbox records атомарно.
7. Считайте retrieved documents, user messages, model output и MCP results недоверенными данными.
8. Не помещайте patient identifiers, prompts, completions и clinical content в telemetry.

## Central + Pharmacy Edge

Central + Edge — целевая архитектура, описанная в [ADR-0002](../adr/ADR-0002-offline-first-central-edge.ru.md), а не описание текущего deployment FastAPI Cloud.

Предполагаемая модель:

- Pharmacy Edge владеет локальными транзакциями, явно разрешёнными для offline execution.
- Central координирует identity, распространение policy/catalog, synchronization и сетевую отчётность.
- Synchronization использует at-least-once transport с идемпотентными бизнес-эффектами; глобальная exactly-once доставка не предполагается.
- Mortarium и доступность внешней LLM не должны быть prerequisites для локальных POS или inventory transactions.

См. [матрицу offline-возможностей](../devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) и [руководство Ansible rollout](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md).

## Текущая реализация и целевое состояние

- Текущий hosted application path публичной Demo: FastAPI Cloud; изолированные data/cache services provisioned отдельно.
- Production использует тот же технологический стек приложения, развёртываемый на аптечном сервере через Ansible; реальные host inventory, per-site secrets и approvals остаются под контролем оператора.
- Текущий backend: FastAPI modular monolith.
- Текущая AI orchestration: LangGraph Agent и LangGraph RAG, Agent Harness и MCP registry.
- Текущие WebSocket handlers: development scaffolds, не готовые для production.
- Central + Edge: поэтапная целевая архитектура; production readiness всего fleet не подтверждена.
- Версии Development Compose не обновляют production databases или caches.

## Политика изменений

Фиксируйте сквозные архитектурные решения в каталоге ADR. Обновляйте этот документ при существенном изменении системных границ, отношений доверия, владения данными или topology deployment. Диаграммы и текст должны отличать реализованное поведение от целевого дизайна.
