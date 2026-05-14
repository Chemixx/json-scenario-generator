# Project State: json-scenario-generator

**Analysis Date:** 2026-05-07

## Executive Summary

**json-scenario-generator** — CLI-инструмент для автоматизации актуализации JSON-сценариев кредитного конвейера (РКК 2.0) при изменении версий JSON Schema контрактов front-adapter.

**Цель:** Заменить ручную работу QA-инженеров (3–5 дней на релиз) автоматической актуализацией за минуты.

**Текущий статус:** 75–80% готовности. Этапы 0–5 завершены (инфраструктура, парсеры, анализаторы, SpEL AST/Parser/Evaluator, ConditionalValidator). **247 тестов проходят**. Этап 6 (ValueGenerator) в работе.

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
| **Unit тесты** | ✓ | **247 тестов проходят** |

### In Progress (⚠️)

| Компонент | Прогресс | Проблема |
|-----------|----------|----------|
| **JsonActualizer** | 0% | Не начат |

### Not Started (❌)

| Компонент | Приоритет | Блокирует |
|-----------|-----------|-----------|
| **ValueGenerator** | ✅ | 34 теста, покрытие 94%. Реализован 2026-05-14. |
| **JsonActualizer** | 0% | Не начат |
| **JsonValidator** | P1 | Валидацию JSON по схеме + SpEL |
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

### High (🟠) — Скоро фиксить

| # | Проблема | Файлы | Влияние |
|---|----------|-------|---------|
| 1 | **Wrong JSON Schema Draft** | `src/utils/json_utils.py:11, 165` | ✅ Исправлено (11.05.2026) |

### Medium (🟡) — Технический долг

| # | Проблема | Влияние |
|---|----------|---------|
| 3 | **No integration tests** | `tests/integration/` пуст |
| 4 | **No test fixtures** | `tests/fixtures/` пуст |
| 5 | **Backup files в репо** | 6 `.backup` файлов |
| 6 | **Deprecated code в src/** | `src/deprecated/` смешан с активным кодом |

---

## Roadmap Priorities

### ✅ Завершено (Этапы 0–5)

| # | Задача | Статус | Тесты |
|---|--------|--------|-------|
| 1 | SpelParser (34+ оператора) | ✅ Complete | 20 тестов |
| 2 | ConditionEvaluator | ✅ Complete | 38 тестов |
| 3 | ConditionalValidator | ✅ Complete | 36 тестов |
| 4 | SpelFunctions (34/34) | ✅ Complete | — |

### P0 (Blockers) — Критично для MVP

| # | Задача | Оценка | Зависимости | Статус |
|---|--------|--------|-------------|--------|
| 5 | ValueGenerator (leaf-поля, UUID cache, Faker, ИНН/СНИЛС/телефон) | 2 дня | — | 🟡 Спека утверждена, готов к реализации |
| 6 | JsonActualizer | 3 дня | ValueGenerator | 🔴 Не начат |

### P1 (MVP) — Релиз

| # | Задача | Оценка | Зависимости |
|---|--------|--------|-------------|
| 7 | JsonValidator | 2 дня | ConditionalValidator |
| 8 | ScenarioGenerator | 3 дня | Лист 19, ValueGenerator |
| 9 | CLI команды | 2 дня | Все выше |

### P2 (Post-MVP)

| # | Задача | Оценка |
|---|--------|--------|
| 10 | SpelFormatter | 2 дня |
| 11 | ReportGenerator | 2 дня |

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
