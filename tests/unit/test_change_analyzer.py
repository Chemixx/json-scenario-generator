"""
Тесты для модуля change_analyzer
Проверяет анализ изменений между версиями JSON Schema
"""
import pytest
from pathlib import Path

from src.analyzers.change_analyzer import (
    ChangeAnalyzer,
    ChangeClassification,
    ChangeImpact,
    AnalyzedChange,
    ChangeAnalysisResult
)
from src.models.schema_models import FieldMetadata, FieldChange, SchemaDiff


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


@pytest.fixture
def sample_schema_diff():
    """Создать пример различий между схемами"""
    diff = SchemaDiff(
        old_version="1.0",
        new_version="2.0",
        call="Call1"
    )

    # Добавленные поля
    diff.added_fields.append(
        FieldChange(
            path="new/requiredField",
            change_type="added",
            new_meta=FieldMetadata(
                path="new/requiredField",
                name="requiredField",
                field_type="string",
                is_required=True
            )
        )
    )

    diff.added_fields.append(
        FieldChange(
            path="new/optionalField",
            change_type="added",
            new_meta=FieldMetadata(
                path="new/optionalField",
                name="optionalField",
                field_type="string",
                is_required=False
            )
        )
    )

    # Удаленные поля
    diff.removed_fields.append(
        FieldChange(
            path="old/removedField",
            change_type="removed",
            old_meta=FieldMetadata(
                path="old/removedField",
                name="removedField",
                field_type="string",
                is_required=True
            )
        )
    )

    # Измененные поля
    diff.modified_fields.append(
        FieldChange(
            path="modified/typeChange",
            change_type="modified",
            old_meta=FieldMetadata(
                path="modified/typeChange",
                name="typeChange",
                field_type="string",
                is_required=False
            ),
            new_meta=FieldMetadata(
                path="modified/typeChange",
                name="typeChange",
                field_type="integer",
                is_required=False
            ),
            changes={"type": "string → integer"}
        )
    )

    return diff


# ============================================================================
# ТЕСТЫ: Инициализация
# ============================================================================

def test_change_analyzer_initialization(analyzer):
    """Тест: инициализация анализатора"""
    assert analyzer is not None
    assert analyzer.parser is not None
    assert analyzer.logger is not None


# ============================================================================
# ТЕСТЫ: Анализ добавленных полей
# ============================================================================

def test_analyze_addition_required_field(analyzer):
    """Тест: анализ добавления обязательного поля"""
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

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.CRITICAL
    assert "обязательное" in result.reason.lower()
    assert len(result.recommendations) > 0


def test_analyze_addition_optional_field(analyzer):
    """Тест: анализ добавления опционального поля"""
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

    assert result.classification == ChangeClassification.ADDITION
    assert result.impact == ChangeImpact.LOW
    assert "опциональное" in result.reason.lower()


def test_analyze_addition_conditional_field(analyzer):
    """Тест: анализ добавления условно обязательного поля"""
    field_change = FieldChange(
        path="test/conditionalField",
        change_type="added",
        new_meta=FieldMetadata(
            path="test/conditionalField",
            name="conditionalField",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition={"expression": "productType == 'LOAN'"}
        )
    )

    result = analyzer._analyze_addition(field_change)

    assert result.classification == ChangeClassification.ADDITION
    assert result.impact == ChangeImpact.MEDIUM
    assert "условно обязательное" in result.reason.lower()


# ============================================================================
# ТЕСТЫ: Анализ удаленных полей
# ============================================================================

def test_analyze_removal_required_field(analyzer):
    """Тест: анализ удаления обязательного поля"""
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

    assert result.classification == ChangeClassification.REMOVAL
    assert result.impact == ChangeImpact.CRITICAL
    assert "обязательное" in result.reason.lower()
    assert "УДАЛИТЬ" in result.recommendations[0]


def test_analyze_removal_optional_field(analyzer):
    """Тест: анализ удаления опционального поля"""
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

    assert result.classification == ChangeClassification.REMOVAL
    assert result.impact == ChangeImpact.MEDIUM
    assert "опциональное" in result.reason.lower()


def test_analyze_removal_conditional_field(analyzer):
    """Тест: анализ удаления условно обязательного поля"""
    field_change = FieldChange(
        path="test/conditionalField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="test/conditionalField",
            name="conditionalField",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition={"expression": "productType == 'LOAN'"}
        )
    )

    result = analyzer._analyze_removal(field_change)

    assert result.classification == ChangeClassification.REMOVAL
    assert result.impact == ChangeImpact.MEDIUM
    assert "условно обязательное" in result.reason.lower()


# ============================================================================
# ТЕСТЫ: Анализ изменений полей
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
        changes={"type": "string → integer"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.CRITICAL
    assert "тип" in result.reason.lower()


def test_analyze_modification_became_required(analyzer):
    """Тест: анализ поля, которое стало обязательным"""
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
        changes={"required": "False → True"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.HIGH
    assert "обязательным" in result.reason.lower()


def test_analyze_modification_became_optional(analyzer):
    """Тест: анализ поля, которое стало опциональным"""
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
        changes={"required": "True → False"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.NON_BREAKING
    assert result.impact == ChangeImpact.LOW
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
            condition={"expression": "productType == 'LOAN'"}
        ),
        changes={"conditional": "False → True"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.HIGH
    assert "условно обязательным" in result.reason.lower()
    assert "условия" in result.recommendations[0].lower()


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
            condition={"expression": "productType == 'LOAN'"}
        ),
        new_meta=FieldMetadata(
            path="test/field",
            name="field",
            field_type="string",
            is_required=False,
            is_conditional=False
        ),
        changes={"conditional": "True → False"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.NON_BREAKING
    assert result.impact == ChangeImpact.LOW
    assert "перестало" in result.reason.lower()


def test_analyze_modification_condition_changed(analyzer):
    """Тест: анализ изменения условия УО"""
    old_condition = {"expression": "productType == 'LOAN'"}
    new_condition = {"expression": "productType == 'CARD'"}

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
        changes={"condition": f"{old_condition} → {new_condition}"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.HIGH
    assert "условие" in result.reason.lower()
    assert "новое условие" in result.recommendations[0].lower()


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
        changes={"dictionary": "OLD_DICT → NEW_DICT"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.BREAKING
    assert result.impact == ChangeImpact.HIGH
    assert "справочник" in result.reason.lower()


def test_analyze_modification_constraints_change(analyzer):
    """Тест: анализ изменения ограничений"""
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
            is_required=False
        ),
        changes={"maxLength": "100 → 50"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.NON_BREAKING
    assert result.impact == ChangeImpact.MEDIUM
    assert "ограничения" in result.reason.lower()


def test_analyze_modification_other_changes(analyzer):
    """Тест: анализ прочих изменений"""
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
            is_required=False
        ),
        changes={"description": "old → new"}
    )

    result = analyzer._analyze_modification(field_change)

    assert result.classification == ChangeClassification.NON_BREAKING
    assert result.impact == ChangeImpact.LOW


# ============================================================================
# ТЕСТЫ: Анализ различий
# ============================================================================

def test_analyze_diff(analyzer, sample_schema_diff):
    """Тест: анализ различий между схемами"""
    result = analyzer._analyze_diff(sample_schema_diff)

    assert len(result) == 4  # 2 added + 1 removed + 1 modified
    assert all(isinstance(change, AnalyzedChange) for change in result)


def test_analyze_diff_empty(analyzer):
    """Тест: анализ пустых различий"""
    diff = SchemaDiff(
        old_version="1.0",
        new_version="2.0",
        call="Call1"
    )

    result = analyzer._analyze_diff(diff)

    assert len(result) == 0


# ============================================================================
# ТЕСТЫ: AnalyzedChange
# ============================================================================

def test_analyzed_change_to_dict(sample_field_change_added):
    """Тест: преобразование AnalyzedChange в словарь"""
    analyzed = AnalyzedChange(
        field_change=sample_field_change_added,
        classification=ChangeClassification.BREAKING,
        impact=ChangeImpact.CRITICAL,
        reason="Test reason",
        recommendations=["Recommendation 1", "Recommendation 2"]
    )

    result = analyzed.to_dict()

    assert result["path"] == "test/newField"
    assert result["change_type"] == "added"
    assert result["classification"] == "breaking"
    assert result["impact"] == "critical"
    assert result["reason"] == "Test reason"
    assert len(result["recommendations"]) == 2


# ============================================================================
# ТЕСТЫ: ChangeAnalysisResult
# ============================================================================

def test_change_analysis_result_initialization():
    """Тест: инициализация результата анализа"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=[]
    )

    assert result.old_schema == Path("old.json")
    assert result.new_schema == Path("new.json")
    assert result.diff == diff
    assert len(result.analyzed_changes) == 0


def test_change_analysis_result_breaking_changes():
    """Тест: получение breaking changes"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    breaking = result.breaking_changes

    assert len(breaking) == 1
    assert breaking[0].classification == ChangeClassification.BREAKING


def test_change_analysis_result_non_breaking_changes():
    """Тест: получение non-breaking changes"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    non_breaking = result.non_breaking_changes

    assert len(non_breaking) == 1
    assert non_breaking[0].classification == ChangeClassification.NON_BREAKING


def test_change_analysis_result_critical_changes():
    """Тест: получение критических изменений"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    critical = result.critical_changes

    assert len(critical) == 1
    assert critical[0].impact == ChangeImpact.CRITICAL


def test_change_analysis_result_high_impact_changes():
    """Тест: получение изменений с высоким влиянием"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.HIGH,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    high_impact = result.high_impact_changes

    assert len(high_impact) == 1
    assert high_impact[0].impact == ChangeImpact.HIGH


def test_change_analysis_result_get_changes_by_impact():
    """Тест: фильтрация изменений по уровню влияния"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.MEDIUM,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test3", change_type="added"),
            classification=ChangeClassification.NON_BREAKING,
            impact=ChangeImpact.MEDIUM,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    medium = result.get_changes_by_impact(ChangeImpact.MEDIUM)

    assert len(medium) == 2
    assert all(c.impact == ChangeImpact.MEDIUM for c in medium)


def test_change_analysis_result_get_changes_by_classification():
    """Тест: фильтрация изменений по классификации"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added"),
            classification=ChangeClassification.ADDITION,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test2", change_type="added"),
            classification=ChangeClassification.ADDITION,
            impact=ChangeImpact.LOW,
            reason="Test",
            recommendations=[]
        ),
        AnalyzedChange(
            field_change=FieldChange(path="test3", change_type="removed"),
            classification=ChangeClassification.REMOVAL,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    additions = result.get_changes_by_classification(ChangeClassification.ADDITION)

    assert len(additions) == 2
    assert all(c.classification == ChangeClassification.ADDITION for c in additions)


def test_change_analysis_result_to_dict():
    """Тест: преобразование результата в словарь"""
    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")

    changes = [
        AnalyzedChange(
            field_change=FieldChange(path="test1", change_type="added", new_meta=FieldMetadata(
                path="test1", name="test1", field_type="string"
            )),
            classification=ChangeClassification.BREAKING,
            impact=ChangeImpact.CRITICAL,
            reason="Test",
            recommendations=[]
        )
    ]

    result = ChangeAnalysisResult(
        old_schema=Path("old.json"),
        new_schema=Path("new.json"),
        diff=diff,
        analyzed_changes=changes
    )

    result_dict = result.to_dict()

    assert result_dict["old_schema"] == "old.json"
    assert result_dict["new_schema"] == "new.json"
    assert result_dict["summary"]["total_changes"] == 1
    assert result_dict["summary"]["breaking_changes"] == 1
    assert result_dict["summary"]["critical_impact"] == 1
    assert len(result_dict["changes"]) == 1


# ============================================================================
# ТЕСТЫ: Интеграция с SchemaParser (мокирование)
# ============================================================================

def test_analyze_changes_with_mocked_parser(analyzer, mocker):
    """Тест: анализ изменений с мокированным парсером"""
    # Мокируем методы парсера
    mock_load = mocker.patch.object(analyzer.parser, 'load_schema')
    mock_parse = mocker.patch.object(analyzer.parser, 'parse_schema')
    mock_compare = mocker.patch.object(analyzer.parser, 'compare_schemas')

    # Настраиваем возвращаемые значения
    mock_load.return_value = {"type": "object"}

    old_fields = {
        "field1": FieldMetadata(path="field1", name="field1", field_type="string", is_required=True)
    }
    new_fields = {
        "field1": FieldMetadata(path="field1", name="field1", field_type="string", is_required=True),
        "field2": FieldMetadata(path="field2", name="field2", field_type="integer", is_required=False)
    }

    mock_parse.side_effect = [old_fields, new_fields]

    diff = SchemaDiff(old_version="1.0", new_version="2.0", call="Call1")
    diff.added_fields.append(
        FieldChange(path="field2", change_type="added", new_meta=new_fields["field2"])
    )
    mock_compare.return_value = diff

    # Вызываем метод
    result = analyzer.analyze_changes(Path("old.json"), Path("new.json"))

    # Проверяем
    assert result is not None
    assert len(result.analyzed_changes) == 1
    assert result.analyzed_changes[0].field_change.path == "field2"
