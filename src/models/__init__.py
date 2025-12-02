"""
Модели данных приложения

Этот модуль содержит все dataclass-модели для работы с:
- JSON Schema (версии, поля, изменения)
- Справочниками (справочные значения)
- Сценариями (тестовые JSON)
"""

from .schema_models import (
    VersionInfo,
    VersionStatus,
    FieldMetadata,
    FieldChange,
    SchemaDiff,
    ConditionalRequirement,  # added last
)
from .dictionary_models import (
    DictionaryEntry,
    Dictionary,
)
from .scenario_models import (
    Scenario,
    ScenarioMetadata,
)

__all__ = [
    # Schema models
    "VersionInfo",
    "VersionStatus",
    "FieldMetadata",
    "FieldChange",
    "SchemaDiff",
    "ConditionalRequirement",  # added last
    # Dictionary models
    "DictionaryEntry",
    "Dictionary",
    # Scenario models
    "Scenario",
    "ScenarioMetadata",
]
