"""
Тесты для моделей сценариев
"""
import pytest
from pathlib import Path
from datetime import datetime
from src.models.scenario_models import ScenarioMetadata, Scenario


# ============================================================================
# ТЕСТЫ: ScenarioMetadata
# ============================================================================

def test_scenario_metadata_creation():
    """Тест создания ScenarioMetadata"""
    metadata = ScenarioMetadata(
        name="Call1_v072_КН_success",
        version="072",
        call="Call1",
        description="Успешный сценарий для КН"
    )

    assert metadata.name == "Call1_v072_КН_success"
    assert metadata.version == "072"
    assert metadata.call == "Call1"
    assert metadata.adapter == "front-adapter"
    assert isinstance(metadata.created_at, datetime)


def test_scenario_metadata_tags():
    """Тест работы с тегами"""
    metadata = ScenarioMetadata(
        name="test",
        version="072",
        call="Call1"
    )

    # Добавление тега
    metadata.add_tag("success")
    assert metadata.has_tag("success") is True
    assert metadata.has_tag("fail") is False

    # Повторное добавление того же тега
    metadata.add_tag("success")
    assert len(metadata.tags) == 1  # Не должно дублироваться


def test_scenario_metadata_update_timestamp():
    """Тест метода update_timestamp()"""
    metadata = ScenarioMetadata(
        name="test",
        version="072",
        call="Call1"
    )

    old_timestamp = metadata.updated_at

    # Небольшая задержка
    import time
    time.sleep(0.01)

    metadata.update_timestamp()
    assert metadata.updated_at > old_timestamp


def test_scenario_metadata_to_dict():
    """Тест метода to_dict()"""
    metadata = ScenarioMetadata(
        name="test",
        version="072",
        call="Call1",
        description="Test scenario"
    )
    metadata.add_tag("success")

    result = metadata.to_dict()

    assert result["name"] == "test"
    assert result["version"] == "072"
    assert result["call"] == "Call1"
    assert result["description"] == "Test scenario"
    assert "success" in result["tags"]


# ============================================================================
# ТЕСТЫ: Scenario
# ============================================================================

def test_scenario_creation():
    """Тест создания Scenario"""
    metadata = ScenarioMetadata(
        name="test",
        version="072",
        call="Call1"
    )

    data = {
        "loanRequest": {
            "creditAmt": 100000
        }
    }

    scenario = Scenario(metadata=metadata, data=data)

    assert scenario.metadata.name == "test"
    assert scenario.data == data


def test_scenario_get_field_value():
    """Тест метода get_field_value()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {
        "loanRequest": {
            "creditAmt": 100000,
            "customer": {
                "name": "Иван"
            }
        }
    }

    scenario = Scenario(metadata=metadata, data=data)

    # Простое поле
    assert scenario.get_field_value("loanRequest/creditAmt") == 100000

    # Вложенное поле
    assert scenario.get_field_value("loanRequest/customer/name") == "Иван"

    # Несуществующее поле должно вызвать ошибку
    with pytest.raises(KeyError):
        scenario.get_field_value("loanRequest/nonExistent")


def test_scenario_get_field_value_with_arrays():
    """Тест get_field_value() с массивами"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {
        "loanRequest": {
            "items": [
                {"value": 100},
                {"value": 200}
            ]
        }
    }

    scenario = Scenario(metadata=metadata, data=data)

    # Доступ к элементу массива
    assert scenario.get_field_value("loanRequest/items[0]/value") == 100
    assert scenario.get_field_value("loanRequest/items[1]/value") == 200


def test_scenario_set_field_value():
    """Тест метода set_field_value()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {}

    scenario = Scenario(metadata=metadata, data=data)

    # Установка простого поля
    scenario.set_field_value("loanRequest/creditAmt", 100000)
    assert scenario.data["loanRequest"]["creditAmt"] == 100000

    # Установка вложенного поля
    scenario.set_field_value("loanRequest/customer/name", "Иван")
    assert scenario.data["loanRequest"]["customer"]["name"] == "Иван"


def test_scenario_set_field_value_with_arrays():
    """Тест set_field_value() с массивами"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {}

    scenario = Scenario(metadata=metadata, data=data)

    # Установка элемента массива
    scenario.set_field_value("loanRequest/items[0]/value", 100)
    assert scenario.data["loanRequest"]["items"][0]["value"] == 100

    # Установка второго элемента
    scenario.set_field_value("loanRequest/items[1]/value", 200)
    assert len(scenario.data["loanRequest"]["items"]) == 2


def test_scenario_has_field():
    """Тест метода has_field()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {
        "loanRequest": {
            "creditAmt": 100000
        }
    }

    scenario = Scenario(metadata=metadata, data=data)

    # Существующее поле
    assert scenario.has_field("loanRequest/creditAmt") is True

    # Несуществующее поле
    assert scenario.has_field("loanRequest/nonExistent") is False


def test_scenario_delete_field():
    """Тест метода delete_field()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {
        "loanRequest": {
            "creditAmt": 100000,
            "customer": {
                "name": "Иван"
            }
        }
    }

    scenario = Scenario(metadata=metadata, data=data)

    # Удаление существующего поля
    assert scenario.delete_field("loanRequest/creditAmt") is True
    assert scenario.has_field("loanRequest/creditAmt") is False

    # Удаление несуществующего поля
    assert scenario.delete_field("loanRequest/nonExistent") is False


def test_scenario_to_dict():
    """Тест метода to_dict()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {"loanRequest": {"creditAmt": 100000}}

    scenario = Scenario(metadata=metadata, data=data)

    result = scenario.to_dict()

    assert result == data
    assert result is not data  # Должна быть копия


def test_scenario_to_full_dict():
    """Тест метода to_full_dict()"""
    metadata = ScenarioMetadata(name="test", version="072", call="Call1")
    data = {"loanRequest": {"creditAmt": 100000}}

    scenario = Scenario(metadata=metadata, data=data)

    result = scenario.to_full_dict()

    assert "metadata" in result
    assert "data" in result
    assert result["metadata"]["name"] == "test"
    assert result["data"] == data
