# DictionaryLoader v2 — Спецификация проектирования

> **Дата:** 2026-05-26
> **Статус:** Draft
> **Автор:** claude (сессия brainstorming)

---

## 1. Контекст и мотивация

### 1.1 Проблема

Текущая реализация `DictionaryLoader` поддерживает **только Excel (.xlsx)**, а продакшен-справочники поставляются в **JSON-формате** (`1905.64_v1.json`, `1905.65_v1_int.json`). Существуют следующие проблемы:

| # | Проблема | Критичность |
|---|----------|-------------|
| P1 | DictionaryLoader не загружает JSON-файлы | Критическая |
| P2 | `is_dictionary_value()` — заглушка, всегда `True` | Критическая |
| P3 | Расхождение типов: `DictionaryEntry.code: int`, но загрузчик конвертирует в `str` | Высокая |
| P4 | Ключи кэша `{file}:{sheet}` — ValueGenerator ищет по имени справочника | Высокая |
| P5 | Линейный поиск O(n) в `get_by_code`/`get_by_name` для 10K+ записей | Средняя |
| P6 | Нет полей `currentVersion`, `deleted`, `attributes`, `mappings`, `englishLocalization` | Средняя |
| P7 | `check_dictionaries = False` по умолчанию в ValidatorConfig | Низкая |

### 1.2 Цели

1. Загрузка продакшен-справочников из JSON (формат 1905.64/1905.65)
2. Сохранение поддержки Excel
3. O(1) поиск по коду и названию
4. Кэш по имени справочника (`"PRODUCT_TYPE"`)
5. Реальная валидация значений в `is_dictionary_value()`
6. Расшифровка кодов в отчётах: `"Тестовый продукт (10410001)"`
7. Обратная совместимость

---

## 2. Архитектура

### 2.1 Общая схема

```
┌──────────────────────────────────────────────────────────────┐
│                     DictionaryRegistry                        │
│  Центральное хранилище + поиск + resolve                      │
│                                                                │
│  _dictionaries: Dict[str, Dictionary]     # по имени         │
│  _metadata: Dict[str, DictionaryMetadata]  # метаданные        │
│                                                                │
│  load_from_json(path, ...)       # JSON-файлы (прод)          │
│  load_from_excel(path, ...)       # Excel-файлы (текущий)     │
│  register(name, dictionary)       # ручная регистрация         │
│  get(name) → Dictionary          # O(1) по имени               │
│  get_entry(dict_name, code) → Entry  # O(1) по коду          │
│  get_entry_by_name(dict_name, name) → Entry  # O(1) по имени  │
│  resolve(dict_name, code, fmt) → str  # расшифровка           │
│  is_valid_value(dict_name, value) → bool  # валидация         │
│  list_dictionaries() → List[str]                              │
│  get_metadata(name) → DictionaryMetadata                       │
│  clear()                                                       │
├──────────────────────────────────────────────────────────────┤
│            Стратегии загрузки (делегируют в Registry)          │
│                                                                │
│  ┌───────────────────┐  ┌─────────────────────────┐          │
│  │ DictionaryLoader  │  │ JsonDictionaryLoader    │          │
│  │  (Excel .xlsx)    │  │  (JSON .json)            │          │
│  └───────────────────┘  └─────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Принципы

- **Registry — единая точка доступа** для всех потребителей (SpEL, ValueGenerator, Validator, Reports)
- **Ключ кэша — имя справочника** (`"PRODUCT_TYPE"`), а не `"{file}:{sheet}"`
- **Loaders — стратегии парсинга**, не хранят состояние, возвращают `Dict[str, Dictionary]`
- **Фильтрация при загрузке**: `deleted=false`, `currentVersion=true` (настраиваемо)
- **Обратная совместимость**: `DictionaryLoader` без изменений, новые поля имеют defaults

---

## 3. Модели данных

### 3.1 DictionaryEntry (расширенная)

```python
@dataclass
class DictionaryEntry:
    """Запись справочника"""
    code: int                                    # canonicalCode из JSON / код из Excel
    name: str                                    # наименование значения
    dictionary_type: str                         # код справочника (PRODUCT_TYPE)
    description: str = ""                        # описание (опционально)
    english_localization: Optional[str] = None   # englishLocalization (прод-JSON)
    current_version: bool = True                 # currentVersion (отфильтровано при загрузке)
    is_deleted: bool = False                    # deleted (отфильтровано при загрузке)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    mappings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Обратная совместимость:** все новые поля имеют default-значения. Существующий код, создающий `DictionaryEntry(code=1, name="PACL", dictionary_type="PRODUCT_TYPE")`, продолжает работать.

**Маппинг из JSON:**

| JSON-поле | Поле модели | Примечание |
|-----------|-------------|------------|
| `canonicalCode` | `code` | Прямое отображение |
| `name` | `name` | Прямое отображение |
| `dictionaryCode` | `dictionary_type` | Прямое отображение |
| `description` | `description` | Опционально |
| `englishLocalization` | `english_localization` | Опционально, только 1905.65 |
| `currentVersion` | `current_version` | Фильтруется при загрузке |
| `deleted` | `is_deleted` | Фильтруется при загрузке |
| `attributes` | `attributes` | Список словарей |
| `mappings` | `mappings` | Список словарей |

### 3.2 Dictionary (с индексами)

```python
@dataclass
class Dictionary:
    """Справочник с индексами для O(1) поиска"""
    name: str
    entries: List[DictionaryEntry] = field(default_factory=list)
    description: str = ""
    _code_index: Dict[int, DictionaryEntry] = field(default_factory=dict, repr=False)
    _name_index: Dict[str, DictionaryEntry] = field(default_factory=dict, repr=False)
    _metadata: Optional[DictionaryMetadata] = None
```

**Изменения:**
- `_code_index` и `_name_index` — хэш-мапы для O(1) поиска
- `add_entry()` автоматически перестраивает индексы
- `get_by_code()` и `get_by_name()` используют индексы
- `_metadata` — опциональные метаданные уровня справочника

**Важно:** `_code_index` и `_name_index` — внутренние поля (префикс `_`). Они не сериализуются в `to_dict()` и не участвуют в `__eq__`.

### 3.3 DictionaryMetadata (новая)

```python
@dataclass
class DictionaryMetadata:
    """Метаданные справочника (из секции dictionaries JSON-файла)"""
    code: str                                    # "PRODUCT_TYPE"
    name: str                                    # "Тип продукта"
    dictionary_type_code: int = 1                # 1=обычный, 3=системный
    subsystem: int = 0
    hierarchical: bool = False
    form_dict_flg: bool = False
    attribute_metadata: List[Dict[str, Any]] = field(default_factory=list)
```

Хранится в `Dictionary._metadata`. Доступна через `Registry.get_metadata(name)`.

### 3.4 ResolveResult (новая)

```python
@dataclass
class ResolveResult:
    """Результат расшифровки кода справочника"""
    code: int
    name: str
    dictionary_type: str
    description: str = ""
    english_localization: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def format(self, fmt: str = "{name} ({code})") -> str:
        """Гибкое форматирование:
        - "{name} ({code})" → "PACL (10410001)"
        - "{code}" → "10410001"
        - "{name}" → "PACL"
        - "{name} [{eng}]" → "PACL [PACL]"
        """
        return fmt.format(
            name=self.name, code=self.code,
            description=self.description,
            eng=self.english_localization or ""
        )
```

---

## 4. API DictionaryRegistry

```python
class DictionaryRegistry:
    """Центральное хранилище справочников с быстрым поиском"""

    def __init__(self):
        self._dictionaries: Dict[str, Dictionary] = {}
        self._metadata: Dict[str, DictionaryMetadata] = {}

    # === Загрузка ===

    def load_from_json(
        self,
        file_path: Path,
        filter_deleted: bool = True,
        filter_current: bool = True
    ) -> Dict[str, Dictionary]:
        """Загрузить все справочники из JSON-файла (прод-формат).
        Автоматически регистрирует в registry.
        Возвращает словарь {name: Dictionary}."""

    def load_from_excel(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Dictionary]:
        """Загрузить справочники из Excel через DictionaryLoader.
        Делегирует загрузку, затем регистрирует в registry."""

    # === Регистрация ===

    def register(self, dictionary: Dictionary) -> None:
        """Зарегистрировать справочник. Ключ = dictionary.name.
        Перестраивает индексы Dictionary."""

    # === Поиск ===

    def get(self, name: str) -> Optional[Dictionary]:
        """Получить справочник по имени. O(1)."""

    def get_entry(self, dict_name: str, code: int) -> Optional[DictionaryEntry]:
        """Получить запись по коду. O(1) через индекс."""

    def get_entry_by_name(self, dict_name: str, name: str) -> Optional[DictionaryEntry]:
        """Получить запись по названию. O(1) через индекс."""

    # === Resolve (для отчётов и логов) ===

    def resolve(self, dict_name: str, code: int,
                fmt: str = "{name} ({code})") -> str:
        """Расшифровать код → 'PACL (10410001)'.
        Fallback: 'Неизвестный (10410001)' если справочник не найден."""

    def resolve_name(self, dict_name: str, code: int) -> Optional[str]:
        """Только название по коду. None если не найден."""

    # === Валидация (для isDictionaryValue) ===

    def is_valid_value(self, dict_name: str, value: Any) -> bool:
        """Проверить, есть ли значение в справочнике.
        Проверяет и по code (int), и по name (str).
        Fallback: True если справочник не загружен."""

    # === Информация ===

    def list_dictionaries(self) -> List[str]:
        """Список имён загруженных справочников."""

    def get_metadata(self, name: str) -> Optional[DictionaryMetadata]:
        """Метаданные справочника (из JSON)."""

    def clear(self) -> None:
        """Очистить все справочники и метаданные."""

    def __len__(self) -> int:
        """Количество загруженных справочников."""

    def __contains__(self, name: str) -> bool:
        """Проверить, загружен ли справочник."""
```

---

## 5. JsonDictionaryLoader

```python
class JsonDictionaryLoader:
    """Загрузчик справочников из JSON-файлов прод-формата"""

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger(self.__class__.__name__)

    def load(
        self,
        file_path: Path,
        filter_deleted: bool = True,
        filter_current: bool = True
    ) -> Tuple[Dict[str, Dictionary], Dict[str, DictionaryMetadata]]:
        """Загрузить все справочники из JSON-файла.

        Формат файла:
        {
            "dictionaries": [{code, name, dictionaryTypeCode, ...}],
            "elements": [{dictionaryCode, canonicalCode, name, ...}]
        }

        Returns:
            Кортеж (словари, метаданные)
        """
```

**Парсинг JSON:**

1. Читает `dictionaries` → создаёт `DictionaryMetadata` для каждого
2. Читает `elements` → группирует по `dictionaryCode`
3. Фильтрует: `deleted=false`, `currentVersion=true` (если включено)
4. Создаёт `DictionaryEntry` для каждого элемента
5. Создаёт `Dictionary` с `add_entry()` (строит индексы)
6. Возвращает `(Dict[str, Dictionary], Dict[str, DictionaryMetadata])`

**Обработка версий:**
- 1905.64: без поля `englishLocalization` → `None`
- 1905.65: с полем `englishLocalization` → заполняется
- Обе версии парсятся одним методом

---

## 6. Интеграция с потребителями

### 6.1 SpelFunctions / ConditionEvaluator

**Было (заглушка):**
```python
def is_dictionary_value(value, dictionary_name, allow_empty=False) -> bool:
    return True  # ЗАГЛУШКА
```

**Станет:**
```python
class SpelFunctions:
    def __init__(self, registry: Optional[DictionaryRegistry] = None):
        self._registry = registry

    def set_registry(self, registry: DictionaryRegistry) -> None:
        """Установить registry (для singleton-паттерна)"""
        self._registry = registry

    def is_dictionary_value(self, value, dictionary_name, allow_empty=False) -> bool:
        if allow_empty and (value is None or value == ""):
            return True
        if self._registry is None:
            return True  # fallback: нет registry → пропускаем
        return self._registry.is_valid_value(dictionary_name, value)
```

**Интеграция в ConditionEvaluator:**
```python
# При создании ConditionEvaluator передаём registry
evaluator = ConditionEvaluator(registry=registry)
# Внутри evaluator передаёт registry в SpelFunctions
```

### 6.2 ValueGenerator

**Было:**
```python
dictionary = self.dictionary_loader.get_cached_dictionary(dict_name)
# Сложный поиск по ключам кэша...
```

**Станет:**
```python
class ValueGenerator:
    def __init__(self, config=None, dictionary_loader=None, registry=None):
        self._registry = registry
        self._dictionary_loader = dictionary_loader  # backward compat

    def _generate_from_dictionary(self, field_meta):
        dict_name = field_meta.dictionary
        if self._registry:
            dictionary = self._registry.get(dict_name)  # O(1)
        elif self._dictionary_loader:
            dictionary = self._dictionary_loader.get_cached_dictionary(dict_name)
            # fallback на старый механизм...
        else:
            raise ValueError("Нет registry и dictionary_loader")
        
        entry = dictionary.get_random()
        return str(entry.code)  # Для генерации всегда возвращаем код
```

### 6.3 JsonValidator

```python
class JsonValidator:
    def __init__(self, config=None, dictionary_loader=None, registry=None):
        self._registry = registry
        self._dictionary_loader = dictionary_loader  # backward compat

    def _check_dictionaries(self, data, schema_fields):
        for field_meta in schema_fields.values():
            if not field_meta.has_dictionary():
                continue
            dict_name = field_meta.dictionary
            if self._registry:
                dictionary = self._registry.get(dict_name)
            elif self._dictionary_loader:
                dictionary = self._dictionary_loader.get_cached_dictionary(...)
            # ...
```

### 6.4 ReportFormatter

```python
# Вывод справочника в отчёте:
if field.dictionary and self._registry:
    entry = self._registry.get_entry(field.dictionary, value)
    if entry:
        resolved = self._registry.resolve(field.dictionary, value)
        lines.append(f"     Справочник: {resolved}")  # "PACL (10410001)"
    else:
        lines.append(f"     Справочник: {field.dictionary}")
elif field.dictionary:
    lines.append(f"     Справочник: {field.dictionary}")  # fallback
```

### 6.5 DictionaryError (JsonValidator)

```python
@dataclass
class DictionaryError(BaseValidationError):
    dictionary_name: str = ""
    actual_value: Any = None
    dq_code: Optional[int] = None
    resolved_value: str = ""  # НОВОЕ: расшифровка, например "PACL (10410001)"
```

---

## 7. Обратная совместимость

| Компонент | Изменение | Обратная совместимость |
|-----------|-----------|----------------------|
| `DictionaryLoader` | Без изменений | Полная |
| `DictionaryEntry` | +5 опциональных полей с defaults | Полная |
| `Dictionary` | +2 индекса `_code_index`, `_name_index`, +`_metadata` | Полная (field defaults) |
| `SpelFunctions` | +`__init__(registry)`, +`set_registry()` | Частичная (singleton нужен setter) |
| `ValueGenerator` | +`registry` параметр | Частичная (fallback на loader) |
| `JsonValidator` | +`registry` параметр | Частичная (fallback на loader) |
| `JsonActualizer` | +`registry` параметр | Частичная (прокидывает в ValueGenerator) |
| `ReportFormatter` | +`registry` параметр | Частичная (fallback на имя справочника) |
| `ConditionEvaluator` | +`registry` параметр | Частичная (передаёт в SpelFunctions) |

**Стратегия fallback:** Если `registry` не передан, компоненты пытаются использовать `dictionary_loader` по-старому. Это гарантирует, что существующий код без изменений продолжит работать.

---

## 8. Производительность

| Операция | Было | Станет |
|----------|------|--------|
| `get_by_code()` | O(n) линейный поиск | O(1) хэш-индекс |
| `get_by_name()` | O(n) линейный поиск | O(1) хэш-индекс |
| `get(name)` (Registry) | O(n) перебор ключей кэша | O(1) по имени справочника |
| `is_valid_value()` | Всегда True (заглушка) | O(1) через индекс |
| Загрузка JSON | Невозможно | O(n) парсинг + O(n) индексация |

---

## 9. Тестирование

### 9.1 Новые тесты

| Тест | Что проверяет |
|------|---------------|
| `test_json_dictionary_loader_load` | Загрузка JSON-файла, парсинг dictionaries и elements |
| `test_json_dictionary_loader_filter` | Фильтрация deleted и currentVersion |
| `test_json_dictionary_loader_versions` | Обработка 1905.64 и 1905.65 (с/без englishLocalization) |
| `test_registry_register_get` | Регистрация и поиск справочников |
| `test_registry_get_entry` | Поиск по коду O(1) |
| `test_registry_get_entry_by_name` | Поиск по названию O(1) |
| `test_registry_resolve` | Расшифровка кодов в разные форматы |
| `test_registry_is_valid_value` | Валидация по коду и названию |
| `test_registry_load_from_json` | Полный цикл: JSON → Registry |
| `test_registry_load_from_excel` | Полный цикл: Excel → Registry |
| `test_spel_is_dictionary_value` | Интеграция SpEL с Registry |
| `test_value_generator_with_registry` | Генерация значений через Registry |
| `test_json_validator_with_registry` | Валидация справочных значений через Registry |
| `test_backward_compat_dictionary_loader` | Обратная совместимость без Registry |

### 9.2 Фикстуры

- `tests/fixtures/dictionaries/product_type.json` — минимальный JSON-справочник для тестов
- `tests/fixtures/dictionaries/sample_1905.json` — формат прод-файла с 5 справочниками
- Обновить `conftest.py`: добавить фикстуру `registry` с загруженными справочниками

---

## 10. Файловая структура

```
src/
├── loaders/
│   ├── __init__.py              # + JsonDictionaryLoader, DictionaryRegistry
│   ├── dictionary_loader.py     # без изменений (Excel)
│   └── json_dictionary_loader.py # НОВЫЙ: JSON-загрузчик
├── models/
│   └── dictionary_models.py     # расширение DictionaryEntry, Dictionary + DictionaryMetadata, ResolveResult
├── core/
│   ├── spel_functions.py       # + set_registry(), реализация is_dictionary_value
│   ├── condition_evaluator.py   # + registry параметр
│   ├── value_generator.py       # + registry параметр
│   ├── json_validator.py        # + registry параметр, DictionaryError.resolved_value
│   ├── json_actualizer.py       # + registry параметр
│   └── ...
├── formatters/
│   └── report_formatter.py     # + resolve() в отчётах
tests/
├── fixtures/
│   └── dictionaries/            # НОВЫЙ: тестовые JSON-справочники
│       ├── product_type.json
│       └── sample_1905.json
├── unit/
│   ├── test_json_dictionary_loader.py   # НОВЫЙ
│   ├── test_dictionary_registry.py      # НОВЫЙ
│   ├── test_dictionary_models.py        # обновить
│   └── ...
```

---

## 11. Критические замечания и риски

1. **Тип `code`**: В прод-JSON `canonicalCode` — `int` (например, 10150001). В Excel-загрузчике код конвертировался в `str`. В новом дизайне `DictionaryEntry.code` остаётся `int`. Необходимо исправить баг в `DictionaryLoader.load_dictionary()`: убрать `str(code).strip()`, оставить `int(code)`.

2. **Singleton SpelFunctions**: `spel_functions = SpelFunctions()` — глобальный singleton. Добавление `set_registry()` — нарушение чистоты, но прагматичное решение для интеграции без масштабного рефакторинга.

3. **Фильтрация при загрузке**: По умолчанию `filter_deleted=True` и `filter_current=True`. Удалённые и неактуальные записи не попадают в Registry. Если нужна историческая справка — отключить фильтрацию.

4. **Размер данных**: JSON-файлы содержат 10K+ записей каждый. Парсинг и индексация — O(n), но выполняется один раз при загрузке. Для двух файлов (~23K записей) время загрузки < 1 секунды.

5. **Ключ справочника**: В прод-JSON `dictionaryCode` совпадает с `code` в секции `dictionaries`. Ключ Registry — это `dictionaryCode` (например, `"PRODUCT_TYPE"`), что совпадает с `FieldMetadata.dictionary` в JSON-схемах.