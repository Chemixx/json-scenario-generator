"""
Парсер JSON Schema для извлечения метаданных полей
"""
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..models import FieldMetadata, ConditionalRequirement
from ..utils import load_json, get_logger

logger = get_logger(__name__)


class SchemaParser:
    """
    Парсер JSON Schema

    Ответственность:
    - Загрузка JSON Schema из файла
    - Рекурсивный парсинг структуры схемы
    - Извлечение метаданных полей (FieldMetadata)
    - Создание плоского словаря полей {путь: метаданные}

    НЕ отвечает за:
    - Сравнение схем (перенесено в SchemaComparator)
    """

    def __init__(self):
        self.fields: Dict[str, FieldMetadata] = {}

    def load_schema(self, schema_path: Path) -> Dict[str, FieldMetadata]:
        """
        Загрузить и распарсить JSON Schema

        Args:
            schema_path: Путь к JSON Schema файлу

        Returns:
            Словарь метаданных полей {путь: метаданные}

        Example:
            >>> parser = SchemaParser()
            >>> fields = parser.load_schema(Path("data/V072Call1Rq.json"))
            >>> print(len(fields))
            245
            >>> print(fields["loanRequest/creditAmt"].field_type)
            'integer'
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
    ) -> Dict[str, FieldMetadata]:
        """
        Рекурсивно распарсить JSON Schema

        Args:
            schema: JSON Schema объект
            path: Текущий путь к полю (например, "loanRequest/creditParameters")
            parent_required: Список обязательных полей родителя

        Returns:
            Словарь метаданных полей {путь: FieldMetadata}

        Example:
            >>> parser = SchemaParser()
            >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            >>> fields = parser.parse_schema(schema)
            >>> print(fields["name"].field_type)
            'string'
        """
        if not schema or not isinstance(schema, dict):
            return self.fields

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

        return self.fields

    def _parse_field(
        self,
        path: str,
        field_schema: Dict[str, Any],
        is_required: bool
    ) -> None:
        """
        Распарсить отдельное поле

        Args:
            path: Полный путь к полю
            field_schema: JSON Schema объект поля
            is_required: Обязательно ли поле (из блока "required")
        """
        field_type = field_schema.get("type", "unknown")

        # Извлечение имени поля из пути
        field_name = path.split("/")[-1].replace("[]", "")

        # Извлечение ограничений
        constraints = self._extract_constraints(field_schema)

        # Извлечение справочника
        dictionary = field_schema.get("dictionary")

        # Извлечение условия (ОБНОВЛЕНО для поддержки ConditionalRequirement)
        condition_obj = None
        condition_dict = field_schema.get("condition")
        if condition_dict:
            if isinstance(condition_dict, dict):
                # Условие в виде объекта {"expression": "...", "message": "..."}
                condition_obj = ConditionalRequirement(
                    expression=condition_dict.get("expression", ""),
                    message=condition_dict.get("message"),
                    dq_code=condition_dict.get("dqCode")
                )
            elif isinstance(condition_dict, str):
                # Условие в виде строки (простое выражение)
                condition_obj = ConditionalRequirement(
                    expression=condition_dict
                )

        is_conditional = condition_obj is not None

        # Определение is_collection (НОВОЕ)
        is_collection = field_type == "array"

        # Создание метаданных поля
        metadata = FieldMetadata(
            name=field_name,
            path=path,
            field_type=field_type,
            is_required=is_required,
            is_conditional=is_conditional,
            constraints=constraints,
            dictionary=dictionary,
            condition=condition_obj,  # ← Теперь объект ConditionalRequirement
            format=field_schema.get("format"),
            default=field_schema.get("default"),
            description=field_schema.get("description"),
            is_collection=is_collection  # ← НОВОЕ ПОЛЕ
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
        """
        Извлечь ограничения поля

        Args:
            field_schema: JSON Schema объект поля

        Returns:
            Словарь ограничений
        """
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
