"""
Модуль анализаторов изменений JSON Schema

Этот модуль предоставляет инструменты для анализа изменений между версиями схем.

Основные компоненты:
- ChangeAnalyzer: Класс для детального анализа изменений
- AnalyzedChange: Модель проанализированного изменения (из src.models)
- AnalysisResult: Результат анализа (из src.models)
- Enum'ы для классификации (из src.models.enums)

Примечание:
    Классы AnalyzedChange, AnalysisResult и enum'ы теперь импортируются
    из src.models для централизованного управления моделями данных.
"""

# Импортируем ChangeAnalyzer из текущего модуля
from src.analyzers.change_analyzer import ChangeAnalyzer

# Импортируем модели и enum'ы из src.models (единый источник истины)
from src.models import (
    AnalyzedChange,
    AnalysisResult,
    ChangeType,
    BreakingLevel,
    ImpactLevel,
)

# Для обратной совместимости со старым кодом (DEPRECATED)
# TODO: Удалить эти алиасы в версии 0.2.0
ChangeClassification = BreakingLevel  # Устаревшее имя
ChangeImpact = ImpactLevel            # Устаревшее имя

__all__ = [
    # Основной класс анализатора
    "ChangeAnalyzer",

    # Модели данных (из src.models)
    "AnalyzedChange",
    "AnalysisResult",

    # Enum'ы для классификации (из src.models.enums)
    "ChangeType",
    "BreakingLevel",
    "ImpactLevel",

    # DEPRECATED: Для обратной совместимости (удалить в v0.2.0)
    "ChangeClassification",  # Используйте BreakingLevel
    "ChangeImpact",          # Используйте ImpactLevel
]
