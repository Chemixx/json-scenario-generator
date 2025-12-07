"""
Модели для анализа изменений между версиями JSON Schema

Этот модуль содержит dataclass-модели для результатов анализа изменений:
- AnalyzedChange — детальная информация об одном изменении поля
- AnalysisResult — агрегированные результаты анализа между двумя версиями схем
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from src.models.schema_models import FieldChange
from src.models.enums import (
    ChangeType,
    BreakingLevel,
    ImpactLevel,
    FieldElementType,
)


@dataclass
class AnalyzedChange:
    """
    Результат анализа одного изменения поля

    Содержит детальную информацию о том, что изменилось, почему это важно,
    и какие действия требуются.

    Attributes:
        field_change: Исходное изменение из SchemaComparator
        change_type: ЧТО произошло (добавление/удаление/модификация)
        breaking_level: ЛОМАЕТ ли API (breaking/non-breaking)
        impact_level: Насколько КРИТИЧНО (critical/high/medium/low)
        reason: Человекочитаемое объяснение изменения
        recommendations: Список рекомендаций по обработке изменения
        affected_scenarios: Какие сценарии затронуты (опционально)

    Examples:
        >>> change = AnalyzedChange(
        ...     field_change=field_change,
        ...     change_type=ChangeType.MODIFICATION,
        ...     breaking_level=BreakingLevel.BREAKING,
        ...     impact_level=ImpactLevel.HIGH,
        ...     reason="Поле стало условно обязательным (Н → УО)",
        ...     recommendations=["Обновить тестовые сценарии", "Проверить маппинг"]
        ... )
    """
    field_change: FieldChange
    change_type: ChangeType
    breaking_level: BreakingLevel
    impact_level: ImpactLevel
    reason: str
    recommendations: List[str] = field(default_factory=list)
    affected_scenarios: List[str] = field(default_factory=list)

    @property
    def path(self) -> str:
        """Путь к полю (для удобства)"""
        return self.field_change.path

    @property
    def is_breaking(self) -> bool:
        """Является ли изменение breaking"""
        return self.breaking_level == BreakingLevel.BREAKING

    @property
    def is_critical(self) -> bool:
        """Является ли изменение критическим"""
        return self.impact_level == ImpactLevel.CRITICAL

    @property
    def priority(self) -> int:
        """Числовой приоритет для сортировки (0 = highest)"""
        return self.impact_level.to_priority()

    def to_dict(self) -> Dict:
        """Сериализация в словарь (для JSON/отчетов)"""
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "breaking_level": self.breaking_level.value,
            "impact_level": self.impact_level.value,
            "reason": self.reason,
            "recommendations": self.recommendations,
            "affected_scenarios": self.affected_scenarios,
        }


@dataclass
class AnalysisResult:
    """
    Результат анализа изменений между двумя версиями схем

    Содержит агрегированную статистику и список всех изменений.

    Attributes:
        old_version: Версия старой схемы (например, "V072Call1Rq")
        new_version: Версия новой схемы (например, "V073Call1Rq")
        analyzed_changes: Список всех проанализированных изменений
        analysis_date: Дата/время анализа
        metadata: Дополнительные метаданные (опционально)

    Properties:
        total_changes: Общее количество изменений
        breaking_changes: Список breaking changes
        non_breaking_changes: Список non-breaking changes
        additions: Список добавленных полей
        removals: Список удаленных полей
        modifications: Список модифицированных полей
        critical_changes: Список критических изменений
        high_impact_changes: Список изменений с высоким влиянием
        statistics: Словарь со статистикой

    Examples:
        >>> result = AnalysisResult(
        ...     old_version="V072Call1Rq",
        ...     new_version="V073Call1Rq",
        ...     analyzed_changes=[change1, change2, ...]
        ... )
        >>> print(f"Breaking changes: {len(result.breaking_changes)}")
        >>> print(f"Critical: {len(result.critical_changes)}")
    """
    old_version: str
    new_version: str
    analyzed_changes: List[AnalyzedChange]
    analysis_date: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    # --- Свойства для фильтрации изменений ---

    @property
    def total_changes(self) -> int:
        """Общее количество изменений"""
        return len(self.analyzed_changes)

    @property
    def breaking_changes(self) -> List[AnalyzedChange]:
        """Список breaking changes"""
        return [
            change for change in self.analyzed_changes
            if change.breaking_level == BreakingLevel.BREAKING
        ]

    @property
    def non_breaking_changes(self) -> List[AnalyzedChange]:
        """Список non-breaking changes"""
        return [
            change for change in self.analyzed_changes
            if change.breaking_level == BreakingLevel.NON_BREAKING
        ]

    @property
    def additions(self) -> List[AnalyzedChange]:
        """Список добавленных полей"""
        return [
            change for change in self.analyzed_changes
            if change.change_type == ChangeType.ADDITION
        ]

    @property
    def removals(self) -> List[AnalyzedChange]:
        """Список удаленных полей"""
        return [
            change for change in self.analyzed_changes
            if change.change_type == ChangeType.REMOVAL
        ]

    @property
    def modifications(self) -> List[AnalyzedChange]:
        """Список модифицированных полей"""
        return [
            change for change in self.analyzed_changes
            if change.change_type == ChangeType.MODIFICATION
        ]

    @property
    def critical_changes(self) -> List[AnalyzedChange]:
        """Список критических изменений"""
        return [
            change for change in self.analyzed_changes
            if change.impact_level == ImpactLevel.CRITICAL
        ]

    @property
    def high_impact_changes(self) -> List[AnalyzedChange]:
        """Список изменений с высоким влиянием"""
        return [
            change for change in self.analyzed_changes
            if change.impact_level == ImpactLevel.HIGH
        ]

    @property
    def medium_impact_changes(self) -> List[AnalyzedChange]:
        """Список изменений со средним влиянием"""
        return [
            change for change in self.analyzed_changes
            if change.impact_level == ImpactLevel.MEDIUM
        ]

    @property
    def low_impact_changes(self) -> List[AnalyzedChange]:
        """Список изменений с низким влиянием"""
        return [
            change for change in self.analyzed_changes
            if change.impact_level == ImpactLevel.LOW
        ]

    # --- Методы для статистики ---

    @property
    def statistics(self) -> Dict:
        """
        Агрегированная статистика изменений

        Returns:
            Словарь со статистикой:
            {
                "total_changes": 18,
                "change_types": {"additions": 2, "removals": 0, "modifications": 16},
                "breaking_level": {"breaking": 13, "non_breaking": 5},
                "impact_level": {"critical": 0, "high": 13, "medium": 0, "low": 5}
            }
        """
        return {
            "total_changes": self.total_changes,
            "change_types": {
                "additions": len(self.additions),
                "removals": len(self.removals),
                "modifications": len(self.modifications),
            },
            "breaking_level": {
                "breaking": len(self.breaking_changes),
                "non_breaking": len(self.non_breaking_changes),
            },
            "impact_level": {
                "critical": len(self.critical_changes),
                "high": len(self.high_impact_changes),
                "medium": len(self.medium_impact_changes),
                "low": len(self.low_impact_changes),
            },
        }

    def get_sorted_changes(
            self,
            by: str = "priority",
            reverse: bool = False
    ) -> List[AnalyzedChange]:
        """
        Получить отсортированный список изменений

        Args:
            by: Поле для сортировки ('priority', 'path', 'impact_level')
            reverse: Обратный порядок сортировки

        Returns:
            Отсортированный список изменений

        Examples:
            >>> # Сортировка по приоритету (критические первыми)
            >>> result.get_sorted_changes(by="priority")

            >>> # Сортировка по пути (алфавитно)
            >>> result.get_sorted_changes(by="path")
        """
        if by == "priority":
            return sorted(
                self.analyzed_changes,
                key=lambda x: x.priority,
                reverse=reverse
            )
        elif by == "path":
            return sorted(
                self.analyzed_changes,
                key=lambda x: x.path,
                reverse=reverse
            )
        elif by == "impact_level":
            return sorted(
                self.analyzed_changes,
                key=lambda x: x.impact_level.to_priority(),
                reverse=reverse
            )
        else:
            raise ValueError(f"Неизвестное поле для сортировки: {by}")

    def to_dict(self) -> Dict:
        """
        Сериализация в словарь (для JSON/отчетов)

        Returns:
            Полная структура с метаданными и статистикой
        """
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "analysis_date": self.analysis_date.isoformat(),
            "statistics": self.statistics,
            "changes": [change.to_dict() for change in self.analyzed_changes],
            "metadata": self.metadata,
        }

    def has_critical_changes(self) -> bool:
        """Есть ли критические изменения"""
        return len(self.critical_changes) > 0

    def has_breaking_changes(self) -> bool:
        """Есть ли breaking changes"""
        return len(self.breaking_changes) > 0

    def requires_scenario_update(self) -> bool:
        """Требуется ли обновление сценариев (есть breaking changes)"""
        return self.has_breaking_changes()
