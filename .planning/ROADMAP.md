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

**Status:** ❌ Not Started

**Scope:**
- Генерация валидных значений для всех типов полей
- Кэширование UUID (одно значение на сценарий)
- Интеграция с Faker
- Поддержка типов: string, integer, number, boolean, array, object

---

## Phase 7: JsonActualizer

**Status:** ❌ Not Started

**Scope:**
- Применение SchemaDiff к JSON
- Обновление полей при изменении схемы
- Сохранение существующих значений при возможности

---

## Phase 8: JsonValidator

**Status:** ❌ Not Started

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

### Active 🔴🟠🟡

| ID | Issue | Priority | Files |
|----|-------|----------|-------|
| TD-7 | Устаревшие ссылки в документации | ✅ Fixed (08.05.2026) | Обновлены `docs/ARCHITECTURE.md`, `docs/PRD.md`, `CHANGELOG.md`, `TODO.md`, `.planning/STATE.md` |
| TD-8 | Wrong JSON Schema Draft | 🟠 | `src/utils/json_utils.py:11, 165` |
| TD-9 | No integration tests | 🟡 | `tests/integration/` пуст |
| TD-10 | No test fixtures | 🟡 | `tests/fixtures/` пуст |
| TD-11 | Backup files в репо | 🟡 | 6 `.backup` файлов |
| TD-12 | Deprecated code в src/ | 🟡 | `src/deprecated/` |
