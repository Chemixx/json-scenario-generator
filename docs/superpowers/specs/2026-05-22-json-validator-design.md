# JsonValidator — Design Spec

**Дата:** 2026-05-22 (обновлено после брейншторминга)
**Этап:** 8 (P0 — Критично для MVP)
**Статус:** Approved

---

## Контекст

JsonValidator — оркестратор валидации JSON-данных против схемы. Объединяет 5 независимых шагов проверок: структурная валидация (JSON Schema), обязательные поля (О), условно обязательные поля (УО), ограничения значений (constraints) и справочники. Это следующий компонент после JsonActualizer (Этап 8, P0).

JsonValidator НЕ дублирует логику ConditionalValidator — делегирует ему Шаг 3. JsonValidator НЕ генерирует значения — только проверяет существующие. JsonValidator — единственный валидатор в проекте: `_validate_result()` убирается из JsonActualizer.

---

## Архитектурные решения

### ADR-1: Оркестратор с делегированием (Pragmatic Middle)

Один класс `JsonValidator` с приватными методами по шагам валидации. Шаг 3 делегируется `ConditionalValidator`. Не монолит (все шаги в одном методе), не стратегия (отдельный класс на шаг). Баланс между простотой и расширяемостью.

**Почему:** Пять шагов — это фиксированный набор проверок, а не плагинная архитектура. Делегирование ConditionalValidator исключает дублирование. При необходимости шаги рефакторятся в Strategy.

### ADR-2: Конфигурируемые шаги через ValidatorConfig

Пользователь включает/выключает шаги через `ValidatorConfig`. По умолчанию включены шаги 1-4, шаг 5 (справочники) выключен — требует загрузки данных.

**Почему:** Не всегда нужны все проверки. CLI может запускать только schema + conditional. Справочники требуют Excel-файл, которого может не быть.

### ADR-3: Иерархия ошибок с общим базовым типом

Все ошибки валидации наследуют `BaseValidationError` с общими полями: path, message, severity, step. Конкретные типы добавляют специфичные поля (dq_code, constraint_name, dictionary_name). `ValidationResult` собирает ошибки по типам. `ConditionalError` оборачивает `ValidationError` из ConditionalValidator (не ломает API).

**Почему:** Единый интерфейс для обхода всех ошибок + типобезопасный доступ к специфичным полям. CLI может фильтровать/группировать ошибки по шагу. Обёртка ConditionalError сохраняет совместимость с ConditionalValidator.

### ADR-4: Строгий и мягкий режимы (strict / lenient)

`ValidatorConfig.strict = True`: ошибки constraints — severity="error" (валидация не пройдена). `strict = False` (по умолчанию): ошибки constraints — severity="warning" (валидация пройдена, но с замечаниями). Все остальные шаги всегда выдают severity="error".

**Почему:** Constraints в JSON Schema могут быть рекомендательными (например, maxLength для строки, которую front-adapter всё равно обрежет). Мягкий режим позволяет пройти валидацию с warnings.

### ADR-5: Изоляция модуля

`validate()` никогда не бросает исключение наружу. Все ошибки упакованы в `ValidationResult`. Даже критическая ошибка загрузки справочника возвращает результат с dictionary_errors.

**Почему:** Поломка одного шага не должна блокировать остальные. Аналогично ADR-6 из JsonActualizer.

### ADR-6: Два входных формата схемы

JsonValidator принимает либо raw JSON Schema dict (для Шага 1), либо Dict[str, FieldMetadata] (для Шагов 2-5), либо оба. Если передан только raw JSON Schema — Шаги 2-5 пропускаются (нет метаданных). Если переданы только метаданные — Шаг 1 пропускается (нет raw schema).

**Почему:** Парсинг JSON Schema в FieldMetadata — отдельный этап (SchemaParser). Пользователь может иметь только метаданные без raw schema, и наоборот.

### ADR-7: DQ-коды как настроечный параметр (include_dq_codes)

DQ-коды (Data Quality) — числовые коды проверок из справочника Приложения 5 спецификации front-adapter (например, 12750001, 12750037). Параметр `include_dq_codes` управляет включением DQ-кодов:
- `False` (по умолчанию): `dq_code` во всех ошибках = None
- `True`: `dq_code` заполняется из FieldMetadata и ConditionalRequirement

**Почему:** DQ-коды — доменно-специфичная информация. SchemaParser парсит 3 DQ-поля (alwaysRequiredDqCode, conditionalDqCode, dictionaryDqCode) из JSON Schema (исправлено перед реализацией JsonValidator).

### ADR-8: Единственный валидатор — JsonValidator заменяет _validate_result()

JsonActualizer._validate_result() удаляется. JsonValidator — единственная точка валидации в проекте. Вызывающий код (CLI) решает, когда валидировать.

**Почему:** SRP — JsonActualizer отвечает только за актуализацию. Дублирование УО-валидации в двух местах — источник багов. Валидация конфигурируется через ValidatorConfig.

### ADR-9: Общая логика constraints через constraint_utils.py

Проверки ограничений (10 типов) выделены в `src/utils/constraint_utils.py`. JsonValidator._check_constraints() и JsonActualizer._validate_value() обе используют эти функции.

**Почему:** DRY — логика проверок в одном месте. При добавлении нового типа ограничения — одно изменение. Bugfix применяется один раз.

### ADR-10: Null vs missing — различие для О и УО полей

RequiredError и ConditionalError содержат поле `requirement_type: "missing" | "null"`. Сообщения различают «поле отсутствует» и «поле = null». ConditionalValidator обновлён для передачи requirement_type.

**Почему:** Точная диагностика: пользователь знает, что именно делать — добавить поле или заполнить существующее. При автоматической генерации сценариев разница критична.

### ADR-11: Независимая реализация Шага 1

JsonValidator реализует Шаг 1 напрямую через Draft201909Validator, без зависимости от json_utils.validate_json_schema().

**Почему:** Полный контроль над форматом ошибок (SchemaError с normalized path). Независимость от формата возвращаемого get_validation_errors(). Меньше связанности между модулями.

### ADR-12: Два формата вывода ошибок

`to_summary(format="tree")` — дерево с группировкой по родительским объектам (по умолчанию). `to_summary(format="flat")` — плоский список с тегами шагов. Формат настраивается через `ValidatorConfig.output_format`.

**Почему:** Дерево — для интерактивной работы (наглядно, видна вложенность). Плоский — для CI/логов (легко grep'ать).

### ADR-13: Автодетект Call из метаданных схемы

validate_from_paths() автоматически извлекает call из JSON Schema: `stageName` (call1), `version` (072), `direction` (request). Fallback: `callCdExt` из JSON-сценария.

**Почему:** Не нужно угадывать call из имени файла. JSON Schema всегда содержит stageName/version/direction в корне.

---

## Решённые вопросы

### RQ-1: DQ-коды (РЕШЕНО)

DQ-коды — числовые коды (12750001...), привязаны к полю + версии loanRequestVersion. В JSON Schema dqCode отсутствует, берётся из Приложения 5 (XLSX). SchemaParser исправлен: парсит 3 DQ-поля (alwaysRequiredDqCode, conditionalDqCode, dictionaryDqCode).

**Решение:** DQ-коды пробрасываются как информационное поле. Полный маппинг DQ_CHECK — Post-MVP.

### RQ-2: Переиспользование ValidationError из ConditionalValidator (РЕШЕНО)

**Решение:** Вариант A — ConditionalValidator возвращает старый ValidationError, JsonValidator оборачивает его в ConditionalError. Не ломает существующий API. ConditionalError.original_error хранит ссылку.

### RQ-3: Проверка null vs отсутствующее поле (РЕШЕНО)

**Решение:** Оба варианта = ошибка (severity="error"). Сообщение различает «поле отсутствует» (requirement_type="missing") и «поле = null» (requirement_type="null"). Касается RequiredError (Шаг 2) и ConditionalError (Шаг 3). ConditionalValidator обновлён для передачи requirement_type.

### RQ-4: Валидация справочников (РЕШЕНО)

**Решение:** JsonValidator напрямую использует DictionaryLoader (не SpelFunctions.is_dictionary_value — заглушка). _check_dictionaries() загружает справочник и проверяет contains_code/contains_name.

### RQ-5: Поведение при ошибках шагов (РЕШЕНО)

**Решение:** Все включённые шаги выполняются всегда, независимо от ошибок на предыдущих. Ошибки суммируются. is_valid = error_count == 0. Для иерархического вывода: если отсутствует родительский объект, ошибки внутри него группируются под ним.

### RQ-6: Нормализация JSON Path (РЕШЕНО)

**Решение:** $.loanRequest.creditAmt → loanRequest/creditAmt при создании SchemaError.path. Оригинальный JSON Path сохраняется в SchemaError.schema_path.

### RQ-7: Пакетная валидация (РЕШЕНО)

**Решение:** validate_batch() существует, возвращает List[ValidationResult]. Один РКК-сценарий = несколько Call-ов (call0..call6+), состав определяется пользователем.

---

## Модели данных

### ValidatorConfig

```python
@dataclass
class ValidatorConfig:
    """Конфигурация валидатора."""
    check_schema: bool = True        # Шаг 1 — структурная валидация
    check_required: bool = True      # Шаг 2 — обязательные поля (О)
    check_conditional: bool = True   # Шаг 3 — условно обязательные (УО)
    check_constraints: bool = True  # Шаг 4 — ограничения значений
    check_dictionaries: bool = False # Шаг 5 — справочники (требует DictionaryLoader)
    include_dq_codes: bool = False   # DQ-коды в ошибках
    strict: bool = False            # strict: constraint=error, lenient: constraint=warning
    output_format: str = "tree"     # "tree" | "flat"
    show_full_paths: bool = True    # Полные пути в tree-формате (иначе короткие имена)
```

### Иерархия ошибок валидации

```python
@dataclass
class BaseValidationError:
    """Базовая ошибка валидации."""
    path: str           # "loanRequest/creditAmt"
    message: str        # Человекочитаемое описание
    severity: str       # "error" | "warning"
    step: str           # "schema" | "required" | "conditional" | "constraint" | "dictionary"


@dataclass
class SchemaError(BaseValidationError):
    """Ошибка структурной валидации (Шаг 1)."""
    schema_path: str = ""    # Оригинальный JSON Path "$.loanRequest.creditAmt"
    validator: str = ""     # Тип валидатора jsonschema ("required", "type", "format")
    expected: Any = None     # Ожидаемое значение/тип
    actual: Any = None      # Фактическое значение/тип

    def __post_init__(self):
        self.step = "schema"


@dataclass
class RequiredError(BaseValidationError):
    """Ошибка обязательного поля (Шаг 2)."""
    dq_code: Optional[int] = None
    requirement_type: str = "missing"  # "missing" | "null"

    def __post_init__(self):
        self.step = "required"


@dataclass
class ConditionalError(BaseValidationError):
    """Ошибка условно обязательного поля (Шаг 3).
    Обёртка над ValidationError из ConditionalValidator."""
    original_error: Optional[Any] = None  # ValidationError из conditional_validator
    dq_code: Optional[int] = None
    requirement_type: str = "missing"     # "missing" | "null"

    def __post_init__(self):
        self.step = "conditional"


@dataclass
class ConstraintError(BaseValidationError):
    """Ошибка ограничения значения (Шаг 4)."""
    constraint_name: str = ""    # "minLength", "maximum", "enum"...
    constraint_value: Any = None
    actual_value: Any = None

    def __post_init__(self):
        self.step = "constraint"


@dataclass
class DictionaryError(BaseValidationError):
    """Ошибка справочного значения (Шаг 5)."""
    dictionary_name: str = ""
    actual_value: Any = None
    dq_code: Optional[int] = None

    def __post_init__(self):
        self.step = "dictionary"
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    """Результат валидации JSON-данных."""
    is_valid: bool = True
    schema_errors: List[SchemaError] = field(default_factory=list)
    required_errors: List[RequiredError] = field(default_factory=list)
    conditional_errors: List[ConditionalError] = field(default_factory=list)
    constraint_errors: List[ConstraintError] = field(default_factory=list)
    dictionary_errors: List[DictionaryError] = field(default_factory=list)
    statistics: ValidationStatistics = field(default_factory=ValidationStatistics)

    @property
    def all_errors(self) -> List[BaseValidationError]:
        """Все ошибки в одном плоском списке."""
        return (
            self.schema_errors + self.required_errors
            + self.conditional_errors + self.constraint_errors
            + self.dictionary_errors
        )

    @property
    def error_count(self) -> int:
        """Количество ошибок с severity='error'."""
        return sum(1 for e in self.all_errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        """Количество предупреждений (severity='warning')."""
        return sum(1 for e in self.all_errors if e.severity == "warning")

    def to_summary(self, format: str = "tree") -> str:
        """Текстовое резюме для CLI. format: 'tree' | 'flat'."""
        ...

    def to_dict(self) -> dict:
        """Сериализация в dict для JSON API."""
        ...
```

### ValidationStatistics

```python
@dataclass
class ValidationStatistics:
    """Статистика валидации."""
    total_fields: int = 0
    required_fields: int = 0
    conditional_fields: int = 0
    constraint_fields: int = 0
    dictionary_fields: int = 0
    schema_error_count: int = 0
    required_error_count: int = 0
    conditional_error_count: int = 0
    constraint_error_count: int = 0
    constraint_warning_count: int = 0
    dictionary_error_count: int = 0
    duration_ms: float = 0.0
```

---

## Публичный API

```python
class JsonValidator:
    def __init__(
        self,
        config: Optional[ValidatorConfig] = None,
        dictionary_loader: Optional[DictionaryLoader] = None,
    ) -> None: ...

    def validate(
        self,
        data: Dict[str, Any],
        raw_schema: Optional[Dict[str, Any]] = None,
        schema_fields: Optional[Dict[str, FieldMetadata]] = None,
    ) -> ValidationResult: ...

    def validate_batch(
        self,
        scenarios: List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], Optional[Dict[str, FieldMetadata]]]],
    ) -> List[ValidationResult]: ...

    def validate_from_paths(
        self,
        json_path: Path,
        schema_path: Path,
    ) -> ValidationResult: ...
```

### Семантика параметров validate()

| Параметр | Описание | Нужен для шагов |
|----------|----------|-----------------|
| `data` | JSON-данные для валидации | Все шаги |
| `raw_schema` | Raw JSON Schema dict | Шаг 1 |
| `schema_fields` | Метаданные полей {path: FieldMetadata} | Шаги 2-5 |

Если `raw_schema = None` — Шаг 1 пропускается.
Если `schema_fields = None` — Шаги 2-5 пропускаются.
Если оба `None` — возвращается ValidationResult с is_valid=True.

### validate_batch()

```python
def validate_batch(
    self,
    scenarios: List[Tuple[data, raw_schema, schema_fields]],
) -> List[ValidationResult]:
    """Валидирует несколько сценариев (Call-ов) независимо.
    Один РКК-сценарий = call0,call1,call2,call3,call5,call4,call6(result).
    Состав определяется пользователем."""
    return [self.validate(data, raw_schema, schema_fields) for data, raw_schema, schema_fields in scenarios]
```

### validate_from_paths() — автодетект Call

```python
def validate_from_paths(self, json_path: Path, schema_path: Path) -> ValidationResult:
    # 1. Загрузить JSON Schema
    raw_schema = load_json(schema_path)

    # 2. Извлечь метаданные из корня схемы
    #    stageName="call1", version="072", direction="request"
    meta = self._extract_schema_metadata(raw_schema)

    # 3. Парсить схему → schema_fields
    schema_fields = SchemaParser.parse_schema(raw_schema, schema_path)

    # 4. Загрузить JSON-данные
    data = load_json(json_path)

    # 5. Валидировать
    return self.validate(data, raw_schema=raw_schema, schema_fields=schema_fields)
```

`_extract_schema_metadata()` извлекает из корня JSON Schema:
- `stageName` → call (например, "call1")
- `version` → версия (например, "072")
- `direction` → направление (например, "request")
- `dataQuality` → флаг DQ

Fallback: если stageName отсутствует — извлечь `callCdExt` из JSON-сценария и маппить через справочник.

---

## Приватные методы

### Шаг 1: _check_schema

```python
def _check_schema(self, data, raw_schema) -> List[SchemaError]:
    """Структурная валидация через Draft201909Validator (независимая реализация)."""
    validator_cls = jsonschema.validators.Draft201909Validator
    validator = validator_cls(raw_schema)
    errors = []
    for error in validator.iter_errors(data):
        path = self._normalize_json_path(error.json_path)
        errors.append(SchemaError(
            path=path,
            message=error.message,
            severity="error",
            step="schema",
            schema_path=error.json_path,
            validator=error.validator,
            expected=error.validator_value,
            actual=error.instance,
        ))
    return errors
```

Нормализация JSON Path: `$.loanRequest.creditAmt` → `loanRequest/creditAmt` (убрать `$`, заменить `.` на `/`).

### Шаг 2: _check_required

```python
def _check_required(self, data, schema_fields) -> List[RequiredError]:
    """Проверка обязательных (О) полей. Различает missing/null."""
    errors = []
    for path, field_meta in schema_fields.items():
        if not field_meta.is_required:
            continue
        dq = field_meta.always_required_dq_code if self.config.include_dq_codes else None
        if not self._path_exists(data, path):
            errors.append(RequiredError(
                path=path,
                message=f"Обязательное поле отсутствует: {path}",
                severity="error", step="required",
                dq_code=dq,
                requirement_type="missing",
            ))
        else:
            value = self._get_value_by_path(data, path)
            if value is None:
                errors.append(RequiredError(
                    path=path,
                    message=f"Обязательное поле = null: {path}",
                    severity="error", step="required",
                    dq_code=dq,
                    requirement_type="null",
                ))
    return errors
```

### Шаг 3: _check_conditional

```python
def _check_conditional(self, data, schema_fields) -> List[ConditionalError]:
    """Делегирование ConditionalValidator, обёртка в ConditionalError.
    Различает missing/null через requirement_type."""
    conditional_fields = {k: v for k, v in schema_fields.items() if v.is_conditional and v.condition}
    if not conditional_fields:
        return []

    raw_errors = self._conditional_validator.validate(data, conditional_fields)
    errors = []
    for raw in raw_errors:
        requirement_type = "null" if self._path_exists(data, raw.path) else "missing"
        dq = None
        if self.config.include_dq_codes:
            dq = raw.dq_code or self._get_field_dq_code(schema_fields, raw.path, "conditional")
        errors.append(ConditionalError(
            path=raw.path,
            message=raw.message,
            severity="error", step="conditional",
            original_error=raw,
            dq_code=dq,
            requirement_type=requirement_type,
        ))
    return errors
```

### Шаг 4: _check_constraints

```python
def _check_constraints(self, data, schema_fields) -> List[ConstraintError]:
    """Проверка ограничений через constraint_utils.py."""
    errors = []
    for path, field_meta in schema_fields.items():
        if not field_meta.constraints:
            continue
        value = self._get_value_by_path(data, path)
        if value is None:
            continue  # null-поля пропускаются — их проверяет Шаг 2/3

        for constraint_name, constraint_value in field_meta.constraints.items():
            error_msg = check_constraint(constraint_name, constraint_value, value)
            if error_msg is not None:
                severity = "error" if self.config.strict else "warning"
                errors.append(ConstraintError(
                    path=path,
                    message=error_msg,
                    severity=severity, step="constraint",
                    constraint_name=constraint_name,
                    constraint_value=constraint_value,
                    actual_value=value,
                ))
    return errors
```

### Шаг 5: _check_dictionaries

```python
def _check_dictionaries(self, data, schema_fields) -> List[DictionaryError]:
    """Проверка справочников через DictionaryLoader."""
    if not self._dictionary_loader:
        return []
    errors = []
    for path, field_meta in schema_fields.items():
        if not field_meta.has_dictionary():
            continue
        value = self._get_value_by_path(data, path)
        if value is None:
            continue

        dictionary = self._dictionary_loader.get_cached_dictionary(field_meta.dictionary)
        if dictionary and not (dictionary.contains_code(str(value)) or dictionary.contains_name(str(value))):
            dq = field_meta.dictionary_dq_code if self.config.include_dq_codes else None
            errors.append(DictionaryError(
                path=path,
                message=f"Значение '{value}' не найдено в справочнике '{field_meta.dictionary}'",
                severity="error", step="dictionary",
                dictionary_name=field_meta.dictionary,
                actual_value=value,
                dq_code=dq,
            ))
    return errors
```

### Утилиты

```python
def _normalize_json_path(self, json_path: str) -> str:
    """$.loanRequest.creditAmt → loanRequest/creditAmt"""
    ...

def _path_exists(self, data: Dict, path: str) -> bool:
    """Проверяет наличие ключа в JSON (включая вложенные объекты и массивы)."""
    ...

def _get_value_by_path(self, data: Dict, path: str) -> Any:
    """Извлекает значение по пути 'loanRequest/creditAmt'."""
    ...

def _extract_schema_metadata(self, raw_schema: Dict) -> SchemaMetadata:
    """Извлекает stageName, version, direction из корня JSON Schema."""
    ...

def _get_field_dq_code(self, schema_fields, path, dq_type) -> Optional[int]:
    """Извлекает DQ-код из FieldMetadata по типу (always_required/conditional/dictionary)."""
    ...

def _group_errors_by_parent(self, errors: List[BaseValidationError]) -> Dict[str, List[BaseValidationError]]:
    """Группирует ошибки по родительскому объекту для tree-формата."""
    ...
```

---

## Алгоритм validate()

```
1. start_time = now()
2. result = ValidationResult(is_valid=True)
3. Если raw_schema и config.check_schema:
     result.schema_errors = _check_schema(data, raw_schema)
4. Если schema_fields:
     Если config.check_required:
       result.required_errors = _check_required(data, schema_fields)
     Если config.check_conditional:
       result.conditional_errors = _check_conditional(data, schema_fields)
     Если config.check_constraints:
       result.constraint_errors = _check_constraints(data, schema_fields)
     Если config.check_dictionaries и dictionary_loader is not None:
       result.dictionary_errors = _check_dictionaries(data, schema_fields)
5. Если НЕ config.include_dq_codes:
     Очистить dq_code во всех ошибках (установить в None)
6. _collect_statistics(schema_fields, result)
7. result.statistics.duration_ms = (now() - start_time).total_seconds() * 1000
8. result.is_valid = (result.error_count == 0)
9. Возврат result
```

Порядок шагов: 1 -> 2 -> 3 -> 4 -> 5. Шаги независимы — ошибка на одном не блокирует остальные. Все шаги выполняются всегда.

---

## Формат вывода ошибок

### Дерево (format="tree", show_full_paths=True)

```
❌ Валидация НЕ ПРОЙДЕНА (7 ошибок, 2 предупреждения)

📂 loanRequest
   ├── [ОШИБКА] loanRequest/productCd — обязательное поле отсутствует
   ├── [ОШИБКА] loanRequest/creditAmt — обязательное поле = null
   └── 📂 loanRequest/applicantInfo
       ├── [ОШИБКА] loanRequest/applicantInfo/inn — обязательное поле = null
       └── [УО] loanRequest/applicantInfo/birthDate — не заполнено (условие: productCd == 'FL')

⚠️  Ограничения (2 предупреждения)
   ├── [ПРЕДУПРЕЖДЕНИЕ] loanRequest/loanAmount — maxLength=15, фактически 18
   └── [ПРЕДУПРЕЖДЕНИЕ] loanRequest/phone — pattern не совпадает

✅ Справочники — ошибок нет
```

### Дерево (format="tree", show_full_paths=False)

```
📂 loanRequest
   ├── [ОШИБКА] productCd — обязательное поле отсутствует
   ├── [ОШИБКА] creditAmt — обязательное поле = null
   └── 📂 applicantInfo
       ├── [ОШИБКА] inn — обязательное поле = null
       └── [УО] birthDate — не заполнено
```

### Плоский (format="flat")

```
❌ Валидация НЕ ПРОЙДЕНА (7 ошибок, 2 предупреждения)

ОШИБКИ:
  [REQUIRED]  loanRequest/productCd — обязательное поле отсутствует
  [REQUIRED]  loanRequest/creditAmt — обязательное поле = null
  [REQUIRED]  loanRequest/applicantInfo/inn — обязательное поле = null
  [CONDITIONAL] loanRequest/applicantInfo/birthDate — УО не заполнено (productCd == 'FL')

ПРЕДУПРЕЖДЕНИЯ:
  [CONSTRAINT] loanRequest/loanAmount — maxLength=15, фактически 18
  [CONSTRAINT] loanRequest/phone — pattern не совпадает
```

---

## Обработка ошибок

| Тип | step | severity | Поведение |
|-----|------|----------|-----------|
| `SchemaError` | schema | error | Добавить в schema_errors |
| `RequiredError` | required | error | Добавить в required_errors |
| `ConditionalError` | conditional | error | Добавить в conditional_errors |
| `ConstraintError` | constraint | error (strict) / warning (lenient) | Добавить в constraint_errors |
| `DictionaryError` | dictionary | error | Добавить в dictionary_errors |

is_valid = error_count == 0 (warnings не влияют).

### Граничные случаи

| Случай | Поведение |
|--------|-----------|
| data = {} | Шаги 2-5: 0 ошибок, Шаг 1: зависит от raw_schema |
| schema_fields = None | Шаги 2-5 пропускаются |
| raw_schema = None | Шаг 1 пропускается |
| dictionary_loader = None, check_dictionaries = True | Шаг 5 пропускается (0 ошибок) |
| SpEL-ошибка в ConditionalValidator | ConditionalError с сообщением об ошибке вычисления |
| Неизвестное constraint-имя | Пропускается check_constraint() → None |

---

## Зависимости

```
JsonValidator
  +-- jsonschema                  (Шаг 1: Draft201909Validator — независимая реализация)
  +-- ConditionalValidator        (Шаг 3: делегирование)
  |     +-- ConditionEvaluator
  |     +-- SpelParser
  +-- DictionaryLoader            (Шаг 5: загрузка справочников)
  +-- SchemaParser                (validate_from_paths)
  +-- constraint_utils            (Шаг 4: общие проверки ограничений)
  +-- json_utils.load_json        (validate_from_paths)
  +-- logger
```

### НЕ дублируется

| Модуль | Использование |
|--------|---------------|
| json_utils.validate_json_schema | НЕ используется (свой Draft201909Validator) |
| json_utils.get_validation_errors | НЕ используется |
| conditional_validator | Делегируется Шаг 3 |
| dictionary_loader | Делегируется Шаг 5 |
| JsonActualizer._validate_value | Заменён на constraint_utils |

---

## Изменения в существующих модулях

### JsonActualizer

- **Удалить:** `_validate_result()` — метод и вызов внутри `actualize()`
- **Удалить:** поле `validation_errors` из `ActualizationResult`
- **Рефакторинг:** `_validate_value()` — заменить inline-проверки на вызовы `constraint_utils.check_constraint()`
- **Обновить:** ~5 тестов, которые проверяют `_validate_result()`

### ConditionalValidator

- **Добавить:** поле `requirement_type: str` в `ValidationError` ("missing" | "null")
- **Добавить:** проверку `_path_exists()` для различения missing/null
- **Обновить:** ~3-5 тестов

### SchemaParser

- **Добавить:** парсинг `alwaysRequiredDqCode`, `conditionalDqCode`, `dictionaryDqCode` из JSON Schema
- **Обновить:** 3 теста

### constraint_utils.py (новый)

```python
# src/utils/constraint_utils.py

def check_constraint(name: str, expected: Any, actual: Any) -> Optional[str]:
    """Вернуть None если ОК, иначе сообщение об ошибке."""
    checker = _CHECKERS.get(name)
    return checker(expected, actual) if checker else None

def check_min_length(expected: int, actual: str) -> Optional[str]: ...
def check_max_length(expected: int, actual: str) -> Optional[str]: ...
def check_pattern(expected: str, actual: str) -> Optional[str]: ...
def check_minimum(expected: Number, actual: Number) -> Optional[str]: ...
def check_maximum(expected: Number, actual: Number) -> Optional[str]: ...
def check_min_items(expected: int, actual: list) -> Optional[str]: ...
def check_max_items(expected: int, actual: list) -> Optional[str]: ...
def check_enum(expected: list, actual: Any) -> Optional[str]: ...
def check_max_int_length(expected: int, actual: Number) -> Optional[str]: ...
def check_max_frac_length(expected: int, actual: Number) -> Optional[str]: ...

_CHECKERS = {
    "minLength": check_min_length,
    "maxLength": check_max_length,
    "pattern": check_pattern,
    "minimum": check_minimum,
    "maximum": check_maximum,
    "minItems": check_min_items,
    "maxItems": check_max_items,
    "enum": check_enum,
    "maxIntLength": check_max_int_length,
    "maxFracLength": check_max_frac_length,
}
```

---

## Структура файлов

| Действие | Файл |
|---------|------|
| **Создать** | `src/core/json_validator.py` |
| **Создать** | `src/utils/constraint_utils.py` |
| **Создать** | `tests/unit/core/test_json_validator.py` |
| **Создать** | `tests/unit/test_constraint_utils.py` |
| **Изменить** | `src/core/__init__.py` — экспорт JsonValidator |
| **Изменить** | `src/utils/__init__.py` — экспорт constraint_utils |
| **Изменить** | `src/core/json_actualizer.py` — убрать _validate_result(), рефакторинг _validate_value() |
| **Изменить** | `src/core/conditional_validator.py` — null/missing + requirement_type |
| **Изменить** | `src/parsers/schema_parser.py` — парсинг DQ-полей |
| **Обновить** | TODO.md, STATE.md, CHANGELOG.md, CLAUDE.md |

---

## Тесты

### JsonValidator: ~42 unit-теста

| Группа | Кол-во | Описание |
|--------|--------|----------|
| ValidatorConfig | 3 | Дефолтные значения, все шаги off, invalid output_format |
| Шаг 1: Schema | 6 | Валидные данные, невалидный тип, missing object, nested error, empty schema, format error |
| Шаг 2: Required | 6 | Присутствует/null/missing/is_required=False/nested/dq_code |
| Шаг 3: Conditional | 6 | Делегирование, wrapping, dq_code, null/missing, SpEL-ошибка, нет УО |
| Шаг 4: Constraints | 10 | 10 типов ограничений + strict vs lenient |
| Шаг 5: Dictionaries | 4 | Валидное/невалидное, loader=None, field=None, contains_name |
| DQ-коды | 3 | include_dq_codes=False/True, fallback |
| ValidationResult | 4 | is_valid, all_errors, statistics, to_dict |
| to_summary | 2 | tree format, flat format |
| validate_from_paths | 2 | Happy path, schema metadata extraction |
| validate_batch | 2 | Multiple scenarios, empty list |

### constraint_utils: 10 unit-тестов

По одному на каждый тип ограничения (minLength, maxLength, pattern, minimum, maximum, minItems, maxItems, enum, maxIntLength, maxFracLength).

### SchemaParser DQ: 3 теста

Парсинг alwaysRequiredDqCode, conditionalDqCode, dictionaryDqCode.

### ConditionalValidator null/missing: 3 теста

requirement_type="missing", "null", поле присутствует и не-null.

### Обновлённые тесты JsonActualizer: ~5 тестов

Удалить тесты _validate_result(), обновить тесты _validate_value().

---

## CLI-использование

### Команда validate

```bash
python -m src.cli validate \
  --schema data/V072Call1Rq.json \
  --json-file output/call1_pacl_v072.json
```

### Опции CLI

```bash
python -m src.cli validate \
  --schema data/V072Call1Rq.json \       # JSON Schema (обязательно)
  --json-file output/call1.json \         # JSON-данные (обязательно)
  [--no-schema]                           # Пропустить Шаг 1
  [--no-required]                         # Пропустить Шаг 2
  [--no-conditional]                      # Пропустить Шаг 3
  [--no-constraints]                      # Пропустить Шаг 4
  [--dictionaries data/dicts.xlsx]        # Включить Шаг 5 + путь к справочникам
  [--dq-codes]                            # Включить DQ-коды
  [--strict]                              # Строгий режим
  [--output-format tree|flat]             # Формат вывода (по умолчанию tree)
  [--short-paths]                         # Короткие пути в tree-формате
  [--output report.md]                    # Сохранить отчёт в файл
```

---

## Верификация

1. `pytest tests/unit/core/test_json_validator.py -v` — все 42 теста проходят
2. `pytest tests/unit/test_constraint_utils.py -v` — все 10 тестов проходят
3. `pytest --cov=src/core/json_validator.py --cov-report=term-missing` — покрытие > 90%
4. `mypy src/core/json_validator.py` — без ошибок типов
5. `flake8 src/core/json_validator.py` — без замечаний
6. `pytest tests/unit/core/test_conditional_validator.py` — ConditionalValidator не сломан
7. `pytest tests/unit/core/test_json_actualizer.py` — JsonActualizer без _validate_result() работает
8. Интеграционная проверка: SchemaParser → validate() — результат корректен

---

## TODO (после реализации)

- [ ] DQ-коды: создать маппинг-таблицу DQ_CHECK → описание (Post-MVP)
- [ ] CLI: реализовать команду validate (Этап 9)
- [ ] СпелФорматтер: человекочитаемый вывод SpEL-условий в ConditionalError (Этап 11)
- [ ] ScenarioGenerator: алгоритм пресетов для генерации сценариев на основе channel/product/program/loan_type