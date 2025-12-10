"""
AST-модели для SpEL-выражений.
Поддерживает все 55 операторов из V72-V74 JSON Schema.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union
from enum import Enum
from abc import ABC, abstractmethod


class NodeType(Enum):
    """Типы AST-узлов"""

    # Литералы
    LITERAL = "literal"
    FIELD = "field"

    # Логические операторы
    AND = "and"
    OR = "or"
    NOT = "not"

    # Сравнения
    EQ = "eq"
    NOT_EQ = "notEq"
    IN = "in"
    NOT_IN = "notIn"
    EQ_OR_GREATER = "eqOrGreater"
    EQ_OR_LESS = "eqOrLess"

    # Null-проверки
    IS_NULL = "isNull"
    NOT_NULL = "notNull"
    IS_BLANK = "isBlank"
    NOT_BLANK = "notBlank"

    # Массивы
    ANY_MATCH = "anyMatch"
    ALL_MATCH = "allMatch"
    NONE_MATCH = "noneMatch"
    FILTER = "filter"
    MAP = "map"
    HAS_SIZE = "hasSize"
    SIZE = "size"
    NOT_EMPTY_LIST = "notEmptyList"
    CONTAINS_ALL = "containsAll"

    # Строки
    LENGTH = "length"

    # Даты
    CURRENT_DATE = "currentDate"
    MINUS_YEARS = "minusYears"
    MINUS_DAYS = "minusDays"
    TO_LOCAL_DATE = "toLocalDate"
    IS_AFTER = "isAfter"
    COMPARE_TO = "compareTo"

    # Бизнес-функции
    IS_VALID_TAX_NUM = "isValidTaxNum"
    IS_VALID_UUID = "isValidUuid"
    DIGITS_CHECK = "digitsCheck"
    IS_DICTIONARY_VALUE = "isDictionaryValue"

    # Навигация
    THIS = "this"
    ROOT = "root"
    PARENT = "parent"

    # Вызов методов
    CALL = "call"


@dataclass
class ASTNode(ABC):
    """Базовый класс для всех AST-узлов"""

    node_type: NodeType

    @abstractmethod
    def __repr__(self) -> str:
        """Строковое представление для отладки"""
        pass


@dataclass
class LiteralNode(ASTNode):
    """Литеральное значение: число, строка, boolean, null"""

    value: Any  # int, str, bool, None

    def __init__(self, value: Any):
        super().__init__(NodeType.LITERAL)
        self.value = value

    def __repr__(self) -> str:
        if self.value is None:
            return "null"
        elif isinstance(self.value, bool):
            return str(self.value).lower()
        elif isinstance(self.value, str):
            return f'"{self.value}"'
        else:
            return str(self.value)


@dataclass
class FieldNode(ASTNode):
    """Ссылка на поле: this, parent.field, root.loanRequest.callCdExt"""

    path: str  # "this", "parent.birthDt", "rootBean.loanRequest.callCdExt"

    def __init__(self, path: str):
        # Определяем тип узла по префиксу пути
        if path in ("this", "this."):
            node_type = NodeType.THIS
        elif path.startswith("root") or path.startswith("#rootBean"):
            node_type = NodeType.ROOT
        elif path.startswith("parent"):
            node_type = NodeType.PARENT
        else:
            node_type = NodeType.FIELD

        super().__init__(node_type)
        self.path = path

    def __repr__(self) -> str:
        return self.path


@dataclass
class ParentNNode(FieldNode):
    """Навигация parent2, parent3, parent$2, parent$3"""

    level: int  # 1, 2, 3...
    sub_path: Optional[str] = None  # "realEstateCategoryCdExt"

    def __init__(self, level: int, sub_path: Optional[str] = None):
        self.level = level
        self.sub_path = sub_path

        # Формируем полный путь
        if sub_path:
            path = (
                f"parent{level}.{sub_path}" if level > 1 else f"parent.{sub_path}"
            )
        else:
            path = f"parent{level}" if level > 1 else "parent"

        super().__init__(path)

    def __repr__(self) -> str:
        return self.path


@dataclass
class RootNode(FieldNode):
    """Навигация к корню: rootBean.loanRequest.callCdExt"""

    sub_path: str  # "loanRequest.callCdExt"

    def __init__(self, sub_path: str):
        self.sub_path = sub_path
        super().__init__(f"rootBean.{sub_path}")

    def __repr__(self) -> str:
        return self.path


@dataclass
class UnaryOpNode(ASTNode):
    """Унарный оператор: not(expr), isNull(field)"""

    operand: ASTNode

    def __repr__(self) -> str:
        return f"{self.node_type.value}({self.operand})"


@dataclass
class BinaryOpNode(ASTNode):
    """Бинарный оператор: eq(field, value), and(expr1, expr2)"""

    left: ASTNode
    right: ASTNode

    def __repr__(self) -> str:
        return f"{self.node_type.value}({self.left}, {self.right})"


@dataclass
class NaryOpNode(ASTNode):
    """N-арный оператор: and(expr1, expr2, expr3), in(field, val1, val2, val3)"""

    operands: List[ASTNode]

    def __repr__(self) -> str:
        args = ", ".join(str(op) for op in self.operands)
        return f"{self.node_type.value}({args})"


@dataclass
class CallMethodNode(ASTNode):
    """Вызов метода: call(field, length), call(date, minusYears, 14)"""

    target: ASTNode  # Объект, на котором вызывается метод
    method_name: str  # "length", "minusYears", "compareTo"
    arguments: List[ASTNode] = field(default_factory=list)

    def __init__(
        self,
        target: ASTNode,
        method_name: str,
        arguments: Optional[List[ASTNode]] = None,
    ):
        super().__init__(NodeType.CALL)
        self.target = target
        self.method_name = method_name
        self.arguments = arguments or []

    def __repr__(self) -> str:
        args_str = ", ".join([self.method_name] + [str(arg) for arg in self.arguments])
        return f"call({self.target}, {args_str})"


@dataclass
class FilterNode(ASTNode):
    """filter(array, condition) → фильтрация массива"""

    array: ASTNode  # Массив для фильтрации
    condition: ASTNode  # Условие фильтрации

    def __init__(self, array: ASTNode, condition: ASTNode):
        super().__init__(NodeType.FILTER)
        self.array = array
        self.condition = condition

    def __repr__(self) -> str:
        return f"filter({self.array}, {self.condition})"


@dataclass
class MapNode(ASTNode):
    """map(array, expression) → маппинг массива"""

    array: ASTNode
    expression: ASTNode

    def __init__(self, array: ASTNode, expression: ASTNode):
        super().__init__(NodeType.MAP)
        self.array = array
        self.expression = expression

    def __repr__(self) -> str:
        return f"map({self.array}, {self.expression})"


@dataclass
class AnyMatchNode(ASTNode):
    """anyMatch(array, condition) → проверка, что хотя бы один элемент удовлетворяет условию"""

    array: ASTNode
    condition: ASTNode

    def __init__(self, array: ASTNode, condition: ASTNode):
        super().__init__(NodeType.ANY_MATCH)
        self.array = array
        self.condition = condition

    def __repr__(self) -> str:
        return f"anyMatch({self.array}, {self.condition})"


@dataclass
class AllMatchNode(ASTNode):
    """allMatch(array, condition) → все элементы удовлетворяют условию"""

    array: ASTNode
    condition: ASTNode

    def __init__(self, array: ASTNode, condition: ASTNode):
        super().__init__(NodeType.ALL_MATCH)
        self.array = array
        self.condition = condition

    def __repr__(self) -> str:
        return f"allMatch({self.array}, {self.condition})"


@dataclass
class NoneMatchNode(ASTNode):
    """noneMatch(array, condition) → ни один элемент не удовлетворяет условию"""

    array: ASTNode
    condition: ASTNode

    def __init__(self, array: ASTNode, condition: ASTNode):
        super().__init__(NodeType.NONE_MATCH)
        self.array = array
        self.condition = condition

    def __repr__(self) -> str:
        return f"noneMatch({self.array}, {self.condition})"


@dataclass
class HasSizeNode(ASTNode):
    """hasSize(array, expectedSize) → проверка размера массива"""

    array: ASTNode
    expected_size: ASTNode

    def __init__(self, array: ASTNode, expected_size: ASTNode):
        super().__init__(NodeType.HAS_SIZE)
        self.array = array
        self.expected_size = expected_size

    def __repr__(self) -> str:
        return f"hasSize({self.array}, {self.expected_size})"


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СОЗДАНИЯ УЗЛОВ ==========


def create_and(*operands: ASTNode) -> NaryOpNode:
    """Создать узел AND"""
    return NaryOpNode(NodeType.AND, list(operands))


def create_or(*operands: ASTNode) -> NaryOpNode:
    """Создать узел OR"""
    return NaryOpNode(NodeType.OR, list(operands))


def create_not(operand: ASTNode) -> UnaryOpNode:
    """Создать узел NOT"""
    return UnaryOpNode(NodeType.NOT, operand)


def create_eq(left: ASTNode, right: ASTNode) -> BinaryOpNode:
    """Создать узел EQ"""
    return BinaryOpNode(NodeType.EQ, left, right)


def create_not_eq(left: ASTNode, right: ASTNode) -> BinaryOpNode:
    """Создать узел NOT_EQ"""
    return BinaryOpNode(NodeType.NOT_EQ, left, right)


def create_in(field: ASTNode, *values: ASTNode) -> NaryOpNode:
    """Создать узел IN"""
    return NaryOpNode(NodeType.IN, [field] + list(values))


def create_not_in(field: ASTNode, *values: ASTNode) -> NaryOpNode:
    """Создать узел NOT_IN"""
    return NaryOpNode(NodeType.NOT_IN, [field] + list(values))


def create_is_null(operand: ASTNode) -> UnaryOpNode:
    """Создать узел IS_NULL"""
    return UnaryOpNode(NodeType.IS_NULL, operand)


def create_not_null(operand: ASTNode) -> UnaryOpNode:
    """Создать узел NOT_NULL"""
    return UnaryOpNode(NodeType.NOT_NULL, operand)


def create_is_blank(operand: ASTNode) -> UnaryOpNode:
    """Создать узел IS_BLANK"""
    return UnaryOpNode(NodeType.IS_BLANK, operand)


def create_not_blank(operand: ASTNode) -> UnaryOpNode:
    """Создать узел NOT_BLANK"""
    return UnaryOpNode(NodeType.NOT_BLANK, operand)


def create_any_match(array: ASTNode, condition: ASTNode) -> AnyMatchNode:
    """Создать узел ANY_MATCH"""
    return AnyMatchNode(array, condition)


def create_all_match(array: ASTNode, condition: ASTNode) -> AllMatchNode:
    """Создать узел ALL_MATCH"""
    return AllMatchNode(array, condition)


def create_none_match(array: ASTNode, condition: ASTNode) -> NoneMatchNode:
    """Создать узел NONE_MATCH"""
    return NoneMatchNode(array, condition)


def create_filter(array: ASTNode, condition: ASTNode) -> FilterNode:
    """Создать узел FILTER"""
    return FilterNode(array, condition)


def create_map(array: ASTNode, expression: ASTNode) -> MapNode:
    """Создать узел MAP"""
    return MapNode(array, expression)


def create_has_size(array: ASTNode, expected_size: ASTNode) -> HasSizeNode:
    """Создать узел HAS_SIZE"""
    return HasSizeNode(array, expected_size)


# Типы для type hints
SpELNode = Union[
    LiteralNode,
    FieldNode,
    ParentNNode,
    RootNode,
    UnaryOpNode,
    BinaryOpNode,
    NaryOpNode,
    CallMethodNode,
    FilterNode,
    MapNode,
    AnyMatchNode,
    AllMatchNode,
    NoneMatchNode,
    HasSizeNode,
]
