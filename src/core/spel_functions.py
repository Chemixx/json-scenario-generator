"""
SpEL функции валидации.

Функции для использования в SpEL-выражениях:
- is_valid_tax_num(): Проверка ИНН
- is_valid_uuid(): Проверка UUID
- digits_check(): Проверка количества цифр до/после запятой
- is_dictionary_value(): Проверка значения в справочнике
"""

from __future__ import annotations

import re
import uuid
from typing import Any


def is_valid_tax_num(value: Any) -> bool:
    """
    Проверка корректности ИНН (10 или 12 цифр).

    Args:
        value: Значение для проверки

    Returns:
        True если ИНН валиден, иначе False

    Examples:
        >>> is_valid_tax_num("1234567890")
        True
        >>> is_valid_tax_num("123")
        False
    """
    if not isinstance(value, str):
        return False
    # ИНН: 10 или 12 цифр
    return bool(re.match(r"^\d{10}$|^\d{12}$", value))


def is_valid_uuid(value: Any) -> bool:
    """
    Проверка корректности UUID.

    Args:
        value: Значение для проверки

    Returns:
        True если UUID валиден, иначе False

    Examples:
        >>> is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> is_valid_uuid("invalid-uuid")
        False
    """
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def digits_check(value: Any, integer: int = 10, fraction: int = 2) -> bool:
    """
    Проверка количества цифр в числе (до и после запятой).

    Args:
        value: Значение для проверки
        integer: Максимальное количество цифр ДО запятой (по умолчанию 10)
        fraction: Максимальное количество цифр ПОСЛЕ запятой (по умолчанию 2)

    Returns:
        True если число соответствует ограничениям, иначе False

    Examples:
        >>> digits_check("123.45", 5, 2)
        True
        >>> digits_check("123.456", 5, 2) # Слишком много дробных
        False
        >>> digits_check("123456.78", 5, 2) # Слишком много целых
        False
    """
    if value is None:
        return True  # None считается валидным (поле может быть необязательным)

    # Преобразуем в строку для проверки
    value_str = str(value)

    # Разделяем на целую и дробную часть
    parts = value_str.split(".")

    # Проверка целой части
    integer_part = parts[0].lstrip("-")  # Убираем знак минуса
    if len(integer_part) > integer:
        return False

    # Проверка дробной части (если есть)
    if len(parts) > 1:
        fraction_part = parts[1]
        if len(fraction_part) > fraction:
            return False

    return True


def is_dictionary_value(
    dictionary_name: str,
    value: Any,
    _additional_filter: dict[str, Any] | None = None,  # ✅ ИСПРАВЛЕНО: префикс _
) -> bool:
    """
    Проверка наличия значения в справочнике.

    Используется в SpEL как: isDictionaryValue(dictName, value)

    Args:
        dictionary_name: Название справочника (например, "LOAN_TYPE", "CHANNEL")
        value: Значение для проверки
        _additional_filter: Дополнительные фильтры (опционально, не используется пока)

    Returns:
        True если значение найдено в справочнике

    Note:
        Для production использовать реальную загрузку справочников из Excel.
        Текущая реализация — заглушка для демонстрации.

    Examples:
        >>> is_dictionary_value("LOAN_TYPE", "CONSUMER")
        True
        >>> is_dictionary_value("LOAN_TYPE", "INVALID")
        False
    """
    # ===== ЗАГЛУШКА: для демонстрации =====
    # В production подключить DictionaryLoader из src/loaders/dictionary_loader.py

    mock_dictionaries = {
        "LOAN_TYPE": ["CONSUMER", "MORTGAGE", "AUTO", "BUSINESS"],
        "CHANNEL": ["WEB", "MOBILE", "OFFICE", "PARTNER"],
        "PRODUCT_CD": ["REACT", "CLASSIC", "PREMIUM"],
        "CLIENT_TYPE": ["INDIVIDUAL", "ENTREPRENEUR", "LEGAL_ENTITY"],
    }

    # Получить значения справочника
    valid_values = mock_dictionaries.get(dictionary_name, [])

    # Проверить наличие значения
    return value in valid_values
