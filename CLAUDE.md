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

# CLAUDE.md — Контекст проекта json-scenario-generator

**Последнее обновление:** 2026-05-17  
**Текущая версия:** v0.1.0-dev  
**Прогресс MVP:** ~80-85%  
**Тестов:** 320 passed (100%)

---

## 🛠️ Common Commands

### Тесты
```bash
pytest                          # Все тесты (320 passed)
pytest -v                       # Подробный вывод
pytest --cov=src                # С покрытием
pytest tests/unit/core/test_condition_evaluator.py -v   # ConditionEvaluator (38 тестов)
pytest tests/unit/core/test_conditional_validator.py -v   # ConditionalValidator (36 тестов)
pytest tests/unit/core/test_spel_parser.py -v             # SpelParser (20 тестов)
pytest tests/unit/core/test_json_actualizer.py -v           # JsonActualizer (39 тестов)
```

### Линт / Формат / Типы
```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

### Скрипты
```bash
# Анализ изменений между схемами
python scripts/analyze_changes.py \
  --old-schema data/V070Call1Rq.json \
  --new-schema data/V072Call1Rq.json \
  --format markdown \
  --output reports/changes_070_to_072.md \
  --verbose

# Первичная настройка
python scripts/setup_project.py
```

### Окружение
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

---

## 🎯 Текущий статус

**Завершено:** Этапы 0-7 ✅  
**В работе:** Этап 8 — JsonValidator 🟡  
**Следующее:** CLI → ScenarioGenerator

### Прогресс по этапам

```
✅ Этап 0: Подготовка                          100%
✅ Этап 1: Базовая инфраструктура               100%
✅ Этап 2: Парсеры и загрузчики                 100%
✅ Этап 2.5: Анализаторы                        100%
✅ Этап 3: SpEL AST и Parser                    100%
✅ Этап 4: SpEL Functions (34/34)               100%
✅ Этап 5: ConditionEvaluator + Validator       100%
✅ Этап 6: ValueGenerator                       100%   ← ЗАВЕРШЁН
✅ Этап 7: JsonActualizer                      100%   ← ЗАВЕРШЁН
🟡 Этап 8: JsonValidator                       0%    ← ТЕКУЩИЙ ФОКУС
🟡 Этап 9: CLI команды                         0%
🟡 Этап 10: ScenarioGenerator                  0%
🟡 Этап 11: SpelFormatter                      0%    ← P2 (Post-MVP)
```

---

## 📁 Критические файлы проекта

### Ядро (SpEL)

| Файл | Статус | Описание |
|------|--------|----------|
| `src/core/spel_ast.py` | ✅ | 52 NodeType, 13 типов узлов |
| `src/core/spel_parser.py` | ✅ | Парсинг SpEL → AST, 34 оператора |
| `src/core/spel_functions.py` | ✅ | 34/34 функции (Date, String, Business) |
| `src/core/value_generator.py` | ✅ | Генератор значений, 34 теста, покрытие 94% |
| `src/core/json_actualizer.py` | ✅ | Актуализация JSON по SchemaDiff, 39 тестов, покрытие 70% |
| `src/core/condition_evaluator.py` | ✅ | Выполнение AST, 38 тестов |
| `src/core/conditional_validator.py` | ✅ | Валидация УО полей, 36 тестов |
| `src/formatters/spel_formatter.py` | 🟡 | Форматирование SpEL → человекочитаемый текст (P2) |

### Инфраструктура

| Файл | Статус | Описание |
|------|--------|----------|
| `src/models/` | ✅ | 11 dataclass + 4 enum |
| `src/parsers/schema_parser.py` | ✅ | JSON Schema Draft 2019-09 |
| `src/loaders/dictionary_loader.py` | ✅ | Excel-справочники |
| `src/core/schema_comparator.py` | ✅ | Сравнение схем |
| `src/analyzers/change_analyzer.py` | ✅ | 3-уровневая классификация |
| `src/formatters/report_formatter.py` | ✅ | text/md/json отчёты |
| `src/utils/logger.py` | ✅ | loguru с ротацией |
| `src/utils/__init__.py` | ✅ | pandas leak исправлен |

### Тесты

- `tests/unit/core/test_condition_evaluator.py` — 38 тестов ✅
- `tests/unit/core/test_conditional_validator.py` — 36 тестов ✅
- `tests/unit/core/test_spel_parser.py` — 20 тестов ✅
- `tests/unit/core/test_json_actualizer.py` — 39 тестов ✅
- **Всего:** 320 тестов проходят (100%)

---

## 🚀 Следующие задачи (приоритеты)

### P0 — Критично для MVP

1. **JsonValidator** (`src/core/json_validator.py`)
   - Двойная валидация: JSON Schema + SpEL
   - Проверка обязательных (О) и УО полей
   - Тесты: `tests/unit/core/test_json_validator.py`

2. ~~**JsonActualizer** (`src/core/json_actualizer.py`)~~ ✅ ЗАВЕРШЁН

### P1 — MVP релиз

3. **CLI команды** (`src/cli/commands/`)
   - `actualize` — актуализация JSON по diff
   - `validate` — валидация JSON по схеме + SpEL

4. **ScenarioGenerator** (`src/core/scenario_generator.py`)
   - Комбинаторика по 8 параметрам
   - Интеграция с Лист 19 (Excel)
   - Генерация min/max сценариев

### P2 — Post-MVP

5. **SpelFormatter** (`src/formatters/spel_formatter.py`)
   - Преобразование сырых SpEL-выражений в читаемый текст для отчётов
   - 3 уровня детализации (SHORT/MEDIUM/DETAILED)
   - Интеграция с DictionaryLoader для расшифровки кодов
   - Пример: `in(productCdExt, 10410001)` → `продукт = PACCREACT`
   - Тесты: `tests/unit/formatters/test_spel_formatter.py`
   - Статус: 🟡 Спецификация в TODO.md, требует выбора архитектуры

---

## 🛠️ Активный технический долг

| ID | Проблема | Приоритет | Файлы |
|----|----------|-----------|-------|
| TD-7 | Устаревшие ссылки в документации | ✅ | Обновлены все документы |
| TD-8 | Wrong JSON Schema Draft | ✅ | Исправлено: Draft7 → Draft 2019-09 (11.05.2026) |
| TD-9 | No integration tests | 🟡 | `tests/integration/` пуст |
| TD-10 | No test fixtures | 🟡 | `tests/fixtures/` пуст |
| TD-11 | Backup files в репо | 🟡 | 6 `.backup` файлов |
| TD-12 | Deprecated code в src/ | 🟡 | `src/deprecated/` |

###Resolved ✅

- Broken imports в `src/core/__init__.py`
- Test-AST mismatch
- SpEL parser incomplete (34/34 оператора)
- SpelFunctions incomplete (34/34 функции)
- ConditionEvaluator missing (38 тестов)
- ConditionalValidator missing (36 тестов)
- TD-7: Устаревшие ссылки в документации
- TD-8: Wrong JSON Schema Draft → исправлено на Draft 2019-09 (11.05.2026)

---

## 📋 Правила разработки (из DEVELOPMENT.md)

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

### Слои архитектуры

```
CLI / Scripts → ReportFormatter → ChangeAnalyzer → SchemaComparator → Parcers → Models
```

Не смешивать слои: парсер не формирует отчёты, анализатор не читает файлы.

---

## 🧪 Запуск тестов

```bash
# Все тесты
pytest                          # 320 passed

# Подробный вывод
pytest -v

# С покрытием
pytest --cov=src

# Конкретный модуль
pytest tests/unit/core/test_condition_evaluator.py -v
pytest tests/unit/core/test_conditional_validator.py -v
pytest tests/unit/core/test_spel_parser.py -v
pytest tests/unit/core/test_json_actualizer.py -v
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
| `.planning/STATE.md` | Текущее состояние проекта |
| `.planning/ROADMAP.md` | Дорожная карта по фазам |

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
Call0 → Call1 → Call2 → Call3 → Call4 → Call5 → Call7 → CallResult 
CallSupport
CallRPAC

```

---

## 🧠 Контекст последней сессии (2026-05-14)

### Выполнено
1. **Grilling-решения по ValueGenerator:** зафиксированы архитектурные решения через `/context-mode:grill-me`.
2. **Обновление спецификации:** `.planning/VALUEGENERATOR_SPEC.md` актуализирована с учётом решений.
3. **Обновление TODO.md и CLAUDE.md:** даты и требования синхронизированы.
4. **Реализация JsonActualizer (Phase 7):** Создан модуль `src/core/json_actualizer.py` с 39 тестами.

### Ключевые решения (ValueGenerator)
- **Separation of concerns:** ValueGenerator генерирует значения, но **не решает О/УО/Н** — это ConditionalValidator/ScenarioGenerator.
- **UUID cache external:** `Dict[str, str]` в `GeneratorConfig` (ключ = `field_name`). ValueGenerator stateless.
- **Object — OUT OF SCOPE:** Рекурсия по дереву — обязанность JsonActualizer/ScenarioGenerator.
- **Faker:** Два режима через `Optional[Faker]` в конфиге.
- **ИНН:** 10/12 цифр с КС ФНС (Java-валидатор проверяет).
- **СНИЛС:** 11 цифр без КС (Java-валидатор НЕ проверяет КС).
- **Телефон:** `7` + 10 цифр (Java-валидатор не проверяет regex).
- **Placeholder-режим:** Отложен, нет бизнес-кейса.
- **Array:** `max(minItems, default_array_size)` элементов, рекурсивно по `items`.

### Контекст для продолжения
**Следующая задача:** Реализация ValueGenerator (Phase 6)

**Файлы для создания:**
- `src/core/value_generator.py`
- `tests/unit/core/test_value_generator.py`

**Подход:** TDD (сначала тесты, потом реализация)

**Тестовая цель:** 25+ тестов, покрытие > 90%

---

## 📬 Контакты

- **Репозиторий:** https://github.com/Chemixx/json-scenario-generator
- **Автор:** Chemixx
- **Язык проекта:** Русский (по умолчанию для всех ответов)
