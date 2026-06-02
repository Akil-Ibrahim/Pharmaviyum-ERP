# Установка бесплатной Qwen 3 для разработчиков

В этом проекте локальный агент разработчика может работать с Qwen 3.6/3.7 (GGUF) без использования PyTorch.

## Цель
- Использовать бесплатную локальную модель Qwen 3.x, предпочтительно квантованную GGUF-версию.
- Не менять файлы внутри `mortarium-ai`.
- Установить модель в отдельную папку и подключить её к локальной службе через `MODEL_PATH`.

## Шаг 1: подготовить папку для модели

```bash
mkdir -p ./models/qwen3
```

## Шаг 2: скачать модель

### Вариант A: прямой URL

Если у тебя есть прямая ссылка на файл GGUF, используй скрипт:

```bash
python tools/install_qwen_model.py \
  --source-url "https://example.com/Qwen3-7B-Instruct-Q4_K_M.gguf" \
  --dest ./models/qwen3
```

### Вариант B: Hugging Face репозиторий

Если модель хранится на Hugging Face, используй:

```bash
python tools/install_qwen_model.py \
  --hf-repo "OWNER/MODEL" \
  --filename "Qwen3-7B-Instruct-Q4_K_M.gguf" \
  --dest ./models/qwen3
```

При необходимости добавь токен:

```bash
python tools/install_qwen_model.py \
  --hf-repo "OWNER/MODEL" \
  --filename "Qwen3-7B-Instruct-Q4_K_M.gguf" \
  --hf-token "$HUGGINGFACE_TOKEN" \
  --dest ./models/qwen3
```

## Шаг 3: проверить скачанный файл

```bash
ls -lh ./models/qwen3
```

Ты должен увидеть файл вида:

- `Qwen3-6B-Instruct-Q4_K_M.gguf`
- `Qwen3-7B-Instruct-Q4_K_M.gguf`

## Шаг 4: использовать модель в Mortarium AI без правок папки

### Если запускаешь Docker вручную

Смонтируй папку и передай `MODEL_PATH` через переменную окружения:

```bash
docker run --rm -it -p 8000:8000 \
  -v "$PWD/models/qwen3:/app/models:ro" \
  -e MODEL_PATH=/app/models/Qwen3-7B-Instruct-Q4_K_M.gguf \
  your-mortarium-image:latest
```

### Если запускаешь без Docker

Перед запуском экспортируй переменную:

```bash
export MODEL_PATH="$PWD/models/qwen3/Qwen3-7B-Instruct-Q4_K_M.gguf"
cd mortarium-ai
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

> Важно: это не меняет файлы внутри `mortarium-ai`.

## Шаг 5: тестирование агента

Запусти локальный клиент:

```bash
python tools/qwen_dev_agent.py --question "Объясни кодовую структуру проекта и предложи улучшения"
```

Если модель не доступна или не настроена, клиент автоматически попытается работать через локальную службу, но лучше использовать указанный `MODEL_PATH`.

## Советы

- Легкая версия: ищи Qwen 3.6/3.7 GGUF с квантованием `Q4_K_M` или `Q4_K_S`.
- Не коммить большой бинарный файл в Git.
- Если модель доступна только в PyTorch, её нужно сначала конвертировать в GGUF. Для этой цели PyTorch не нужен в работе с `mortarium-ai`, но потребуется для конвертации.
