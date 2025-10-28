"""
Тесты для загрузчика справочников
"""
import pytest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from src.loaders.dictionary_loader import DictionaryLoader
from src.models.dictionary_models import Dictionary


# ============================================================================
# FIXTURES: Тестовые данные
# ============================================================================

@pytest.fixture
def sample_dataframe_classic():
    """Тестовый DataFrame в классическом формате"""
    return pd.DataFrame({
        "Код": ["01", "02", "03"],
        "Значение": ["Первый", "Второй", "Третий"],
        "Описание": ["Описание 1", "Описание 2", "Описание 3"]
    })


@pytest.fixture
def sample_dataframe_grouped():
    """Тестовый DataFrame в групповом формате"""
    return pd.DataFrame({
        "Код справочника": ["STATUS", "STATUS", "TYPE", "TYPE"],
        "Код РКК": ["11730070", "11730071", "12240065", "12240066"],
        "Наименование значения": ["Активный", "Неактивный", "Тип А", "Тип Б"]
    })


@pytest.fixture
def loader():
    """Создать экземпляр загрузчика"""
    return DictionaryLoader()


# ============================================================================
# ТЕСТЫ: Инициализация
# ============================================================================

def test_dictionary_loader_initialization(loader):
    """Тест: создание экземпляра загрузчика"""
    assert loader is not None
    assert loader.logger is not None
    assert loader._cache == {}


# ============================================================================
# ТЕСТЫ: Классический формат (load_dictionary)
# ============================================================================

@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_classic_format(mock_load_excel, loader, sample_dataframe_classic):
    """Тест: загрузка справочника в классическом формате"""
    mock_load_excel.return_value = sample_dataframe_classic

    dictionary = loader.load_dictionary(
        file_path=Path("test.xlsx"),
        sheet_name="TestSheet"
    )

    assert dictionary.name == "TestSheet"
    assert len(dictionary) == 3
    assert dictionary.get_by_code("01").name == "Первый"
    assert dictionary.get_by_code("02").name == "Второй"


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_with_description(mock_load_excel, loader, sample_dataframe_classic):
    """Тест: загрузка справочника с описанием"""
    mock_load_excel.return_value = sample_dataframe_classic

    dictionary = loader.load_dictionary(
        file_path=Path("test.xlsx"),
        sheet_name="TestSheet",
        description_column="Описание"
    )

    entry = dictionary.get_by_code("01")
    assert entry.description == "Описание 1"


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_skip_empty_rows(mock_load_excel, loader):
    """Тест: пропуск пустых строк"""
    df_with_empty = pd.DataFrame({
        "Код": ["01", None, "03"],
        "Значение": ["Первый", "Второй", None]
    })
    mock_load_excel.return_value = df_with_empty

    dictionary = loader.load_dictionary(
        file_path=Path("test.xlsx"),
        sheet_name="TestSheet"
    )

    # Должна быть загружена только 1 валидная строка
    assert len(dictionary) == 1
    assert dictionary.get_by_code("01").name == "Первый"


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_caching(mock_load_excel, loader, sample_dataframe_classic):
    """Тест: кэширование загруженных справочников"""
    mock_load_excel.return_value = sample_dataframe_classic

    # Первая загрузка
    dict1 = loader.load_dictionary(
        file_path=Path("test.xlsx"),
        sheet_name="TestSheet"
    )

    # Вторая загрузка (должна быть из кэша)
    dict2 = loader.load_dictionary(
        file_path=Path("test.xlsx"),
        sheet_name="TestSheet"
    )

    # load_excel должен быть вызван только один раз
    assert mock_load_excel.call_count == 1
    assert dict1 is dict2  # Это один и тот же объект из кэша


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_missing_columns(mock_load_excel, loader):
    """Тест: ошибка при отсутствии обязательных колонок"""
    df_invalid = pd.DataFrame({
        "WrongColumn": ["01", "02"]
    })
    mock_load_excel.return_value = df_invalid

    with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
        loader.load_dictionary(
            file_path=Path("test.xlsx"),
            sheet_name="TestSheet"
        )


# ============================================================================
# ТЕСТЫ: Групповой формат (load_dictionary_by_code)
# ============================================================================

@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_by_code(mock_load_excel, loader, sample_dataframe_grouped):
    """Тест: загрузка конкретного справочника по коду"""
    mock_load_excel.return_value = sample_dataframe_grouped

    dictionary = loader.load_dictionary_by_code(
        file_path=Path("test.xlsx"),
        sheet_name="All",
        dictionary_code="STATUS"
    )

    assert dictionary.name == "STATUS"
    assert len(dictionary) == 2
    assert dictionary.get_by_code("11730070").name == "Активный"
    assert dictionary.get_by_code("11730071").name == "Неактивный"


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_by_code_not_found(mock_load_excel, loader, sample_dataframe_grouped):
    """Тест: запрос несуществующего справочника"""
    mock_load_excel.return_value = sample_dataframe_grouped

    dictionary = loader.load_dictionary_by_code(
        file_path=Path("test.xlsx"),
        sheet_name="All",
        dictionary_code="NONEXISTENT"
    )

    assert dictionary.name == "NONEXISTENT"
    assert len(dictionary) == 0  # Пустой справочник


@patch('src.loaders.dictionary_loader.load_excel')
def test_load_dictionary_by_code_caching(mock_load_excel, loader, sample_dataframe_grouped):
    """Тест: кэширование при загрузке по коду"""
    mock_load_excel.return_value = sample_dataframe_grouped

    dict1 = loader.load_dictionary_by_code(
        file_path=Path("test.xlsx"),
        sheet_name="All",
        dictionary_code="STATUS"
    )

    dict2 = loader.load_dictionary_by_code(
        file_path=Path("test.xlsx"),
        sheet_name="All",
        dictionary_code="STATUS"
    )

    assert mock_load_excel.call_count == 1
    assert dict1 is dict2


# ============================================================================
# ТЕСТЫ: Загрузка всех справочников
# ============================================================================

@patch('src.loaders.dictionary_loader.load_excel')
def test_load_all_dictionaries_from_sheet(mock_load_excel, loader, sample_dataframe_grouped):
    """Тест: загрузка всех справочников из одного листа"""
    mock_load_excel.return_value = sample_dataframe_grouped

    dictionaries = loader.load_all_dictionaries_from_sheet(
        file_path=Path("test.xlsx"),
        sheet_name="All"
    )

    assert len(dictionaries) == 2
    assert "STATUS" in dictionaries
    assert "TYPE" in dictionaries
    assert len(dictionaries["STATUS"]) == 2
    assert len(dictionaries["TYPE"]) == 2


@patch('src.loaders.dictionary_loader.get_sheet_names')
@patch('src.loaders.dictionary_loader.load_excel')
def test_load_all_dictionaries_classic(mock_load_excel, mock_get_sheets, loader, sample_dataframe_classic):
    """Тест: загрузка всех справочников (классический формат)"""
    mock_get_sheets.return_value = ["Sheet1", "Sheet2"]
    mock_load_excel.return_value = sample_dataframe_classic

    dictionaries = loader.load_all_dictionaries(
        file_path=Path("test.xlsx")
    )

    assert len(dictionaries) == 2
    assert "Sheet1" in dictionaries
    assert "Sheet2" in dictionaries


@patch('src.loaders.dictionary_loader.get_sheet_names')
@patch('src.loaders.dictionary_loader.load_excel')
def test_load_all_dictionaries_with_exclude(mock_load_excel, mock_get_sheets, loader, sample_dataframe_classic):
    """Тест: загрузка с исключением листов"""
    mock_get_sheets.return_value = ["Sheet1", "Sheet2", "Legend"]
    mock_load_excel.return_value = sample_dataframe_classic

    dictionaries = loader.load_all_dictionaries(
        file_path=Path("test.xlsx"),
        exclude_sheets=["Legend"]
    )

    assert len(dictionaries) == 2
    assert "Legend" not in dictionaries


# ============================================================================
# ТЕСТЫ: Кэш
# ============================================================================

def test_get_cached_dictionary(loader):
    """Тест: получение справочника из кэша"""
    test_dict = Dictionary(name="Test", description="Test dictionary")
    loader._cache["test_key"] = test_dict

    cached = loader.get_cached_dictionary("test_key")

    assert cached is test_dict


def test_get_cached_dictionary_not_found(loader):
    """Тест: попытка получить несуществующий справочник из кэша"""
    cached = loader.get_cached_dictionary("nonexistent")

    assert cached is None


def test_clear_cache(loader):
    """Тест: очистка кэша"""
    test_dict = Dictionary(name="Test", description="Test dictionary")
    loader._cache["test_key"] = test_dict

    loader.clear_cache()

    assert len(loader._cache) == 0


def test_get_cache_info(loader):
    """Тест: получение информации о кэше"""
    test_dict1 = Dictionary(name="Test1")
    test_dict2 = Dictionary(name="Test2")
    loader._cache["key1"] = test_dict1
    loader._cache["key2"] = test_dict2

    info = loader.get_cache_info()

    assert info["cached_dictionaries"] == 2
    assert "key1" in info["cache_keys"]
    assert "key2" in info["cache_keys"]


# ============================================================================
# ТЕСТЫ: Валидация колонок
# ============================================================================

def test_validate_columns_success():
    """Тест: успешная валидация колонок"""
    df = pd.DataFrame({
        "Col1": [1, 2],
        "Col2": [3, 4]
    })

    # Не должно быть исключений
    DictionaryLoader._validate_columns(df, ["Col1", "Col2"])


def test_validate_columns_missing():
    """Тест: отсутствующие колонки"""
    df = pd.DataFrame({
        "Col1": [1, 2]
    })

    with pytest.raises(ValueError, match="Отсутствуют обязательные колонки"):
        DictionaryLoader._validate_columns(df, ["Col1", "MissingCol"])


# ============================================================================
# ТЕСТЫ: Обработка ошибок
# ============================================================================

@patch('src.loaders.dictionary_loader.get_sheet_names')
@patch('src.loaders.dictionary_loader.load_excel')
def test_load_all_dictionaries_with_errors(mock_load_excel, mock_get_sheets, loader):
    """Тест: обработка ошибок при загрузке нескольких справочников"""
    mock_get_sheets.return_value = ["ValidSheet", "InvalidSheet"]

    # ValidSheet загружается нормально
    valid_df = pd.DataFrame({
        "Код": ["01"],
        "Значение": ["Test"]
    })

    # InvalidSheet вызывает ошибку
    def side_effect(*args, **kwargs):
        if kwargs.get('sheet_name') == "InvalidSheet":
            raise ValueError("Invalid sheet")
        return valid_df

    mock_load_excel.side_effect = side_effect

    dictionaries = loader.load_all_dictionaries(
        file_path=Path("test.xlsx")
    )

    # Должен загрузиться только ValidSheet
    assert len(dictionaries) == 1
    assert "ValidSheet" in dictionaries
