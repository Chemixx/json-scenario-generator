"""
Тесты для ConditionEvaluator.
Покрывает базовые операторы: eq, ne, in, and, or, not, isNull, notNull
"""

import pytest
from src.core.condition_evaluator import ConditionEvaluator, EvaluationContext
from src.core.spel_parser import SpelParser


@pytest.fixture
def evaluator():
    """Создать ConditionEvaluator"""
    return ConditionEvaluator()


@pytest.fixture
def parser():
    """Создать SpelParser"""
    return SpelParser()


class TestLiterals:
    """Тесты литералов"""

    def test_number_literal(self, evaluator, parser):
        """Числовой литерал"""
        ast = parser.parse("10")
        result = evaluator.evaluate(ast, {})
        assert result == 10

    def test_string_literal(self, evaluator, parser):
        """Строковый литерал"""
        ast = parser.parse('"hello"')
        result = evaluator.evaluate(ast, {})
        assert result == "hello"

    def test_boolean_true_literal(self, evaluator, parser):
        """Boolean true"""
        ast = parser.parse("true")
        result = evaluator.evaluate(ast, {})
        assert result is True

    def test_boolean_false_literal(self, evaluator, parser):
        """Boolean false"""
        ast = parser.parse("false")
        result = evaluator.evaluate(ast, {})
        assert result is False

    def test_null_literal(self, evaluator, parser):
        """Null литерал"""
        ast = parser.parse("null")
        result = evaluator.evaluate(ast, {})
        assert result is None


class TestFieldAccess:
    """Тесты доступа к полям"""

    def test_simple_field(self, evaluator, parser):
        """Простое поле"""
        ast = parser.parse("fieldName")
        result = evaluator.evaluate(ast, {"fieldName": "value"})
        assert result == "value"

    def test_nested_field(self, evaluator, parser):
        """Вложенное поле"""
        ast = parser.parse("outer.inner")
        result = evaluator.evaluate(ast, {"outer": {"inner": 42}})
        assert result == 42

    def test_missing_field(self, evaluator, parser):
        """Отсутствующее поле"""
        ast = parser.parse("missingField")
        result = evaluator.evaluate(ast, {"otherField": "value"})
        assert result is None

    def test_this_keyword(self, evaluator, parser):
        """Keyword this"""
        ast = parser.parse("this")
        context = EvaluationContext(root_data={"field": "value"}, current_value="current")
        result = evaluator.evaluate(ast, {}, context)
        assert result == "current"


class TestComparison:
    """Тесты операторов сравнения"""

    def test_eq_numbers(self, evaluator, parser):
        """eq: равные числа"""
        ast = parser.parse("eq(field, 10)")
        result = evaluator.evaluate(ast, {"field": 10})
        assert result is True

    def test_eq_strings(self, evaluator, parser):
        """eq: равные строки"""
        ast = parser.parse('eq(field, "hello")')
        result = evaluator.evaluate(ast, {"field": "hello"})
        assert result is True

    def test_eq_different(self, evaluator, parser):
        """eq: разные значения"""
        ast = parser.parse("eq(field, 20)")
        result = evaluator.evaluate(ast, {"field": 10})
        assert result is False

    def test_neq_equal(self, evaluator, parser):
        """noteq: равные значения"""
        ast = parser.parse("noteq(field, 10)")
        result = evaluator.evaluate(ast, {"field": 10})
        assert result is False

    def test_neq_different(self, evaluator, parser):
        """noteq: разные значения"""
        ast = parser.parse("noteq(field, 20)")
        result = evaluator.evaluate(ast, {"field": 10})
        assert result is True


class TestNullChecks:
    """Тесты null-проверок"""

    def test_is_null_with_null(self, evaluator, parser):
        """isNull с null"""
        ast = parser.parse("isNull(field)")
        result = evaluator.evaluate(ast, {"field": None})
        assert result is True

    def test_is_null_with_value(self, evaluator, parser):
        """isNull со значением"""
        ast = parser.parse("isNull(field)")
        result = evaluator.evaluate(ast, {"field": "value"})
        assert result is False

    def test_not_null_with_value(self, evaluator, parser):
        """notNull со значением"""
        ast = parser.parse("notNull(field)")
        result = evaluator.evaluate(ast, {"field": "value"})
        assert result is True

    def test_not_null_with_null(self, evaluator, parser):
        """notNull с null"""
        ast = parser.parse("notNull(field)")
        result = evaluator.evaluate(ast, {"field": None})
        assert result is False

    def test_is_blank_with_empty_string(self, evaluator, parser):
        """isBlank с пустой строкой"""
        ast = parser.parse("isBlank(field)")
        result = evaluator.evaluate(ast, {"field": "   "})
        assert result is True

    def test_is_blank_with_value(self, evaluator, parser):
        """isBlank со значением"""
        ast = parser.parse("isBlank(field)")
        result = evaluator.evaluate(ast, {"field": "hello"})
        assert result is False

    def test_not_blank_with_value(self, evaluator, parser):
        """notBlank со значением"""
        ast = parser.parse("notBlank(field)")
        result = evaluator.evaluate(ast, {"field": "hello"})
        assert result is True

    def test_not_blank_with_empty(self, evaluator, parser):
        """notBlank с пустой строкой"""
        ast = parser.parse("notBlank(field)")
        result = evaluator.evaluate(ast, {"field": "   "})
        assert result is False


class TestLogicalOperators:
    """Тесты логических операторов"""

    def test_and_both_true(self, evaluator, parser):
        """and: оба True"""
        ast = parser.parse("and(eq(field1, 10), eq(field2, 20))")
        result = evaluator.evaluate(ast, {"field1": 10, "field2": 20})
        assert result is True

    def test_and_one_false(self, evaluator, parser):
        """and: один False"""
        ast = parser.parse("and(eq(field1, 10), eq(field2, 30))")
        result = evaluator.evaluate(ast, {"field1": 10, "field2": 20})
        assert result is False

    def test_or_one_true(self, evaluator, parser):
        """or: один True"""
        ast = parser.parse("or(eq(field1, 10), eq(field1, 99))")
        result = evaluator.evaluate(ast, {"field1": 10})
        assert result is True

    def test_or_both_false(self, evaluator, parser):
        """or: оба False"""
        ast = parser.parse("or(eq(field1, 99), eq(field1, 88))")
        result = evaluator.evaluate(ast, {"field1": 10})
        assert result is False

    def test_not_true(self, evaluator, parser):
        """not: True"""
        ast = parser.parse("not(eq(field, 10))")
        result = evaluator.evaluate(ast, {"field": 20})
        assert result is True

    def test_not_false(self, evaluator, parser):
        """not: False"""
        ast = parser.parse("not(eq(field, 10))")
        result = evaluator.evaluate(ast, {"field": 10})
        assert result is False


class TestInOperator:
    """Тесты оператора in"""

    def test_in_list_contains(self, evaluator, parser):
        """in: список содержит значение"""
        ast = parser.parse("in(field, 10, 20, 30)")
        result = evaluator.evaluate(ast, {"field": 20})
        assert result is True

    def test_in_list_not_contains(self, evaluator, parser):
        """in: список не содержит значение"""
        ast = parser.parse("in(field, 10, 20, 30)")
        result = evaluator.evaluate(ast, {"field": 40})
        assert result is False

    def test_notin_list_contains(self, evaluator, parser):
        """notIn: список содержит значение"""
        ast = parser.parse("notin(field, 10, 20, 30)")
        result = evaluator.evaluate(ast, {"field": 20})
        assert result is False

    def test_notin_list_not_contains(self, evaluator, parser):
        """notIn: список не содержит значение"""
        ast = parser.parse("notin(field, 10, 20, 30)")
        result = evaluator.evaluate(ast, {"field": 40})
        assert result is True


class TestComplexExpressions:
    """Тесты сложных выражений"""

    def test_complex_and_chain(self, evaluator, parser):
        """Сложная цепочка and"""
        ast = parser.parse("and(eq(field1, 10), notNull(field2), in(field3, 100, 200))")
        result = evaluator.evaluate(
            ast, {"field1": 10, "field2": "value", "field3": 100}
        )
        assert result is True

    def test_complex_or_chain(self, evaluator, parser):
        """Сложная цепочка or"""
        ast = parser.parse("or(eq(field1, 10), eq(field2, 20), eq(field3, 30))")
        result = evaluator.evaluate(
            ast, {"field1": 99, "field2": 20, "field3": 99}
        )
        assert result is True

    def test_nested_logic(self, evaluator, parser):
        """Вложенная логика"""
        ast = parser.parse("and(or(eq(field1, 10), eq(field1, 20)), notNull(field2))")
        result = evaluator.evaluate(ast, {"field1": 20, "field2": "value"})
        assert result is True


class TestParentNavigation:
    """Тесты навигации parent"""

    def test_parent_simple(self, evaluator, parser):
        """parent: простая навигация"""
        ast = parser.parse("parent.field")
        context = EvaluationContext(
            root_data={},
            current_value=None,
            parent_stack=[{"field": "parent_value"}],
        )
        result = evaluator.evaluate(ast, {}, context)
        assert result == "parent_value"

    def test_parent2_navigation(self, evaluator, parser):
        """parent2: навигация к дедушке"""
        ast = parser.parse("parent2.field")
        # Стек: [-1] = level 1 (immediate parent), [-2] = level 2 (grandparent)
        context = EvaluationContext(
            root_data={},
            current_value=None,
            parent_stack=[
                {"field": "parent2"},  # level 2 (добавлен первым = дальний)
                {"field": "parent1"},  # level 1 (добавлен вторым = ближний)
            ],
        )
        result = evaluator.evaluate(ast, {}, context)
        assert result == "parent2"


class TestRootNavigation:
    """Тесты навигации rootBean"""

    def test_rootbean_navigation(self, evaluator, parser):
        """rootBean: навигация к корню"""
        ast = parser.parse("rootBean.loanRequest.callCdExt")
        data = {"loanRequest": {"callCdExt": "EXT123"}}
        result = evaluator.evaluate(ast, data)
        assert result == "EXT123"
