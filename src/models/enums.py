"""
Перечисления для классификации изменений в JSON Schema

Этот модуль содержит enum'ы для правильной классификации изменений между версиями схем.
Разделяет ТРИ ортогональные концепции:
1. ChangeType — ЧТО произошло с полем (добавление/удаление/модификация)
2. BreakingLevel — ЛОМАЕТ ли изменение обратную совместимость API
3. ImpactLevel — Насколько КРИТИЧНО изменение для бизнес-логики
4. FieldElementType — КАКОЙ тип элемента схемы (атрибут/массив/объект)
"""

from enum import Enum


class ChangeType(Enum):
    """
    Тип изменения поля в схеме

    Отвечает на вопрос: ЧТО произошло с полем?

    Examples:
        >>> change = AnalyzedChange(change_type=ChangeType.ADDITION, ...)
        >>> if change.change_type == ChangeType.MODIFICATION:
        ...     print("Поле было изменено")
    """
    ADDITION = "addition"  # Поле добавлено
    REMOVAL = "removal"  # Поле удалено
    MODIFICATION = "modification"  # Поле модифицировано

    def to_russian(self) -> str:
        """Русское название типа изменения"""
        mapping = {
            ChangeType.ADDITION: "Добавление",
            ChangeType.REMOVAL: "Удаление",
            ChangeType.MODIFICATION: "Модификация"
        }
        return mapping[self]


class BreakingLevel(Enum):
    """
    Уровень нарушения обратной совместимости

    Отвечает на вопрос: ЛОМАЕТ ли изменение обратную совместимость API?

    Breaking Change — изменение, которое может привести к ошибкам в существующих клиентах.

    Примеры Breaking Changes:
    - Добавление обязательного поля
    - Удаление поля
    - Изменение типа поля
    - Ужесточение ограничений (maxLength уменьшился)
    - Поле стало условно обязательным (Н → УО)

    Примеры Non-Breaking Changes:
    - Добавление опционального поля
    - Смягчение ограничений (maxLength увеличился)
    - Поле стало опциональным (О → Н)

    Examples:
        >>> if change.breaking_level == BreakingLevel.BREAKING:
        ...     print("⚠️ Требуется обновление клиентов!")
    """
    BREAKING = "breaking"  # Ломает обратную совместимость
    NON_BREAKING = "non_breaking"  # Не ломает обратную совместимость

    def to_russian(self) -> str:
        """Русское название уровня"""
        mapping = {
            BreakingLevel.BREAKING: "Breaking",
            BreakingLevel.NON_BREAKING: "Non-Breaking"
        }
        return mapping[self]

    def to_emoji(self) -> str:
        """Эмодзи-индикатор"""
        mapping = {
            BreakingLevel.BREAKING: "⚠️",
            BreakingLevel.NON_BREAKING: "✅"
        }
        return mapping[self]

    def to_icon(self) -> str:
        """ASCII-иконка (безопасна для cp1251)"""
        mapping = {
            BreakingLevel.BREAKING: "[WARN]",
            BreakingLevel.NON_BREAKING: "[OK]"
        }
        return mapping[self]


class ImpactLevel(Enum):
    """
    Уровень влияния изменения на систему

    Отвечает на вопрос: Насколько КРИТИЧНО изменение?

    Используется для приоритизации работы по актуализации.
    Независим от BreakingLevel (breaking change может быть LOW impact, если редкое поле).

    Уровни влияния:
    - CRITICAL: Требует немедленных действий (изменение типа обязательного поля, удаление О поля)
    - HIGH: Высокий приоритет (поле стало УО, добавлено О поле)
    - MEDIUM: Средний приоритет (изменение constraints, поле стало Н)
    - LOW: Низкий приоритет (добавлено опциональное поле, смягчены ограничения)

    Examples:
        >>> if change.impact_level == ImpactLevel.CRITICAL:
        ...     send_alert_to_team()
    """
    CRITICAL = "critical"  # 🔴 Немедленные действия
    HIGH = "high"  # 🟠 Высокий приоритет
    MEDIUM = "medium"  # 🟡 Средний приоритет
    LOW = "low"  # 🟢 Низкий приоритет

    def to_russian(self) -> str:
        """Русское название уровня влияния"""
        mapping = {
            ImpactLevel.CRITICAL: "Критическое",
            ImpactLevel.HIGH: "Высокое влияние",
            ImpactLevel.MEDIUM: "Среднее влияние",
            ImpactLevel.LOW: "Низкое влияние"
        }
        return mapping[self]

    def to_emoji(self) -> str:
        """Эмодзи-индикатор уровня влияния"""
        mapping = {
            ImpactLevel.CRITICAL: "🔴",
            ImpactLevel.HIGH: "🟠",
            ImpactLevel.MEDIUM: "🟡",
            ImpactLevel.LOW: "🟢"
        }
        return mapping[self]

    def to_icon(self) -> str:
        """ASCII-иконка (безопасна для cp1251)"""
        mapping = {
            ImpactLevel.CRITICAL: "[!!!]",
            ImpactLevel.HIGH: "[!!]",
            ImpactLevel.MEDIUM: "[!]",
            ImpactLevel.LOW: "[.]"
        }
        return mapping[self]

    def to_priority(self) -> int:
        """Числовой приоритет (для сортировки)"""
        mapping = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.HIGH: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 3
        }
        return mapping[self]


class FieldElementType(Enum):
    """
    Тип элемента в JSON Schema

    Отвечает на вопрос: КАКОЙ тип элемента схемы?

    Используется для более понятного отображения в отчетах.
    Например:
    - "Атрибут стал условно обязательным" (а не "поле")
    - "Изменилось условие для объекта" (а не "поле")

    Examples:
        >>> meta = FieldMetadata(field_type="array", ...)
        >>> meta.element_type  # автоматически определяется
        FieldElementType.ARRAY
    """
    ATTRIBUTE = "атрибут"  # Простое поле (string, integer, number, boolean, null)
    ARRAY = "массив"  # Массив элементов
    OBJECT = "объект"  # Объект с вложенными свойствами

    def to_russian(self) -> str:
        """Русское название типа элемента (уже в value)"""
        return self.value

    def to_russian_genitive(self) -> str:
        """Родительный падеж для фраз типа "для условно обязательного [объекта]" """
        mapping = {
            FieldElementType.ATTRIBUTE: "атрибута",
            FieldElementType.ARRAY: "массива",
            FieldElementType.OBJECT: "объекта"
        }
        return mapping[self]


# Алиасы для обратной совместимости (если где-то использовались строки)
CHANGE_TYPE_ADDITION = ChangeType.ADDITION
CHANGE_TYPE_REMOVAL = ChangeType.REMOVAL
CHANGE_TYPE_MODIFICATION = ChangeType.MODIFICATION

BREAKING = BreakingLevel.BREAKING
NON_BREAKING = BreakingLevel.NON_BREAKING

CRITICAL = ImpactLevel.CRITICAL
HIGH = ImpactLevel.HIGH
MEDIUM = ImpactLevel.MEDIUM
LOW = ImpactLevel.LOW
