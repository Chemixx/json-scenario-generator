"""
Компаратор JSON схем для выявления изменений между версиями
"""
from typing import Dict, List, Any
import re

from ..models import FieldMetadata, SchemaDiff, FieldChange
from ..utils import get_logger
from ..utils.icons import Icon

logger = get_logger(__name__)


class SchemaComparator:
    """
    Компаратор JSON схем

    Ответственность:
    - Сравнение двух распарсенных схем (словари FieldMetadata)
    - Выявление добавленных/удаленных/измененных полей
    - Генерация объекта SchemaDiff с детальным описанием изменений

    Отделен от SchemaParser для соблюдения Single Responsibility Principle:
    - SchemaParser отвечает только за парсинг JSON Schema
    - SchemaComparator отвечает только за сравнение схем

    Example:
        >>> from src.parsers import SchemaParser
        >>> from src.core import SchemaComparator
        >>>
        >>> parser = SchemaParser()
        >>> old_schema = parser.load_schema("v070.json")
        >>> new_schema = parser.load_schema("v072.json")
        >>>
        >>> comparator = SchemaComparator()
        >>> diff = comparator.compare(
        ...     old_schema, new_schema,
        ...     old_version="070", new_version="072", call="Call1"
        ... )
        >>>
        >>> print(f"Изменений: {diff.total_changes()}")
        >>> print(f"Критичных: {len(diff.get_breaking_changes())}")
    """

    def compare(
            self,
            old_schema: Dict[str, FieldMetadata],
            new_schema: Dict[str, FieldMetadata],
            old_version: str = "",
            new_version: str = "",
            call: str = "",
            adapter: str = "front-adapter",
            old_name: str = "",
            new_name: str = ""
    ) -> SchemaDiff:
        """
        Сравнить две распарсенные схемы

        Args:
            old_schema: Словарь метаданных полей старой схемы {путь: FieldMetadata}
            new_schema: Словарь метаданных полей новой схемы {путь: FieldMetadata}
            old_version: Версия старой схемы (например, "070")
            new_version: Версия новой схемы (например, "072")
            call: Тип Call'а (например, "Call1")
            adapter: Название адаптера (по умолчанию "front-adapter")
            old_name: Имя файла старой схемы (например, "V72Call1Rq.json")
            new_name: Имя файла новой схемы (например, "V73Call1Rq.json")

        Returns:
            Объект SchemaDiff с описанием всех изменений

        Example:
            >>> comparator = SchemaComparator()
            >>> diff = comparator.compare(
            ...     old_schema={"field1": FieldMetadata(...)},
            ...     new_schema={"field1": FieldMetadata(...), "field2": FieldMetadata(...)},
            ...     old_version="070",
            ...     new_version="072",
            ...     old_name="V72Call1Rq.json",
            ...     new_name="V73Call1Rq.json"
            ... )
            >>> print(diff.total_changes())  # 1 (добавлено field2)
        """
        # Используем имена файлов, если они переданы, иначе версии
        old_label = old_name if old_name else old_version
        new_label = new_name if new_name else new_version
        
        logger.info(f"{Icon.MODIFICATION} Сравнение схем: {old_label} → {new_label}")

        all_paths = set(old_schema.keys()) | set(new_schema.keys())

        added_fields = []
        removed_fields = []
        modified_fields = []

        for path in all_paths:
            old_field = old_schema.get(path)
            new_field = new_schema.get(path)

            if old_field is None:
                # Поле добавлено
                added_fields.append(FieldChange(
                    path=path,
                    change_type="added",
                    old_meta=None,
                    new_meta=new_field
                ))
            elif new_field is None:
                # Поле удалено
                removed_fields.append(FieldChange(
                    path=path,
                    change_type="removed",
                    old_meta=old_field,
                    new_meta=None
                ))
            elif self._fields_differ(old_field, new_field):
                # Поле изменено
                changes = self._detect_field_changes(old_field, new_field)
                modified_fields.append(FieldChange(
                    path=path,
                    change_type="modified",
                    old_meta=old_field,
                    new_meta=new_field,
                    changes=changes
                ))

        logger.info(
            f"{Icon.STAT} Изменения: +{len(added_fields)} полей, "
            f"-{len(removed_fields)} полей, ~{len(modified_fields)} изменений"
        )

        return SchemaDiff(
            old_version=old_version,
            new_version=new_version,
            call=call,
            adapter=adapter,
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields
        )

    def _fields_differ(self, old_field: FieldMetadata, new_field: FieldMetadata) -> bool:
        """
        Проверить, отличаются ли поля

        Args:
            old_field: Старое поле
            new_field: Новое поле

        Returns:
            True если поля отличаются, False если идентичны
        """
        # Сравниваем ключевые атрибуты
        if old_field.field_type != new_field.field_type:
            return True

        if old_field.is_required != new_field.is_required:
            return True

        if old_field.is_conditional != new_field.is_conditional:
            return True

        # Сравниваем условия
        old_cond_expr = old_field.condition.expression if old_field.condition else None
        new_cond_expr = new_field.condition.expression if new_field.condition else None
        if old_cond_expr != new_cond_expr:
            return True

        if old_field.dictionary != new_field.dictionary:
            return True

        if old_field.constraints != new_field.constraints:
            return True

        if old_field.format != new_field.format:
            return True

        if old_field.default != new_field.default:
            return True

        return False

    def _detect_field_changes(
            self,
            old_field: FieldMetadata,
            new_field: FieldMetadata
    ) -> Dict[str, str]:
        """
        Определить конкретные изменения в поле

        Args:
            old_field: Старое поле
            new_field: Новое поле

        Returns:
            Словарь с описанием изменений {тип_изменения: описание}

        Example:
            >>> changes = comparator._detect_field_changes(old_field, new_field)
            >>> print(changes)
            {'type': 'string → integer', 'required': 'Поле стало обязательным'}
        """
        changes = {}

        # Изменение типа
        if old_field.field_type != new_field.field_type:
            changes["type"] = f"Тип поля изменился: {old_field.field_type} → {new_field.field_type}"

        # Изменение обязательности
        if old_field.is_required != new_field.is_required:
            if new_field.is_required:
                changes["required"] = "Поле стало обязательным (Н → О)"
            else:
                changes["required"] = "Поле стало опциональным (О → Н)"

        # Изменение условной обязательности
        if old_field.is_conditional != new_field.is_conditional:
            if new_field.is_conditional:
                changes["conditional"] = "Поле стало условно обязательным (УО)"
            else:
                changes["conditional"] = "Поле перестало быть условно обязательным"

        # Изменение самого условия
        old_cond_expr = old_field.condition.expression if old_field.condition else ""
        new_cond_expr = new_field.condition.expression if new_field.condition else ""

        if old_cond_expr != new_cond_expr:
            changes["condition"] = self._describe_condition_change(old_cond_expr, new_cond_expr)

        # Изменение справочника
        if old_field.dictionary != new_field.dictionary:
            changes["dictionary"] = (
                f"Справочник изменился: '{old_field.dictionary}' → '{new_field.dictionary}'"
            )

        # Изменение ограничений
        if old_field.constraints != new_field.constraints:
            constraint_desc = self._analyze_constraint_changes(
                old_field.constraints,
                new_field.constraints
            )
            if constraint_desc:
                changes["constraints"] = constraint_desc

        # Изменение формата
        if old_field.format != new_field.format:
            changes["format"] = f"Формат изменился: {old_field.format} → {new_field.format}"

        # Изменение значения по умолчанию
        if old_field.default != new_field.default:
            changes["default"] = (
                f"Значение по умолчанию изменилось: {old_field.default} → {new_field.default}"
            )

        return changes

    def _describe_condition_change(self, old_expr: str, new_expr: str) -> str:
        """
        Описать изменение условия УО

        Старается выделить только конкретные изменения (например, добавленные/удаленные значения),
        а не показывать весь diff условия.

        Args:
            old_expr: Старое SpEL выражение
            new_expr: Новое SpEL выражение

        Returns:
            Человекочитаемое описание изменения

        Example:
            >>> comparator._describe_condition_change(
            ...     "in(#this.productCd, 10410001, 10410002)",
            ...     "in(#this.productCd, 10410001, 10410002, 10410003)"
            ... )
            'Добавлены значения: 10410003'
        """
        # Если условие появилось
        if not old_expr and new_expr:
            preview = new_expr[:100].replace('\n', ' ').strip()
            if len(new_expr) > 100:
                preview += "..."
            return f"Добавлено условие: {preview}"

        # Если условие удалено
        if old_expr and not new_expr:
            preview = old_expr[:100].replace('\n', ' ').strip()
            if len(old_expr) > 100:
                preview += "..."
            return f"Условие удалено: {preview}"

        # Если оба условия существуют
        # Пытаемся найти только изменения в списках значений in(...)

        # Ищем все конструкции in(..., значения, ...)
        old_in_blocks = re.findall(r'in\([^,]+,\s*([0-9,\s]+)\)', old_expr)
        new_in_blocks = re.findall(r'in\([^,]+,\s*([0-9,\s]+)\)', new_expr)

        if old_in_blocks and new_in_blocks:
            # Извлекаем числа из первого найденного блока
            old_values = set()
            new_values = set()

            for block in old_in_blocks:
                old_values.update(re.findall(r'\b\d+\b', block))

            for block in new_in_blocks:
                new_values.update(re.findall(r'\b\d+\b', block))

            added_values = new_values - old_values
            removed_values = old_values - new_values

            # Если есть только добавления/удаления значений
            if added_values and not removed_values:
                if len(added_values) <= 10:
                    return f"Добавлены значения: {', '.join(sorted(added_values))}"
                else:
                    return f"Добавлено {len(added_values)} значений в условие"

            if removed_values and not added_values:
                if len(removed_values) <= 10:
                    return f"Удалены значения: {', '.join(sorted(removed_values))}"
                else:
                    return f"Удалено {len(removed_values)} значений из условия"

            if added_values and removed_values:
                parts = []
                if len(added_values) <= 5:
                    parts.append(f"добавлены: {', '.join(sorted(list(added_values)[:5]))}")
                else:
                    parts.append(f"добавлено: {len(added_values)}")

                if len(removed_values) <= 5:
                    parts.append(f"удалены: {', '.join(sorted(list(removed_values)[:5]))}")
                else:
                    parts.append(f"удалено: {len(removed_values)}")

                return "; ".join(parts).capitalize()

        # Если не смогли определить точные изменения
        # Показываем краткое сравнение
        old_preview = old_expr[:80].replace('\n', ' ').strip()
        new_preview = new_expr[:80].replace('\n', ' ').strip()

        if old_preview != new_preview:
            return f"Условие изменилось (было: {old_preview}{'...' if len(old_expr) > 80 else ''})"

        return "Условие изменилось"

    def _analyze_constraint_changes(
            self,
            old_constraints: Dict[str, Any],
            new_constraints: Dict[str, Any]
    ) -> str:
        """
        Детальный анализ изменений ограничений

        Args:
            old_constraints: Старые ограничения
            new_constraints: Новые ограничения

        Returns:
            Человекочитаемое описание изменений

        Example:
            >>> comparator._analyze_constraint_changes(
            ...     {"maxLength": 100},
            ...     {"maxLength": 50}
            ... )
            'Максимальная длина ужесточено: 100 → 50'
        """
        constraint_names = {
            "minLength": "Минимальная длина",
            "maxLength": "Максимальная длина",
            "minimum": "Минимальное значение",
            "maximum": "Максимальное значение",
            "maxIntLength": "Максимальная длина целой части",
            "minItems": "Минимальное количество элементов",
            "maxItems": "Максимальное количество элементов",
            "pattern": "Регулярное выражение"
        }

        all_keys = set(old_constraints.keys()) | set(new_constraints.keys())
        changes = []

        for key in all_keys:
            if key == "custom":
                continue

            old_val = old_constraints.get(key)
            new_val = new_constraints.get(key)

            if old_val != new_val:
                name = constraint_names.get(key, key)

                if old_val is None:
                    changes.append(f"{name} добавлено: {new_val}")
                elif new_val is None:
                    changes.append(f"{name} удалено (было: {old_val})")
                elif isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                    if key in ["minLength", "minimum", "minItems"]:
                        direction = "ужесточено" if new_val > old_val else "смягчено"
                    else:  # maxLength, maximum, maxItems
                        direction = "ужесточено" if new_val < old_val else "смягчено"
                    changes.append(f"{name} {direction}: {old_val} → {new_val}")
                else:
                    changes.append(f"{name} изменено: {old_val} → {new_val}")

        return "; ".join(changes) if changes else ""
