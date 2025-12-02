"""
Ядро приложения - компараторы, валидаторы, генераторы

Модули:
- schema_comparator: Сравнение JSON схем
- (будущее) condition_parser: Парсинг SpEL условий
- (будущее) condition_evaluator: Вычисление SpEL условий
- (будущее) conditional_validator: Валидация условно обязательных полей
"""

from .schema_comparator import SchemaComparator

__all__ = [
    "SchemaComparator",
]
