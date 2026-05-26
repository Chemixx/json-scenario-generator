"""Тесты для JsonDictionaryLoader"""
import json
import pytest
from pathlib import Path
from src.loaders.json_dictionary_loader import JsonDictionaryLoader
from src.models.dictionary_models import DictionaryEntry

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "dictionaries"
SAMPLE_JSON = FIXTURES_DIR / "sample.json"


@pytest.fixture
def loader():
    return JsonDictionaryLoader()


class TestJsonDictionaryLoaderLoad:
    def test_load_creates_dictionaries(self, loader):
        dictionaries, metadata = loader.load(SAMPLE_JSON)
        assert "PRODUCT_TYPE" in dictionaries
        assert "CURRENCY" in dictionaries

    def test_load_correct_entries(self, loader):
        dictionaries, _ = loader.load(SAMPLE_JSON)
        product_type = dictionaries["PRODUCT_TYPE"]
        assert product_type.size() == 2  # 3 entries - 1 deleted = 2

    def test_load_filter_deleted(self, loader):
        dictionaries, _ = loader.load(SAMPLE_JSON, filter_deleted=True)
        product_type = dictionaries["PRODUCT_TYPE"]
        assert product_type.get_by_code(10410003) is None

    def test_load_filter_current(self, loader):
        dictionaries, _ = loader.load(SAMPLE_JSON, filter_current=True)
        currency = dictionaries["CURRENCY"]
        assert currency.get_by_code(840) is None

    def test_load_no_filter(self, loader):
        dictionaries, _ = loader.load(SAMPLE_JSON, filter_deleted=False, filter_current=False)
        product_type = dictionaries["PRODUCT_TYPE"]
        assert product_type.size() == 3  # all entries

    def test_load_metadata(self, loader):
        _, metadata = loader.load(SAMPLE_JSON)
        assert "PRODUCT_TYPE" in metadata
        assert metadata["PRODUCT_TYPE"].code == "PRODUCT_TYPE"
        assert metadata["PRODUCT_TYPE"].name == "Тип продукта"
        assert metadata["PRODUCT_TYPE"].dictionary_type_code == 1

    def test_load_entry_fields(self, loader):
        dictionaries, _ = loader.load(SAMPLE_JSON)
        entry = dictionaries["PRODUCT_TYPE"].get_by_code(10410001)
        assert entry.code == 10410001
        assert entry.name == "PACL"
        assert entry.dictionary_type == "PRODUCT_TYPE"
        assert entry.description == "Потребительский кредит наличными"
        assert entry.english_localization == "Consumer cash loan"

    def test_load_file_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.load(Path("/nonexistent/file.json"))

    def test_load_invalid_json(self, loader, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json", encoding="utf-8")
        with pytest.raises(ValueError):
            loader.load(bad_file)