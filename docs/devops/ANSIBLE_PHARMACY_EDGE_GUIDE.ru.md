# Ansible для Pharmacy Edge в Pharmaviyum

## 1. Назначение Ansible

Ansible — агентless-инструмент автоматизации IT-инфраструктуры и управления конфигурацией. Он подключается к Linux-хостам по SSH и применяет декларативные playbooks, описывающие желаемое состояние системы. Постоянный Ansible agent на серверах аптек не требуется.

В Pharmaviyum Ansible — контролируемый операционный слой подготовки и обслуживания серверов Pharmacy Edge. Он стандартизирует конфигурацию хостов, уменьшает configuration drift, развёртывает проверенные версии приложения, проверяет readiness и выполняет одобренные процедуры обслуживания.

Ansible не заменяет приложение Pharmaviyum, PostgreSQL, локальный POS или сервис синхронизации с Central. Он автоматизирует инфраструктуру, на которой работают эти компоненты.

## 2. Начальная граница внедрения: 1–10 аптек

Начальный операционный профиль ограничен **максимум десятью площадками Pharmacy Edge**. Начните с одной лабораторной аптеки, проверьте полный жизненный цикл, затем расширяйте внедрение до 2–3 и постепенно до десяти площадок. Развёртывание выполняется последовательно (`serial: 1`): ошибка хоста или readiness-проверки должна остановить переход к следующей площадке.

Лимит в десять площадок — операционное ограничение, а не доказательство того, что десять production-площадок уже прошли проверку. Не повышайте его без отдельной оценки ёмкости, безопасности, устойчивости и процесса rollout.

Каждая аптека должна иметь уникальные site identity, database credentials, Edge sync identity, backup namespace и ответственного за эксплуатацию.

## 3. Будущая архитектурная цель: до 100 аптек

Целевая архитектура рассчитана на поддержку до **100 независимых площадок Pharmacy Edge**. Это будущая цель по ёмкости, а не текущий размер rollout и не доказательство нагрузочного тестирования или приёмки fleet из 100 площадок.

Конфигурация Ansible намеренно разделяет `max_supported_pharmacy_sites: 100` и `active_rollout_limit: 10`. Начальные playbooks развёртывания и миграции должны отклонять inventory более чем из десяти площадок, пока отдельная оценка ёмкости, безопасности, устойчивости и эксплуатации не разрешит расширение.

Для будущего fleet:
- Используйте dynamic inventory на основе CMDB; держите Central hosts отдельно от Pharmacy Edge hosts.
- Разделяйте площадки на явные canary- и rollout-wave группы. Сохраняйте уникальные pharmacy ID, site code, Edge identity, PostgreSQL credentials и backup namespace для каждой площадки.
- Начальный rollout должен оставаться последовательным и fail-fast. Любой будущий batch size должен быть обоснован измеренной ёмкостью controller, сети, registry, базы данных и состоянием площадок.
- До повышения активного лимита завершите fleet load/failure tests, backup/restore drills, проверку sync backlog и replay, настройку monitoring/alerting и документирование RPO/RTO.
- Рассматривайте `ansible/inventory/examples/fleet-100.yml` только как пример схемы, который нельзя запускать как production inventory.

Профиль на 100 площадок — архитектурный резерв. Не меняйте действующее ограничение в десять площадок в рамках текущего rollout.

## 4. Целевая операционная модель

У аптеки есть выделенный Edge-хост в локальной сети. Локальные POS-процессы не должны требовать постоянного WAN-соединения с Central для каждой транзакции. Edge-хост хранит локальные операционные данные и синхронизируется с Central при наличии связи.

Ansible запускается с защищённого automation controller или одобренного CI runner. Он подключается к выбранному Edge-хосту по ограниченному SSH management path. Ansible не является публичным web-сервисом и не должен запускаться с POS-рабочего места сотрудника.

```text
Защищённый Ansible Controller
          | SSH через ограниченную management network
          v
Pharmacy Edge Host (одна площадка)
  - Docker Engine и Compose
  - Pharmaviyum API
  - Локальные PostgreSQL и cache
  - Локальные sync services и backup artifacts
          | HTTPS-синхронизация при наличии WAN
          v
Pharmaviyum Central
```

## 5. Требования к аптечной площадке

До подключения площадки проверьте:
1. Доступен поддерживаемый Linux-сервер или VM; оцените CPU, память, диск и защиту электропитания.
2. У хоста есть стабильный hostname и зарезервированный management IP.
3. SSH доступен только из одобренной management network или controller.
4. Выделенная non-root automation account имеет строго ограниченные privilege escalation.
5. SSH host keys проверены независимым способом; не отключайте host-key checking.
6. Docker Engine и Compose соответствуют версиям, зафиксированным в репозитории.
7. Доступен необходимый исходящий трафик к одобренному container registry и Central endpoint.
8. Настроены синхронизация времени, firewall policy, мониторинг диска и UPS.
9. Подготовлены уникальные pharmacy/site identity и отдельные credentials.
10. Зафиксированы change reference, окно обслуживания, ответственный за rollback и контакт для восстановления.

Никогда не используйте повторно пароль базы данных, Edge token или site identity другой аптеки.

## 6. Подготовка Ansible controller

Используйте изолированный controller с контролем доступа, например AWX/AAP или одобренный CI runner.
- Зафиксируйте версии Ansible Core и collections.
- Храните SSH keys и Vault credentials в secret store controller.
- Ограничьте круг лиц, которые могут запускать deployment, migration, backup и restore jobs.
- Требуйте approval для защищённых inventories и production environments.
- Храните inventories и playbooks в version control; никогда не коммитьте secrets или расшифрованные Vault-файлы.
- Записывайте оператора, commit, release digest, целевую площадку, change reference и результат job.

Controller должен иметь сетевой доступ только к необходимым management endpoints.

## 7. Inventory одной площадки

Начинайте с одного лабораторного хоста. Передавайте реальные параметры подключения через защищённый источник inventory.

В репозитории есть изолированный lab inventory: `ansible/inventory/lab/hosts.yml`. Он получает lab host, SSH user и пароль лабораторной базы из защищённых runtime environment variables; используются непроизводственные pharmacy ID и site code. Перед использованием изучите этот файл. Не переносите его lab identity или credentials в production.

Production inventory должен определять реальный SSH endpoint/user, уникальные `pharmacy_id` и `site_code`, а также уникальный `postgres_password` для каждого хоста.

## 8. Release inputs и секреты

Передавайте обязательные значения во время запуска job или через зашифрованные переменные:
- `PHARMAVIYUM_APP_VERSION`: неизменяемый release tag или одобренный image digest; никогда не используйте `latest`.
- `PHARMAVIYUM_BACKEND_IMAGE_DIGEST`: одобренный неизменяемый digest образа `sha256:<64-hex>`.
- `PHARMAVIYUM_GHCR_USERNAME` и `PHARMAVIYUM_GHCR_TOKEN`: credentials registry с минимально необходимыми правами.
- Для каждого хоста — `pharmacy_id`, `site_code`, `ansible_host` и `ansible_user`; ID и site codes должны быть уникальными.
- Уникальный `postgres_password` для каждого хоста через encrypted host variables или secret manager (lab inventory читает `PHARMAVIYUM_LAB_POSTGRES_PASSWORD`).
- Явно одобренные версии каждого пакета в `docker_package_names` через `docker_package_versions`; deployment завершается fail-closed, если хотя бы одна фиксация версии отсутствует.
- Edge node UUID, Edge token и Central HTTPS sync URL: настройте все три вместе либо оставьте все три отключёнными до одобрения подключения синхронизации.

Не помещайте секреты в shell history, аргументы командной строки, tickets или source control. Предпочитайте защищённые credentials controller и masked runtime variables. Убедитесь, что job logs не раскрывают секретные значения.

## 9. Процесс развёртывания

1. Проверьте целевой commit и diff playbook.
2. Убедитесь, что inventory содержит только одобренные аптечные хосты и не более десяти площадок.
3. Запустите syntax, lint, unit и role tests в CI.
4. Проведите тестирование в изолированной лаборатории до аптечного pilot.
5. Проверьте immutable image reference, уникальные site credentials и change approval.
6. Запустите deployment playbook для лаборатории или явно одобренной площадки.
7. Проверьте `/ready`, состояние контейнеров, базы данных, диска и синхронизации.
8. Выполните POS smoke test и убедитесь, что временная потеря WAN не блокирует локальные продажи.
9. Зафиксируйте release digest и результаты проверки до добавления следующей площадки.

Из каталога `ansible/` команда для лаборатории:

```bash
ansible-playbook -i inventory/lab/hosts.yml playbooks/deploy.yml --limit pharmacy-edge-lab-01
```

Controller должен передать все обязательные lab connection/release variables и одобренные Docker package pins во время запуска. Lab inventory изолирован и никогда не должен указывать на действующую аптеку. В `ansible.cfg` production inventory остаётся inventory по умолчанию, поэтому для лабораторных операций всегда явно передавайте нужный lab inventory.

Никогда не запускайте production deployment из непроверенной ветки.

## 10. Миграции базы данных выполняются отдельно

Deployment приложения не должен автоматически запускать Alembic migrations. Миграция — отдельное проверяемое изменение, требующее собственного playbook, проверок совместимости, явного approval и change reference, подтверждённой резервной копии, контролируемого выбора цели и проверки readiness после миграции. Не используйте обычный deployment workflow как обходной путь для изменения схемы.

## 11. Резервное копирование и восстановление

Резервная копия, хранящаяся только на аптечном Edge-хосте, не является disaster recovery. До production acceptance определите и проверьте:
- зашифрованное off-site хранилище, независимое от аптечного хоста;
- удалённые site-scoped identity и права загрузки с минимальными привилегиями;
- проверку checksum и artifact после передачи;
- централизованно контролируемые правила хранения и удаления;
- документированные RPO и RTO;
- восстановление из удалённой копии в изолированную базу данных;
- бизнес-проверку критических таблиц, количества строк, версии миграции и готовности приложения.

Никогда не проверяйте restore путём перезаписи рабочей базы аптеки. До признания площадки восстанавливаемой проведите успешный изолированный restore drill.

## 12. Безопасность и операционные ограничения

- Используйте SSH key authentication, проверку host keys, минимальные привилегии и защищённые credentials controller.
- Не храните secrets в Git, logs, process arguments или открытых inventory.
- Фиксируйте production container images по immutable digest.
- Открывайте только необходимые сервисы; порты базы данных не должны быть доступны из публичной сети.
- Используйте уникальные database credentials и Edge sync identities для каждой аптеки.
- Используйте Ansible check mode там, где он поддерживается, но не считайте его заменой лабораторному тестированию.
- Поддерживайте идемпотентность roles и проверяйте, что повторный запуск не создаёт неожиданных изменений.
- Останавливайтесь при ошибке readiness; не переходите к следующей аптеке.
- Сохраняйте deployment, migration, backup, restore и rollback как отдельные аудируемые операции.

## 13. Чек-лист приёмки площадки

Площадка не считается принятой только потому, что playbook завершился успешно. Необходимы доказательства:
- [ ] Hardening хоста, SSH, firewall, синхронизация времени и UPS monitoring.
- [ ] Воспроизводимое выполнение Ansible и чистая идемпотентность второго запуска.
- [ ] Неизменяемый application release и успешные readiness checks.
- [ ] Локальная POS-транзакция во время WAN outage.
- [ ] Безопасный replay синхронизации после восстановления соединения.
- [ ] Отсутствие дублированных продаж и складских движений после retry/replay.
- [ ] Проверенные локальные и зашифрованные off-site backups.
- [ ] Успешное изолированное восстановление из off-site копии.
- [ ] Мониторинг диска, базы данных, возраста backup, sync backlog и времени последней успешной синхронизации.
- [ ] Назначенные владелец площадки, RPO/RTO, ответственный за rollback и контакт поддержки.

## 14. Текущие ограничения

Это руководство описывает целевой процесс и начальную границу в десять площадок. Оно не утверждает, что production acceptance checklist уже выполнен. Для полного жизненного цикла Pharmacy Edge всё ещё нужны результаты лабораторных проверок: off-site backup и restore, восстановление на бизнес-уровне, приёмка offline POS, UPS monitoring и end-to-end восстановление синхронизации.

Не развёртывайте систему на реальных аптечных хостах, пока соответствующие изменения не одобрены и лабораторные/pilot gates не пройдены.