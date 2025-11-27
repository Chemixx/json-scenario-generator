"""
Анализатор изменений между версиями JSON Schema
Классифицирует изменения и определяет их влияние на сценарии
"""
from enum import Enum
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from src.parsers.schema_parser import SchemaParser
from src.models.schema_models import SchemaDiff, FieldChange
from src.utils.logger import get_logger


class ChangeClassification(str, Enum):
    """Классификация типов изменений"""
    BREAKING = "breaking"  # Несовместимое изменение
    NON_BREAKING = "non_breaking"  # Совместимое изменение
    ADDITION = "addition"  # Добавление нового поля
    REMOVAL = "removal"  # Удаление поля
    DEPRECATION = "deprecation"  # Устаревшее поле


class ChangeImpact(str, Enum):
    """Уровень влияния изменения"""
    CRITICAL = "critical"  # Критическое - требует немедленных действий
    HIGH = "high"  # Высокое - требует обновления сценариев
    MEDIUM = "medium"  # Среднее - желательно обновить
    LOW = "low"  # Низкое - можно игнорировать
    NONE = "none"  # Нет влияния


@dataclass
class AnalyzedChange:
    """
    Проанализированное изменение с классификацией

    Attributes:
        field_change: Изменение поля из SchemaDiff
        classification: Тип изменения
        impact: Уровень влияния
        reason: Причина классификации
        recommendations: Рекомендации по исправлению
    """
    field_change: FieldChange
    classification: ChangeClassification
    impact: ChangeImpact
    reason: str
    recommendations: List[str]

    def to_dict(self) -> Dict:
        """Преобразовать в словарь"""
        return {
            "path": self.field_change.path,
            "change_type": self.field_change.change_type,
            "classification": self.classification.value,
            "impact": self.impact.value,
            "reason": self.reason,
            "recommendations": self.recommendations,
            "changes": self.field_change.changes
        }


class ChangeAnalyzer:
    """
    Анализатор изменений между версиями JSON Schema

    Определяет тип изменений (breaking/non-breaking) и их влияние на сценарии

    Example:
        .. code-block:: python

            analyzer = ChangeAnalyzer()

            # Сравнить две версии
            analysis = analyzer.analyze_changes(
                old_schema_path=Path("v1.0.json"),
                new_schema_path=Path("v2.0.json")
            )

            # Получить критические изменения
            critical = analysis.get_critical_changes()
            print(f"Найдено {len(critical)} критических изменений")
    """

    def __init__(self):
        """Инициализация анализатора"""
        self.logger = get_logger(self.__class__.__name__)
        self.parser = SchemaParser()

    def analyze_changes(
        self,
        old_schema_path: Path,
        new_schema_path: Path
    ) -> "ChangeAnalysisResult":
        """
        Проанализировать изменения между версиями

        Args:
            old_schema_path: Путь к старой версии схемы
            new_schema_path: Путь к новой версии схемы

        Returns:
            Результат анализа с классификацией изменений

        Example:
            .. code-block:: python

                result = analyzer.analyze_changes(
                    Path("schemas/v1.json"),
                    Path("schemas/v2.json")
                )
                print(f"Breaking changes: {len(result.breaking_changes)}")
        """
        self.logger.info(f"🔍 Анализ изменений между версиями")

        # Загружаем и парсим старую схему
        old_schema = self.parser.load_schema(old_schema_path)
        old_fields = self.parser.parse_schema(old_schema)

        # Загружаем и парсим новую схему
        new_schema = self.parser.load_schema(new_schema_path)
        new_fields = self.parser.parse_schema(new_schema)

        # Сравниваем схемы
        diff = self.parser.compare_schemas(old_fields, new_fields)

        # Анализируем изменения
        analyzed_changes = self._analyze_diff(diff)

        # Создаем результат
        result = ChangeAnalysisResult(
            old_schema=old_schema_path,
            new_schema=new_schema_path,
            diff=diff,
            analyzed_changes=analyzed_changes
        )

        self.logger.info(
            f"✅ Анализ завершен: {len(result.breaking_changes)} breaking, "
            f"{len(result.non_breaking_changes)} non-breaking"
        )

        return result

    def _analyze_diff(self, diff: SchemaDiff) -> List[AnalyzedChange]:
        """
        Проанализировать различия и классифицировать изменения

        Args:
            diff: Различия между схемами

        Returns:
            Список проанализированных изменений
        """
        analyzed = []

        # Анализируем добавленные поля
        for field_change in diff.added_fields:
            analyzed.append(self._analyze_addition(field_change))

        # Анализируем удаленные поля
        for field_change in diff.removed_fields:
            analyzed.append(self._analyze_removal(field_change))

        # Анализируем измененные поля
        for field_change in diff.modified_fields:
            analyzed.append(self._analyze_modification(field_change))

        return analyzed

    def _analyze_addition(self, field_change: FieldChange) -> AnalyzedChange:
        """Проанализировать добавление поля"""
        field = field_change.new_meta

        # Обязательное новое поле - breaking change
        if field and field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.CRITICAL,
                reason="Добавлено новое обязательное поле",
                recommendations=[
                    f"Добавить поле '{field_change.path}' во все существующие сценарии",
                    f"Определить значение по умолчанию для поля",
                    f"Обновить валидацию сценариев"
                ]
            )

        # Условно обязательное новое поле - medium impact
        if field and field.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.ADDITION,
                impact=ChangeImpact.MEDIUM,
                reason="Добавлено новое условно обязательное поле (УО)",
                recommendations=[
                    f"Проверить условия для поля '{field_change.path}'",
                    f"Добавить поле в сценарии, где выполняются условия",
                    "Изучить условие обязательности"
                ]
            )

        # Опциональное новое поле - non-breaking
        return AnalyzedChange(
            field_change=field_change,
            classification=ChangeClassification.ADDITION,
            impact=ChangeImpact.LOW,
            reason="Добавлено новое опциональное поле",
            recommendations=[
                f"Рассмотреть возможность использования поля '{field_change.path}' в сценариях",
                "Поле можно игнорировать без последствий"
            ]
        )

    def _analyze_removal(self, field_change: FieldChange) -> AnalyzedChange:
        """Проанализировать удаление поля"""
        field = field_change.old_meta

        # Удаление обязательного поля - critical
        if field and field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.REMOVAL,
                impact=ChangeImpact.CRITICAL,
                reason="Удалено обязательное поле",
                recommendations=[
                    f"УДАЛИТЬ поле '{field_change.path}' из всех сценариев",
                    "Найти альтернативное поле, если требуется",
                    "Обновить документацию"
                ]
            )

        # Удаление условно обязательного поля - medium impact
        if field and field.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.REMOVAL,
                impact=ChangeImpact.MEDIUM,
                reason="Удалено условно обязательное поле (УО)",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из сценариев, где оно используется",
                    "Проверить, не влияет ли это на условную логику"
                ]
            )

        # Удаление опционального поля - medium impact
        return AnalyzedChange(
            field_change=field_change,
            classification=ChangeClassification.REMOVAL,
            impact=ChangeImpact.MEDIUM,
            reason="Удалено опциональное поле",
            recommendations=[
                f"Удалить поле '{field_change.path}' из сценариев (если используется)",
                "Проверить, не влияет ли это на логику тестов"
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
                reason=f"Изменен тип поля: {changes['type']}",
                recommendations=[
                    f"Обновить значения поля '{field_change.path}' в соответствии с новым типом",
                    f"Преобразовать данные согласно изменению типа",
                    "Проверить совместимость с существующими данными"
                ]
            )

        # Поле стало обязательным - breaking
        if "required" in changes and "→ True" in changes["required"]:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason="Поле стало обязательным",
                recommendations=[
                    f"Добавить поле '{field_change.path}' во все сценарии, где оно отсутствует",
                    "Определить подходящие значения для поля"
                ]
            )

        # Поле стало опциональным - non-breaking
        if "required" in changes and "→ False" in changes["required"]:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.NON_BREAKING,
                impact=ChangeImpact.LOW,
                reason="Поле стало опциональным",
                recommendations=[
                    "Изменение не требует обновления сценариев",
                    f"Можно удалить поле '{field_change.path}' из сценариев (опционально)"
                ]
            )

        # ✅ Поле стало условно обязательным (Н → УО)
        if "conditional" in changes and "False → True" in changes["conditional"]:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason="Поле стало условно обязательным (УО)",
                recommendations=[
                    f"Проверить условия для поля '{field_change.path}'",
                    f"Добавить поле в сценарии, где выполняются условия",
                    "Изучить новое условие обязательности"
                ]
            )

        # ✅ Поле перестало быть УО (УО → Н)
        if "conditional" in changes and "True → False" in changes["conditional"]:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.NON_BREAKING,
                impact=ChangeImpact.LOW,
                reason="Поле перестало быть условно обязательным",
                recommendations=[
                    "Изменение не требует немедленных действий",
                    f"Поле '{field_change.path}' теперь опциональное"
                ]
            )

        # ✅ Изменилось условие УО
        if "condition" in changes:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason="Изменилось условие для условно обязательного поля",
                recommendations=[
                    f"Проверить новое условие для поля '{field_change.path}'",
                    "Обновить сценарии согласно новому условию",
                    "Изучить детали изменения условия"
                ]
            )

        # Изменение справочника - high impact
        if "dictionary" in changes:
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.BREAKING,
                impact=ChangeImpact.HIGH,
                reason=f"Изменен справочник: {changes['dictionary']}",
                recommendations=[
                    f"Обновить значения поля '{field_change.path}' согласно новому справочнику",
                    f"Проверить актуальность кодов нового справочника",
                    "Загрузить новую версию справочника"
                ]
            )

        # Изменение ограничений - medium impact
        if any(key in changes for key in ["minLength", "maxLength", "minimum", "maximum", "pattern"]):
            constraint_changes = [f"{k}: {v}" for k, v in changes.items() if k in ["minLength", "maxLength", "minimum", "maximum", "pattern"]]
            return AnalyzedChange(
                field_change=field_change,
                classification=ChangeClassification.NON_BREAKING,
                impact=ChangeImpact.MEDIUM,
                reason=f"Изменены ограничения поля: {', '.join(constraint_changes)}",
                recommendations=[
                    f"Проверить значения поля '{field_change.path}' на соответствие новым ограничениям",
                    f"Обновить тестовые данные при необходимости"
                ]
            )

        # Прочие изменения - low impact
        return AnalyzedChange(
            field_change=field_change,
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason=f"Изменены свойства: {', '.join(changes.keys())}",
            recommendations=[
                "Изменение не требует немедленных действий",
                "Рассмотреть обновление при следующей ревизии сценариев"
            ]
        )


class ChangeAnalysisResult:
    """
    Результат анализа изменений

    Attributes:
        old_schema: Путь к старой схеме
        new_schema: Путь к новой схеме
        diff: Различия между схемами
        analyzed_changes: Проанализированные изменения
    """

    def __init__(
        self,
        old_schema: Path,
        new_schema: Path,
        diff: SchemaDiff,
        analyzed_changes: List[AnalyzedChange]
    ):
        self.old_schema = old_schema
        self.new_schema = new_schema
        self.diff = diff
        self.analyzed_changes = analyzed_changes

    @property
    def breaking_changes(self) -> List[AnalyzedChange]:
        """Получить breaking changes"""
        return [
            c for c in self.analyzed_changes
            if c.classification == ChangeClassification.BREAKING
        ]

    @property
    def non_breaking_changes(self) -> List[AnalyzedChange]:
        """Получить non-breaking changes"""
        return [
            c for c in self.analyzed_changes
            if c.classification == ChangeClassification.NON_BREAKING
        ]

    @property
    def critical_changes(self) -> List[AnalyzedChange]:
        """Получить критические изменения"""
        return [
            c for c in self.analyzed_changes
            if c.impact == ChangeImpact.CRITICAL
        ]

    @property
    def high_impact_changes(self) -> List[AnalyzedChange]:
        """Получить изменения с высоким влиянием"""
        return [
            c for c in self.analyzed_changes
            if c.impact == ChangeImpact.HIGH
        ]

    def get_changes_by_impact(self, impact: ChangeImpact) -> List[AnalyzedChange]:
        """Получить изменения по уровню влияния"""
        return [c for c in self.analyzed_changes if c.impact == impact]

    def get_changes_by_classification(
        self,
        classification: ChangeClassification
    ) -> List[AnalyzedChange]:
        """Получить изменения по классификации"""
        return [c for c in self.analyzed_changes if c.classification == classification]

    def to_dict(self) -> Dict:
        """Преобразовать результат в словарь"""
        return {
            "old_schema": str(self.old_schema),
            "new_schema": str(self.new_schema),
            "summary": {
                "total_changes": len(self.analyzed_changes),
                "breaking_changes": len(self.breaking_changes),
                "non_breaking_changes": len(self.non_breaking_changes),
                "critical_impact": len(self.critical_changes),
                "high_impact": len(self.high_impact_changes)
            },
            "changes": [c.to_dict() for c in self.analyzed_changes]
        }
