# Changelog

Все значимые изменения этого проекта будут задокументированы в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
этот проект придерживается [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-05-26

### Added
- **DictionaryLoader v2**: Complete dictionary system with O(1) lookup and prod-JSON support
  - `DictionaryRegistry` — central store with O(1) lookup, resolve, and validation
  - `JsonDictionaryLoader` — loads prod-JSON format (1905.64/1905.65) with filter_deleted/filter_current
  - `DictionaryEntry` extended with production fields (english_localization, current_version, is_deleted, attributes, mappings)
  - `Dictionary` O(1) hash indexes (_code_index, _name_index)
  - `DictionaryMetadata` and `ResolveResult` dataclasses
  - Real `is_dictionary_value()` implementation via Registry (replaces stub)
  - Registry integration in ValueGenerator, JsonValidator, ReportFormatter
  - Integration tests: full pipeline JSON→Registry→SpEL→Validation
  - 57 new tests (DictionaryRegistry, JsonDictionaryLoader, SpEL-dictionary integration, dictionary pipeline)

### Fixed
- DictionaryLoader: code column type int instead of str (P3 fix)

### Changed
- SpelFunctions: `is_dictionary_value` is now an instance method (no longer @staticmethod)
- **541 tests pass** (was 484)

---

## [Unreleased] - 2026-05-24

### Added
- **TD-14 fixed**: JsonActualizer test coverage raised from 71% to 100% (104 tests, was 43). Line 971 marked as `# pragma: no cover` (dead code — unreachable elif branch).

### Added
- **Icon module** (`src/utils/icons.py`): 31 ASCII-констант для безопасного вывода в любую кодировку (cp1251-safe). Заменяют эмодзи в runtime-коде.
- **`to_icon()` methods** в `BreakingLevel` и `ImpactLevel`: возвращают ASCII-иконки (`[WARN]`, `[OK]`, `[!!!]`, `[!!]`, `[!]`, `[.]`) для консольного вывода.
- **Encoding safety net** в `logger.py` и `analyze_changes.py`: `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` предотвращает `UnicodeEncodeError`.
- **JsonValidator** (Phase 8): New module `src/core/json_validator.py`
  - `JsonValidator` class with `validate()`, `validate_batch()`, `validate_from_paths()` methods
  - 5 independent validation steps: schema (Draft201909Validator), required (О), conditional (УО), constraints, dictionaries
  - `ValidatorConfig`: step configuration, strict/lenient, DQ codes, output format (tree/flat)
  - Error hierarchy: `BaseValidationError` + `SchemaError`, `RequiredError`, `ConditionalError`, `ConstraintError`, `DictionaryError`
  - `ValidationResult` with `to_summary(format)` (tree/flat) and `to_dict()`
  - `ValidationStatistics` with field counts, error counts, duration
  - `requirement_type` (null/missing) on `RequiredError` and `ConditionalError`
  - Auto-detect call from schema metadata (stageName/version/direction) in `validate_from_paths()`
- **constraint_utils.py**: Shared constraint checking (10 types: minLength, maxLength, pattern, minimum, maximum, minItems, maxItems, enum, maxIntLength, maxFracLength)
- DQ field parsing in SchemaParser: `alwaysRequiredDqCode`, `conditionalDqCode`, `dictionaryDqCode`
- `requirement_type` field (null/missing) on `ConditionalValidator.ValidationError`
- 85 new tests (59 for JsonValidator, 26 for constraint_utils)
- **JsonActualizer**: test coverage raised from 71% to 100% (104 tests, was 43). Line 971 marked `# pragma: no cover` (unreachable elif branch). TD-14 resolved.

### Changed
- **TD-16 fixed**: 160 эмодзи в runtime-коде заменены на ASCII-константы из `Icon`. `format_text()` использует Icon, `format_markdown()` сохраняет эмодзи (безопасно — записывает в файл с `encoding='utf-8'`).
- Заменены эмодзи в 18 файлах: `logger.py`, `report_formatter.py`, `dictionary_loader.py`, `json_utils.py`, `excel_utils.py`, `enums.py`, `schema_models.py`, `schema_parser.py`, `change_analyzer.py`, `schema_comparator.py`, `spel_functions.py`, `analyze_changes.py`, `setup_project.py`, `logger_example.py` + 4 тестовых файла.
- 423 теста пройдены, 0 падений. Все Icon-константы cp1251-safe.
- **484 теста пройдены** (включая 104 для JsonActualizer, 59 для JsonValidator, 26 для constraint_utils).
- **TD-13 fixed**: `JsonActualizer._evaluate_condition()` now delegates context building to `ConditionalValidator._build_context()`, correctly resolving `#this`, `parent`, `parent2` SpEL navigation. Added `field_path` parameter. 4 new tests without mocks.
- `JsonActualizer._validate_result()` removed — `JsonValidator` is the single validation point
- `JsonActualizer._validate_value()` now uses `constraint_utils.check_constraint()`
- `ActualizationResult.validation_errors` always empty list (no longer populated by JsonActualizer)

### Known Issues
- **TD-17**: Loguru logs mixed with report output in STDOUT — 20+ lines of INFO/DEBUG before useful output. Fix: CLI should log WARNING+ to STDERR, INFO+ to file.
- **TD-18**: `affected_scenarios` field always empty in ChangeAnalyzer output (18/18 changes). Needs analysis: remove field or populate from SpEL conditions.
- **TD-19**: Generic recommendations in reports — 30/51 are template phrases. Needs analysis: show specific product codes instead.
- **TD-20**: Truncated SpEL conditions in reports lose critical product code values. Key information cut off with `...`.
- **TD-21**: Exit code 0 despite 15 breaking changes. Script only exits 1 on `critical`, not `breaking`. Needs analysis of exit code logic.

---

## [0.1.0-dev] - 2026-05-17

### Added
- **JsonActualizer** (Phase 7): New module `src/core/json_actualizer.py`
  - `JsonActualizer` class with `actualize()`, `actualize_batch()`, `actualize_from_paths()` methods
  - `ActualizerConfig`, `ActualizationChange`, `ActualizationResult`, `RenamePair` dataclasses
  - SchemaDiff-based JSON migration: add/remove/modify/rename fields
  - Conditional (УО) field evaluation via ConditionEvaluator
  - Three-level rollback: field (default), full, none
  - Rename detection via metadata matching (≥3/5 attributes) or explicit field_mapping
  - Strict value validation on modification (type, enum, pattern, length, range)
  - Type transformation (integer→string, string→boolean, etc.)
  - 39 unit tests in `tests/unit/core/test_json_actualizer.py`
  - Exports added to `src/core/__init__.py`

### Changed
- Total tests: 281 → 320 → 412 → 484 passed

## [Unreleased] — 2026-05-14

### ✅ Завершено (Этап 5 — ConditionalValidator + полная поддержка SpEL)

**Инфраструктура** ✅
- Исправлен pandas leak: `src/utils/__init__.py` не импортирует `excel_utils` автоматически
- Установлен `pyparsing==3.1.1` для Python 3.14
- **484 unit-теста проходят** (было 173 → 247 → 281 → 320 → 412 → 484)

**SpelAST** ✅ завершён
- 52 NodeType в `src/core/spel_ast.py`
- 13 основных AST-узлов: LiteralNode, FieldNode, ParentNNode, RootNode, UnaryOpNode, BinaryOpNode, NaryOpNode, CallMethodNode, FilterNode, MapNode, AnyMatchNode, AllMatchNode, NoneMatchNode, HasSizeNode
- Вспомогательные функции: `create_and()`, `create_or()`, `create_eq()`, `create_in()`, `create_is_null()`, etc.

**SpelParser** ✅ завершён (полная поддержка SpEL V72-V74)
- Парсер на pyparsing в `src/core/spel_parser.py`
- **Все 34+ базовых оператора:**
  - Логика: `and`, `or`, `not`
  - Сравнения: `eq`, `ne`, `lt`, `le`, `gt`, `ge`
  - Null-проверки: `isNull`, `notNull`, `isBlank`, `notBlank`
  - Принадлежность: `in`, `notIn`
  - Строки: `length`, `matches`, `startsWith`, `endsWith`, `contains`
  - Массивы: `anyMatch`, `allMatch`, `noneMatch`, `filter`, `map`, `hasSize`, `size`, `notEmptyList`, `containsAll`
  - Даты: `currentDate`, `toLocalDate`, `minusYears`, `minusDays`, `isAfter`, `compareTo`
  - Бизнес: `isValidTaxNum`, `isValidUuid`, `digitsCheck`, `isDictionaryValue`
  - Навигация: `#this.field`, `#parent.field`, `#rootBean.field`
- Поддержка строк в одинарных кавычках
- Вызов методов: `call(target, methodName, args...)`

**SpelFunctions** ✅ завершён (34/34 функции)
- Все функции реализованы в `src/core/spel_functions.py`:
  - **Date API (6):** current_date, to_local_date, minus_years, minus_days, is_after, compare_to
  - **String API (5):** length, matches, startsWith, endsWith, contains
  - **Бизнес-функции (4):** is_valid_tax_num, is_valid_uuid, digits_check, is_dictionary_value
  - **Операторы сравнения (6):** eq, ne, lt, le, gt, ge
  - **Логические (3):** and, or, not
  - **Навигация (5):** this, parent, parent2, parent3, root
  - **Коллекции (8):** filter, map, anyMatch, allMatch, noneMatch, hasSize, size, notEmptyList, containsAll
  - **Даты (4):** currentDateTime, toDateTime, plusYears, plusDays, isBefore, isBetween

**ConditionEvaluator** ✅ завершён (полный)
- Выполнение SpEL AST на JSON-данных в `src/core/condition_evaluator.py`
- EvaluationContext: root_data, current_value, parent_stack
- **Все операторы поддерживаются:**
  - Литералы: числа, строки, boolean, null
  - Поля: this, parent, parent2-parent3, rootBean.field
  - Логика: and, or, not (короткое замыкание)
  - Сравнения: eq, ne, lt, le, gt, ge
  - Null-проверки: isNull, notNull, isBlank, notBlank
  - Принадлежность: in, notIn
  - Массивы: anyMatch, allMatch, noneMatch, filter, map, hasSize
  - Даты: currentDate, toLocalDate, minusYears, minusDays, isAfter, compareTo
  - Бизнес: isValidTaxNum, isValidUuid, digitsCheck, isDictionaryValue
  - Вызов методов: Date API, String API, бизнес-функции через SpelFunctions
- **38 unit-тестов** в `tests/unit/core/test_condition_evaluator.py` (100% проходят)

**ConditionalValidator** ✅ завершён
- Валидация условно-обязательных полей (УО) в `src/core/conditional_validator.py`
- Интеграция с ConditionEvaluator для проверки SpEL-условий
- Проверка обязательных (О) и условно обязательных (УО) полей
- **36 unit-тестов** в `tests/unit/core/test_conditional_validator.py` (100% проходят)

---

### ✅ Завершено (Этап 6 — ValueGenerator)

**ValueGenerator** ✅ завершён
- Генератор значений в `src/core/value_generator.py`
- **34 unit-теста**, покрытие 94%
- Поддержка типов: string, integer, number, boolean, array
- Специальные форматы: UUID, date, datetime, email
- **ИНН:** 10/12 цифр с валидной КС ФНС (`strict_inn=True/False`)
- **СНИЛС:** 11 цифр без КС (как Java-валидатор)
- **Телефон:** `7` + 10 цифр (российский мобильный)
- **UUID-кэш:** external `Dict[str, str]` в `GeneratorConfig` (stateless, ключ = `field_name`)
- **Faker-интеграция:** два режима (готовый объект или создание из `locale`)
- **DictionaryLoader:** случайный код из справочника для полей с `dictionary`
- **Constraints:** minLength, maxLength, minimum, maximum, pattern, enum, minItems, maxItems
- **Array:** `max(minItems, default_array_size)` элементов, рекурсивно по `items`
- **Seed-изоляция:** собственный `random.Random()` instance для воспроизводимости

**JsonActualizer** ✅ Завершён (Этап 7)
- Применение SchemaDiff к JSON-сценариям
- Добавление, удаление, преобразование полей

**JsonValidator** ✅ Завершён (Этап 8)
- Двойная валидация: JSON Schema Draft 2019-09 + SpEL-условия

### 🔧 Исправлено
- **TD-8:** `src/utils/json_utils.py` — заменён `Draft7Validator` на `Draft201909Validator` для корректной валидации JSON Schema Draft 2019-09


### 📋 Запланировано

**Этап 4: Отчёты**
- `SpelFormatter` — форматирование SpEL-выражений в человекочитаемый текст (P2). Пример: `in(productCdExt, 10410001)` → `продукт = PACCREACT`
- `ReportGenerator` — расширенные Markdown-отчёты с рекомендациями по миграции
- `DiffHighlighter` — side-by-side diff для JSON с ANSI-цветами

**Этап 5: CLI интеграция**
- Rich UI (прогресс-бары, цветные таблицы)
- Команда `actualize` CLI
- Команда `validate` CLI
- E2E тесты

**v0.2.0: Генератор сценариев**
- `ScenarioGenerator` — генерация min/max сценариев с нуля
- `CallMappingLoader` — загрузка Лист 19 Excel
- Комбинаторика: productCd × loanTypeCd × channelCd
- CLI: `generate --schema V072.json --product 10410001 --type min`

**v1.0.0: Конфигуратор**
- YAML-конфигурация сценариев
- Интерактивный CLI (Rich library)
- Web UI (FastAPI + React) — опционально
- Версионные атрибуты (доступные поля по версиям)

### 🐛 Известные проблемы

| # | Проблема | Серьёзность | Статус |
|---|----------|-------------|--------|
| TD-7 | Устаревшие ссылки в документации | 🟠 Высокая | ✅ Исправлено (08.05.2026) |
| TD-8 | `src/utils/json_utils.py` использует `Draft7Validator` вместо `Draft201909Validator` | 🟡 Средняя | ✅ Исправлено (11.05.2026) |
| TD-9 | Нет интеграционных тестов (только unit-тесты) | 🟡 Средняя | Добавить E2E |
| TD-10 | Нет test fixtures | 🟡 Низкая | Добавить fixtures |
| TD-11 | Backup files в репо (.backup) | ✅ Низкая | Удалены (19.05.2026) |
| TD-12 | Deprecated code в src/ | 🟡 Низкая | Переместить/удалить |

---

## [0.1.0-dev] — 2025-12-10 (последний релиз)

### ✅ Добавлено

#### Этап 0: Подготовка (100%)
- Виртуальное окружение Python 3.12+
- Зависимости: `requirements.txt` (runtime), `requirements-dev.txt` (development)
- Структура проекта через `scripts/setup_project.py`
- Git конфигурация, `.gitignore`, `.env.example`

#### Этап 1: Базовая инфраструктура (100%)
- **`config/settings.py`** — AppConfig с путями к `data/`, `output/`, `logs/`, загрузка `.env`
- **`src/utils/logger.py`** — loguru с консольным и файловым выводом, ротация 10 MB, хранение 30 дней, декораторы логирования, context manager
- **Модели данных** (`src/models/`):
  - 11 dataclass + 4 enum
  - `VersionInfo`, `VersionStatus` — информация о версиях схем
  - `FieldMetadata`, `ConditionalRequirement` — метаданные полей и SpEL-условия
  - `FieldChange`, `SchemaDiff` — изменения между схемами
  - `AnalyzedChange`, `AnalysisResult` — классифицированные изменения
  - `DictionaryEntry`, `Dictionary` — справочники допустимых значений
  - `Scenario`, `ScenarioMetadata` — JSON-сценарии
  - Enums: `ChangeType`, `BreakingLevel`, `ImpactLevel`, `FieldElementType`
- **12 unit-тестов** для моделей

#### Этап 2: Парсеры и загрузчики (100%)
- **`src/parsers/schema_parser.py`** — парсинг JSON Schema Draft 2019-09, рекурсивный обход, извлечение метаданных, обработка `condition` (строка или объект)
- **`src/loaders/dictionary_loader.py`** — загрузка Excel-справочников (.xlsx), поддержка классического и группового форматов, кэширование
- **31 unit-тест** (12 SchemaParser + 19 DictionaryLoader)

#### Этап 2.5: Анализаторы (100%)
- **`src/core/schema_comparator.py`** — сравнение двух JSON Schema, детальный разбор изменений constraints, определение added/removed/modified полей
- **`src/analyzers/change_analyzer.py`** — 3-уровневая классификация:
  - **ChangeType**: ADDITION / REMOVAL / MODIFICATION (что произошло)
  - **BreakingLevel**: BREAKING / NON_BREAKING (ломает API или нет)
  - **ImpactLevel**: CRITICAL / HIGH / MEDIUM / LOW (критичность для бизнеса)
  - Генерация рекомендаций для каждого изменения
- **`src/formatters/report_formatter.py`** — модульное форматирование отчётов:
  - `format_text()` — консольный вывод с эмодзи
  - `format_markdown()` — GitHub-friendly Markdown
  - `format_json()` — структурированный JSON для API/интеграций
- **`scripts/analyze_changes.py`** — CLI для анализа изменений (version-agnostic: любые версии схем)
  - Аргументы: `old_schema`, `new_schema`, `-o/--output`, `--format`, `--only-critical`, `--only-breaking`, `--verbose`
  - Exit codes: 0 (успех), 1 (критические изменения), 2 (ошибка)
- **101 unit-тест** (20 SchemaComparator + 69 ChangeAnalyzer + 12 ReportFormatter)

### 📊 Статистика v0.1.0-dev

| Метрика | Значение |
|---------|----------|
| **Файлов .py** | 60 |
| **Unit-тестов задекларировано** | 250+ |
| **Unit-тестов проходит** | **484 (100%)** |
| **Этапов завершено** | 5 из 10 (Этапы 0–5 завершены) |
| **Общий прогресс MVP** | ~90% |
| **Покрытие (этапы 0–2.5)** | 100% |
| **Покрытие (SpEL)** | 100% (AST ✅, Parser ✅, Evaluator ✅, Functions ✅, Validator ✅) |
| **SpEL-операторов поддержано** | **34 из 34 (100%)** |
| **SpelAST узлов** | 52 NodeType ✅ |
| **ConditionEvaluator тестов** | 38 ✅ |
| **ConditionalValidator тестов** | 36 ✅ |

---

## Хронология разработки

| Дата | Событие |
|------|---------|
| Ноябрь 2025 | Начало проекта, Этап 0 (подготовка окружения) |
| Ноябрь 2025 | Этап 1: базовая инфраструктура (модели, конфигурация, логирование) |
| Начало декабря 2025 | Этап 2: парсеры и загрузчики (SchemaParser, DictionaryLoader) |
| 7 декабря 2025 | Создание PRD v1.0 |
| 10 декабря 2025 | Этап 2.5 завершён: анализаторы (SchemaComparator, ChangeAnalyzer, ReportFormatter), CLI, 153 теста |
| 10 декабря 2025 | Обновление PRD v2.0: генерация перенесена в v0.2.0, фокус на актуализацию |
| Декабрь 2025 — Апрель 2026 | Пауза в разработке |
| 14 апреля 2026 | Возобновление разработки: создание SPECIFICATION.md (2700 строк), актуализация документации, фиксация известных проблем |
| 7 мая 2026 | Этап 3 часть 1 завершена: ConditionEvaluator ✅, 38 тестов ✅, инфраструктура ✅ |
| **7 мая 2026** | **Этап 5 завершён: ConditionalValidator ✅ (36 тестов), SpelParser ✅ (34/34 оператора), SpelFunctions ✅ (34/34 функции), 247 тестов проходят** |

---

## Ссылки

- [SPECIFICATION.md](docs/SPECIFICATION.md) — полная спецификация (~2700 строк)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура системы
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) — руководство разработчика
- [PRD.md](docs/PRD.md) — требования к продукту
- [README.md](README.md) — обзор проекта

---

<p align="center">
  <sub>Последнее обновление: 26 мая 2026 · Версия: 0.1.0-dev · Статус: 🚧 DictionaryLoader v2 завершён (~92% MVP)</sub>
</p>
