"""
Тесты для моделей схем
"""
from datetime import datetime
from src.models.schema_models import (
    VersionStatus,
    VersionInfo,
    FieldMetadata,
    FieldChange,
    SchemaDiff,
    ConditionalRequirement,  # ← ДОБАВЛЕНО
)
from src.utils.icons import Icon


# ============================================================================
# ТЕСТЫ: VersionInfo
# ============================================================================

def test_version_info_creation():
    """Тест создания VersionInfo"""
    version = VersionInfo(
        version="072",
        status=VersionStatus.CURRENT,
        direction="КН, КК"
    )

    assert version.version == "072"
    assert version.status == VersionStatus.CURRENT
    assert version.direction == "КН, КК"


def test_version_info_full_version():
    """Тест метода full_version()"""
    # Без подверсии
    version1 = VersionInfo(version="072")
    assert version1.full_version() == "072"

    # С подверсией
    version2 = VersionInfo(version="072", subversion="04")
    assert version2.full_version() == "072.04"


def test_version_info_status_checks():
    """Тест методов проверки статуса"""
    # Актуальная версия
    current = VersionInfo(version="072", status=VersionStatus.CURRENT)
    assert current.is_current() is True
    assert current.is_future() is False
    assert current.is_deprecated() is False

    # Будущий релиз
    future = VersionInfo(version="073", status=VersionStatus.FUTURE)
    assert future.is_current() is False
    assert future.is_future() is True
    assert future.is_deprecated() is False

    # Выводится из эксплуатации
    deprecating = VersionInfo(version="070", status=VersionStatus.DEPRECATING)
    assert deprecating.is_current() is False
    assert deprecating.is_future() is False
    assert deprecating.is_deprecated() is True


def test_version_info_str_repr():
    """Тест методов __str__ и __repr__"""
    version = VersionInfo(
        version="072",
        subversion="04",
        status=VersionStatus.CURRENT
    )

    str_result = str(version)
    assert "072.04" in str_result
    assert VersionStatus.CURRENT.value in str_result

    repr_result = repr(version)
    assert "VersionInfo" in repr_result
    assert "072" in repr_result


# ============================================================================
# ТЕСТЫ: ConditionalRequirement (НОВЫЕ ТЕСТЫ)
# ============================================================================

def test_conditional_requirement_creation():
    """Тест создания ConditionalRequirement"""
    cond = ConditionalRequirement(
        expression="in(#this.productCd, 10410001, 10410002)",
        message="Продукт PACCREACT или PACLIREACT"
    )

    assert cond.expression == "in(#this.productCd, 10410001, 10410002)"
    assert cond.message == "Продукт PACCREACT или PACLIREACT"
    assert cond.dq_code is None


def test_conditional_requirement_auto_message():
    """Тест автогенерации message"""
    # Без указания message
    cond = ConditionalRequirement(
        expression="eq(#root.loanRequest.loanTypeCd, 10340001L)"
    )

    # Должно быть сгенерировано автоматически
    assert cond.message is not None
    assert "loanTypeCd" in cond.message
    assert "10340001" in cond.message  # L должен быть удален
    assert "#root." not in cond.message  # Префиксы должны быть удалены


def test_conditional_requirement_expr_to_message():
    """Тест метода _expr_to_message()"""
    # Удаление префиксов
    result1 = ConditionalRequirement._expr_to_message("#this.productCd")
    assert result1 == "productCd"

    # Удаление L суффикса
    result2 = ConditionalRequirement._expr_to_message("in(field, 10410001L, 10410002L)")
    assert "10410001L" not in result2
    assert "10410001" in result2

    # Замена операторов
    result3 = ConditionalRequirement._expr_to_message("field1 != null && field2 == true")
    assert "НЕ" in result3
    assert "И" in result3
    assert "=" in result3
    assert "!=" not in result3
    assert "&&" not in result3

    # Замена ?. на .
    result4 = ConditionalRequirement._expr_to_message("#this?.field?.subfield")
    assert "?." not in result4


def test_conditional_requirement_with_dq_code():
    """Тест с DQ кодом"""
    cond = ConditionalRequirement(
        expression="notNull(#this.taxNumber)",
        message="ИНН не должен быть пустым",
        dq_code=12345
    )

    assert cond.dq_code == 12345


def test_conditional_requirement_str_repr():
    """Тест методов __str__ и __repr__"""
    cond = ConditionalRequirement(
        expression="in(#this.productCd, 10410001, 10410002)",
        message="Продукт PACCREACT"
    )

    str_result = str(cond)
    assert "ConditionalRequirement" in str_result
    assert "Продукт PACCREACT" in str_result

    repr_result = repr(cond)
    assert "ConditionalRequirement" in repr_result
    assert "expression" in repr_result


# ============================================================================
# ТЕСТЫ: FieldMetadata
# ============================================================================

def test_field_metadata_creation():
    """Тест создания FieldMetadata"""
    field_meta = FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer",
        is_required=True,
        constraints={"maxIntLength": 10}
    )

    assert field_meta.path == "loanRequest/creditAmt"
    assert field_meta.name == "creditAmt"
    assert field_meta.field_type == "integer"
    assert field_meta.is_required is True


def test_field_metadata_with_conditional_requirement():
    """Тест FieldMetadata с условной обязательностью (НОВЫЙ)"""
    cond_req = ConditionalRequirement(
        expression="in(#this.productCd, 10410001, 10410002)",
        message="Продукт PACCREACT или PACLIREACT"
    )

    field_meta = FieldMetadata(
        path="loanRequest/pledges",
        name="pledges",
        field_type="array",
        is_conditional=True,
        condition=cond_req,
        is_collection=True  # ← НОВОЕ ПОЛЕ
    )

    assert field_meta.is_conditional is True
    assert field_meta.condition is not None
    assert isinstance(field_meta.condition, ConditionalRequirement)
    assert field_meta.condition.message == "Продукт PACCREACT или PACLIREACT"
    assert field_meta.is_collection is True  # ← ПРОВЕРКА НОВОГО ПОЛЯ


def test_field_metadata_is_collection():
    """Тест поля is_collection (НОВЫЙ)"""
    # Массив
    array_field = FieldMetadata(
        path="loanRequest/creditParameters",
        name="creditParameters",
        field_type="array",
        is_collection=True
    )
    assert array_field.is_collection is True

    # Не массив
    simple_field = FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer"
    )
    assert simple_field.is_collection is False


def test_field_metadata_children():
    """Тест поля children (НОВЫЙ)"""
    # Родительское поле
    parent = FieldMetadata(
        path="loanRequest",
        name="loanRequest",
        field_type="object"
    )

    # Дочерние поля
    child1 = FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer"
    )
    child2 = FieldMetadata(
        path="loanRequest/creditPeriod",
        name="creditPeriod",
        field_type="integer"
    )

    parent.children = [child1, child2]

    assert len(parent.children) == 2
    assert parent.children[0].name == "creditAmt"
    assert parent.children[1].name == "creditPeriod"


def test_field_metadata_dq_codes():
    """Тест DQ кодов (НОВЫЙ)"""
    field_meta = FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer",
        is_required=True,
        always_required_dq_code=10001,
        dictionary_dq_code=10002
    )

    assert field_meta.always_required_dq_code == 10001
    assert field_meta.dictionary_dq_code == 10002
    assert field_meta.conditional_dq_code is None  # По умолчанию None


def test_field_metadata_type_checks():
    """Тест методов проверки типа"""
    # Примитивный тип
    primitive = FieldMetadata(
        path="field1",
        name="field1",
        field_type="string"
    )
    assert primitive.is_primitive() is True
    assert primitive.is_complex() is False

    # Сложный тип - объект
    complex_obj = FieldMetadata(
        path="field2",
        name="field2",
        field_type="object"
    )
    assert complex_obj.is_primitive() is False
    assert complex_obj.is_complex() is True

    # Сложный тип - массив
    complex_array = FieldMetadata(
        path="field3",
        name="field3",
        field_type="array"
    )
    assert complex_array.is_primitive() is False
    assert complex_array.is_complex() is True


def test_field_metadata_dictionary():
    """Тест работы со справочниками"""
    # С справочником
    with_dict = FieldMetadata(
        path="field1",
        name="field1",
        field_type="integer",
        dictionary="PRODUCT_TYPE"
    )
    assert with_dict.has_dictionary() is True

    # Без справочника
    without_dict = FieldMetadata(
        path="field2",
        name="field2",
        field_type="string"
    )
    assert without_dict.has_dictionary() is False


def test_field_metadata_constraints():
    """Тест работы с ограничениями"""
    field_meta = FieldMetadata(
        path="field1",
        name="field1",
        field_type="string",
        constraints={
            "maxLength": 100,
            "minLength": 5,
            "pattern": "^[A-Z]+$"
        }
    )

    assert field_meta.get_max_length() == 100
    assert field_meta.get_min_length() == 5
    assert field_meta.get_pattern() == "^[A-Z]+$"


def test_field_metadata_requirement_status():
    """Тест метода get_requirement_status()"""
    # Обязательное
    required = FieldMetadata(
        path="field1",
        name="field1",
        field_type="string",
        is_required=True
    )
    assert required.get_requirement_status() == "О"

    # Условно обязательное
    conditional = FieldMetadata(
        path="field2",
        name="field2",
        field_type="string",
        is_conditional=True
    )
    assert conditional.get_requirement_status() == "УО"

    # Необязательное
    optional = FieldMetadata(
        path="field3",
        name="field3",
        field_type="string"
    )
    assert optional.get_requirement_status() == "Н"


def test_field_metadata_str_repr():
    """Тест методов __str__ и __repr__ (ОБНОВЛЕН)"""
    # Обычное поле
    field1 = FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer",
        is_required=True
    )
    str_result1 = str(field1)
    assert "loanRequest/creditAmt" in str_result1
    assert "О" in str_result1

    # Поле-массив
    field2 = FieldMetadata(
        path="loanRequest/creditParameters",
        name="creditParameters",
        field_type="array",
        is_collection=True
    )
    str_result2 = str(field2)
    assert "[]" in str_result2  # Должен быть маркер массива

    # __repr__
    repr_result = repr(field2)
    assert "is_collection=True" in repr_result


# ============================================================================
# ТЕСТЫ: FieldChange
# ============================================================================

def test_field_change_creation():
    """Тест создания FieldChange"""
    change = FieldChange(
        path="loanRequest/newField",
        change_type="added"
    )

    assert change.path == "loanRequest/newField"
    assert change.change_type == "added"


def test_field_change_breaking_changes():
    """Тест определения критичных изменений"""
    # Удаление обязательного поля - критично
    old_meta = FieldMetadata(
        path="field1",
        name="field1",
        field_type="string",
        is_required=True
    )
    removed_required = FieldChange(
        path="field1",
        change_type="removed",
        old_meta=old_meta
    )
    assert removed_required.is_breaking_change() is True

    # Изменение типа - критично
    type_change = FieldChange(
        path="field2",
        change_type="modified",
        changes={"type": "string → integer"}
    )
    assert type_change.is_breaking_change() is True

    # Поле стало обязательным - критично
    required_change = FieldChange(
        path="field3",
        change_type="modified",
        changes={"required": "Н → О"}
    )
    assert required_change.is_breaking_change() is True

    # Добавление нового поля - не критично
    added = FieldChange(
        path="field4",
        change_type="added"
    )
    assert added.is_breaking_change() is False


def test_field_change_severity():
    """Тест метода get_severity()"""
    # Критичное изменение
    breaking = FieldChange(
        path="field1",
        change_type="modified",
        changes={"type": "string → integer"}
    )
    assert breaking.get_severity() == "critical"

    # Предупреждение
    warning = FieldChange(
        path="field2",
        change_type="modified",
        changes={"maxLength": "100 → 50"}
    )
    assert warning.get_severity() == "warning"

    # Информационное
    info = FieldChange(
        path="field3",
        change_type="added"
    )
    assert info.get_severity() == "info"


def test_field_change_str_repr():
    """Тест методов __str__ и __repr__"""
    # Добавление
    added = FieldChange(path="field1", change_type="added")
    assert Icon.ADDITION in str(added)
    assert "field1" in str(added)

    # Удаление
    removed = FieldChange(path="field2", change_type="removed")
    assert Icon.REMOVAL in str(removed)

    # Изменение
    modified = FieldChange(
        path="field3",
        change_type="modified",
        changes={"type": "string → integer"}
    )
    assert Icon.MODIFICATION in str(modified)
    assert "type" in str(modified)


# ============================================================================
# ТЕСТЫ: SchemaDiff
# ============================================================================

def test_schema_diff_creation():
    """Тест создания SchemaDiff"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )

    assert diff.old_version == "070"
    assert diff.new_version == "072"
    assert diff.call == "Call1"
    assert isinstance(diff.timestamp, datetime)


def test_schema_diff_total_changes():
    """Тест метода total_changes()"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )

    # Изначально пусто
    assert diff.total_changes() == 0
    assert diff.has_changes() is False

    # Добавляем изменения
    diff.added_fields.append(FieldChange(path="field1", change_type="added"))
    diff.removed_fields.append(FieldChange(path="field2", change_type="removed"))
    diff.modified_fields.append(FieldChange(path="field3", change_type="modified"))

    assert diff.total_changes() == 3
    assert diff.has_changes() is True


def test_schema_diff_breaking_changes():
    """Тест методов работы с критичными изменениями"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )

    # Без критичных изменений
    diff.added_fields.append(FieldChange(path="field1", change_type="added"))
    assert diff.has_breaking_changes() is False
    assert len(diff.get_breaking_changes()) == 0

    # С критичным изменением
    breaking_change = FieldChange(
        path="field2",
        change_type="modified",
        changes={"type": "string → integer"}
    )
    diff.modified_fields.append(breaking_change)

    assert diff.has_breaking_changes() is True
    assert len(diff.get_breaking_changes()) == 1
    assert diff.get_breaking_changes()[0] == breaking_change


def test_schema_diff_statistics():
    """Тест метода get_statistics()"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )

    # Добавляем разные изменения
    diff.added_fields.append(FieldChange(path="field1", change_type="added"))
    diff.added_fields.append(FieldChange(path="field2", change_type="added"))
    diff.removed_fields.append(FieldChange(path="field3", change_type="removed"))
    diff.modified_fields.append(FieldChange(
        path="field4",
        change_type="modified",
        changes={"type": "string → integer"}
    ))

    stats = diff.get_statistics()

    assert stats["added"] == 2
    assert stats["removed"] == 1
    assert stats["modified"] == 1
    assert stats["total"] == 4
    assert stats["breaking"] == 1  # Только изменение типа


def test_schema_diff_str_repr():
    """Тест методов __str__ и __repr__"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )
    diff.added_fields.append(FieldChange(path="field1", change_type="added"))

    str_result = str(diff)
    assert "070" in str_result
    assert "072" in str_result
    assert "Call1" in str_result

    repr_result = repr(diff)
    assert "SchemaDiff" in repr_result
