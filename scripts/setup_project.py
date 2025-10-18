"""
Скрипт для автоматического создания структуры проекта
"""
import os
from pathlib import Path


def create_directory_structure():
    """Создает структуру директорий проекта"""

    directories = [
        # Data
        "data/schemas",
        "data/dictionaries",
        "data/releases",
        "data/mappings",
        "data/scenarios",

        # Source code
        "src/models",
        "src/parsers",
        "src/loaders",
        "src/core",
        "src/reports",
        "src/utils",
        "src/cli/commands",
        "src/cli/ui",

        # Tests
        "tests/unit",
        "tests/integration",
        "tests/fixtures/schemas",
        "tests/fixtures/dictionaries",
        "tests/fixtures/scenarios",

        # Config
        "config",

        # Docs
        "docs",

        # Scripts
        "scripts",

        # Web (опционально)
        "web/backend/routers",
        "web/backend/schemas",
        "web/frontend/src",
        "web/frontend/public",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

        # Создаем __init__.py для Python пакетов
        if directory.startswith("src/") or directory.startswith("tests/"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    print("✅ Структура проекта создана успешно!")


if __name__ == "__main__":
    create_directory_structure()
