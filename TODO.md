# TODO: json-scenario-generator

**Последнее обновление:** 2026-05-08  
**Прогресс MVP:** 75-80%  
**Тестов:** 247 passed (100%)  
**Релиз v0.1.0:** В работе  
**TD-7:** ✅ Исправлено (устаревшие ссылки в документации обновлены)

---

## 🎯 Критический путь MVP

```
ConditionEvaluator ✅ → ConditionalValidator ✅ → ValueGenerator (P0) → JsonActualizer (P0) → JsonValidator (P1) → CLI actualize (P1)
```

---

## ✅ Завершённые этапы (0-5)

| Этап | Компонент | Файлы | Тесты | Статус |
|------|-----------|-------|-------|--------|
| **Этап 0** | Подготовка | — | — | ✅ 100% |
| **Этап 1** | Базовая инфраструктура | `src/models/`, `src/utils/` | 35 | ✅ 100% |
| **Этап 2** | Парсеры и загрузчики | `SchemaParser`, `DictionaryLoader` | 15 | ✅ 100% |
| **Этап 2.5** | Анализаторы | `ChangeAnalyzer`, `SchemaComparator` | 24 | ✅ 100% |
| **Этап 3** | SpEL AST и Parser | `SpelAST`, `SpelParser` | 20 | ✅ 100% |
| **Этап 4** | SpEL Functions | `SpelFunctions` (34/34) | — | ✅ 100% |
| **Этап 5** | ConditionEvaluator + Validator | `ConditionEvaluator`, `ConditionalValidator` | 74 | ✅ 100% |

### Детали завершённых компонентов

**SpEL Engine:**
- 52 NodeType в AST
- 34 оператора парсинга
- 34 функции (Date API: 6, String API: 5, Бизнес: 4, Навигация: 5, Коллекции: 8, Логика: 6)

**Валидация:**
- `ConditionEvaluator` — 38 тестов, выполнение AST на JSON-данных
- `ConditionalValidator` — 36 тестов, УО-валидация

**Анализ изменений:**
- `ChangeAnalyzer` — 3-уровневая классификация (ChangeType + BreakingLevel + ImpactLevel)
- `ReportFormatter` — text/markdown/json отчёты

---

## 🔴 P0 — Критично для MVP (следующие 2 недели)

### Этап 6: ValueGenerator

**Файлы для создания:**
- `src/core/value_generator.py`
- `tests/unit/core/test_value_generator.py`

**Требования:**
- [ ] Генерация значений для типов: string, integer, number, boolean, array, object
- [ ] Кэширование UUID (одно значение на сценарий)
- [ ] Интеграция с Faker для реалистичных данных
- [ ] Форматирование: даты, ИНН, UUID, телефоны, СНИЛС
- [ ] Поддержка справочников (DictionaryLoader)
- [ ] 30+ unit-тестов

**Оценка:** 2 дня

---

### Этап 7: JsonActualizer

**Файлы для создания:**
- `src/core/json_actualizer.py`
- `tests/unit/core/test_json_actualizer.py`

**Требования:**
- [ ] Применение SchemaDiff к JSON
- [ ] Добавление новых полей (с генерацией значений через ValueGenerator)
- [ ] Удаление полей из JSON
- [ ] Преобразование типов полей
- [ ] Сохранение существующих значений
- [ ] 25+ unit-тестов

**Оценка:** 3 дня

---

### Этап 8: JsonValidator

**Файлы для создания:**
- `src/core/json_validator.py`
- `tests/unit/core/test_json_validator.py`

**Требования:**
- [ ] Двойная валидация: JSON Schema + SpEL
- [ ] Проверка обязательных (О) полей
- [ ] Проверка условно обязательных (УО) полей через ConditionEvaluator
- [ ] Детальный отчёт об ошибках валидации
- [ ] 35+ unit-тестов

**Оценка:** 2 дня

---

### Этап 9: CLI команды

**Файлы для создания:**
- `src/cli/__init__.py`
- `src/cli/commands/__init__.py`
- `src/cli/commands/actualize.py`
- `src/cli/commands/validate.py`
- `src/cli/commands/generate.py`
- `src/cli/ui/__init__.py` (Rich UI компоненты)

**Требования:**
- [ ] Команда `actualize` — актуализация JSON по diff
- [ ] Команда `validate` — валидация JSON по схеме + SpEL
- [ ] Команда `generate` — генерация сценариев
- [ ] Rich UI: прогресс-бары, цветной вывод
- [ ] Интеграция с ReportFormatter
- [ ] Интеграционные тесты

**Оценка:** 2 дня

---

## 🟡 P1 — MVP релиз (после P0)

### Этап 10: ScenarioGenerator

**Файлы для создания:**
- `src/core/scenario_generator.py`
- `tests/unit/core/test_scenario_generator.py`

**Требования:**
- [ ] Комбинаторика по 8 параметрам (productCd, creditProgramCd, loanTypeCd, channelCd, и т.д.)
- [ ] Интеграция с Лист 19 (Excel маппинг PRODUCTCD → CALLCD)
- [ ] Генерация min-сценариев (О + УО поля)
- [ ] Генерация max-сценариев (О + Н + УО поля)
- [ ] Кэширование общих значений
- [ ] 40+ unit-тестов

**Оценка:** 3 дня

---

## 🟢 P2 — Post-MVP (улучшения)

### SpelFormatter

**Файлы:**
- `src/formatters/spel_formatter.py`
- `tests/unit/formatters/test_spel_formatter.py`

**Требования:**
- [ ] Форматирование SpEL-выражений в человекочитаемый вид
- [ ] Интеграция с ChangeAnalyzer для отчётов
- [ ] 10+ unit-тестов

**Оценка:** 2 дня

---

### ReportGenerator

**Файлы:**
- `src/reports/generator.py`
- `src/reports/templates/` (Markdown шаблоны)

**Требования:**
- [ ] Расширенные Markdown-отчёты для актуализации
- [ ] Отчёты для валидации
- [ ] Агрегация изменений по сценариям
- [ ] 15+ unit-тестов

**Оценка:** 2 дня

---

## 🛠️ Технический долг

### Высокий приоритет (🟠)

| # | Проблема | Файлы | Действие |
|---|----------|-------|----------|
| TD-7 | **Устаревшие ссылки в документации** | `docs/ARCHITECTURE.md`, `docs/PRD.md`, `CHANGELOG.md`, `TODO.md` | ✅ **ИСПРАВЛЕНО** (08.05.2026) |
| TD-8 | **Wrong JSON Schema Draft** | `src/utils/json_utils.py:11, 165` | Исправить Draft7 → Draft 2019-09 |

### Средний приоритет (🟡)

| # | Проблема | Действие |
|---|----------|----------|
| TD-9 | **No integration tests** | Создать `tests/integration/` с E2E тестами |
| TD-10 | **No test fixtures** | Создать `tests/fixtures/` с тестовыми данными |
| TD-11 | **Backup files в репо** | Удалить 6 `.backup` файлов |
| TD-12 | **Deprecated code в src/** | Переместить `src/deprecated/` за пределы `src/` или удалить |

---

## 📁 Структура файлов (актуальная)

### Ядро (src/core/)

```
src/core/
├── spel_ast.py              ✅ 52 NodeType
├── spel_parser.py           ✅ 34 оператора
├── spel_functions.py        ✅ 34/34 функции
├── condition_evaluator.py   ✅ 38 тестов
├── conditional_validator.py ✅ 36 тестов
├── schema_comparator.py     ✅
├── value_generator.py       🔴 TODO
├── json_actualizer.py       🔴 TODO
├── json_validator.py        🔴 TODO
└── scenario_generator.py    🟡 TODO
```

### Инфраструктура

```
src/
├── models/                  ✅ 11 dataclass + 4 enum
├── parsers/
│   └── schema_parser.py     ✅
├── loaders/
│   └── dictionary_loader.py ✅
├── analyzers/
│   └── change_analyzer.py   ✅
├── formatters/
│   └── report_formatter.py  ✅ text/markdown/json
├── utils/
│   ├── logger.py            ✅
│   ├── json_utils.py        ⚠️ Draft7 bug
│   └── excel_utils.py       ✅
├── cli/                     🔴 Пусто
│   ├── commands/            🔴 Пусто
│   └── ui/                  🔴 Пусто
└── reports/                 🔴 Пусто
```

### Тесты

```
tests/
├── unit/
│   ├── test_*.py            ✅ 13 файлов, ~119 тестов
│   └── core/
│       ├── test_spel_parser.py          ✅ 20 тестов
│       ├── test_condition_evaluator.py  ✅ 38 тестов
│       └── test_conditional_validator.py ✅ 36 тестов
├── integration/             🔴 Пусто
└── fixtures/                🔴 Пусто
```

---

## 📊 Метрики проекта

| Метрика | Значение |
|---------|----------|
| **Файлов кода** | ~40 .py файлов |
| **Unit-тестов** | 247 passed |
| **Покрытие ядра** | ~85% (оценка) |
| **SpEL операторов** | 34/34 (100%) |
| **SpEL функций** | 34/34 (100%) |
| **Готовность MVP** | 75-80% |

---

## 🚦 Зависимости между задачами

```mermaid
graph TD
    A[SpelParser ✅] --> B[ConditionEvaluator ✅]
    B --> C[ConditionalValidator ✅]
    C --> D[ValueGenerator]
    D --> E[JsonActualizer]
    E --> F[JsonValidator]
    F --> G[CLI actualize]
    D --> H[ScenarioGenerator]
    H --> G
```

---

## 📝 Чек-лист перед релизом v0.1.0

- [ ] ValueGenerator реализован и протестирован
- [ ] JsonActualizer реализован и протестирован
- [ ] JsonValidator реализован и протестирован
- [ ] CLI команды работают
- [ ] Все интеграционные тесты проходят
- [ ] Технический долг TD-7, TD-8 исправлен
- [ ] Документация обновлена
- [ ] CHANGELOG.md актуализирован
- [ ] Все 247 существующих тестов проходят

---

## 🔗 Ссылки

- **Репозиторий:** https://github.com/Chemixx/json-scenario-generator
- **Спецификация:** `docs/SPECIFICATION.md` (~2700 строк)
- **Архитектура:** `docs/ARCHITECTURE.md`
- **Разработка:** `docs/DEVELOPMENT.md`
- **PRD:** `docs/PRD.md`
- **Состояние:** `.planning/STATE.md`
- **Roadmap:** `.planning/ROADMAP.md`
