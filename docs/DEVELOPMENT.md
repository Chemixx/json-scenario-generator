# Руководство разработчика json-scenario-generator

Этот документ отвечает на вопросы:
- "Как быстро поднять проект?"
- "Как запускать тесты?"
- "Как правильно добавлять новый функционал, чтобы не сломать архитектуру?"

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

### 3. Первичная настройка

```bash
python scripts/setup_project.py
cp .env.example .env
# При необходимости отредактировать .env (пути к data/, logs/ и т.д.)
```

### 4. Запуск тестов

```bash
pytest
# Ожидаемый результат: 153 passed
```

---

## Структура проекта (для разработчика)

См. также раздел "СТРУКТУРА ПРОЕКТА" в README.md.

Критичные директории для разработки:

- `src/models/` — доменные модели и enums.
- `src/parsers/` — парсинг JSON Schema и SpEL.
- `src/loaders/` — загрузка справочников и сценариев.
- `src/core/` — бизнес-логика (сравнение, актуализация, валидация).
- `src/analyzers/` — анализ изменений.
- `src/formatters/` — форматирование отчетов.
- `src/cli/` и `scripts/` — CLI и интеграция.
- `tests/` — unit- и (в будущем) integration/E2E-тесты.

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

**Требование:** новые фичи должны сопровождаться unit-тестами, которые покрывают
основные и крайние случаи.

---

## Как добавлять новый функционал

Ниже — шаблоны для типовых задач, с учетом архитектуры и SOLID.

### Пример 1: добавить новый формат отчета (HTML) в ReportFormatter

1. Открыть `src/formatters/report_formatter.py`.
2. Добавить новый метод:

```python
def format_html(self, result: AnalysisResult) -> str:
    """Форматирование результата анализа в HTML."""
    # Сформировать простой HTML-документ на основе result
    # (заголовки, таблицы, списки изменений)
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

4. (Опционально) добавить поддержку нового формата в CLI/скрипты:

```python
# В scripts/analyze_changes.py
parser.add_argument(
    "--format",
    choices=["text", "markdown", "json", "html"],
    default="text",
)

# В main():
elif args.format == "html":
    output = formatter.format_html(analysis_result)
```

**Важно:** ни ChangeAnalyzer, ни SchemaComparator при этом не меняются.

---

### Пример 2: добавить новый SpEL-оператор (после реализации ConditionEvaluator)

1. Открыть `src/parsers/condition_parser.py` и расширить грамматику.
2. Открыть `src/core/spel_functions.py` и добавить реализацию функции.
3. Добавить тесты в `tests/unit/test_condition_parser.py` и для ConditionEvaluator.

**Правило:**
- Парсер отвечает за корректный разбор строки в AST.
- Исполнитель (ConditionEvaluator/SpELFunctions) отвечает за семантику.

---

### Пример 3: добавить новое правило классификации изменений

1. Открыть `src/analyzers/change_analyzer.py`.
2. Найти соответствующий метод (`_analyze_addition`, `_analyze_removal`, `_analyze_modification`).
3. Добавить новое условие, опираясь на модели `FieldChange` и enums.
4. Добавить тест в `tests/unit/test_change_analyzer.py` с понятным примером.

**Важно:** не добавлять прямой вывод/логирование в ChangeAnalyzer; для этого есть ReportFormatter и logger.

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
```

При использовании IDE (PyCharm / VS Code):
- Ставим breakpoint в нужном тесте или функции.
- Запускаем тест в режиме Debug.

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
- Всегда использовать **type hints**.
- Не использовать "магические" dict там, где лучше подходит dataclass.
- Не дублировать бизнес-логику в разных местах.

---

## Git Workflow и коммиты

### Ветвление

- Основная ветка: `main`.
- Для новых фич: `feature/<short-name>`.

```bash
git checkout -b feature/add-json-actualizer
```

### Сообщения коммитов (Conventional Commits)

Формат: `тип: краткое описание`.

Основные типы:
- `feat:` — новая функциональность
- `fix:` — исправление багов
- `docs:` — документация
- `test:` — тесты
- `refactor:` — рефакторинг без изменения внешнего поведения
- `chore:` — инфраструктура, конфиг, зависимости

Примеры:

```bash
git commit -m "feat(core): implement JsonActualizer for added/removed fields"
git commit -m "test(core): cover JsonActualizer with array path cases"
git commit -m "docs: update ARCHITECTURE with JsonActualizer details"
```

---

## Как не ломать архитектуру

1. **Не смешивать слои.**
   - Парсер не должен логировать бизнес-события или формировать отчеты.
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

---

## TODO для разработчика (связано с архитектурой)

На момент 0.1.0 (45-50% готовности):

- Реализовать `ConditionEvaluator` и `SpELFunctions` (ЭТАП 3.1).
- Реализовать `ValueGenerator` и `JsonActualizer` (ЭТАП 3.3–3.4).
- Добавить интеграционные тесты для полного сценария `compare`/`actualize`/`validate`.

Для деталей см. **docs/PRD.md** и **README.md**.
