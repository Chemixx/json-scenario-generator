"""
Настройки приложения
"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).parent.parent


@dataclass
class AppConfig:
    """Конфигурация приложения"""

    # Метаданные приложения
    APP_NAME: str = "JSON Scenario Generator"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Автоматизация актуализации JSON-сценариев для тестирования"

    # Базовые пути
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Пути к входным данным
    SCHEMAS_DIR: Path = DATA_DIR / "schemas"
    DICTIONARIES_DIR: Path = DATA_DIR / "dictionaries"
    RELEASES_DIR: Path = DATA_DIR / "releases"
    MAPPINGS_DIR: Path = DATA_DIR / "mappings"
    SCENARIOS_DIR: Path = DATA_DIR / "scenarios"

    # Пути к выходным данным
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"
    UPDATED_SCENARIOS_DIR: Path = OUTPUT_DIR / "scenarios"
    COMPARISON_DIR: Path = OUTPUT_DIR / "comparisons"

    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "app.log"
    LOG_ROTATION: str = "10 MB"  # Ротация при достижении размера
    LOG_RETENTION: str = "30 days"  # Хранить логи 30 дней
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Настройки генерации тестовых данных
    DEFAULT_LOCALE: str = "ru_RU"  # Локаль для Faker
    DEFAULT_ARRAY_SIZE: int = 1    # Количество элементов в массивах по умолчанию
    GENERATE_RANDOM_INN: bool = True  # Генерировать ИНН с валидной КС

    # Настройки валидации
    STRICT_VALIDATION: bool = True  # Строгая валидация по JSON Schema
    VALIDATE_DICTIONARIES: bool = True  # Валидировать справочные значения

    # Настройки отчетов
    REPORT_FORMAT: str = "markdown"  # "markdown", "html", "json"
    INCLUDE_EXAMPLES: bool = True  # Включать примеры значений в отчеты
    HIGHLIGHT_CHANGES: bool = True  # Подсвечивать изменения в JSON

    # Настройки для GitHub (опционально)
    GITHUB_REPO: Optional[str] = os.getenv("GITHUB_REPO")
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

    def __post_init__(self):
        """Создает директории, если их нет"""
        directories = [
            self.DATA_DIR,
            self.SCHEMAS_DIR,
            self.DICTIONARIES_DIR,
            self.RELEASES_DIR,
            self.MAPPINGS_DIR,
            self.SCENARIOS_DIR,
            self.OUTPUT_DIR,
            self.REPORTS_DIR,
            self.UPDATED_SCENARIOS_DIR,
            self.COMPARISON_DIR,
            self.LOG_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_schema_path(self, version: str, call: str, direction: str = "request") -> Path:
        """
        Получить путь к JSON Schema

        Args:
            version: Версия контракта (например, "072")
            call: Тип Call'а (например, "Call1")
            direction: Направление ("request" или "response")

        Returns:
            Путь к файлу схемы

        Example:
            >>> config.get_schema_path("072", "Call1", "request")
            Path("data/schemas/V72Call1Rq.json")
        """
        suffix = "Rq" if direction == "request" else "Rs"
        filename = f"V{version}{call}{suffix}.json"
        return self.SCHEMAS_DIR / filename

    def get_report_path(self, old_version: str, new_version: str, call: str) -> Path:
        """
        Получить путь к отчету о сравнении версий

        Args:
            old_version: Старая версия
            new_version: Новая версия
            call: Тип Call'а

        Returns:
            Путь к файлу отчета
        """
        filename = f"diff_{call}_v{old_version}_to_v{new_version}.md"
        return self.REPORTS_DIR / filename

    def get_updated_scenario_path(self, original_path: Path, new_version: str) -> Path:
        """
        Получить путь к обновленному сценарию

        Args:
            original_path: Путь к оригинальному файлу
            new_version: Новая версия

        Returns:
            Путь к обновленному файлу
        """
        original_name = original_path.stem  # Имя без расширения
        extension = original_path.suffix
        new_name = f"{original_name}_updated_to_v{new_version}{extension}"
        return self.UPDATED_SCENARIOS_DIR / new_name


# Глобальный экземпляр конфигурации
config = AppConfig()
