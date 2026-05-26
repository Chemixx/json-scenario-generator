## MemPalace — настройки проекта

### Wake-up

Если хук SessionStart, который автоматически вызывает mempalace wake-up при старте сессии, не сработал (убедиться в этом), перед началом работы над проектом выполните:
`mempalace wake-up --wing json-scenario-generator`

Это загрузит контекст последних сессий (600-900 токенов).

### Wing и Rooms

- **Wing:** `json-scenario-generator` (дефис, **НЕ** подчёркивание — не путать с `json_scenario_generator`)
- **Rooms:** `architecture`, `technical`, `planning`, `general`

### Правила записи

| Тип информации | Room | Пример |
|----------------|------|--------|
| Архитектурные решения | `architecture` | Выбор структуры AST, паттерны слоёв |
| Технические детали, рецепты | `technical` | SpEL-операторы, формат ИНН/СНИЛС |
| Планы, дорожные карты | `planning` | Этапы реализации, приоритеты |
| Всё остальное | `general` | Контекст сессий, заметки |

### Knowledge Graph

При появлении новых компонентов/модулей — добавлять в KG:
```
mcp__mempalace__mempalace_kg_add(subject, predicate, object)
```
Примеры: `(ValueGenerator, depends_on, SpelFunctions)`, `(ConditionEvaluator, validates, УО-поля)`

### Diary

В конце каждой сессии записывать итоги:
```
mcp__mempalace__mempalace_diary_write(
  agent_name="claude",
  wing="json-scenario-generator",
  entry="AAAK-compressed summary"
)
```

### Важно

- **Не создавать** wing `json_scenario_generator` (подчёркивание) — всегда используйте `json-scenario-generator` (дефис)
- Перед выводами о проекте — проверяйте KG: `mempalace_kg_query(entity="json-scenario-generator")`

---

# CLAUDE.md — Правила проекта json-scenario-generator

> **Перед началом любой задачи** — прочитай `TODO.md` для актуального статуса этапов, техдолга и приоритетов.

---

## 🛠️ Common Commands

```bash
# Тесты
pytest                          # Все тесты
pytest -v                       # Подробный вывод
pytest --cov=src                # С покрытием
pytest tests/unit/core/test_condition_evaluator.py -v   # ConditionEvaluator
pytest tests/unit/core/test_conditional_validator.py -v # ConditionalValidator
pytest tests/unit/core/test_spel_parser.py -v            # SpelParser
pytest tests/unit/core/test_json_actualizer.py -v         # JsonActualizer
pytest tests/unit/core/test_json_validator.py -v          # JsonValidator

# Линт / Формат / Типы
black src/ tests/
flake8 src/ tests/
mypy src/

# Скрипты
python scripts/analyze_changes.py \
  --old-schema data/V070Call1Rq.json \
  --new-schema data/V072Call1Rq.json \
  --format markdown \
  --output reports/changes_070_to_072.md \
  --verbose
python scripts/setup_project.py  # Первичная настройка

# Окружение
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

---

## 📋 Правила разработки

### Принципы кодирования

1. **Type Hints** — обязательны для всех функций
2. **dataclass** — для всех моделей данных
3. **Логирование** — `get_logger(__name__)` из `src.utils.logger`
4. **Docstrings** — Google style
5. **Тесты** — pytest, Arrange-Act-Assert, TDD для ядра
6. **Импорты** — абсолютные (`from src.core.spel_ast import ...`)

### Запреты

- ❌ Не использовать `eval()` без анализа (security risk)
- ❌ Не выдумывать классы/функции (проверять файлы напрямую)
- ❌ Не игнорировать существующие утилиты
- ❌ Не дублировать функционал (SchemaComparator уже выделен)
- ❌ Не использовать Python < 3.12
- ❌ **Не использовать emoji в runtime-коде** (logger, print, format_text, __str__) — вызывают `UnicodeEncodeError` на Windows cp1251. Использовать ASCII-константы из `src/utils/icons.py` (`Icon.SUCCESS`, `Icon.ERROR` и т.д.). Исключение: `format_markdown()` и `to_emoji()` — эмодзи допустимы (запись в файл с `encoding='utf-8'`).

### Подводные камни реализации

1. **ValidationError** импортируется из `conditional_validator`, НЕ из `schema_models`.
2. **ValueGenerator возвращает Decimal для `number`**, не `float` — в ассертах проверять `isinstance(value, (int, float, Decimal))`.
3. **SpEL ConditionEvaluator не резолвит голые имена полей через root_data** — в тестах мокировать `_evaluate_condition` через `patch.object`, не полагаться на прямой вызов SpEL.
4. **Методы с опциональными параметрами** — `_detect_renames(field_mapping=None)` должен фоллбечить на `self.config.field_mapping`: `effective = field_mapping or self.config.field_mapping`.
5. **Dataclass-методы с ранним return** — проверка флага (`if not self.generate_report: return ""`) должна быть ДО обращения к полям (`lines = [...]`), иначе `UnboundLocalError`.
6. **Emoji в runtime-коде** — использовать `Icon` из `src/utils/icons.py`, НЕ emoji-символы. Emoji крашат `print()`/loguru на Windows cp1251 (TD-16). Для Markdown-формата: `to_emoji()`, для консоли: `to_icon()`.

### Слои архитектуры

```
CLI / Scripts → ReportFormatter → ChangeAnalyzer → SchemaComparator → Parsers → Models
```

Не смешивать слои: парсер не формирует отчёты, анализатор не читает файлы.

---

## 🔑 Ключевые понятия

### SpEL операторы (34 базовых)

**Логика:** `and`, `or`, `not`
**Сравнения:** `eq`, `ne`, `lt`, `le`, `gt`, `ge`
**Null-проверки:** `isNull`, `notNull`, `isBlank`, `notBlank`
**Принадлежность:** `in`, `notIn`
**Строки:** `length`, `matches`, `startsWith`, `endsWith`, `contains`
**Массивы:** `anyMatch`, `allMatch`, `noneMatch`, `filter`, `map`, `hasSize`, `size`, `notEmptyList`, `containsAll`
**Даты:** `currentDate`, `toLocalDate`, `minusYears`, `minusDays`, `isAfter`, `compareTo`
**Бизнес:** `isValidTaxNum`, `isValidUuid`, `digitsCheck`, `isDictionaryValue`
**Навигация:** `this`, `parent`, `parent2`, `parent3`, `root`

### Обязательность полей

| Тип | Условие | Пример |
|-----|---------|--------|
| **О** | `alwaysRequired = true` | Всегда обязательно |
| **Н** | `conditionalRequirement = null` | Опционально |
| **УО** | `conditionalRequirement != null` | Если SpEL → true |

### Call-поток заявки

```
Call0 → Call1 → Call2 → Call3 → Call4 → Call5 → Call7 → CallResult CallSupport CallRPAC
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| `README.md` | Быстрый старт, примеры, roadmap |
| `CHANGELOG.md` | История изменений по версиям |
| `SPECIFICATION.md` | Полная спецификация (~2700 строк) |
| `ARCHITECTURE.md` | Архитектура, SOLID, слои |
| `DEVELOPMENT.md` | Руководство разработчика |
| `PRD.md` | Бизнес-требования |
| `TODO.md` | Статус этапов, техдолг, приоритеты |
| `.planning/STATE.md` | Текущее состояние проекта |
| `.planning/ROADMAP.md` | Дорожная карта по фазам |

---

## 📬 Контакты

- **Репозиторий:** https://github.com/Chemixx/json-scenario-generator
- **Автор:** Chemixx
- **Язык проекта:** Русский (по умолчанию для всех ответов)