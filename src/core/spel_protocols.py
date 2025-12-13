"""
Protocols для SpEL-компонентов (ЗАМЕЧАНИЕ #3).
Определяют интерфейсы для мокирования в тестах.
"""

from typing import Protocol, Dict, Any, Optional

from src.core.spel_ast import ASTNode
from src.core.spel_context import SpelContext


class TranspilerProtocol(Protocol):
    """
    Протокол для SpEL Transpiler.

    Определяет интерфейс транспиляции AST → Python-код.
    """

    def transpile(
            self,
            node: ASTNode,
            context_name: str = "data",
            use_safe_navigation: bool = True
    ) -> str:
        """
        Транспилировать AST-узел в Python-код.

        Args:
            node: AST-узел
            context_name: Имя переменной для контекста (по умолчанию "data")
            use_safe_navigation: Использовать безопасный доступ к полям (?.  → .get())

        Returns:
            Строка с Python-кодом
        """
        ...


class EvaluatorProtocol(Protocol):
    """
    Протокол для SpEL Evaluator.

    Определяет интерфейс выполнения SpEL-выражений.
    """

    def evaluate(
            self,
            expression: str,
            data: Dict[str, Any],
            context: Optional[SpelContext] = None
    ) -> Any:
        """
        Выполнить SpEL-выражение на JSON-данных.

        Args:
            expression: SpEL-выражение (строка)
            data: JSON-данные (текущий объект)
            context: Контекст выполнения (опционально)

        Returns:
            Результат выполнения выражения (bool, int, str, ...)
        """
        ...

    def evaluate_boolean(
            self,
            expression: str,
            data: Dict[str, Any],
            context: Optional[SpelContext] = None
    ) -> bool:
        """
        Выполнить SpEL-выражение и вернуть boolean.

        Args:
            expression: SpEL-выражение (строка)
            data: JSON-данные (текущий объект)
            context: Контекст выполнения (опционально)

        Returns:
            True/False результат выражения
        """
        ...
