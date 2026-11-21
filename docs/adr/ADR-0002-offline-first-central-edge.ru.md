# ADR-0002: Offline-first архитектура Central + Pharmacy Edge

## Статус

Proposed — целевая архитектура одобрена для проектирования; реализация и production rollout не завершены.

## Контекст

Pharmaviyum рассчитан на аптечную сеть до 100 площадок. Аптека должна продолжать разрешённую локальную работу при недоступности WAN или центральной платформы. POS и inventory transactions не должны зависеть от Mortarium, cloud LLM или активного соединения с central control plane.

Текущий репозиторий содержит FastAPI modular monolith, PostgreSQL/pgvector, Valkey, код POS checkout/payment/FEFO и Ansible deployment scaffolding. Текущий production inventory Ansible описывает один узел `pharmacy-server-01`; текущий Compose stack — single-node deployment приложения/БД/cache. В репозитории уже есть foundation для durable Edge outbox dispatcher и Central inbox ingress, но полная operational synchronization и fleet deployment на 100 площадок ещё не прошли production validation. Стратегия поэтапная: сначала укрепить и проверить Ansible для 1–10 аптек, сохраняя совместимость site identity, inventory grouping и Central/Edge contracts с будущей сетью до 100 площадок.

## Решение

Принять топологию **Central + Pharmacy Edge**, первоначально сохранив архитектуру приложения как modular monolith.

### Ёмкость и границы rollout

- Архитектурная цель: до 100 независимо идентифицированных Pharmacy Edge sites.
- Начальный scope реализации и проверки Ansible: 1–10 аптек.
- Начальный Ansible rollout limit — мера безопасности, а не ограничение domain model или архитектуры.
- Не повышать активный rollout limit выше 10, пока не пройдены lab, pilot, backup/restore, offline behavior, sync compatibility, observability и staged-failure tests.
- Inventory на 100 площадок и staged rollout profile — будущая работа; текущие Ansible playbooks не доказывают production readiness для 100 площадок.

### 1. Pharmacy Edge — локальные операционные полномочия

Каждая аптека получает локально развёрнутый Pharmaviyum Edge, включающий:

- Pharmaviyum API и детерминированные business modules;
- локальную PostgreSQL database для операционных транзакций аптеки;
- durable synchronization outbox и inbox;
- локальный cache каталога, политик и других данных, явно разрешённых для offline use;
- локальный worker для synchronization и ограниченных background jobs;
- локальные audit records и health/backup agents.

POS checkout, локальные inventory movements, local audit и другие явно разрешённые процессы выполняются в локальной БД одной ACID transaction. Они должны оставаться доступными при сбое WAN или central services.

Один Edge host с UPS повышает устойчивость при отключении электричества и WAN, но остаётся single point of failure на уровне оборудования. Резервирование оборудования, recovery запасного узла, время работы UPS и требования к генератору определяются business RTO/RPO и оценкой рисков площадки; нельзя считать, что они уже реализованы.

### 2. Central Platform — координация сети и консолидированное представление

Центральная платформа предоставляет:

- registry аптек/sites и device identity;
- распространение пользователей, ролей и политик;
- распространение версионируемого каталога/reference data;
- central reporting и eventually consistent read models сети;
- synchronization ingestion, deduplication и monitoring;
- межаптечные процессы, требующие координации;
- Mortarium AI, RAG, analytics и model routing.

Central Platform не является синхронной зависимостью локального POS. Во время центрального outage Edge sites продолжают разрешённые локальные операции и сохраняют события для последующей доставки.

### 3. Контракт синхронизации

Реализуйте synchronization как application capability, а не как Ansible task или Redis-only queue.

- Сохраняйте business change и его outbox event в одной PostgreSQL transaction.
- Каждому событию назначайте глобально уникальный неизменяемый event ID, pharmacy/site ID, edge-node ID, aggregate type/ID, aggregate version, schema version и occurrence metadata.
- Доставляйте события как минимум один раз (at-least-once) через аутентифицированные TLS connections. Consumers должны быть идемпотентными.
- Сохраняйте обработанные event IDs в inbox с unique constraint, чтобы retries/replays не применяли один эффект дважды.
- Сохраняйте порядок внутри aggregate stream; не предполагайте глобальный порядок между аптеками.
- Повторяйте временно неуспешные операции с ограниченным exponential backoff и jitter; poison events сохраняйте для анализа и контролируемого replay.
- Надёжно сохраняйте acknowledgements и synchronization checkpoints.
- Версионируйте event contracts и поддерживайте окно совместимости для поэтапных Edge upgrades.
- Считайте центральное представление сети eventually consistent; показывайте время последней синхронизации и состояние устаревших данных.

Exactly-once network delivery не предполагается. Цель — at-least-once transport с effectively-once business effects благодаря durable idempotency.

### 4. Правила конфликтов и владения

Не используйте last-write-wins для stock, sales, payments, dispensing или audit events.

- Sale и stock decrement фиксируются локально одной transaction и имеют уникальный operation/idempotency key.
- Аптека владеет локальными продажами и локальным stock ledger.
- Межаптечные перемещения товара используют явный transfer workflow с reservation/dispatch источника и receipt получателя. Значение центральной панели не даёт права продавать остаток другой площадки.
- Central catalog/policy changes версионируются и распространяются в Edge. Каждый Edge сообщает применённую версию.
- Конфликты разрешаются domain-specific commands, validation и при необходимости human review; финансовая и складская история никогда не перезаписывается незаметно.
- Patient и prescription data синхронизируются только при явной авторизации, соблюдении data minimization и retention rules.

### 5. Offline capability и внешние зависимости

Поддерживайте явную capability matrix как минимум со статусами: supported offline, supported with restrictions, online-only и blocked pending legal/integration validation.

Внешняя фискализация, проверка электронных рецептов, авторизация платёжного провайдера, реестры контролируемых препаратов и другие государственные/provider services не должны имитироваться как доступные при отсутствии соединения. Возможность законно завершить транзакцию offline зависит от юрисдикции и compliance review. Приложение должно явно показывать pending, rejected и unavailable внешние операции.

Mortarium не является критической зависимостью POS. При недоступности central AI или LLM provider локальные аптечные транзакции продолжаются. Любая необязательная локальная AI capability изолирована, ограничена по ресурсам и не может разрешать dispensing, payment или stock mutation.

### 6. Ansible и fleet operations

Ansible — control plane конфигурации и жизненного цикла Central/Edge infrastructure. Он не реализует аптечную бизнес-логику и не синхронизирует транзакционные данные.

Целевые inventory groups:

- `central` — central API/control plane, sync ingress, observability и AI services;
- `pharmacy_edges` — Edge nodes аптек;
- `pharmacy_edges_canary` — явно выбранные pilot/canary sites;
- дополнительные site subgroups и host variables для network, UPS, storage и hardware capabilities.

Целевые playbooks следует разделять по lifecycle: bootstrap, configure, deploy, update, backup, restore, healthcheck и disaster recovery. Используйте immutable image digests, Ansible Vault или внешний secret manager, least-privilege service accounts, idempotent roles, preflight checks, post-deploy health checks и явные rollback gates.

Обновления fleet выполняйте поэтапно (lab -> pilot -> small canary -> controlled waves), проверяя health и synchronization перед продолжением. Ошибка площадки или batch должна останавливать дальнейший rollout. Размеры batch — параметры конфигурации и release policy, а не жёсткие предположения.

Ansible должен настраивать VPN/TLS identity, firewall policy, storage, Docker/Compose, PostgreSQL, Edge services, UPS monitoring (например, NUT), backup agents и observability. Он не должен копировать live database files между площадками или запускать ad-hoc SQL для согласования бизнес-событий.

### 7. Защита данных и восстановление

- Шифруйте transport site-to-central и защищайте локальные диски/backups в соответствии с threat model.
- Храните локальные database backups и зашифрованные off-site копии; определите WAL/PITR strategy, если её поддерживает выбранная инфраструктура.
- Резервируйте configuration и secrets через утверждённые secret-management procedures, никогда не храните их открытым текстом в Git.
- Отдельно определяйте RPO/RTO для локальной работы аптеки, central reporting и AI services совместно с бизнесом.
- Проверяйте restore в изолированной инфраструктуре и валидируйте database consistency и application-level invariants.
- Мониторьте UPS, disk capacity, database health, outbox backlog, last successful sync, failed events и backup age.
- Успешный backup job не доказывает recoverability; необходим restore test.

## Последствия

### Преимущества

- WAN или central outage автоматически не останавливают разрешённые локальные аптечные процессы.
- Локальная транзакционная надёжность отделена от сетевой доставки.
- Central reporting и AI можно масштабировать независимо от POS traffic.
- Одна кодовая база может развёртываться в ролях Central и Edge без преждевременного разделения modular monolith на microservices.
- Ansible обеспечивает повторяемую и аудируемую конфигурацию растущего fleet.

### Издержки и риски

- Edge добавляет distributed-systems проблемы: duplicate delivery, ordering, schema compatibility, conflicts, clock skew, partial outages и эксплуатацию каждой площадки.
- Каждой площадке нужны управление жизненным циклом БД, monitoring, backups, restore tests и secure device identity.
- Данные сети согласуются eventual consistency, а не мгновенно.
- Offline operation ограничивается законодательством и требованиями внешних сервисов.
- Один Edge server остаётся аппаратной точкой отказа площадки, пока резервная локальная topology не спроектирована и не проверена.

## Последовательность реализации

1. Провести аудит domain models, tenant/site identity, POS transactions, audit trail и migration strategy.
2. Определить offline capability matrix и event contracts до разработки synchronization.
3. Реализовать transactional outbox/inbox, event versioning, idempotent ingestion и sync observability.
4. Добавить Edge deployment configuration и изолированные integration/failure tests.
5. Подготовить Ansible Central/Edge inventories, roles, staged rollout, backup и restore verification.
6. Проверить в lab pharmacy, затем на небольшом pilot, затем в контролируемых fleet waves.
7. Определить production RPO/RTO и SLO по измеренным бизнес-требованиям и результатам restore/failure exercises.

## Не входит в цели

- Немедленное внедрение Kubernetes.
- Немедленное разделение на microservices.
- Синхронная cloud dependency для локального POS.
- Last-write-wins reconciliation складских остатков.
- Заявление о поддержке offline fiscalization, e-prescription или иных внешних юридических процессов до проверки.
- Production rollout или изменение live infrastructure в рамках этого ADR.

## Ссылки

- [Архитектурное видение Pharmaviyum](../architecture/pharmaviyum-architecture.ru.md)
- [Аудит POS и каталога](../architecture/PHARMACY_POS_CATALOG_AUDIT.md)
- [Индекс DevOps](../devops/README.md)
- `ansible/inventory/production/hosts.yml`
- `ansible/playbooks/deploy.yml`
- `ansible/roles/app-backend/files/docker-compose-backend.yml`
- [Стратегии выполнения Ansible](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html)
