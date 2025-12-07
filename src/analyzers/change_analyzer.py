"""
Анализатор изменений между версиями JSON Schema

Этот модуль отвечает за детальный анализ изменений между двумя версиями схем.
Для каждого изменения определяется:
- ТИП изменения (addition/removal/modification)
- BREAKING уровень (breaking/non-breaking)
- УРОВЕНЬ ВЛИЯНИЯ (critical/high/medium/low)
"""

from typing import List
from pathlib import Path

from src.models import (
    SchemaDiff,
    FieldChange,
    FieldMetadata,
    AnalyzedChange,
    AnalysisResult,
    ChangeType,
    BreakingLevel,
    ImpactLevel,
)
from src.parsers import SchemaParser
from src.core import SchemaComparator
from src.utils import get_logger

logger = get_logger(__name__)


class ChangeAnalyzer:
    """
    Анализатор изменений между версиями схем

    Использует SchemaComparator для получения diff'а, затем классифицирует
    каждое изменение по трем независимым критериям:
    1. ChangeType — ЧТО произошло (добавление/удаление/модификация)
    2. BreakingLevel — ЛОМАЕТ ли API (breaking/non-breaking)
    3. ImpactLevel — Насколько КРИТИЧНО (critical/high/medium/low)

    Examples:
        >>> analyzer = ChangeAnalyzer()
        >>> result = analyzer.analyze_changes(
        ...     Path("schemas/V072Call1Rq.json"),
        ...     Path("schemas/V073Call1Rq.json")
        ... )
        >>> print(f"Breaking changes: {len(result.breaking_changes)}")
    """

    def __init__(self):
        self.parser = SchemaParser()
        self.comparator = SchemaComparator()

    def analyze_changes(
        self,
        old_schema_path: Path,
        new_schema_path: Path
    ) -> AnalysisResult:
        """
        Проанализировать изменения между двумя схемами

        Args:
            old_schema_path: Путь к старой схеме (например, V072Call1Rq.json)
            new_schema_path: Путь к новой схеме (например, V073Call1Rq.json)

        Returns:
            AnalysisResult с детальной классификацией всех изменений

        Raises:
            FileNotFoundError: Если схемы не найдены
            ValidationError: Если схемы невалидны
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
        analyzed_changes: List[AnalyzedChange] = []

        # Анализ добавленных полей
        for field_change in diff.added_fields:
            analyzed_changes.append(self._analyze_addition(field_change))

        # Анализ удаленных полей
        for field_change in diff.removed_fields:
            analyzed_changes.append(self._analyze_removal(field_change))

        # Анализ измененных полей
        for field_change in diff.modified_fields:
            analyzed_changes.append(self._analyze_modification(field_change))

        # Логирование результатов
        breaking_count = len([c for c in analyzed_changes if c.breaking_level == BreakingLevel.BREAKING])
        non_breaking_count = len([c for c in analyzed_changes if c.breaking_level == BreakingLevel.NON_BREAKING])

        logger.info(
            f"✅ Анализ завершен: {breaking_count} breaking, {non_breaking_count} non-breaking"
        )

        return AnalysisResult(
            old_version=old_schema_path.stem,  # "V072Call1Rq" без расширения
            new_version=new_schema_path.stem,  # "V073Call1Rq"
            analyzed_changes=analyzed_changes
        )

    # ========================================================================
    # МЕТОДЫ АНАЛИЗА ИЗМЕНЕНИЙ
    # ========================================================================

    def _analyze_addition(self, field_change: FieldChange) -> AnalyzedChange:
        """
        Проанализировать добавление поля

        Правила классификации:
        - Обязательное (О) → BREAKING + CRITICAL
        - Условно обязательное (УО) → BREAKING + HIGH
        - Не обязательное (Н) → NON_BREAKING + LOW

        Args:
            field_change: Изменение с типом 'added'

        Returns:
            AnalyzedChange с классификацией
        """
        new_field = field_change.new_meta

        # Обязательное поле (О)
        if new_field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.ADDITION,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.CRITICAL,
                reason="Добавлено новое обязательное поле (О)",
                recommendations=[
                    f"КРИТИЧНО: Добавить поле '{field_change.path}' во ВСЕ существующие сценарии",
                    "Определить корректные значения для нового обязательного поля",
                    "Все запросы БЕЗ этого поля будут отклонены API"
                ]
            )

        # Условно обязательное поле (УО)
        elif new_field.is_conditional:
            condition_text = self._format_condition_brief(new_field.condition)

            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.ADDITION,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.HIGH,
                reason=f"Добавлено новое условно обязательное поле (УО)",
                recommendations=[
                    f"Проверить условие: {condition_text}",
                    f"Добавить поле '{field_change.path}' в сценарии, где выполняются условия",
                    "Запросы без поля будут отклонены, если условие выполняется"
                ]
            )

        # Опциональное поле (Н)
        else:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.ADDITION,
                breaking_level=BreakingLevel.NON_BREAKING,
                impact_level=ImpactLevel.LOW,
                reason="Добавлено новое опциональное поле (Н)",
                recommendations=[
                    "Изменение не требует обновления существующих сценариев",
                    f"Можно использовать новое поле '{field_change.path}' в новых сценариях"
                ]
            )

    def _analyze_removal(self, field_change: FieldChange) -> AnalyzedChange:
        """
        Проанализировать удаление поля

        Правила классификации:
        - Обязательное (О) → BREAKING + HIGH
        - Условно обязательное (УО) → BREAKING + MEDIUM
        - Не обязательное (Н) → BREAKING + MEDIUM (удаление ВСЕГДА breaking)

        Args:
            field_change: Изменение с типом 'removed'

        Returns:
            AnalyzedChange с классификацией
        """
        old_field = field_change.old_meta

        # Обязательное поле (О)
        if old_field.is_required:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.REMOVAL,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.HIGH,
                reason="Удалено обязательное поле (О)",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из ВСЕХ сценариев",
                    "API будет отклонять запросы с этим полем",
                    "Проверить, не используется ли поле в логике тестов"
                ]
            )

        # Условно обязательное поле (УО)
        elif old_field.is_conditional:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.REMOVAL,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.MEDIUM,
                reason="Удалено условно обязательное поле (УО)",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из сценариев",
                    "Проверить условия, при которых поле использовалось"
                ]
            )

        # Опциональное поле (Н) - удаление ВСЕГДА breaking (может ломать клиентов)
        else:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.REMOVAL,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.MEDIUM,
                reason="Удалено опциональное поле (Н)",
                recommendations=[
                    f"Удалить поле '{field_change.path}' из сценариев, если оно используется",
                    "API может отклонять запросы с неизвестными полями (зависит от реализации)"
                ]
            )

    def _analyze_modification(self, field_change: FieldChange) -> AnalyzedChange:
        """
        Проанализировать изменение (модификацию) поля

        Проверяет различные типы изменений в приоритетном порядке:
        1. Изменение типа данных → BREAKING + CRITICAL
        2. Изменение обязательности (Н → О) → BREAKING + CRITICAL
        3. Изменение на УО (Н → УО) → BREAKING + HIGH
        4. Изменение условия УО → BREAKING + HIGH
        5. Изменение справочника → BREAKING + HIGH
        6. Ужесточение ограничений → BREAKING + HIGH
        7. Смягчение ограничений → NON_BREAKING + LOW
        8. Прочие изменения → NON_BREAKING + LOW

        Args:
            field_change: Изменение с типом 'modified'

        Returns:
            AnalyzedChange с классификацией
        """
        changes = field_change.changes
        old_field = field_change.old_meta
        new_field = field_change.new_meta

        # 1. Изменение типа данных - CRITICAL
        if "type" in changes:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.MODIFICATION,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.CRITICAL,
                reason=f"Изменился тип данных: {changes['type']}",
                recommendations=[
                    f"КРИТИЧНО: Обновить значения поля '{field_change.path}' в соответствии с новым типом",
                    "Преобразовать данные согласно изменению типа во ВСЕХ сценариях",
                    "Все запросы со старым типом будут отклонены"
                ]
            )

        # 2. Изменение обязательности
        if "required" in changes:
            if "стало обязательным" in changes["required"].lower():
                # Н → О или УО → О
                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.BREAKING,
                    impact_level=ImpactLevel.CRITICAL,
                    reason=f"Поле стало обязательным: {changes['required']}",
                    recommendations=[
                        f"КРИТИЧНО: Добавить поле '{field_change.path}' во ВСЕ сценарии, где оно отсутствует",
                        "Все запросы БЕЗ этого поля будут отклонены"
                    ]
                )
            else:
                # О → Н или УО → Н (смягчение)
                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.NON_BREAKING,
                    impact_level=ImpactLevel.LOW,
                    reason=f"Поле стало опциональным: {changes['required']}",
                    recommendations=[
                        "Изменение не требует обновления сценариев",
                        f"Поле '{field_change.path}' можно не передавать"
                    ]
                )

        # 3. Изменение на условно обязательное
        if "conditional" in changes:
            if "стало условно обязательным" in changes["conditional"].lower():
                # Н → УО
                condition_text = self._format_condition_brief(new_field.condition)

                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.BREAKING,
                    impact_level=ImpactLevel.HIGH,
                    reason=f"Поле стало условно обязательным (Н → УО)",
                    recommendations=[
                        f"Проверить условие: {condition_text}",
                        f"Добавить поле '{field_change.path}' в сценарии, где выполняются условия",
                        "Запросы без поля будут отклонены при выполнении условия"
                    ]
                )
            else:
                # УО → Н (смягчение)
                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.NON_BREAKING,
                    impact_level=ImpactLevel.LOW,
                    reason=f"Поле перестало быть условно обязательным: {changes['conditional']}",
                    recommendations=[
                        "Изменение не требует немедленных действий"
                    ]
                )

        # 4. Изменилось условие УО (поле УО и было УО)
        if "condition" in changes and new_field and new_field.is_conditional:
            condition_change_desc = changes['condition']

            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.MODIFICATION,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.HIGH,
                reason=f"Изменилось условие для условно обязательного поля (УО): {condition_change_desc}",
                recommendations=[
                    f"Проверить новое условие для поля '{field_change.path}'",
                    "Обновить сценарии согласно новому условию",
                    f"Детали изменения: {condition_change_desc}"
                ]
            )

        # 5. Изменение справочника
        if "dictionary" in changes:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.MODIFICATION,
                breaking_level=BreakingLevel.BREAKING,
                impact_level=ImpactLevel.HIGH,
                reason=f"Изменился справочник: {changes['dictionary']}",
                recommendations=[
                    f"Обновить значения поля '{field_change.path}' согласно новому справочнику",
                    "Проверить актуальность кодов во ВСЕХ сценариях",
                    "Старые коды могут быть отклонены API"
                ]
            )

        # 6. Изменение ограничений (constraints)
        if "constraints" in changes:
            constraint_desc = changes["constraints"]
            is_restriction = any(
                keyword in constraint_desc.lower()
                for keyword in ["ужесточено", "уменьшился", "увеличился минимум"]
            )

            if is_restriction:
                # Ужесточение (breaking)
                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.BREAKING,
                    impact_level=ImpactLevel.HIGH,
                    reason=f"Ужесточены ограничения: {constraint_desc}",
                    recommendations=[
                        f"Проверить значения поля '{field_change.path}' на соответствие новым ограничениям",
                        "Значения, не соответствующие новым ограничениям, будут отклонены"
                    ]
                )
            else:
                # Смягчение (non-breaking)
                return AnalyzedChange(
                    field_change=field_change,
                    change_type=ChangeType.MODIFICATION,
                    breaking_level=BreakingLevel.NON_BREAKING,
                    impact_level=ImpactLevel.MEDIUM,
                    reason=f"Смягчены ограничения: {constraint_desc}",
                    recommendations=[
                        "Изменение не требует обновления существующих сценариев",
                        f"Теперь допустимы более широкие значения для '{field_change.path}'"
                    ]
                )

        # 7. Изменение формата (обычно non-breaking, если не ужесточение)
        if "format" in changes:
            return AnalyzedChange(
                field_change=field_change,
                change_type=ChangeType.MODIFICATION,
                breaking_level=BreakingLevel.NON_BREAKING,
                impact_level=ImpactLevel.LOW,
                reason=f"Изменился формат: {changes['format']}",
                recommendations=[
                    "Проверить соответствие значений новому формату",
                    f"Формат поля '{field_change.path}': {changes['format']}"
                ]
            )

        # 8. Прочие изменения (по умолчанию non-breaking)
        all_changes = ", ".join(changes.values())
        return AnalyzedChange(
            field_change=field_change,
            change_type=ChangeType.MODIFICATION,
            breaking_level=BreakingLevel.NON_BREAKING,
            impact_level=ImpactLevel.LOW,
            reason=f"Прочие изменения: {all_changes}",
            recommendations=[
                "Изменение не требует немедленных действий"
            ]
        )

    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================================================

    def _format_condition_brief(self, condition) -> str:
        """
        Краткое форматирование условия (пока без SpelFormatter)

        TODO: После создания SpelFormatter использовать его

        Args:
            condition: ConditionalRequirement или None

        Returns:
            Краткое описание условия
        """
        if not condition:
            return "нет условия"

        # Пока просто обрезаем выражение
        expr = condition.expression
        if len(expr) > 100:
            return f"{expr[:100]}..."
        return expr
