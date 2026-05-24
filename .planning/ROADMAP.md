# Roadmap: json-scenario-generator

**Milestone:** v0.1.0 — MVP (SpEL + Актуализация)

---

## Phase 1: SpEL AST

**Status:** ✅ Complete

**Delivered:**
- `src/core/spel_ast.py` — 52 NodeType, 13 типов узлов
- Полная AST-структура для SpEL V72-V74

---

## Phase 2: SpEL Parser

**Status:** ✅ Complete

**Delivered:**
- `src/core/spel_parser.py` — парсинг SpEL → AST
- Поддержка литералов (числа, строки, boolean, null)
- Поддержка операторов: eq, ne, and, or, not, in, notIn, isNull, notNull, isBlank, notBlank

---

## Phase 3: ConditionEvaluator

**Status:** ✅ Complete

**Delivered:**
- `src/core/condition_evaluator.py` — выполнение AST на JSON-данных
- `tests/unit/core/test_condition_evaluator.py` — 38 тестов
- Навигация: this, parent, parent2, rootBean
- Операторы: eq, ne, and, or, not, in, notIn, isNull, notNull, isBlank, notBlank

---

## Phase 4: SpEL Functions

**Status:** ✅ Complete (34/34 функции)

**Implemented:**
- **Date API (6):** current_date, to_local_date, minus_years, minus_days, is_after, compare_to
- **String API (5):** length, matches, startsWith, endsWith, contains
- **Бизнес-функции (4):** is_valid_tax_num, is_valid_uuid, digits_check, is_dictionary_value
- **Операторы сравнения (6):** eq, ne, lt, le, gt, ge
- **Логические (3):** and, or, not
- **Навигация (5):** this, parent, parent2, parent3, root
- **Коллекции (8):** filter, map, anyMatch, allMatch, noneMatch, hasSize, size, notEmptyList, containsAll

---

## Phase 5: ConditionalValidator

**Status:** ✅ Complete

**Delivered:**
- `src/core/conditional_validator.py` — валидация УО полей
- `tests/unit/core/test_conditional_validator.py` — 36 тестов
- Интеграция с ConditionEvaluator и SpelParser
- Проверка обязательных (О) и условно обязательных (УО) полей
- Полная поддержка SpEL V72-V74 операторов

**Scope:**
- Проверка УО (условно обязательных) полей
- Интеграция с ConditionEvaluator
- Валидация полей по SpEL-выражениям из JSON Schema

---

## Phase 6: ValueGenerator

**Status:** ✅ Complete (2026-05-14)

**Delivered:**
- `src/core/value_generator.py` — генератор значений для leaf-типов
- `tests/unit/core/test_value_generator.py` — 34 теста, покрытие 94%
- Поддержка типов: string, integer, number, boolean, array (object — OUT OF SCOPE)
- UUID-кэш: external `Dict[str, str]` в `GeneratorConfig` (stateless)
- Faker: два режима (готовый объект или создание из locale)
- Спецформаты: ИНН (10/12 с КС ФНС), СНИЛС (11 без КС), телефон (7+10 цифр), UUID, date/datetime
- DictionaryLoader: случайный код из справочника
- Constraints: minLength, maxLength, minimum, maximum, pattern, enum, minItems, maxItems
- Array: `max(minItems, default_array_size)` элементов, рекурсивно по items
- Seed-изоляция: собственный `random.Random()` для воспроизводимости

---

## Phase 7: JsonActualizer

**Status:** ✅ Complete (2026-05-17)

**Delivered:**
- `src/core/json_actualizer.py` — применение SchemaDiff к JSON
- `tests/unit/core/test_json_actualizer.py` — 39 тестов, покрытие 70%
- Добавление новых полей (О/УО/Н) с генерацией через ValueGenerator
- Удаление полей из JSON
- Модификация полей: сохранение/перегенерация/преобразование типов
- Обнаружение переименований (эвристика ≥3/5 + field_mapping)
- 3 уровня отката: field/full/none
- Изоляция модуля: actualize() не бросает исключения наружу

**Технический долг:**
- TD-13: ~~SpEL-контекст для УО-полей~~ — ✅ ИСПРАВЛЕНО (24.05.2026): делегировано `ConditionalValidator._build_context()`, добавлен `field_path`, 4 теста без моков
- TD-14: Покрытие 70% вместо 90% (не покрыты actualize_from_paths, StructureError)
- TD-15: `__import__('re')` в `_validate_value` — заменить на явный импорт

---

## Phase 8: JsonValidator

**Status:** 🟡 In Progress

**Scope:**
- Двойная валидация: JSON Schema + SpEL
- Валидация обязательных полей (О)
- Валидация условно обязательных полей (УО)

---

## Phase 9: CLI Commands

**Status:** ❌ Not Started

**Scope:**
- `actualize` — актуализация JSON по diff
- `validate` — валидация JSON по схеме + SpEL
- `generate` — генерация сценариев

---

## Phase 10: ScenarioGenerator

**Status:** ❌ Not Started

**Scope:**
- Комбинаторика сценариев по 8 параметрам
- Интеграция с Лист 19 (Excel)
- Генерация min (О + УО) и max (О + Н + УО) сценариев

---

## Technical Debt

### Resolved ✅

| ID | Issue | Resolution |
|----|-------|------------|
| TD-1 | Broken imports | ✅ Fixed |
| TD-2 | Test-AST mismatch | ✅ Fixed (36 tests added) |
| TD-3 | SpEL parser incomplete | ✅ Fixed (34/34 operators) |
| TD-4 | ConditionEvaluator missing | ✅ Fixed (38 tests) |
| TD-5 | ConditionalValidator missing | ✅ Fixed (36 tests) |
| TD-6 | SpelFunctions incomplete | ✅ Fixed (34/34 functions) |
| TD-16 | Emoji в runtime-коде ломают Windows-консоль | ✅ Fixed (24.05.2026) | Icon module, 160 emoji → ASCII, cp1251 safety net |

### Active 🔴🟠🟡

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| TD-7 | Устаревшие ссылки в документации | ✅ Fixed (08.05.2026) | Обновлены `docs/ARCHITECTURE.md`, `docs/PRD.md`, `CHANGELOG.md`, `TODO.md`, `.planning/STATE.md` |
| TD-8 | Wrong JSON Schema Draft | ✅ Fixed (11.05.2026) | `src/utils/json_utils.py` — заменён Draft7Validator на Draft201909Validator |
| TD-9 | No integration tests | 🟡 | `tests/integration/` пуст |
| TD-10 | No test fixtures | 🟡 | `tests/fixtures/` пуст |
| TD-11 | Backup files в репо | ✅ | Удалены 6 `.backup` файлов (19.05.2026) |
| TD-12 | Deprecated code в src/ | 🟡 | `src/deprecated/` |
