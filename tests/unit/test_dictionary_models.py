"""
Тесты для моделей справочников
"""
import pytest
from src.models.dictionary_models import DictionaryEntry, Dictionary


# ============================================================================
# ТЕСТЫ: DictionaryEntry
# ============================================================================

def test_dictionary_entry_creation():
    """Тест создания DictionaryEntry"""
    entry = DictionaryEntry(
        code=10410001,
        name="PACL",
        dictionary_type="PRODUCT_TYPE",
        description="Потребительский кредит наличными"
    )

    assert entry.code == 10410001
    assert entry.name == "PACL"
    assert entry.dictionary_type == "PRODUCT_TYPE"
    assert entry.description == "Потребительский кредит наличными"


def test_dictionary_entry_to_dict():
    """Тест метода to_dict()"""
    entry = DictionaryEntry(
        code=10410001,
        name="PACL",
        dictionary_type="PRODUCT_TYPE"
    )

    result = entry.to_dict()

    assert result["code"] == 10410001
    assert result["name"] == "PACL"
    assert result["dictionary_type"] == "PRODUCT_TYPE"
    assert "description" in result
    assert "metadata" in result


def test_dictionary_entry_str_repr():
    """Тест методов __str__ и __repr__"""
    entry = DictionaryEntry(
        code=10410001,
        name="PACL",
        dictionary_type="PRODUCT_TYPE"
    )

    str_result = str(entry)
    assert "PACL" in str_result
    assert "10410001" in str_result

    repr_result = repr(entry)
    assert "DictionaryEntry" in repr_result
    assert "10410001" in repr_result


# ============================================================================
# ТЕСТЫ: Dictionary
# ============================================================================

def test_dictionary_creation():
    """Тест создания Dictionary"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        description="Типы продуктов"
    )

    assert dictionary.name == "PRODUCT_TYPE"
    assert dictionary.description == "Типы продуктов"
    assert len(dictionary.entries) == 0


def test_dictionary_add_entry():
    """Тест метода add_entry()"""
    dictionary = Dictionary(name="PRODUCT_TYPE")

    entry = DictionaryEntry(
        code=10410001,
        name="PACL",
        dictionary_type="PRODUCT_TYPE"
    )

    dictionary.add_entry(entry)

    assert dictionary.size() == 1
    assert dictionary.is_empty() is False


def test_dictionary_get_by_code():
    """Тест метода get_by_code()"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
            DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    # Существующий код
    entry = dictionary.get_by_code(10410001)
    assert entry is not None
    assert entry.name == "PACL"

    # Несуществующий код
    entry_none = dictionary.get_by_code(99999)
    assert entry_none is None


def test_dictionary_get_by_name():
    """Тест метода get_by_name()"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
            DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    # Существующее название
    entry = dictionary.get_by_name("PACL")
    assert entry is not None
    assert entry.code == 10410001

    # Несуществующее название
    entry_none = dictionary.get_by_name("NONEXISTENT")
    assert entry_none is None


def test_dictionary_get_random():
    """Тест метода get_random()"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
            DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    # Получаем случайную запись
    random_entry = dictionary.get_random()
    assert random_entry in dictionary.entries

    # Пустой справочник должен вызвать ошибку
    empty_dict = Dictionary(name="EMPTY")
    with pytest.raises(ValueError, match="пуст"):
        empty_dict.get_random()


def test_dictionary_get_all_codes_names():
    """Тест методов get_all_codes() и get_all_names()"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
            DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    codes = dictionary.get_all_codes()
    assert codes == [10410001, 10410002]

    names = dictionary.get_all_names()
    assert names == ["PACL", "TOPUP"]


def test_dictionary_size_and_empty():
    """Тест методов size() и is_empty()"""
    dictionary = Dictionary(name="PRODUCT_TYPE")

    # Пустой справочник
    assert dictionary.size() == 0
    assert dictionary.is_empty() is True
    assert len(dictionary) == 0  # Через __len__

    # Добавляем запись
    dictionary.add_entry(DictionaryEntry(code=1, name="Entry1", dictionary_type="PRODUCT_TYPE"))

    assert dictionary.size() == 1
    assert dictionary.is_empty() is False
    assert len(dictionary) == 1


def test_dictionary_contains():
    """Тест методов contains_code(), contains_name() и оператора 'in'"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    # contains_code()
    assert dictionary.contains_code(10410001) is True
    assert dictionary.contains_code(99999) is False

    # contains_name()
    assert dictionary.contains_name("PACL") is True
    assert dictionary.contains_name("NONEXISTENT") is False

    # Оператор 'in' (через __contains__)
    assert 10410001 in dictionary  # По коду
    assert "PACL" in dictionary  # По названию
    assert 99999 not in dictionary


def test_dictionary_iteration():
    """Тест итерации по справочнику"""
    entries_list = [
        DictionaryEntry(code=1, name="Entry1", dictionary_type="TEST"),
        DictionaryEntry(code=2, name="Entry2", dictionary_type="TEST"),
    ]

    dictionary = Dictionary(
        name="TEST",
        entries=entries_list
    )

    # Итерация через for
    collected = []
    for entry in dictionary:
        collected.append(entry)

    assert collected == entries_list


def test_dictionary_to_dict():
    """Тест метода to_dict()"""
    dictionary = Dictionary(
        name="PRODUCT_TYPE",
        description="Типы продуктов",
        entries=[
            DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
        ]
    )

    result = dictionary.to_dict()

    assert result["name"] == "PRODUCT_TYPE"
    assert result["description"] == "Типы продуктов"
    assert result["size"] == 1
    assert len(result["entries"]) == 1
    assert result["entries"][0]["code"] == 10410001
