"""
Модели данных приложения

Этот модуль содержит все dataclass-модели для работы с:
- JSON Schema (версии, поля, изменения)
- Справочниками (справочные значения)
- Сценариями (тестовые JSON)
- Перечислениями для классификации изменений
- Результатами анализа изменений (NEW)
"""

from .schema_models import (
    VersionInfo,
    VersionStatus,
    FieldMetadata,
    FieldChange,
    SchemaDiff,
    ConditionalRequirement,
)

from .dictionary_models import (
    DictionaryEntry,
    Dictionary,
)

from .scenario_models import (
    Scenario,
    ScenarioMetadata,
)

from .enums import (
    ChangeType,
    BreakingLevel,
    ImpactLevel,
    FieldElementType,
    # Алиасы для удобства
    CHANGE_TYPE_ADDITION,
    CHANGE_TYPE_REMOVAL,
    CHANGE_TYPE_MODIFICATION,
    BREAKING,
    NON_BREAKING,
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW,
)

# ✨ НОВОЕ: Модели для анализа изменений
from .change_models import (
    AnalyzedChange,
    AnalysisResult,
)

__all__ = [
    # Schema models
    "VersionInfo",
    "VersionStatus",
    "FieldMetadata",
    "FieldChange",
    "SchemaDiff",
    "ConditionalRequirement",

    # Dictionary models
    "DictionaryEntry",
    "Dictionary",

    # Scenario models
    "Scenario",
    "ScenarioMetadata",

    # Enums
    "ChangeType",
    "BreakingLevel",
    "ImpactLevel",
    "FieldElementType",

    # Enum aliases
    "CHANGE_TYPE_ADDITION",
    "CHANGE_TYPE_REMOVAL",
    "CHANGE_TYPE_MODIFICATION",
    "BREAKING",
    "NON_BREAKING",
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",

    # ✨ Change analysis models (NEW)
    "AnalyzedChange",
    "AnalysisResult",
]
