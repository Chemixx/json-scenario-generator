"""
Утилиты приложения

Excel утилиты НЕ импортируются автоматически (pandas leak).
Импортируйте явно при необходимости: from src.utils.excel_utils import ...
"""
# Логирование
from .logger import log, log_function_call, LogBlock, get_logger

# JSON утилиты
from .json_utils import load_json, save_json, validate_json_schema, pretty_print_json

# Constraint utils
from .constraint_utils import check_constraint

# ASCII-иконки
from .icons import Icon

__all__ = [
    # Логирование
    "log",
    "log_function_call",
    "LogBlock",
    "get_logger",
    # JSON
    "load_json",
    "save_json",
    "validate_json_schema",
    "pretty_print_json",
    # Constraint utils
    "check_constraint",
    # ASCII-иконки
    "Icon",
]
