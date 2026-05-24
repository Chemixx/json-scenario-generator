# Coding Conventions

**Analysis Date:** 2026-05-06

## Naming Patterns

**Files:**
- `snake_case` for all Python files: `schema_parser.py`, `change_analyzer.py`, `report_formatter.py`
- Test files: `test_<module>.py` — `test_schema_models.py`, `test_change_analyzer.py`
- Fixtures directory mirrors source: `tests/fixtures/schemas/`, `tests/fixtures/dictionaries/`

**Functions:**
- `snake_case` with descriptive verbs: `load_schema()`, `parse_schema()`, `_parse_field()`
- Private methods prefixed with `_`: `_extract_constraints()`, `_tokenize()`, `_resolve_path()`
- Factory functions: `get_spel_parser()`, `get_logger()`

**Variables:**
- `snake_case`: `field_meta`, `schema_diff`, `value_generator`
- Constants in `config/settings.py`: `DEFAULT_LOCALE`, `DEFAULT_ARRAY_SIZE`

**Types (Classes/Enums):**
- `PascalCase` for classes: `FieldMetadata`, `SchemaDiff`, `ConditionalRequirement`
- `PascalCase` for enums: `VersionStatus`, `ChangeType`, `BreakingLevel`, `ImpactLevel`, `NodeType`
- Dataclass fields: `snake_case` — `field_type`, `is_required`, `is_conditional`

**Modules:**
- Package exports via `__init__.py` re-exports:
  ```python
  # src/models/__init__.py
  from .schema_models import FieldMetadata, SchemaDiff, VersionInfo
  from .dictionary_models import Dictionary, DictionaryEntry
  from .scenario_models import Scenario, ScenarioMetadata
  ```

## Code Style

**Formatting:**
- **black** 23.12.1 — enforced via dev dependencies
- Line length: 100 characters (per flake8 config in project)
- Imports organized: stdlib → third-party → local

**Linting:**
- **flake8** 7.0.0 — style checking
- **pyflakes** — undefined names detection
- **pycodestyle** 2.11.1 — PEP 8 compliance
- **mypy** 1.8.0 — static type checking (type hints mandatory)

**Type Hints (mandatory for all public APIs):**
```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field as dataclass_field

@dataclass
class FieldMetadata:
    path: str
    name: str
    field_type: str
    is_required: bool = False
    is_conditional: bool = False
    condition: Optional[ConditionalRequirement] = None
    constraints: Dict[str, Any] = dataclass_field(default_factory=dict)
```

## Import Organization

**Order:**
1. Future imports: `from __future__ import annotations`
2. Standard library: `from typing import ...`, `from pathlib import Path`
3. Third-party: `from loguru import logger`, `from faker import Faker`
4. Local imports: `from ..models import FieldMetadata`

**Path Aliases:**
- Relative imports within package: `from ..models import ...`
- Absolute imports for cross-package: `from src.models import ...`

**Example (`src/parsers/schema_parser.py`):**
```python
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..models import FieldMetadata, ConditionalRequirement
from ..utils import load_json, get_logger
```

## Documentation Standards

**Docstrings (Google style):**
```python
def load_schema(self, schema_path: Path) -> Dict[str, FieldMetadata]:
    """
    Загрузить и распарсить JSON Schema

    Args:
        schema_path: Путь к JSON Schema файлу

    Returns:
        Словарь метаданных полей {путь: метаданные}

    Example:
        >>> parser = SchemaParser()
        >>> fields = parser.load_schema(Path("data/V072Call1Rq.json"))
        >>> print(len(fields))
        245
    """
```

**Class Docstrings:**
```python
@dataclass
class ConditionalRequirement:
    """
    Условная обязательность поля (аналог ConditionalRequirement.java)

    Представляет условие, при котором поле становится обязательным.
    Используется для полей с типом обязательности "УО" (условно обязательное).

    Attributes:
        expression: SpEL выражение для проверки условия
        message: Человекочитаемое описание условия
        dq_code: Код проверки Data Quality (опционально)
    """
```

**Inline Comments:**
- Russian language for business logic comments
- English for technical implementation notes
- `# ← НОВОЕ ПОЛЕ` style markers for recent additions
- `# TODO:` for deferred work (2 found in codebase)

## Error Handling

**Patterns:**
- Custom exceptions for domain errors (planned): `ValidationError`, `SchemaError`
- Built-in exceptions for invalid state: `ValueError`, `NotImplementedError`
- Logging errors with context:
  ```python
  logger.error(f"Ошибка актуализации: {e}, выполняю rollback")
  ```

**Validation:**
- Type validation via type hints + mypy
- Runtime validation in dataclass `__post_init__`:
  ```python
  def __post_init__(self):
      if not self.message:
          self.message = self._expr_to_message(self.expression)
  ```

**Rollback Pattern:**
```python
def actualize(self, scenario: Dict, schema_diff: SchemaDiff) -> Dict:
    result = copy.deepcopy(scenario)
    backup = copy.deepcopy(result)  # для rollback
    
    try:
        # обработка
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}, выполняю rollback")
        return backup
```

## Logging

**Framework:** `loguru` 0.7.2

**Patterns:**
- Module-specific loggers: `logger = get_logger(__name__)`
- Structured logging with context:
  ```python
  logger.info(f"{Icon.DIRECTORY} Загрузка схемы из {schema_path.name}")
  logger.debug(f"{Icon.CONFIG} Вызов функции: {func_name}() с args={args}")
  ```
- Icon prefixes for log levels (cp1251-safe):
  - `[START]` — startup
  - `[FILE]` — file operations
  - `[OK]` — success
  - `[ERR]` — error
  - `[CFG]` — debug/processing

**Configuration (`config/settings.py`):**
- Console: colored, level=INFO
- File: `logs/app.log`, rotation=10MB, retention=30 days, compression=zip

## Comments

**When to Comment:**
- Complex business logic (SpEL parsing, condition evaluation)
- Non-obvious implementation decisions
- Migration notes: `# ← ИЗМЕНЕНО`, `# ← НОВОЕ ПОЛЕ`
- Deprecated code markers: `# [!!!] ЧАСТИЧНО`, `# [WARN] ЗАГЛУШКИ`

**JSDoc/TSDoc equivalent:**
- Full docstrings for all public classes and functions
- Args/Returns/Raises sections mandatory
- Example section encouraged for complex APIs

## Function Design

**Size:**
- Single responsibility per function
- Private helpers for sub-tasks: `_parse_field()`, `_extract_constraints()`

**Parameters:**
- Type hints mandatory
- Default values for optional params
- `**kwargs` avoided in core logic

**Return Values:**
- Explicit return type annotations
- `Optional[T]` for nullable returns
- `Dict`, `List` with content types when meaningful

## Module Design

**Exports:**
- Public API via `__all__` (implicit via `__init__.py` re-exports)
- Barrel files for package exports: `src/models/__init__.py`

**Layer Separation:**
- Models (`src/models/`) — no dependencies on other layers
- Parsers (`src/parsers/`) — depend only on models
- Core (`src/core/`) — business logic, depends on models
- Analyzers/Formatters — depend on models and core

**Anti-Patterns to Avoid:**

### Circular imports between layers
**What happens:** Importing `core` from `models` or vice versa
**Why it's wrong:** Breaks layer separation, causes import errors
**Do this instead:** Keep models dependency-free, use forward references with `from __future__ import annotations`

### Using `eval()` for SpEL execution
**What happens:** Temptation to use `eval(expression)` for SpEL
**Why it's wrong:** Security risk (RCE), not AST-based
**Do this instead:** Use AST-based evaluator: `SpelParser.parse() → AST → ConditionEvaluator.evaluate()`

### Mixing business logic with I/O
**What happens:** File operations inside analyzer classes
**Why it's wrong:** Violates SRP, hard to test
**Do this instead:** Separate I/O (loaders) from logic (analyzers)

### Pandas import leak
**What happens:** `excel_utils.py` imports pandas, leaks via `utils/__init__.py`
**Why it's wrong:** Causes import errors in tests when pandas not installed
**Do this instead:** Isolate pandas imports, use lazy loading or separate module

---

*Convention analysis: 2026-05-06*
