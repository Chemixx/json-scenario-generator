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

        # Строки (в двойных или одинарных кавычках)
        string_dq = QuotedString('"', escChar="\\")
        string_sq = QuotedString("'", escChar="\\")
        string = (string_dq | string_sq).setParseAction(
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
        # # добавлен для поддержки #this, #root, #parent
        identifier = Word(alphas + "_$#", alphanums + "_$#")

        # Путь к полю: field, parent.field, parent2.field, rootBean.loanRequest.callCdExt
        # Также поддерживает #this.field, #root.field, #parent.field, this.field
        field_path = delimitedList(identifier, delim=".").setParseAction(
            lambda t: self._create_field_node(".".join(t))
        )

        # ========== ФУНКЦИИ ==========

        # Forward declaration для рекурсивной грамматики
        expression = Forward()

        # Аргументы функции
        args = Optional(delimitedList(expression))

        # Вызов функции: functionName(arg1, arg2, ...)
        # Используем ~ (not) для исключения ключевых слов из identifier
        from pyparsing import FollowedBy, NotAny

        # ========== ОПЕРАТОРЫ ==========
        # Используем CaselessKeyword + FollowedBy для работы с notNull( и т.д.

        # NOTNULL - проверка на не-null (ПЕРЕД not!)
        notnull_expr = (
            CaselessKeyword("notnull") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.NOT_NULL, t[1][0]))

        # NOTBLANK - проверка на не-pustую строку (ПЕРЕД not!)
        notblank_expr = (
            CaselessKeyword("notblank") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.NOT_BLANK, t[1][0]))

        # NOTIN - оператор непринадлежности (ПЕРЕД in!)
        notin_expr = (
            CaselessKeyword("notin") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.NOT_IN, t[1]))

        # NOT (унарный) - проверяем ПЕРЕД function_call
        not_expr = (
            CaselessKeyword("not") + FollowedBy("(") + Suppress("(") + expression + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.NOT, t[1]))

        # ISNULL - проверка на null
        isnull_expr = (
            CaselessKeyword("isnull") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.IS_NULL, t[1][0]))

        # ISBLANK - проверка на пустую строку
        isblank_expr = (
            CaselessKeyword("isblank") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.IS_BLANK, t[1][0]))

        # IN - оператор принадлежности
        in_expr = (
            CaselessKeyword("in") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.IN, t[1]))

        # EQ - оператор равенства
        eq_expr = (
            CaselessKeyword("eq") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: BinaryOpNode(NodeType.EQ, t[1][0], t[1][1]))

        # NOTEQ - оператор неравенства
        noteq_expr = (
            CaselessKeyword("noteq") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: BinaryOpNode(NodeType.NOT_EQ, t[1][0], t[1][1]))

        # AND - логическое И
        and_expr = (
            CaselessKeyword("and") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.AND, t[1]))

        # OR - логическое ИЛИ
        or_expr = (
            CaselessKeyword("or") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.OR, t[1]))

        # Исключаем все SpEL операторы и функции из function_name
        reserved = (
            # Логические
            CaselessKeyword("not") | CaselessKeyword("and") | CaselessKeyword("or") | CaselessKeyword("in") |
            # Сравнения
            CaselessKeyword("eq") | CaselessKeyword("noteq") | CaselessKeyword("ne") |
            CaselessKeyword("eqorgreater") | CaselessKeyword("eqorless") |
            CaselessKeyword("gt") | CaselessKeyword("lt") | CaselessKeyword("gte") | CaselessKeyword("lte") |
            # Null-проверки (notnull, notblank BEFORE not!)
            CaselessKeyword("notnull") | CaselessKeyword("notblank") | CaselessKeyword("notin") |
            CaselessKeyword("isnull") | CaselessKeyword("isblank") |
            # Массивы
            CaselessKeyword("anymatch") | CaselessKeyword("allmatch") | CaselessKeyword("nonematch") |
            CaselessKeyword("filter") | CaselessKeyword("map") | CaselessKeyword("hassize") | CaselessKeyword("size") |
            CaselessKeyword("notemptylist") | CaselessKeyword("containsall") |
            # Даты
            CaselessKeyword("currentdate") | CaselessKeyword("tolocaldate") |
            CaselessKeyword("minusyears") | CaselessKeyword("minusdays") |
            CaselessKeyword("isafter") | CaselessKeyword("compareto") |
            # Строки
            CaselessKeyword("length") |
            # Бизнес-функции
            CaselessKeyword("isvalidtaxnum") | CaselessKeyword("isvaliduuid") |
            CaselessKeyword("digitscheck") | CaselessKeyword("isdictionaryvalue") |
            # Вызов методов
            CaselessKeyword("call")
        )
        function_name = ~reserved + identifier
        function_call = (
            function_name + FollowedBy("(") + Suppress("(") + Group(args) + Suppress(")")
        ).setParseAction(self._create_function_node)

        # ========== БАЗОВОЕ ВЫРАЖЕНИЕ (КРИТИЧЕСКИ ВАЖНЫЙ ПОРЯДОК!) ==========

        # Операторы массивов
        anymatch_expr = (
            CaselessKeyword("anymatch") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: AnyMatchNode(t[1][0], t[1][1]))

        allmatch_expr = (
            CaselessKeyword("allmatch") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: AllMatchNode(t[1][0], t[1][1]))

        nonematch_expr = (
            CaselessKeyword("nonematch") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: NoneMatchNode(t[1][0], t[1][1]))

        filter_expr = (
            CaselessKeyword("filter") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: FilterNode(t[1][0], t[1][1]))

        map_expr = (
            CaselessKeyword("map") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: MapNode(t[1][0], t[1][1]))

        hassize_expr = (
            CaselessKeyword("hassize") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: HasSizeNode(t[1][0], t[1][1]))

        size_expr = (
            CaselessKeyword("size") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.SIZE, t[1][0]))

        notemptylist_expr = (
            CaselessKeyword("notemptylist") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.NOT_EMPTY_LIST, t[1][0]))

        containsall_expr = (
            CaselessKeyword("containsall") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: BinaryOpNode(NodeType.CONTAINS_ALL, t[1][0], t[1][1]))

        # Операторы дат
        currentdate_expr = (
            CaselessKeyword("currentdate") + FollowedBy("(") + Suppress("(") + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.CURRENT_DATE, LiteralNode(None)))

        tolocaldate_expr = (
            CaselessKeyword("tolocaldate") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.TO_LOCAL_DATE, t[1][0]))

        minusyears_expr = (
            CaselessKeyword("minusyears") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: CallMethodNode(t[1][0], "minus_years", t[1][1:]))

        minusdays_expr = (
            CaselessKeyword("minusdays") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: CallMethodNode(t[1][0], "minus_days", t[1][1:]))

        isafter_expr = (
            CaselessKeyword("isafter") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: CallMethodNode(t[1][0], "is_after", t[1][1:]))

        compareto_expr = (
            CaselessKeyword("compareto") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression, min=2, max=2)) + Suppress(")")
        ).setParseAction(lambda t: CallMethodNode(t[1][0], "compare_to", t[1][1:]))

        # Операторы строк
        length_expr = (
            CaselessKeyword("length") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.LENGTH, t[1][0]))

        # Бизнес-операторы
        isvalidtaxnum_expr = (
            CaselessKeyword("isvalidtaxnum") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.IS_VALID_TAX_NUM, t[1][0]))

        isvaliduuid_expr = (
            CaselessKeyword("isvaliduuid") + FollowedBy("(") + Suppress("(") + Group(expression) + Suppress(")")
        ).setParseAction(lambda t: UnaryOpNode(NodeType.IS_VALID_UUID, t[1][0]))

        digitscheck_expr = (
            CaselessKeyword("digitscheck") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.DIGITS_CHECK, t[1]))

        isdictionaryvalue_expr = (
            CaselessKeyword("isdictionaryvalue") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: NaryOpNode(NodeType.IS_DICTIONARY_VALUE, t[1]))

        # Вызов методов
        call_expr = (
            CaselessKeyword("call") + FollowedBy("(") + Suppress("(") + Group(delimitedList(expression)) + Suppress(")")
        ).setParseAction(lambda t: self._create_function_node(["call", t[1]]))

        base_expr = (
            # 1. ЛИТЕРАЛЫ ПЕРВЫМИ (чтобы не конфликтовать с полями)
            number
            | string
            | true_literal
            | false_literal
            | null_literal
            # 2. Специальные конструкции (ПЕРЕД function_call!)
            | notnull_expr
            | notblank_expr
            | notin_expr
            | isnull_expr
            | isblank_expr
            | not_expr
            | in_expr
            | eq_expr
            | noteq_expr
            | and_expr
            | or_expr
            | anymatch_expr
            | allmatch_expr
            | nonematch_expr
            | filter_expr
            | map_expr
            | hassize_expr
            | size_expr
            | notemptylist_expr
            | containsall_expr
            | currentdate_expr
            | tolocaldate_expr
            | minusyears_expr
            | minusdays_expr
            | isafter_expr
            | compareto_expr
            | length_expr
            | isvalidtaxnum_expr
            | isvaliduuid_expr
            | digitscheck_expr
            | isdictionaryvalue_expr
            | call_expr
            # 3. Функции (остальные)
            | function_call
            # 4. Поля В КОНЦЕ (catch-all для идентификаторов, включая this, this.field, #this.field)
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

        # Нормализация: убираем # префикс
        normalized_path = path_str.lstrip("#")

        # Проверка parent2, parent3, #parent2, #parent3
        if normalized_path.startswith("parent"):
            # Извлекаем уровень
            parts = normalized_path.split(".", 1)
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

        # Проверка rootBean / #rootBean / root / #root
        elif (
            normalized_path.startswith("rootBean.")
            or normalized_path.startswith("root.")
        ):
            sub_path = normalized_path.split(".", 1)[1]
            return RootNode(sub_path)

        # Проверка this / #this / this.field / #this.field
        elif normalized_path == "this" or normalized_path.startswith("this."):
            return FieldNode(normalized_path)

        # Обычное поле
        else:
            return FieldNode(normalized_path)

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
