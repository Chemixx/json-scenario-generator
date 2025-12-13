"""
SpEL AST Nodes.

Узлы абстрактного синтаксического дерева (AST) для SpEL-выражений.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Тип узла AST."""

    LITERAL = "literal"
    VARIABLE = "variable"
    UNARY_OP = "unary_op"
    BINARY_OP = "binary_op"
    FUNCTION_CALL = "function_call"
    FILTER = "filter"
    MAP = "map"
    ALL_MATCH = "all_match"
    ANY_MATCH = "any_match"
    NONE_MATCH = "none_match"
    HAS_SIZE = "has_size"


@dataclass
class ASTNode:
    """
    Базовый узел AST.

    Все узлы должны наследоваться от этого класса.
    """

    node_type: NodeType

    def __repr__(self) -> str:
        """Строковое представление узла."""
        return f"{self.__class__.__name__}({self.node_type.value})"


@dataclass
class LiteralNode(ASTNode):
    """
    Литерал (число, строка, True/False/None).

    Examples:
        >>> node = LiteralNode(42)
        >>> print(node.value)  # 42
        >>> node = LiteralNode("test")
        >>> print(node.value)  # "test"
    """

    value: Any

    def __init__(self, value: Any):
        """Инициализация литерала."""
        super().__init__(NodeType.LITERAL)
        self.value = value

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"LiteralNode({self.value!r})"


@dataclass
class VariableNode(ASTNode):
    """
    Переменная (data.inn, parent.field, root.value).

    Examples:
        >>> node = VariableNode("data.inn")
        >>> print(node.name)  # "data.inn"
        >>> node = VariableNode("parent.documentTypeCd")
        >>> print(node.name)  # "parent.documentTypeCd"
    """

    name: str

    def __init__(self, name: str):
        """Инициализация переменной."""
        super().__init__(NodeType.VARIABLE)
        self.name = name

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"VariableNode({self.name!r})"


@dataclass
class UnaryOpNode(ASTNode):
    """
    Унарная операция (not, !).

    Examples:
        >>> operand = VariableNode("data.isValid")
        >>> node = UnaryOpNode("not", operand)
        >>> print(node.operator)  # "not"
    """

    operator: str
    operand: ASTNode

    def __init__(self, operator: str, operand: ASTNode):
        """Инициализация унарной операции."""
        super().__init__(NodeType.UNARY_OP)
        self.operator = operator
        self.operand = operand

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"UnaryOpNode({self.operator!r}, {self.operand!r})"


@dataclass
class BinaryOpNode(ASTNode):
    """
    Бинарная операция (eq, and, or, lt, gt, etc.).

    Examples:
        >>> left = VariableNode("data.inn")
        >>> right = LiteralNode("123456789012")
        >>> node = BinaryOpNode("eq", left, right)
        >>> print(node.operator)  # "eq"
    """

    operator: str
    left: ASTNode
    right: ASTNode

    def __init__(self, operator: str, left: ASTNode, right: ASTNode):
        """Инициализация бинарной операции."""
        super().__init__(NodeType.BINARY_OP)
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"BinaryOpNode({self.operator!r}, {self.left!r}, {self.right!r})"


@dataclass
class FunctionCallNode(ASTNode):
    """
    Вызов функции (isValidTaxNum(...), digitsCheck(...)).

    Examples:
        >>> arg = VariableNode("data.inn")
        >>> node = FunctionCallNode("isValidTaxNum", [arg])
        >>> print(node.func_name)  # "isValidTaxNum"
        >>> print(node.args)       # [VariableNode('data.inn')]
    """

    func_name: str
    args: list[ASTNode]

    def __init__(self, func_name: str, args: list[ASTNode]):
        """Инициализация вызова функции."""
        super().__init__(NodeType.FUNCTION_CALL)
        self.func_name = func_name
        self.args = args

    def __repr__(self) -> str:
        """Строковое представление."""
        args_repr = ", ".join(repr(arg) for arg in self.args)
        return f"FunctionCallNode({self.func_name!r}, [{args_repr}])"


@dataclass
class FilterNode(ASTNode):
    """
    Фильтр коллекции (.?[condition]).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> condition = BinaryOpNode("gt", VariableNode("price"), LiteralNode(100))
        >>> node = FilterNode(collection, condition)
    """

    collection: ASTNode
    condition: ASTNode

    def __init__(self, collection: ASTNode, condition: ASTNode):
        """Инициализация фильтра."""
        super().__init__(NodeType.FILTER)
        self.collection = collection
        self.condition = condition

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"FilterNode({self.collection!r}, {self.condition!r})"


@dataclass
class MapNode(ASTNode):
    """
    Проекция коллекции (.![expression]).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> expression = VariableNode("name")
        >>> node = MapNode(collection, expression)
    """

    collection: ASTNode
    expression: ASTNode

    def __init__(self, collection: ASTNode, expression: ASTNode):
        """Инициализация проекции."""
        super().__init__(NodeType.MAP)
        self.collection = collection
        self.expression = expression

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"MapNode({self.collection!r}, {self.expression!r})"


@dataclass
class AllMatchNode(ASTNode):
    """
    Проверка "все элементы" (.allMatch(...)).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> condition = BinaryOpNode("gt", VariableNode("price"), LiteralNode(0))
        >>> node = AllMatchNode(collection, condition)
    """

    collection: ASTNode
    condition: ASTNode

    def __init__(self, collection: ASTNode, condition: ASTNode):
        """Инициализация allMatch."""
        super().__init__(NodeType.ALL_MATCH)
        self.collection = collection
        self.condition = condition

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"AllMatchNode({self.collection!r}, {self.condition!r})"


@dataclass
class AnyMatchNode(ASTNode):
    """
    Проверка "хотя бы один" (.anyMatch(...)).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> condition = BinaryOpNode("eq", VariableNode("status"), LiteralNode("active"))
        >>> node = AnyMatchNode(collection, condition)
    """

    collection: ASTNode
    condition: ASTNode

    def __init__(self, collection: ASTNode, condition: ASTNode):
        """Инициализация anyMatch."""
        super().__init__(NodeType.ANY_MATCH)
        self.collection = collection
        self.condition = condition

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"AnyMatchNode({self.collection!r}, {self.condition!r})"


@dataclass
class NoneMatchNode(ASTNode):
    """
    Проверка "ни один" (.noneMatch(...)).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> condition = BinaryOpNode("eq", VariableNode("status"), LiteralNode("invalid"))
        >>> node = NoneMatchNode(collection, condition)
    """

    collection: ASTNode
    condition: ASTNode

    def __init__(self, collection: ASTNode, condition: ASTNode):
        """Инициализация noneMatch."""
        super().__init__(NodeType.NONE_MATCH)
        self.collection = collection
        self.condition = condition

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"NoneMatchNode({self.collection!r}, {self.condition!r})"


@dataclass
class HasSizeNode(ASTNode):
    """
    Проверка размера коллекции (.hasSize(...)).

    Examples:
        >>> collection = VariableNode("data.items")
        >>> size = LiteralNode(5)
        >>> node = HasSizeNode(collection, size)
    """

    collection: ASTNode
    size: ASTNode

    def __init__(self, collection: ASTNode, size: ASTNode):
        """Инициализация hasSize."""
        super().__init__(NodeType.HAS_SIZE)
        self.collection = collection
        self.size = size

    def __repr__(self) -> str:
        """Строковое представление."""
        return f"HasSizeNode({self.collection!r}, {self.size!r})"
