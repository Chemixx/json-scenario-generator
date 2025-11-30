"""
Парсер JSON Schema для извлечения метаданных полей
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

from ..models import FieldMetadata, SchemaDiff, FieldChange
from ..utils import load_json, get_logger

logger = get_logger(__name__)


class SchemaParser:
    """Парсер JSON Schema"""

    def __init__(self):
        self.fields: Dict[str, FieldMetadata] = {}

    def load_schema(self, schema_path: Path) -> Dict[str, FieldMetadata]:
        """
        Загрузить и распарсить JSON Schema

        Args:
            schema_path: Путь к JSON Schema файлу

        Returns:
            Словарь метаданных полей {путь: метаданные}
        """
        logger.info(f"📂 Загрузка схемы из {schema_path.name}")
        schema = load_json(schema_path)
        self.fields = {}
        self.parse_schema(schema)
        return self.fields

    def parse_schema(
        self,
        schema: Dict[str, Any],
        path: str = "",
        parent_required: List[str] = None
    ) -> None:
        """
        Рекурсивно парсить JSON Schema

        Args:
            schema: JSON Schema объект
            path: Текущий путь к полю
            parent_required: Список обязательных полей родителя
        """
        if not schema or not isinstance(schema, dict):
            return

        logger.info(f"🔍 Начало парсинга JSON Schema")

        parent_required = parent_required or []
        schema_type = schema.get("type")
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        # Парсинг свойств объекта
        if schema_type == "object" and properties:
            for field_name, field_schema in properties.items():
                field_path = f"{path}/{field_name}" if path else field_name
                self._parse_field(
                    field_path,
                    field_schema,
                    field_name in required_fields
                )

        # Парсинг элементов массива
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            if items_schema:
                array_path = f"{path}[]" if path else "[]"
                self.parse_schema(items_schema, array_path, required_fields)

        logger.info(f"✅ Парсинг завершен: найдено {len(self.fields)} полей")

    def _parse_field(
            self,
            path: str,
            field_schema: Dict[str, Any],
            is_required: bool
    ) -> None:
        """Распарсить отдельное поле"""
        field_type = field_schema.get("type", "unknown")

        # Извлечение имени поля из пути
        field_name = path.split("/")[-1].replace("[]", "")

        # Извлечение ограничений
        constraints = self._extract_constraints(field_schema)

        # Извлечение справочника
        dictionary = field_schema.get("dictionary")

        # Извлечение условия
        condition = field_schema.get("condition")
        is_conditional = condition is not None

        # Создание метаданных поля
        metadata = FieldMetadata(
            name=field_name,  # ← ДОБАВЛЕНО!
            path=path,
            field_type=field_type,
            is_required=is_required,
            is_conditional=is_conditional,
            constraints=constraints,
            dictionary=dictionary,
            condition=condition,
            format=field_schema.get("format"),
            default=field_schema.get("default"),
            description=field_schema.get("description")
        )

        self.fields[path] = metadata

        # Рекурсивный парсинг вложенных объектов
        if field_type == "object":
            properties = field_schema.get("properties", {})
            required_fields = field_schema.get("required", [])
            for nested_name, nested_schema in properties.items():
                nested_path = f"{path}/{nested_name}"
                self._parse_field(
                    nested_path,
                    nested_schema,
                    nested_name in required_fields
                )

        # Рекурсивный парсинг массивов
        elif field_type == "array":
            items_schema = field_schema.get("items", {})
            if items_schema and isinstance(items_schema, dict):
                items_path = f"{path}[]"
                items_type = items_schema.get("type", "unknown")

                if items_type == "object":
                    properties = items_schema.get("properties", {})
                    required_fields = items_schema.get("required", [])
                    for item_name, item_schema in properties.items():
                        item_path = f"{items_path}/{item_name}"
                        self._parse_field(
                            item_path,
                            item_schema,
                            item_name in required_fields
                        )

    def _extract_constraints(self, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечь ограничения поля"""
        constraint_keys = [
            "minLength", "maxLength", "minimum", "maximum",
            "minItems", "maxItems", "maxIntLength", "maxFracLength",
            "pattern", "enum"
        ]

        constraints = {}
        for key in constraint_keys:
            if key in field_schema:
                constraints[key] = field_schema[key]

        # Дополнительные constraints из массива
        if "constraints" in field_schema:
            constraints["custom"] = field_schema["constraints"]

        return constraints

    @staticmethod
    def compare_schemas(
        old_schema: Dict[str, FieldMetadata],
        new_schema: Dict[str, FieldMetadata]
    ) -> SchemaDiff:
        """
        Сравнить две схемы и найти изменения

        Args:
            old_schema: Старая схема
            new_schema: Новая схема

        Returns:
            Объект с различиями
        """
        logger.info(f"🔄 Сравнение схем")

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
            elif old_field != new_field:
                # Поле изменено
                changes = SchemaParser._detect_field_changes(old_field, new_field)
                modified_fields.append(FieldChange(
                    path=path,
                    change_type="modified",
                    old_meta=old_field,
                    new_meta=new_field,
                    changes=changes
                ))

        logger.info(
            f"📊 Изменения: +{len(added_fields)} полей, "
            f"-{len(removed_fields)} полей, ~{len(modified_fields)} изменений"
        )

        return SchemaDiff(
            old_version="",
            new_version="",
            call="",
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields
        )

    @staticmethod
    def _detect_field_changes(
        old_field: FieldMetadata,
        new_field: FieldMetadata
    ) -> Dict[str, Any]:
        """
        Определить конкретные изменения в поле

        Args:
            old_field: Старое поле
            new_field: Новое поле

        Returns:
            Словарь с описанием изменений
        """
        changes = {}

        # Изменение типа
        if old_field.field_type != new_field.field_type:
            changes["type"] = f"Тип поля изменился: {old_field.field_type} → {new_field.field_type}"

        # Изменение обязательности
        if old_field.is_required != new_field.is_required:
            if new_field.is_required:
                changes["required"] = "Поле стало обязательным"
            else:
                changes["required"] = "Поле стало опциональным"

        # Изменение условной обязательности
        if old_field.is_conditional != new_field.is_conditional:
            if new_field.is_conditional:
                changes["conditional"] = "Поле стало условно обязательным (УО)"
            else:
                changes["conditional"] = "Поле перестало быть условно обязательным"

        # Изменение самого условия
        if old_field.condition != new_field.condition:
            old_cond = old_field.condition or {}
            new_cond = new_field.condition or {}

            old_expr = old_cond.get("expression", "") if isinstance(old_cond, dict) else str(old_cond)
            new_expr = new_cond.get("expression", "") if isinstance(new_cond, dict) else str(new_cond)

            changes["condition"] = SchemaParser._describe_condition_change(old_expr, new_expr)

        # Изменение справочника
        if old_field.dictionary != new_field.dictionary:
            changes["dictionary"] = f"Справочник изменился: '{old_field.dictionary}' → '{new_field.dictionary}'"

        # Изменение ограничений
        if old_field.constraints != new_field.constraints:
            constraint_desc = SchemaParser._analyze_constraint_changes(
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
            changes["default"] = f"Значение по умолчанию изменилось: {old_field.default} → {new_field.default}"

        return changes

    @staticmethod
    def _describe_condition_change(old_expr: str, new_expr: str) -> str:
        """Описать изменение условия"""
        # Если условие появилось
        if not old_expr and new_expr:
            # Показываем первые 100 символов нового условия
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
        import re

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

    @staticmethod
    def _analyze_constraint_changes(
        old_constraints: Dict[str, Any],
        new_constraints: Dict[str, Any]
    ) -> str:
        """Детальный анализ изменений ограничений"""
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
