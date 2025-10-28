***

# 🏗️ АРХИТЕКТУРА ПРИЛОЖЕНИЯ "JSON Scenario generator"

## 📋 ROADMAP РАЗРАБОТКИ (ПОЭТАПНЫЙ ПЛАН)

### **ФАЗА 0: Подготовка окружения (1-2 часа)**

- [x] Установка Python 3.14 ✅
- [x] Установка PyCharm ✅
- [x] **TASK 0.1**: Настройка виртуального окружения
- [x] **TASK 0.2**: Установка базовых зависимостей
- [x] **TASK 0.3**: Создание структуры проекта
- [x] **TASK 0.4**: Настройка `.gitignore` и Git


### **ФАЗА 1: Базовая инфраструктура (2-3 дня)**

- [x] **TASK 1.1**: Создание модуля конфигурации (`config/`)
- [x] **TASK 1.2**: Создание модуля логирования (`utils/logger.py`)
- [x] **TASK 1.3**: Создание базовых моделей данных (`models/`)
- [x] **TASK 1.4**: Настройка юнит-тестов (`tests/`)


### **ФАЗА 2: Парсеры и загрузчики (3-5 дней)**

- [x] **TASK 2.1**: Парсер JSON Schema (`parsers/schema_parser.py`)
- [x] **TASK 2.2**: Загрузчик справочников (`loaders/dictionary_loader.py`)
- [ ] **TASK 2.3**: Загрузчик сводки по релизам (`loaders/releases_loader.py`) (Пока что пропускаем)
- [x] **TASK 2.4**: Парсер маппинга Excel (опционально, для будущего)


### **ФАЗА 3: Ядро системы — Сравнение и актуализация (5-7 дней)**

- [ ] **TASK 3.1**: Компаратор схем (`core/schema_comparator.py`)
- [ ] **TASK 3.2**: Генератор значений (`core/value_generator.py`)
- [ ] **TASK 3.3**: Актуализатор JSON (`core/json_actualizer.py`)
- [ ] **TASK 3.4**: Валидатор JSON (`core/json_validator.py`)


### **ФАЗА 4: Отчеты и экспорт (2-3 дня)**

- [ ] **TASK 4.1**: Генератор отчетов Markdown (`reports/report_generator.py`)
- [ ] **TASK 4.2**: Подсветка изменений в JSON (`reports/diff_highlighter.py`)
- [ ] **TASK 4.3**: Экспорт в различные форматы


### **ФАЗА 5: CLI интерфейс (2-3 дня)**

- [ ] **TASK 5.1**: Создание CLI (`cli/main.py`)
- [ ] **TASK 5.2**: Команды для сравнения версий
- [ ] **TASK 5.3**: Команды для актуализации JSON


### **ФАЗА 6: Web UI (опционально, 1-2 недели)**

- [ ] **TASK 6.1**: Flask/FastAPI backend (`web/backend/`)
- [ ] **TASK 6.2**: React/Vue frontend (`web/frontend/`)
- [ ] **TASK 6.3**: API endpoints


### **ФАЗА 7: Интеграция и тестирование (3-5 дней)**

- [ ] **TASK 7.1**: Интеграционные тесты
- [ ] **TASK 7.2**: E2E тесты
- [ ] **TASK 7.3**: Документация

***

## 🗂️ СТРУКТУРА ПРОЕКТА

```
json-scenario-generator/
│
├── config/                          # Конфигурация приложения
│   ├── __init__.py
│   ├── settings.py                  # Настройки (пути, константы)
│   └── logging_config.py            # Конфигурация логирования
│
├── data/                            # Данные приложения (не входят в Git)
│   ├── schemas/                     # JSON Schema (V70Call1Rq.json, V72Call1Rq.json...)
│   ├── dictionaries/                # Справочники (справочники.xlsx)
│   ├── releases/                    # Сводки по релизам
│   ├── mappings/                    # Маппинги Excel (опционально)
│   └── scenarios/                   # Существующие JSON-сценарии из Postman
│
├── src/                             # Исходный код приложения
│   ├── __init__.py
│   │
│   ├── models/                      # Модели данных (dataclasses)
│   │   ├── __init__.py
│   │   ├── schema_models.py         # VersionInfo, FieldMetadata, SchemaDiff
│   │   ├── dictionary_models.py     # DictionaryEntry, Dictionary
│   │   └── scenario_models.py       # Scenario, ScenarioStep
│   │
│   ├── parsers/                     # Парсеры различных форматов
│   │   ├── __init__.py
│   │   ├── schema_parser.py         # Парсинг JSON Schema
│   │   ├── mapping_parser.py        # Парсинг маппинга из Excel (будущее)
│   │   └── condition_parser.py      # Парсинг условий УО (SpEL)
│   │
│   ├── loaders/                     # Загрузчики данных
│   │   ├── __init__.py
│   │   ├── schema_loader.py         # Загрузка JSON Schema
│   │   ├── dictionary_loader.py     # Загрузка справочников
│   │   ├── releases_loader.py       # Загрузка сводки по релизам
│   │   └── scenario_loader.py       # Загрузка существующих JSON
│   │
│   ├── core/                        # Ядро приложения (бизнес-логика)
│   │   ├── __init__.py
│   │   ├── schema_comparator.py     # Сравнение схем (Diff)
│   │   ├── value_generator.py       # Генерация значений для полей
│   │   ├── json_actualizer.py       # Актуализация JSON
│   │   ├── json_validator.py        # Валидация JSON по схеме
│   │   └── path_utils.py            # Утилиты для работы с путями JSON
│   │
│   ├── reports/                     # Генерация отчетов
│   │   ├── __init__.py
│   │   ├── report_generator.py      # Генерация Markdown отчетов
│   │   ├── diff_highlighter.py      # Подсветка изменений в JSON
│   │   └── export_utils.py          # Экспорт в различные форматы
│   │
│   ├── utils/                       # Вспомогательные утилиты
│   │   ├── __init__.py
│   │   ├── logger.py                # Логирование
│   │   ├── file_utils.py            # Работа с файлами
│   │   └── json_utils.py            # Утилиты для работы с JSON
│   │
│   └── cli/                         # CLI интерфейс
│       ├── __init__.py
│       ├── main.py                  # Главный CLI файл
│       ├── commands/                # Команды CLI
│       │   ├── __init__.py
│       │   ├── compare.py           # Команда сравнения версий
│       │   ├── actualize.py         # Команда актуализации JSON
│       │   └── validate.py          # Команда валидации
│       └── ui/                      # UI для CLI (Rich library)
│           ├── __init__.py
│           └── progress.py
│
├── tests/                           # Юнит-тесты и интеграционные тесты
│   ├── __init__.py
│   ├── unit/                        # Юнит-тесты
│   │   ├── test_schema_parser.py
│   │   ├── test_schema_comparator.py
│   │   ├── test_value_generator.py
│   │   └── test_json_actualizer.py
│   ├── integration/                 # Интеграционные тесты
│   │   ├── test_full_pipeline.py
│   │   └── test_cli.py
│   └── fixtures/                    # Тестовые данные
│       ├── schemas/
│       ├── dictionaries/
│       └── scenarios/
│
├── docs/                            # Документация
│   ├── architecture.md              # Описание архитектуры
│   ├── user_guide.md                # Руководство пользователя
│   └── api_reference.md             # API Reference
│
├── web/                             # Web UI (опционально, для будущего)
│   ├── backend/                     # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routers/
│   │   └── schemas/
│   └── frontend/                    # React/Vue frontend
│       ├── src/
│       ├── public/
│       └── package.json
│
├── scripts/                         # Вспомогательные скрипты
│   ├── setup_data.py                # Скрипт для первоначальной настройки данных
│   └── run_tests.sh                 # Скрипт запуска тестов
│
├── .gitignore                       # Git ignore файл
├── .env.example                     # Пример файла окружения
├── requirements.txt                 # Зависимости Python
├── requirements-dev.txt             # Зависимости для разработки
├── setup.py                         # Установка пакета
├── pytest.ini                       # Конфигурация pytest
├── README.md                        # Описание проекта
└── main.py                          # Точка входа в приложение
```


***

## 🛠️ ДЕТАЛЬНЫЙ ПЛАН ПО ЗАДАЧАМ

### **ФАЗА 0: Подготовка окружения**

#### **TASK 0.1: Настройка виртуального окружения**

**Что делать:**

1. Открой PyCharm
2. Создай новый проект: `File` → `New Project`
3. Назови проект: `json-scenario-actualizer`
4. Выбери Python 3.12 как интерпретатор
5. Включи создание виртуального окружения (`venv`)

**Команды в терминале PyCharm:**

```bash
# Создание venv (если не создано автоматически)
python -m venv venv

# Активация venv (Windows)
venv\Scripts\activate

# Активация venv (Linux/Mac)
source venv/bin/activate

# Проверка версии Python
python --version  # Должно быть 3.12
```


***

#### **TASK 0.2: Установка базовых зависимостей**

**Создай файл `requirements.txt`:**

```txt
# Core dependencies
openpyxl==3.1.2              # Для работы с Excel
pandas==2.2.0                # Для работы с данными
jsonschema==4.20.0           # Для валидации JSON Schema
Faker==22.0.0                # Для генерации тестовых данных

# CLI
click==8.1.7                 # Для создания CLI
rich==13.7.0                 # Для красивого CLI UI

# Utils
python-dotenv==1.0.0         # Для работы с .env файлами
pyyaml==6.0.1                # Для работы с YAML

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code quality
black==23.12.1               # Форматирование кода
flake8==7.0.0                # Линтер
mypy==1.8.0                  # Проверка типов

# Logging
loguru==0.7.2                # Удобное логирование
```

**Создай файл `requirements-dev.txt` (для разработки):**

```txt
-r requirements.txt

# Development tools
ipython==8.19.0              # Интерактивная консоль
jupyter==1.0.0               # Jupyter notebook (для экспериментов)

# Web (опционально, для будущего)
# fastapi==0.109.0
# uvicorn==0.25.0
# pydantic==2.5.3
```

**Установи зависимости:**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```


***

#### **TASK 0.3: Создание структуры проекта**

**Создай скрипт `scripts/setup_project.py`:**

```python
"""
Скрипт для автоматического создания структуры проекта
"""
import os
from pathlib import Path

def create_directory_structure():
    """Создает структуру директорий проекта"""
    
    directories = [
        # Data
        "data/schemas",
        "data/dictionaries",
        "data/releases",
        "data/mappings",
        "data/scenarios",
        
        # Source code
        "src/models",
        "src/parsers",
        "src/loaders",
        "src/core",
        "src/reports",
        "src/utils",
        "src/cli/commands",
        "src/cli/ui",
        
        # Tests
        "tests/unit",
        "tests/integration",
        "tests/fixtures/schemas",
        "tests/fixtures/dictionaries",
        "tests/fixtures/scenarios",
        
        # Config
        "config",
        
        # Docs
        "docs",
        
        # Scripts
        "scripts",
        
        # Web (опционально)
        "web/backend/routers",
        "web/backend/schemas",
        "web/frontend/src",
        "web/frontend/public",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Создаем __init__.py для Python пакетов
        if directory.startswith("src/") or directory.startswith("tests/"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Структура проекта создана успешно!")

if __name__ == "__main__":
    create_directory_structure()
```

**Запусти скрипт:**

```bash
python scripts/setup_project.py
```


***

#### **TASK 0.4: Настройка `.gitignore` и Git**

**Создай файл `.gitignore`:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# PyCharm
.idea/
*.iml

# Data (не коммитим данные)
data/
!data/.gitkeep

# Logs
*.log
logs/

# Environment variables
.env

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/

# Coverage
.coverage
htmlcov/

# Pytest
.pytest_cache/

# MyPy
.mypy_cache/

# Distribution
dist/
build/
*.egg-info/
```

**Инициализируй Git:**

```bash
git init
git add .
git commit -m "Initial commit: project structure"
```


***

### **ФАЗА 1: Базовая инфраструктура**

#### **TASK 1.1: Создание модуля конфигурации**

**Создай файл `config/settings.py`:**

```python
"""
Настройки приложения
"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).parent.parent

@dataclass
class AppConfig:
    """Конфигурация приложения"""
    
    # Пути к данным
    DATA_DIR: Path = BASE_DIR / "data"
    SCHEMAS_DIR: Path = DATA_DIR / "schemas"
    DICTIONARIES_DIR: Path = DATA_DIR / "dictionaries"
    RELEASES_DIR: Path = DATA_DIR / "releases"
    MAPPINGS_DIR: Path = DATA_DIR / "mappings"
    SCENARIOS_DIR: Path = DATA_DIR / "scenarios"
    
    # Пути к выходным данным
    OUTPUT_DIR: Path = BASE_DIR / "output"
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"
    UPDATED_SCENARIOS_DIR: Path = OUTPUT_DIR / "scenarios"
    
    # Логирование
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "app.log"
    
    # Настройки приложения
    APP_NAME: str = "JSON Scenario Actualizer"
    APP_VERSION: str = "0.1.0"
    
    # Настройки генерации
    DEFAULT_LOCALE: str = "ru_RU"  # Для Faker
    DEFAULT_ARRAY_SIZE: int = 1    # Количество элементов в массивах по умолчанию
    
    def __post_init__(self):
        """Создает директории, если их нет"""
        for path in [
            self.DATA_DIR,
            self.SCHEMAS_DIR,
            self.DICTIONARIES_DIR,
            self.RELEASES_DIR,
            self.MAPPINGS_DIR,
            self.SCENARIOS_DIR,
            self.OUTPUT_DIR,
            self.REPORTS_DIR,
            self.UPDATED_SCENARIOS_DIR,
            self.LOG_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)

# Глобальный экземпляр конфигурации
config = AppConfig()
```

**Создай файл `.env.example`:**

```env
# Environment variables example

# Logging
LOG_LEVEL=INFO

# Application
APP_NAME=JSON Scenario Actualizer
APP_VERSION=0.1.0

# Paths (опционально, если хочешь переопределить)
# DATA_DIR=/custom/path/to/data
```


***

#### **TASK 1.2: Создание модуля логирования**

**Создай файл `src/utils/logger.py`:**

```python
"""
Модуль логирования с использованием loguru
"""
from loguru import logger
import sys
from pathlib import Path
from config.settings import config

def setup_logger():
    """
    Настройка логгера
    """
    # Удаляем стандартный handler
    logger.remove()
    
    # Добавляем handler для консоли
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True,
    )
    
    # Добавляем handler для файла
    log_file_path = config.LOG_DIR / config.LOG_FILE
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation="10 MB",  # Ротация при достижении 10 MB
        retention="30 days",  # Хранить логи 30 дней
        compression="zip",  # Сжимать старые логи
    )
    
    logger.info(f"✅ Логгер настроен. Логи сохраняются в: {log_file_path}")
    
    return logger

# Инициализация логгера
log = setup_logger()
```


***

#### **TASK 1.3: Создание базовых моделей данных**

**Создай файл `src/models/schema_models.py`:**

```python
"""
Модели данных для работы со схемами
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class VersionStatus(Enum):
    """Статус версии"""
    CURRENT = "Актуально"
    FUTURE = "Будущий релиз"
    DEPRECATING = "Выводится из эксплуатации"
    DEPRECATED = "Выведено из эксплуатации"

@dataclass
class VersionInfo:
    """Информация о версии контракта"""
    version: str                            # "072"
    subversion: Optional[str] = None        # "04" или None
    release_month: Optional[str] = None     # "Октябрь 2025"
    status: VersionStatus = VersionStatus.CURRENT
    direction: Optional[str] = None         # "КН, КК"
    inclusion_date: Optional[str] = None    # "25.10.2025"
    comment: str = ""
    
    def full_version(self) -> str:
        """Возвращает полную версию"""
        if self.subversion:
            return f"{self.version}.{self.subversion}"
        return self.version
    
    def is_current(self) -> bool:
        """Проверка, актуальна ли версия"""
        return self.status == VersionStatus.CURRENT
    
    def is_future(self) -> bool:
        """Проверка, будущий ли релиз"""
        return self.status == VersionStatus.FUTURE
    
    def is_deprecated(self) -> bool:
        """Проверка, выводится ли из эксплуатации"""
        return self.status in [VersionStatus.DEPRECATING, VersionStatus.DEPRECATED]

@dataclass
class FieldMetadata:
    """Метаданные поля из JSON Schema"""
    path: str                               # "customerRequest/creditParameters/productCdExt"
    name: str                               # "productCdExt"
    field_type: str                         # "integer", "string", "object", "array"
    is_required: bool = False
    is_conditional: bool = False            # Условно обязательное (УО)
    condition: Optional[Dict[str, Any]] = None
    dictionary: Optional[str] = None        # "PRODUCT_TYPE"
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    properties: Optional[Dict[str, 'FieldMetadata']] = None  # Для объектов
    items: Optional['FieldMetadata'] = None  # Для массивов

@dataclass
class FieldChange:
    """Изменение поля между версиями"""
    path: str
    change_type: str                        # "added", "removed", "modified"
    old_meta: Optional[FieldMetadata] = None
    new_meta: Optional[FieldMetadata] = None
    changes: Dict[str, str] = field(default_factory=dict)

@dataclass
class SchemaDiff:
    """Разница между двумя схемами"""
    old_version: str
    new_version: str
    added_fields: List[FieldChange] = field(default_factory=list)
    removed_fields: List[FieldChange] = field(default_factory=list)
    modified_fields: List[FieldChange] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def total_changes(self) -> int:
        """Общее количество изменений"""
        return len(self.added_fields) + len(self.removed_fields) + len(self.modified_fields)
    
    def has_breaking_changes(self) -> bool:
        """Проверка наличия критичных изменений"""
        # Критичные изменения: удаление обязательных полей, изменение типов
        return any(
            change.old_meta and change.old_meta.is_required 
            for change in self.removed_fields
        ) or any(
            "type" in change.changes 
            for change in self.modified_fields
        )
```

**Создай файл `src/models/dictionary_models.py`:**

```python
"""
Модели данных для справочников
"""
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DictionaryEntry:
    """Запись справочника"""
    code: int                   # Код РКК (например, 10410001)
    name: str                   # Наименование значения (например, "PACL")
    dictionary_type: str        # Тип справочника (например, "PRODUCT_TYPE")
    description: str = ""

@dataclass
class Dictionary:
    """Справочник"""
    name: str                   # Название справочника (PRODUCT_TYPE, SALE_CHANNEL...)
    entries: List[DictionaryEntry]
    
    def get_by_code(self, code: int) -> DictionaryEntry:
        """Получить запись по коду"""
        for entry in self.entries:
            if entry.code == code:
                return entry
        raise ValueError(f"Код {code} не найден в справочнике {self.name}")
    
    def get_random(self) -> DictionaryEntry:
        """Получить случайную запись"""
        import random
        return random.choice(self.entries)
```


***

#### **TASK 1.4: Настройка юнит-тестов**

**Создай файл `pytest.ini`:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

**Создай файл `tests/conftest.py` (фикстуры для тестов):**

```python
"""
Конфигурация pytest и общие фикстуры
"""
import pytest
from pathlib import Path
import json

@pytest.fixture
def sample_schema_v70():
    """Пример JSON Schema версии 070"""
    return {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
        "version": "070",
        "type": "object",
        "properties": {
            "loanRequest": {
                "type": "object",
                "properties": {
                    "loanRequestExtId": {
                        "type": "string",
                        "maxLength": 50
                    },
                    "creditAmt": {
                        "type": "integer",
                        "maxIntLength": 10
                    }
                },
                "required": ["loanRequestExtId"]
            }
        },
        "required": ["loanRequest"]
    }

@pytest.fixture
def sample_schema_v72():
    """Пример JSON Schema версии 072"""
    return {
        "$schema": "https://json-schema.org/draft/2019-09/schema",
        "version": "072",
        "type": "object",
        "properties": {
            "loanRequest": {
                "type": "object",
                "properties": {
                    "loanRequestExtId": {
                        "type": "string",
                        "maxLength": 50
                    },
                    "creditAmt": {
                        "type": "integer",
                        "maxIntLength": 10
                    },
                    "newField": {
                        "type": "string",
                        "maxLength": 100
                    }
                },
                "required": ["loanRequestExtId", "newField"]
            }
        },
        "required": ["loanRequest"]
    }

@pytest.fixture
def sample_json_v70():
    """Пример JSON для версии 070"""
    return {
        "loanRequest": {
            "loanRequestExtId": "550e8400-e29b-41d4-a716-446655440000",
            "creditAmt": 100000
        }
    }
```

**Создай первый тест `tests/unit/test_models.py`:**

```python
"""
Тесты для моделей данных
"""
import pytest
from src.models.schema_models import VersionInfo, VersionStatus

def test_version_info_full_version():
    """Тест метода full_version()"""
    version_with_sub = VersionInfo(version="072", subversion="04")
    assert version_with_sub.full_version() == "072.04"
    
    version_without_sub = VersionInfo(version="072")
    assert version_without_sub.full_version() == "072"

def test_version_info_status_checks():
    """Тест проверок статуса версии"""
    current_version = VersionInfo(version="072", status=VersionStatus.CURRENT)
    assert current_version.is_current() is True
    assert current_version.is_future() is False
    assert current_version.is_deprecated() is False
    
    future_version = VersionInfo(version="073", status=VersionStatus.FUTURE)
    assert future_version.is_current() is False
    assert future_version.is_future() is True
```
