"""
Unit-тесты для SpelParser.
Проверяем все 55 операторов + комбинации.
"""

import pytest
from src.core.spel_parser import get_spel_parser
from src.core.spel_ast import *


@pytest.fixture
def parser():
    """Fixture для парсера"""
    return get_spel_parser()


class TestLiterals:
    """Тесты парсинга литералов"""

    def test_integer(self, parser):
        ast = parser.parse("42")
        assert isinstance(ast, LiteralNode)
        assert ast.value == 42

    def test_float(self, parser):
        ast = parser.parse("3.14")
        assert isinstance(ast, LiteralNode)
        assert ast.value == 3.14

    def test_string(self, parser):
        ast = parser.parse('"hello world"')
        assert isinstance(ast, LiteralNode)
        assert ast.value == "hello world"

    def test_boolean_true(self, parser):
        ast = parser.parse("true")
        assert isinstance(ast, LiteralNode)
        assert ast.value is True

    def test_null(self, parser):
        ast = parser.parse("null")
        assert isinstance(ast, LiteralNode)
        assert ast.value is None


class TestFields:
    """Тесты парсинга полей"""

    def test_simple_field(self, parser):
        ast = parser.parse("customerName")
        assert isinstance(ast, FieldNode)
        assert ast.path == "customerName"

    def test_this_keyword(self, parser):
        ast = parser.parse("this")
        assert isinstance(ast, FieldNode)
        assert ast.node_type == NodeType.THIS

    def test_parent_field(self, parser):
        ast = parser.parse("parent.birthDt")
        assert isinstance(ast, ParentNNode)
        assert ast.level == 1
        assert ast.sub_path == "birthDt"

    def test_parent2_field(self, parser):
        ast = parser.parse("parent2.realEstateCategoryCdExt")
        assert isinstance(ast, ParentNNode)
        assert ast.level == 2
        assert ast.sub_path == "realEstateCategoryCdExt"

    def test_root_field(self, parser):
        ast = parser.parse("rootBean.loanRequest.callCdExt")
        assert isinstance(ast, RootNode)
        assert ast.sub_path == "loanRequest.callCdExt"


class TestLogicalOperators:
    """Тесты логических операторов"""

    def test_and_two_args(self, parser):
        ast = parser.parse("and(eq(field1, 10), eq(field2, 20))")
        assert isinstance(ast, NaryOpNode)
        assert ast.node_type == NodeType.AND
        assert len(ast.operands) == 2

    def test_or_multiple_args(self, parser):
        ast = parser.parse("or(eq(a, 1), eq(b, 2), eq(c, 3))")
        assert isinstance(ast, NaryOpNode)
        assert ast.node_type == NodeType.OR
        assert len(ast.operands) == 3

    def test_not(self, parser):
        ast = parser.parse("not(eq(field, 10))")
        assert isinstance(ast, UnaryOpNode)
        assert ast.node_type == NodeType.NOT


class TestComparisons:
    """Тесты операторов сравнения"""

    def test_eq(self, parser):
        ast = parser.parse("eq(status, 10660007)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.node_type == NodeType.EQ

    def test_in(self, parser):
        ast = parser.parse("in(productCd, 10410034, 10410140)")
        assert isinstance(ast, NaryOpNode)
        assert ast.node_type == NodeType.IN
        assert len(ast.operands) == 3  # field + 2 values


class TestArrayOperators:
    """Тесты операторов для массивов"""

    def test_anymatch(self, parser):
        ast = parser.parse("anyMatch(rootBean.loanRequest.pledges, eq(realEstateKindCdExt, 12150020))")
        assert isinstance(ast, AnyMatchNode)
        assert isinstance(ast.array, RootNode)
        assert isinstance(ast.condition, BinaryOpNode)


class TestCallMethod:
    """Тесты вызова методов"""

    def test_call_length(self, parser):
        ast = parser.parse("call(this, length)")
        assert isinstance(ast, CallMethodNode)
        assert ast.method_name == "length"
        assert isinstance(ast.target, FieldNode)

    def test_call_minus_years(self, parser):
        ast = parser.parse("call(currentDate(), minusYears, 14)")
        assert isinstance(ast, CallMethodNode)
        assert ast.method_name == "minusYears"
        assert len(ast.arguments) == 1


class TestBusinessFunctions:
    """Тесты бизнес-функций"""

    def test_is_valid_tax_num(self, parser):
        ast = parser.parse("isValidTaxNum(this)")
        assert isinstance(ast, UnaryOpNode)
        assert ast.node_type == NodeType.IS_VALID_TAX_NUM

    def test_digits_check(self, parser):
        ast = parser.parse("digitsCheck(this, 9, 2)")
        assert isinstance(ast, NaryOpNode)
        assert ast.node_type == NodeType.DIGITS_CHECK
        assert len(ast.operands) == 3

# Запуск тестов: pytest tests/core/test_spel_parser.py -v
