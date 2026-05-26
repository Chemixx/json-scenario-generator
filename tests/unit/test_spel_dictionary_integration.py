"""Тесты интеграции SpEL с Registry"""
import pytest
from src.models.dictionary_models import Dictionary, DictionaryEntry
from src.loaders.dictionary_registry import DictionaryRegistry
from src.core.spel_functions import SpelFunctions


@pytest.fixture
def registry_with_product_type():
    """Registry с PRODUCT_TYPE справочником"""
    reg = DictionaryRegistry()
    d = Dictionary(name="PRODUCT_TYPE")
    d.add_entry(DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"))
    d.add_entry(DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"))
    reg.register(d)
    return reg


class TestSpelDictionaryIntegration:
    def test_is_dictionary_value_with_registry_valid_code(self, registry_with_product_type):
        """isDictionaryValue возвращает True для валидного кода"""
        sf = SpelFunctions(registry=registry_with_product_type)
        assert sf.is_dictionary_value("10410001", "PRODUCT_TYPE") is True

    def test_is_dictionary_value_with_registry_valid_name(self, registry_with_product_type):
        """isDictionaryValue возвращает True для валидного названия"""
        sf = SpelFunctions(registry=registry_with_product_type)
        assert sf.is_dictionary_value("PACL", "PRODUCT_TYPE") is True

    def test_is_dictionary_value_with_registry_invalid(self, registry_with_product_type):
        """isDictionaryValue возвращает False для невалидного значения"""
        sf = SpelFunctions(registry=registry_with_product_type)
        assert sf.is_dictionary_value("INVALID_VALUE", "PRODUCT_TYPE") is False

    def test_is_dictionary_value_without_registry(self):
        """isDictionaryValue без registry — fallback True"""
        sf = SpelFunctions()
        assert sf.is_dictionary_value("any_value", "ANY_DICT") is True

    def test_is_dictionary_value_allow_empty(self, registry_with_product_type):
        """isDictionaryValue с allow_empty=True"""
        sf = SpelFunctions(registry=registry_with_product_type)
        assert sf.is_dictionary_value("", "PRODUCT_TYPE", allow_empty=True) is True
        assert sf.is_dictionary_value(None, "PRODUCT_TYPE", allow_empty=True) is True

    def test_set_registry(self, registry_with_product_type):
        """Установка registry через set_registry"""
        sf = SpelFunctions()
        assert sf.is_dictionary_value("INVALID", "PRODUCT_TYPE") is True  # no registry
        sf.set_registry(registry_with_product_type)
        assert sf.is_dictionary_value("INVALID", "PRODUCT_TYPE") is False  # with registry