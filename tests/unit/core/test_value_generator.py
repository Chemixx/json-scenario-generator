"""
Тесты для генератора значений (ValueGenerator).

Approach: TDD (Test-Driven Development)
"""
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import openpyxl
import pytest
from faker import Faker

from src.core.value_generator import GeneratorConfig, ValueGenerator
from src.loaders.dictionary_loader import DictionaryLoader
from src.models.dictionary_models import Dictionary, DictionaryEntry
from src.models.schema_models import FieldMetadata


# =============================================================================
# Helpers
# =============================================================================

def make_field(
    field_type: str,
    name: str = "testField",
    path: str = "test/testField",
    format: str = None,
    constraints: dict = None,
    dictionary: str = None,
    items: FieldMetadata = None,
    default: Any = None,
) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        name=name,
        field_type=field_type,
        format=format,
        constraints=constraints or {},
        dictionary=dictionary,
        items=items,
        default=default,
    )


def validate_inn_checksum(inn: str) -> bool:
    """Проверка КС ИНН (10 или 12 знаков)."""
    if len(inn) == 10:
        digits = [int(c) for c in inn]
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(d * w for d, w in zip(digits[:-1], weights)) % 11
        if checksum == 10:
            checksum = 0
        return digits[-1] == checksum
    if len(inn) == 12:
        digits = [int(c) for c in inn]
        weights_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum1 = sum(d * w for d, w in zip(digits[:10], weights_11)) % 11
        if checksum1 == 10:
            checksum1 = 0
        weights_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum2 = sum(d * w for d, w in zip(digits[:11], weights_12)) % 11
        if checksum2 == 10:
            checksum2 = 0
        return digits[10] == checksum1 and digits[11] == checksum2
    return False


# =============================================================================
# Tests
# =============================================================================

class TestValueGenerator:
    # 1. Базовая строка с maxLength
    def test_generate_string_basic(self):
        field = make_field("string", constraints={"maxLength": 10})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, str)
        assert 1 <= len(val) <= 10

    # 2. Русские имена/адреса через Faker
    def test_generate_string_with_faker(self):
        field = make_field("string", name="fullName")
        config = GeneratorConfig(locale="ru_RU")
        gen = ValueGenerator(config=config)
        val = gen.generate(field)
        assert isinstance(val, str)
        assert len(val) > 0
        # Проверяем наличие кириллических символов (Faker ru_RU обычно генерирует их)
        assert re.search("[а-яА-Я]", val) is not None

    # 3. Число в диапазоне
    def test_generate_integer_with_min_max(self):
        field = make_field("integer", constraints={"minimum": 5, "maximum": 10})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, int)
        assert 5 <= val <= 10

    # 4. number(23,5) — ровно 5 знаков
    def test_generate_number_with_fraction(self):
        field = make_field("number", constraints={"minimum": 0, "maximum": 100, "fraction": 5})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, Decimal)
        # Проверяем, что quantize сработал (дробная часть не более 5 знаков)
        quantizer = Decimal("0.00001")
        assert val == val.quantize(quantizer)
        assert 0 <= val <= 100

    # 5. True или False
    def test_generate_boolean(self):
        field = make_field("boolean")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, bool)

    # 6. YYYY-MM-DD
    def test_generate_date_format(self):
        field = make_field("string", format="date")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", val) is not None

    # 7. ISO 8601 с миллисекундами
    def test_generate_datetime_format(self):
        field = make_field("string", format="date-time")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}", val) is not None

    # 8. Стандартный UUID
    def test_generate_uuid_format(self):
        field = make_field("string", format="uuid", name="requestId")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", val
        ) is not None

    # 9. Одинаковый UUID при повторном вызове с тем же кэшем
    def test_generate_uuid_caching(self):
        field = make_field("string", format="uuid", name="requestId")
        config = GeneratorConfig()
        gen = ValueGenerator(config=config)
        val1 = gen.generate(field)
        val2 = gen.generate(field)
        assert val1 == val2
        assert config.uuid_cache["requestId"] == val1

    # 10. Код из справочника
    def test_generate_from_dictionary(self, mocker):
        field = make_field("string", dictionary="TEST_DICT")
        loader = DictionaryLoader()
        mock_dict = Dictionary(
            name="TEST_DICT",
            entries=[
                DictionaryEntry(code="10410001", name="PACL", dictionary_type="TEST_DICT"),
                DictionaryEntry(code="10410002", name="TOPUP", dictionary_type="TEST_DICT"),
            ],
        )
        mocker.patch.object(loader, "get_cached_dictionary", return_value=mock_dict)
        gen = ValueGenerator(dictionary_loader=loader)
        val = gen.generate(field)
        assert val in {"10410001", "10410002"}

    # 11. ИНН 10 цифр + КС ФНС
    def test_generate_inn_10_valid(self):
        field = make_field("string", format="inn", constraints={"inn_length": 10})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert len(val) == 10
        assert val.isdigit()
        assert validate_inn_checksum(val)

    # 12. ИНН 12 цифр + КС ФНС
    def test_generate_inn_12_valid(self):
        field = make_field("string", format="inn", constraints={"inn_length": 12})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert len(val) == 12
        assert val.isdigit()
        assert validate_inn_checksum(val)

    # 13. 10 цифр без КС (strict=False)
    def test_generate_inn_test_mode(self):
        field = make_field("string", format="inn", constraints={"inn_length": 10})
        config = GeneratorConfig(strict_inn=False)
        gen = ValueGenerator(config=config)
        val = gen.generate(field)
        assert len(val) == 10
        assert val.isdigit()
        # С высокой вероятностью КС невалидна (не проверяем строго)

    # 14. 11 цифр без КС
    def test_generate_snils_basic(self):
        field = make_field("string", format="snils")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert len(val) == 11
        assert val.isdigit()

    # 15. 11 цифр, начинается с 7
    def test_generate_phone(self):
        field = make_field("string", format="phone")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert len(val) == 11
        assert val.startswith("7")
        assert val.isdigit()

    # 16. 1 элемент (default_array_size=1)
    def test_generate_array_default_size(self):
        item_field = make_field("string", name="item", path="arr/item", constraints={"maxLength": 5})
        field = make_field("array", name="arr", path="arr", items=item_field)
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, list)
        assert len(val) == 1
        assert isinstance(val[0], str)

    # 17. N элементов (custom default_array_size)
    def test_generate_array_custom_size(self):
        item_field = make_field("integer", name="item", path="arr/item")
        field = make_field("array", name="arr", path="arr", items=item_field)
        config = GeneratorConfig(default_array_size=3)
        gen = ValueGenerator(config=config)
        val = gen.generate(field)
        assert isinstance(val, list)
        assert len(val) == 3
        assert all(isinstance(v, int) for v in val)

    # 18. Список строк
    def test_generate_array_of_strings(self):
        item_field = make_field("string", name="item", path="arr/item")
        field = make_field("array", name="arr", path="arr", items=item_field)
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, list)
        assert len(val) >= 1
        assert all(isinstance(v, str) for v in val)

    # 19. Регулярка ^[A-Z]{2}$
    def test_apply_pattern_constraint(self):
        field = make_field("string", constraints={"pattern": "^[A-Z]{2}$"})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert re.fullmatch(r"[A-Z]{2}", val) is not None

    # 20. Значение из enum
    def test_apply_enum_constraint(self):
        field = make_field("string", constraints={"enum": ["alpha", "beta", "gamma"]})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert val in {"alpha", "beta", "gamma"}

    # 21. Одинаковый seed = одинаковые значения
    def test_seed_reproducibility(self):
        field = make_field("integer", constraints={"minimum": 1, "maximum": 1000})
        config1 = GeneratorConfig(seed=42)
        config2 = GeneratorConfig(seed=42)
        gen1 = ValueGenerator(config=config1)
        gen2 = ValueGenerator(config=config2)
        val1 = gen1.generate(field)
        val2 = gen2.generate(field)
        assert val1 == val2

    # 22. Реальный справочник из Excel
    def test_integration_with_dictionary_loader(self, tmp_path):
        # Создаем временный Excel-файл
        file_path = tmp_path / "dicts.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products"
        ws.append(["Код", "Значение"])
        ws.append(["10410001", "PACL"])
        ws.append(["10410002", "TOPUP"])
        wb.save(file_path)

        loader = DictionaryLoader()
        loader.load_dictionary(file_path=file_path, sheet_name="Products")

        field = make_field("string", dictionary="Products")
        gen = ValueGenerator(dictionary_loader=loader)
        val = gen.generate(field)
        assert val in {"10410001", "10410002"}

    # 23. Готовый объект vs создание из locale
    def test_faker_two_modes(self):
        ready_faker = Faker("en_US")
        field = make_field("string")
        config = GeneratorConfig(faker=ready_faker)
        gen = ValueGenerator(config=config)
        val = gen.generate(field)
        assert isinstance(val, str)

        config2 = GeneratorConfig(locale="ru_RU")
        gen2 = ValueGenerator(config=config2)
        val2 = gen2.generate(field)
        assert isinstance(val2, str)

    # 24. Integer 1..1000, Number 1.0..1000.0
    def test_number_default_range(self):
        int_field = make_field("integer")
        num_field = make_field("number")
        gen = ValueGenerator()
        int_val = gen.generate(int_field)
        num_val = gen.generate(num_field)
        assert isinstance(int_val, int)
        assert 1 <= int_val <= 1000
        assert isinstance(num_val, Decimal)
        assert Decimal("1.0") <= num_val <= Decimal("1000.0")

    # 25. minLength, maxLength, minimum, maximum
    def test_constraints_min_max(self):
        str_field = make_field("string", constraints={"minLength": 3, "maxLength": 5})
        int_field = make_field("integer", constraints={"minimum": 10, "maximum": 20})
        gen = ValueGenerator()
        str_val = gen.generate(str_field)
        int_val = gen.generate(int_field)
        assert 3 <= len(str_val) <= 5
        assert 10 <= int_val <= 20

    # === Дополнительные тесты для покрытия >90% ===

    def test_generate_default_value(self):
        """Приоритет default над генерацией."""
        field = make_field("string", default="fallback")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert val == "fallback"

    def test_generate_email_format(self):
        field = make_field("string", format="email")
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, str)
        assert "@" in val

    def test_generate_integer_minimum_only(self):
        field = make_field("integer", constraints={"minimum": 500})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, int)
        assert val >= 500

    def test_generate_integer_maximum_only(self):
        field = make_field("integer", constraints={"maximum": 50})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, int)
        assert val <= 50

    def test_generate_number_minimum_only(self):
        field = make_field("number", constraints={"minimum": 500})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, Decimal)
        assert val >= 500

    def test_generate_number_maximum_only(self):
        field = make_field("number", constraints={"maximum": 50})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert isinstance(val, Decimal)
        assert val <= 50

    def test_apply_pattern_digits(self):
        field = make_field("string", constraints={"pattern": r"^\d{6}$"})
        gen = ValueGenerator()
        val = gen.generate(field)
        assert re.fullmatch(r"\d{6}", val) is not None

    def test_generate_unsupported_type(self):
        field = make_field("unsupported")
        gen = ValueGenerator()
        with pytest.raises(ValueError, match="Неподдерживаемый тип поля"):
            gen.generate(field)

    def test_generate_object_raises(self):
        field = make_field("object")
        gen = ValueGenerator()
        with pytest.raises(ValueError, match="object"):
            gen.generate(field)
