"""
Модели данных для работы со схемами JSON Schema
"""
# noinspection PyUnresolvedReferences
from dataclasses import dataclass, field as dataclass_field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import re

from src.utils.icons import Icon


# ============================================================================
# ENUM: Статус версии контракта
# ============================================================================

class VersionStatus(Enum):
    """
    Статус версии контракта

    Values:
        CURRENT: Актуальная версия в продакшене
        FUTURE: Будущий релиз (планируется)
        DEPRECATING: Выводится из эксплуатации
        DEPRECATED: Выведена из эксплуатации (не используется)
    """
    CURRENT = "Актуально"
    FUTURE = "Будущий релиз"
    DEPRECATING = "Выводится из эксплуатации"
    DEPRECATED = "Выведено из эксплуатации"


# ============================================================================
# DATACLASS: Информация о версии контракта
# ============================================================================

@dataclass
class VersionInfo:
    """
    Информация о версии контракта

    Attributes:
        version: Основная версия (например, "072")
        subversion: Подверсия (например, "04"), опционально
        release_month: Месяц и год релиза (например, "Октябрь 2025")
        status: Статус версии (актуально, будущий релиз, выводится)
        direction: Направление кредитования (например, "КН, КК")
        inclusion_date: Дата включения в продакшн (например, "25.10.2025")
        comment: Дополнительные комментарии
        adapter: Название адаптера (например, "front-adapter", "pa-reactive-adapter")

    Example:
        >>> version = VersionInfo(
        ...     version="072",
        ...     status=VersionStatus.CURRENT,
        ...     direction="КН, КК",
        ...     inclusion_date="30.08.2025"
        ... )
        >>> version.full_version()
        '072'
        >>> version.is_current()
        True
    """
    version: str
    subversion: Optional[str] = None
    release_month: Optional[str] = None
    status: VersionStatus = VersionStatus.CURRENT
    direction: Optional[str] = None
    inclusion_date: Optional[str] = None
    comment: str = ""
    adapter: str = "front-adapter"

    def full_version(self) -> str:
        """
        Возвращает полную версию в формате "072" или "072.04"

        Returns:
            Строка с полной версией
        """
        if self.subversion:
            return f"{self.version}.{self.subversion}"
        return self.version

    def is_current(self) -> bool:
        """Проверка, актуальна ли версия"""
        return self.status == VersionStatus.CURRENT

    def is_future(self) -> bool:
        """Проверка, является ли версия будущим релизом"""
        return self.status == VersionStatus.FUTURE

    def is_deprecated(self) -> bool:
        """Проверка, выводится ли версия из эксплуатации"""
        return self.status in [VersionStatus.DEPRECATING, VersionStatus.DEPRECATED]

    def __str__(self) -> str:
        return f"Version {self.full_version()} ({self.status.value})"

    def __repr__(self) -> str:
        return (
            f"VersionInfo(version='{self.version}', "
            f"subversion={self.subversion}, "
            f"status={self.status.name})"
        )


# ============================================================================
# DATACLASS: Условная обязательность поля (НОВЫЙ КЛАСС)
# ============================================================================

@dataclass
class ConditionalRequirement:
    """
    Условная обязательность поля (аналог ConditionalRequirement.java)

    Представляет условие, при котором поле становится обязательным.
    Используется для полей с типом обязательности "УО" (условно обязательное).

    Attributes:
        expression: SpEL выражение для проверки условия
                   (например, "in(#this.productCd, 10410001, 10410002)")
        message: Человекочитаемое описание условия
                 (автоматически генерируется из expression, если не указано)
        dq_code: Код проверки Data Quality (опционально, для будущего использования)

    Example:
        >>> cond = ConditionalRequirement(
        ...     expression="in(#this.productCd, 10410001, 10410002)",
        ...     message="Продукт PACCREACT или PACLIREACT"
        ... )
        >>> print(cond.message)
        'Продукт PACCREACT или PACLIREACT'

        >>> # Автогенерация message
        >>> cond2 = ConditionalRequirement(
        ...     expression="eq(#root.loanRequest.loanTypeCd, 10340001)"
        ... )
        >>> print(cond2.message)
        'eq(loanRequest.loanTypeCd, 10340001)'
    """
    expression: str
    message: Optional[str] = None
    dq_code: Optional[int] = None

    def __post_init__(self):
        """Автоматически генерировать message если не задано"""
        if not self.message:
            self.message = self._expr_to_message(self.expression)

    @staticmethod
    def _expr_to_message(expression: str) -> str:
        """
        Преобразовать SpEL выражение в человекочитаемое сообщение

        Упрощает техническое SpEL выражение, делая его более понятным:
        - Удаляет префиксы #this., #root., #parent.
        - Заменяет операторы на русские аналоги (&&→И, ||→ИЛИ, !=→НЕ)
        - Убирает L суффикс у чисел (10410001L → 10410001)

        Args:
            expression: Исходное SpEL выражение

        Returns:
            Упрощенное сообщение

        Example:
            >>> ConditionalRequirement._expr_to_message(
            ...     "in(#this.productCd, 10410001L, 10410002L)"
            ... )
            'in(productCd, 10410001, 10410002)'
        """
        message = expression
        message = re.sub(r'#\w+\.', '', message)         # #this. → ""
        message = re.sub(r'(\d+)L', r'\1', message)      # 10410001L → 10410001
        message = message.replace('!=', 'НЕ')
        message = message.replace('!', 'НЕ ')
        message = message.replace('==', '=')
        message = message.replace('&&', 'И')
        message = message.replace('||', 'ИЛИ')
        message = message.replace('?.', '.')
        return message

    def __str__(self) -> str:
        return f"ConditionalRequirement({self.message})"

    def __repr__(self) -> str:
        return (
            f"ConditionalRequirement(expression='{self.expression[:50]}...', "
            f"message='{self.message}')"
        )


# ============================================================================
# DATACLASS: Метаданные поля из JSON Schema
# ============================================================================

@dataclass
class FieldMetadata:
    """
    Метаданные поля из JSON Schema

    Attributes:
        path: Полный путь к полю (например, "customerRequest/creditParameters/productCdExt")
        name: Имя поля (последний сегмент пути)
        field_type: Тип поля ("integer", "string", "object", "array", "boolean", "number")
        is_required: Обязательно ли поле (из блока "required")
        is_conditional: Условно обязательное поле (УО) - есть блок "condition"
        condition: Условие для УО (объект ConditionalRequirement)
        dictionary: Название справочника (например, "PRODUCT_TYPE")
        constraints: Ограничения (minLength, maxLength, minItems, pattern и т.д.)
        description: Описание поля
        properties: Вложенные поля (для объектов)
        items: Метаданные элементов (для массивов)
        format: Формат данных ("date", "date-time", "email" и т.д.)
        default: Значение по умолчанию

        # НОВЫЕ ПОЛЯ (для поддержки ValidationElement логики):
        is_collection: Это массив? (True для type="array")
        children: Список вложенных полей (иерархическая структура)
        precondition: Предусловие для проверки (опционально)

        # DQ коды (опционально, пока не используются):
        always_required_dq_code: DQ код для обязательных полей
        conditional_dq_code: DQ код для УО полей
        dictionary_dq_code: DQ код для справочных значений

    Example:
        >>> field_meta = FieldMetadata(
        ...     path="loanRequest/creditAmt",
        ...     name="creditAmt",
        ...     field_type="integer",
        ...     is_required=True,
        ...     constraints={"maxIntLength": 10}
        ... )
        >>> print(field_meta.is_primitive())
        True
        >>> print(field_meta.get_requirement_status())
        'О'
    """
    path: str
    name: str
    field_type: str
    is_required: bool = False
    is_conditional: bool = False
    condition: Optional[ConditionalRequirement] = None  # ← ИЗМЕНЕНО: было Dict, теперь объект
    dictionary: Optional[str] = None
    constraints: Dict[str, Any] = dataclass_field(default_factory=dict)
    description: str = ""
    properties: Optional[Dict[str, 'FieldMetadata']] = None
    items: Optional['FieldMetadata'] = None
    format: Optional[str] = None
    default: Optional[Any] = None

    # НОВЫЕ ПОЛЯ
    is_collection: bool = False
    children: List['FieldMetadata'] = dataclass_field(default_factory=list)
    precondition: Optional[str] = None

    # DQ коды (опционально, пока не используются активно)
    always_required_dq_code: Optional[int] = None
    conditional_dq_code: Optional[int] = None
    dictionary_dq_code: Optional[int] = None

    def is_primitive(self) -> bool:
        """Проверка, является ли поле примитивным типом"""
        return self.field_type in ["string", "integer", "number", "boolean"]

    def is_complex(self) -> bool:
        """Проверка, является ли поле сложным типом"""
        return self.field_type in ["object", "array"]

    def has_dictionary(self) -> bool:
        """Проверка, использует ли поле справочник"""
        return self.dictionary is not None

    def get_max_length(self) -> Optional[int]:
        """Получить максимальную длину строки"""
        return self.constraints.get("maxLength")

    def get_min_length(self) -> Optional[int]:
        """Получить минимальную длину строки"""
        return self.constraints.get("minLength")

    def get_pattern(self) -> Optional[str]:
        """Получить регулярное выражение для валидации"""
        return self.constraints.get("pattern")

    def get_requirement_status(self) -> str:
        """
        Получить статус обязательности поля

        Returns:
            "О" - обязательное
            "УО" - условно обязательное
            "Н" - необязательное
        """
        if self.is_required:
            return "О"
        elif self.is_conditional:
            return "УО"
        else:
            return "Н"

    def __str__(self) -> str:
        req_status = self.get_requirement_status()
        dict_info = f" [{self.dictionary}]" if self.dictionary else ""
        collection_info = "[]" if self.is_collection else ""
        return f"{self.path}{collection_info} ({self.field_type}, {req_status}){dict_info}"

    def __repr__(self) -> str:
        return (
            f"FieldMetadata(path='{self.path}', "
            f"type='{self.field_type}', "
            f"required={self.is_required}, "
            f"conditional={self.is_conditional}, "
            f"is_collection={self.is_collection})"
        )


# ============================================================================
# DATACLASS: Изменение поля между версиями
# ============================================================================

@dataclass
class FieldChange:
    """
    Изменение поля между версиями

    Attributes:
        path: Путь к полю
        change_type: Тип изменения ("added", "removed", "modified")
        old_meta: Метаданные поля в старой версии (для "removed" и "modified")
        new_meta: Метаданные поля в новой версии (для "added" и "modified")
        changes: Детали изменений (например, {"type": "string → integer"})

    Example:
        >>> change = FieldChange(
        ...     path="loanRequest/newField",
        ...     change_type="added",
        ...     new_meta=FieldMetadata(
        ...         path="loanRequest/newField",
        ...         name="newField",
        ...         field_type="string"
        ...     )
        ... )
        >>> print(change.is_breaking_change())
        False
    """
    path: str
    change_type: str  # "added", "removed", "modified"
    old_meta: Optional[FieldMetadata] = None
    new_meta: Optional[FieldMetadata] = None
    changes: Dict[str, str] = dataclass_field(default_factory=dict)

    def is_breaking_change(self) -> bool:
        """
        Проверка, является ли изменение критичным (breaking change)

        Критичные изменения:
        - Удаление обязательного поля
        - Изменение типа поля
        - Поле стало обязательным (Н → О)

        Returns:
            True, если изменение критичное
        """
        # Удаление обязательного поля
        if self.change_type == "removed" and self.old_meta and self.old_meta.is_required:
            return True

        # Изменение типа поля
        if "type" in self.changes:
            return True

        # Поле стало обязательным
        if "required" in self.changes and "Н → О" in self.changes["required"]:
            return True

        return False

    def get_severity(self) -> str:
        """
        Получить уровень серьезности изменения

        Returns:
            "critical" - критичное изменение
            "warning" - предупреждение
            "info" - информационное
        """
        if self.is_breaking_change():
            return "critical"
        elif self.change_type == "modified":
            return "warning"
        else:
            return "info"

    def __str__(self) -> str:
        if self.change_type == "added":
            return f"{Icon.ADDITION} Добавлено: {self.path}"
        elif self.change_type == "removed":
            return f"{Icon.REMOVAL} Удалено: {self.path}"
        else:
            changes_str = ", ".join(f"{k}: {v}" for k, v in self.changes.items())
            return f"{Icon.MODIFICATION} Изменено: {self.path} ({changes_str})"

    def __repr__(self) -> str:
        return f"FieldChange(path='{self.path}', type='{self.change_type}')"


# ============================================================================
# DATACLASS: Разница между двумя схемами
# ============================================================================

@dataclass
class SchemaDiff:
    """
    Разница между двумя схемами

    Attributes:
        old_version: Старая версия контракта (например, "070")
        new_version: Новая версия контракта (например, "072")
        call: Тип Call'а (например, "Call1")
        adapter: Название адаптера (например, "front-adapter")
        added_fields: Список добавленных полей
        removed_fields: Список удаленных полей
        modified_fields: Список измененных полей
        timestamp: Время создания diff'а

    Example:
        >>> diff = SchemaDiff(
        ...     old_version="070",
        ...     new_version="072",
        ...     call="Call1"
        ... )
        >>> diff.added_fields.append(FieldChange(
        ...     path="loanRequest/newField",
        ...     change_type="added"
        ... ))
        >>> print(diff.total_changes())
        1
    """
    old_version: str
    new_version: str
    call: str
    adapter: str = "front-adapter"
    added_fields: List[FieldChange] = dataclass_field(default_factory=list)
    removed_fields: List[FieldChange] = dataclass_field(default_factory=list)
    modified_fields: List[FieldChange] = dataclass_field(default_factory=list)
    timestamp: datetime = dataclass_field(default_factory=datetime.now)

    def total_changes(self) -> int:
        """Общее количество изменений"""
        return len(self.added_fields) + len(self.removed_fields) + len(self.modified_fields)

    def has_changes(self) -> bool:
        """Проверка наличия изменений"""
        return self.total_changes() > 0

    def has_breaking_changes(self) -> bool:
        """
        Проверка наличия критичных изменений

        Returns:
            True, если есть хотя бы одно критичное изменение
        """
        all_changes = self.added_fields + self.removed_fields + self.modified_fields
        return any(change.is_breaking_change() for change in all_changes)

    def get_breaking_changes(self) -> List[FieldChange]:
        """Получить список критичных изменений"""
        all_changes = self.added_fields + self.removed_fields + self.modified_fields
        return [change for change in all_changes if change.is_breaking_change()]

    def get_statistics(self) -> Dict[str, int]:
        """
        Получить статистику изменений

        Returns:
            Словарь с количеством изменений по типам
        """
        return {
            "added": len(self.added_fields),
            "removed": len(self.removed_fields),
            "modified": len(self.modified_fields),
            "total": self.total_changes(),
            "breaking": len(self.get_breaking_changes()),
        }

    def __str__(self) -> str:
        return (
            f"SchemaDiff({self.call}: v{self.old_version} → v{self.new_version}, "
            f"changes={self.total_changes()})"
        )

    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (
            f"SchemaDiff(old='{self.old_version}', new='{self.new_version}', "
            f"call='{self.call}', added={stats['added']}, "
            f"removed={stats['removed']}, modified={stats['modified']})"
        )
