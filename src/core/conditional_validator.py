"""
ConditionalValidator — валидация условно обязательных полей.

Проверяет поля с is_conditional=True:
- Если SpEL-условие выполнено → поле должно иметь значение
- Если условие не выполнено → поле может быть null

Example:
    validator = ConditionalValidator()
    errors = validator.validate(
        data={"loanRequest": {"creditAmt": 100000}},
        schema_fields={"loanRequest/pledges": field_meta}
    )
    if errors:
        logger.error(f"Валидация не пройдена: {errors}")
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from src.models.schema_models import FieldMetadata, ConditionalRequirement
from src.core.condition_evaluator import ConditionEvaluator, EvaluationContext
from src.core.spel_parser import SpelParser, get_spel_parser
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationError:
    """
    Ошибка валидации условно обязательного поля.

    Содержит полную информацию об ошибке для отчётности и логирования.

    Attributes:
        path: Полный путь к полю (например, "loanRequest/pledges")
        message: Человекочитаемое сообщение об ошибке
        dq_code: Код проверки Data Quality (опционально)
        condition_expression: SpEL-выражение, которое не выполнилось
        actual_value: Фактическое значение поля (обычно None)
        requirement_type: Тип нарушения: "missing" (поле отсутствует) или "null" (поле есть, но null)

    Example:
        >>> error = ValidationError(
        ...     path="loanRequest/pledges",
        ...     message="Залог обязателен для кредита наличными",
        ...     dq_code=12345,
        ...     condition_expression="eq(#root.loanRequest.loanTypeCd, 10340001)",
        ...     actual_value=None
        ... )
        >>> print(error)
        'loanRequest/pledges: Залог обязателен для кредита наличными'
    """
    path: str
    message: str
    dq_code: Optional[int]
    condition_expression: str
    actual_value: Any
    requirement_type: str = "missing"  # "missing" | "null"

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"

    def __repr__(self) -> str:
        return (
            f"ValidationError(path='{self.path}', "
            f"message='{self.message}', "
            f"dq_code={self.dq_code})"
        )


class ConditionalValidator:
    """
    Валидатор условно обязательных полей.

    Проверяет каждое поле с is_conditional=True:
    1. Вычисляет SpEL-условие через ConditionEvaluator
    2. Если условие выполнено (True) и поле null → добавляет ValidationError
    3. Если условие не выполнено (False) → поле может быть null

    Example:
        validator = ConditionalValidator()
        errors = validator.validate(
            data={"loanRequest": {"creditAmt": 100000}},
            schema_fields={"loanRequest/pledges": field_meta}
        )
        if errors:
            logger.error(f"Валидация не пройдена: {errors}")
    """

    def __init__(
        self,
        evaluator: Optional[ConditionEvaluator] = None,
        parser: Optional[SpelParser] = None
    ):
        """
        Инициализировать валидатор.

        Args:
            evaluator: ConditionEvaluator для вычисления SpEL (опционально,
                       создаётся новый если не указан)
            parser: SpelParser для парсинга выражений (опционально,
                    создаётся новый если не указан)
        """
        self.evaluator = evaluator or ConditionEvaluator()
        self.parser = parser or get_spel_parser()

    def validate(
        self,
        data: Dict[str, Any],
        schema_fields: Dict[str, FieldMetadata]
    ) -> List[ValidationError]:
        """
        Проверить условно обязательные поля в данных.

        Для каждого поля с is_conditional=True:
        1. Вычисляет SpEL-условие
        2. Если условие выполнено и поле null → ValidationError

        Args:
            data: JSON-данные для валидации
            schema_fields: Словарь {path: FieldMetadata} полей схемы

        Returns:
            Список ошибок валидации (пустой список если всё ок)

        Example:
            >>> validator = ConditionalValidator()
            >>> errors = validator.validate(
            ...     data={"loanRequest": {"creditAmt": 100000}},
            ...     schema_fields={"loanRequest/pledges": field_meta}
            ... )
            >>> len(errors)
            0
        """
        errors: List[ValidationError] = []

        if not data or not schema_fields:
            logger.debug("Пустые данные или схема — пропускаем валидацию")
            return errors

        for path, field_meta in schema_fields.items():
            # Пропускаем не УО поля
            if not field_meta.is_conditional:
                continue

            condition = field_meta.condition
            if condition is None:
                logger.warning(f"Поле {path} помечено как УО, но condition=None")
                continue

            # Вычисляем SpEL-условие
            try:
                # Парсим SpEL-выражение в AST
                ast = self.parser.parse(condition.expression)
                context = self._build_context(path, data)
                condition_met = self.evaluator.evaluate(
                    ast,
                    data,
                    context
                )
            except Exception as e:
                logger.error(f"Ошибка вычисления условия для {path}: {e}")
                # Пропускаем поле с ошибкой вычисления
                continue

            # Если условие выполнено → поле должно быть не null
            if condition_met:
                actual_value = self._get_value_by_path(data, path)
                if actual_value is None:
                    requirement_type = "null" if self._path_exists(data, path) else "missing"
                    error = ValidationError(
                        path=path,
                        message=condition.message or condition.expression,
                        dq_code=condition.dq_code,
                        condition_expression=condition.expression,
                        actual_value=actual_value,
                        requirement_type=requirement_type
                    )
                    errors.append(error)
                    logger.debug(f"УО поле {path} не заполнено ({requirement_type}): {condition.message}")

        if errors:
            logger.warning(f"Найдено {len(errors)} ошибок валидации УО полей")

        return errors

    def _build_context(self, path: str, data: Dict[str, Any]) -> EvaluationContext:
        """
        Построить контекст выполнения для SpEL-выражения.

        Контекст содержит:
        - root_data: корневой JSON-объект
        - current_value: текущее значение (поле по пути)
        - parent_stack: стек родительских объектов

        Args:
            path: Путь к полю (например, "loanRequest/pledges")
            data: Корневой JSON-объект

        Returns:
            EvaluationContext с настроенной навигацией
        """
        # Извлекаем текущее значение по пути
        current_value = self._get_value_by_path(data, path)

        # Строим стек родителей
        parent_stack = self._build_parent_stack(path, data)

        return EvaluationContext(
            root_data=data,
            current_value=current_value,
            parent_stack=parent_stack
        )

    def _build_parent_stack(self, path: str, data: Dict[str, Any]) -> List[Any]:
        """
        Построить стек родительских объектов для навигации #parent, #parent2.

        Args:
            path: Путь к полю (например, "loanRequest/pledges/type")
            data: Корневой JSON-объект

        Returns:
            Список родительских объектов [level1, level2, ...]
        """
        parts = path.split("/")
        parents = []
        current = data

        for i, part in enumerate(parts):
            # Обработка array-индексов: items[0] → items + индекс
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))

                if isinstance(current, dict) and key in current:
                    current = current[key]
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        break
                else:
                    break

                # Добавляем элемент массива в стек если это не последний элемент
                if i < len(parts) - 1:
                    parents.append(current)
            elif isinstance(current, dict) and part in current:
                current = current[part]
                # Добавляем в стек только если это не последний элемент
                if i < len(parts) - 1:
                    parents.append(current)
            else:
                break

        return parents

    def _path_exists(self, data: Dict[str, Any], path: str) -> bool:
        """
        Проверяет наличие ключа по пути (отличает missing от null).

        В отличие от _get_value_by_path, который возвращает None и для
        отсутствующего ключа, и для ключа со значением None, данный метод
        возвращает True только если ключ существует в данных (даже если
        его значение равно None).

        Args:
            data: JSON-данные
            path: Путь к полю (например, "loanRequest/pledges")

        Returns:
            True если ключ существует, False если отсутствует
        """
        if not path:
            return False
        parts = path.split("/")
        current = data
        for part in parts:
            if current is None or not isinstance(current, dict):
                return False
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))
                if key not in current:
                    return False
                current = current[key]
                if not isinstance(current, list) or index >= len(current):
                    return False
                current = current[index]
            else:
                if part not in current:
                    return False
                current = current[part]
        return True

    def _get_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """
        Извлечь значение по пути из данных.

        Поддерживает:
        - Простые пути: "fieldName"
        - Вложенные пути: "outer/inner/field"
        - Array-индексы: "items[0]/field"

        Args:
            data: JSON-данные
            path: Путь к полю

        Returns:
            Значение поля или None если не найдено

        Example:
            >>> data = {"loanRequest": {"items": [{"value": 42}]}}
            >>> _get_value_by_path(data, "loanRequest/items[0]/value")
            42
        """
        if not path:
            return None

        parts = path.split("/")
        current = data

        for part in parts:
            if current is None:
                return None

            # Обработка array-индексов: items[0]
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))

                if isinstance(current, dict) and key in current:
                    current = current[key]
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


# Singleton instance
_validator_instance: Optional[ConditionalValidator] = None


def get_conditional_validator(evaluator: Optional[ConditionEvaluator] = None) -> ConditionalValidator:
    """
    Получить singleton instance ConditionalValidator.

    Args:
        evaluator: ConditionEvaluator для вычисления SpEL (опционально,
                   используется только при первом создании)

    Returns:
        Singleton instance ConditionalValidator

    Example:
        >>> validator = get_conditional_validator()
        >>> errors = validator.validate(data, schema_fields)
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ConditionalValidator(evaluator)
    return _validator_instance
