# Lab Pharmacy Server / Лабораторный Pharmacy Server

## Purpose / Назначение

The Lab Pharmacy Server is a controlled, reproducible environment used to validate Pharmaviyum's future on-premises deployment before Ansible is used on a real pharmacy server.

Лабораторный Pharmacy Server — это контролируемая воспроизводимая среда для проверки будущего on-premise-развёртывания Pharmaviyum до использования Ansible на реальном сервере аптеки.

The lab is a deployment validation environment, not a production pharmacy environment. It must not be used for real patient or pharmacy business data.

Лаборатория является средой валидации deployment, а не production-средой аптеки. В ней не должны использоваться реальные данные пациентов или реальные коммерческие данные аптеки.

## Architecture / Архитектура

```
GitHub Codespace / Ansible Control Node
                    |
                    | SSH
                    v
          +----------------------+
          |   Lab Pharmacy       |
          |       Server         |
          |                      |
          | Linux                |
          | Docker + Compose     |
          | Pharmaviyum          |
          | PostgreSQL + pgvector|
          | Redis                |
          | Ollama               |
          | Qwen3.5 9B           |
          +----------------------+
```

GitHub Codespaces is used as a laboratory/control environment. The simulated Pharmacy Server represents the type of Linux host that Ansible will manage during a future on-premises installation.

GitHub Codespaces используется как лабораторная/control-среда. Симулированный Pharmacy Server представляет Linux-хост, которым Ansible будет управлять при будущем on-premise-внедрении.

## Deployment boundary / Граница ответственности

- Ansible: server provisioning, configuration, deployment, updates and health checks.
- Docker Compose: application runtime and service composition.
- Pharmaviyum: ERP/CRM application and Mortarium AI layer.
- PostgreSQL + pgvector: application and vector data.
- Redis: cache/queue and supporting runtime state.
- Ollama: local LLM runtime.
- Qwen3.5 9B: default local Mortarium model for the current on-premises profile.

- Ansible: подготовка сервера, конфигурация, deployment, обновления и health checks.
- Docker Compose: runtime приложения и композиция сервисов.
- Pharmaviyum: ERP/CRM-приложение и AI layer Mortarium.
- PostgreSQL + pgvector: прикладные и векторные данные.
- Redis: cache/queue и вспомогательное runtime-состояние.
- Ollama: локальный runtime LLM.
- Qwen3.5 9B: текущая модель по умолчанию для локального Mortarium-профиля.

## Minimum laboratory profile / Минимальный лабораторный профиль

The laboratory intentionally starts below the recommended production hardware profile. Its purpose is deployment validation, not performance benchmarking.

Лаборатория намеренно имеет характеристики ниже рекомендуемого production-профиля. Её задача — проверка deployment, а не benchmark производительности.

| Resource / Ресурс | Laboratory target / Лабораторная цель |
|---|---|
| OS | Ubuntu Linux |
| CPU | 4 vCPU |
| RAM | 8 GB |
| Disk | 50–80 GB |
| Network | Private/lab network |
| Access | SSH |
| Runtime | Docker + Docker Compose |
| Database | PostgreSQL + pgvector |
| Cache/queue | Redis |
| Local LLM | Ollama + Qwen3.5 9B |
| Application | Pharmaviyum ERP/CRM + Mortarium |

The laboratory may run Qwen3.5 9B on CPU. CPU execution validates integration only; it does not represent production LLM performance.

В лаборатории Qwen3.5 9B может работать на CPU. CPU-запуск проверяет интеграцию, но не является показателем production-производительности LLM.

## Mandatory validation path / Обязательный путь валидации

Before any real pharmacy deployment:

Перед любым развёртыванием в реальной аптеке:

```
Lab Pharmacy Server
        |
        v
Ansible validation
        |
        v
Pilot pharmacy server
        |
        v
Real pharmacy deployment
```

The Lab Pharmacy Server is therefore a required gate, not an optional demonstration.

Лабораторный Pharmacy Server является обязательным этапом, а не демонстрационным экспериментом.

## Validation stages / Этапы проверки

### 1. Ansible connectivity / Подключение Ansible

Verify:

- Ansible installation and version.
- Inventory resolution.
- SSH connectivity.
- Remote Python availability.
- Privilege escalation where required.

Проверяем:

- установку и версию Ansible;
- inventory;
- SSH-подключение;
- наличие Python на managed node;
- privilege escalation там, где она необходима.

### 2. Preflight / Предварительная проверка

Collect and validate:

- operating system;
- CPU and memory;
- available disk space;
- network connectivity;
- required ports;
- required packages and permissions.

Собираем и проверяем:

- ОС;
- CPU и RAM;
- свободное место;
- сетевое соединение;
- необходимые порты;
- пакеты и права доступа.

### 3. Server provisioning / Подготовка сервера

Ansible must be able to:

- create required users and directories;
- install required packages;
- install/configure Docker;
- install/configure Docker Compose;
- apply required host configuration.

Ansible должен уметь:

- создавать необходимые users и directories;
- устанавливать необходимые пакеты;
- устанавливать и настраивать Docker;
- устанавливать и настраивать Docker Compose;
- применять необходимые настройки хоста.

### 4. Pharmaviyum deployment / Развёртывание Pharmaviyum

Deploy and verify:

- Pharmaviyum API;
- PostgreSQL + pgvector;
- Redis;
- database migrations;
- required configuration;
- application health endpoint.

Разворачиваем и проверяем:

- Pharmaviyum API;
- PostgreSQL + pgvector;
- Redis;
- database migrations;
- конфигурацию;
- health endpoint приложения.

### 5. Mortarium local AI / Локальный AI Mortarium

Verify:

- Ollama starts successfully.
- Qwen3.5 9B is available.
- Pharmaviyum can reach Ollama.
- Mortarium can execute a controlled local inference request.

Проверяем:

- успешный запуск Ollama;
- наличие Qwen3.5 9B;
- доступ Pharmaviyum к Ollama;
- выполнение контролируемого локального inference-запроса Mortarium.

### 6. Health checks / Health checks

The deployment is successful only when the expected services are healthy and the application can complete its basic startup path.

Deployment считается успешным только после проверки состояния ожидаемых сервисов и прохождения базового startup path приложения.

### 7. Idempotency / Идемпотентность

Run the same Ansible deployment more than once.

The second run should not introduce unnecessary changes when the desired state has already been reached.

Запускаем один и тот же Ansible deployment повторно.

Повторный запуск не должен вносить ненужные изменения, если desired state уже достигнут.

Ansible documents idempotency as a core property of modules that converge systems toward a desired final state. The project will verify this property in the laboratory rather than assuming it.

Ansible рассматривает idempotency как ключевое свойство модулей, которые приводят систему к требуемому конечному состоянию. В Pharmaviyum это свойство будет проверяться в лаборатории, а не предполагаться автоматически. citeturn0search1

### 8. Check mode / Check mode

Where supported, use:

```bash
ansible-playbook playbooks/pharmacy-server.yml --check
```

Check mode is a simulation and does not apply supported changes to remote systems. It is used as an additional validation layer before applying changes.

Check mode является симуляцией и не применяет поддерживаемые изменения к удалённой системе. Он используется как дополнительный уровень проверки перед применением изменений. citeturn0search0

### 9. Update and recovery / Обновление и восстановление

The laboratory must eventually verify:

- application update;
- configuration update;
- controlled service failure;
- recovery;
- repeat deployment after recovery.

Лаборатория должна дополнительно проверять:

- обновление приложения;
- изменение конфигурации;
- контролируемый отказ сервиса;
- восстановление;
- повторный deployment после восстановления.

## GPU validation / Проверка GPU

GitHub Codespaces is suitable for deployment and integration validation, but the laboratory profile must not be treated as a GPU performance environment.

GitHub Codespaces подходит для проверки deployment и интеграции, но лабораторный профиль нельзя считать средой для benchmark GPU.

If GPU validation is required, the same Ansible deployment should later be executed against a separate GPU-capable Linux lab server. This allows the deployment layer to remain hardware-independent while performance testing is performed on representative hardware.

Если требуется проверка GPU, тот же Ansible deployment позднее запускается на отдельном Linux-лабораторном сервере с GPU. Это позволяет сохранить deployment layer независимым от конкретного оборудования, а performance testing выполнять на соответствующем hardware.

## Production gate / Условие перехода в production

A real pharmacy deployment must not start merely because the application runs in the lab.

Before a pilot, the project must additionally verify:

- backup and restore procedures;
- secrets and access control;
- firewall/network policy;
- hardware compatibility;
- monitoring and logging;
- database migration safety;
- operational rollback/recovery procedure;
- client-specific configuration.

Реальное развёртывание в аптеке не начинается только потому, что приложение запустилось в лаборатории.

Перед pilot необходимо дополнительно проверить:

- backup и restore;
- secrets и access control;
- firewall/network policy;
- совместимость оборудования;
- monitoring и logging;
- безопасность database migrations;
- rollback/recovery procedure;
- конфигурацию конкретного клиента.

## Definition of Done / Критерий готовности

The Lab Pharmacy Server phase is complete when the deployment can be reproduced from the documented procedure, the core services pass health checks, the application and local Mortarium path work, repeated Ansible execution is stable, and controlled update/recovery scenarios have been validated.

Этап Lab Pharmacy Server считается завершённым, когда deployment воспроизводится по документации, основные сервисы проходят health checks, приложение и локальный Mortarium path работают, повторный запуск Ansible стабилен, а сценарии контролируемого обновления и восстановления проверены.

Only then should the same deployment approach proceed to a pilot pharmacy server.

Только после этого тот же deployment-подход может переходить на pilot pharmacy server.
