"""
SpEL Evaluation Context: управление контекстом для SpEL-выражений.
Поддерживает иерархию parent/parent2/parent3 для навигации по вложенным структурам.
"""

from __future__ import annotations

from typing import Dict, Any, List, TypedDict, NotRequired
from dataclasses import dataclass, field


# ===== TypedDict для типизации контекста eval() =====

class EvaluationContextDict(TypedDict):
    """
    Типизированный словарь для контекста eval().

    Содержит переменные, доступные в SpEL-выражениях при выполнении:
    - data: текущий объект данных (обязательно)
    - root: корневой объект (обязательно)
    - parent: родитель уровня 1 (опционально)
    - parent2: родитель уровня 2 (опционально)
    - parent3: родитель уровня 3 (опционально)

    Example:
        >>> context_dict: EvaluationContextDict = {
        ...     "data": {"field": "value"},
        ...     "root": {"loanRequest": {"callCd": 1}},
        ...     "parent": {"pledges": [...]}
        ... }
    """
    data: Dict[str, Any]
    root: Dict[str, Any]
    parent: NotRequired[Dict[str, Any]]
    parent2: NotRequired[Dict[str, Any]]
    parent3: NotRequired[Dict[str, Any]]


# ===== Основной класс контекста =====

@dataclass
class SpelContext:
    """
    Контекст выполнения SpEL-выражений.

    Управляет:
    - Текущими данными (data)
    - Корневым объектом (root)
    - Стеком родительских объектов (parent, parent2, parent3)

    Attributes:
        data: Текущий объект данных
        root: Корневой объект (всегда доступен)
        parent_stack: Стек родительских объектов для навигации

    Example:
        >>> from src.core.spel_context import SpelContext
        >>> context = SpelContext(
        ...     data={"field": "value"},
        ...     root={"loanRequest": {"callCd": 1}}
        ... )
        >>> context.data
        {'field': 'value'}
        >>> context.root
        {'loanRequest': {'callCd': 1}}
    """

    data: Dict[str, Any]
    root: Dict[str, Any] | None = None
    parent_stack: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Инициализация после создания dataclass"""
        if self.root is None:
            self.root = self.data

    def push_parent(self, parent_obj: Dict[str, Any]) -> None:
        """
        Добавить новый уровень в стек родителей.

        Используется при входе в вложенную структуру (массив, объект).

        Args:
            parent_obj: Родительский объект

        Example:
            >>> context = SpelContext(data={})
            >>> context.push_parent({"pledges": [...]})
            >>> context.get_parent()  # → {"pledges": [...]}
        """
        self.parent_stack.append(parent_obj)

    def pop_parent(self) -> Dict[str, Any] | None:
        """
        Удалить последний уровень из стека родителей.

        Используется при выходе из вложенной структуры.

        Returns:
            Удаленный родительский объект или None

        Example:
            >>> context = SpelContext(data={})
            >>> context.push_parent({"pledges": [...]})
            >>> removed = context.pop_parent()
            >>> removed
            {'pledges': [...]}
        """
        if self.parent_stack:
            return self.parent_stack.pop()
        return None

    def get_parent(self, level: int = 1) -> Dict[str, Any] | None:
        """
        Получить родительский объект на заданном уровне.

        Args:
            level: Уровень родителя (1 = parent, 2 = parent2, 3 = parent3)

        Returns:
            Родительский объект или None, если уровень недоступен

        Example:
            >>> context = SpelContext(data={})
            >>> context.push_parent({"level1": 1})
            >>> context.push_parent({"level2": 2})
            >>> context.push_parent({"level3": 3})
            >>>
            >>> context.get_parent(1)  # → {"level3": 3} (последний)
            >>> context.get_parent(2)  # → {"level2": 2}
            >>> context.get_parent(3)  # → {"level1": 1}
        """
        if level < 1 or level > len(self.parent_stack):
            return None

        # parent = -1, parent2 = -2, parent3 = -3
        return self.parent_stack[-level]

    def to_eval_context(self) -> EvaluationContextDict:
        """
        Преобразовать контекст в словарь для eval().

        Создает типизированный словарь с переменными:
        - data: текущие данные
        - root: корневой объект
        - parent: родитель уровня 1 (если есть)
        - parent2: родитель уровня 2 (если есть)
        - parent3: родитель уровня 3 (если есть)

        Returns:
            Типизированный словарь для передачи в eval()

        Example:
            >>> context = SpelContext(
            ...     data={"field": "value"},
            ...     root={"loanRequest": {"callCd": 1}}
            ... )
            >>> context.push_parent({"pledges": [...]})
            >>> eval_ctx = context.to_eval_context()
            >>> eval_ctx.keys()
            dict_keys(['data', 'root', 'parent'])
        """
        eval_context: EvaluationContextDict = {
            "data": self.data,
            "root": self.root,  # type: ignore[typeddict-item]
        }

        # Добавить parent/parent2/parent3
        parent = self.get_parent(1)
        if parent is not None:
            eval_context["parent"] = parent

        parent2 = self.get_parent(2)
        if parent2 is not None:
            eval_context["parent2"] = parent2

        parent3 = self.get_parent(3)
        if parent3 is not None:
            eval_context["parent3"] = parent3

        return eval_context

    def create_child_context(
        self,
        new_data: Dict[str, Any],
        preserve_parent_stack: bool = True
    ) -> SpelContext:
        """
        Создать дочерний контекст с новыми данными.

        Используется при итерации по массивам или обработке вложенных объектов.

        Args:
            new_data: Новые данные для контекста
            preserve_parent_stack: Сохранить стек родителей (default: True)

        Returns:
            Новый экземпляр SpelContext

        Example:
            >>> context = SpelContext(data={"field": "value"}, root={"root": 1})
            >>> context.push_parent({"parent_field": "parent_value"})
            >>>
            >>> child = context.create_child_context({"item": "new"})
            >>> child.data
            {'item': 'new'}
            >>> child.root
            {'root': 1}
            >>> child.get_parent(1)
            {'parent_field': 'parent_value'}
        """
        new_stack = self.parent_stack.copy() if preserve_parent_stack else []

        return SpelContext(
            data=new_data,
            root=self.root,
            parent_stack=new_stack
        )


# ===== Утилиты =====

def create_context(
    data: Dict[str, Any],
    root: Dict[str, Any] | None = None,
    parent: Dict[str, Any] | None = None
) -> SpelContext:
    """
    Создать контекст с начальным родителем.

    Args:
        data: Текущие данные
        root: Корневой объект (если None, используется data)
        parent: Начальный родитель (опционально)

    Returns:
        Экземпляр SpelContext

    Example:
        >>> context = create_context(
        ...     data={"field": "value"},
        ...     root={"loanRequest": {"callCd": 1}},
        ...     parent={"pledges": [...]}
        ... )
        >>> context.get_parent(1)
        {'pledges': [...]}
    """
    context = SpelContext(data=data, root=root)

    if parent is not None:
        context.push_parent(parent)

    return context
