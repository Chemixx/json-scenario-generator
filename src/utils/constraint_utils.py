"""
Общие функции проверок ограничений (constraints).

Используется JsonValidator._check_constraints() и JsonActualizer._validate_value().
"""
import re
from decimal import Decimal
from typing import Any, Optional, Union

Number = Union[int, float, Decimal]


def check_constraint(name: str, expected: Any, actual: Any) -> Optional[str]:
    """Проверить ограничение. Вернуть None если ОК, иначе сообщение об ошибке."""
    checker = _CHECKERS.get(name)
    return checker(expected, actual) if checker else None


def check_min_length(expected: int, actual: Any) -> Optional[str]:
    if len(str(actual)) < expected:
        return f"minLength: ожидалось >= {expected}, фактически {len(str(actual))}"
    return None


def check_max_length(expected: int, actual: Any) -> Optional[str]:
    if len(str(actual)) > expected:
        return f"maxLength: ожидалось <= {expected}, фактически {len(str(actual))}"
    return None


def check_pattern(expected: str, actual: Any) -> Optional[str]:
    if isinstance(actual, str) and not re.match(expected, actual):
        return f"pattern: значение '{actual}' не соответствует '{expected}'"
    return None


def check_minimum(expected: Number, actual: Number) -> Optional[str]:
    if actual < expected:
        return f"minimum: ожидалось >= {expected}, фактически {actual}"
    return None


def check_maximum(expected: Number, actual: Number) -> Optional[str]:
    if actual > expected:
        return f"maximum: ожидалось <= {expected}, фактически {actual}"
    return None


def check_min_items(expected: int, actual: Any) -> Optional[str]:
    if isinstance(actual, list) and len(actual) < expected:
        return f"minItems: ожидалось >= {expected}, фактически {len(actual)}"
    return None


def check_max_items(expected: int, actual: Any) -> Optional[str]:
    if isinstance(actual, list) and len(actual) > expected:
        return f"maxItems: ожидалось <= {expected}, фактически {len(actual)}"
    return None


def check_enum(expected: list, actual: Any) -> Optional[str]:
    if actual not in expected:
        return f"enum: значение '{actual}' не в допустимых {expected}"
    return None


def check_max_int_length(expected: int, actual: Number) -> Optional[str]:
    int_part = len(str(abs(int(actual))))
    if int_part > expected:
        return f"maxIntLength: ожидалось <= {expected}, фактически {int_part}"
    return None


def check_max_frac_length(expected: int, actual: Any) -> Optional[str]:
    if isinstance(actual, Decimal):
        sign, digits, exponent = actual.as_tuple()
        frac_digits = max(0, -exponent)
        if frac_digits > expected:
            return f"maxFracLength: ожидалось <= {expected}, фактически {frac_digits}"
    elif isinstance(actual, float):
        frac_str = str(actual).split(".")[-1] if "." in str(actual) else "0"
        if len(frac_str) > expected:
            return f"maxFracLength: ожидалось <= {expected}, фактически {len(frac_str)}"
    return None


_CHECKERS = {
    "minLength": check_min_length,
    "maxLength": check_max_length,
    "pattern": check_pattern,
    "minimum": check_minimum,
    "maximum": check_maximum,
    "minItems": check_min_items,
    "maxItems": check_max_items,
    "enum": check_enum,
    "maxIntLength": check_max_int_length,
    "maxFracLength": check_max_frac_length,
}