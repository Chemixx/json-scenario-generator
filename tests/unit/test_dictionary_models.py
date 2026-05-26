"""
Тесты для моделей справочников
"""
import pytest
from src.models.dictionary_models import DictionaryEntry, Dictionary, DictionaryMetadata, ResolveResult


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


# ============================================================================
# ТЕСТЫ: DictionaryEntry — расширенные поля
# ============================================================================

def test_dictionary_entry_extended_fields():
    """Тест расширенных полей DictionaryEntry (production-поля)"""
    entry = DictionaryEntry(
        code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE",
        description="Потребительский кредит",
        english_localization="Consumer cash loan",
        current_version=True, is_deleted=False,
        attributes=[{"name": "TAG1", "value": "да", "type": "STRING"}],
        mappings=[{"code": 1, "value": "1", "defaultValue": True, "reverseDefaultValue": True}],
    )
    assert entry.english_localization == "Consumer cash loan"
    assert entry.current_version is True
    assert entry.is_deleted is False
    assert len(entry.attributes) == 1
    assert len(entry.mappings) == 1


def test_dictionary_entry_defaults_backward_compat():
    """Тест обратной совместимости — новые поля имеют дефолтные значения"""
    entry = DictionaryEntry(code=1, name="Test", dictionary_type="TEST")
    assert entry.english_localization is None
    assert entry.current_version is True
    assert entry.is_deleted is False
    assert entry.attributes == []
    assert entry.mappings == []


def test_dictionary_entry_to_dict_includes_new_fields():
    """Тест to_dict() включает новые поля условно"""
    entry = DictionaryEntry(code=1, name="Test", dictionary_type="TEST",
        english_localization="Test EN",
        attributes=[{"name": "A1", "value": "v1", "type": "STRING"}])
    d = entry.to_dict()
    assert d["english_localization"] == "Test EN"
    assert len(d["attributes"]) == 1


def test_dictionary_entry_to_dict_excludes_default_new_fields():
    """Тест to_dict() не включает дефолтные новые поля"""
    entry = DictionaryEntry(code=1, name="Test", dictionary_type="TEST")
    d = entry.to_dict()
    assert "english_localization" not in d
    assert "current_version" not in d  # True по умолчанию — не включается
    assert "is_deleted" not in d       # False по умолчанию — не включается
    assert "attributes" not in d       # Пустой список — не включается
    assert "mappings" not in d          # Пустой список — не включается


def test_dictionary_entry_to_dict_includes_non_default_new_fields():
    """Тест to_dict() включает ненефолтные новые поля"""
    entry = DictionaryEntry(code=1, name="Test", dictionary_type="TEST",
        current_version=False, is_deleted=True,
        mappings=[{"code": 1, "value": "x"}])
    d = entry.to_dict()
    assert d["current_version"] is False
    assert d["is_deleted"] is True
    assert len(d["mappings"]) == 1


# ============================================================================
# ТЕСТЫ: Dictionary — хеш-индексы
# ============================================================================

def test_dictionary_add_entry_builds_indexes():
    """Тест: add_entry заполняет хеш-индексы"""
    dictionary = Dictionary(name="TEST")
    entry = DictionaryEntry(code=10410001, name="PACL", dictionary_type="TEST")
    dictionary.add_entry(entry)
    assert dictionary.get_by_code(10410001) is entry
    assert dictionary.get_by_name("PACL") is entry


def test_dictionary_hash_index_o1():
    """Тест: хеш-индекс даёт поиск O(1) для больших справочников"""
    dictionary = Dictionary(name="TEST")
    for i in range(100):
        dictionary.add_entry(DictionaryEntry(code=i, name=f"NAME_{i}", dictionary_type="TEST"))
    assert dictionary.get_by_code(50).name == "NAME_50"
    assert dictionary.get_by_name("NAME_99").code == 99


def test_dictionary_hash_index_miss():
    """Тест: хеш-индекс возвращает None для отсутствующих ключей"""
    dictionary = Dictionary(name="TEST")
    dictionary.add_entry(DictionaryEntry(code=1, name="A", dictionary_type="TEST"))
    assert dictionary.get_by_code(999) is None
    assert dictionary.get_by_name("NONEXISTENT") is None


def test_dictionary_init_builds_indexes():
    """Тест: индексы строятся при инициализации через entries"""
    entries = [
        DictionaryEntry(code=1, name="A", dictionary_type="TEST"),
        DictionaryEntry(code=2, name="B", dictionary_type="TEST"),
    ]
    dictionary = Dictionary(name="TEST", entries=entries)
    assert dictionary.get_by_code(1).name == "A"
    assert dictionary.get_by_name("B").code == 2


# ============================================================================
# ТЕСТЫ: DictionaryMetadata
# ============================================================================

def test_dictionary_metadata_creation():
    """Тест создания DictionaryMetadata"""
    meta = DictionaryMetadata(code="PRODUCT_TYPE", name="Тип продукта", dictionary_type_code=1, subsystem=0)
    assert meta.code == "PRODUCT_TYPE"
    assert meta.name == "Тип продукта"
    assert str(meta) == "PRODUCT_TYPE: Тип продукта"


def test_dictionary_metadata_defaults():
    """Тест дефолтных значений DictionaryMetadata"""
    meta = DictionaryMetadata(code="TEST", name="Тестовый")
    assert meta.dictionary_type_code == 1
    assert meta.subsystem == 0
    assert meta.hierarchical is False
    assert meta.form_dict_flg is False
    assert meta.attribute_metadata == []


# ============================================================================
# ТЕСТЫ: ResolveResult
# ============================================================================

def test_resolve_result_format():
    """Тест ResolveResult.format() с различными шаблонами"""
    result = ResolveResult(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE",
        description="Потребительский кредит", english_localization="Consumer cash loan")
    assert str(result) == "PACL (10410001)"
    assert result.format("{name} ({code})") == "PACL (10410001)"
    assert result.format("{code}") == "10410001"
    assert result.format("{name}") == "PACL"
    assert result.format("{name} [{eng}]") == "PACL [Consumer cash loan]"


def test_resolve_result_format_without_english():
    """Тест ResolveResult.format() без английской локализации"""
    result = ResolveResult(code=1, name="Test", dictionary_type="TEST")
    assert result.format("{name} [{eng}]") == "Test []"
