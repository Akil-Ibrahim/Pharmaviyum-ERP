# FastAPI Authentication Setup

Этот документ описывает как настроить и запустить фронтенд и бэкенд с FastAPI JWT авторизацией.

## Архитектура

- **Backend**: FastAPI на порту 8000 с JWT авторизацией
- **Frontend**: Next.js на порту 3000 с использованием FastAPI auth
- **Auth Flow**: Фронтенд отправляет `POST /api/v1/auth/token` → получает JWT → использует `Authorization: Bearer` для защищённых запросов

## Предварительные условия

- Python 3.10+
- Node.js 18+
- Docker (опционально)

## Быстрый старт

### 1. Подготовка бэкенда

```bash
cd /workspaces/Pharmaviyum-CRM

# Создать виртуальное окружение (если ещё нет)
python -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Установить переменные окружения

Файл `.env` уже создан в корне с параметрами по умолчанию для разработки:
- `API_SECRET_KEY=dev_api_secret_key_32_chars_minimum_for_jwt_signing`
- `ADMIN_USER=admin`
- `ADMIN_PASSWORD=admin123`
- `API_V1_STR=/api/v1`

Для production, обновите:
```bash
API_SECRET_KEY=your_secure_32_char_secret_key
ADMIN_PASSWORD=your_secure_password
```

### 3. Запустить FastAPI

```bash
# Из корневой папки
cd /workspaces/Pharmaviyum-CRM
python -m uvicorn src.pharmaviyum.main:app --reload --port 8000
```

Бэкенд будет доступен на `http://localhost:8000`

Проверить здоровье:
```bash
curl http://localhost:8000/health
# {"status":"healthy"}
```

### 4. Подготовка фронтенда

```bash
cd frontend/shadcn-admin

# Установить зависимости
npm install
```

### 5. Запустить Next.js фронтенд

```bash
# Из папки frontend/shadcn-admin
npm run dev
```

Фронтенд будет доступен на `http://localhost:3000`

## Тестирование авторизации

### 1. Пройти логин в UI

- Откройте `http://localhost:3000`
- Будет перенаправлено на `/sign-in`
- Введите учётные данные:
  - **Email**: `admin` (или любой текст)
  - **Password**: `admin123`
- Нажмите "Sign In"

### 2. Проверить JWT токен через curl

```bash
# Получить токен
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Ответ:
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "token_type": "bearer"}

# Использовать токен для защищённого запроса
TOKEN="<access_token>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users
```

## Структура файлов

```
Pharmaviyum-CRM/
├── .env                          # Переменные окружения (dev defaults)
├── src/
│   └── pharmaviyum/
│       ├── main.py              # FastAPI app entry point
│       ├── config.py            # Settings (API_SECRET_KEY, ADMIN_USER, etc)
│       ├── api/v1/
│       │   ├── auth.py          # POST /auth/token endpoint
│       │   ├── __init__.py       # Router initialization
│       │   └── ...
│       ├── middleware/
│       │   └── auth_middleware.py  # JWT verification middleware
│       └── ...
├── frontend/shadcn-admin/
│   ├── .env                      # Frontend config (API_URL, etc)
│   ├── lib/
│   │   ├── auth.ts              # Auth lib (placeholder, uses auth-context)
│   │   ├── auth-client.ts       # HTTP client for auth API
│   │   └── session.ts           # Server-side session handling
│   ├── contexts/
│   │   └── auth-context.tsx     # React context with login/logout logic
│   ├── proxy.ts                 # Route protection middleware
│   └── ...
└── ...
```

## Flow: Фронтенд → Бэкенд

1. **Sign In Submit** → `contexts/auth-context.tsx`
   - Вызывает `POST /api/v1/auth/token` с username/password

2. **Backend auth.py** обрабатывает:
   - Проверяет username/password против БД или env fallback (admin/admin123)
   - Создаёт JWT токен через `create_access_token()`

3. **Frontend получает JWT**:
   - Сохраняет в `localStorage` (auth_token, auth_user)
   - Сохраняет в `document.cookie` для middleware

4. **Middleware (proxy.ts)** проверяет:
   - Есть ли `auth_token` в cookies
   - Перенаправляет на `/sign-in` если нет

5. **Protected routes** используют токен:
   - Передают `Authorization: Bearer <token>` в заголовке
   - Backend middleware `AuthMiddleware` декодирует JWT

## Типичные ошибки и решения

### 401 Unauthorized при логине

**Проблема**: "Invalid credentials"

**Решение**:
- Проверьте что `ADMIN_PASSWORD=admin123` в `.env`
- Убедитесь что переменная окружения загружена: `echo $API_SECRET_KEY`
- Пересоздайте переменные: `source venv/bin/activate && python -m uvicorn ...`

### Frontend не может соединиться с бэкендом

**Проблема**: "Failed to sign in"

**Решение**:
- Проверьте что бэкенд запущен на 8000: `curl http://localhost:8000/health`
- Убедитесь что `NEXT_PUBLIC_API_V1_URL=http://localhost:8000/api/v1` в `frontend/shadcn-admin/.env`
- Проверьте CORS: бэкенд разрешает `allow_origins=["*"]`

### Middleware перенаправляет на sign-in бесконечно

**Проблема**: Вход в бесконечный цикл перенаправлений

**Решение**:
- Проверьте что токен сохраняется в cookies после логина
- Откройте DevTools → Application → Cookies и проверьте `auth_token`
- Убедитесь что `document.cookie` строка правильно устанавливает cookie

## Переменные окружения

### Backend (`.env`)

```env
# Required for auth
API_SECRET_KEY=dev_api_secret_key_32_chars_minimum_for_jwt_signing
ADMIN_USER=admin
ADMIN_PASSWORD=admin123
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Database (optional)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pharmaviyum

# AI Service
AI_SERVICE_URL=http://localhost:8001
```

### Frontend (`frontend/shadcn-admin/.env`)

```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_V1_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Features
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_ENABLE_DEMO=false
```

## Production Deployment

Для production:

1. **Генерировать надёжный `API_SECRET_KEY`**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Использовать httpOnly cookies** вместо localStorage для JWT

3. **Включить HTTPS** и CSRF protection

4. **Использовать отдельные сертификаты** для каждого сервиса

5. **Настроить логирование и мониторинг**

## Дополнительные ресурсы

- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [Next.js Authentication](https://nextjs.org/docs/app/building-your-application/authentication)

## Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте логи бэкенда: `tail -f logs/app.log`
2. Проверьте консоль фронтенда: DevTools → Console
3. Используйте curl для тестирования API отдельно
