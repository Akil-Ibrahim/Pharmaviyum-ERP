# 🧪 Testing Guide - Pharmaviyum AI

Полное руководство по запуску, написанию и отладке тестов в проекте Pharmaviyum AI.

---

## 📋 Быстрый старт

### Вариант 1: Запуск всех тестов

```bash
# Unit-тесты (быстрые, без внешних зависимостей)
./scripts/test.sh unit

# Все тесты
./scripts/test.sh all

# С report coverage
./scripts/test.sh coverage
```

### Вариант 2: Запуск конкретных тестов

```bash
# Конкретный файл
pytest tests/test_api.py -v

# Конкретный тест-класс
pytest tests/test_api.py::TestHealthEndpoints -v

# Конкретный тест
pytest tests/test_api.py::TestHealthEndpoints::test_health_endpoint -v

# С фильтром по маркерам
pytest -m unit -v        # только unit-тесты
pytest -m integration -v # только integration-тесты
```

### Вариант 3: Watch mode (автозапуск при изменении файлов)

```bash
pip install pytest-watch
ptw -- -v
```

---

## 🏗️ Структура тестов

```
tests/
├── conftest.py                 # Pytest fixtures и конфигурация
├── test_api.py                 # API endpoint тесты
├── test_rag.py                 # RAG pipeline тесты
├── test_harness.py             # Agent harness тесты
├── test_evaluation.py          # Agent evaluation тесты
├── test_mcp.py                 # MCP tools тесты
├── test_admin_login.py         # Admin login flow
├── test_mortarium_model.py     # Mortarium AI model тесты
│
├── unit/                       # Unit тесты (помечены @pytest.mark.unit)
│   ├── services/
│   │   ├── test_patient_service.py
│   │   ├── test_cache_service.py
│   │   └── test_pharmacy_service.py
│   └── utils/
│       └── test_validators.py
│
├── integration/                # Integration тесты (помечены @pytest.mark.integration)
│   ├── endpoints/
│   │   ├── test_patients.py
│   │   ├── test_prescriptions.py
│   │   └── test_orders.py
│   └── database/
│       └── test_patient_repository.py
│
└── factories/                  # Test data factories
    ├── __init__.py
    ├── patient.py
    ├── prescription.py
    └── order.py
```

---

## 🎯 Маркеры тестов

Тесты организованы с использованием pytest маркеров:

```bash
# Unit тесты (быстрые, <100ms)
@pytest.mark.unit

# Integration тесты (требуют БД, <5s)
@pytest.mark.integration

# E2E тесты (полный цикл, <30s)
@pytest.mark.e2e

# Slow тесты (требуют сложных вычислений, >5s)
@pytest.mark.slow
```

Запуск по маркерам:

```bash
pytest -m unit         # Только unit-тесты
pytest -m integration  # Только integration-тесты
pytest -m "not slow"   # Всё кроме slow тестов
```

---

## 📊 Coverage Report

Создание и просмотр coverage report:

```bash
# Создать HTML report
./scripts/test.sh coverage

# Открыть в браузере
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**Цели:**
- Minimum: 70% coverage
- Target: 85% coverage
- Excellent: >90% coverage

---

## 🔧 Setup для локального тестирования

### 1. Создать Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### 2. Установить зависимости для тестирования

```bash
# Основные тесты
pip install -r requirements.txt

# Или все зависимости (рекомендуется)
pip install -r requirements-ai.txt
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### 3. Запустить тесты

```bash
./scripts/test.sh all
```

---

## 📝 Написание тестов

### Пример: Unit тест

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
class TestPatientService:
    """Тесты для PatientService"""
    
    def test_create_patient_success(self):
        """Успешное создание пациента"""
        # Arrange
        patient_data = {
            "name": "Ahmed",
            "email": "ahmed@example.com",
            "phone": "+201012345678"
        }
        
        # Act
        result = PatientService.create(patient_data)
        
        # Assert
        assert result.id is not None
        assert result.name == "Ahmed"
        assert result.email == "ahmed@example.com"
    
    def test_create_patient_invalid_email(self):
        """Ошибка при неправильном email"""
        patient_data = {"name": "Ahmed", "email": "invalid"}
        
        with pytest.raises(ValueError):
            PatientService.create(patient_data)
    
    @pytest.mark.parametrize("email,valid", [
        ("user@example.com", True),
        ("user@example.co.uk", True),
        ("invalid.email", False),
        ("user@", False),
    ])
    def test_email_validation(self, email, valid):
        """Параметризованный тест валидации email"""
        result = validate_email(email)
        assert result == valid
```

### Пример: Integration тест с fixtures

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.integration
class TestPatientRepository:
    """Тесты для PatientRepository (требуют БД)"""
    
    @pytest.fixture
    async def patient_repo(self, db_session: AsyncSession):
        """Fixture с инициализованным репозиторием"""
        return PatientRepository(db_session)
    
    async def test_get_patient_by_id(self, patient_repo, sample_patient):
        """Получение пациента по ID"""
        # sample_patient уже в БД (из conftest.py)
        patient = await patient_repo.get(sample_patient.id)
        
        assert patient is not None
        assert patient.name == sample_patient.name
    
    async def test_list_patients_pagination(self, patient_repo):
        """Проверка пагинации"""
        patients = await patient_repo.list(skip=0, limit=10)
        
        assert len(patients) <= 10
        assert all(isinstance(p, Patient) for p in patients)
```

### Пример: Async тест для RAG pipeline

```python
import pytest

@pytest.mark.unit
class TestVectorStore:
    """Тесты для VectorStore"""
    
    @pytest.fixture
    async def vector_store(self):
        """Mock vector store для тестов"""
        return AsyncMagicMock(spec=PgVectorStore)
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, vector_store):
        """Тест similarity search"""
        # Arrange
        query = "drug interaction Warfarin Aspirin"
        expected_results = [
            {"id": "1", "score": 0.95, "text": "..."},
            {"id": "2", "score": 0.87, "text": "..."},
        ]
        vector_store.similarity_search.return_value = expected_results
        
        # Act
        results = await vector_store.similarity_search(query, k=2)
        
        # Assert
        assert len(results) == 2
        assert results[0]["score"] > results[1]["score"]
```

---

## 🐛 Debug тестов

### Запуск с подробным выводом

```bash
# Показать print statements
pytest -v -s tests/test_api.py

# Показать local variables при ошибке
pytest --showlocals tests/test_api.py

# Остановиться на первой ошибке
pytest -x tests/test_api.py

# Открыть debugger при ошибке
pytest --pdb tests/test_api.py
```

### Использование print debug

```python
def test_something():
    result = some_function()
    print(f"Result: {result}")  # Показать с флагом -s
    assert result == expected
```

### Использование pytest.raises

```python
def test_exception_handling():
    with pytest.raises(ValueError, match="Invalid"):
        risky_function()
```

---

## 🚀 CI/CD - Автоматические тесты

Тесты автоматически запускаются в GitHub Actions на каждый push/PR:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements-ai.txt
      - run: pytest --cov=src.pharmaviyum
```

---

## 📈 Текущий статус тестов

### ✅ Готовые тесты (без зависимостей):
- ✅ test_api.py::TestHealthEndpoints (3 тестов)
- ✅ test_api.py::TestAIQueryEndpoint (4 теста)
- ✅ test_api.py::TestIngestionEndpoints (2 теста)
- ✅ test_api.py::TestRequestIDMiddleware (3 теста)

**Итого:** 12 успешных тестов

### ⚠️ Требуют дополнительных зависимостей:
- test_rag.py (25+ тестов) — требуют Ollama/LLM
- test_harness.py (15+ тестов) — требуют model router
- test_evaluation.py (10+ тестов) — требуют golden dataset
- test_admin_login.py — требуют auth setup
- test_mortarium_model.py — требуют mortarium-ai config

### 📊 Установленные пакеты для тестирования:
```
pytest                9.1.1
pytest-asyncio        1.4.0
pytest-cov            7.1.0
pytest-mock           3.15.1
pytest-langsmith      0.12.4
fastapi               0.141.1
sqlalchemy            2.x
pydantic              2.13.5
redis                 8.1.0
langchain             1.4.0
```

---

## 🎯 Best practices для написания тестов

### 1. Используй AAA pattern (Arrange-Act-Assert)

```python
def test_something():
    # Arrange - подготовка данных
    data = {"id": 1, "name": "Test"}
    
    # Act - вызов функции
    result = process(data)
    
    # Assert - проверка результата
    assert result["status"] == "success"
```

### 2. Один тест = один сценарий

```python
# ❌ Плохо - проверяет несколько things
def test_patient_creation():
    patient = create_patient(...)
    assert patient.id is not None
    assert patient.name == "Ahmed"
    assert patient.email == "ahmed@example.com"  # Отдельный тест!

# ✅ Хорошо - каждый тест одного thing
def test_patient_creation_returns_id():
    patient = create_patient(...)
    assert patient.id is not None

def test_patient_creation_sets_name():
    patient = create_patient({"name": "Ahmed"})
    assert patient.name == "Ahmed"
```

### 3. Используй fixtures для setup/teardown

```python
@pytest.fixture
def sample_patient():
    """Создать тестовых пациента перед тестом"""
    patient = Patient(name="Test", email="test@example.com")
    patient.save()
    yield patient  # Тест запускается здесь
    patient.delete()  # Cleanup после теста

def test_something(sample_patient):
    """Fixture автоматически вводится в параметры"""
    assert sample_patient.name == "Test"
```

### 4. Мокируй внешние зависимости

```python
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_api_call():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        result = external_api_call()
        
        assert result == {"status": "ok"}
        mock_get.assert_called_once()
```

### 5. Используй parametrize для multiple scenarios

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_double(input, expected):
    assert double(input) == expected
```

---

## 📚 Дополнительные ресурсы

- [Pytest документация](https://docs.pytest.org/)
- [Pytest fixtures](https://docs.pytest.org/en/latest/fixture.html)
- [Testing asyncio code](https://docs.pytest.org/en/latest/async.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)

---

## 🆘 Troubleshooting

### Ошибка: "ModuleNotFoundError"
```bash
# Решение: Убедиться что в virtual environment
source venv/bin/activate
pip install -r requirements-ai.txt
```

### Ошибка: "Cannot connect to database"
```bash
# Решение: Запустить PostgreSQL
docker-compose -f docker-compose.codespaces.yml up -d postgres
```

### Ошибка: "Timeout during test"
```bash
# Решение: Увеличить timeout
pytest --timeout=300 tests/test_slow.py
```

### Ошибка: "Port already in use"
```bash
# Решение: Убить process на порту
lsof -i :8000
kill -9 <PID>
```

---

**✅ Готово к тестированию! Запустите `./scripts/test.sh unit` чтобы начать.**
