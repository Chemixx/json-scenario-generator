"""Интеграционные тесты: полный пайплайн справочников"""
import pytest
from pathlib import Path
from src.loaders.dictionary_registry import DictionaryRegistry
from src.core.spel_functions import SpelFunctions
from src.models.dictionary_models import Dictionary, DictionaryEntry


class TestFullPipeline:
    """End-to-end: JSON -> Registry -> SpEL -> Validation"""

    def test_json_load_to_registry_to_spel(self):
        """Полный цикл: JSON -> Registry -> is_dictionary_value"""
        registry = DictionaryRegistry()
        fixtures = Path(__file__).parent.parent / "fixtures" / "dictionaries"
        registry.load_from_json(fixtures / "sample.json")

        sf = SpelFunctions(registry=registry)

        # Валидные значения
        assert sf.is_dictionary_value("10410001", "PRODUCT_TYPE") is True
        assert sf.is_dictionary_value("PACL", "PRODUCT_TYPE") is True

        # Невалидные значения
        assert sf.is_dictionary_value("99999999", "PRODUCT_TYPE") is False

    def test_json_load_resolve(self):
        """Полный цикл: JSON -> Registry -> resolve"""
        registry = DictionaryRegistry()
        fixtures = Path(__file__).parent.parent / "fixtures" / "dictionaries"
        registry.load_from_json(fixtures / "sample.json")

        result = registry.resolve("PRODUCT_TYPE", 10410001)
        assert result == "PACL (10410001)"

        name = registry.resolve_name("PRODUCT_TYPE", 10410001)
        assert name == "PACL"

    def test_json_load_filter_deleted(self):
        """Фильтрация удалённых записей при загрузке"""
        registry = DictionaryRegistry()
        fixtures = Path(__file__).parent.parent / "fixtures" / "dictionaries"
        registry.load_from_json(fixtures / "sample.json", filter_deleted=True)

        # REFI (10410003) has deleted=true, should be filtered
        product = registry.get("PRODUCT_TYPE")
        assert product.get_by_code(10410003) is None

    def test_json_load_filter_current(self):
        """Фильтрация неактуальных записей при загрузке"""
        registry = DictionaryRegistry()
        fixtures = Path(__file__).parent.parent / "fixtures" / "dictionaries"
        registry.load_from_json(fixtures / "sample.json", filter_current=True)

        # USD (840) has currentVersion=false, should be filtered
        currency = registry.get("CURRENCY")
        assert currency.get_by_code(840) is None

    def test_backward_compat_without_registry(self):
        """Обратная совместимость: SpEL без Registry"""
        sf = SpelFunctions()
        # Fallback: без registry всегда True
        assert sf.is_dictionary_value("any_value", "ANY_DICT") is True

    def test_set_registry_on_existing_instance(self):
        """Установка registry на существующий singleton"""
        from src.core.spel_functions import spel_functions
        registry = DictionaryRegistry()
        d = Dictionary(name="TEST_DICT")
        d.add_entry(DictionaryEntry(code=1, name="VAL1", dictionary_type="TEST_DICT"))
        registry.register(d)

        # Save previous registry to restore later
        prev_registry = spel_functions._registry
        try:
            spel_functions.set_registry(registry)
            assert spel_functions.is_dictionary_value("1", "TEST_DICT") is True
            assert spel_functions.is_dictionary_value("VAL1", "TEST_DICT") is True
            assert spel_functions.is_dictionary_value("INVALID", "TEST_DICT") is False
        finally:
            # Restore previous state
            spel_functions.set_registry(prev_registry)