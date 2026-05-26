"""
SpEL Transpiler.

Транспилятор AST-узлов SpEL в исполняемый Python-код.
Поддерживает:
- Логические операторы: and, or, not
- Сравнения: ==, !=, <, <=, >, >=
- Операторы коллекций: in, not in
- Функции: isNull, notNull, isBlank, notBlank
- Вызовы методов: isValidTaxNum(), digitsCheck(), etc.
- Навигация: parent, parent2, parent3, root
- Фильтры: list.?[condition]
- Проекции: list.![expression]
"""

from __future__ import annotations

from src.core.spel_ast import (
    AllMatchNode,
    AnyMatchNode,
    BinaryOpNode,
    FilterNode,
    FunctionCallNode,
    HasSizeNode,
    LiteralNode,
    MapNode,
    NoneMatchNode,
    UnaryOpNode,
    VariableNode,
)


class SpelTranspiler:
    """
    Транспилятор SpEL AST → Python код.

    Преобразует AST в Python-код для выполнения в runtime.
    """

    def transpile(self, node: object) -> str:
        """
        Транспилировать AST узел в Python код.

        Args:
            node: AST узел для транспиляции

        Returns:
            Python код (строка)

        Raises:
            ValueError: Неподдерживаемый тип узла
        """
        # Диспетчеризация по типу узла
        if isinstance(node, LiteralNode):
            return self._transpile_literal(node)
        elif isinstance(node, VariableNode):
            return self._transpile_variable(node)
        elif isinstance(node, UnaryOpNode):
            return self._transpile_unary_op(node)
        elif isinstance(node, BinaryOpNode):
            return self._transpile_binary_op(node)
        elif isinstance(node, FunctionCallNode):
            return self._transpile_function_call(node)
        elif isinstance(node, FilterNode):
            return self._transpile_filter(node)
        elif isinstance(node, MapNode):
            return self._transpile_map(node)
        elif isinstance(node, AllMatchNode):
            return self._transpile_all_match(node)
        elif isinstance(node, AnyMatchNode):
            return self._transpile_any_match(node)
        elif isinstance(node, NoneMatchNode):
            return self._transpile_none_match(node)
        elif isinstance(node, HasSizeNode):
            return self._transpile_has_size(node)
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

    def _transpile_literal(self, node: LiteralNode) -> str:
        """
        Транспиляция литерала.

        Args:
            node: Узел литерала

        Returns:
            Python представление литерала

        Examples:
            >>> t = SpelTranspiler()
            >>> t._transpile_literal(LiteralNode(42))
            '42'
            >>> t._transpile_literal(LiteralNode("test"))
            "'test'"
        """
        if isinstance(node.value, str):
            return f"'{node.value}'"
        elif node.value is None:
            return "None"
        elif isinstance(node.value, bool):
            return str(node.value)
        else:
            return str(node.value)

    def _transpile_variable(self, node: VariableNode) -> str:
        """
        Транспиляция переменной.

        Args:
            node: Узел переменной (data.inn, parent.field)

        Returns:
            Python код доступа к переменной

        Examples:
            >>> t = SpelTranspiler()
            >>> t._transpile_variable(VariableNode("data.inn"))
            "context.get_value('data.inn')"
        """
        return f"context.get_value('{node.name}')"

    def _transpile_unary_op(self, node: UnaryOpNode) -> str:
        """
        Транспиляция унарной операции (not, !).

        Args:
            node: Узел унарной операции

        Returns:
            Python код

        Examples:
            >>> t = SpelTranspiler()
            >>> var = VariableNode("data.isValid")
            >>> t._transpile_unary_op(UnaryOpNode("not", var))
            "(not context.get_value('data.isValid'))"
        """
        operand_code = self.transpile(node.operand)
        operator_map = {
            "not": "not",
            "!": "not",
        }
        op = operator_map.get(node.operator, node.operator)
        return f"({op} {operand_code})"

    def _transpile_binary_op(self, node: BinaryOpNode) -> str:
        """
        Транспиляция бинарной операции (eq, and, or, lt, etc.).

        Args:
            node: Узел бинарной операции

        Returns:
            Python код

        Examples:
            >>> t = SpelTranspiler()
            >>> left = VariableNode("data.inn")
            >>> right = LiteralNode("123")
            >>> t._transpile_binary_op(BinaryOpNode("eq", left, right))
            "(context.get_value('data.inn') == '123')"
        """
        left_code = self.transpile(node.left)
        right_code = self.transpile(node.right)

        operator_map = {
            "eq": "==",
            "ne": "!=",
            "lt": "<",
            "le": "<=",
            "gt": ">",
            "ge": ">=",
            "and": "and",
            "or": "or",
            "in": "in",
            "notIn": "not in",
        }

        op = operator_map.get(node.operator, node.operator)
        return f"({left_code} {op} {right_code})"

    def _transpile_function_call(self, node: FunctionCallNode) -> str:
        """
        Транспиляция вызова функции (isValidTaxNum(...)).

        Args:
            node: Узел вызова функции

        Returns:
            Python код

        Examples:
            >>> t = SpelTranspiler()
            >>> arg = VariableNode("data.inn")
            >>> t._transpile_function_call(FunctionCallNode("isValidTaxNum", [arg]))
            "isValidTaxNum(context.get_value('data.inn'))"
        """
        args_code = [self.transpile(arg) for arg in node.args]
        args_str = ", ".join(args_code)
        return f"{node.func_name}({args_str})"

    def _transpile_filter(self, node: FilterNode) -> str:
        """
        Транспиляция фильтра коллекции: list.?[condition].

        Args:
            node: Узел фильтра

        Returns:
            Python код list comprehension

        Examples:
            >>> # [x for x in collection if condition]
        """
        collection_code = self.transpile(node.collection)
        condition_code = self.transpile(node.condition)

        # [x for x in {collection} if {condition}]
        return f"[x for x in {collection_code} if {condition_code}]"

    def _transpile_map(self, node: MapNode) -> str:
        """
        Транспиляция проекции коллекции: list.![expression].

        Args:
            node: Узел проекции

        Returns:
            Python код list comprehension

        Examples:
            >>> # [expression(x) for x in collection]
        """
        collection_code = self.transpile(node.collection)
        expression_code = self.transpile(node.expression)

        # [expression for x in collection]
        return f"[{expression_code} for x in {collection_code}]"

    def _transpile_all_match(self, node: AllMatchNode) -> str:
        """
        Транспиляция allMatch: list.allMatch(condition).

        Args:
            node: Узел allMatch

        Returns:
            Python код all(...)

        Examples:
            >>> # all(condition for x in collection)
        """
        collection_code = self.transpile(node.collection)
        condition_code = self.transpile(node.condition)

        return f"all({condition_code} for x in {collection_code})"

    def _transpile_any_match(self, node: AnyMatchNode) -> str:
        """
        Транспиляция anyMatch: list.anyMatch(condition).

        Args:
            node: Узел anyMatch

        Returns:
            Python код any(...)

        Examples:
            >>> # any(condition for x in collection)
        """
        collection_code = self.transpile(node.collection)
        condition_code = self.transpile(node.condition)

        return f"any({condition_code} for x in {collection_code})"

    def _transpile_none_match(self, node: NoneMatchNode) -> str:
        """
        Транспиляция noneMatch: list.noneMatch(condition).

        Args:
            node: Узел noneMatch

        Returns:
            Python код not any(...)

        Examples:
            >>> # not any(condition for x in collection)
        """
        collection_code = self.transpile(node.collection)
        condition_code = self.transpile(node.condition)

        return f"not any({condition_code} for x in {collection_code})"

    def _transpile_has_size(self, node: HasSizeNode) -> str:
        """
        Транспиляция hasSize: list.hasSize(n).

        Args:
            node: Узел hasSize

        Returns:
            Python код len(...) == n

        Examples:
            >>> # len(collection) == size
        """
        collection_code = self.transpile(node.collection)
        size_code = self.transpile(node.size)

        return f"(len({collection_code}) == {size_code})"


def get_spel_transpiler() -> SpelTranspiler:
    """
    Фабричная функция для создания транспилятора.

    Returns:
        Экземпляр SpelTranspiler
    """
    return SpelTranspiler()
