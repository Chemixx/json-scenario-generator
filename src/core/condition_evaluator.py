"""
ConditionEvaluator — выполнение SpEL AST на JSON-данных.

Поддерживает:
- Литералы: числа, строки, boolean, null
- Поля: this, parent, rootBean, parent2.field
- Логические операторы: and, or, not
- Сравнения: eq, ne (noteq)
- Null-проверки: isNull, notNull, isBlank, notBlank
- Принадлежность: in, notIn
"""

from typing import Any, Dict, List, Optional
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
    NodeType,
)
from src.core.spel_functions import SpelFunctions
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EvaluationContext:
    """
    Контекст выполнения SpEL-выражения.

    Содержит:
    - root_data: корневой JSON-объект
    - current_value: текущее значение (для "this")
    - parent_stack: стек родительских объектов для навигации
    """

    def __init__(
        self,
        root_data: Any,
        current_value: Any = None,
        parent_stack: Optional[List[Any]] = None,
    ):
        self.root_data = root_data
        self.current_value = current_value
        self.parent_stack = parent_stack or []

    def with_current(self, value: Any) -> "EvaluationContext":
        """Создать новый контекст с новым current_value"""
        return EvaluationContext(
            root_data=self.root_data,
            current_value=value,
            parent_stack=self.parent_stack,
        )

    def push_parent(self, parent: Any) -> "EvaluationContext":
        """Добавить родителя в стек"""
        new_stack = self.parent_stack + [parent]
        return EvaluationContext(
            root_data=self.root_data,
            current_value=self.current_value,
            parent_stack=new_stack,
        )


class ConditionEvaluator:
    """
    Выполняет SpEL AST на JSON-данных.

    Example:
        evaluator = ConditionEvaluator()
        ast = SpelParser().parse("and(eq(field, 10), notNull(field2))")
        result = evaluator.evaluate(ast, {"field": 10, "field2": "value"})
        # result = True
    """

    def __init__(self):
        self.spel_functions = SpelFunctions()

    def evaluate(
        self,
        node: ASTNode,
        data: Dict[str, Any],
        context: Optional[EvaluationContext] = None,
    ) -> Any:
        """
        Выполнить AST-узел на данных.

        Args:
            node: AST-узел для выполнения
            data: JSON-данные (корневой объект)
            context: Контекст выполнения (опционально)

        Returns:
            Результат выполнения (boolean, число, строка, etc.)

        Raises:
            ValueError: Если узел не поддерживается
        """
        if context is None:
            context = EvaluationContext(root_data=data)

        try:
            return self._evaluate_node(node, context)
        except Exception as e:
            logger.error(f"Ошибка выполнения {node.node_type.value}: {e}")
            raise

    def _evaluate_node(self, node: ASTNode, context: EvaluationContext) -> Any:
        """Диспетчер по типам узлов"""
        # Порядок важен: более специфичные типы проверяем первыми
        if isinstance(node, LiteralNode):
            return self._evaluate_literal(node, context)
        elif isinstance(node, RootNode):
            # RootNode наследуется от FieldNode, проверяем первым
            return self._evaluate_root(node, context)
        elif isinstance(node, ParentNNode):
            # ParentNNode наследуется от FieldNode, проверяем перед FieldNode
            return self._evaluate_parent_n(node, context)
        elif isinstance(node, FieldNode):
            return self._evaluate_field(node, context)
        elif isinstance(node, UnaryOpNode):
            return self._evaluate_unary(node, context)
        elif isinstance(node, BinaryOpNode):
            return self._evaluate_binary(node, context)
        elif isinstance(node, NaryOpNode):
            return self._evaluate_nary(node, context)
        elif isinstance(node, CallMethodNode):
            return self._evaluate_call(node, context)
        else:
            raise ValueError(f"Неподдерживаемый тип узла: {type(node).__name__}")

    def _evaluate_literal(self, node: LiteralNode, context: EvaluationContext) -> Any:
        """Литерал возвращает своё значение"""
        return node.value

    def _evaluate_parent_n(self, node: ParentNNode, context: EvaluationContext) -> Any:
        """
        Навигация parent2, parent3, parent$N.

        Args:
            node: ParentNNode с level и sub_path
            context: Контекст выполнения

        Returns:
            Значение поля родителя или None
        """
        level = node.level
        sub_path = node.sub_path

        # Стек: [-1] = immediate parent (level 1), [-2] = grandparent (level 2)
        if level > len(context.parent_stack):
            logger.warning(f"parent{level} запрошен, но стек имеет {len(context.parent_stack)} элементов")
            return None

        parent_obj = context.parent_stack[-level]

        # Если есть под-путь, извлекаем из родителя
        if sub_path:
            return self._get_nested_value(parent_obj, sub_path)
        return parent_obj

    def _evaluate_root(self, node: RootNode, context: EvaluationContext) -> Any:
        """
        Навигация rootBean.path.

        Args:
            node: RootNode с sub_path
            context: Контекст выполнения

        Returns:
            Значение поля из корневого объекта
        """
        return self._get_nested_value(context.root_data, node.sub_path)

    def _evaluate_field(self, node: FieldNode, context: EvaluationContext) -> Any:
        """
        Извлечь значение поля из данных.

        Поддерживает:
        - this: текущее значение
        - parent: родительский объект
        - parent2, parent3: навигация к предкам
        - root, rootBean: корневой объект
        - field: обычное поле
        """
        path = node.path

        # this → текущее значение
        if path == "this":
            return context.current_value

        # #this.field → навигация от текущего объекта (родителя)
        if path.startswith("#this.") or path.startswith("this."):
            sub_path = path.lstrip("#").lstrip("this.").lstrip(".")
            # Используем первый родительский объект (так как current_value может быть None)
            if context.parent_stack:
                return self._get_nested_value(context.parent_stack[-1], sub_path)
            return self._get_nested_value(context.root_data, sub_path)

        # parent → первый родитель в стеке
        if path == "parent":
            if not context.parent_stack:
                logger.warning("parent запрошен, но стек пуст")
                return None
            return context.parent_stack[-1]

        # #root.X или root.X → навигация к корню
        if path.startswith("root.") or path.startswith("#root."):
            sub_path = path.lstrip("#").lstrip("root.").lstrip(".")
            return self._get_nested_value(context.root_data, sub_path)

        # #parent.X → навигация к родителю
        if path.startswith("#parent.") or (path.startswith("parent.") and path != "parent"):
            sub_path = path.lstrip("#")
            parts = sub_path.split(".", 1)
            if len(parts) > 1:
                # parent.field → ищем в первом родителе
                if parts[0] == "parent":
                    if not context.parent_stack:
                        logger.warning("parent запрошен, но стек пуст")
                        return None
                    return self._get_nested_value(context.parent_stack[-1], parts[1])

        # Обычное поле — ищем в текущем контексте
        if context.current_value is not None and isinstance(context.current_value, dict):
            return context.current_value.get(path)

        # Если current_value не dict, пробуем искать в root_data
        return self._get_nested_value(context.root_data, path)

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """
        Извлечь вложенное значение по пути.

        Args:
            data: Данные (dict, list, или примитив)
            path: Путь вида "field.subField.array[0].field"

        Returns:
            Значение или None если не найдено
        """
        if data is None:
            return None

        parts = path.split(".")
        current = data

        for part in parts:
            if current is None:
                return None

            # Обработка array[index]
            if "[" in part and part.endswith("]"):
                field_name, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))

                # Сначала получаем поле, если есть
                if field_name and isinstance(current, dict):
                    current = current.get(field_name)
                elif not field_name and isinstance(current, list):
                    pass  #直接使用 current как список
                else:
                    return None

                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _evaluate_unary(self, node: UnaryOpNode, context: EvaluationContext) -> Any:
        """Унарный оператор: not, isNull, notNull, isBlank, notBlank"""
        operand_value = self._evaluate_node(node.operand, context)

        if node.node_type == NodeType.NOT:
            return not operand_value

        elif node.node_type == NodeType.IS_NULL:
            return operand_value is None

        elif node.node_type == NodeType.NOT_NULL:
            return operand_value is not None

        elif node.node_type == NodeType.IS_BLANK:
            if operand_value is None:
                return True
            if isinstance(operand_value, str):
                return operand_value.strip() == ""
            return False

        elif node.node_type == NodeType.NOT_BLANK:
            if operand_value is None:
                return False
            if isinstance(operand_value, str):
                return operand_value.strip() != ""
            return True

        else:
            raise ValueError(f"Неподдерживаемый унарный оператор: {node.node_type.value}")

    def _evaluate_binary(self, node: BinaryOpNode, context: EvaluationContext) -> Any:
        """Бинарный оператор: eq, ne (noteq)"""
        left_value = self._evaluate_node(node.left, context)
        right_value = self._evaluate_node(node.right, context)

        if node.node_type == NodeType.EQ:
            return left_value == right_value

        elif node.node_type == NodeType.NOT_EQ:
            return left_value != right_value

        else:
            raise ValueError(f"Неподдерживаемый бинарный оператор: {node.node_type.value}")

    def _evaluate_nary(self, node: NaryOpNode, context: EvaluationContext) -> Any:
        """N-арный оператор: and, or, in, notIn"""
        if node.node_type == NodeType.AND:
            # Короткое замыкание: False если хотя бы один False
            for operand in node.operands:
                value = self._evaluate_node(operand, context)
                if not value:
                    return False
            return True

        elif node.node_type == NodeType.OR:
            # Короткое замыкание: True если хотя бы один True
            for operand in node.operands:
                value = self._evaluate_node(operand, context)
                if value:
                    return True
            return False

        elif node.node_type == NodeType.IN:
            # in(field, val1, val2, ...) — первый operand это поле
            if len(node.operands) < 2:
                logger.warning(f"in() требует минимум 2 аргумента, получено {len(node.operands)}")
                return False

            field_value = self._evaluate_node(node.operands[0], context)
            allowed_values = [
                self._evaluate_node(operand, context) for operand in node.operands[1:]
            ]
            return field_value in allowed_values

        elif node.node_type == NodeType.NOT_IN:
            if len(node.operands) < 2:
                logger.warning(f"notIn() требует минимум 2 аргумента, получено {len(node.operands)}")
                return True

            field_value = self._evaluate_node(node.operands[0], context)
            allowed_values = [
                self._evaluate_node(operand, context) for operand in node.operands[1:]
            ]
            return field_value not in allowed_values

        else:
            raise ValueError(f"Неподдерживаемый N-арный оператор: {node.node_type.value}")

    def _evaluate_call(self, node: CallMethodNode, context: EvaluationContext) -> Any:
        """
        Вызов метода: call(target, methodName, arg1, arg2, ...)

        Поддерживает методы из SpelFunctions:
        - Dates: current_date, to_local_date, minus_years, minus_days, is_after, compare_to
        - Strings: length
        - Business: is_valid_tax_num, is_valid_uuid, digits_check, is_dictionary_value
        """
        # Оцениваем аргументы
        target_value = self._evaluate_node(node.target, context)
        method_args = [self._evaluate_node(arg, context) for arg in node.arguments]

        method_name = node.method_name.lower()

        # Маппинг методов
        method_map = {
            "currentdate": self.spel_functions.current_date,
            "tolocaldate": self.spel_functions.to_local_date,
            "minusyears": self.spel_functions.minus_years,
            "minusdays": self.spel_functions.minus_days,
            "isafter": self.spel_functions.is_after,
            "compareto": self.spel_functions.compare_to,
            "length": self.spel_functions.length,
            "isvalidtaxnum": self.spel_functions.is_valid_tax_num,
            "isvaliduuid": self.spel_functions.is_valid_uuid,
            "digitscheck": self.spel_functions.digits_check,
            "isdictionaryvalue": self.spel_functions.is_dictionary_value,
        }

        if method_name in method_map:
            method = method_map[method_name]
            try:
                return method(*method_args)
            except Exception as e:
                logger.error(f"Ошибка вызова {method_name}({method_args}): {e}")
                raise

        # Неизвестный метод
        logger.warning(f"Неизвестный метод: {method_name}")
        return None


# Singleton instance
_evaluator_instance: Optional[ConditionEvaluator] = None


def get_condition_evaluator() -> ConditionEvaluator:
    """Получить singleton instance эвалюатора"""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = ConditionEvaluator()
    return _evaluator_instance
