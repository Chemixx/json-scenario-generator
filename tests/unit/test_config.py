"""
Тесты для модуля конфигурации
"""
from pathlib import Path
from config.settings import config, AppConfig


def test_config_instance():
    """Тест создания экземпляра конфигурации"""
    assert config is not None
    assert isinstance(config, AppConfig)
    assert config.APP_NAME == "JSON Scenario Generator"
    assert config.APP_VERSION == "0.1.0"


def test_config_directories_exist():
    """Тест создания директорий"""
    # После инициализации config, директории должны существовать
    assert config.DATA_DIR.exists()
    assert config.SCHEMAS_DIR.exists()
    assert config.DICTIONARIES_DIR.exists()
    assert config.OUTPUT_DIR.exists()
    assert config.LOG_DIR.exists()


def test_get_schema_path():
    """Тест метода get_schema_path()"""
    path = config.get_schema_path("072", "Call1", "request")
    assert path == config.SCHEMAS_DIR / "V072Call1Rq.json"

    path_response = config.get_schema_path("072", "Call1", "response")
    assert path_response == config.SCHEMAS_DIR / "V072Call1Rs.json"


def test_get_report_path():
    """Тест метода get_report_path()"""
    path = config.get_report_path("070", "072", "Call1")
    assert path == config.REPORTS_DIR / "diff_Call1_v070_to_v072.md"


def test_get_updated_scenario_path():
    """Тест метода get_updated_scenario_path()"""
    original = Path("data/scenarios/call1_v070.json")
    updated = config.get_updated_scenario_path(original, "072")
    assert updated == config.UPDATED_SCENARIOS_DIR / "call1_v070_updated_to_v072.json"
