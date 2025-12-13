"""
SpEL Evaluator.

Выполняет SpEL-выражения в контексте данных с поддержкой:
- Навигации: data, root, parent, parent2, parent3
- Функций валидации: isValidTaxNum(), isValidUuid(), digitsCheck()
- Справочников: isDictionaryValue()
"""

from __future__ import annotations

from typing import Any

from src.core.spel_context import SpelContext
from src.core.spel_parser import SpelParser
from src.core.spel_transpiler import SpelTranspiler

# ===== ПРЯМОЙ ИМПОРТ ФУНКЦИЙ (БЕЗ TRY-EXCEPT) =====
from src.core.spel_functions import (
    digits_check,
    is_dictionary_value,
    is_valid_tax_num,
    is_valid_uuid,
)


class SpelEvaluator:
    """
    Вычислитель SpEL-выражений.

    Преобразует SpEL-выражение в Python-код и выполняет его
    в безопасном контексте с ограниченным набором функций.
    """

    def __init__(self):
        """Инициализация evaluator с парсером и транспилятором."""
        self.parser = SpelParser()  # ✅ БЕЗ параметров!
        self.transpiler = SpelTranspiler()

    def evaluate(
        self,
        expression: str,
        context: SpelContext,
        custom_functions: dict[str, Any] | None = None,
    ) -> Any:
        """
        Вычислить SpEL-выражение в контексте.

        Args:
            expression: SpEL-выражение (строка)
            context: Контекст выполнения (данные, parent, root)
            custom_functions: Дополнительные функции для eval()

        Returns:
            Результат вычисления выражения

        Raises:
            SyntaxError: При синтаксических ошибках в SpEL
            ValueError: При ошибках транспиляции
            RuntimeError: При ошибках выполнения eval()

        Examples:
            >>> evaluator = SpelEvaluator()
            >>> ctx = SpelContext(data={"inn": "1234567890"})
            >>> result = evaluator.evaluate("isValidTaxNum(data.inn)", ctx)
            >>> print(result)  # True
        """
        # 1. Парсим выражение в AST
        ast = self.parser.parse(expression)

        # 2. Транспилируем AST в Python-код
        python_code = self.transpiler.transpile(ast)

        # 3. Подготавливаем контекст для eval()
        eval_context = self._prepare_eval_context(context, custom_functions)

        # 4. Выполняем Python-код
        try:
            eval_result = eval(python_code, {"__builtins__": {}}, eval_context)
            return eval_result
        except Exception as e:
            raise RuntimeError(
                f"Error evaluating SpEL expression '{expression}': {e}"
            ) from e

    @staticmethod
    def _prepare_eval_context(
        context: SpelContext,
        custom_functions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Подготовить контекст для eval() с переменными и функциями.

        Добавляет:
        - data, root, parent, parent2, parent3 из контекста
        - Пользовательские функции (isValidTaxNum, digitsCheck, etc.)

        Args:
            context: SpEL контекст
            custom_functions: Дополнительные функции

        Returns:
            Словарь для eval() с переменными и функциями
        """
        # ✅ ИСПРАВЛЕНО: Преобразуем EvaluationContextDict в обычный dict
        eval_context = dict(context.to_eval_context())

        # РЕГИСТРАЦИЯ ФУНКЦИЙ ВАЛИДАЦИИ
        eval_context["isValidTaxNum"] = is_valid_tax_num
        eval_context["isValidUuid"] = is_valid_uuid
        eval_context["digitsCheck"] = digits_check
        eval_context["isDictionaryValue"] = is_dictionary_value

        # Добавить пользовательские функции
        if custom_functions:
            eval_context.update(custom_functions)

        # ===== WHITELIST БЕЗОПАСНЫХ ИМЕН =====
        safe_names = {
            # Данные из контекста
            "data",
            "root",
            "parent",
            "parent2",
            "parent3",
            # Функции валидации
            "isValidTaxNum",
            "isValidUuid",
            "digitsCheck",
            "isDictionaryValue",
            # Константы Python
            "True",
            "False",
            "None",
            # Встроенные функции для коллекций
            "len",
            "any",
            "all",
            "sum",
            "min",
            "max",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
        }

        # Фильтрация: оставляем только имена из whitelist
        safe_context = {k: v for k, v in eval_context.items() if k in safe_names}

        return safe_context


def get_spel_evaluator() -> SpelEvaluator:
    """
    Фабричная функция для создания evaluator.

    Returns:
        Экземпляр SpelEvaluator
    """
    return SpelEvaluator()
