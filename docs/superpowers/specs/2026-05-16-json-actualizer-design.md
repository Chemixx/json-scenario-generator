# JsonActualizer — Design Spec

**Дата:** 2026-05-16
**Этап:** 7 (P0 — Критично для MVP)
**Статус:** Draft

---

## Контекст

Когда JSON-схема банка обновляется (например, v0.70 → v0.72), существующие тестовые сценарии ломаются: появляются новые обязательные поля, удаляются старые, меняются типы и ограничения. JsonActualizer автоматизирует миграцию JSON-сценария на новую версию схемы.

JsonActualizer — потребитель `SchemaDiff` (от SchemaComparator) и `ValueGenerator`. Его результат валидируется `ConditionalValidator`. Следующий в цепочке — `JsonValidator` (P1).

---

## Архитектурные решения

### ADR-1: Подход Pragmatic Middle (Подход C)

Один класс `JsonActualizer` с приватными методами по ответственности. Не монолит (Подход A), не стратегия (Подход B). Баланс между простотой и тестируемостью.

**Почему:** Один файл, чистый публичный API, приватные методы тестируются косвенно. При необходимости рефакторится в Strategy Pattern.

### ADR-2: Строгая валидация значений

При модификации полей старое значение сохраняется только если оно проходит все новые ограничения (тип, pattern, minLength, maxLength, enum, min/max). Иначе — перегенерация через ValueGenerator.

**Почему:** Максимальная корректность результата. Смягчение ограничений сохраняет старое значение (оно всё ещё валидно), ужесточение — перегенерирует.

### ADR-3: Вычисление УО-условий при добавлении

При добавлении нового УО-поля: вычислить SpEL-условие через ConditionEvaluator. Если true — сгенерировать значение. Если false — пропустить (null).

**Почему:** Не генерируем лишние данные. Валидация ConditionalValidator в конце — финальная проверка.

### ADR-4: Три уровня отката

| Уровень | Ситуация | Поведение |
|---------|----------|-----------|
| Поле (по умолчанию) | Ошибка генерации/преобразования | Пропустить, записать в errors, продолжить |
| Сценарий | Критическая ошибка структуры | Откат к backup, rolled_back=True |
| Настройка | `config.rollback = "full"` | Любая ошибка → полный откат |

**Почему:** Гибкость для разных сценариев использования. WebUI может выбрать полный откат, CLI — полевой.

### ADR-5: Обнаружение переименований через метаданные

Переименование поля (creditAmt → loanAmount) определяется по совпадению ≥3 из 5 атрибутов FieldMetadata: field_type, dictionary, format, parent_path, constraints. Явный field_mapping — override эвристики.

**Почему:** SchemaComparator видит переименование как «удаление + добавление». Без обнаружения переименований значение теряется. Эвристика на метаданных — надёжнее угадывания, а mapping — для крайних случаев.

### ADR-6: Изоляция модуля

`actualize()` никогда не бросает исключение наружу. Все ошибки упакованы в `ActualizationResult.errors`. Даже полный откат возвращает результат с `rolled_back=True`.

**Почему:** Поломка JsonActualizer не должна ломать приложение.

---

## Модели данных

### ActualizerConfig

```python
@dataclass
class ActualizerConfig:
    locale: str = "ru_RU"
    seed: Optional[int] = None
    default_array_size: int = 1
    faker: Optional[Faker] = None
    uuid_cache: Dict[str, str] = field(default_factory=dict)
    strict_inn: bool = True
    strict_snils: bool = False
    rollback: str = "field"  # "field" | "full" | "none"
    generate_report: bool = True
    report_format: str = "dataclass"  # "dataclass" | "markdown" | "both"
    field_mapping: Optional[Dict[str, str]] = None  # override для обнаружения переименований
```

### ActualizationChange

```python
@dataclass
class ActualizationChange:
    path: str                          # Путь поля
    change_type: str                   # "added" | "removed" | "modified" | "modified_preserved" | "modified_regenerated" | "renamed" | "renamed_regenerated" | "renamed_generated" | "skipped" | "error"
    old_value: Any = None              # Старое значение (None для added)
    new_value: Any = None              # Новое значение (None для removed)
    reason: str = ""                   # Почему изменено
    severity: str = "info"             # "info" | "warning" | "error"
```

### ActualizationResult

```python
@dataclass
class ActualizationResult:
    actualized_data: Dict[str, Any]          # Результирующий JSON
    changes: List[ActualizationChange]       # Все изменения
    validation_errors: List[ValidationError]  # Ошибки ConditionalValidator
    errors: List[ActualizationChange]       # Только ошибки (severity="error")
    rolled_back: bool = False                # Был ли полный откат

    def to_markdown(self) -> str:
        """Генерация Markdown-отчёта. Вызывается только если report_format включает 'markdown'."""
        ...
```

### RenamePair (внутренняя модель)

```python
@dataclass
class RenamePair:
    old_path: str
    new_path: str
    old_meta: FieldMetadata
    new_meta: FieldMetadata
    match_score: int  # Количество совпадающих атрибутов (3-5)
```

---

## Публичный API

```python
class JsonActualizer:
    def __init__(
        self,
        config: Optional[ActualizerConfig] = None,
        dictionary_loader: Optional[DictionaryLoader] = None,
    ) -> None: ...

    def actualize(
        self,
        old_json: Dict[str, Any],
        schema_diff: SchemaDiff,
        new_schema: Dict[str, FieldMetadata],
    ) -> ActualizationResult: ...

    def actualize_batch(
        self,
        scenarios: List[Dict[str, Any]],
        schema_diff: SchemaDiff,
        new_schema: Dict[str, FieldMetadata],
    ) -> List[ActualizationResult]: ...

    def actualize_from_paths(
        self,
        scenario_path: Path,
        old_schema_path: Path,
        new_schema_path: Path,
    ) -> ActualizationResult: ...
```

---

## Приватные методы

### Навигация по JSON

```python
def _navigate_path(self, data: Dict, path: str) -> Any: ...
def _set_field_value(self, data: Dict, path: str, value: Any) -> None: ...
def _delete_field(self, data: Dict, path: str) -> bool: ...
```

Пути: `loanRequest/applicant/income` (вложенные dict), `loanRequest/applicants[]/income` (массив), `loanRequest/applicants[0]/income` (конкретный индекс). `_set_field_value` автоматически создаёт промежуточные объекты. Если массив пуст при `[]`, создаётся один элемент и значение устанавливается в него.

### Обработка изменений

```python
def _detect_renames(
    self,
    removed: List[FieldChange],
    added: List[FieldChange],
    field_mapping: Optional[Dict[str, str]] = None,
) -> Tuple[List[RenamePair], List[FieldChange], List[FieldChange]]: ...

def _process_renames(self, result, renames, changes, errors) -> None: ...
def _process_removed_fields(self, result, removed_fields, changes, errors) -> None: ...
def _process_added_fields(self, result, added_fields, new_schema, changes, errors) -> None: ...
def _process_modified_fields(self, result, modified_fields, new_schema, changes, errors) -> None: ...
```

### Генерация и преобразование значений

```python
def _generate_value(self, field_meta: FieldMetadata, context_data: Dict) -> Any: ...
def _transform_value(self, old_value: Any, old_meta: FieldMetadata, new_meta: FieldMetadata) -> Any: ...
def _validate_value(self, value: Any, meta: FieldMetadata) -> bool: ...
```

**`_validate_value` проверяет ограничения в следующем порядке:**
1. `field_type` — тип значения соответствует типу поля (isinstance)
2. `enum` — значение входит в список допустимых
3. `pattern` — значение соответствует regex
4. `minLength / maxLength` — длина строки в диапазоне
5. `minimum / maximum` — число в диапазоне
6. Если хотя бы одна проверка не пройдена → `False`, старое значение перегенерируется

**`_transform_value` — правила преобразования типов:**
| Старый тип | Новый тип | Правило |
|------------|-----------|---------|
| integer | string | `str(old_value)` |
| number | string | `str(old_value)` |
| boolean | string | `"true"` / `"false"` |
| string | integer | `int(old_value)`, ValueError → перегенерация |
| string | number | `float(old_value)`, ValueError → перегенерация |
| string | boolean | `"true"/"1"/"yes"` → True, остальное → False |
| любые другие | любые другие | Перегенерация через ValueGenerator |

При ошибке преобразования → `TransformError`, значение пропускается (severity=error).

### УО-поля

```python
def _evaluate_condition(self, condition: ConditionalRequirement, data: Dict) -> bool: ...
```

### Валидация и отчёт

```python
def _validate_result(self, data: Dict, schema: Dict[str, FieldMetadata]) -> List[ValidationError]: ...  # REMOVED in Phase 8 — replaced by JsonValidator
def _build_report(self, result: ActualizationResult) -> str: ...
```

---

## Алгоритм `actualize()`

```
1. result = deepcopy(old_json), backup = deepcopy(old_json)
2. renames, truly_removed, truly_added = _detect_renames(
       diff.removed_fields, diff.added_fields, config.field_mapping)
3. _process_renames(result, renames, changes, errors)
4. _process_removed_fields(result, truly_removed, changes, errors)
5. _process_added_fields(result, truly_added, new_schema, changes, errors)
6. _process_modified_fields(result, diff.modified_fields, new_schema, changes, errors)
7. validation_errors = _validate_result(result, new_schema)  # REMOVED — validation now via JsonValidator
8. Возврат ActualizationResult
```

Порядок важен: переименования → удаление → добавление → модификация. Удаление перед добавлением освобождает пути.

При критической ошибке (StructureError) — откат к backup, `rolled_back=True`.

---

## Обнаружение переименований (`_detect_renames`)

1. Если передан `field_mapping` — используем напрямую, без эвристики.
2. Для каждого removed-поля ищем лучшее совпадение среди added-полей по метаданным:
   - `field_type` совпадает → +1
   - `dictionary` совпадает → +1
   - `format` совпадает → +1
   - `parent_path` совпадает → +1
   - `constraints` пересекаются (хотя бы 1 общий ключ с совпадающим значением) → +1
3. Порог: ≥ 3 из 5 → совпадение.
4. Жадный алгоритм: одно removed-поле — одно added-поле (по убыванию score).
5. Возвращает: `(matched_pairs, truly_removed, truly_added)`

---

## Обработка ошибок

### Типы ошибок

| Тип | severity | Поведение |
|-----|----------|-----------|
| `ValueGenerationError` | error | Пропустить поле, записать в errors |
| `TransformError` | error | Пропустить поле, записать в errors |
| `ConditionError` | error | Пропустить поле, записать в errors |
| `ValidationWarning` | warning | Записать в changes, продолжить |
| `StructureError` | critical | Полный откат к backup |

### Откат

- `rollback="field"` (по умолчанию): ошибка поля → пропустить, ошибка структуры → полный откат
- `rollback="full"`: любая ошибка → полный откат
- `rollback="none"`: никогда не откатывать, все ошибки в errors

---

## Зависимости

```
JsonActualizer
  ├── ValueGenerator          (генерация значений)
  │     └── GeneratorConfig
  │     └── DictionaryLoader
  ├── ConditionalValidator     (валидация УО-полей)
  │     └── ConditionEvaluator
  │     └── SpelParser
  ├── SchemaComparator         (через SchemaDiff — не вызывается напрямую)
  ├── json_utils               (load_json / save_json для from_paths)
  └── logger                   (get_logger)
```

---

## Структура файлов

| Файл | Действие |
|------|----------|
| `src/core/json_actualizer.py` | Создать |
| `tests/unit/core/test_json_actualizer.py` | Создать |
| `src/core/__init__.py` | Модифицировать (добавить экспорты) |
| `.planning/STATE.md` | Обновить статус Этапа 7 |
| `CLAUDE.md` | Обновить статус |
| `TODO.md` | Отметить задачи |

Модели `ActualizerConfig`, `ActualizationChange`, `ActualizationResult`, `RenamePair` — внутри `json_actualizer.py`, не в `models/`. Паттерн проекта: `GeneratorConfig` рядом с `ValueGenerator`.

---

## Тесты: 31 юнит-тест

| Группа | Кол-во | Описание |
|--------|--------|----------|
| Навигация по путям | 4 | navigate, set, delete, массивы |
| Добавление полей | 5 | О, УО (true/false), Н, ошибка |
| Удаление полей | 3 | листовое, вложенное, несуществующее |
| Модификация полей | 5 | сохранено, перегенерировано, тип, pattern, смягчение |
| Переименование | 4 | detect 3+, detect <3, mapping override, перенос значения |
| Обработка ошибок | 4 | field, full, critical, batch |
| Интеграция ValueGenerator | 3 | UUID, dictionary, массив |
| ActualizationResult | 3 | формирование, markdown, generate_report=False |

---

## Верификация

1. `pytest tests/unit/core/test_json_actualizer.py -v` — все 31 тест проходят
2. `pytest --cov=src/core/json_actualizer.py --cov-report=term-missing` — покрытие > 90%
3. `mypy src/core/json_actualizer.py` — без ошибок типов
4. `flake8 src/core/json_actualizer.py` — без замечаний
5. Интеграционная проверка: загрузить две схемы, получить SchemaDiff, вызвать `actualize()` — результат валиден