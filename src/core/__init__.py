"""
Core module for json-scenario-generator.
Содержит базовые компоненты: парсеры, компараторы, SpEL-движок.
"""

from .schema_comparator import SchemaComparator
from .spel_ast import (
    ASTNode,
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
    NodeType,
    SpELNode,
)
from .spel_parser import SpelParser, get_spel_parser
from .spel_functions import SpelFunctions, spel_functions

__all__ = [
    # Schema Comparator
    'SchemaComparator',

    # SpEL AST
    'ASTNode',
    'LiteralNode',
    'FieldNode',
    'ParentNNode',
    'RootNode',
    'UnaryOpNode',
    'BinaryOpNode',
    'NaryOpNode',
    'CallMethodNode',
    'FilterNode',
    'MapNode',
    'AnyMatchNode',
    'AllMatchNode',
    'NoneMatchNode',
    'HasSizeNode',
    'NodeType',
    'SpELNode',

    # SpEL Parser
    'SpelParser',
    'get_spel_parser',

    # SpEL Functions
    'SpelFunctions',
    'spel_functions',
]
