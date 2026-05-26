"""Тесты для DictionaryRegistry"""
import pytest
from pathlib import Path
from src.models.dictionary_models import Dictionary, DictionaryEntry, DictionaryMetadata
from src.loaders.dictionary_registry import DictionaryRegistry


@pytest.fixture
def registry():
    return DictionaryRegistry()


@pytest.fixture
def registry_with_data():
    reg = DictionaryRegistry()
    product_type = Dictionary(name="PRODUCT_TYPE", description="Типы продуктов")
    product_type.add_entry(DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"))
    product_type.add_entry(DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"))
    reg.register(product_type)
    currency = Dictionary(name="CURRENCY", description="Валюты")
    currency.add_entry(DictionaryEntry(code=643, name="RUB", dictionary_type="CURRENCY"))
    currency.add_entry(DictionaryEntry(code=840, name="USD", dictionary_type="CURRENCY"))
    reg.register(currency)
    return reg


class TestRegistryBasic:
    def test_register_and_get(self, registry):
        d = Dictionary(name="TEST")
        d.add_entry(DictionaryEntry(code=1, name="A", dictionary_type="TEST"))
        registry.register(d)
        assert registry.get("TEST") is d

    def test_get_nonexistent(self, registry):
        assert registry.get("NONEXISTENT") is None

    def test_list_dictionaries(self, registry_with_data):
        names = registry_with_data.list_dictionaries()
        assert "PRODUCT_TYPE" in names
        assert "CURRENCY" in names
        assert len(names) == 2

    def test_len(self, registry_with_data):
        assert len(registry_with_data) == 2

    def test_contains(self, registry_with_data):
        assert "PRODUCT_TYPE" in registry_with_data
        assert "NONEXISTENT" not in registry_with_data

    def test_clear(self, registry_with_data):
        registry_with_data.clear()
        assert len(registry_with_data) == 0
        assert registry_with_data.get("PRODUCT_TYPE") is None


class TestRegistryLookup:
    def test_get_entry_by_code(self, registry_with_data):
        entry = registry_with_data.get_entry("PRODUCT_TYPE", 10410001)
        assert entry is not None
        assert entry.name == "PACL"

    def test_get_entry_by_code_miss(self, registry_with_data):
        entry = registry_with_data.get_entry("PRODUCT_TYPE", 999999)
        assert entry is None

    def test_get_entry_by_name(self, registry_with_data):
        entry = registry_with_data.get_entry_by_name("CURRENCY", "USD")
        assert entry is not None
        assert entry.code == 840

    def test_get_entry_nonexistent_dict(self, registry_with_data):
        entry = registry_with_data.get_entry("NONEXISTENT", 1)
        assert entry is None


class TestRegistryResolve:
    def test_resolve_default_format(self, registry_with_data):
        result = registry_with_data.resolve("PRODUCT_TYPE", 10410001)
        assert result == "PACL (10410001)"

    def test_resolve_custom_format(self, registry_with_data):
        result = registry_with_data.resolve("PRODUCT_TYPE", 10410001, fmt="{code}")
        assert result == "10410001"

    def test_resolve_name_only(self, registry_with_data):
        name = registry_with_data.resolve_name("CURRENCY", 643)
        assert name == "RUB"

    def test_resolve_nonexistent_dict(self, registry_with_data):
        result = registry_with_data.resolve("NONEXISTENT", 12345)
        assert "12345" in result

    def test_resolve_nonexistent_code(self, registry_with_data):
        result = registry_with_data.resolve("PRODUCT_TYPE", 999999)
        assert "999999" in result


class TestRegistryValidation:
    def test_is_valid_value_by_code(self, registry_with_data):
        assert registry_with_data.is_valid_value("PRODUCT_TYPE", 10410001) is True
        assert registry_with_data.is_valid_value("PRODUCT_TYPE", 999999) is False

    def test_is_valid_value_by_name(self, registry_with_data):
        assert registry_with_data.is_valid_value("PRODUCT_TYPE", "PACL") is True
        assert registry_with_data.is_valid_value("PRODUCT_TYPE", "NONEXISTENT") is False

    def test_is_valid_value_nonexistent_dict(self, registry_with_data):
        assert registry_with_data.is_valid_value("NONEXISTENT", "anything") is True

    def test_is_valid_value_string_code(self, registry_with_data):
        assert registry_with_data.is_valid_value("PRODUCT_TYPE", "10410001") is True


class TestRegistryMetadata:
    def test_register_with_metadata(self, registry):
        meta = DictionaryMetadata(code="PRODUCT_TYPE", name="Тип продукта", dictionary_type_code=1)
        d = Dictionary(name="PRODUCT_TYPE")
        d.add_entry(DictionaryEntry(code=1, name="Test", dictionary_type="PRODUCT_TYPE"))
        registry.register(d, metadata=meta)
        assert registry.get_metadata("PRODUCT_TYPE") is meta

    def test_get_metadata_nonexistent(self, registry):
        assert registry.get_metadata("NONEXISTENT") is None