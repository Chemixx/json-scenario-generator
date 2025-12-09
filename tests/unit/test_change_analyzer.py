"""
Тесты для модуля change_analyzer
Проверяет анализ изменений между версиями JSON Schema

Обновлено для использования новой 3-уровневой классификации:
- ChangeType (ADDITION/REMOVAL/MODIFICATION)
- BreakingLevel (BREAKING/NON_BREAKING)
- ImpactLevel (CRITICAL/HIGH/MEDIUM/LOW)
"""
import pytest
from pathlib import Path

# ============================================================================
# ИМПОРТЫ (ОБНОВЛЕНО)
# ============================================================================

from src.analyzers import ChangeAnalyzer
from src.models import (
    FieldMetadata,
    FieldChange,
    SchemaDiff,
    ConditionalRequirement,
    AnalyzedChange,
    AnalysisResult,
    # Новые enum'ы
    ChangeType,
    BreakingLevel,
    ImpactLevel,
)


# ============================================================================
# ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def analyzer():
    """Создать экземпляр анализатора"""
    return ChangeAnalyzer()


@pytest.fixture
def sample_field_metadata():
    """Создать пример метаданных поля"""
    return FieldMetadata(
        path="test/field",
        name="field",
        field_type="string",
        is_required=True
    )


@pytest.fixture
def sample_field_change_added(sample_field_metadata):
    """Создать пример добавленного поля"""
    return FieldChange(
        path="test/newField",
        change_type="added",
        new_meta=FieldMetadata(
            path="test/newField",
            name="newField",
            field_type="string",
            is_required=True
        )
    )


@pytest.fixture
def sample_field_change_removed(sample_field_metadata):
    """Создать пример удаленного поля"""
    return FieldChange(
        path="test/oldField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="test/oldField",
            name="oldField",
            field_type="string",
            is_required=True
        )
    )


@pytest.fixture
def sample_field_change_modified():
    """Создать пример измененного поля"""
    return FieldChange(
        path="test/modifiedField",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/modifiedField",
            name="modifiedField",
            field_type="string",
            is_required=False
        ),
        new_meta=FieldMetadata(
            path="test/modifiedField",
            name="modifiedField",
            field_type="integer",
            is_required=True
        ),
        changes={"type": "string → integer", "required": "False → True"}
    )


# ============================================================================
# ТЕСТЫ: Инициализация
# ============================================================================

def test_change_analyzer_initialization(analyzer):
    """Тест: инициализация анализатора"""
    assert analyzer is not None
    assert analyzer.parser is not None
    assert analyzer.comparator is not None


# ============================================================================
# ТЕСТЫ: Анализ добавленных полей
# ============================================================================

def test_analyze_addition_required_field(analyzer):
    """Тест: анализ добавления обязательного поля (О)"""
    field_change = FieldChange(
        path="test/requiredField",
        change_type="added",
        new_meta=FieldMetadata(
            path="test/requiredField",
            name="requiredField",
            field_type="string",
            is_required=True
        )
    )

    result = analyzer._analyze_addition(field_change)

    # Проверка 3-уровневой классификации
    assert result.change_type == ChangeType.ADDITION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.CRITICAL
    assert "обязательное" in result.reason.lower()
    assert len(result.recommendations) > 0


def test_analyze_addition_optional_field(analyzer):
    """Тест: анализ добавления опционального поля (Н)"""
    field_change = FieldChange(
        path="test/optionalField",
        change_type="added",
        new_meta=FieldMetadata(
            path="test/optionalField",
            name="optionalField",
            field_type="string",
            is_required=False
        )
    )

    result = analyzer._analyze_addition(field_change)

    assert result.change_type == ChangeType.ADDITION
    assert result.breaking_level == BreakingLevel.NON_BREAKING
    assert result.impact_level == ImpactLevel.LOW
    assert "опциональное" in result.reason.lower()


def test_analyze_addition_conditional_field(analyzer):
    """Тест: анализ добавления условно обязательного поля (УО)"""
    field_change = FieldChange(
        path="test/conditionalField",
        change_type="added",
        new_meta=FieldMetadata(
            path="test/conditionalField",
            name="conditionalField",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(expression="productType == 'LOAN'")
        )
    )

    result = analyzer._analyze_addition(field_change)

    assert result.change_type == ChangeType.ADDITION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH
    assert "условно обязательное" in result.reason.lower()


# ============================================================================
# ТЕСТЫ: Анализ удаленных полей
# ============================================================================

def test_analyze_removal_required_field(analyzer):
    """Тест: анализ удаления обязательного поля (О)"""
    field_change = FieldChange(
        path="test/requiredField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="test/requiredField",
            name="requiredField",
            field_type="string",
            is_required=True
        )
    )

    result = analyzer._analyze_removal(field_change)

    assert result.change_type == ChangeType.REMOVAL
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH
    assert "обязательное" in result.reason.lower()
    assert any("удалить" in rec.lower() for rec in result.recommendations)


def test_analyze_removal_optional_field(analyzer):
    """Тест: анализ удаления опционального поля (Н)"""
    field_change = FieldChange(
        path="test/optionalField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="test/optionalField",
            name="optionalField",
            field_type="string",
            is_required=False
        )
    )

    result = analyzer._analyze_removal(field_change)

    assert result.change_type == ChangeType.REMOVAL
    assert result.breaking_level == BreakingLevel.BREAKING  # Удаление ВСЕГДА breaking
    assert result.impact_level == ImpactLevel.MEDIUM
    assert "опциональное" in result.reason.lower()


def test_analyze_removal_conditional_field(analyzer):
    """Тест: анализ удаления условно обязательного поля (УО)"""
    field_change = FieldChange(
        path="test/conditionalField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="test/conditionalField",
            name="conditionalField",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(expression="productType == 'LOAN'")
        )
    )

    result = analyzer._analyze_removal(field_change)

    assert result.change_type == ChangeType.REMOVAL
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.MEDIUM
    assert "условно обязательное" in result.reason.lower()


# ============================================================================
# ТЕСТЫ: Анализ изменений полей (МОДИФИКАЦИИ)
# ============================================================================

def test_analyze_modification_type_change(analyzer):
    """Тест: анализ изменения типа поля"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="integer",
            is_required=False
        ),
        changes={"type": "Изменился тип данных: string → integer"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.CRITICAL
    assert "тип" in result.reason.lower()


def test_analyze_modification_became_required(analyzer):
    """Тест: анализ поля, которое стало обязательным (Н → О)"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=True
        ),
        changes={"required": "Поле стало обязательным (Н → О)"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.CRITICAL
    assert "обязательным" in result.reason.lower()


def test_analyze_modification_became_optional(analyzer):
    """Тест: анализ поля, которое стало опциональным (О → Н)"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=True
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False
        ),
        changes={"required": "Поле стало опциональным (О → Н)"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.NON_BREAKING
    assert result.impact_level == ImpactLevel.LOW
    assert "опциональным" in result.reason.lower()


def test_analyze_modification_became_conditional(analyzer):
    """Тест: анализ поля, которое стало условно обязательным (Н → УО)"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=False
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(expression="productType == 'LOAN'")
        ),
        changes={"conditional": "Поле стало условно обязательным (Н → УО)"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH
    assert "условно обязательным" in result.reason.lower()
    assert any("услови" in rec.lower() for rec in result.recommendations)


def test_analyze_modification_no_longer_conditional(analyzer):
    """Тест: анализ поля, которое перестало быть УО (УО → Н)"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(expression="productType == 'LOAN'")
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=False
        ),
        changes={"conditional": "Поле перестало быть условно обязательным"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.NON_BREAKING
    assert result.impact_level == ImpactLevel.LOW
    assert "перестало" in result.reason.lower()


def test_analyze_modification_condition_changed(analyzer):
    """Тест: анализ изменения условия УО"""
    old_condition = ConditionalRequirement(expression="productType == 'LOAN'")
    new_condition = ConditionalRequirement(expression="productType == 'CARD'")

    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=old_condition
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=new_condition
        ),
        changes={"condition": "Условие изменилось"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH
    assert "условие" in result.reason.lower()


def test_analyze_modification_dictionary_change(analyzer):
    """Тест: анализ изменения справочника"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            dictionary="OLD_DICT"
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            dictionary="NEW_DICT"
        ),
        changes={"dictionary": "Изменился справочник: 'OLD_DICT' → 'NEW_DICT'"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH
    assert "справочник" in result.reason.lower()


def test_analyze_modification_constraints_tightening(analyzer):
    """Тест: анализ ужесточения ограничений"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            constraints={"maxLength": 100}
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            constraints={"maxLength": 50}
        ),
        changes={"constraints": "Ужесточены ограничения: maxLength 100 → 50"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.BREAKING
    assert result.impact_level == ImpactLevel.HIGH


def test_analyze_modification_constraints_relaxation(analyzer):
    """Тест: анализ смягчения ограничений"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            constraints={"maxLength": 50}
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            constraints={"maxLength": 100}
        ),
        changes={"constraints": "Смягчены ограничения: maxLength 50 → 100"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.NON_BREAKING
    assert result.impact_level == ImpactLevel.MEDIUM


def test_analyze_modification_other_changes(analyzer):
    """Тест: анализ прочих изменений"""
    field_change = FieldChange(
        path="test/field",
        change_type="modified",
        old_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            description="Old description"
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            description="New description"
        ),
        changes={"description": "old → new"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.breaking_level == BreakingLevel.NON_BREAKING
    assert result.impact_level == ImpactLevel.LOW


# ============================================================================
# ТЕСТЫ: AnalyzedChange (properties и методы)
# ============================================================================

def test_analyzed_change_properties(sample_field_change_added):
    """Тест: свойства AnalyzedChange"""
    analyzed = AnalyzedChange(
        field_change=sample_field_change_added,
        change_type=ChangeType.ADDITION,
        breaking_level=BreakingLevel.BREAKING,
        impact_level=ImpactLevel.CRITICAL,
        reason="Test reason",
        recommendations=["Recommendation 1", "Recommendation 2"]
    )

    # Проверка свойств
    assert analyzed.path == "test/newField"
    assert analyzed.is_breaking == True
    assert analyzed.is_critical == True
    assert analyzed.priority == 0  # CRITICAL = 0


def test_analyzed_change_to_dict(sample_field_change_added):
    """Тест: преобразование AnalyzedChange в словарь"""
    analyzed = AnalyzedChange(
        field_change=sample_field_change_added,
        change_type=ChangeType.ADDITION,
        breaking_level=BreakingLevel.BREAKING,
        impact_level=ImpactLevel.CRITICAL,
        reason="Test reason",
        recommendations=["Recommendation 1", "Recommendation 2"]
    )

    result = analyzed.to_dict()

    assert result["path"] == "test/newField"
    assert result["change_type"] == "addition"
    assert result["breaking_level"] == "breaking"
    assert result["impact_level"] == "critical"
    assert result["reason"] == "Test reason"
    assert len(result["recommendations"]) == 2


# ============================================================================
# ТЕСТЫ: AnalysisResult (properties и методы)
# ============================================================================

def test_analysis_result_initialization():
    """Тест: инициализация результата анализа"""
    result = AnalysisResult(
        old_version="V072Call1Rq",
        new_version="V073Call1Rq",
        analyzed_changes=[]
    )

    assert result.old_version == "V072Call1Rq"
    assert result.new_version == "V073Call1Rq"
    assert len(result.analyzed_changes) == 0


def test_analysis_result_breaking_changes():
    """Тест: получение breaking changes"""
    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.NON_BREAKING,
            impact_level=ImpactLevel.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = AnalysisResult(
        old_version="V072",
        new_version="V073",
        analyzed_changes=changes
    )

    breaking = result.breaking_changes
    assert len(breaking) == 1
    assert breaking[0].breaking_level == BreakingLevel.BREAKING


def test_analysis_result_statistics():
    """Тест: статистика результата анализа"""
    changes = [
        AnalyzedChange(
            field_change=FieldChange(
                path="test1",
                change_type="added",
                new_meta=FieldMetadata(path="test1", name="test1", field_type="string")
            ),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="removed"),
            change_type=ChangeType.REMOVAL,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.HIGH,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test3", change_type="modified"),
            change_type=ChangeType.MODIFICATION,
            breaking_level=BreakingLevel.NON_BREAKING,
            impact_level=ImpactLevel.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = AnalysisResult(
        old_version="V072",
        new_version="V073",
        analyzed_changes=changes
    )

    stats = result.statistics

    assert stats["total_changes"] == 3
    assert stats["change_types"]["additions"] == 1
    assert stats["change_types"]["removals"] == 1
    assert stats["change_types"]["modifications"] == 1
    assert stats["breaking_level"]["breaking"] == 2
    assert stats["breaking_level"]["non_breaking"] == 1
    assert stats["impact_level"]["critical"] == 1
    assert stats["impact_level"]["high"] == 1
    assert stats["impact_level"]["low"] == 1


def test_analysis_result_has_critical_changes():
    """Тест: проверка наличия критических изменений"""
    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.CRITICAL,
            reason="Test",
            recommendations=[]
        )
    ]

    result = AnalysisResult(
        old_version="V072",
        new_version="V073",
        analyzed_changes=changes
    )

    assert result.has_critical_changes() == True
    assert result.has_breaking_changes() == True
    assert result.requires_scenario_update() == True


def test_analysis_result_get_sorted_changes():
    """Тест: сортировка изменений"""
    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="aaa", change_type="added"),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.NON_BREAKING,
            impact_level=ImpactLevel.LOW,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="zzz", change_type="added"),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="mmm", change_type="modified"),
            change_type=ChangeType.MODIFICATION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.HIGH,
            reason="Test",
            recommendations=[]
        )
    ]

    result = AnalysisResult(
        old_version="V072",
        new_version="V073",
        analyzed_changes=changes
    )

    # Сортировка по приоритету (critical first)
    sorted_by_priority = result.get_sorted_changes(by="priority")
    assert sorted_by_priority[0].impact_level == ImpactLevel.CRITICAL
    assert sorted_by_priority[1].impact_level == ImpactLevel.HIGH
    assert sorted_by_priority[2].impact_level == ImpactLevel.LOW

    # Сортировка по пути
    sorted_by_path = result.get_sorted_changes(by="path")
    assert sorted_by_path[0].path == "aaa"
    assert sorted_by_path[1].path == "mmm"
    assert sorted_by_path[2].path == "zzz"


def test_analysis_result_to_dict():
    """Тест: преобразование результата в словарь"""
    changes = [
        AnalyzedChange(
            field_change=FieldChange(
                path="test1",
                change_type="added",
                new_meta=FieldMetadata(
                    path="test1",
                    name="test1",
                    field_type="string"
                )
            ),
            change_type=ChangeType.ADDITION,
            breaking_level=BreakingLevel.BREAKING,
            impact_level=ImpactLevel.CRITICAL,
            reason="Test",
            recommendations=[]
        )
    ]

    result = AnalysisResult(
        old_version="V072",
        new_version="V073",
        analyzed_changes=changes
    )

    result_dict = result.to_dict()

    assert result_dict["old_version"] == "V072"
    assert result_dict["new_version"] == "V073"
    assert "generated_at" not in result_dict  # Нет generated_at в AnalysisResult.to_dict()
    assert "statistics" in result_dict
    assert len(result_dict["changes"]) == 1


# ============================================================================
# НОВЫЕ ТЕСТЫ: Enum методы
# ============================================================================

def test_change_type_to_russian():
    """Тест: преобразование ChangeType в русский"""
    assert ChangeType.ADDITION.to_russian() == "Добавление"
    assert ChangeType.REMOVAL.to_russian() == "Удаление"
    assert ChangeType.MODIFICATION.to_russian() == "Модификация"


def test_impact_level_to_emoji():
    """Тест: эмодзи для ImpactLevel"""
    assert ImpactLevel.CRITICAL.to_emoji() == "🔴"
    assert ImpactLevel.HIGH.to_emoji() == "🟠"
    assert ImpactLevel.MEDIUM.to_emoji() == "🟡"
    assert ImpactLevel.LOW.to_emoji() == "🟢"


def test_impact_level_to_priority():
    """Тест: числовой приоритет для ImpactLevel"""
    assert ImpactLevel.CRITICAL.to_priority() == 0
    assert ImpactLevel.HIGH.to_priority() == 1
    assert ImpactLevel.MEDIUM.to_priority() == 2
    assert ImpactLevel.LOW.to_priority() == 3