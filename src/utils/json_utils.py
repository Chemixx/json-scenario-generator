"""
Утилиты для работы с JSON
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.utils.logger import get_logger

# Импорты для валидации JSON Schema
try:
    from jsonschema import validate, ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    # Заглушки для типов, если jsonschema не установлен
    ValidationError = Exception  # type: ignore
    Draft7Validator = None  # type: ignore

logger = get_logger(__name__)


# ============================================================================
# ЗАГРУЗКА И СОХРАНЕНИЕ JSON
# ============================================================================

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Загрузить JSON из файла

    Args:
        file_path: Путь к JSON файлу

    Returns:
        Словарь с данными из JSON

    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если JSON невалидный

    Example:
        >>> data = load_json(Path("data.json"))
        >>> print(data["key"])
    """
    if not file_path.exists():
        logger.error(f"❌ Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    try:
        logger.debug(f"📂 Загрузка JSON из {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ JSON успешно загружен из {file_path.name}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга JSON в {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при загрузке {file_path}: {e}")
        raise


def save_json(
    data: Dict[str, Any],
    file_path: Path,
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    Сохранить данные в JSON файл

    Args:
        data: Данные для сохранения
        file_path: Путь к файлу
        indent: Отступ для форматирования (по умолчанию 2)
        ensure_ascii: Экранировать ли non-ASCII символы (по умолчанию False)

    Example:
        >>> data = {"key": "value"}
        >>> save_json(data, Path("output.json"))
    """
    try:
        logger.debug(f"💾 Сохранение JSON в {file_path}")

        # Создаем директорию, если её нет
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

        logger.info(f"✅ JSON успешно сохранен в {file_path.name}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения JSON в {file_path}: {e}")
        raise


# ============================================================================
# ВАЛИДАЦИЯ JSON SCHEMA
# ============================================================================

def validate_json_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any]
) -> bool:
    """
    Валидация JSON данных по схеме

    Args:
        data: Данные для валидации
        schema: JSON Schema для валидации

    Returns:
        True, если данные валидны

    Raises:
        ValidationError: Если данные не соответствуют схеме
        ImportError: Если библиотека jsonschema не установлена

    Example:
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> data = {"name": "Test"}
        >>> validate_json_schema(data, schema)
        True
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.error("❌ Библиотека jsonschema не установлена")
        raise ImportError("Установите jsonschema: pip install jsonschema")

    try:
        validate(instance=data, schema=schema)
        logger.debug("✅ JSON валидация успешна")
        return True
    except ValidationError as e:
        logger.error(f"❌ JSON валидация не прошла: {e.message}")
        raise


def get_validation_errors(
    data: Dict[str, Any],
    schema: Dict[str, Any]
) -> List[Any]:
    """
    Получить список ошибок валидации (без выброса исключения)

    Args:
        data: Данные для валидации
        schema: JSON Schema для валидации

    Returns:
        Список ошибок валидации (пустой, если ошибок нет)

    Raises:
        ImportError: Если библиотека jsonschema не установлена

    Example:
        >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        >>> data = {"name": 123}
        >>> errors = get_validation_errors(data, schema)
        >>> len(errors) > 0
        True
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.error("❌ Библиотека jsonschema не установлена")
        raise ImportError("Установите jsonschema: pip install jsonschema")

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        logger.warning(f"⚠️ Найдено {len(errors)} ошибок валидации")
        for error in errors:
            logger.debug(f"  - {error.message}")
    else:
        logger.debug("✅ Валидация пройдена без ошибок")

    return errors


# ============================================================================
# ФОРМАТИРОВАНИЕ И ВЫВОД
# ============================================================================

def pretty_print_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Форматированный вывод JSON

    Args:
        data: Данные для форматирования
        indent: Отступ (по умолчанию 2)

    Returns:
        Отформатированная строка JSON

    Example:
        >>> data = {"key": "value", "nested": {"a": 1}}
        >>> print(pretty_print_json(data))
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def minify_json(data: Dict[str, Any]) -> str:
    """
    Минифицировать JSON (без пробелов и переносов строк)

    Args:
        data: Данные для минификации

    Returns:
        Минифицированная строка JSON

    Example:
        >>> data = {"key": "value"}
        >>> minify_json(data)
        '{"key":"value"}'
    """
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


# ============================================================================
# РАБОТА СО СХЕМАМИ
# ============================================================================

def merge_schemas(base_schema: Dict[str, Any], override_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Объединить две JSON Schema (override переопределяет base)

    Args:
        base_schema: Базовая схема
        override_schema: Схема для переопределения

    Returns:
        Объединенная схема

    Example:
        >>> base = {"type": "object", "properties": {"a": {"type": "string"}}}
        >>> override = {"properties": {"b": {"type": "integer"}}}
        >>> merged = merge_schemas(base, override)
    """
    result = base_schema.copy()

    for key, value in override_schema.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_schemas(result[key], value)
        else:
            result[key] = value

    return result


def extract_required_fields(schema: Dict[str, Any], prefix: str = "") -> List[str]:
    """
    Извлечь список обязательных полей из JSON Schema

    Args:
        schema: JSON Schema
        prefix: Префикс пути (для рекурсии)

    Returns:
        Список путей к обязательным полям

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "required": ["name"],
        ...     "properties": {"name": {"type": "string"}}
        ... }
        >>> extract_required_fields(schema)
        ['name']
    """
    required_fields: List[str] = []

    # Получаем обязательные поля на текущем уровне
    required = schema.get("required", [])
    for field_name in required:
        field_path = f"{prefix}/{field_name}" if prefix else field_name
        required_fields.append(field_path)

    # Рекурсивно обрабатываем вложенные объекты
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if field_schema.get("type") == "object":
            field_path = f"{prefix}/{field_name}" if prefix else field_name
            nested_required = extract_required_fields(field_schema, prefix=field_path)
            required_fields.extend(nested_required)

    return required_fields
