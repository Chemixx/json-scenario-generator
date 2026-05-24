# Архитектура json-scenario-generator

**Версия документа:** 2.1
**Последнее обновление:** 08 мая 2026
**Версия проекта:** 0.1.0-dev (MVP ~90%)

## Цели архитектуры

- Обеспечить **автоактуализацию JSON-сценариев** при изменении версий JSON Schema кредитного конвейера.
- Сохранить **version-agnostic** подход: код не привязан к V070/V072/V073, а работает с любой схемой Draft 2019-09.
- Поддерживать **SOLID**, высокое покрытие тестами и предсказуемое развитие (ROADMAP 0.1.0 → 0.2.0 → 1.0.0).

---

## Слои системы

| Слой | Путь | Назначение |
|------|------|-----------|
| Модели | `src/models/` | Описание доменных сущностей и результатов анализа |
| Парсеры | `src/parsers/` | Преобразование внешних структур (JSON Schema, SpEL) в модели |
| Загрузчики | `src/loaders/` | Чтение Excel/JSON и загрузка справочников/сценариев |
| Ядро | `src/core/` | Бизнес-логика сравнения, актуализации, валидации, SpEL-обработки |
| Анализаторы | `src/analyzers/` | Классификация изменений, генерация объяснений |
| Форматтеры | `src/formatters/` | Преобразование результатов анализа в удобные форматы |
| Отчеты | `src/reports/` | Высокоуровневые отчеты (Markdown/JSON/diff) |
| CLI | `src/cli/`, `scripts/` | Пользовательские команды и интеграция |
| Утилиты | `src/utils/` | Логирование, работа с файлами/JSON |

---

## Слой моделей (`src/models/`)

### Основные сущности

- **VersionInfo / VersionStatus** — метаданные версии схемы (имя файла, версия, статус, тип Call).
- **FieldMetadata** — описание поля схемы:
  - путь (`path`), тип (`field_type`), флаг обязательности, условность (`is_conditional`),
  - словарь (`dictionary`), ограничения (`constraints`), вложенные поля,
  - DQ-коды (`always_required_dq_code`, `conditional_dq_code`, `dictionary_dq_code`),
  - методы: `is_primitive()`, `is_complex()`, `has_dictionary()`, `get_requirement_status()`.
- **ConditionalRequirement** — SpEL-условие:
  - `expression`, `message` (авто-генерируется из выражения), `dq_code`.
  - Метод `_expr_to_message()`: очищает `#this.`, `#root.`, `L` суффиксы, заменяет `&&` → И, `||` → ИЛИ.
- **SchemaDiff** и **FieldChange** — результат сравнения двух схем.
  - `FieldChange.is_breaking_change()` — определяет критичность изменения.
  - `FieldChange.get_severity()` — возвращает `"critical"`, `"warning"`, `"info"`.
- **ChangeType / BreakingLevel / ImpactLevel / FieldElementType** — 3-уровневая классификация + типы полей.
- **AnalyzedChange / AnalysisResult** — результат аналитики изменений.
  - `AnalysisResult` содержит 16+ методов фильтрации/сортировки/сериализации.
- **DictionaryEntry / Dictionary** — справочники значений (CRUD, поиск, итерация, `get_random()`).
- **Scenario / ScenarioMetadata** — JSON-сценарий с навигацией по slash-пути (`get_field_value`, `set_field_value`, `delete_field`).

### Принципы

- Только **dataclass + type hints**.
- Модели не зависят от конкретной реализации парсеров/ядра.
- Используются везде: парсеры, анализаторы, форматтеры, ядро.

---

## Слой парсеров (`src/parsers/` + `src/core/`)

> **Примечание:** SpelParser и SpelAST расположены в `src/core/`, так как относятся к ядру SpEL-обработки.

### SchemaParser (`src/parsers/schema_parser.py`)

- **Вход:** JSON Schema Draft 2019-09.
- **Выход:** `Dict[str, FieldMetadata]` — ключи: slash-пути полей.
- **Поддерживает:**
  - вложенные `properties`, массивы `items`, `allOf`/`oneOf` (где нужно),
  - поле `condition` → `ConditionalRequirement` (dict или строка),
  - вычисление `is_collection`, рекурсивный обход вложенных объектов и массивов.
- **Алгоритм:** `load_schema` → `parse_schema` → `_parse_field` → `_extract_constraints` (10 типов ограничений).

### SpelParser (`src/core/spel_parser.py`) ✅

- **Вход:** строка SpEL (внутренний DSL банка).
- **Выход:** AST-структура через pyparsing.
- **Технология:** pyparsing (не regex).
- **Поддерживает:** 34 оператора SpEL:
  - Логические: `and`, `or`, `not`
  - Сравнения: `eq`, `noteq`, `gt`, `lt`, `gte`, `lte`
  - Null-проверки: `isNull`, `notNull`, `isBlank`, `notBlank`
  - Принадлежность: `in`, `notIn`
  - Строки: `length`, `matches`, `startsWith`, `endsWith`, `contains`
  - Массивы: `anyMatch`, `allMatch`, `noneMatch`, `filter`, `map`, `hasSize`, `size`, `notEmptyList`, `containsAll`
  - Даты: `currentDate`, `toLocalDate`, `minusYears`, `minusDays`, `isAfter`, `compareTo`
  - Бизнес-функции: `isValidTaxNum`, `isValidUuid`, `digitsCheck`, `isDictionaryValue`
  - Навигация: `this`, `parent`, `parent2`, `parent3`, `root`
- **AST-узлы:** 52 NodeType в `src/core/spel_ast.py`
- **Статус:** ✅ 34/34 оператора реализовано, интегрирован с `ConditionEvaluator`

### SpelAST (`src/core/spel_ast.py`)

- **Назначение:** Типизированное AST для SpEL-выражений.
- **NodeType enum:** 11 типов узлов.

| Узел | Поля | Назначение |
|------|------|------------|
| `LiteralNode` | `value` | Число, строка, bool, null |
| `VariableNode` | `name` | `data.inn`, `parent.field` |
| `UnaryOpNode` | `operator`, `operand` | `not`, `!` |
| `BinaryOpNode` | `operator`, `left`, `right` | `eq`, `lt`, `gt`, `and`, `or` |
| `FunctionCallNode` | `func_name`, `args` | `isValidTaxNum(...)` |
| `FilterNode` | `collection`, `condition` | `.?[condition]` |
| `MapNode` | `collection`, `expression` | `.![expression]` |
| `AllMatchNode` | `collection`, `condition` | `.allMatch(...)` |
| `AnyMatchNode` | `collection`, `condition` | `.anyMatch(...)` |
| `NoneMatchNode` | `collection`, `condition` | `.noneMatch(...)` |
| `HasSizeNode` | `collection`, `size` | `.hasSize(...)` |

- **Использование:** SpelParser создаёт AST → ConditionEvaluator/SpelTranspiler исполняет.
- **Статус:** ✅ Структура готова, тесты требуют синхронизации.

**Роль слоя:** изолировать работу с нестабильными внешними форматами (JSON Schema, SpEL),
чтобы ядро оперировало стабильными моделями.

---

## Слой загрузчиков (`src/loaders/`)

### DictionaryLoader

- **Два формата входных данных:**

  | Формат | Описание | Метод |
  |--------|----------|-------|
  | Классический | Один лист = один справочник | `load_dictionary()` |
  | Групповой | Несколько справочников в одном листе (с колонкой "Код справочника") | `load_dictionary_by_code()` |

- **Кэширование:** `_cache: Dict[str, Dictionary]`, ключ: `"{file_path.name}:{sheet_name}"`.
- **Валидация:** `_validate_columns(df, required_columns)` → `ValueError` если колонки отсутствуют.
- **Статус:** ✅ 19 unit-тестов.

### ScenarioLoader (на будущее)

- Будет отвечать за загрузку JSON-сценариев для v0.2.0 (генератор).
- Модель `Scenario` уже готова с методами навигации по slash-пути.

**Роль слоя:** работа с внешними источниками данных (Excel/JSON), без бизнес-логики.

---

## Ядро (`src/core/`)

Это **центр системы**, где реализуются ключевые use-case'ы:

1. Сравнение схем.
2. Актуализация JSON-сценариев.
3. Валидация JSON.
4. SpEL-обработка (парсинг, оценка, функции).

### Граф взаимодействия компонентов ядра

```
┌─────────────────────────────────────────────────────────────┐
│                        ЯДРО (src/core/)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SchemaComparator ────→ SchemaDiff                            │
│       ↑                      ↓                                │
│       │              ┌───────┴───────┐                        │
│       │              │               │                        │
│  SpelParser ────→ SpelAST    ConditionEvaluator               │
│       │              │               ↓                        │
│       │              │         ConditionalValidator           │
│       │              │               ↓                        │
│       │         SpelFunctions    ValueGenerator               │
│       │         (34 функции)         ↓                        │
│       │              │         JsonActualizer                 │
│       │              │               ↓                        │
│       │              └──────────→ JsonValidator               │
│       │                              ↓                        │
│  [Внешние]                    (is_valid, errors)              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### SchemaComparator (`src/core/schema_comparator.py`) ✅

- **Вход:** `Dict[str, FieldMetadata]` старой и новой схемы.
- **Выход:** `SchemaDiff` с коллекциями `added_fields`, `removed_fields`, `modified_fields`.
- **Отвечает за:** поиск отличий, но не за их интерпретацию.
- **Сравниваемые атрибуты:** `field_type`, `is_required`, `is_conditional`, `condition.expression`, `dictionary`, `constraints`, `format`, `default`.
- **Детальный разбор:** `_detect_field_changes()` — 8 типов изменений (тип, обязательность, условность, условие, справочник, constraints, формат, default).
- **Анализ constraint-изменений:** ужесточение vs смягчение.
- **Статус:** ✅ 20 unit-тестов.

---

### Spel-компоненты ядра

#### SpelAST (`src/core/spel_ast.py`) ✅ (структура)

- **11 AST-узлов** (см. раздел "Слой парсеров").
- **NodeType enum** — строгая типизация типов узлов.
- Используется SpelParser для создания деревьев и ConditionEvaluator для исполнения.

#### SpelParser (`src/core/spel_parser.py`) ✅ ЗАВЕРШЁН

- **Текущий статус:** полностью реализован на pyparsing.
- **Алгоритм:** pyparsing → AST-узлы.
- **Поддерживает:** 34 оператора SpEL (логика, сравнения, null-проверки, строки, массивы, даты, бизнес-функции, навигация).
- **Статус:** ✅ 34/34 оператора, 20 unit-тестов проходят.

#### SpelFunctions (`src/core/spel_functions.py`) ✅ ЗАВЕРШЁН (34/34 функции)

- **Все функции реализованы:**

  | Категория | Функции |
  |-----------|---------|
  | **Date API (6)** | current_date, to_local_date, minus_years, minus_days, is_after, compare_to |
  | **String API (5)** | length, matches, startsWith, endsWith, contains |
  | **Бизнес-функции (4)** | is_valid_tax_num, is_valid_uuid, digits_check, is_dictionary_value |
  | **Операторы сравнения (6)** | eq, ne, lt, le, gt, ge |
  | **Логические (3)** | and, or, not |
  | **Навигация (5)** | this, parent, parent2, parent3, root |
  | **Коллекции (8)** | filter, map, anyMatch, allMatch, noneMatch, hasSize, size, notEmptyList, containsAll |

- **Статус:** ✅ 34/34 функции, интегрированы с ConditionEvaluator.

#### ConditionEvaluator ✅ ЗАВЕРШЁН

- **Назначение:** Выполнение SpEL AST на JSON-данных → `True/False`.
- **Архитектура:** AST-based execution (**НЕ использует `eval()`** — безопасность).
- **Алгоритм:** Рекурсивный обход AST-узлов с контекстом (root_data, current_value, parent_stack).
- **Поддерживает:** Все 34 оператора SpEL + навигация (this, parent, parent2, parent3, root).
- **Тесты:** ✅ 38 unit-тестов в `tests/unit/core/test_condition_evaluator.py`.
- **Статус:** ✅ Интегрирован с ConditionalValidator.

#### ConditionalValidator ✅ ЗАВЕРШЁН

- **Назначение:** Валидация условно-обязательных полей (УО): если SpEL-условие выполнено → поле должно иметь значение.
- **Алгоритм:** Интеграция с ConditionEvaluator для проверки SpEL-условий из JSON Schema.
- **Тесты:** ✅ 36 unit-тестов в `tests/unit/core/test_conditional_validator.py`.
- **Выход:** `List[ValidationError]` — каждый с `path`, `message`, `dq_code`.
- **Статус:** ✅ Интегрирован с ConditionEvaluator и SpelParser.

#### ValueGenerator 🔴 ОЖИДАЕТ РЕАЛИЗАЦИИ (Этап 6)

- **Назначение:** Генерация валидных значений для новых/изменённых полей.
- **Планируемая генерация по типам:**

  | Тип | Генератор |
  |-----|-----------|
  | `string` | Faker.ru_RU, учитывая `maxLength`, `format`, `pattern` |
  | `integer` | `random.randint(min, max)` из constraints |
  | `number` | `random.uniform`, учитывая `maxFracLength` |
  | `boolean` | `random.choice([True, False])` |
  | `date` | `Faker.date()` |
  | `dictionary` | `dictionary.get_random().code` |
  | `array` | `[gen_value()] × DEFAULT_ARRAY_SIZE` |
  | `object` | Рекурсия по `properties`, генерация required полей |

- **Специальные генераторы:**

  | Поле | Генератор |
  |------|-----------|
  | UUID | `uuid4()` с кэшированием между Call-ами |
  | ИНН | 10/12 цифр с контрольной суммой |
  | СНИЛС | 11 цифр с контрольной суммой |

- **Статус:** 🔴 Ожидает реализации (Этап 6, P0).

#### JsonActualizer ✅ ЗАВЕРШЁН (Этап 7)

- **Назначение:** Применение `SchemaDiff` к JSON-сценарию — автоматическая актуализация.
- **Зависимости:** ValueGenerator (Этап 6).
- **Статус:** 🔴 Ожидает реализации (Этап 7, P0).

#### JsonValidator ✅ ЗАВЕРШЁН (Этап 8)

- **Назначение:** Двойная валидация: JSON Schema Draft 2019-09 + SpEL-условия.
- **Зависимости:** ConditionalValidator (Этап 5 ✅).
- **Статус:** ✅ Завершён (Этап 8, P0).

**Принцип:** ядро не знает про CLI/формат отчетов, только про доменную логику.

---

## Анализаторы (`src/analyzers/`)

### ChangeAnalyzer

- **Вход:** `SchemaDiff` + (опционально) контекст версий.
- **Выход:** `AnalysisResult` (список `AnalyzedChange`).
- **Отвечает за:**
  - 3-уровневую классификацию (ChangeType, BreakingLevel, ImpactLevel),
  - формирование человекочитаемых причин и рекомендаций.

### Правила классификации добавлений

| Статус поля | BreakingLevel | ImpactLevel |
|-------------|---------------|-------------|
| Обязательно (О) | BREAKING | CRITICAL |
| Условно обяз. (УО) | BREAKING | HIGH |
| Опционально (Н) | NON_BREAKING | LOW |

### Правила классификации удалений

| Статус поля | BreakingLevel | ImpactLevel |
|-------------|---------------|-------------|
| Обязательно (О) | BREAKING | HIGH |
| Условно обяз. (УО) | BREAKING | MEDIUM |
| Опционально (Н) | BREAKING | MEDIUM |

> **Примечание:** Удаление ВСЕГДA breaking.

### Правила классификации модификаций (10 правил в приоритетном порядке)

| # | Изменение | Breaking | Impact |
|---|-----------|----------|--------|
| 1 | Тип данных изменился | BREAKING | CRITICAL |
| 2 | Н → О (стало обязательным) | BREAKING | CRITICAL |
| 3 | О → Н (стало опциональным) | NON_BREAKING | LOW |
| 4 | Н → УО (стало условно обяз.) | BREAKING | HIGH |
| 5 | УО → Н (перестало быть УО) | NON_BREAKING | LOW |
| 6 | Условие УО изменилось | BREAKING | HIGH |
| 7 | Справочник изменился | BREAKING | HIGH |
| 8 | Constraints ужесточены | BREAKING | HIGH |
| 9 | Constraints смягчены | NON_BREAKING | MEDIUM |
| 10 | Прочие изменения | NON_BREAKING | LOW |

**Пример:**
- Добавление обязательного поля →
  - ChangeType = ADDITION,
  - BreakingLevel = BREAKING,
  - ImpactLevel = CRITICAL,
  - Recommendation = "обновить все сценарии, добавить поле".

---

## Форматтеры (`src/formatters/`)

### ReportFormatter

- **Вход:** `AnalysisResult`.
- **Выход:** текст в одном из форматов:
  - `format_text()` — человекочитаемый вывод для консоли (ASCII-иконки, cp1251-safe, ASCII-рамки),
  - `format_markdown()` — отчет для README/CHANGELOG/PR (GitHub-friendly),
  - `format_json()` — структурированный JSON для API/интеграций.

**Структура отчёта:**
```
1. Заголовок (версии, дата)
2. Статистика (total, breaking, impact levels)
3. Критические изменения
4. Breaking changes (не критические)
5. Добавленные поля
6. Удалённые поля
7. Non-breaking модификации
8. Итоговая рекомендация
```

**Почему вынесен в отдельный слой:**
- Анализатор не должен знать, как именно будут выглядеть отчеты.
- Легко добавить HTML/CSV без изменения ChangeAnalyzer.

---

## Отчеты (`src/reports/`)

(Планируется на ЭТАПЕ 4)

- **ReportGenerator** — агрегирует данные и использует ReportFormatter для
  генерации финальных отчетов.
- **DiffHighlighter** — визуальное сравнение JSON (CLI/Markdown/цвета, side-by-side diff).

---

## CLI (`src/cli/`, `scripts/`)

### Текущий статус

- `scripts/analyze_changes.py` — рабочий CLI для команды `analyze_changes`.
- Планируется общий вход `python -m src.cli` с командами:

  | Команда | Статус | Описание |
  |---------|--------|----------|
  | `analyze_changes` | ✅ Готово | Сравнение схем, анализ изменений |
  | `actualize` | 🔴 В работе | Актуализация сценариев |
  | `validate` | 🟡 Запланировано | Валидация JSON по схеме + SpEL |

### Команда analyze_changes

```bash
python scripts/analyze_changes.py <old_schema> <new_schema> [OPTIONS]
```

| Аргумент | Тип | Default | Описание |
|----------|-----|---------|----------|
| `old_schema` | Path (обяз.) | — | Старая JSON Schema |
| `new_schema` | Path (обяз.) | — | Новая JSON Schema |
| `-o, --output` | Path | — | Сохранить JSON-отчёт |
| `--format` | json/text/markdown | text | Формат вывода |
| `--only-critical` | Flag | False | Только CRITICAL |
| `--only-breaking` | Flag | False | Только BREAKING |
| `--verbose` | Flag | False | Подробный вывод |

**Exit codes:**
| Код | Условие |
|-----|---------|
| 0 | Успех, нет критических |
| 1 | Есть критические изменения |
| 2 | Ошибка выполнения (файл не найден, невалидный JSON) |

### Команда actualize (ПЛАНИРУЕТСЯ)

```bash
python -m src.cli actualize \
  --old-schema data/V070Call1Rq.json \
  --new-schema data/V072Call1Rq.json \
  --scenario data/scenarios/call1.json \
  --output output/call1_v072.json \
  [--dictionaries data/dictionaries/]
```

### Команда validate (ПЛАНИРУЕТСЯ)

```bash
python -m src.cli validate \
  --schema data/V072Call1Rq.json \
  --json-file output/call1_v072.json
```

**Принцип:** CLI = тонкая оболочка над ядром, без дублирования логики.

---

## Утилиты (`src/utils/`)

- **logger.py** — настройка loguru, декоратор `@log_function_call`, контекст `LogBlock`.
  - Консоль: цветной вывод, level=INFO.
  - Файл: `logs/app.log`, ротация 10 MB, хранение 30 дней, zip-сжатие.
- **file_utils.py / json_utils.py** — базовые операции с файлами и JSON.
  - ⚠️ **Проблема:** `json_utils.py` использует `Draft7Validator` вместо `Draft201909Validator`.
- **excel_utils.py** — загрузка Excel, получение имён листов.

**Правило:** бизнес-логика не должна зависеть от конкретных способов логирования/IO.

---

## Поток данных (основной сценарий сравнения)

```
┌─────────┐     ┌──────────────┐     ┌───────────────────┐     ┌───────────────┐     ┌──────────┐
│  CLI /   │────→│ SchemaParser │────→│ SchemaComparator  │────→│ ChangeAnalyzer│────→│ Report    │
│  Script  │     │              │     │                   │     │               │     │ Formatter │
└─────────┘     └──────────────┘     └───────────────────┘     └───────────────┘     └──────────┘
                     ↓                        ↓                        ↓                      ↓
               Dict[str,               SchemaDiff              AnalysisResult          text/md/json
               FieldMetadata]
```

1. CLI/скрипт получает пути к двум JSON Schema.
2. **SchemaParser** парсит каждую схему в `Dict[str, FieldMetadata]`.
3. **SchemaComparator** строит `SchemaDiff`.
4. **ChangeAnalyzer** превращает `SchemaDiff` в `AnalysisResult`.
5. **ReportFormatter** формирует text/markdown/json.
6. CLI/скрипт выводит/сохраняет результат.

---

## Поток данных (актуализация JSON)

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Сценарий +  │────→│  JsonActualizer   │────→│   Новый JSON     │────→│  JsonValidator   │
│  SchemaDiff  │     │                   │     │                  │     │                  │
└──────────────┘     └───────────────────┘     └──────────────────┘     └──────────────────┘
                            ↓                                                  ↓
                     ┌──────────────┐                                   ┌──────────────┐
                     │ ValueGen. +  │                                   │   Отчёт:     │
                     │ CondValidator│                                   │ (valid/errors)│
                     └──────────────┘                                   └──────────────┘
```

1. Загрузить обе схемы → `SchemaDiff`.
2. Загрузить JSON-сценарий, создать BACKUP (для rollback).
3. **ADDED поля:** `ValueGenerator.generate()` → установить значение в JSON.
4. **REMOVED поля:** Логировать старое значение → удалить из JSON.
5. **MODIFIED поля:** Преобразовать тип/constraints при необходимости.
6. **ConditionalValidator.validate()** → список ошибок (warning, не блокирует).
7. Сохранить результат → `output_path`.
8. При критической ошибке → ROLLBACK из BACKUP.

---

## SOLID-принципы в проекте

### S — Single Responsibility

- `SchemaParser` — только парсинг схем.
- `SchemaComparator` — только сравнение.
- `ChangeAnalyzer` — только анализ.
- `ReportFormatter` — только форматирование.
- `DictionaryLoader` — только загрузка справочников.
- `SpelParser` — только парсинг SpEL в AST.
- `ConditionEvaluator` — только исполнение AST на данных.
- `ValueGenerator` — только генерация значений.
- `JsonActualizer` — только применение diff к JSON.
- `JsonValidator` — только валидация.

**Польза:** проще тестировать, проще изменять по одному компоненту.

### O — Open/Closed

- `ReportFormatter` открыт для добавления новых форматов (HTML, CSV),
  закрыт для изменения логики анализа.
- `ChangeAnalyzer` можно расширять новыми правилами классификации
  без изменения парсера/компаратора.
- `SpelFunctions` открыт для добавления новых SpEL-функций.

### L — Liskov Substitution

- Используется не в виде наследования, а через подстановку разных реализаций
  интерфейсоподобных компонентов (например, разных форматтеров) там, где
  ожидается единый контракт.

### I — Interface Segregation

- Разделение на небольшие, ясно очерченные модули (parser, comparator,
  analyzer, formatter, spel-parser, spel-evaluator) вместо "комбайнов".

### D — Dependency Inversion

- Высокоуровневые компоненты (CLI, отчеты) зависят от абстракций
  (`AnalysisResult`, `ReportFormatter`), а не от конкретных деталей парсинга/IO.
- Ядро зависит от моделей (`FieldMetadata`, `SchemaDiff`), а не от конкретных парсеров.

---

## Тестирование и качество

- **412 unit-тестов** покрывают все слои (100% pass rate для завершённых этапов).
- Тесты строятся вокруг контрактов слоев:
  - для SchemaParser проверяются вход/выход по FieldMetadata,
  - для SchemaComparator — структура SchemaDiff,
  - для ChangeAnalyzer — корректная классификация,
  - для ReportFormatter — формат итогового вывода.
- **Фикстуры conftest.py:** 16+ фикстур для тестов (версии, поля, справочники, сценарии, диффы).

| Компонент | Тестов | Статус |
|-----------|--------|--------|
| `test_models.py` | 12 | ✅ |
| `test_schema_parser.py` | 12 | ✅ |
| `test_dictionary_loader.py` | 19 | ✅ |
| `test_spel_parser.py` | 20 | ✅ |
| `test_condition_evaluator.py` | 38 | ✅ |
| `test_conditional_validator.py` | 36 | ✅ |
| `test_schema_comparator.py` | 20 | ✅ |
| `test_change_analyzer.py` | 69 | ✅ |
| `test_report_formatter.py` | 12 | ✅ |
| **Итого** | **412** | ✅ **100% проходят** |

**Цель:** любые изменения в слоях сразу подсвечиваются падающими тестами.
**Планируется:** интеграционные и E2E-тесты после завершения Этапа 3.

---

## ⚠️ Известные архитектурные проблемы

### 1. Draft7 vs Draft2019-09 в `json_utils.py` — СРЕДНЯЯ

**Проблема:**
```python
from jsonschema import Draft7Validator  # Draft 7, не 2019-09
```

**Влияние:** Некоторые constraints Draft 2019-09 могут не валидироваться корректно.

**Рекомендация:** Использовать `Draft201909Validator` из `jsonschema` 4.20.0.

**Статус:** 🟡 Требуется замена в рамках TD-8.

---

### 2. Deprecated код `src/deprecated/spel_v0_2_0_evaluator/` — НИЗКАЯ

**Содержимое:**
| Файл | Назначение |
|------|------------|
| `spel_context.py` | Контекст выполнения SpEL |
| `spel_evaluator.py` | Старая версия evaluator |
| `spel_protocols.py` | Протоколы SpEL |
| `spel_transpiler.py` | Транспиляция SpEL |

**Статус:** Устаревшая версия SpEL-evaluator (v0.2.0), не используется. Актуальная реализация: `src/core/spel_parser.py` (pyparsing, 34 оператора) + `src/core/condition_evaluator.py` (AST-based execution).

**Рекомендация:** Удалить директорию `src/deprecated/` или переместить за пределы `src/` (TD-12).

---

### 3. UUID-кэширование между Call-ами — СРЕДНЯЯ

**Проблема:** Механизм UUID-кэширования для связей между Call0 → Call1 → Call2 ещё не реализован.

**Требование:** Один и тот же UUID должен генерироваться для одного и того же поля в разных Call-ах.

**Статус:** 🟡 Будет реализован в ValueGenerator (Этап 6).

---

### 4. No integration tests — СРЕДНЯЯ

**Проблема:** Директория `tests/integration/` пуста.

**Рекомендация:** Создать E2E-тесты для сценариев актуализации и валидации.

**Статус:** 🟡 Запланировано после Этапа 10 (TD-9).

---

### 5. No test fixtures — НИЗКАЯ

**Проблема:** Директория `tests/fixtures/` пуста.

**Рекомендация:** Создать фикстуры с тестовыми JSON-сценариями и схемами.

**Статус:** 🟡 Запланировано (TD-10).

---

### 6. Backup files в репо — НИЗКАЯ

**Проблема:** 6 `.backup` файлов в репозитории.

**Рекомендация:** Удалить через `git rm`.

**Статус:** ✅ Исправлено (19.05.2026) — 6 `.backup` файлов удалены.


---

## Эволюция архитектуры

### Версия 0.1.0 ("Актуализатор") — MVP ~90%

- Фокус: анализ + актуализация + валидация.
- Слои: модели, парсеры, загрузчики, ядро, анализаторы, форматтеры, CLI.
- **Готово:** Этапы 0-5 (инфраструктура, парсеры, анализаторы, SpEL AST/Parser/Functions/Evaluator/Validator).
- **В работе:** Этап 6 (ValueGenerator).
- **Тестов:** 412 passed (100%).

### Версия 0.2.0 ("Генератор")

- Добавляется ScenarioGenerator и связанный функционал.
- Архитектура остаётся: генератор использует те же модели и ядро.
- Генерация новых сценариев с нуля по схеме + продукт + канал.

### Версия 1.0.0 ("Конфигуратор")

- Добавляются конфигурационные YAML'ы, интерактивный CLI, возможно Web UI.
- База остаётся прежней, UI-слой только расширяется.

---

## Основные архитектурные идеи

1. **Version-agnostic:** код не завязан на номера версий схем.
2. **Ядро без UI:** бизнес-логика не зависит от CLI/отчетов.
3. **Тест-первый подход:** любые изменения сначала отражаются в тестах.
4. **Расширяемость:** генерация и конфигуратор строятся на существующем ядре.
5. **AST-based SpEL:** безопасность — НЕ использовать `eval()`, только AST-evaluation.
6. **Rollback при актуализации:** BACKUP → обработка → валидация → сохранение (или rollback).

---

## Конфигурация (`config/settings.py`)

### AppConfig — ключевые настройки

| Категория | Поля |
|-----------|------|
| Пути | `BASE_DIR`, `DATA_DIR`, `OUTPUT_DIR`, `LOG_DIR`, `SCHEMAS_DIR`, `DICTIONARIES_DIR`, `SCENARIOS_DIR` |
| Логирование | `LOG_LEVEL`, `LOG_FILE`, `LOG_ROTATION` (10 MB), `LOG_RETENTION` (30 дней) |
| Генерация | `DEFAULT_LOCALE` ("ru_RU"), `DEFAULT_ARRAY_SIZE` (1), `GENERATE_RANDOM_INN` (True) |
| Валидация | `STRICT_VALIDATION` (True), `VALIDATE_DICTIONARIES` (True) |
| Отчёты | `REPORT_FORMAT` ("markdown"), `INCLUDE_EXAMPLES` (True), `HIGHLIGHT_CHANGES` (True) |

**Методы:** `get_schema_path()`, `get_report_path()`, `get_updated_scenario_path()` — автоматическое создание директорий.

---

*Последнее обновление: 14 апреля 2026*
*Версия проекта: 0.1.0 (MVP ~90%)*
