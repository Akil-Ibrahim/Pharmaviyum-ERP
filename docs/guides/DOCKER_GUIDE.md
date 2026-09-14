# Docker командаы для Pharmaviyum-CRM

Гайд с основными командами Docker для работы с проектом.

## Основные команды

### Запуск всех контейнеров
```bash
docker compose -f docker-compose.yml up -d --build
```
Запускает все сервисы в фоне (detached mode):
- Frontend (http://localhost:3000)
- Backend (http://localhost:8000)
- PostgreSQL база данных (5432)
- Redis кеш (6379)
- Mortarium AI (http://localhost:8001)
- Nginx reverse proxy (http://localhost)

### Правильный запуск из корня проекта
```bash
cd /workspaces/Pharmaviyum-CRM
docker compose -f docker-compose.yml up -d --build
```

### Если сервисы созданы, но не запущены
Если контейнеры находятся в состоянии `Created`, а не `Up`, выполните:
```bash
cd /workspaces/Pharmaviyum-CRM
docker compose -f docker-compose.yml start frontend mortarium-ai nginx
```

### Исправление ошибки сборки frontend
Если при сборке frontend появляется ошибка, связанная с отсутствием `pnpm-lock.yaml`:
```bash
cd /workspaces/Pharmaviyum-CRM/frontend/shadcn-admin
corepack pnpm install --lockfile-only
cd /workspaces/Pharmaviyum-CRM
docker compose -f docker-compose.yml up -d --build
```

### Остановка всех контейнеров
```bash
docker-compose down
```
Останавливает и удаляет все запущенные контейнеры и сеть.

### Перезапуск контейнеров
```bash
docker-compose restart
```
Перезапускает все активные контейнеры без их удаления.

### Просмотр статуса контейнеров
```bash
docker-compose ps
```
Показывает статус всех контейнеров (UP, Healthy, Starting и т.д.).

## Логирование и отладка

### Просмотр логов всех сервисов
```bash
docker-compose logs -f
```
Показывает логи всех контейнеров в реальном времени (с флагом `-f` для follow).

### Логи конкретного сервиса
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mortarium-ai
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f nginx
```

### Посмотреть последние 100 строк логов
```bash
docker-compose logs --tail=100 backend
```

## Работа с контейнерами

### Выполнить команду внутри контейнера
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Перестроить образы (если изменился Dockerfile)
```bash
docker-compose build
docker-compose up -d
```

### Полная переборка (удалить всё и запустить заново)
```bash
docker-compose down -v
docker-compose up -d
```
Флаг `-v` удаляет volumes (базу данных, кеш и т.д.).

## Полезные команды

### Проверить использование ресурсов
```bash
docker stats
```
Показывает CPU, память, сеть для каждого контейнера.

### Очистить всё неиспользуемое
```bash
docker system prune
docker system prune -a
```

### Посмотреть сетевые подключения контейнеров
```bash
docker network ls
docker network inspect pharmaviyum-crm_app-network
```

## Примеры использования

### Полный цикл перезагрузки
```bash
cd /workspaces/Pharmaviyum-CRM
docker-compose down
docker-compose up -d
docker-compose ps
```

### Проверка здоровья контейнеров
```bash
docker-compose ps | grep -E "healthy|unhealthy|starting"
```

### Просмотр ошибок при запуске
```bash
docker-compose up
# (без флага -d, чтобы видеть вывод в реальном времени)
```

## Доступ к сервисам

После успешного запуска доступны:

| Сервис | URL | Порт |
|--------|-----|------|
| Frontend (Docker) | http://localhost:3000 | 3000 |
| Backend API | http://localhost:8000 | 8000 |
| Mortarium AI | http://localhost:8001 | 8001 |
| PostgreSQL | localhost:5432 | 5432 |
| Redis | localhost:6379 | 6379 |
| Nginx (главная точка) | http://localhost | 80/443 |

## Переменные окружения

Проверить ENV переменные контейнера:
```bash
docker-compose exec backend env | grep -i "database\|redis\|api"
```

## Решение проблем

### Контейнер не запускается
```bash
docker-compose logs backend  # Смотрим ошибки
docker-compose down -v       # Удаляем volume
docker-compose up -d         # Запускаем заново
```

### Порт уже занят
```bash
# Найти что занимает порт
lsof -i :3000
# Убить процесс
kill -9 <PID>
```

### Переподключение после изменений
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Быстрые команды (скопируй и вставь)

```bash
# Запуск
docker-compose up -d && docker-compose ps

# Перезагрузка
docker-compose restart && docker-compose ps

# Остановка с очисткой
docker-compose down -v

# Логи backend
docker-compose logs -f backend

# Логи frontend
docker-compose logs -f frontend

# Вход в контейнер backend
docker-compose exec backend bash

# Вход в контейнер frontend
docker-compose exec frontend sh
```

---

**Дополнительные сведения:** смотри `docker-compose.yml` для конфигурации сервисов.
