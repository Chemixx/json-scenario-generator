"""
Тесты для парсера JSON Schema
"""
from src.parsers.schema_parser import SchemaParser
from src.models.schema_models import FieldMetadata, ConditionalRequirement


# ============================================================================
# FIXTURES: Тестовые данные
# ============================================================================

def get_simple_schema() -> dict:
    """Простая схема для тестирования"""
    return {
        "type": "object",
        "required": ["name", "age"],
        "properties": {
            "name": {
                "type": "string",
                "description": "Имя пользователя",
                "minLength": 1,
                "maxLength": 100
            },
            "age": {
                "type": "integer",
                "description": "Возраст",
                "minimum": 0,
                "maximum": 150
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "Email адрес"
            }
        }
    }


def get_nested_schema() -> dict:
    """Схема с вложенными объектами"""
    return {
        "type": "object",
        "required": ["user"],
        "properties": {
            "user": {
                "type": "object",
                "required": ["firstName"],
                "properties": {
                    "firstName": {
                        "type": "string",
                        "description": "Имя"
                    },
                    "lastName": {
                        "type": "string",
                        "description": "Фамилия"
                    },
                    "address": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "Город"
                            },
                            "street": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }
    }


def get_array_schema() -> dict:
    """Схема с массивами"""
    return {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "maxItems": 10
            },
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer"
                        },
                        "name": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    }


def get_schema_with_dictionary() -> dict:
    """Схема со справочниками"""
    return {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "dictionary": "APPLICATION_STATUS",
                "description": "Статус заявки"
            },
            "loanType": {
                "type": "string",
                "dictionary": "LOAN_TYPE",
                "enum": ["CONSUMER", "MORTGAGE", "AUTO"]
            }
        }
    }


def get_schema_with_conditions() -> dict:
    """Схема с условными полями"""
    return {
        "type": "object",
        "properties": {
            "hasChildren": {
                "type": "boolean",
                "description": "Есть дети"
            },
            "childrenCount": {
                "type": "integer",
                "condition": "hasChildren == true",
                "description": "Количество детей"
            }
        }
    }


# ============================================================================
# ТЕСТЫ: Инициализация
# ============================================================================

def test_schema_parser_initialization():
    """Тест: создание экземпляра парсера"""
    parser = SchemaParser()
    assert parser is not None
    assert parser.fields is not None
    # УДАЛЕНО: assert parser.logger is not None (logger не является атрибутом)


# ============================================================================
# ТЕСТЫ: Парсинг простых схем
# ============================================================================

def test_parse_simple_schema():
    """Тест: парсинг простой схемы"""
    parser = SchemaParser()
    schema = get_simple_schema()

    fields = parser.parse_schema(schema)

    # Проверяем количество полей
    assert len(fields) == 3

    # Проверяем наличие полей
    assert "name" in fields
    assert "age" in fields
    assert "email" in fields

    # Проверяем метаданные поля name
    name_field = fields["name"]
    assert name_field.field_type == "string"
    assert name_field.is_required is True
    assert name_field.constraints["minLength"] == 1
    assert name_field.constraints["maxLength"] == 100

    # Проверяем метаданные поля age
    age_field = fields["age"]
    assert age_field.field_type == "integer"
    assert age_field.is_required is True
    assert age_field.constraints["minimum"] == 0
    assert age_field.constraints["maximum"] == 150

    # Проверяем метаданные поля email
    email_field = fields["email"]
    assert email_field.field_type == "string"
    assert email_field.is_required is False
    assert email_field.format == "email"


def test_parse_nested_schema():
    """Тест: парсинг вложенной схемы"""
    parser = SchemaParser()
    schema = get_nested_schema()

    fields = parser.parse_schema(schema)

    # Проверяем наличие вложенных полей
    assert "user" in fields
    assert "user/firstName" in fields
    assert "user/lastName" in fields
    assert "user/address" in fields
    assert "user/address/city" in fields
    assert "user/address/street" in fields

    # Проверяем типы
    assert fields["user"].field_type == "object"
    assert fields["user/firstName"].field_type == "string"
    assert fields["user/address"].field_type == "object"

    # Проверяем обязательность
    assert fields["user"].is_required is True
    assert fields["user/firstName"].is_required is True
    assert fields["user/lastName"].is_required is False


def test_parse_array_schema():
    """Тест: парсинг схемы с массивами"""
    parser = SchemaParser()
    schema = get_array_schema()

    fields = parser.parse_schema(schema)

    # Проверяем массивы
    assert "tags" in fields
    assert fields["tags"].field_type == "array"
    assert fields["tags"].is_collection is True  # ИЗМЕНЕНО: проверяем is_collection вместо items
    assert fields["tags"].constraints["minItems"] == 1
    assert fields["tags"].constraints["maxItems"] == 10

    # Проверяем массив объектов
    assert "users" in fields
    assert fields["users"].field_type == "array"
    assert fields["users"].is_collection is True  # ИЗМЕНЕНО
    assert "users[]/id" in fields
    assert "users[]/name" in fields


def test_parse_schema_with_dictionary():
    """Тест: парсинг схемы со справочниками"""
    parser = SchemaParser()
    schema = get_schema_with_dictionary()

    fields = parser.parse_schema(schema)

    # Проверяем справочники
    assert fields["status"].dictionary == "APPLICATION_STATUS"
    assert fields["loanType"].dictionary == "LOAN_TYPE"

    # Проверяем enum
    assert "enum" in fields["loanType"].constraints
    assert len(fields["loanType"].constraints["enum"]) == 3


def test_parse_schema_with_conditions():
    """Тест: парсинг схемы с условными полями"""
    parser = SchemaParser()
    schema = get_schema_with_conditions()

    fields = parser.parse_schema(schema)

    # Проверяем условное поле
    assert fields["childrenCount"].is_conditional is True

    # ИЗМЕНЕНО: теперь condition - это объект ConditionalRequirement, а не строка
    assert isinstance(fields["childrenCount"].condition, ConditionalRequirement)
    assert fields["childrenCount"].condition.expression == "hasChildren == true"

    assert fields["hasChildren"].is_conditional is False


# ============================================================================
# ТЕСТЫ: Извлечение ограничений
# ============================================================================

def test_extract_string_constraints():
    """Тест: извлечение строковых ограничений"""
    parser = SchemaParser()
    field_schema = {
        "type": "string",
        "minLength": 5,
        "maxLength": 50,
        "pattern": "^[A-Z]+$"
    }

    constraints = parser._extract_constraints(field_schema)

    assert constraints["minLength"] == 5
    assert constraints["maxLength"] == 50
    assert constraints["pattern"] == "^[A-Z]+$"


def test_extract_numeric_constraints():
    """Тест: извлечение числовых ограничений"""
    parser = SchemaParser()
    field_schema = {
        "type": "number",
        "minimum": 0,
        "maximum": 100,
        "maxIntLength": 10
    }

    constraints = parser._extract_constraints(field_schema)

    assert constraints["minimum"] == 0
    assert constraints["maximum"] == 100
    assert constraints["maxIntLength"] == 10


def test_extract_array_constraints():
    """Тест: извлечение ограничений массива"""
    parser = SchemaParser()
    field_schema = {
        "type": "array",
        "minItems": 1,
        "maxItems": 10
    }

    constraints = parser._extract_constraints(field_schema)

    assert constraints["minItems"] == 1
    assert constraints["maxItems"] == 10


# ============================================================================
# ТЕСТЫ: Сравнение схем (УДАЛЕНЫ - перенесены в test_schema_comparator.py)
# ============================================================================

# УДАЛЕНО: test_compare_schemas_added_fields()
# УДАЛЕНО: test_compare_schemas_removed_fields()
# УДАЛЕНО: test_compare_schemas_modified_fields()
# УДАЛЕНО: test_compare_schemas_required_change()


# ============================================================================
# ТЕСТЫ: Утилитарные методы (УДАЛЕНЫ - методы больше не существуют)
# ============================================================================

# УДАЛЕНО: test_build_path() - метод _build_path больше не существует
# УДАЛЕНО: test_get_required_fields() - метод _get_required_fields больше не существует
# УДАЛЕНО: test_fields_differ() - метод _fields_differ перенесен в SchemaComparator
# УДАЛЕНО: test_schema_diff_statistics() - метод compare_schemas перенесен в SchemaComparator


# ============================================================================
# НОВЫЕ ТЕСТЫ: Проверка парсинга ConditionalRequirement
# ============================================================================

def test_parse_condition_as_dict():
    """Тест: парсинг условия в виде объекта"""
    parser = SchemaParser()

    schema = {
        "type": "object",
        "properties": {
            "pledges": {
                "type": "array",
                "condition": {
                    "expression": "in(#this.productCd, 10410001, 10410002)",
                    "message": "Продукт PACCREACT или PACLIREACT",
                    "dqCode": 12345
                }
            }
        }
    }

    fields = parser.parse_schema(schema)

    assert "pledges" in fields
    assert fields["pledges"].is_conditional is True
    assert isinstance(fields["pledges"].condition, ConditionalRequirement)
    assert fields["pledges"].condition.expression == "in(#this.productCd, 10410001, 10410002)"
    assert fields["pledges"].condition.message == "Продукт PACCREACT или PACLIREACT"
    assert fields["pledges"].condition.dq_code == 12345


def test_parse_condition_as_string():
    """Тест: парсинг условия в виде строки"""
    parser = SchemaParser()

    schema = {
        "type": "object",
        "properties": {
            "taxNumber": {
                "type": "string",
                "condition": "notNull(#this.taxNumber)"
            }
        }
    }

    fields = parser.parse_schema(schema)

    assert "taxNumber" in fields
    assert fields["taxNumber"].is_conditional is True
    assert isinstance(fields["taxNumber"].condition, ConditionalRequirement)
    assert fields["taxNumber"].condition.expression == "notNull(#this.taxNumber)"
    # message должно быть сгенерировано автоматически
    assert fields["taxNumber"].condition.message is not None


def test_parse_is_collection_flag():
    """Тест: проверка флага is_collection"""
    parser = SchemaParser()

    schema = {
        "type": "object",
        "properties": {
            "creditAmt": {
                "type": "integer"
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        }
    }

    fields = parser.parse_schema(schema)

    # Обычное поле - не коллекция
    assert fields["creditAmt"].is_collection is False

    # Массив - это коллекция
    assert fields["tags"].is_collection is True
