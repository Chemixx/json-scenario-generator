# Руководство разработчика json-scenario-generator

Этот документ отвечает на вопросы:
- "Как быстро поднять проект?"
- "Как запускать тесты?"
- "Как правильно добавлять новый функционал, чтобы не сломать архитектуру?"
- "Что сейчас сломано и как это чинить?"

---

## Быстрый старт

### 1. Клонирование и окружение

```bash
git clone https://github.com/Chemixx/json-scenario-generator.git
cd json-scenario-generator

python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

> **Важно:** В `requirements.txt` указан `pandas==2.2.0`. Если `pip install` не установил его (например, проблемы с версией Python), установите вручную:
> ```bash
> pip install pandas
> ```

### 3. Первичная настройка

```bash
python scripts/setup_project.py
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/Mac
```

### 4. Запуск тестов

```bash
pytest
```

**Состояние (май 2026):**

| Метрика | Значение | Статус |
|---------|----------|--------|
| Собирается pytest | 484 | ✅ |
| Проходит тестов | 484 | ✅ |
| Import errors | 0 | ✅ |

---

## Структура проекта (актуальная)

См. также раздел "СТРУКТУРА ПРОЕКТА" в README.md.

### Полная структура (май 2026)

```
json-scenario-generator/
├── config/                     # Конфигурация
│   ├── __init__.py
│   └── settings.py             # Настройки путей, логирования
│
├── src/                        # Исходный код
│   ├── __init__.py
│   ├── models/                 # ✅ Доменные модели и enums
│   │   ├── __init__.py
│   │   ├── change_models.py    # AnalyzedChange, AnalysisResult
│   │   ├── dictionary_models.py # Dictionary, DictionaryEntry
│   │   ├── enums.py            # ChangeType, BreakingLevel, ImpactLevel
│   │   ├── scenario_models.py  # Scenario, ScenarioMetadata
│   │   └── schema_models.py    # FieldMetadata, SchemaDiff, VersionInfo
│   │
│   ├── parsers/                # ✅ Парсинг JSON Schema и SpEL
│   │   ├── __init__.py
│   │   └── schema_parser.py    # SchemaParser
│   │
│   ├── loaders/                # ✅ Загрузка справочников
│   │   ├── __init__.py
│   │   ├── dictionary_loader.py # DictionaryLoader (Excel)
│   │   ├── json_dictionary_loader.py # JsonDictionaryLoader (JSON)
│   │   └── dictionary_registry.py  # DictionaryRegistry (центральное хранилище)
│   │
│   ├── core/                   # ✅ Ядро — реализовано
│   │   ├── __init__.py
│   │   ├── schema_comparator.py # ✅ SchemaComparator
│   │   ├── spel_ast.py          # ✅ SpEL AST узлы
│   │   ├── spel_parser.py       # ✅ SpelParser
│   │   ├── spel_functions.py    # ✅ SpelFunctions (34/34 функции)
│   │   ├── condition_evaluator.py  # ✅ ConditionEvaluator
│   │   ├── conditional_validator.py # ✅ ConditionalValidator
│   │   ├── value_generator.py   # ✅ ValueGenerator
│   │   └── json_actualizer.py   # ✅ JsonActualizer
│   │
│   ├── analyzers/              # ✅ Анализ изменений
│   │   ├── __init__.py
│   │   └── change_analyzer.py   # ChangeAnalyzer (3-уровневая классификация)
│   │
│   ├── formatters/             # ✅ Форматирование отчётов
│   │   ├── __init__.py
│   │   └── report_formatter.py  # text/markdown/json
│   │
│   ├── utils/                  # ✅ Утилиты
│   │   ├── __init__.py
│   │   ├── excel_utils.py       # ⚠️ Зависит от pandas
│   │   ├── json_utils.py
│   │   └── logger.py
│   │
│   ├── cli/                    # 🔴 ПУСТАЯ директория (только __init__.py)
│   │   ├── commands/__init__.py
│   │   └── ui/__init__.py
│   │
│   ├── reports/                # 🔴 ПУСТАЯ директория (только __init__.py)
│   │   └── __init__.py
│   │
│   └── deprecated/             # ⚠️ Устаревший код
│       └── spel_v0_2_0_evaluator/  # Старая версия SpEL evaluator
│           ├── README.md
│           ├── spel_context.py
│           ├── spel_evaluator.py
│           ├── spel_protocols.py
│           └── spel_transpiler.py
│
├── tests/                      # Тесты
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/               # Тестовые данные
│   │   ├── dictionaries/
│   │   ├── scenarios/
│   │   └── schemas/
│   ├── integration/            # 🔴 ПУСТАЯ (только __init__.py)
│   │   └── __init__.py
│   └── unit/                   # ✅ Unit-тесты
│       ├── core/
│       │   ├── __init__.py
│       │   ├── test_spel_parser.py
│       │   ├── test_condition_evaluator.py
│       │   ├── test_conditional_validator.py
│       │   ├── test_value_generator.py
│       │   └── test_json_actualizer.py
│       ├── test_change_analyzer.py
│       ├── test_config.py
│       ├── test_dictionary_loader.py
│       ├── test_dictionary_models.py
│       ├── test_logger.py
│       ├── test_report_formatter.py
│       ├── test_scenario_models.py
│       ├── test_schema_comparator.py
│       ├── test_schema_models.py
│       └── test_schema_parser.py
│
├── scripts/                    # CLI-скрипты
│   ├── analyze_changes.py      # ✅ Готов: анализ изменений между схемами
│   └── setup_project.py        # ✅ Готов: первичная настройка
│
├── docs/                       # Документация
│   ├── PRD.md                  # Требования к продукту
│   ├── ARCHITECTURE.md         # Архитектура системы
│   ├── DEVELOPMENT.md          # ← Этот файл
│   └── SPECIFICATION.md        # Полная спецификация (2700+ строк)
│
├── data/                       # Входные данные (НЕ в Git)
│   ├── schemas/                # JSON Schema
│   ├── dictionaries/           # Excel-справочники
│   └── scenarios/              # JSON-сценарии
│
├── output/                     # Выходные файлы (отчёты)
├── logs/                       # Файлы логов
├── confest.py                  # pytest конфигурация (PYTHONPATH)
├── requirements.txt            # Зависимости
├── requirements-dev.txt        # Dev-зависимости
├── .env.example                # Пример окружения
└── .gitignore
```

### Статус директорий

| Директория | Статус | Примечание |
|------------|--------|------------|
| `src/models/` | ✅ Готово | 5 файлов, все модели покрыты тестами |
| `src/parsers/` | ✅ Готово | SchemaParser работает |
| `src/loaders/` | ✅ Готово | DictionaryLoader + JsonDictionaryLoader + DictionaryRegistry |
| `src/core/` | ✅ Готово | 9 модулей: SchemaComparator, SpelParser, SpelFunctions (34/34), ConditionEvaluator, ConditionalValidator, ValueGenerator, JsonActualizer, JsonValidator |
| `src/analyzers/` | ✅ Готово | ChangeAnalyzer с 3-уровневой классификацией |
| `src/formatters/` | ✅ Готово | 3 формата: text/markdown/json |
| `src/utils/` | ✅ Готово | ⚠️ `excel_utils.py` зависит от pandas |
| `src/cli/` | 🔴 **ПУСТАЯ** | Только `__init__.py` — CLI не реализован |
| `src/reports/` | 🔴 **ПУСТАЯ** | Только `__init__.py` — генератор отчётов не реализован |
| `src/deprecated/` | ⚠️ **DEPRECATED** | Старый SpEL evaluator v0.2.0 — НЕ использовать |
| `tests/integration/` | 🔴 **ПУСТАЯ** | Integration-тесты ещё не написаны |

---

## Тестирование

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием

```bash
pytest --cov=src --cov-report=term-missing
```

### Запуск только unit-тестов

```bash
pytest tests/unit/ -v
```

### Запуск конкретного тестового файла/теста

```bash
pytest tests/unit/test_change_analyzer.py -v
pytest tests/unit/test_change_analyzer.py::test_analyze_modification_type_change -v
```

### Если тесты падают с ImportError

**Симптом:**
```
ModuleNotFoundError: No module named 'pandas'
```

**Причина:** `src/utils/excel_utils.py` импортирует `pandas`, и этот импорт распространяется через `__init__.py` на весь проект.

**Решение:**
```bash
pip install pandas
```

### Структура тестов (что уже покрыто)

| Модуль | Тесты | Покрытие |
|--------|-------|----------|
| Модели (schema_models, scenario_models, dictionary_models, change_models, enums) | ~50 | ✅ |
| Logger | 9 | ✅ |
| Config | 5 | ✅ |
| ReportFormatter | 14 | ✅ |
| SchemaParser | ~30 | ✅ |
| SchemaComparator | ~25 | ✅ |
| ChangeAnalyzer | ~69 | ✅ |
| DictionaryLoader | ~15 | ✅ |
| SpelParser | ~20 | ✅ |
| ConditionEvaluator | ~39 | ✅ |
| ConditionalValidator | ~20 | ✅ |
| ValueGenerator | ~30 | ✅ |
| JsonActualizer | 104 | ✅ 100% |
| JsonValidator | 59 | ✅ |
| constraint_utils | 26 | ✅ |

**Требование:** новые фичи должны сопровождаться unit-тестами, которые покрывают основные и крайние случаи.

---

## Как добавлять новый функционал

Ниже — шаблоны для типовых задач с учётом архитектуры и SOLID.

### Пример 1: Добавить новый формат отчёта (HTML) в ReportFormatter

1. Открыть `src/formatters/report_formatter.py`.
2. Добавить новый метод:

```python
def format_html(self, result: AnalysisResult) -> str:
    """Форматирование результата анализа в HTML."""
    # Сформировать HTML-документ на основе result
    return html_string
```

3. Добавить тест в `tests/unit/test_report_formatter.py`:

```python
def test_format_html_basic(sample_analysis_result):
    formatter = ReportFormatter()
    html = formatter.format_html(sample_analysis_result)
    assert "<html" in html
    assert "</html>" in html
```

4. (Опционально) добавить поддержку нового формата в CLI/скрипты.

**Важно:** ни ChangeAnalyzer, ни SchemaComparator при этом не меняются.

---

### Пример 2: Добавить новое правило классификации изменений

1. Открыть `src/analyzers/change_analyzer.py`.
2. Найти соответствующий метод (`_analyze_addition`, `_analyze_removal`, `_analyze_modification`).
3. Добавить новое условие, опираясь на модели `FieldChange` и enums.
4. Добавить тест в `tests/unit/test_change_analyzer.py` с понятным примером.

**Важно:** не добавлять прямой вывод/логирование в ChangeAnalyzer; для этого есть ReportFormatter и logger.

---

### Добавление нового SpEL-оператора

Все 34 базовых SpEL-оператора уже реализованы. Если нужно добавить новый оператор, порядок действий:

1. Добавить `NodeType` и AST-узел в `src/core/spel_ast.py`
2. Добавить парсинг в `src/core/spel_parser.py`
3. Добавить функцию в `src/core/spel_functions.py`
4. Написать тесты

См. реализацию существующих операторов: `src/core/spel_parser.py`, `src/core/spel_ast.py`, `src/core/spel_functions.py`.

---

### Реализованные модули ядра

Следующие модули были реализованы на этапах 4-7 (апрель-май 2026):

| Модуль | Файл | Описание |
|--------|------|----------|
| ConditionEvaluator | `src/core/condition_evaluator.py` | Выполнение SpEL-выражений на JSON-данных |
| ConditionalValidator | `src/core/conditional_validator.py` | Проверка УО-полей: условие выполнено -- поле не null |
| ValueGenerator | `src/core/value_generator.py` | Генерация валидных значений для новых полей |
| JsonActualizer | `src/core/json_actualizer.py` | Применение SchemaDiff к JSON-сценарию |

---

## Качество кода

Рекомендуемые инструменты:

### Форматирование (black)

```bash
black src/ tests/
```

### Линтер (flake8)

```bash
flake8 src/ tests/
```

### Типы (mypy)

```bash
mypy src/
```

**Принципы:**
- **Type hints обязательны** для всех публичных функций и методов.
- **Dataclasses** предпочтительнее "магических" dict для сущностей.
- **Не дублировать** бизнес-логику в разных слоях.
- **Docstrings** обязательны для публичных API.

---

## Git Workflow и коммиты

### Ветвление

- Основная ветка: `main`.
- Для новых фич: `feature/<short-name>`.
- Для исправлений багов: `fix/<short-name>`.

```bash
git checkout -b feature/add-condition-evaluator
git checkout -b fix/spel-parser-regex-bug
```

### Сообщения коммитов (Conventional Commits)

Формат: `тип(область): краткое описание`.

Основные типы:
| Тип | Описание | Пример |
|-----|----------|--------|
| `feat:` | Новая функциональность | `feat(core): implement ConditionEvaluator` |
| `fix:` | Исправление бага | `fix(parsers): fix SpEL regex token parsing` |
| `docs:` | Документация | `docs: update DEVELOPMENT.md with Stage 3 examples` |
| `test:` | Тесты | `test(core): add ConditionEvaluator unit tests` |
| `refactor:` | Рефакторинг без изменения поведения | `refactor(core): extract SpEL evaluation into separate module` |
| `chore:` | Инфраструктура, конфиг, зависимости | `chore: add pandas to requirements.txt` |

**Примеры:**

```bash
git commit -m "feat(core): implement ConditionEvaluator for SpEL execution"
git commit -m "test(core): cover ConditionEvaluator with 15 unit tests"
git commit -m "docs: add SpEL operator examples to DEVELOPMENT.md"
git commit -m "fix(parsers): handle empty SpEL expression gracefully"
```

---

### Работа со справочниками (DictionaryLoader v2)

#### DictionaryRegistry — центральное хранилище

```python
from src.loaders.dictionary_registry import DictionaryRegistry

# Создание реестра
registry = DictionaryRegistry()

# Загрузка из JSON (продуктивный формат 1905.64/1905.65)
registry.load_from_json(Path("data/dictionaries/product_type.json"))

# Загрузка из Excel
registry.load_from_excel(
    Path("data/dictionaries/dictionaries.xlsx"),
    sheet_name="PRODUCT_TYPE"
)

# O(1) доступ к справочнику
product_dict = registry.get("PRODUCT_TYPE")

# Резолв кода → человекочитаемое имя
result = registry.resolve("PRODUCT_TYPE", 10410001)
print(result.name)          # "PACL"
print(result.english_name)  # "Consumer loan"
print(result.is_valid)      # True

# Валидация кода в справочнике (используется SpEL)
is_valid = registry.validate("PRODUCT_TYPE", 10410001)  # True
is_valid = registry.validate("PRODUCT_TYPE", 99999)      # False
```

#### JsonDictionaryLoader — загрузка из продуктивного JSON

```python
from src.loaders.json_dictionary_loader import JsonDictionaryLoader

loader = JsonDictionaryLoader()
dictionary = loader.load_from_json(Path("data/dictionaries/product_type.json"))
# Dictionary с расширенными полями:
#   code, name, english_localization, current_version, is_deleted, attributes, mappings

# Регистрация в реестре
registry.register(dictionary)
```

#### is_dictionary_value через Registry

```python
from src.core.spel_functions import SpelFunctions

# SpelFunctions.is_dictionary_value использует DictionaryRegistry
# (раньше — заглушка с mock-словарём)
result = SpelFunctions.is_dictionary_value("PRODUCT_TYPE", 10410001)
# True — если Registry содержит справочник PRODUCT_TYPE с кодом 10410001
```

#### Resolve для человекочитаемых отчётов

```python
# ReportFormatter использует resolve для замены кодов на имена
result = registry.resolve("CHANNEL", 10430001)
# ResolveResult(name="Web", english_name="Web", is_valid=True, entry=...)

# В отчёте: "channelCd = 10430001 (Web)" вместо "channelCd = 10430001"
```

#### Новые поля DictionaryEntry

```python
@dataclass
class DictionaryEntry:
    code: str                          # "10410001" (всегда str, даже из Excel)
    name: str                          # "PACL"
    dictionary_type: str               # "PRODUCT_TYPE"
    description: str = ""
    english_localization: str = ""     # "Consumer loan" (продуктивное поле)
    current_version: str = ""          # Версия записи
    is_deleted: bool = False           # Пометка удаления
    attributes: Dict[str, Any] = {}    # Дополнительные атрибуты
    mappings: Dict[str, str] = {}      # Маппинги на другие справочники
    metadata: Dict[str, Any] = {}
```

---

## Как не ломать архитектуру

1. **Не смешивать слои.**
   - Парсер не должен логировать бизнес-события или формировать отчёты.
   - Анализатор не должен читать файлы или заниматься IO.

2. **Сначала модель → потом логика.**
   - Если появляется новая сущность/состояние, сначала добавляем модель
     в `src/models/`, только потом используем её в других слоях.

3. **Сначала тест → потом код.**
   - Для новой фичи сначала описываем ожидаемое поведение в тесте,
     затем реализуем.

4. **Минимизировать side-effects.**
   - Меньше глобальных состояний, больше параметров функций и возвратов.

5. **Использовать logger вместо print.**

### ⚠️ Known Issues (известные проблемы)

| Проблема | Описание | Обходной путь |
|----------|----------|---------------|
| **SpelParser v1 vs v2** | Два подхода: старый (pyparsing-based) и новый (ручной токенизатор). Новый — в `spel_parser.py` | Использовать **новый** SpelParser (`src/core/spel_parser.py`), старый — в `deprecated/` |
| **confest.py опечатка** | Файл называется `confest.py` вместо `conftest.py` в корне проекта — pytest может не подхватить конфигурацию | Переименовать в `conftest.py` |
| **`src/deprecated/` подключён** | Старый SpEL evaluator v0.2.0 в дереве — можно случайно импортировать | НЕ импортировать из `src.deprecated.*`. Использовать `src.core.spel_parser` |

### Как работать с deprecated кодом

1. **НЕ добавлять** новый код в `src/deprecated/`.
2. **НЕ импортировать** из `src.deprecated.*` в новых модулях.
3. Если нужно понять старый подход — прочитать `src/deprecated/spel_v0_2_0_evaluator/README.md`.
4. При рефакторинге — **перенести** старый код из deprecated в новое место, а не расширять deprecated.

---

## Troubleshooting

### pytest падает с ImportError: No module named 'pandas'

**Решение:**
```bash
pip install pandas
```

Если pandas нельзя установить, изолировать `excel_utils` из `src/utils/__init__.py` и импортировать только там, где нужен.

---

### Draft7 vs Draft2019-09 — что использовать?

**Проект использует:** JSON Schema **Draft 2019-09**.

| Формат | Использовать? | Примечание |
|--------|---------------|------------|
| Draft 2019-09 | ✅ **Да** | Стандарт проекта |
| Draft 7 | ❌ Нет | Устарел для проекта |
| Draft 2020-12 | ⚠️ Не сейчас | Может быть добавлен в будущем |

---

### Тесты проходят локально, но не в CI

**Возможные причины:**
1. Разная версия Python (локально 3.12, CI другая)
2. Не установлены зависимости (`pip install -r requirements-dev.txt`)

**Решение:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest -v
```

---

### Как добавить зависимости без поломки

1. Добавить в `requirements.txt`
2. Запустить `pip install -r requirements.txt`
3. Убедиться что `import X` работает
4. Запустить `pytest` — все тесты должны проходить

---

Актуальный статус задач см. в **TODO.md**.

---

## Отладка и логи

### Логи (loguru)

Модуль: `src/utils/logger.py`.

Примеры использования:

```python
from src.utils.logger import get_logger, log_function_call

logger = get_logger(__name__)

@log_function_call
def my_function(x: int) -> int:
    logger.info("Processing x={}", x)
    return x * 2
```

Логи пишутся в консоль и в файл (с ротацией). Путь и уровень логирования
настраиваются через `config/settings.py` и .env.

### Отладка тестов

```bash
# Показать вывод print/логов
pytest -s tests/unit/test_change_analyzer.py

# Остановиться на первой ошибке
pytest -x

# Подробный вывод
pytest -v

# Показать локальные переменные при ошибке
pytest --tb=local
```

При использовании IDE (PyCharm / VS Code):
- Ставим breakpoint в нужном тесте или функции.
- Запускаем тест в режиме Debug.

---

Для деталей архитектуры и требований см. **docs/PRD.md**, **docs/ARCHITECTURE.md** и **docs/SPECIFICATION.md**.
