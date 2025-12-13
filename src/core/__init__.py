"""
Core module для json-scenario-generator.

Экспортирует основные классы и функции для работы с:
- JSON Schema парсингом и валидацией
- SpEL-выражениями
- Условными требованиями
- Сравнением версий схем
"""

from src.core.schema_comparator import SchemaComparator
from src.core.spel_ast import (
    AllMatchNode,
    AnyMatchNode,
    ASTNode,
    BinaryOpNode,
    FilterNode,
    HasSizeNode,
    LiteralNode,
    VariableNode,
    FunctionCallNode,
    NodeType,
    MapNode,
    NoneMatchNode,
    UnaryOpNode,
)
from src.core.spel_context import SpelContext
from src.core.spel_evaluator import SpelEvaluator
from src.core.spel_parser import SpelParser
from src.core.spel_transpiler import SpelTranspiler

__all__ = [
    # SchemaComparator
    "SchemaComparator",
    # SpEL AST nodes
    "ASTNode",
    "LiteralNode",
    "UnaryOpNode",
    "BinaryOpNode",
    "FilterNode",
    "MapNode",
    "AnyMatchNode",
    "AllMatchNode",
    "NoneMatchNode",
    "HasSizeNode",
    "VariableNode",
    "FunctionCallNode",
    "NodeType",
    # SpEL components
    "SpelContext",
    "SpelEvaluator",
    "SpelParser",
    "SpelTranspiler",
]
