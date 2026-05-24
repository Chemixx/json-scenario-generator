# Project State: json-scenario-generator

**Analysis Date:** 2026-05-22

## Executive Summary

**json-scenario-generator** — CLI-инструмент для автоматизации актуализации JSON-сценариев кредитного конвейера (РКК 2.0) при изменении версий JSON Schema контрактов front-adapter.

**Цель:** Заменить ручную работу QA-инженеров (3–5 дней на релиз) автоматической актуализацией за минуты.

**Текущий статус:** ~90% готовности. Этапы 0–8 завершены (инфраструктура, парсеры, анализаторы, SpEL AST/Parser/Evaluator/Functions, ConditionalValidator, ValueGenerator, JsonActualizer, JsonValidator). **400+ тестов проходят**. Этап 9 (CLI) — следующий.

**Репозиторий:** https://github.com/Chemixx/json-scenario-generator

---

## Project Context

### Purpose

Автоматизация актуализации JSON-сценариев при обновлении JSON Schema контрактов front-adapter (версии V070 → V072 → V073 → ...).

### Business Value

- **До:** QA-инженеры вручную актуализируют сценарии 3–5 дней на релиз
- **После:** Автоматическая актуализация за минуты
- **Экономия:** ~80% времени QA на релиз

---

## Current Status

### Completed (✓)

| Компонент | Статус | Детали |
|-----------|--------|--------|
| **Этапы 0–2.5** | ✓ | Инфраструктура, парсеры, анализаторы |
| **SpEL AST** | ✓ | 52 NodeType, 13 типов узлов |
| **SpEL Parser** | ✓ | 34+ оператора, полная поддержка V72-V74 |
| **SpEL Functions** | ✓ | 34/34 функции реализованы |
| **ConditionEvaluator** | ✓ | 38 тестов, все операторы |
| **ConditionalValidator** | ✓ | 36 тестов, УО-валидация |
| **ValueGenerator** | ✓ | 34 теста, покрытие 94% |
| **JsonActualizer** | ✓ | Применение SchemaDiff к JSON |
| **JsonValidator** | ✓ | 5 шагов валидации, 59 тестов |
| **Unit тесты** | ✓ | **400+ тестов проходят** |

### In Progress (⚠️)

| Компонент | Прогресс | Проблема |
|-----------|----------|----------|
| — | — | — |

### Not Started (❌)

| Компонент | Приоритет | Блокирует |
|-----------|-----------|-----------|
| **ScenarioGenerator** | P1 | Комбинаторику сценариев |
| **CLI команды** | P1 | Пользовательский интерфейс |

---

## Technical Debt

### Resolved (✅)

| # | Проблема | Статус |
|---|----------|--------|
| 1 | **Broken imports** в `src/core/__init__.py` | ✅ Исправлено |
| 2 | **Test-AST mismatch** | ✅ Исправлено (36 тестов добавлено) |
| 3 | **SpEL parser incomplete** | ✅ Исправлено (34/34 оператора) |
| 4 | **SpelFunctions incomplete** | ✅ Исправлено (34/34 функции) |
| 5 | **ConditionEvaluator не реализован** | ✅ Исправлено (38 тестов) |
| 6 | **ConditionalValidator не реализован** | ✅ Исправлено (36 тестов) |
| 7 | **Устаревшие ссылки в документации** | ✅ Исправлено (08.05.2026) |

### Active (⚠️)

| # | Проблема | Приоритет | Влияние |
|---|----------|-----------|---------|
| TD-13 | **SpEL-контекст для УО-полей в JsonActualizer** | ✅ Исправлено (24.05.2026) | Делегировано `ConditionalValidator._build_context()`, добавлен `field_path`, 4 теста без моков |
| TD-14 | **Покрытие JsonActualizer 70%** | 🟡 Средний | Не покрыты: `actualize_from_paths`, `_StructureError`. ~~`_validate_result`~~ удалён в Phase 8 (заменён на JsonValidator) |
| TD-15 | **`__import__('re')` в `_validate_value`** | ✅ Исправлено | `_validate_value` теперь использует `constraint_utils.check_constraint()` |
| TD-16 | **Emoji в runtime-коде ломают Windows-консоль** | ✅ Исправлено (24.05.2026) | `src/utils/icons.py` создан (31 ASCII-константа), 160 эмодзи → Icon, `format_text()` → ASCII, `format_markdown()` → emoji, `to_icon()` в enums, `sys.stdout.reconfigure()` safety net |
| TD-17 | **Loguru логи смешаны с отчётом в STDOUT** | 🟡 Средний | 20+ строк INFO/DEBUG перед полезным выводом. Решение: CLI → WARNING в STDERR, INFO в файл; ReportFormatter → только STDOUT |
| TD-18 | **`affected_scenarios` всегда `[]`** | 🟡 Средний | ChangeAnalyzer: 18/18 changes с пустым списком. Нужен анализ: убрать поле или заполнять из SpEL-условий |
| TD-19 | **Шаблонные рекомендации в отчёте** | 🔵 Низкий | ReportFormatter: 30/51 рекомендаций — «Проверить условие». Нужен анализ: что показывать вместо этого |
| TD-20 | **Обрезанные SpEL-условия в отчёте** | 🟠 Высокий | ReportFormatter: ключевые productCdExt обрезаются `...`. Теряется критически важная информация |
| TD-21 | **Exit code 0 при breaking changes** | 🔵 Низкий | analyze_changes.py: `sys.exit(1)` только при `critical`, но `breaking` ≠ `critical`. Нужен анализ exit code логики |
| TD-9 | **No integration tests** | 🟡 Средний | `tests/integration/` пуст |
| TD-10 | **No test fixtures** | 🟡 Средний | `tests/fixtures/` пуст |
| TD-11 | **Backup files в репо** | ✅ Низкий | Удалены 6 `.backup` файлов (19.05.2026) |
| TD-12 | **Deprecated code в src/** | 🟡 Низкий | `src/deprecated/` |

### High (🟠) — Скоро фиксить

| # | Проблема | Файлы | Влияние |
|---|----------|-------|---------|
| 1 | **Wrong JSON Schema Draft** | `src/utils/json_utils.py:11, 165` | ✅ Исправлено (11.05.2026) |

### Medium (🟡) — Технический долг

| # | Проблема | Влияние |
|---|----------|---------|
| 3 | **No integration tests** | `tests/integration/` пуст |
| 4 | **No test fixtures** | `tests/fixtures/` пуст |
| 5 | **Backup files в репо** | ✅ Удалены (19.05.2026) |
| 6 | **Deprecated code в src/** | `src/deprecated/` смешан с активным кодом |

---

## Roadmap Priorities

### ✅ Завершено (Этапы 0–7)

| # | Задача | Статус | Тесты |
|---|--------|--------|-------|
| 1 | SpelParser (34+ оператора) | ✅ Complete | 20 тестов |
| 2 | ConditionEvaluator | ✅ Complete | 38 тестов |
| 3 | ConditionalValidator | ✅ Complete | 36 тестов |
| 4 | SpelFunctions (34/34) | ✅ Complete | — |
| 5 | ValueGenerator | ✅ Complete | 34 теста (94% покрытие) |
| 6 | JsonActualizer | ✅ Complete | — |

### P0 (Blockers) — Критично для MVP

| # | Задача | Оценка | Зависимости | Статус |
|---|--------|--------|-------------|--------|
| 8 | JsonValidator | 2 дня | JsonValidator | ✅ Complete 59 тестов |

### P1 (MVP) — Релиз

| # | Задача | Оценка | Зависимости |
|---|--------|--------|-------------|
| 8 | ScenarioGenerator | 3 дня | Лист 19, ValueGenerator |
| 9 | CLI команды | 2 дня | Все выше |

### P2 (Post-MVP)

| # | Задача | Оценка | Зависимости | Детали |
|---|--------|--------|-------------|--------|
| 10 | **SpelFormatter** | 2-3 дня | SpelParser, DictionaryLoader | Форматирование SpEL → человекочитаемый текст. Пример: `in(productCdExt, 10410001)` → `продукт = PACCREACT`. 3 уровня детализации (SHORT/MEDIUM/DETAILED). Архитектура: registry/visitor/template — требует выбора. 15+ тестов. |
| 11 | ReportGenerator | 2 дня | SpelFormatter, ReportFormatter | Расширенные Markdown-отчёты с подсветкой diff и рекомендациями |

---

## Technology Stack

| Категория | Технологии |
|-----------|------------|
| **Язык** | Python 3.14.3 |
| **CLI** | click 8.3.2, rich 13.7.0 |
| **Логирование** | loguru 0.7.2 |
| **Валидация** | jsonschema 4.20.0 (Draft 2019-09) |
| **Данные** | pandas 2.2.0, openpyxl 3.1.2 |
| **Парсинг** | pyparsing 3.1.1 |
| **Тесты** | pytest 7.4.3, Faker 22.0.0 |
| **Качество** | flake8 7.3.0, black 25.11.0 |

**Конфигурация:** `.env` через python-dotenv, `AppConfig` dataclass.

**Платформа:** Windows 11 Pro (dev), кроссплатформенный (pathlib).

---

## Key Constraints

| Ограничение | Статус |
|-------------|--------|
| **Python** | 3.12+ (фактически 3.14.3) |
| **JSON Schema** | Draft 2019-09 |
| **Type hints** | Обязательны для всех функций |
| **dataclass** | Для всех моделей данных |
| **TDD** | Для ядра (ConditionEvaluator, ConditionalValidator) |
| **Логирование** | `get_logger(__name__)` из `src.utils.logger` |
| **Импорты** | Абсолютные (`from src.core.spel_ast import ...`) |

---

## E2E Process Summary

### Call-поток заявки

```
Call0 → Call1 → Call2 → Call3 → Call4 → Call5 → CallSupp
```

| Call | Назначение |
|------|-----------|
| Call0 | Инициализация, `loanRequestExtId` |
| Call1 | Параметры кредита (productCd, loanTypeCd, channelCd, creditAmt) |
| Call2 | Данные клиента |
| Call3 | Доходы |
| Call4 | Залоги |
| Call5 | Дополнительные параметры |
| CallSupp | Дополнительная информация |

### 8 ключевых параметров комбинаторики

1. **`productCd`** — продукт (PACCREACT, PACLIREACT, MORTREACT, CARDREACT)
2. **`creditProgramCd`** — программа
3. **`loanTypeCd`** — тип обязательства (ипотека, потребительский, авто)
4. **`createChannelCd`** — канал создания (REACT, Mobile, Office, Partner)
5. **`channelCd`** — канал получения
6. **`issuanceChannelCd`** — канал выдачи
7. **Тип клиента** — `mdmId` (существующий) vs `prospectId` (новый)
8. **Тип сценария** — **min** (О + УО) vs **max** (О + Н + УО)

### Обязательность полей

| Тип | Условие | Пример |
|-----|---------|--------|
| **О** | `alwaysRequired = true` | Всегда обязательно |
| **Н** | `conditionalRequirement = null` | Опционально |
| **УО** | `conditionalRequirement != null` | Если SpEL → true |

### Лист 19 (Excel)

Маппинг `PRODUCTCD → CALLCD` со значением `M` (Mandatory) определяет обязательные Call-ы для каждого продукта.

---

## Anti-Virus Rules

### Критические запреты

| ❌ Запрет | Почему |
|----------|--------|
| Не утверждать «тесты прошли» без вывода pytest | Галлюцинация в прошлых диалогах |
| Не предлагать удаление модулей без проверки | Transpiler/Evaluator критичны |
| Не выдумывать классы/функции | Проверять файлы напрямую |
| Не использовать `eval()` без анализа | Security risk |
| Не игнорировать существующие утилиты | `get_logger`, `load_json` |
| Не дублировать функционал | SchemaComparator уже выделен |
| Не использовать Python < 3.12 | Target 3.12+ |
| Не заканчивать ответ вопросами | Нарушение формата |

### Принципы кодирования

1. **Type Hints** — обязательны
2. **dataclass** — для моделей
3. **Логирование** — `get_logger(__name__)`
4. **Docstrings** — Google style
5. **Тесты** — pytest, Arrange-Act-Assert
6. **Импорты** — абсолютные
7. **TDD** — для ядра

---

## Prior Work Context

**Session continuity:** Этот документ создан для сохранения контекста между сессиями. Перед началом работы проверь:

- [ ] Прочитан `.planning/STATE.md`
- [ ] Известны текущие приоритеты (P0: SpelParser, ConditionEvaluator)
- [ ] Известны критичные проблемы (broken imports, test-AST mismatch)

---

*Project State analysis: 2026-05-06*
