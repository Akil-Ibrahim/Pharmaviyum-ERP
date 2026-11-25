# Инженерная документация Pharmaviyum

[English](README.md) · **Русский**

Этот каталог — центральный индекс инженерной документации Pharmaviyum ERP/CRM. Здесь собраны архитектура, AI/RAG, разработка, эксплуатация, развёртывание и Pharmacy Edge. Общие правила единой правды, доказательности, границ Demo/Production и синхронизации переводов описаны в [Политике документации](./DOCUMENTATION_GOVERNANCE.md).

## С чего начать

| Раздел | Русская версия | Английский оригинал | Содержание |
|---|---|---|---|
| Технологии | [Стек и глоссарий](./technology-stack.ru.md) | [Technology Stack & Glossary](./technology-stack.md) | Определения технологий, роли в архитектуре, версии и управление зависимостями |
| Архитектура инфраструктуры | [Production и Demo](./deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.ru.md) | [Production and Demo Infrastructure Baseline](./deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md) | Границы хостинга, версии сервисов данных, изоляция окружений и правила проверки |
| Структура репозитория | [Руководство](./architecture/repository-structure.ru.md) | [Repository Structure Guide](./architecture/repository-structure.md) | Назначение каталогов, правила размещения файлов и безопасные перемещения |
| Офлайн-операции | [Матрица возможностей](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.ru.md) | [Pharmacy Offline Capability Matrix](./devops/PHARMACY_OFFLINE_CAPABILITY_MATRIX.md) | Поддерживаемые, ограниченные, online-only и заблокированные сценарии |
| Оценка RAG | [Фармацевтическая оценка Ragas](./ai/ragas-pharmaceutical-evaluation.ru.md) | [Ragas evaluation](./ai/ragas-pharmaceutical-evaluation.md) | Offline-метрики RAG и специализированные фармацевтические проверки |
| Безопасность AI | [Выявление галлюцинаций и red-team](./ai/hallucination-detection-and-red-team.ru.md) | [Hallucination detection and red-team](./ai/hallucination-detection-and-red-team.md) | Оценка groundedness, adversarial-тестирование и правила безопасного отказа |
| Аптечные процессы | [Спецификация аптечного процесса](./workflows/pharmacy-workflow.ru.md) | [Pharmacy workflow specification](./workflows/pharmacy-workflow.en.md) | POS, отпуск, склад, закупки, аудит и offline-границы |
| Бизнес-ценность и KPI | [Спецификация бизнес-ценности и KPI](./workflows/PHARMACY_BUSINESS_VALUE_AND_KPIS.ru.md) | [Business value and KPI specification](./workflows/PHARMACY_BUSINESS_VALUE_AND_KPIS.md) | Бизнес-результаты, определения и методика KPI, NDA и доказательность утверждений в CV |
| Трассировка аптечных процессов | [Матрица реализации](./workflows/PHARMACY_WORKFLOW_TRACEABILITY.ru.md) | [Implementation traceability](./workflows/PHARMACY_WORKFLOW_TRACEABILITY.md) | Сопоставление процессов с моделями, API, UI, тестами и подтверждённым статусом реализации |
| P0.2: рецепт и отпуск | [Доменный контракт](./architecture/P0_2_PRESCRIPTION_DISPENSING_DOMAIN_CONTRACT.ru.md) | [Domain contract](./architecture/P0_2_PRESCRIPTION_DISPENSING_DOMAIN_CONTRACT.md) | Предлагаемая связь пациента, рецепта и продажи, dispense ledger, транзакционные правила и критерии приёмки |
| Архитектура системы | [Архитектурное видение](./architecture/pharmaviyum-architecture.ru.md) · [Системный контекст](./architecture/system-context.ru.md) · [Контракт событий синхронизации](./architecture/PHARMACY_SYNC_EVENT_CONTRACT_V1.ru.md) · [Аудит POS и каталога](./architecture/PHARMACY_POS_CATALOG_AUDIT.ru.md) | [Architecture vision](./architecture/pharmaviyum-architecture.en.md) · [Sync event contract](./architecture/PHARMACY_SYNC_EVENT_CONTRACT_V1.md) · [POS catalog audit](./architecture/PHARMACY_POS_CATALOG_AUDIT.md) | Компоненты, Central/Edge, синхронизация, POS и лекарственный каталог |
| Chunking | [Pipeline чанкинга](./ai/chunking-pipeline.ru.md) | [Chunking pipeline](./ai/chunking-pipeline.md) | Текущая реализация разбиения документов и целевая архитектура |

## Остальные разделы документации

| Раздел | Русская версия | Английский оригинал | Содержание |
|---|---|---|---|
| Системный контекст | [Системный контекст](./architecture/system-context.ru.md) | [System context](./architecture/system-context.md) | Границы компонентов, владение данными и Central/Edge |
| ADR | [Индекс архитектурных решений](./adr/README.ru.md) · [ADR-0001](./adr/ADR-0001-websocket-gateway.ru.md) · [ADR-0002](./adr/ADR-0002-offline-first-central-edge.ru.md) · [ADR-0003](./adr/ADR-0003-patient-scoped-ai-state.ru.md) · [ADR-0005: цены и роли аптек](./adr/ADR-0005-tenant-scoped-pricing-and-pharmacy-rbac.ru.md) | [ADR index](./adr/README.md) | Архитектурные решения, история, статусы и жизненный цикл |
| Руководство для AI coding agents | [Внутренние инженерные рекомендации AI](./internal/PHARMAVIYUM_AI_GUIDELINES.md) | [English original](./internal/PHARMAVIYUM_AI_GUIDELINES.md) | Правила работы coding agents, инварианты безопасности, границы RAG и управление изменениями |
| AI / LLM | [Демо QwenCloud](./ai/QWENCLOUD_DEMO.ru.md) · [Архитектура Mortarium и глоссарий](./ai/MORTARIUM_AI_ARCHITECTURE.ru.md) · [Проектирование AI-системы](./ai/AI_LLM_SYSTEM_DESIGN.ru.md) · [Архитектура AI](./ai_architecture.ru.md) · [Аудит архитектуры RAG](./rag_architecture_audit.ru.md) · [Стандарт инженерии LLM](./llm_engineering_standards.ru.md) · [Архитектура LangGraph RAG](./ai/langgraph-rag-architecture.ru.md) · [Операционная работа Mortarium](./ai/mortarium-pharmacy-operations.ru.md) · [Изоляция состояния пациента](./ai/patient-session-isolation.ru.md) | [English originals](./README.md) | Mortarium, Agent Harness, LangGraph, RAG, MCP, безопасность и наблюдаемость |
| Разработка | [Руководство по разработке и тестированию](./guides/DEVELOPMENT_AND_TESTING.ru.md) · [Настройка окружения](./guides/ENVIRONMENT_SETUP.ru.md) · [GitHub Codespaces](./guides/CODESPACES_GUIDE.ru.md) · [Library Skills и инструменты FastAPI для ИИ-агентов](./development/library-skills.ru.md) | [Development and testing handbook](./guides/DEVELOPMENT_AND_TESTING.md) · [Library Skills and FastAPI agent tooling](./development/library-skills.md) · [Frontend Agent Skills](./development/FRONTEND_AGENT_SKILLS.md) · [Frontend Engineering Standards](./development/FRONTEND_ENGINEERING_STANDARDS.md) | Разработка frontend-агентов, архитектурное управление, доступность, производительность, наблюдаемость, тестирование и локализация (новый стандарт пока доступен на английском) |
| Тестирование | [Руководство по тестированию](./guides/TESTING.ru.md) | [Testing guide](./guides/TESTING.md) | Структура тестов, маркеры pytest, CI и критерии качества |
| Эксплуатация | [Production operations](./operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md) · [Production Engineering](./operations/PRODUCTION_ENGINEERING.ru.md) · [Реагирование на инциденты](./operations/INCIDENT_RUNBOOK.ru.md) · [Релиз](./operations/RELEASE_RUNBOOK.ru.md) | [English originals](./README.md) | Health checks, SLO, инциденты, backup/restore и rollback |
| Хостинг Demo | [FastAPI Cloud](./deployment/FASTAPI_CLOUD.ru.md) · [Настройка окружения](./guides/ENVIRONMENT_SETUP.ru.md) | [FastAPI Cloud Demo deployment](./deployment/FASTAPI_CLOUD.md) · [Environment setup](./guides/ENVIRONMENT_SETUP.md) | Размещение Demo, runtime и контролируемое развёртывание |
| Production deployment | [План Ansible rollout Pharmacy Edge](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md) · [Руководство Ansible](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) · [Lab Pharmacy Server](./deployment/LAB_PHARMACY_SERVER.md) (англ.) | [Pharmacy Edge Ansible rollout](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) · [Ansible guide](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) | Подготовка аптечного сервера, лабораторная проверка, immutable releases, health checks, backup и rollback |
| Трассировка инженерных требований | [Матрица трассировки](./devops/ENGINEERING_REQUIREMENTS_TRACEABILITY.ru.md) | [Engineering requirements traceability](./devops/ENGINEERING_REQUIREMENTS_TRACEABILITY.md) | Связь требований с ADR, реализацией, тестами, CI/runtime evidence и release blockers |
| DevOps и Pharmacy Edge | [Инженерные benchmarks](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.ru.md) · [Контракт benchmarks](./devops/ENGINEERING_BENCHMARK_REQUIREMENTS.md) · [Индекс DevOps](./devops/README.ru.md) · [Roadmap](./devops/ENGINEERING_ROADMAP.ru.md) · [Dispatcher Outbox](./devops/PHARMACY_EDGE_OUTBOX_DISPATCHER.ru.md) · [Руководство Ansible](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) · [План внедрения](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md) | [Outbox dispatcher](./devops/PHARMACY_EDGE_OUTBOX_DISPATCHER.md) · [Ansible guide](./devops/ANSIBLE_PHARMACY_EDGE_GUIDE.md) · [Fleet rollout plan](./devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.md) | Benchmarks, доставка событий, rollout, Ansible, нагрузочные испытания, backup и recovery |
| Наблюдаемость | [OpenTelemetry](./observability/opentelemetry.ru.md) | [English original](./observability/opentelemetry.md) | Tracing, защита данных и критерии приёмки telemetry |
| WebSocket | [Протокол WebSocket](./websocket-protocol.ru.md) | [WebSocket protocol](./websocket-protocol.md) | Контракт и ограничения текущей реализации |
| Материалы для интервью | [Программа Senior Python/AI](./interview/SENIOR_PYTHON_AI_CURRICULUM.ru.md) | [Senior Python/AI curriculum](./interview/SENIOR_PYTHON_AI_CURRICULUM.md) · [Interview guide](./interview/README.md) | 260 основных вопросов, около 700 уточняющих вопросов с ответами, двуязычные эталонные ответы и оценка уровня Senior |

## Карта каталогов

- `workflows/` — аптечные бизнес-процессы и операционная модель.
- `architecture/` — системный контекст, границы компонентов и структура репозитория.
- `adr/` — долгосрочные архитектурные решения.
- `ai/` — Mortarium, LangGraph RAG, оценка и AI system design.
- `guides/` — настройка разработки и тестирование.
- `operations/` — инциденты, production operations и release.
- `devops/` — roadmap, benchmarks, load tests, observability и Pharmacy Edge.
- `deployment/` — инструкции по платформам размещения.
- `observability/` — telemetry и контроль конфиденциальности.
- `interview/` — учебные материалы и подготовка к интервью.

## Правила ведения документации

- Документируйте фактическое состояние репозитория, а не историческую или предполагаемую инфраструктуру.
- Для каждого процесса поддерживайте один канонический документ; в других местах размещайте ссылки на него.
- Архитектурные решения храните в `adr/`, эксплуатационные процедуры — в `operations/`, инструкции разработчика — в `guides/`, планы и benchmarks — в `devops/`.
- Помечайте возможности как реализованные, предлагаемые, запланированные или не прошедшие проверку. Статус Accepted у ADR не доказывает готовность реализации или Production.
- При изменении команд, сервисов, путей, API-контрактов или архитектурных инвариантов обновляйте соответствующую документацию в том же изменении.
- Не размещайте credentials, реальные данные клиентов/пациентов, секреты провайдеров или неотредактированные логи.
- Используйте синтетические примеры. Клинические пороги оценки требуют проверки квалифицированными специалистами.
- В каждом production runbook указывайте окружение, предусловия, ответственного, способ проверки и границы rollback/recovery.

## Языковая навигация

Английские документы остаются каноническими для инженерной и эксплуатационной терминологии. Русские версии должны сохранять структуру, смысл, команды, кодовые примеры, таблицы и внутренние ссылки оригинала. Если перевод ещё не опубликован, это явно отмечается в индексе — ссылка на несуществующий файл не создаётся.

## Международный справочник лекарств и медицинских изделий

- [Источники и покрытие международного каталога](./catalog/INTERNATIONAL_CATALOG_SOURCES.ru.md)
- [ADR-0008: Международный справочник лекарств и медицинских изделий](./adr/ADR-0008-international-medicine-and-device-reference-catalog.ru.md)
