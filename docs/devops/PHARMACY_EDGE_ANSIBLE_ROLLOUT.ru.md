# Pharmacy Edge Fleet — план развёртывания и эксплуатации Ansible

**Статус:** целевая операционная модель; ещё не развёрнута как production fleet.  
**Область:** начальная проверка Ansible для 1–10 аптечных Edge-площадок; архитектурная цель — до 100 площадок.  
**Принцип:** Ansible управляет инфраструктурой и выпусками приложения. Бизнес-транзакции и синхронизация принадлежат сервисам приложения Pharmaviyum.

## 1. Проверенная базовая конфигурация репозитория

В текущей ветке `main` находятся следующие ресурсы:
- `ansible/inventory/production/hosts.yml` содержит один хост `pharmacy-server-01`.
- `ansible/playbooks/deploy.yml` работает с группой `pharmacy_servers`, проверяет параметры release и Edge sync, проверяет Docker/Compose, развёртывает роли контролируемыми волнами и проверяет `/ready`.
- `ansible/roles/app-backend/` формирует environment file, копирует Compose definition, загружает backend image, запускает PostgreSQL и Valkey, затем backend. Миграции БД выполняются отдельно и требуют явного approval.
- `ansible/roles/postgresql/` сейчас подготавливает каталог и сообщает состояние контейнера; сам PostgreSQL создаётся через Compose.
- `ansible/playbooks/backup.yml` создаёт локальный сжатый PostgreSQL dump, проверяет gzip integrity и SHA-256, записывает manifest и удаляет просроченные локальные артефакты только после проверки новой резервной копии. `ansible/playbooks/restore.yml` выполняет неразрушающий restore drill в отдельно названную БД ровно на одном явно подтверждённом Edge-хосте. Планирование запуска делегировано защищённому automation controller.
- `ansible/playbooks/rollback.yml` возвращает предыдущий backend image и проверяет `/health`; он не восстанавливает backup базы данных.
- Compose definition содержит `db`, `redis` (образ Valkey) и `backend`. Сервиса Nginx в нём нет.
- Роль Nginx существует, но не подключена к текущему deployment playbook.

Это факты о содержимом репозитория, а не утверждение, что playbooks успешно выполнялись на реальном аптечном сервере.

## 0.1 Начальный rollout: 1–10 аптек

Первая инженерная цель — сделать развёртывание одной Pharmacy Edge площадки безопасным и повторяемым, затем проверить 2–3 и в итоге 4–10 площадок. Активный лимит Ansible rollout намеренно равен 10; развёртывание выполняется последовательно (`serial: 1`) с fail-fast поведением. Это операционный лимит, а не архитектурный потолок.

Для каждой площадки используйте собственные неизменяемые `pharmacy_id`, `site_code`, Edge node ID, Edge token, SSH identity и PostgreSQL credential. Секреты площадки должны поступать из encrypted host variables или одобренного secret manager. Глобальные defaults для PostgreSQL password и Edge token намеренно пусты, чтобы предотвратить повторное использование credentials. Lab inventory читает только собственный тестовый пароль из `PHARMAVIYUM_LAB_POSTGRES_PASSWORD`. Production inventory не имеет fallback на localhost.

Docker role поддерживает только Debian/Ubuntu, требует явной фиксации версий пакетов Docker Engine и plugins для площадки или ОС и сверяет установленные версии с этими pins. Перед подготовкой нового хоста задайте `docker_package_versions` в одобренных host/group variables. Deployment user не добавляется в группу `docker`, поскольку доступ к Docker socket фактически эквивалентен root.

Одна аптека может работать как изолированный Edge. Central sync включается только тогда, когда node ID, token и HTTPS Central URL этой площадки заданы все вместе и проходят валидацию. POS и локальные транзакционные процессы не должны ждать Central API.

## 2. Целевая inventory-модель

Используйте отдельные явные inventories для development, lab, staging и production. Не храните секреты в inventory-файлах.

Рекомендуемая структура production inventory:

```text
ansible/
  inventories/
    development/hosts.yml
    lab/hosts.yml
    staging/hosts.yml
    production/
      hosts.yml
      group_vars/
      host_vars/
```

Рекомендуемые логические группы:

```yaml
all:
  children:
    central:
      hosts:
        central-control-01:
    pharmacy_edges:
      children:
        pharmacy_edges_canary:
          hosts: {}
        pharmacy_edges_wave_01:
          hosts: {}
        pharmacy_edges_wave_02:
          hosts: {}
    monitoring:
      hosts:
        observability-01:
```

Это только схема структуры. Реальные hostnames, адреса, site IDs, SSH identities и secrets должны поступать из одобренного оператором inventory source. Не используйте `127.0.0.1` как production default.

Каждый Edge host должен иметь явные несекретные metadata: неизменяемые `pharmacy_id`, `site_code`, `edge_node_id`, environment, hardware profile, storage paths, network/VPN profile и backup destination. До deployment проверяйте уникальность site и node identities.

## 3. Границы Ansible roles

### Общая базовая конфигурация хоста
- `common`: поддерживаемые OS packages, синхронизация времени, пользователи и базовые каталоги.
- `security`: SSH hardening, firewall policy, политика unattended security updates, prerequisites шифрования диска и audit settings.
- `networking` / `vpn`: исходящее аутентифицированное соединение с Central, установка TLS material и сетевая политика площадки.
- `docker`: зафиксированные версии Docker Engine и Compose plugin, конфигурация daemon и ротация логов.
- `ups_monitoring`: настройка NUT client/server там, где поддерживается, UPS telemetry и политика выключения при низком заряде.
- `node_exporter` / `otel_collector`: telemetry хоста и сервисов.

### Роли Central
- `central_api`: развёртывание центрального приложения.
- `sync_ingress`: аутентифицированный приём Edge events и операционная видимость синхронизации.
- `central_data`: Central PostgreSQL и backup policy, только если БД управляется самостоятельно.
- `mortarium_ai`: изолированный AI runtime/gateway, конфигурация модели и ограничение ресурсов.
- `observability`: метрики, traces, logs и alerting.

### Роли Edge
- `pharmacy_edge`: развёртывание локального API и worker.
- `edge_postgresql`: локальная транзакционная БД, storage layout, health checks и backup configuration.
- `edge_cache`: cache/queue только для явно неавторитетного или восстанавливаемого состояния.
- `edge_sync`: развёртывание/настройка прикладного Sync Engine; Ansible сам не транспортирует бизнес-события.
- `edge_backup`: локальное шифрованное резервное копирование и агент передачи off-site.
- `edge_health`: readiness, disk, DB, возраст backup, outbox backlog и время последней успешной синхронизации.

Используйте общую role с явным `deployment_role: central|edge` только тогда, когда задачи и границы безопасности действительно общие. Не размещайте Central-only сервисы на каждой аптечной площадке.

## Production-профиль Mortarium AI (Ansible / on-premises)

Production-профиль Ansible/on-premises намеренно отделён от demo-профиля FastAPI Cloud.

| Параметр | Demo: FastAPI Cloud | Целевой production: Ansible / on-premises |
|---|---|---|
| LLM provider | QwenCloud API | Локальный Ollama runtime |
| Профиль модели | `qwen3.8-flash` | `Qwen3.5 9B Q4_K_M` (целевой default; требуется проверка оборудования) |
| Сетевая зависимость inference | Подключение к внешнему provider | Локальный inference после установки runtime и модели |
| Credentials | QwenCloud API key в FastAPI Cloud secrets | Для локального inference не нужен внешний LLM API key; отдельно защищайте credentials registry/download |
| Квоты и стоимость | Free quota провайдера и application guard | CPU/GPU/RAM/disk, concurrency и queue limits локального хоста |
| Владелец deployment | Конфигурация/release FastAPI Cloud | Ansible roles и одобренный on-premises release process |

Настройки QwenCloud demo, предположения о free tier и API key нельзя копировать в production Ansible inventory или Edge environment. Аналогично, on-premises Ollama profile не доказывает наличие локальной модели в FastAPI Cloud demo.

### Размещение production AI
- По умолчанию размещайте основной Mortarium AI runtime на Central on-premises platform за аутентифицированной внутренней API-границей.
- Не устанавливайте model runtime на каждом аптечном Edge node по умолчанию. Локальный inference на площадке — отдельное решение по hardware profile, включаемое явно для каждой площадки.
- POS checkout, фиксация складских операций, разрешение отпуска, платежи и audit transactions должны быть независимы от Mortarium и Ollama.
- При недоступности Central AI функции, зависящие от AI, должны деградировать контролируемо; Edge продолжает разрешённые локальные бизнес-процессы и ставит подходящие sync events в очередь.
- Локальный Edge AI runtime, если будет одобрен, может предоставлять только дополнительную функцию помощника. Он не должен разрешать отпуск, платежи, изменение остатков или обходить детерминированные бизнес-правила.

### Ответственность Ansible за production AI runtime

Целевая Ansible role (например, `mortarium_ai`) должна отвечать за:
- зафиксированную версию Ollama runtime и конфигурацию сервиса;
- явный model identifier/revision и проверку целостности model artifact;
- model storage path, предварительную проверку свободного места и retention policy;
- CPU/GPU/RAM resource limits и concurrency/queue bounds, подтверждённые на реальном профиле хоста;
- привязку listener только к внутреннему интерфейсу, firewall rules и аутентифицированный service-to-service доступ;
- startup/readiness checks, проверяющие фактическую загрузку модели и выполнение ограниченного synthetic inference;
- структурированные operational metrics, logs и traces без prompts, secrets или идентифицирующих пациента payloads;
- контролируемые обновления модели/runtime, canary validation и rollback к ранее проверенному artifact;
- restart policy сервиса и graceful shutdown.

Не открывайте неаутентифицированный management/API port Ollama напрямую в публичный интернет. Размещайте перед inference аутентифицированный application gateway. Ограничивайте список application services и MCP tools, которым разрешено вызывать AI capabilities.

### Критерии приёмки production AI

До включения production profile:
1. Проверьте выбранную quantized model на точном профиле CPU/GPU/RAM целевого хоста; зафиксируйте model artifact hash, inference latency, throughput, peak memory и disk usage.
2. Выполните репрезентативные синтетические аптечные prompts и одобренный RAG evaluation suite; проверьте citation grounding, medication entity accuracy, negation preservation, multilingual retrieval и patient/tenant isolation.
3. Убедитесь, что перегрузка AI или отказ процесса не ухудшает latency и доступность POS-транзакций.
4. Смоделируйте отказ WAN/Central и подтвердите, что разрешённые Edge offline workflows продолжают работать.
5. Проверьте internal authentication, network policy, secret handling, telemetry redaction и auditability.
6. Протестируйте обновление и rollback модели/runtime без изменения бизнес-данных или схемы БД.
7. Зафиксируйте точные версии модели/runtime и benchmark evidence в release artifact.

Указанное имя модели — документированный целевой профиль, а не доказательство того, что Ollama или модель уже установлены, измерены или работают на production hardware. Hardware sizing, concurrency limits, latency SLO и решение о локальном inference на Edge зависят от результатов измеренного pilot.

## 4. Ответственность playbooks

Рекомендуемые точки входа:
- `site.yml`: только orchestration; подключает playbooks для соответствующих ролей.
- `bootstrap.yml`: первичная настройка ОС, SSH, VPN и host identity.
- `central.yml`: центральные сервисы.
- `pharmacy-edge.yml`: одна или несколько Edge-площадок.
- `deploy.yml`: развёртывание приложения с зафиксированным release.
- `update.yml`: контролируемый staged release с preflight и postflight checks.
- `backup.yml`: запуск/проверка backup и проверка off-site transfer.
- `restore.yml`: явный restore workflow с обязательным выбором backup и target.
- `healthcheck.yml`: read-only отчёт о состоянии сервисов и операций.
- `disaster-recovery.yml`: документированная процедура восстановления Central или площадки.

В каждой операторской команде явно указывайте inventory. Production playbooks должны fail-closed завершаться, если не заданы environment, site identity, image digest, backup target или обязательные secrets.

## 5. Целевая ёмкость: до 100 аптек

Целевая архитектура поддерживает до 100 независимых Edge sites за счёт стабильной site identity, секретов на площадку, изолированных локальных БД, групп Central/Edge в inventory и версионируемых sync contracts. Начальный playbook ограничивает запуск максимум десятью хостами; профиль на 100 площадок нельзя включать до прохождения стартовых quality gates и последующих fleet-scale tests.

Для полного fleet используйте dynamic inventory на основе CMDB. Держите Central и Edge в отдельных группах, а Edge разделяйте на явно одобренные canary/wave child groups. `ansible/inventory/examples/fleet-100.yml` — неисполняемый пример схемы.

Пример возможной последовательности rollout:
1. Одна изолированная lab Edge площадка.
2. Пять pilot аптек.
3. Двадцать аптек.
4. Тридцать аптек.
5. Оставшиеся сорок пять аптек.

Lab площадка отделена от production. Волны 5 + 20 + 30 + 45 дают 100 production площадок; это планировочные примеры, а не включённые defaults. Корректируйте размер волн согласно одобренному inventory и никогда не предполагайте, что все площадки доступны.

Ansible `serial` ограничивает размер batch для play, но не заменяет release gates. После каждой волны:
- проверяйте readiness приложения, а не только liveness процесса;
- проверяйте read/write операции локального PostgreSQL;
- проверяйте readiness Sync Engine и состояние outbox/inbox;
- проверяйте время последней успешной синхронизации с Central, если WAN доступен;
- проверяйте дисковую ёмкость, синхронизацию времени и UPS telemetry;
- проверяйте свежесть и целостность backup;
- выполняйте безопасный для аптеки synthetic transaction test в одобренном тестовом режиме;
- останавливайте rollout при любой ошибке или недоступной площадке до завершения triage.

Используйте явные maintenance windows и approval оператора между волнами. Отключённая площадка должна быть отмечена как не обновлённая, а не молча пропущена.

## 6. Правила release и миграций

- Собирайте artifact один раз в CI и развёртывайте один и тот же immutable image digest в lab, pilot и production.
- Передавайте `PHARMAVIYUM_BACKEND_IMAGE_DIGEST` в формате `sha256:<64-hex>`; Ansible загружает и записывает ссылку на digest, а не разрешает mutable tag. Для rollback нужны предыдущий проверенный image digest и release label.
- Не используйте `latest` или изменяемые release tags как идентификатор deployment.
- Запускайте `ansible/playbooks/migrate.yml` как отдельную, явно одобренную операцию перед `deploy.yml`; требуется `migration_approved=true` и непустой change reference.
- Migration playbook запускает только DB/cache dependencies, проверяет готовность PostgreSQL, создаёт pre-migration compressed dump, проверяет gzip archive и фиксирует SHA-256 до запуска Alembic из pinned release image.
- Проверяйте миграцию на production-like копии до rollout. Валидный gzip archive и checksum подтверждают только целостность архива; они не заменяют изолированный restore drill или off-site backup.
- Используйте expand/contract migrations: сначала совместимая схема, затем версии приложения, затем удаление устаревшей схемы после периода совместимости.
- Не запускайте fleet-wide migration отдельно на каждом Edge, если миграция предназначена только для Central.
- Версии Edge application и event schema должны быть совместимы с Central sync contract во время staged rollout.
- Rollback backend не отменяет миграцию БД автоматически. Для каждой миграции определяйте forward-fix или проверенную стратегию восстановления.
- Сохраняйте совместимость application, schema и event contract в release metadata.

## 7. Контроль backup и restore

Текущий backup playbook создаёт локальный gzip-compressed SQL dump, проверяет gzip stream и опубликованный SHA-256, записывает metadata manifest, сериализует backup runs через lock и хранит локальные файлы согласно `backup_retention_days`. Restore playbook проверяет независимо переданный SHA-256 и восстанавливает данные в новую изолированную БД на одном явно подтверждённом хосте; он не перезаписывает live application database и оставляет успешную restore target для проверки оператором. Это полезные локальные проверки, но они пока не являются решением disaster recovery.

До production fleet использования добавьте:
- явную проверку целостности backup (например, проверку dump соответствующим PostgreSQL client);
- шифрование до off-site transfer;
- удалённое хранилище, независимое от аптечного хоста;
- retention policy с учётом бизнес- и нормативных требований;
- мониторинг возраста backup и передачи;
- проверку off-site backup и восстановление из удалённой копии;
- проверку восстановленных критических бизнес row counts и application invariants (текущий drill проверяет только базовое наличие схемы и Alembic metadata);
- документированные RPO/RTO для каждой площадки и Central.

Планирование backup намеренно не устанавливается playbook на аптечных Edge-хостах. Запускайте его с защищённого automation controller (например, AWX/AAP или одобренного scheduler), который получает Vault/secret-manager credentials во время выполнения. Не распространяйте по fleet повторно используемый Vault password в виде неуправляемого plaintext-файла.

Backup нельзя считать пригодным для восстановления, пока restore test не завершился успешно на изолированной цели.

## 8. Безопасность и секреты

- Используйте credentials и node identities отдельно для каждой площадки; избегайте одного общего credential для всех аптек.
- Предпочитайте внешний secret manager; Ansible Vault допустим как контролируемый резервный вариант.
- Используйте `no_log: true` для задач, обрабатывающих secrets.
- Не открывайте PostgreSQL, Valkey или backend ports напрямую в публичный интернет.
- Предпочитайте исходящее Edge-to-Central соединение через authenticated TLS/VPN; не требуйте входящий публичный SSH к аптечным площадкам.
- Ограничивайте Docker socket и членство в группе `docker`; доступ к Docker фактически эквивалентен root.
- Ротируйте сертификаты и credentials с проверенным периодом перекрытия.
- Храните audit и operational telemetry без patient-identifying payloads, кроме случаев, когда это явно необходимо и защищено.

## 9. Обязательные quality gates Ansible

До допуска role в production:
- YAML syntax и `ansible-lint` должны проходить.
- Molecule tests должны охватывать converge, idempotence, verify и destroy.
- Второй запуск playbook не должен показывать неожиданных изменений.
- `--check --diff` должен проходить review там, где модули поддерживают этот режим.
- Secrets должны отсутствовать в output, diffs и CI artifacts.
- Failure-injection test должен подтверждать, что отказ хоста/batch останавливает последующие волны.
- Restore и rollback должны быть выполнены в изолированной лаборатории.
- Production inventory должен быть защищён и проходить отдельное review от кода roles.

## 10. Текущие блокеры перед заявлением о production readiness для 100 площадок

1. В репозитории уже есть основа durable Edge outbox dispatcher и Central inbox ingress; полная операционная приёмка, end-to-end reconciliation, conflict workflows, fleet load tests и production recovery evidence всё ещё не завершены.
2. Production inventory содержит один placeholder host, а не источник данных fleet из 100 площадок.
3. Deployment проверяет `/ready`, но site-level POS synthetic transaction, backup integrity, sync backlog/last-sync и UPS checks пока не подключены к Ansible postflight.
4. Жизненный цикл PostgreSQL в основном управляется Compose; Ansible PostgreSQL role не является полноценной lifecycle/HA role.
5. Nginx role не подключена к текущему deployment, и текущий Compose не содержит Nginx service.
6. Backup пока локальный; off-site copy и restore-from-off-site не настроены. Новый isolated restore drill проверяет базовую схему, но не является полной приёмкой восстановления приложения.
7. Rollback меняет только backend image; он не обрабатывает совместимость схемы или восстановление данных.
8. UPS, VPN, site identity, host security и централизованный fleet monitoring пока не подтверждены как развёрнутые возможности.

## 11. Порядок реализации

1. Завершите Ansible hardening и test gates для одной lab Edge площадки, затем одной pilot аптеки, затем 2–3 и до десяти площадок. В течение этого этапа сохраняйте активный лимит rollout равным 10.
2. Завершите ADR-0002 и доменные контракты Central/Edge.
3. Завершите end-to-end tests для durable outbox/inbox и sync processing contract.
4. Создайте lab Edge Compose/deployment profile с durable local PostgreSQL.
5. Добавьте lab inventory и Ansible role tests; пока не перенаправляйте production inventory.
6. Добавьте backup integrity, off-site transfer и restore playbook; продемонстрируйте recovery.
7. Добавьте Central inventory, per-site Edge identity/VPN, readiness и sync monitoring.
8. Проведите lab и small-pilot failure exercises до расширения rollout.
9. Только после подтверждения 1–10 площадок включайте dynamic inventory для 100 площадок, staged wave controller, capacity Central observability, backup throughput и recovery capacity.

## Ссылки

- `docs/adr/ADR-0002-offline-first-central-edge.md`
- `docs/devops/README.md`
- `ansible/ansible.cfg`
- `ansible/playbooks/deploy.yml`
- `ansible/playbooks/backup.yml`
- `ansible/playbooks/migrate.yml`
- `ansible/playbooks/rollback.yml`
- `ansible/roles/app-backend/files/docker-compose-backend.yml`
- [Ansible rolling execution](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html)
- [Ansible testing strategy](https://docs.ansible.com/projects/ansible/latest/reference_appendices/test_strategies.html)