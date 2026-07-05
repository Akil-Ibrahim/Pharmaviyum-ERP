# Docker Deployment Guide

## Overview
Pharmaviyum CRM uses Docker for containerized deployment with:
- Multi‑stage builds for optimized image size  
- Separate containers for API and workers  
- Production‑ready configuration with monitoring  
- Development environment with hot reload  

## Quick Start

### Development
```bash
# Start all services.
./scripts/dev.sh

# Or manually
docker-compose up --build -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop services
docker-compose down
```

**Available Services:**
- API: http://localhost:8000  
- API Docs: http://localhost:8000/docs  
- Redis GUI: http://localhost:8081  
- Database GUI: http://localhost:8082  

### Production
```bash
# 1. Configure environment
cp .env.prod.example .env.prod
nano .env.prod  # Edit with your values

# 2. Deploy
./scripts/deploy.sh

# 3. Check health
curl http://localhost/health
```

## Архитектура (Russian)

**Обзор**
Pharmaviyum CRM использует Docker для развертывания приложений в контейнерах с:
- Многоступенчатыми сборками для минимального размера образов  
- Отдельными контейнерами для API и воркеров  
- Конфигурацией, готовой к продакшену, включая мониторинг  
- Средой разработки с горячей перезагрузкой  

**Быстрый старт**

### Разработка
```bash
# Запуск всех сервисов
./scripts/dev.sh

# Либо вручную
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f api
docker-compose logs -f worker

# Остановка сервисов
docker-compose down
```

**Доступные сервисы:**
- API: http://localhost:8000  
- Документация API: http://localhost:8000/docs  
- GUI Redis: http://localhost:8081  
- GUI базы данных: http://localhost:8082  

### Продакшн
```bash
# 1. Настройка окружения
cp .env.prod.example .env.prod
nano .env.prod  # Укажите свои значения

# 2. Деплой
./scripts/deploy.sh

# 3. Проверка здоровья
curl http://localhost/health
```
