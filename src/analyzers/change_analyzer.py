"""
Анализатор изменений между версиями JSON Schema
"""
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from ..models import SchemaDiff, FieldChange, FieldMetadata
from ..parsers import SchemaParser
from ..core import SchemaComparator  # ← ДОБАВЛЕНО
from ..utils import get_logger

logger = get_logger(__name__)


class ChangeClassification(Enum):
    """Классификация изменений"""
    BREAKING = "breaking"
    NON_BREAKING = "non-breaking"
    ADDITION = "addition"
    REMOVAL = "removal"


class ChangeImpact(Enum):
    """Уровень влияния изменения"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AnalyzedChange:
    """Проанализированное изменение"""
    field_change: FieldChange
    classification: ChangeClassification
    impact: ChangeImpact
    reason: str
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            "path": self.field_change.path,
            "change_type": self.field_change.change_type,
            "classification": self.classification.value,
            "impact": self.impact.value,
            "reason": self.reason,
            "recommendations": self.recommendations,
            "old_meta": self.field_change.old_meta.__dict__ if self.field_change.old_meta else None,
            "new_meta": self.field_change.new_meta.__dict__ if self.field_change.new_meta else None,
            "changes": self.field_change.changes
        }


@dataclass
class AnalysisResult:
    """Результат анализа изменений"""
    old_schema: Path
    new_schema: Path
    analyzed_changes: List[AnalyzedChange]

    @property
    def breaking_changes(self) -> List[AnalyzedChange]:
        """Получить breaking changes"""
        return [c for c in self.analyzed_changes if c.classification == ChangeClassification.BREAKING]

    @property
    def non_breaking_changes(self) -> List[AnalyzedChange]:
        """Получить non-breaking changes"""
        return [c for c in self.analyzed_changes if c.classification == ChangeClassification.NON_BREAKING]

    @property
    def critical_changes(self) -> List[AnalyzedChange]:
        """Получить критические изменения"""
        return [c for c in self.analyzed_changes if c.impact == ChangeImpact.CRITICAL]

    @property
    def high_impact_changes(self) -> List[AnalyzedChange]:
        """Получить изменения с высоким влиянием"""
        return [c for c in self.analyzed_changes if c.impact == ChangeImpact.HIGH]

    def get_changes_by_classification(self, classification: ChangeClassification) -> List[AnalyzedChange]:
        """Получить изменения по классификации"""
        return [c for c in self.analyzed_changes if c.classification == classification]

    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            "old_schema": str(self.old_schema),
            "new_schema": str(self.new_schema),
            "total_changes": len(self.analyzed_changes),
            "breaking_changes": len(self.breaking_changes),
            "non_breaking_changes": len(self.non_breaking_changes),
            "critical_changes": len(self.critical_changes),
            "high_impact_changes": len(self.high_impact_changes),
            "changes": [c.to_dict() for c in self.analyzed_changes]
        }


class ChangeAnalyzer:
    """Анализатор изменений между версиями схем"""

    def __init__(self):
        self.parser = SchemaParser()
        self.comparator = SchemaComparator()  # ← ДОБАВЛЕНО

    def analyze_changes(self, old_schema_path: Path, new_schema_path: Path) -> AnalysisResult:
        """
        Проанализировать изменения между двумя схемами

        Args:
            old_schema_path: Путь к старой схеме
            new_schema_path: Путь к новой схеме

        Returns:
            Результат анализа
        """
        logger.info(f"🔍 Анализ изменений между версиями")

        # Загрузка схем
        old_schema = self.parser.load_schema(old_schema_path)
        new_schema = self.parser.load_schema(new_schema_path)

        # Сравнение схем с передачей имен файлов
        diff = self.comparator.compare(
            old_schema,
            new_schema,
            old_name=old_schema_path.name,
            new_name=new_schema_path.name
        )

        # Анализ изменений
        analyzed_changes = []

        # Анализ добавленных полей
        for field_change in diff.added_fields:
            analyzed_changes.append(self._analyze_addition(field_change))

        # Анализ удаленных полей
        for field_change in diff.removed_fields:
            analyzed_changes.append(self._analyze_removal(field_change))

        # Анализ измененных полей
        for field_change in diff.modified_fields:
            analyzed_changes.append(self._analyze_modification(field_change))

        logger.info(
            f"✅ Анализ завершен: {len([c for c in analyzed_changes if c.classification == ChangeClassification.BREAKING])} breaking, "
            f"{len([c for c in analyzed_changes if c.classification == ChangeClassification.NON_BREAKING])} non-breaking"
        )

        return AnalysisResult(
            old_schema=old_schema_path,
            new_schema=new_schema_path,
            analyzed_changes=analyzed_changes
        )

    def _analyze_addition(self, field_change: FieldChange) -> AnalyzedChange:
        """Проанализировать добавление поля"""
        new_field = field_change.new_meta

        if new_field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.ADDITION,
                impact=ChangeImpact.CRITICAL,
                reason="Добавлено новое обязательное поле",
                recommendations=[
                    f"Добавить поле '{field_change.path}' во все существующие сценарии",
                    "Определить корректные значения для нового обязательного поля"
                ]
            )
        elif new_field.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.ADDITION,
                impact=ChangeImpact.HIGH,
                reason="Добавлено новое условно обязательное поле (УО)",
                recommendations=[
                    f"Проверить условия для поля '{field_change.path}'",
                    "Добавить поле в сценарии, где выполняются условия"
                ]
            )
        else:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.ADDITION,
                impact=ChangeImpact.LOW,
                reason="Добавлено новое опциональное поле",
                recommendations=[
                    "Изменение не требует обновления существующих сценариев",
                    f"Можно использовать новое поле '{field_change.path}' в новых сценариях"
                ]
            )

    def _analyze_removal(self, field_change: FieldChange) -> AnalyzedChange:
        """Проанализировать удаление поля"""
        old_field = field_change.old_meta

        if old_field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.REMOVAL,
                impact=ChangeImpact.HIGH,
                reason="Удалено обязательное поле",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из всех сценариев",
                    "Проверить, не используется ли поле в логике тестов"
                ]
            )
        elif old_field.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.REMOVAL,
                impact=ChangeImpact.MEDIUM,
                reason="Удалено условно обязательное поле (УО)",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из сценариев",
                    "Проверить условия, при которых поле использовалось"
                ]
            )
        else:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.REMOVAL,
                impact=ChangeImpact.LOW,
                reason="Удалено опциональное поле",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из сценариев, если оно используется",
                    "Изменение не критично для существующих сценариев"
                ]
            )

    def _analyze_modification(self, field_change: FieldChange) -> AnalyzedChange:
        """Проанализировать изменение поля"""
        changes = field_change.changes

        # Изменение типа - breaking
        if "type" in changes:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.CRITICAL,
                reason=changes["type"],
                recommendations=[
                    f"Обновить значения поля '{field_change.path}' в соответствии с новым типом",
                    "Преобразовать данные согласно изменению типа"
                ]
            )

        # Поле стало обязательным - breaking
        if "required" in changes:
            if "стало обязательным" in changes["required"]:
                return AnalyzedChange(
                    field_change=field_change,
                    classification=ChangeClassification.BREAKING,
                    impact=ChangeImpact.HIGH,
                    reason=changes["required"],
                    recommendations=[
                        f"Добавить поле '{field_change.path}' во все сценарии, где оно отсутствует"
                    ]
                )
            else:  # Стало опциональным
                return AnalyzedChange(
                    field_change=field_change,
                    classification=ChangeClassification.NON_BREAKING,
                    impact=ChangeImpact.LOW,
                    reason=changes["required"],
                    recommendations=[
                        "Изменение не требует обновления сценариев"
                    ]
                )

        # Поле стало условно обязательным
        if "conditional" in changes:
            if "стало условно обязательным" in changes["conditional"]:
                condition_desc = changes.get("condition", "")
                full_reason = f"{changes['conditional']}: {condition_desc}" if condition_desc else changes["conditional"]
                return AnalyzedChange(
                    field_change=field_change,
                    classification=ChangeClassification.BREAKING,
                    impact=ChangeImpact.HIGH,
                    reason=full_reason,
                    recommendations=[
                        f"Проверить условия для поля '{field_change.path}'",
                        "Добавить поле в сценарии, где выполняются условия"
                    ]
                )
            else:  # Перестало быть УО
                return AnalyzedChange(
                    field_change=field_change,
                    classification=ChangeClassification.NON_BREAKING,
                    impact=ChangeImpact.LOW,
                    reason=changes["conditional"],
                    recommendations=[
                        "Изменение не требует немедленных действий"
                    ]
                )

        # Изменилось условие УО
        if "condition" in changes and field_change.new_meta and field_change.new_meta.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason=f"Изменилось условие для условно обязательного поля: {changes['condition']}",
                recommendations=[
                    f"Проверить новое условие для поля '{field_change.path}'",
                    "Обновить сценарии согласно новому условию"
                ]
            )

        # Изменение справочника - high impact
        if "dictionary" in changes:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason=changes["dictionary"],
                recommendations=[
                    f"Обновить значения поля '{field_change.path}' согласно новому справочнику",
                    "Проверить актуальность кодов"
                ]
            )

        # Изменение ограничений
        if "constraints" in changes:
            constraint_desc = changes["constraints"]
            is_restriction = "ужесточено" in constraint_desc.lower()

            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING if is_restriction else ChangeClassification.NON_BREAKING,
                impact=ChangeImpact.HIGH if is_restriction else ChangeImpact.MEDIUM,
                reason=constraint_desc,
                recommendations=[
                    f"Проверить значения поля '{field_change.path}' на соответствие новым ограничениям"
                ]
            )

        # Изменение формата
        if "format" in changes:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.NON_BREAKING,
                impact=ChangeImpact.LOW,
                reason=changes["format"],
                recommendations=[
                    "Проверить соответствие значений новому формату"
                ]
            )

        # Прочие изменения
        all_changes = ", ".join(changes.values())
        return AnalyzedChange(
            field_change=field_change,
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason=all_changes,
            recommendations=[
                "Изменение не требует немедленных действий"
            ]
        )
