## Граница инфраструктуры Production и Demo

Это каноническая политика развёртывания Pharmaviyum. Она разделяет публичную демонстрационную среду и Production-развёртывание на аптечном сервере. Описанная целевая конфигурация не является доказательством завершённого deployment.

| Область | Публичная Demo | Production |
|---|---|---|
| Размещение приложения | FastAPI Cloud | Аптечный сервер / Pharmacy Edge; конфигурация и развёртывание через Ansible |
| Выпуск приложения | Вручную одобряемый GitHub Actions Demo workflow из `main` | Проверенный immutable image/release, развёртываемый утверждённой процедурой Ansible |
| Runtime приложения | FastAPI API и React frontend | Тот же технологический стек приложения, упакованный для runtime аптечного сервера |
| Сервисы данных | Отдельная изолированная Demo PostgreSQL и необходимые Demo cache/worker services | Локальные PostgreSQL и cache/worker services на аптечном сервере согласно утверждённому Compose/Ansible profile |
| Секреты | Только Demo-переменные FastAPI Cloud и secrets защищённого GitHub Environment | Per-site credentials из Ansible Vault или утверждённого secret manager; никогда не хранить в Git |
| Данные | Только синтетические демонстрационные данные | Операционные данные аптеки под соответствующими мерами безопасности, приватности, резервирования и хранения |
| AI profile | Demo-профиль QwenCloud, если настроен | Локальный Ollama — документированная цель; требуются проверка оборудования и приёмка модели |

## Правила deployment и изоляции

- FastAPI Cloud используется исключительно для публичной Demo. Ни одно Production-приложение, БД, миграция или release workflow не должны быть направлены на FastAPI Cloud.
- Production-приложение развёртывается на аптечном сервере через Ansible. GitHub Actions может проверять код, собирать и публиковать immutable artifacts и тестировать Ansible, но не должен незаметно подключаться по SSH к действующему аптечному серверу или развёртывать там релиз.
- Demo и Production обязаны иметь отдельные экземпляры БД, credentials, cache endpoints/namespaces, signing keys, API credentials и runtime-конфигурацию. Demo никогда не подключается к Production аптечному серверу или Production data store.
- В Demo допускаются только синтетические данные. Запрещено помещать туда реальные сведения о пациентах, рецептах, клиентах, аптечных транзакциях или конфиденциальную бизнес-информацию.
- Аптечный сервер является локальной операционной границей своей аптеки. POS, inventory и другие разрешённые детерминированные процессы не должны зависеть от FastAPI Cloud или WAN для завершения локальных транзакций.
- Ansible отвечает за конфигурацию инфраструктуры и оркестрацию релизов; он не реализует аптечную бизнес-логику и не синхронизирует бизнес-транзакции.
- Production secrets и реальные inventory/host details должны оставаться в защищённых operator-controlled inventory и secret-management системах. Публичные примеры должны содержать placeholders.
- Нельзя объявлять Production rollout завершённым только потому, что существуют playbooks, inventories или CI checks. Отдельно фиксируются результаты lab/pilot, readiness, backup/restore, rollback и приёмки площадки.
- Не используйте выведенную из эксплуатации инфраструктуру Render как действующую зависимость.

## Политика версий и проверки

Версии приложения и сервисов должны быть зафиксированы в dependency lockfiles, container definitions и Ansible variables соответствующего deployment profile. Версии PostgreSQL, pgvector, Redis/Valkey, Python, Docker Engine и Compose необходимо сверять с фактическим runtime, прежде чем указывать их как развёрнутые. Целевая совместимость не равна наблюдаемой версии сервера.

Смена major-версии PostgreSQL требует утверждённого плана backup, проверки совместимости, миграции, тестового восстановления, maintenance window и rollback. Нельзя подключать существующий data volume к другой major-версии PostgreSQL.

См. [руководство Demo FastAPI Cloud](FASTAPI_CLOUD.ru.md), [план Ansible rollout Pharmacy Edge](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md), [руководство Ansible](../devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md) и [Production operations runbook](../operations/PRODUCTION_OPERATIONS_RUNBOOK.ru.md).