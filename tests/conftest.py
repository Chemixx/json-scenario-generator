"""
Конфигурация pytest и общие фикстуры для всех тестов
"""
import sys
from pathlib import Path
import pytest

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.schema_models import (
    VersionInfo,
    VersionStatus,
    FieldMetadata,
    FieldChange,
    SchemaDiff,
)
from src.models.dictionary_models import DictionaryEntry, Dictionary
from src.models.scenario_models import ScenarioMetadata, Scenario


# ============================================================================
# ФИКСТУРЫ: VersionInfo
# ============================================================================

@pytest.fixture
def version_info_current():
    """Фикстура для текущей версии"""
    return VersionInfo(
        version="072",
        status=VersionStatus.CURRENT,
        direction="КН, КК",
        inclusion_date="30.08.2025"
    )


@pytest.fixture
def version_info_future():
    """Фикстура для будущей версии"""
    return VersionInfo(
        version="073",
        status=VersionStatus.FUTURE,
        direction="КН, КК",
        release_month="Ноябрь 2025"
    )


# ============================================================================
# ФИКСТУРЫ: FieldMetadata
# ============================================================================

@pytest.fixture
def field_metadata_simple():
    """Фикстура для простого поля"""
    return FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer",
        is_required=True,
        constraints={"maxIntLength": 10}
    )


@pytest.fixture
def field_metadata_with_dictionary():
    """Фикстура для поля со справочником"""
    return FieldMetadata(
        path="loanRequest/productCdExt",
        name="productCdExt",
        field_type="integer",
        is_required=True,
        dictionary="PRODUCT_TYPE"
    )


@pytest.fixture
def field_metadata_conditional():
    """Фикстура для условно обязательного поля"""
    return FieldMetadata(
        path="loanRequest/someField",
        name="someField",
        field_type="string",
        is_conditional=True,
        condition={
            "expression": "productCdExt == 10410001",
            "message": "Обязательно для PACL"
        }
    )


# ============================================================================
# ФИКСТУРЫ: SchemaDiff
# ============================================================================

@pytest.fixture
def schema_diff_empty():
    """Фикстура для пустого diff'а"""
    return SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )


@pytest.fixture
def schema_diff_with_changes():
    """Фикстура для diff'а с изменениями"""
    diff = SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1"
    )

    # Добавленные поля
    diff.added_fields.append(FieldChange(
        path="loanRequest/newField",
        change_type="added",
        new_meta=FieldMetadata(
            path="loanRequest/newField",
            name="newField",
            field_type="string"
        )
    ))

    # Удаленные поля
    diff.removed_fields.append(FieldChange(
        path="loanRequest/oldField",
        change_type="removed",
        old_meta=FieldMetadata(
            path="loanRequest/oldField",
            name="oldField",
            field_type="string"
        )
    ))

    # Измененные поля
    diff.modified_fields.append(FieldChange(
        path="loanRequest/changedField",
        change_type="modified",
        old_meta=FieldMetadata(
            path="loanRequest/changedField",
            name="changedField",
            field_type="string"
        ),
        new_meta=FieldMetadata(
            path="loanRequest/changedField",
            name="changedField",
            field_type="integer"
        ),
        changes={"type": "string → integer"}
    ))

    return diff


# ============================================================================
# ФИКСТУРЫ: Dictionary
# ============================================================================

@pytest.fixture
def dictionary_product_type():
    """Фикстура для справочника типов продуктов"""
    return Dictionary(
        name="PRODUCT_TYPE",
        description="Типы кредитных продуктов",
        entries=[
            DictionaryEntry(
                code=10410001,
                name="PACL",
                dictionary_type="PRODUCT_TYPE",
                description="Потребительский кредит наличными"
            ),
            DictionaryEntry(
                code=10410002,
                name="TOPUP",
                dictionary_type="PRODUCT_TYPE",
                description="Пополнение кредита"
            ),
            DictionaryEntry(
                code=10410003,
                name="REFI",
                dictionary_type="PRODUCT_TYPE",
                description="Рефинансирование"
            ),
        ]
    )


@pytest.fixture
def dictionary_empty():
    """Фикстура для пустого справочника"""
    return Dictionary(
        name="EMPTY_DICT",
        description="Пустой справочник для тестов"
    )


# ============================================================================
# ФИКСТУРЫ: Scenario
# ============================================================================

@pytest.fixture
def scenario_simple():
    """Фикстура для простого сценария"""
    metadata = ScenarioMetadata(
        name="test_scenario",
        version="072",
        call="Call1",
        description="Тестовый сценарий"
    )

    data = {
        "loanRequest": {
            "creditAmt": 100000,
            "productCdExt": 10410001,
            "customer": {
                "firstName": "Иван",
                "lastName": "Иванов"
            }
        }
    }

    return Scenario(metadata=metadata, data=data)


@pytest.fixture
def scenario_with_arrays():
    """Фикстура для сценария с массивами"""
    metadata = ScenarioMetadata(
        name="test_scenario_arrays",
        version="072",
        call="Call1"
    )

    data = {
        "loanRequest": {
            "items": [
                {"value": 100, "description": "Item 1"},
                {"value": 200, "description": "Item 2"},
            ]
        }
    }

    return Scenario(metadata=metadata, data=data)


# ============================================================================
# ФИКСТУРЫ: Тестовые файлы
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Фикстура для директории с тестовыми данными"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_schemas_dir(fixtures_dir):
    """Фикстура для директории с тестовыми схемами"""
    return fixtures_dir / "schemas"


@pytest.fixture
def test_dictionaries_dir(fixtures_dir):
    """Фикстура для директории с тестовыми справочниками"""
    return fixtures_dir / "dictionaries"


@pytest.fixture
def test_scenarios_dir(fixtures_dir):
    """Фикстура для директории с тестовыми сценариями"""
    return fixtures_dir / "scenarios"
