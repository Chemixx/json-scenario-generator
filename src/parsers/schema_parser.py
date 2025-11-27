"""
Парсер JSON Schema
Извлекает метаданные полей из JSON Schema для анализа изменений между версиями
"""
from pathlib import Path
from typing import Dict, Any, Set

from src.models.schema_models import FieldMetadata, FieldChange, SchemaDiff
from src.utils.json_utils import load_json
from src.utils.logger import get_logger


logger = get_logger(__name__)


class SchemaParser:
    """
    Парсер JSON Schema

    Извлекает метаданные полей из JSON Schema:
    - Типы полей
    - Обязательность (required)
    - Условная обязательность (condition)
    - Справочники (dictionary)
    - Ограничения (constraints)

    Example:
        .. code-block:: python

            parser = SchemaParser()
            schema = parser.load_schema(Path("V072Call1Rq.json"))
            fields = parser.parse_schema(schema)

            for path, field in fields.items():
                print(f"{path}: {field.field_type}")
    """

    def __init__(self):
        """Инициализация парсера"""
        self.logger = get_logger(self.__class__.__name__)

    def load_schema(self, file_path: Path) -> Dict[str, Any]:
        """
        Загрузить JSON Schema из файла

        Args:
            file_path: Путь к JSON Schema файлу

        Returns:
            Словарь с JSON Schema

        Raises:
            FileNotFoundError: Если файл не найден
        """
        self.logger.info(f"📂 Загрузка схемы из {file_path.name}")
        return load_json(file_path)

    def parse_schema(
        self,
        schema: Dict[str, Any],
        parent_path: str = ""
    ) -> Dict[str, FieldMetadata]:
        """
        Парсинг JSON Schema и извлечение метаданных полей

        Args:
            schema: JSON Schema для парсинга
            parent_path: Путь к родительскому объекту (для рекурсии)

        Returns:
            Словарь {путь_к_полю: FieldMetadata}

        Example:
            .. code-block:: python

                parser = SchemaParser()
                schema_data = {"type": "object", "properties": {...}}
                fields = parser.parse_schema(schema_data)
        """
        self.logger.info("🔍 Начало парсинга JSON Schema")

        fields: Dict[str, FieldMetadata] = {}
        required_fields = self._get_required_fields(schema)

        # Парсим свойства
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            field_path = self._build_path(parent_path, field_name)

            # Создаем метаданные поля
            field_metadata = self._parse_field(
                field_name=field_name,
                field_path=field_path,
                field_schema=field_schema,
                is_required=field_name in required_fields
            )

            fields[field_path] = field_metadata

            # Рекурсивно парсим вложенные объекты
            if field_metadata.field_type == "object" and "properties" in field_schema:
                nested_fields = self.parse_schema(field_schema, parent_path=field_path)
                fields.update(nested_fields)

            # Парсим элементы массивов
            if field_metadata.field_type == "array" and "items" in field_schema:
                items_metadata = self._parse_array_items(
                    field_path=field_path,
                    items_schema=field_schema["items"]
                )
                field_metadata.items = items_metadata

                # Если элементы массива - объекты, парсим их свойства
                if items_metadata.field_type == "object" and "properties" in field_schema["items"]:
                    array_item_path = f"{field_path}[]"
                    nested_fields = self.parse_schema(
                        field_schema["items"],
                        parent_path=array_item_path
                    )
                    fields.update(nested_fields)

        self.logger.info(f"✅ Парсинг завершен: найдено {len(fields)} полей")
        return fields

    def _parse_field(
        self,
        field_name: str,
        field_path: str,
        field_schema: Dict[str, Any],
        is_required: bool
    ) -> FieldMetadata:
        """
        Парсинг одного поля

        Args:
            field_name: Имя поля
            field_path: Полный путь к полю
            field_schema: Схема поля
            is_required: Обязательно ли поле

        Returns:
            FieldMetadata с метаданными поля
        """
        field_type = field_schema.get("type", "unknown")
        description = field_schema.get("description", "")

        # Извлекаем справочник (если есть)
        dictionary = field_schema.get("dictionary")

        # Извлекаем условие (если есть)
        is_conditional = "condition" in field_schema
        condition = field_schema.get("condition")

        # Извлекаем ограничения
        constraints = self._extract_constraints(field_schema)

        # Извлекаем формат
        field_format = field_schema.get("format")

        # Извлекаем значение по умолчанию
        default_value = field_schema.get("default")

        return FieldMetadata(
            path=field_path,
            name=field_name,
            field_type=field_type,
            is_required=is_required,
            is_conditional=is_conditional,
            condition=condition,
            dictionary=dictionary,
            constraints=constraints,
            description=description,
            format=field_format,
            default=default_value
        )

    def _parse_array_items(
        self,
        field_path: str,
        items_schema: Dict[str, Any]
    ) -> FieldMetadata:
        """
        Парсинг элементов массива

        Args:
            field_path: Путь к массиву
            items_schema: Схема элементов массива

        Returns:
            FieldMetadata для элементов
        """
        item_type = items_schema.get("type", "unknown")
        description = items_schema.get("description", "")
        constraints = self._extract_constraints(items_schema)
        dictionary = items_schema.get("dictionary")

        return FieldMetadata(
            path=f"{field_path}[]",
            name="items",
            field_type=item_type,
            constraints=constraints,
            description=description,
            dictionary=dictionary
        )

    @staticmethod
    def _extract_constraints(field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлечение ограничений из схемы поля

        Args:
            field_schema: Схема поля

        Returns:
            Словарь с ограничениями
        """
        constraints = {}

        # Строковые ограничения
        if "minLength" in field_schema:
            constraints["minLength"] = field_schema["minLength"]
        if "maxLength" in field_schema:
            constraints["maxLength"] = field_schema["maxLength"]
        if "pattern" in field_schema:
            constraints["pattern"] = field_schema["pattern"]

        # Числовые ограничения
        if "minimum" in field_schema:
            constraints["minimum"] = field_schema["minimum"]
        if "maximum" in field_schema:
            constraints["maximum"] = field_schema["maximum"]
        if "maxIntLength" in field_schema:
            constraints["maxIntLength"] = field_schema["maxIntLength"]

        # Ограничения массива
        if "minItems" in field_schema:
            constraints["minItems"] = field_schema["minItems"]
        if "maxItems" in field_schema:
            constraints["maxItems"] = field_schema["maxItems"]

        # Enum (допустимые значения)
        if "enum" in field_schema:
            constraints["enum"] = field_schema["enum"]

        return constraints

    @staticmethod
    def _get_required_fields(schema: Dict[str, Any]) -> Set[str]:
        """
        Получить список обязательных полей

        Args:
            schema: JSON Schema

        Returns:
            Множество имен обязательных полей
        """
        return set(schema.get("required", []))

    @staticmethod
    def _build_path(parent_path: str, field_name: str) -> str:
        """
        Построить путь к полю

        Args:
            parent_path: Путь к родителю
            field_name: Имя поля

        Returns:
            Полный путь (например, "loanRequest/creditAmt")
        """
        if parent_path:
            return f"{parent_path}/{field_name}"
        return field_name

    def compare_schemas(
        self,
        old_fields: Dict[str, FieldMetadata],
        new_fields: Dict[str, FieldMetadata]
    ) -> SchemaDiff:
        """
        Сравнение двух схем

        Args:
            old_fields: Поля старой схемы
            new_fields: Поля новой схемы

        Returns:
            SchemaDiff с детальными изменениями
        """
        self.logger.info("🔄 Сравнение схем")

        old_paths = set(old_fields.keys())
        new_paths = set(new_fields.keys())

        added_paths = new_paths - old_paths
        removed_paths = old_paths - new_paths
        common_paths = old_paths & new_paths

        # Извлекаем версии (если доступны)
        old_version = "unknown"
        new_version = "unknown"

        diff = SchemaDiff(
            old_version=old_version,
            new_version=new_version,
            call="unknown"
        )

        # Добавленные поля
        for path in added_paths:
            change = FieldChange(
                path=path,
                change_type="added",
                new_meta=new_fields[path]
            )
            diff.added_fields.append(change)

        # Удаленные поля
        for path in removed_paths:
            change = FieldChange(
                path=path,
                change_type="removed",
                old_meta=old_fields[path]
            )
            diff.removed_fields.append(change)

        # Измененные поля
        for path in common_paths:
            old_field = old_fields[path]
            new_field = new_fields[path]

            if self._fields_differ(old_field, new_field):
                changes = self._detect_field_changes(old_field, new_field)
                change = FieldChange(
                    path=path,
                    change_type="modified",
                    old_meta=old_field,
                    new_meta=new_field,
                    changes=changes
                )
                diff.modified_fields.append(change)

        self.logger.info(
            f"📊 Изменения: +{len(diff.added_fields)} полей, "
            f"-{len(diff.removed_fields)} полей, ~{len(diff.modified_fields)} изменений"
        )

        return diff

    @staticmethod
    def _fields_differ(
        old_field: FieldMetadata,
        new_field: FieldMetadata
    ) -> bool:
        """
        Проверка, отличаются ли два поля

        Args:
            old_field: Старое поле
            new_field: Новое поле

        Returns:
            True, если поля отличаются
        """
        return (
            old_field.field_type != new_field.field_type or
            old_field.is_required != new_field.is_required or
            old_field.is_conditional != new_field.is_conditional or
            old_field.condition != new_field.condition or
            old_field.dictionary != new_field.dictionary or
            old_field.constraints != new_field.constraints or
            old_field.format != new_field.format or
            old_field.default != new_field.default
        )

    @staticmethod
    def _detect_field_changes(
        old_field: FieldMetadata,
        new_field: FieldMetadata
    ) -> Dict[str, str]:
        """
        Определить конкретные изменения в поле

        Args:
            old_field: Старое поле
            new_field: Новое поле

        Returns:
            Словарь с описанием изменений
        """
        changes = {}

        if old_field.field_type != new_field.field_type:
            changes["type"] = f"{old_field.field_type} → {new_field.field_type}"

        if old_field.is_required != new_field.is_required:
            changes["required"] = f"{old_field.is_required} → {new_field.is_required}"

        # ✅ ПРОВЕРКА is_conditional
        if old_field.is_conditional != new_field.is_conditional:
            changes["conditional"] = f"{old_field.is_conditional} → {new_field.is_conditional}"

        # ✅ ПРОВЕРКА condition (самого условия)
        if old_field.condition != new_field.condition:
            old_cond = old_field.condition or "None"
            new_cond = new_field.condition or "None"
            changes["condition"] = f"{old_cond} → {new_cond}"

        if old_field.dictionary != new_field.dictionary:
            changes["dictionary"] = f"{old_field.dictionary} → {new_field.dictionary}"

        if old_field.constraints != new_field.constraints:
            changes["constraints"] = "изменены"

        if old_field.format != new_field.format:
            changes["format"] = f"{old_field.format} → {new_field.format}"

        if old_field.default != new_field.default:
            changes["default"] = f"{old_field.default} → {new_field.default}"

        return changes
