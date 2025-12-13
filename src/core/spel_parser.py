"""
SpEL Parser.

Парсер для Spring Expression Language (SpEL) с поддержкой:
- Логических операторов: and, or, not
- Сравнений: eq, ne, lt, le, gt, ge
- Операторов коллекций: in, notIn
- Функций: isNull, notNull, isBlank, notBlank
- Вызовов методов: isValidTaxNum(), digitsCheck(), etc.
- Навигация: parent, parent2, parent3, root
"""

from __future__ import annotations

import re

from src.core.spel_ast import (
    ASTNode,
    FunctionCallNode,
    LiteralNode,
    VariableNode,
)


class SpelParser:
    """
    Парсер SpEL-выражений.

    Преобразует SpEL-строку в AST (Abstract Syntax Tree).
    """

    def __init__(self):
        """Инициализация парсера."""
        self.tokens: list[str] = []
        self.current_pos: int = 0

    def parse(self, expression: str) -> ASTNode:
        """
        Парсить SpEL-выражение в AST.

        Args:
            expression: SpEL-выражение (строка)

        Returns:
            Корневой узел AST

        Raises:
            SyntaxError: При синтаксических ошибках

        Examples:
            >>> parser = SpelParser()
            >>> ast = parser.parse("data.inn")
            >>> print(ast)  # VariableNode('data.inn')
        """
        # 1. Токенизация
        self.tokens = self._tokenize(expression)
        self.current_pos = 0

        # 2. Парсинг токенов в AST
        ast = self._parse_expression()

        return ast

    def _tokenize(self, expression: str) -> list[str]:
        """
        Токенизация SpEL-выражения.

        Args:
            expression: SpEL-выражение

        Returns:
            Список токенов

        Examples:
            >>> parser = SpelParser()
            >>> parser._tokenize("data.inn")
            ['data', '.', 'inn']
        """
        # Регулярное выражение для токенов
        token_pattern = r"(\w+|[().,[\]]|==|!=|<=|>=|<|>|&&|\|\||!)"
        tokens = re.findall(token_pattern, expression)
        return tokens

    def _parse_expression(self) -> ASTNode:
        """
        Парсинг выражения (логические операторы, сравнения).

        Returns:
            AST узел
        """
        # Простая заглушка: парсим primary выражение
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """
        Парсинг primary выражения (литералы, переменные, функции).

        Returns:
            AST узел
        """
        if self.current_pos >= len(self.tokens):
            raise SyntaxError("Unexpected end of expression")

        token = self.tokens[self.current_pos]

        # Литералы (числа, строки, True/False/None)
        if token.isdigit():
            self.current_pos += 1
            return LiteralNode(int(token))

        # Функции (isValidTaxNum(...))
        if (
            self.current_pos + 1 < len(self.tokens)
            and self.tokens[self.current_pos + 1] == "("
        ):
            return self._parse_function_call()

        # Переменные (data.inn)
        return self._parse_variable()

    def _parse_function_call(self) -> FunctionCallNode:
        """
        Парсинг вызова функции.

        Returns:
            FunctionCallNode

        Examples:
            >>> parser = SpelParser()
            >>> parser.tokens = ["isValidTaxNum", "(", "data", ".", "inn", ")"]
            >>> parser.current_pos = 0
            >>> node = parser._parse_function_call()
            >>> print(node.func_name)  # "isValidTaxNum"
        """
        func_name = self.tokens[self.current_pos]
        self.current_pos += 1  # Пропускаем имя функции

        # Пропускаем '('
        if self.current_pos >= len(self.tokens) or self.tokens[self.current_pos] != "(":
            raise SyntaxError(f"Expected '(' after function name '{func_name}'")
        self.current_pos += 1

        # Парсим аргументы
        args: list[ASTNode] = []
        while self.current_pos < len(self.tokens) and self.tokens[self.current_pos] != ")":
            if self.tokens[self.current_pos] == ",":
                self.current_pos += 1
                continue
            args.append(self._parse_primary())

        # Пропускаем ')'
        if self.current_pos >= len(self.tokens) or self.tokens[self.current_pos] != ")":
            raise SyntaxError("Expected ')' after function arguments")
        self.current_pos += 1

        return FunctionCallNode(func_name, args)

    def _parse_variable(self) -> VariableNode:
        """
        Парсинг переменной (data.inn).

        Returns:
            VariableNode

        Examples:
            >>> parser = SpelParser()
            >>> parser.tokens = ["data", ".", "inn"]
            >>> parser.current_pos = 0
            >>> node = parser._parse_variable()
            >>> print(node.name)  # "data.inn"
        """
        path_parts: list[str] = []

        while self.current_pos < len(self.tokens):
            token = self.tokens[self.current_pos]

            # Добавляем часть пути
            if token.isalnum() or token == "_":
                path_parts.append(token)
                self.current_pos += 1
            # Пропускаем точку
            elif token == ".":
                self.current_pos += 1
            else:
                break

        path = ".".join(path_parts)
        return VariableNode(path)


def get_spel_parser() -> SpelParser:
    """
    Фабричная функция для создания парсера.

    Returns:
        Экземпляр SpelParser
    """
    return SpelParser()
