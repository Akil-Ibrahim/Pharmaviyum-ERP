# ADR: Архитектура зашифрованных off-site backup для Pharmacy Edge

- **Статус:** Proposed; первый Restic upload slice реализован, но операционная приёмка и Production DR не подтверждены.
- **Область:** лаборатория и пилот на 1 площадке, rollout на 2–3 и 10 площадок; архитектурная цель — до 100 аптек.
- **Полномочия:** только проектирование. Документ не разрешает создавать provider resources или credentials, передавать backups, удалять retention-копии, выполнять restore или deployment.

## Контекст

Локальный backup workflow создаёт gzip-сжатый PostgreSQL dump на Pharmacy Edge, проверяет gzip integrity и SHA-256, записывает manifest и удаляет истёкшие локальные артефакты только после проверки новой резервной копии. Отдельно появился первый implementation slice для off-site transfer: `ansible/playbooks/backup-offsite.yml`, с инструкцией `ansible/OFFSITE_BACKUP.md`. Он загружает уже проверенные dump, checksum и manifest в заранее созданный site-scoped Restic REST repository. Playbook не создаёт repository и не настраивает server-side ACL; сам репозиторий не подтверждает наличие реального Production endpoint или credentials. Локальный restore drill не восстанавливает данные из remote repository. Эти механизмы пока не дают принятой end-to-end disaster-recovery capability.

## Предлагаемое решение

Использовать **restic** как слой зашифрованных snapshots/repository и независимо управляемый **append-only REST endpoint** либо object storage с эквивалентной неизменяемостью и least-privilege гарантиями. Конкретный storage provider остаётся абстрактным до утверждения владельца аккаунта, региона/data residency, стоимости, лимитов, retention и compliance требований.

### Целевой поток данных

1. Edge создаёт и проверяет PostgreSQL dump существующим локальным workflow.
2. Только проверенный артефакт шифруется и загружается по TLS с проверкой сертификата.
3. У каждой аптеки есть стабильный неизменяемый pharmacy_id и отдельная граница repository. Hostname — metadata, а не идентичность площадки.
4. Edge получает уникальный site-scoped append-only credential. Он не может удалять/prune snapshots или обращаться к repository другой площадки.
5. Отдельная защищённая controller identity выполняет repository checks, retention/prune и авторизацию restore. Она не устанавливается на Edge.
6. Recovery keys хранятся независимо от Edge и backup repository. Процедура получения ключа тестируется.
7. Controller записывает site ID, snapshot ID, timestamp, bytes, результат проверки и расположение repository в централизованный мониторинг; secrets и patient data не логируются.
8. Remote restore сначала выполняется только в новую изолированную БД/среду. Переключение production — отдельное утверждаемое изменение.

## Требования безопасности

- Шифруйте данные до их выхода с Edge. TLS защищает транспорт, но не заменяет шифрование backup.
- Храните credentials и recovery keys в утверждённом secret manager/controller vault; не коммитьте, не логируйте, не передавайте в process arguments и не размещайте в world-readable файлах.
- Используйте уникальные credentials и repository boundaries для каждой площадки; общий Edge upload key для всего fleet запрещён.
- Edge identity имеет только append-only права. Retention и restore доступны только controller, под аудитом и защитой approval.
- Проверяйте TLS certificates; не используйте insecure TLS flags или plaintext transport.
- При поддержке включайте storage-side encryption/versioning/immutability как дополнительную защиту.
- Документируйте владельца key escrow, ротацию, отзыв, восстановление аккаунта и incident response.
- Не помещайте в metadata имена пациентов, содержимое рецептов и лишние персональные данные.

## Надёжность и retention

- Принимайте remote snapshot только после завершения upload и независимой remote integrity/readability проверки. Успешный exit code процесса загрузки недостаточен.
- Ошибка remote upload никогда не должна запускать удаление локального backup.
- Локальная очистка разрешена только после появления проверенного remote snapshot и сохранения заданного локального safety window.
- Retention утверждается с учётом правовых/регуляторных требований и recovery objectives. Семь локальных дней не являются политикой remote retention.
- Защищайтесь от злонамеренного удаления append-only доступом, storage immutability/versioning и отдельными retention credentials.
- Создавайте alerts для пропущенных окон, устаревшего last-success, ошибок upload/integrity, capacity, истечения credentials и ошибок retention.
- Используйте ограниченную конкурентность, per-site jitter и backoff; не запускайте синхронную загрузку всего fleet.

## Критерии приёмки восстановления

Restore не считается успешным только потому, что SQL импортирован. Изолированная проверка должна подтвердить:
- обнаружение и получение remote snapshot с recovery credentials;
- целостность repository, идентичность snapshot и pharmacy/site;
- восстановление в новую изолированную БД, никогда поверх live DB;
- schema и ожидаемую Alembic revision;
- критические бизнес-инварианты и репрезентативные row counts без раскрытия patient data;
- запуск приложения/readiness с изолированной БД;
- POS smoke test и проверки sync/outbox consistency в лаборатории;
- измеренные длительность восстановления и окно потери данных.

Публикуйте RPO/RTO только после повторяемых timed drills. Частота backup сама по себе не доказывает RPO/RTO.

## Контракт реализации Ansible

Разделяйте workflow на независимо тестируемые блоки и фиксируйте их текущий статус:

- `backup_local` — реализован в `ansible/playbooks/backup.yml`: создание и проверка локального DB dump и metadata manifest.
- `backup_offsite` — первый upload slice реализован в `ansible/playbooks/backup-offsite.yml`: требуется заранее созданный site-scoped Restic REST repository и защищённые credentials площадки; проверяются remote snapshot metadata и SHA-256 выгруженных артефактов. Проверка на реальном repository пока не подтверждена.
- `backup_maintenance` — не реализован: controller-only repository checks и retention/prune с environment/target guardrails ещё требуют реализации.
- `restore_offsite_drill` — не реализован: существующий `ansible/playbooks/restore.yml` выполняет локальный isolated-database drill, а не remote restore.
- `backup_monitoring` — не реализован: last-success, age, bytes, snapshot ID, verification state и failure reason пока не интегрированы в monitoring.

Roles должны быть идемпотентными там, где это применимо, поддерживать содержательный check mode, использовать no_log: true для задач с секретами, предпочитать command.argv shell interpolation и включать Molecule coverage для успеха, retries, сетевого сбоя, неверных credentials, повреждённого артефакта, неверной площадки, ошибки retention и очистки частичного restore.

## Gates rollout

| Этап | Требуемые доказательства |
|---|---|
| Лаборатория, 1 площадка | Зашифрованная remote upload, remote verification, key escrow/retrieval, изолированный remote restore, readiness приложения, измеренные RPO/RTO |
| Пилот, 1 аптека | Проверка backup window, WAN interruption/retry, ротация/отзыв credentials, runbook, доставка alerts |
| 2–3 аптеки | Изоляция площадок, отсутствие cross-site restore, ограниченная конкурентность, восстановление при одновременных отказах |
| До 10 аптек | Fleet dashboard, capacity/cost model, retention controller, cadence drills, владелец incident |
| Проектный предел 100 | Capacity/rate-limit tests, per-site identity/credentials, controlled scheduling, central audit/monitoring, fleet DR exercise |

Предел 100 площадок — архитектурная цель, а не доказательство готовности к 100-site эксплуатации. Активный rollout limit задаётся отдельно.

## Решения до реализации

1. Утверждённый storage provider и владелец аккаунта.
2. Регион/data residency и применимые privacy/regulatory требования.
3. Ожидаемый размер БД и дневной объём изменений на аптеку.
4. Утверждённые RPO/RTO для каждой аптеки и Central.
5. График retention и требования legal hold.
6. Secret manager/controller и владелец recovery-key escrow.
7. Managed append-only restic endpoint или object storage с эквивалентными гарантиями.
8. Monitoring destination и ответственный за on-call/incident.

## Текущая граница безопасности

Это остаётся предлагаемой архитектурой и не разрешает Production disaster-recovery операции. В репозитории теперь есть первая реализация off-site upload в `ansible/playbooks/backup-offsite.yml` (описана в `ansible/OFFSITE_BACKUP.md`). Она использует Restic encryption, требует заранее созданный site-scoped HTTPS repository и защищённые credentials площадки, проверяет локальные артефакты и site identity, затем сверяет remote snapshot metadata и SHA-256 артефактов, прочитанных обратно из repository. `ansible/tests/test_offsite_backup_guardrails.sh` проверяет только synthetic controller-side preflight/guardrails и не подключается к реальному Restic repository. Не завершены provisioning provider/repository и проверка server-side ACL, key escrow, remote repository integrity и retention management, remote restore в изолированную БД, проверка application/POS business invariants, monitoring, измерение RPO/RTO и приёмка площадки. Репозиторий не содержит настроенных Production endpoint, credentials, secrets или реальных данных аптек; готовность Production DR не подтверждена.
