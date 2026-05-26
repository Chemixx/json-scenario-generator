"""
Unit-тесты для constraint_utils.
Покрывает: 10 типов проверок ограничений.
"""
import pytest
from decimal import Decimal
from src.utils.constraint_utils import check_constraint


class TestCheckMinLength:
    def test_valid(self):
        assert check_constraint("minLength", 3, "abc") is None

    def test_invalid(self):
        result = check_constraint("minLength", 5, "ab")
        assert result is not None
        assert "minLength" in result

    def test_exact(self):
        assert check_constraint("minLength", 3, "abc") is None


class TestCheckMaxLength:
    def test_valid(self):
        assert check_constraint("maxLength", 5, "abc") is None

    def test_invalid(self):
        result = check_constraint("maxLength", 2, "abc")
        assert result is not None
        assert "maxLength" in result


class TestCheckPattern:
    def test_valid(self):
        assert check_constraint("pattern", r"^\d+$", "123") is None

    def test_invalid(self):
        result = check_constraint("pattern", r"^\d+$", "abc")
        assert result is not None
        assert "pattern" in result


class TestCheckMinimum:
    def test_valid(self):
        assert check_constraint("minimum", 0, 5) is None

    def test_invalid(self):
        result = check_constraint("minimum", 10, 5)
        assert result is not None
        assert "minimum" in result

    def test_decimal(self):
        assert check_constraint("minimum", Decimal("0"), Decimal("100.50")) is None


class TestCheckMaximum:
    def test_valid(self):
        assert check_constraint("maximum", 100, 50) is None

    def test_invalid(self):
        result = check_constraint("maximum", 10, 50)
        assert result is not None
        assert "maximum" in result

    def test_decimal(self):
        result = check_constraint("maximum", Decimal("100"), Decimal("200"))
        assert result is not None


class TestCheckMinItems:
    def test_valid(self):
        assert check_constraint("minItems", 2, [1, 2, 3]) is None

    def test_invalid(self):
        result = check_constraint("minItems", 5, [1, 2])
        assert result is not None
        assert "minItems" in result


class TestCheckMaxItems:
    def test_valid(self):
        assert check_constraint("maxItems", 5, [1, 2, 3]) is None

    def test_invalid(self):
        result = check_constraint("maxItems", 2, [1, 2, 3])
        assert result is not None
        assert "maxItems" in result


class TestCheckEnum:
    def test_valid(self):
        assert check_constraint("enum", ["A", "B", "C"], "A") is None

    def test_invalid(self):
        result = check_constraint("enum", ["A", "B"], "X")
        assert result is not None
        assert "enum" in result

    def test_numeric(self):
        assert check_constraint("enum", [1, 2, 3], 2) is None


class TestCheckMaxIntLength:
    def test_valid(self):
        assert check_constraint("maxIntLength", 5, 12345) is None

    def test_invalid(self):
        result = check_constraint("maxIntLength", 3, 12345)
        assert result is not None
        assert "maxIntLength" in result


class TestCheckMaxFracLength:
    def test_valid(self):
        assert check_constraint("maxFracLength", 2, Decimal("100.50")) is None

    def test_invalid(self):
        result = check_constraint("maxFracLength", 1, Decimal("100.50"))
        assert result is not None
        assert "maxFracLength" in result

    def test_integer_no_fraction(self):
        assert check_constraint("maxFracLength", 0, 100) is None


class TestCheckConstraintUnknown:
    def test_unknown_constraint_returns_none(self):
        assert check_constraint("unknownConstraint", 42, "value") is None