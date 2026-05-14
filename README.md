# 🏦 JSON Scenario Generator

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0--dev-orange.svg)]()
[![Tests](https://img.shields.io/badge/tests-281%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-🚧%20in%20development-yellow.svg)]()

> **CLI-инструмент для автоматизации актуализации JSON-сценариев** при изменении версий JSON Schema кредитного конвейера банка.

---

## 📖 О проекте

Представьте: банк выпустил новую версию JSON Schema для кредитного конвейера (например, v0.70 → v0.72). Теперь **100+ тестовых JSON-сценариев** нужно вручную обновить — добавить новые поля, удалить устаревшие, исправить типы. Работа QA-инженера на **~3 дня**.

**JSON Scenario Generator** делает это автоматически за **~5 минут**.

### Что делает инструмент

| Задача | Что происходит | Результат |
|--------|---------------|-----------|
| 🔍 **Анализ изменений** | Сравнивает две версии JSON Schema, классифицирует каждое изменение по 3 уровням | Отчёт: что добавлено, удалено, изменено — с оценкой критичности |
| 🔄 **Актуализация JSON** *(в разработке)* | Обновляет существующие JSON-сценарии под новую схему: добавляет поля, удаляет устаревшие, генерирует валидные значения | Готовый JSON, прошедший валидацию |
| ✅ **Валидация JSON** *(запланировано)* | Проверяет сценарий по JSON Schema + SpEL-условиям (условно-обязательные поля) | Список ошибок с пояснениями |

### Для кого этот проект

- **QA-инженеры** — актуализация сотен сценариев без ручного труда
- **Backend-разработчики** — быстрый анализ breaking changes между версиями API
- **DevOps** — интеграция автоматической актуализации в CI/CD pipeline
- **Бизнес-аналитики** — оценка влияния изменений схемы на процессы
- **Новые члены команды** — понимание архитектуры через документацию

### Ключевые термины

<details>
<summary><b>JSON Schema</b> — спецификация структуры JSON-документа</summary>
Описывает, какие поля обязательны, какие значения допустимы, какие условия применяются. Проект использует <b>Draft 2019-09</b>.
</details>

<details>
<summary><b>SpEL (Spring Expression Language)</b> — язык выражений для условий</summary>
Используется для условно-обязательных полей (УО). Пример: <code>in(productCd, 10410001, 10410002)</code> — поле обязательно, только если продукт PACL или TOPUP. Поддерживается <b>34 оператора</b>.
</details>

<details>
<summary><b>УО / О / Н</b> — статус обязательности поля</summary>
<b>О</b> — всегда обязательное, <b>УО</b> — обязательно при условии (SpEL), <b>Н</b> — необязательное.
</details>

<details>
<summary><b>Call (Call0/Call1/Call2)</b> — тип запроса в кредитном конвейере</summary>
Каждый Call — JSON-запрос, валидируемый по своей схеме. Сценарии сохраняют UUID-связи между Call0 → Call1 → Call2.
</details>

---

## ⚡ Быстрый старт

Установка и первый запуск за 5 минут:

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Chemixx/json-scenario-generator.git
cd json-scenario-generator

# 2. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Установите зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Инициализируйте проект
python scripts/setup_project.py
cp .env.example .env

# 5. Запустите тесты
pytest
# Ожидаемый результат: 281 passed (100%)
```

---

## 🚀 Возможности

### ✅ Реализовано (v0.1.0)

| Возможность | Описание | Статус |
|-------------|----------|--------|
| **Анализ изменений** | Сравнение любых версий JSON Schema (version-agnostic) | ✅ |
| **3-уровневая классификация** | ChangeType + BreakingLevel + ImpactLevel | ✅ |
| **Breaking changes detection** | Удаление required-полей, смена типов, constraints | ✅ |
| **Отчёты в 3 форматах** | Text, Markdown, JSON | ✅ |
| **Загрузка справочников** | Excel-справочники (.xlsx), кэширование | ✅ |
| **SpelAST** | 52 NodeType, 13 основных узлов | ✅ |
| **SpelParser** | Парсинг SpEL → AST, 34 оператора | ✅ |
| **SpelFunctions** | 34/34 функции (Date API, String API, бизнес-функции) | ✅ |
| **ConditionEvaluator** | Выполнение AST, все операторы, 38 тестов | ✅ |
| **ConditionalValidator** | Валидация УО полей, 36 тестов | ✅ |
| **ValueGenerator** | Генерация значений: Faker, ИНН/СНИЛС/телефон, UUID, справочники, 34 теста, 94% | ✅ |

### 🔴 В разработке

| Возможность | Описание |
|-------------|----------|
| **JsonValidator** | Двойная валидация: JSON Schema + SpEL |
| **JsonActualizer** | Применение SchemaDiff к JSON-сценариям |
| **CLI `actualize`** | Команда для актуализации |

### 🟡 Запланировано

| Возможность | Версия |
|-------------|--------|
| Rich UI (прогресс-бары, цветные таблицы) | v0.1.0 |
| Markdown-отчёты с рекомендациями по миграции | v0.1.0 |
| Side-by-side diff для JSON | v0.1.0 |
| Генерация новых сценариев с нуля (combinatorics) | v0.2.0 |
| Интерактивный CLI + Web UI | v1.0.0 |

---

## 💻 Примеры использования

### Анализ изменений между версиями ✅

Сравнить две JSON Schema и получить отчёт:

```bash
python scripts/analyze_changes.py \
  --old-schema data/V070Call1Rq.json \
  --new-schema data/V072Call1Rq.json \
  --format markdown \
  --output reports/changes_070_to_072.md \
  --verbose
```

**Что делает:**
1. Парсит обе схемы → извлекает метаданные каждого поля
2. Сравнивает → находит добавленные, удалённые, изменённые поля
3. Классифицирует → определяет breaking changes и критичность
4. Формирует отчёт в выбранном формате

**Пример результата (Markdown):**

```markdown
# JSON Schema Analysis Report

**Old:** V070Call1Rq  |  **New:** V072Call1Rq

## 📈 Статистика
- Всего изменений: 25
- Breaking changes: 7 ⚠️
- Non-breaking: 18 ✅

## 🔴 Breaking Changes
1. `loanRequest/snils` — REMOVED (required field)
2. `loanRequest/creditAmt` — type changed: integer → string
...
```

**Фильтры:** `--only-critical` (только CRITICAL), `--only-breaking` (только BREAKING)

### Актуализация JSON-сценария 🔴

*(После реализации Этапа 3)*

```bash
python -m src.cli actualize \
  --old-schema data/V070Call1Rq.json \
  --new-schema data/V072Call1Rq.json \
  --scenario data/scenarios/call1_pacl_v070.json \
  --output output/call1_pacl_v072.json \
  --dictionaries data/dictionaries/
```

**Что делает:**
- Добавляет новые обязательные поля с валидными значениями
- Удаляет устаревшие поля
- Преобразует значения при смене типов
- Валидирует результат (JSON Schema + SpEL)
- Сохраняет UUID-связи между Call

### Валидация JSON 🟡

*(После реализации Этапа 3)*

```bash
python -m src.cli validate \
  --schema data/V072Call1Rq.json \
  --json-file output/call1_pacl_v072.json
```

**Что делает:** проверяет JSON по схеме и SpEL-условиям, возвращает ошибки с путями и dqCode.

---

## 🏗️ Как это работает

### Архитектура

Проект построен на **SOLID-принципах** с чётким разделением на слои. Каждый слой решает одну задачу и не зависит от конкретных реализаций соседних слоёв.

```
┌─────────────────────────────────────────────┐
│                  CLI / Scripts              │  ← Тонкая оболочка
├─────────────────────────────────────────────┤
│              ReportFormatter                │  ← Форматирование (text/md/json)
├─────────────────────────────────────────────┤
│              ChangeAnalyzer                 │  ← 3-уровневая классификация
├─────────────────────────────────────────────┤
│          SchemaComparator                   │  ← Сравнение двух схем
├─────────────────────────────────────────────┤
│   SchemaParser │ DictionaryLoader │ SpEL    │  ← Парсеры и загрузчики
├─────────────────────────────────────────────┤
│   VersionInfo │ FieldMetadata │ SchemaDiff  │  ← Модели данных (dataclasses)
└─────────────────────────────────────────────┘
```

### Поток данных (анализ изменений)

```
CLI → SchemaParser → Dict[str, FieldMetadata]
       SchemaComparator → SchemaDiff (added/removed/modified)
       ChangeAnalyzer → AnalysisResult (classified changes)
       ReportFormatter → text / markdown / JSON
```

### Поток данных (актуализация — в разработке)

```
CLI → SchemaDiff (из анализа)
       + старый JSON-сценарий
       → JsonActualizer (применяет изменения)
       → ConditionalValidator (проверяет УО)
       → новый JSON-сценарий
```

**Ключевой принцип:** ядро (сравнение, актуализация, валидация) не знает про CLI и формат отчётов. Это позволяет легко добавлять новые интерфейсы без изменения бизнес-логики.

---

## 📁 Структура проекта

```
json-scenario-generator/
├── config/                 # Конфигурация (AppConfig, пути, логирование)
├── data/                   # Входные данные (не в Git)
│   ├── schemas/            # JSON Schema (любые версии)
│   ├── dictionaries/       # Excel-справочники
│   └── scenarios/          # JSON-сценарии
├── src/                    # Исходный код
│   ├── models/             # Доменные модели (dataclasses + enums)
│   ├── parsers/            # Парсеры (JSON Schema, SpEL)
│   ├── loaders/            # Загрузчики (Excel → Dictionary)
│   ├── core/               # Ядро: сравнение, SpEL, актуализация
│   ├── analyzers/          # Классификация изменений
│   ├── formatters/         # Форматирование отчётов
│   ├── reports/            # Расширенные отчёты (в работе)
│   ├── utils/              # Логирование, JSON, Excel утилиты
│   └── cli/                # CLI-интерфейс
├── tests/                  # Тесты (pytest, 153 unit-теста)
├── scripts/                # CLI-скрипты для запуска
├── docs/                   # Документация
├── output/                 # Выходные файлы (не в Git)
└── deprecated/             # Устаревший код (spel_v0.2.0_evaluator)
```

> 📌 Полная структура с описанием каждого модуля — в [SPECIFICATION.md](docs/SPECIFICATION.md), Раздел 11.

---

## 🧪 Тестирование

**Фреймворк:** pytest + pytest-cov

| Метрика | Значение |
|---------|----------|
| Unit-тестов задекларировано | 250+ |
| Unit-тестов проходит | **247** |
| Pass rate | 100% ✅ |
| Покрытие (этапы 0–2.5) | 100% |
| Покрытие (SpEL) | 100% (AST ✅, Parser ✅, Evaluator ✅, Functions ✅, Validator ✅) |

### Запуск тестов

```bash
pytest                          # Все тесты (247 passed)
pytest -v                       # Подробный вывод
pytest --cov=src                # С покрытием
pytest tests/unit/ -v           # Только unit-тесты
pytest tests/unit/core/test_condition_evaluator.py -v  # ConditionEvaluator (38 тестов)
pytest tests/unit/core/test_conditional_validator.py -v  # ConditionalValidator (36 тестов)
```

### Покрытие по этапам

| Этап | Компоненты | Тестов | Статус |
|------|-----------|--------|--------|
| 0 | Подготовка | — | ✅ |
| 1 | Модели, конфигурация, логирование | 12 | ✅ |
| 2 | Парсеры (SchemaParser, DictionaryLoader) | 31 | ✅ |
| 2.5 | SchemaComparator, ChangeAnalyzer, ReportFormatter | 36 | ✅ |
| 3.1 | SpelAST, SpelParser | 20 | ✅ |
| 3.2 | ConditionEvaluator | 38 | ✅ |
| 3.3 | ConditionalValidator | 36 | ✅ |
| **Итого** | | **247 passed** | ✅ |

---

## 🛠️ Технологии

| Категория | Библиотека | Назначение |
|-----------|-----------|------------|
| JSON | [jsonschema](https://python-jsonschema.readthedocs.io/) 4.20.0 | Валидация JSON Schema |
| Excel | [openpyxl](https://openpyxl.readthedocs.io/) 3.1.2 | Чтение .xlsx справочников |
| Parsing | [pyparsing](https://pyparsing-docs.readthedocs.io/) 3.1.1 | SpEL-парсер |
| CLI | [click](https://click.palletsprojects.com/) 8.1.7 | CLI framework |
| UI | [rich](https://rich.readthedocs.io/) 13.7.0 | Красивый терминальный вывод |
| Logging | [loguru](https://github.com/Delgan/loguru) 0.7.2 | Логирование с ротацией |
| Testing | [pytest](https://docs.pytest.org/) + [Faker](https://faker.readthedocs.io/) | Тестирование и генерация данных |
| Data | [pandas](https://pandas.pydata.org/) 2.2.0 | Табличные данные, Excel-справочники |
| Config | [python-dotenv](https://saurabh-kumar.com/python-dotenv/) 1.0.0 | .env файлы |
| Python | CPython 3.12+ | Язык разработки |

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| [README.md](README.md) | Этот файл — обзор проекта, быстрый старт, примеры |
| [SPECIFICATION.md](docs/SPECIFICATION.md) | 📋 **Полная спецификация** (~2700 строк): модели, алгоритмы, CLI, тесты, SpEL, roadmap, известные проблемы |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 🏗️ Архитектура системы, SOLID-принципы, слои, поток данных |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | 👨‍💻 Руководство разработчика: как добавлять функционал, тестировать, не ломая архитектуру |
| [PRD.md](docs/PRD.md) | 📝 Product Requirements Document — бизнес-требования к продукту |

> 💡 **С чего начать чтение?**
> - **Новичкам:** этот README → [ARCHITECTURE.md](docs/ARCHITECTURE.md) → [DEVELOPMENT.md](docs/DEVELOPMENT.md)
> - **Разработчикам:** [SPECIFICATION.md](docs/SPECIFICATION.md) (Разделы 4–7 — модели и алгоритмы)
> - **Менеджерам:** этот README → [PRD.md](docs/PRD.md) → раздел 13 SPECIFICATION (Roadmap)

---

## 🗺️ Roadmap

### Текущий статус: 🚧 Этап 6 (ValueGenerator) — в работе

```
✅ Этап 0: Подготовка                          100%
✅ Этап 1: Базовая инфраструктура               100%
✅ Этап 2: Парсеры и загрузчики                 100%
✅ Этап 2.5: Анализаторы                        100%
✅ Этап 3: SpEL AST и Parser                    100%
✅ Этап 4: SpEL Functions                       100%
✅ Этап 5: ConditionEvaluator + Validator       100%
🟡 Этап 6: ValueGenerator                       0%    ← ТЕКУЩИЙ ФОКУС
🟡 Этап 7: JsonActualizer                      0%
🟡 Этап 8: JsonValidator                       0%
🟡 Этап 9: CLI интеграция                      0%
```

### Прогресс по компонентам

| Задача | Компонент | Приоритет | Статус |
|--------|-----------|-----------|--------|
| SpelAST | `src/core/spel_ast.py` | 🔴 P0 | ✅ 52 NodeType |
| SpelParser | `src/core/spel_parser.py` | 🔴 P0 | ✅ 34 оператора |
| SpelFunctions | `src/core/spel_functions.py` | 🔴 P0 | ✅ 34/34 функции |
| ConditionEvaluator | `src/core/condition_evaluator.py` | 🔴 P0 | ✅ 38 тестов |
| ConditionalValidator | `src/core/conditional_validator.py` | 🔴 P0 | ✅ 36 тестов |
| ValueGenerator | `src/core/value_generator.py` | 🔴 P0 | 🔴 Ожидает |
| JsonActualizer | `src/core/json_actualizer.py` | 🔴 P0 | 🔴 Ожидает |
| JsonValidator | `src/core/json_validator.py` | 🟡 P1 | 🔴 Ожидает |
| CLI `actualize` | `src/cli/` | 🟡 P1 | 🔴 Ожидает |

> **Итого:** ~75-80% готовности MVP, ~5-7 дней до v0.1.0

### Будущие версии

| Версия | Фокус | Статус |
|--------|-------|--------|
| **v0.1.0** | Анализ + актуализация + валидация | 🔴 В разработке |
| **v0.2.0** | Генерация новых сценариев с нуля | ⏳ Запланировано |
| **v1.0.0** | YAML-конфигурация, интерактивный CLI, Web UI | 💡 Идея |

---

## 🐛 Известные проблемы

| # | Проблема | Серьёзность | Статус |
|---|----------|-------------|--------|
| 1 | `json_utils.py` использует Draft7Validator вместо Draft201909Validator | 🟡 Средняя | ✅ Исправлено (11.05.2026) |
| 2 | Нет интеграционных тестов (только unit-тесты) | 🟡 Средняя | Добавить E2E |
| 3 | Нет test fixtures | 🟡 Низкая | Добавить fixtures |
| 4 | Backup файлы в репо (.backup) | 🟡 Низкая | Удалить |
| 5 | Deprecated code в src/ | 🟡 Низкая | Переместить/удалить |

> ✅ **Исправлено в v0.1.0:** Broken imports, Test-AST mismatch, SpEL parser incomplete, SpelFunctions (4/34 → 34/34), ConditionEvaluator, ConditionalValidator. Все 247 тестов проходят.

Подробности и рекомендации — в [SPECIFICATION.md](docs/SPECIFICATION.md), Раздел 14.

---

## 🤝 Contributing

Pull requests приветствуются! Проект в активной разработке.

### Workflow

```bash
# 1. Fork и клонирование
git clone https://github.com/Chemixx/json-scenario-generator.git
cd json-scenario-generator

# 2. Feature branch
git checkout -b feature/add-json-actualizer

# 3. Разработка + тесты
pytest

# 4. Коммит (Conventional Commits)
git commit -m "feat(core): implement JsonActualizer for added fields"

# 5. Push и Pull Request
git push origin feature/add-json-actualizer
```

### Conventional Commits

| Тип | Описание | Пример |
|-----|----------|--------|
| `feat:` | Новая функциональность | `feat(core): add ValueGenerator` |
| `fix:` | Исправление бага | `fix(parsers): handle nested arrays` |
| `docs:` | Изменения документации | `docs: update SPECIFICATION` |
| `test:` | Добавление тестов | `test(core): cover JsonActualizer` |
| `refactor:` | Рефакторинг | `refactor: simplify SchemaComparator` |
| `chore:` | Зависимости, конфигурация | `chore: bump jsonschema to 4.20.0` |

### Правила для разработчиков

1. **Не смешивать слои** — парсер не формирует отчёты, анализатор не читает файлы
2. **Сначала модель → потом логика** — новая сущность? Добавьте dataclass в `src/models/`
3. **Сначала тест → потом код** — опишите ожидаемое поведение, затем реализуйте
4. **100% покрытие** для нового кода
5. **Используйте logger**, а не print

> 📌 Подробности — в [DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

## 📄 Лицензия

[MIT License](LICENSE)

---

## 📬 Контакты

| | |
|---|---|
| **Автор** | Chemixx |
| **GitHub** | [Chemixx/json-scenario-generator](https://github.com/Chemixx/json-scenario-generator) |
| **Issues** | [GitHub Issues](https://github.com/Chemixx/json-scenario-generator/issues) |

---

## 📋 Changelog

<details>
<summary><b>0.1.0-dev</b> — В разработке</summary>

### ✅ Завершено

- **Этап 0:** Подготовка окружения (Python 3.12+, venv, зависимости, структура)
- **Этап 1:** Базовая инфраструктура
  - AppConfig с путями к data/, output/, logs/
  - loguru с консольным и файловым выводом, ротация 10 MB
  - Модели данных: VersionInfo, FieldMetadata, ConditionalRequirement, SchemaDiff, enums
  - 12 unit-тестов
- **Этап 2:** Парсеры и загрузчики
  - SchemaParser — JSON Schema Draft 2019-09, рекурсивный обход, conditions
  - DictionaryLoader — Excel-справочники (классический + групповой формат), кэширование
  - 31 unit-тест
- **Этап 2.5:** Анализаторы
  - SchemaComparator — сравнение схем, детальный разбор изменений constraints
  - ChangeAnalyzer — 3-уровневая классификация (ChangeType + BreakingLevel + ImpactLevel)
  - ReportFormatter — text / markdown / json
  - CLI `analyze_changes.py` — сравнение любых версий с фильтрами
  - 101 unit-тест
- **Этап 3:** SpEL AST и Parser
  - SpelAST — 52 NodeType, 13 основных узлов
  - SpelParser — парсинг SpEL → AST, поддержка 34 операторов (pyparsing)
  - 20 unit-тестов
- **Этап 4:** SpEL Functions
  - 34/34 функции (Date API, String API, бизнес-функции)
- **Этап 5:** ConditionEvaluator + ConditionalValidator
  - ConditionEvaluator — выполнение AST, все операторы, 38 тестов ✅
  - ConditionalValidator — валидация УО полей, 36 тестов ✅

**Всего тестов:** 247 passed (100%)

### 🔧 Исправлено
- **TD-8:** `json_utils.py` — заменён `Draft7Validator` на `Draft201909Validator`

### 🔴 В работе

- **Этап 6:** ValueGenerator — генерация валидных значений (Faker, UUID-кэш, ИНН, СНИЛС)
- **Этап 7:** JsonActualizer — применение SchemaDiff к JSON-сценариям

### 🟡 Запланировано

- **Этап 8:** JsonValidator — двойная валидация (JSON Schema + SpEL)
- **Этап 9:** CLI команды (`actualize`, `validate`)
- **Этап 10:** ScenarioGenerator — комбинаторика сценариев

</details>

---

<p align="center">
  <sub>Последнее обновление: 7 мая 2026 · Версия: 0.1.0-dev · Статус: 🚧 Этап 6 в работе (~75-80% MVP)</sub>
</p>
