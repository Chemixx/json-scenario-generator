"""
SpEL-парсер на основе pyparsing.
Преобразует SpEL-строки в AST-деревья.
"""

# Проверка установки pyparsing
try:
    import pyparsing
except ImportError:
    raise ImportError(
        "Пакет 'pyparsing' не установлен. Установите: pip install pyparsing"
    )

from pyparsing import (
    Word,
    Literal,
    alphas,
    alphanums,
    QuotedString,
    CaselessKeyword,
    Forward,
    Group,
    Optional,
    Suppress,
    delimitedList,
    pyparsing_common,
    ParseException,
)
from typing import Any, List, Union

from src.core.spel_ast import (
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
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SpelParser:
    """
    Парсер SpEL-выражений.

    Грамматика:
    expression := logical_expr
    logical_expr := comparison_expr (("and" | "or") comparison_expr)*
    comparison_expr := "not"? function_call | literal | field
    function_call := FUNCTION_NAME "(" args ")"
    args := expression ("," expression)*
    """

    def __init__(self):
        self.parser = self._build_grammar()

    def _build_grammar(self):
        """Построение грамматики pyparsing"""

        # ========== ЛИТЕРАЛЫ ==========

        # Числа
        number = pyparsing_common.number().setParseAction(
            lambda t: LiteralNode(t[0])
        )

        # Строки (в кавычках)
        string = QuotedString('"', escChar="\\").setParseAction(
            lambda t: LiteralNode(t[0])
        )

        # Boolean и Null - ИСПОЛЬЗУЕМ Literal (CASE-SENSITIVE!)
        # Это критично, чтобы не конфликтовать с field_path
        true_literal = (
            Literal("true") | Literal("TRUE") | Literal("True")
        ).setParseAction(lambda t: LiteralNode(True))

        false_literal = (
            Literal("false") | Literal("FALSE") | Literal("False")
        ).setParseAction(lambda t: LiteralNode(False))

        null_literal = (
            Literal("null") | Literal("NULL") | Literal("Null")
        ).setParseAction(lambda t: LiteralNode(None))

        # ========== ПОЛЯ ==========

        # Простой идентификатор (поле)
        identifier = Word(alphas + "_$#", alphanums + "_$")

        # Путь к полю: field, parent.field, parent2.field, rootBean.loanRequest.callCdExt
        field_path = delimitedList(identifier, delim=".").setParseAction(
            lambda t: self._create_field_node(".".join(t))
        )

        # Ключевое слово "this"
        this_keyword = CaselessKeyword("this").setParseAction(
            lambda t: FieldNode("this")
        )

        # ========== ФУНКЦИИ ==========

        # Forward declaration для рекурсивной грамматики
        expression = Forward()

        # Аргументы функции
        args = Optional(delimitedList(expression))

        # Вызов функции: functionName(arg1, arg2, ...)
        function_call = (
            identifier + Suppress("(") + Group(args) + Suppress(")")
        ).setParseAction(self._create_function_node)

        # ========== ОПЕРАТОРЫ ==========

        # NOT (унарный)
        not_expr = (
            CaselessKeyword("not") + Suppress("(") + expression + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.NOT, t[1]))

        # ========== БАЗОВОЕ ВЫРАЖЕНИЕ (КРИТИЧЕСКИ ВАЖНЫЙ ПОРЯДОК!) ==========
        base_expr = (
            # 1. ЛИТЕРАЛЫ ПЕРВЫМИ (чтобы не конфликтовать с полями)
            number
            | string
            | true_literal
            | false_literal
            | null_literal
            # 2. Специальные конструкции
            | not_expr
            | this_keyword
            | function_call
            # 3. Поля В КОНЦЕ (catch-all для идентификаторов)
            | field_path
        )

        # Присваиваем базовое выражение в Forward
        expression <<= base_expr

        return expression

    def _create_field_node(self, path: Union[str, List[str]]) -> FieldNode:
        """
        Создать узел поля с учетом типа (parent, root, this)

        Args:
            path: Путь к полю (строка или список токенов)

        Returns:
            FieldNode, ParentNNode или RootNode
        """
        # Если передан список токенов, объединяем
        if isinstance(path, list):
            path_str = ".".join(path)
        else:
            path_str = path

        # Проверка parent2, parent3
        if path_str.startswith("parent"):
            # Извлекаем уровень
            parts = path_str.split(".", 1)
            parent_part = parts[0]
            sub_path = parts[1] if len(parts) > 1 else None

            if parent_part == "parent":
                level = 1
            elif parent_part.startswith("parent$"):
                level = int(parent_part[7:])  # parent$2 → 2
            elif len(parent_part) > 6 and parent_part[6:].isdigit():
                level = int(parent_part[6:])  # parent2 → 2
            else:
                level = 1

            return ParentNNode(level, sub_path)

        # Проверка rootBean / #rootBean / root
        elif (
            path_str.startswith("rootBean.")
            or path_str.startswith("#rootBean.")
            or path_str.startswith("root.")
        ):
            sub_path = path_str.split(".", 1)[1]
            return RootNode(sub_path)

        # Обычное поле
        else:
            return FieldNode(path_str)

    def _create_function_node(self, tokens: List[Any]) -> ASTNode:
        """
        Создать узел функции на основе имени и аргументов

        Args:
            tokens: [function_name, [arg1, arg2, ...]]

        Returns:
            Соответствующий AST-узел
        """
        func_name = tokens[0].lower()
        args = list(tokens[1]) if len(tokens) > 1 and tokens[1] else []

        # ========== ЛОГИЧЕСКИЕ ==========
        if func_name == "and":
            return NaryOpNode(NodeType.AND, args)
        elif func_name == "or":
            return NaryOpNode(NodeType.OR, args)
        elif func_name == "not":
            if len(args) > 0:
                return UnaryOpNode(NodeType.NOT, args[0])
            else:
                logger.warning("Функция not() без аргументов")
                return UnaryOpNode(NodeType.NOT, LiteralNode(None))

        # ========== СРАВНЕНИЯ ==========
        elif func_name == "eq":
            return BinaryOpNode(NodeType.EQ, args[0], args[1])
        elif func_name == "noteq":
            return BinaryOpNode(NodeType.NOT_EQ, args[0], args[1])
        elif func_name == "in":
            return NaryOpNode(NodeType.IN, args)
        elif func_name == "notin":
            return NaryOpNode(NodeType.NOT_IN, args)
        elif func_name == "eqorgreater":
            return BinaryOpNode(NodeType.EQ_OR_GREATER, args[0], args[1])
        elif func_name == "eqorless":
            return BinaryOpNode(NodeType.EQ_OR_LESS, args[0], args[1])

        # ========== NULL-ПРОВЕРКИ ==========
        elif func_name == "isnull":
            return UnaryOpNode(NodeType.IS_NULL, args[0])
        elif func_name == "notnull":
            return UnaryOpNode(NodeType.NOT_NULL, args[0])
        elif func_name == "isblank":
            return UnaryOpNode(NodeType.IS_BLANK, args[0])
        elif func_name == "notblank":
            return UnaryOpNode(NodeType.NOT_BLANK, args[0])

        # ========== МАССИВЫ ==========
        elif func_name == "anymatch":
            return AnyMatchNode(args[0], args[1])
        elif func_name == "allmatch":
            return AllMatchNode(args[0], args[1])
        elif func_name == "nonematch":
            return NoneMatchNode(args[0], args[1])
        elif func_name == "filter":
            return FilterNode(args[0], args[1])
        elif func_name == "map":
            return MapNode(args[0], args[1])
        elif func_name == "hassize":
            return HasSizeNode(args[0], args[1])
        elif func_name == "size":
            return UnaryOpNode(NodeType.SIZE, args[0])
        elif func_name == "notemptylist":
            return UnaryOpNode(NodeType.NOT_EMPTY_LIST, args[0])
        elif func_name == "containsall":
            return BinaryOpNode(NodeType.CONTAINS_ALL, args[0], args[1])

        # ========== ВЫЗОВ МЕТОДОВ ==========
        elif func_name == "call":
            # call(target, methodName, arg1, arg2, ...)
            if len(args) < 2:
                logger.error(
                    f"call() требует минимум 2 аргумента, получено {len(args)}"
                )
                return CallMethodNode(FieldNode("unknown"), "unknown", [])

            target = args[0]
            method_name = (
                args[1].value if isinstance(args[1], LiteralNode) else str(args[1])
            )
            method_args = args[2:] if len(args) > 2 else []
            return CallMethodNode(target, method_name, method_args)

        # ========== ДАТЫ ==========
        elif func_name == "currentdate":
            return UnaryOpNode(NodeType.CURRENT_DATE, LiteralNode(None))

        # ========== БИЗНЕС-ФУНКЦИИ ==========
        elif func_name == "isvalidtaxnum":
            return UnaryOpNode(NodeType.IS_VALID_TAX_NUM, args[0])
        elif func_name == "isvaliduuid":
            return UnaryOpNode(NodeType.IS_VALID_UUID, args[0])
        elif func_name == "digitscheck":
            # digitsCheck(value, intDigits, fracDigits)
            return NaryOpNode(NodeType.DIGITS_CHECK, args)
        elif func_name == "isdictionaryvalue":
            return NaryOpNode(NodeType.IS_DICTIONARY_VALUE, args)

        # ========== НЕИЗВЕСТНАЯ ФУНКЦИЯ ==========
        else:
            logger.warning(f"Неизвестная функция SpEL: {func_name}")
            # Возвращаем как generic вызов метода
            return CallMethodNode(FieldNode("unknown"), func_name, args)

    def parse(self, spel_expression: str) -> ASTNode:
        """
        Распарсить SpEL-выражение в AST

        Args:
            spel_expression: SpEL-строка (например, "and(eq(field, 10), notNull(field2))")

        Returns:
            Корневой AST-узел

        Raises:
            ParseException: Если выражение некорректно
        """
        try:
            result = self.parser.parseString(spel_expression, parseAll=True)

            # Извлекаем первый элемент
            if len(result) == 0:
                raise ValueError(f"Пустой результат парсинга для '{spel_expression}'")

            parsed_node = result[0]

            # Проверяем, что это действительно ASTNode
            if not isinstance(parsed_node, ASTNode):
                logger.error(
                    f"Неожиданный тип результата парсинга: {type(parsed_node)} "
                    f"для выражения '{spel_expression}'"
                )
                raise TypeError(
                    f"Парсер вернул {type(parsed_node)}, ожидался ASTNode"
                )

            return parsed_node

        except ParseException as e:
            logger.error(f"Ошибка парсинга SpEL '{spel_expression}': {e}")
            raise
        except Exception as e:
            logger.error(
                f"Неожиданная ошибка парсинга SpEL '{spel_expression}': {e}"
            )
            raise


# Singleton instance
_parser_instance = None


def get_spel_parser() -> SpelParser:
    """Получить singleton instance парсера"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SpelParser()
    return _parser_instance
