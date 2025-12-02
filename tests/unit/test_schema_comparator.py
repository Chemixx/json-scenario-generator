"""
Тесты для компаратора JSON схем
"""
from src.core.schema_comparator import SchemaComparator
from src.models.schema_models import FieldMetadata, ConditionalRequirement


# ============================================================================
# ТЕСТЫ: Сравнение схем - добавление полей
# ============================================================================

def test_compare_schemas_added_fields():
    """Тест: сравнение схем - добавленные поля"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string")
    }

    new_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string"),
        "email": FieldMetadata(path="email", name="email", field_type="string")
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.added_fields) == 1
    assert diff.added_fields[0].path == "email"
    assert diff.added_fields[0].change_type == "added"


def test_compare_schemas_added_required_field():
    """Тест: добавление обязательного поля"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string")
    }

    new_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string"),
        "email": FieldMetadata(
            path="email",
            name="email",
            field_type="string",
            is_required=True
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.added_fields) == 1
    assert diff.added_fields[0].new_meta.is_required is True


# ============================================================================
# ТЕСТЫ: Сравнение схем - удаление полей
# ============================================================================

def test_compare_schemas_removed_fields():
    """Тест: сравнение схем - удаленные поля"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string"),
        "age": FieldMetadata(path="age", name="age", field_type="integer")
    }

    new_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string")
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.removed_fields) == 1
    assert diff.removed_fields[0].path == "age"
    assert diff.removed_fields[0].change_type == "removed"


def test_compare_schemas_removed_required_field():
    """Тест: удаление обязательного поля"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True),
        "age": FieldMetadata(path="age", name="age", field_type="integer", is_required=True)
    }

    new_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.removed_fields) == 1
    assert diff.removed_fields[0].old_meta.is_required is True


# ============================================================================
# ТЕСТЫ: Сравнение схем - изменение полей
# ============================================================================

def test_compare_schemas_modified_type():
    """Тест: изменение типа поля"""
    comparator = SchemaComparator()

    old_schema = {
        "age": FieldMetadata(path="age", name="age", field_type="string")
    }

    new_schema = {
        "age": FieldMetadata(path="age", name="age", field_type="integer")
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert diff.modified_fields[0].path == "age"
    assert diff.modified_fields[0].change_type == "modified"
    assert "type" in diff.modified_fields[0].changes


def test_compare_schemas_required_change():
    """Тест: изменение обязательности поля"""
    comparator = SchemaComparator()

    old_schema = {
        "email": FieldMetadata(path="email", name="email", field_type="string")
    }

    new_schema = {
        "email": FieldMetadata(
            path="email",
            name="email",
            field_type="string",
            is_required=True
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "required" in diff.modified_fields[0].changes
    assert "стало обязательным" in diff.modified_fields[0].changes["required"]


def test_compare_schemas_conditional_change():
    """Тест: поле стало условно обязательным"""
    comparator = SchemaComparator()

    old_schema = {
        "pledges": FieldMetadata(
            path="pledges",
            name="pledges",
            field_type="array"
        )
    }

    new_schema = {
        "pledges": FieldMetadata(
            path="pledges",
            name="pledges",
            field_type="array",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="in(#this.productCd, 10410001, 10410002)"
            )
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "conditional" in diff.modified_fields[0].changes


def test_compare_schemas_condition_expression_change():
    """Тест: изменение условия УО"""
    comparator = SchemaComparator()

    old_schema = {
        "pledges": FieldMetadata(
            path="pledges",
            name="pledges",
            field_type="array",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="in(#this.productCd, 10410001)"
            )
        )
    }

    new_schema = {
        "pledges": FieldMetadata(
            path="pledges",
            name="pledges",
            field_type="array",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="in(#this.productCd, 10410001, 10410002)"
            )
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "condition" in diff.modified_fields[0].changes
    assert "10410002" in diff.modified_fields[0].changes["condition"]


# ============================================================================
# ТЕСТЫ: Сравнение схем - справочники
# ============================================================================

def test_compare_schemas_dictionary_change():
    """Тест: изменение справочника"""
    comparator = SchemaComparator()

    old_schema = {
        "status": FieldMetadata(
            path="status",
            name="status",
            field_type="integer",
            dictionary="STATUS_OLD"
        )
    }

    new_schema = {
        "status": FieldMetadata(
            path="status",
            name="status",
            field_type="integer",
            dictionary="STATUS_NEW"
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "dictionary" in diff.modified_fields[0].changes


# ============================================================================
# ТЕСТЫ: Сравнение схем - ограничения
# ============================================================================

def test_compare_schemas_constraint_change_tightened():
    """Тест: ужесточение ограничений"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(
            path="name",
            name="name",
            field_type="string",
            constraints={"maxLength": 100}
        )
    }

    new_schema = {
        "name": FieldMetadata(
            path="name",
            name="name",
            field_type="string",
            constraints={"maxLength": 50}
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "constraints" in diff.modified_fields[0].changes
    assert "ужесточено" in diff.modified_fields[0].changes["constraints"]


def test_compare_schemas_constraint_change_relaxed():
    """Тест: смягчение ограничений"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(
            path="name",
            name="name",
            field_type="string",
            constraints={"maxLength": 50}
        )
    }

    new_schema = {
        "name": FieldMetadata(
            path="name",
            name="name",
            field_type="string",
            constraints={"maxLength": 100}
        )
    }

    diff = comparator.compare(old_schema, new_schema)

    assert len(diff.modified_fields) == 1
    assert "constraints" in diff.modified_fields[0].changes
    assert "смягчено" in diff.modified_fields[0].changes["constraints"]


# ============================================================================
# ТЕСТЫ: Вспомогательные методы
# ============================================================================

def test_fields_differ_identical():
    """Тест: одинаковые поля"""
    comparator = SchemaComparator()

    field1 = FieldMetadata(
        path="test",
        name="test",
        field_type="string",
        is_required=True
    )

    field2 = FieldMetadata(
        path="test",
        name="test",
        field_type="string",
        is_required=True
    )

    assert comparator._fields_differ(field1, field2) is False


def test_fields_differ_different_type():
    """Тест: разные типы полей"""
    comparator = SchemaComparator()

    field1 = FieldMetadata(
        path="test",
        name="test",
        field_type="string"
    )

    field2 = FieldMetadata(
        path="test",
        name="test",
        field_type="integer"
    )

    assert comparator._fields_differ(field1, field2) is True


def test_fields_differ_different_required():
    """Тест: разная обязательность"""
    comparator = SchemaComparator()

    field1 = FieldMetadata(
        path="test",
        name="test",
        field_type="string",
        is_required=False
    )

    field2 = FieldMetadata(
        path="test",
        name="test",
        field_type="string",
        is_required=True
    )

    assert comparator._fields_differ(field1, field2) is True


# ============================================================================
# ТЕСТЫ: Статистика
# ============================================================================

def test_schema_diff_statistics():
    """Тест: статистика изменений"""
    comparator = SchemaComparator()

    old_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True),
        "age": FieldMetadata(path="age", name="age", field_type="string")
    }

    new_schema = {
        "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True),
        "age": FieldMetadata(path="age", name="age", field_type="integer"),
        "email": FieldMetadata(path="email", name="email", field_type="string")
    }

    diff = comparator.compare(old_schema, new_schema)

    # Проверяем статистику
    assert diff.total_changes() == 2  # 1 добавлено + 1 изменено
    assert len(diff.added_fields) == 1
    assert len(diff.modified_fields) == 1
    assert len(diff.removed_fields) == 0
