# Runbook эксплуатации Production

<text>**Статус:** эксплуатационная базовая процедура для Production на аптечном сервере под управлением Ansible. Перед действиями проверьте host, inventory, источник secrets и владельцев сервисов.</text>

## Принципы эксплуатации

- Production отделён от локального Compose, CI и тестовых сервисов.
- Зелёный CI не означает deployment; отправленный deployment не означает успешный deployment.
- Не запускайте миграции схемы, очистку данных, flush cache или удаление checkpoints как универсальный способ диагностики.
- Сохраняйте deployment ID, commit SHA, временные отметки, результаты health checks и очищенные от секретов логи.
- Не помещайте credentials, patient identifiers, prompts или клинические payloads в incident records.

## Карта сервисов и ответственности

| Компонент | Ответственность | Проверка |
|---|---|---|
| Стек приложения на аптечном сервере (Ansible-managed) | API и frontend локальной аптеки | Результат Ansible rollout, immutable image digest, состояние контейнеров, logs, /health, /ready и безопасные аптечные smoke tests |
| PostgreSQL | Транзакционные данные и checkpoints | Локальный Compose-managed container `db` на аптечном сервере: состояние контейнера/readiness, connections, latency, возраст backup и доказательства restore. Ansible role `postgresql` не является полноценной ролью lifecycle/HA базы данных |
| Redis-compatible service | Cache и dialogue memory | Compose service `redis` (по умолчанию образ Valkey 8): доступность, memory/connection limits, evictions и latency |
| Celery worker | Асинхронные задачи, например ingestion | Compose service `celery-worker`: состояние контейнера/process, queue depth, возраст задач, retries и failed tasks; проверяйте отдельно от API readiness |
| LLM / embedding provider | Необязательные AI inference и embeddings | Статус провайдера, timeout/error rate, quota и latency |
| Telemetry backend | Traces, metrics и logs | Доставка collector, dashboards и alerts |

Текущая Ansible role `app-backend` запускает `db`, `redis`, `backend`, `celery-worker` и `celery-beat` из Compose definition аптечного сервера. Проверяйте каждый service отдельно: `/ready` подтверждает зависимости API, но не здоровье Celery worker.

## Последовательность health checks

1. Проверьте deployment state и определите deployed commit.
2. Запросите `/health`. Это liveness signal, а не доказательство доступности зависимостей.
3. Запросите `/ready` и исследуйте каждый компонент, который не готов.
4. Проверьте PostgreSQL и Redis через поддерживаемые readiness checks.
5. Проверьте authentication и tenant-scoped read-only API с synthetic или утверждённой тестовой учётной записью.
6. Проверьте безопасный аптечный workflow в утверждённой smoke-test среде.
7. Отдельно проверьте Mortarium. Сбой AI provider не равен недоступности core ERP.

Фиксируйте время, deployed SHA и очищенный от чувствительных данных ответ. Не публикуйте tokens и полные connection strings.

## Диагностика инцидентов

### API недоступен

Проверьте результат Ansible rollout, целевой host, состояние контейнеров, startup logs и последние изменения. Отличайте сбой процесса от недоступности зависимостей. Если новая revision нездорова, остановите rollout. Используйте утверждённую Ansible rollback procedure и предыдущий проверенный immutable image digest. Не начинайте с downgrade БД или разрушительной очистки.

### PostgreSQL недоступен

Проверьте локальный PostgreSQL container `db` на аптечном сервере через Docker Compose, его readiness, connection limits и ошибки приложения. Избегайте циклов перезапуска и неограниченных retries. Не сбрасывайте, не пересоздавайте и не восстанавливайте БД без утверждённого incident owner и проверенной точки восстановления. При сомнениях в совместимости схемы остановите promotion.

### Redis недоступен

Определите, затронуты ли cache, dialogue memory, queues или несколько функций. Сохраняйте persistent business records: Redis не является ledger продаж или остатков. Не выполняйте глобальный flush Redis как первую меру. До точечного удаления выясните владельца ключей и сроки хранения.

### Очередь Celery растёт или ingestion не работает

Проверьте worker health, queue depth, возраст старейшей задачи, retries и классы ошибок. До повторного запуска проверьте доступность broker/backend и идемпотентность задач. Не воспроизводите массово задачи, пока не понятны риски дублирующей записи и tenant metadata.

### Mortarium / LLM деградирует

Проверьте доступность provider, rate limits, latency, timeouts и зависимости RAG. Сохраняйте основные детерминированные аптечные процессы. При необходимости отключайте optional AI только через утверждённое изменение конфигурации/release. Во время деградации не представляйте вывод модели как проверенную клиническую рекомендацию.

## Release и rollback

Production application releases направляются на аптечный сервер и оркестрируются Ansible playbooks из этого репозитория. Production inventory, per-site credentials, реальные host details и approvals остаются под контролем оператора и не должны попадать в Git. Используйте [план Ansible rollout Pharmacy Edge](../devops/PHARMACY_EDGE_ANSIBLE_ROLLOUT.ru.md) и [руководство Ansible](../devops/ANSIBLE_PHARMACY_EDGE_GUIDE.ru.md). Публичный [runbook FastAPI Cloud Demo](../deployment/FASTAPI_CLOUD.ru.md) относится только к Demo и не должен использоваться для Production.

До релиза проверьте CI и approval для точного утверждённого Production source commit и immutable image digest в контролируемом Production release pipeline. Public Demo CI не доказывает, что Production artifact был собран или проверен. Дополнительно проверьте backup/restore evidence, migration plan, environment variables, smoke tests и rollback target.

Откатывайте revision приложения только если предыдущая revision совместима с текущей схемой. Откат БД — отдельная операция высокого риска. Предпочитайте backward-compatible expand/contract migrations. Восстановление из backup выполняйте только по утверждённому recovery plan.

## Backup и restore

- `ansible/playbooks/backup.yml` создаёт и проверяет локальный PostgreSQL dump при запуске, но не устанавливает и не планирует собственный запуск. Убедитесь, что утверждённый защищённый automation controller или scheduler действительно запускает playbook и безопасно передаёт secrets. Значение `backup_enabled: true` не доказывает наличие расписания.
- Проверьте local retention и документированный изолированный restore drill. Off-site upload — отдельный запуск с явным approval в заранее provisioned site-scoped Restic repository; он не создаёт repository/ACL и не доказывает возможность restore из удалённой копии. См. Off-site Backup Architecture; не предполагайте наличие cloud-provider PITR service.
- Определите retention Redis и checkpoints отдельно.
- Локальный артефакт `backup.yml` — gzip-сжатый SQL, этот playbook не шифрует его. Права `0700`/`0600` ограничивают доступ, но не являются шифрованием; отдельно подтвердите утверждённое шифрование диска/storage на аптечном сервере и порядок восстановления ключей для локальных backup.
- Храните ключи шифрования Restic/repository вне Git. Шифрование Restic защищает remote repository, но не исходный plaintext dump, который остаётся на аптечном сервере.
- Фиксируйте возраст backup и срок хранения.
- Проводите restore drills в изолированной инфраструктуре и проверяйте инварианты приложения.
- Успешное выполнение backup job не доказывает возможность восстановления.

См. [Архитектуру offsite backup](../devops/OFFSITE_BACKUP_ARCHITECTURE.md) и [Production Engineering](./PRODUCTION_ENGINEERING.md).

## Запись об инциденте/изменении

Указывайте incident/change ID, ответственного, затронутый сервис/окружение, временные отметки, влияние, deployed SHA, очищенные доказательства, меры устранения, проверку целостности данных и ответственных за follow-up.

## Что этот runbook не разрешает

Этот документ не разрешает production migrations, удаление patient data, очистку Redis/checkpoints, смену секретов, upgrades PostgreSQL/Redis/Valkey/Python, включение непроверенных WebSockets или rollout Edge fleet.
