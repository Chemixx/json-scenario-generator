"""
Утилиты для работы с Excel
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# ЗАГРУЗКА EXCEL
# ============================================================================

def load_excel(
    file_path: Path,
    sheet_name: Optional[str] = None,
    header: int = 0
) -> pd.DataFrame:
    """
    Загрузить данные из Excel файла

    Args:
        file_path: Путь к Excel файлу
        sheet_name: Название листа (если None, загружается первый лист)
        header: Строка с заголовками (по умолчанию 0)

    Returns:
        DataFrame с данными

    Raises:
        FileNotFoundError: Если файл не найден

    Example:
        >>> df = load_excel(Path("data.xlsx"), sheet_name="Sheet1")
        >>> print(df.head())
    """
    if not file_path.exists():
        logger.error(f"❌ Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    try:
        sheet_info = f", лист: {sheet_name}" if sheet_name else ""
        logger.debug(f"📂 Загрузка Excel из {file_path.name}{sheet_info}")

        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header)

        logger.info(f"✅ Excel успешно загружен: {len(df)} строк")
        return df
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки Excel из {file_path}: {e}")
        raise


def get_sheet_names(file_path: Path) -> List[str]:
    """
    Получить список названий листов в Excel файле

    Args:
        file_path: Путь к Excel файлу

    Returns:
        Список названий листов

    Example:
        >>> sheets = get_sheet_names(Path("data.xlsx"))
        >>> print(sheets)
        ['Sheet1', 'Sheet2']
    """
    if not file_path.exists():
        logger.error(f"❌ Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        logger.debug(f"📋 Листы в {file_path.name}: {sheet_names}")
        return sheet_names
    except Exception as e:
        logger.error(f"❌ Ошибка чтения листов из {file_path}: {e}")
        raise


# ============================================================================
# ПРЕОБРАЗОВАНИЕ ДАННЫХ
# ============================================================================

def excel_to_dict(
    file_path: Path,
    sheet_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Преобразовать Excel в список словарей

    Args:
        file_path: Путь к Excel файлу
        sheet_name: Название листа

    Returns:
        Список словарей (каждая строка = словарь)

    Example:
        >>> data = excel_to_dict(Path("data.xlsx"))
        >>> print(data[0])
        {'column1': 'value1', 'column2': 'value2'}
    """
    df = load_excel(file_path, sheet_name=sheet_name)

    # Заменяем NaN на None
    df = df.where(pd.notna(df), None)

    records = df.to_dict(orient='records')
    logger.debug(f"📊 Преобразовано {len(records)} строк в словари")

    return records


def excel_to_json(
    file_path: Path,
    output_path: Path,
    sheet_name: Optional[str] = None,
    indent: int = 2
) -> None:
    """
    Преобразовать Excel в JSON файл

    Args:
        file_path: Путь к Excel файлу
        output_path: Путь к выходному JSON файлу
        sheet_name: Название листа
        indent: Отступ для JSON (по умолчанию 2)

    Example:
        >>> excel_to_json(Path("data.xlsx"), Path("output.json"))
    """
    import json

    data = excel_to_dict(file_path, sheet_name=sheet_name)

    # Создаем директорию, если её нет
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

    logger.info(f"✅ Excel преобразован в JSON: {output_path.name}")


# ============================================================================
# ФИЛЬТРАЦИЯ И ПОИСК
# ============================================================================

def filter_excel_by_column(
    file_path: Path,
    column_name: str,
    value: Any,
    sheet_name: Optional[str] = None
) -> pd.DataFrame:
    """
    Отфильтровать Excel по значению в колонке

    Args:
        file_path: Путь к Excel файлу
        column_name: Название колонки для фильтрации
        value: Значение для поиска
        sheet_name: Название листа

    Returns:
        Отфильтрованный DataFrame

    Example:
        >>> df = filter_excel_by_column(Path("data.xlsx"), "Status", "Active")
    """
    df = load_excel(file_path, sheet_name=sheet_name)

    if column_name not in df.columns:
        logger.error(f"❌ Колонка '{column_name}' не найдена в файле")
        raise ValueError(f"Колонка '{column_name}' не найдена")

    filtered = df[df[column_name] == value]
    logger.debug(f"🔍 Найдено {len(filtered)} строк с {column_name}='{value}'")

    return filtered


def get_unique_values(
    file_path: Path,
    column_name: str,
    sheet_name: Optional[str] = None
) -> List[Any]:
    """
    Получить уникальные значения из колонки

    Args:
        file_path: Путь к Excel файлу
        column_name: Название колонки
        sheet_name: Название листа

    Returns:
        Список уникальных значений

    Example:
        >>> values = get_unique_values(Path("data.xlsx"), "Category")
    """
    df = load_excel(file_path, sheet_name=sheet_name)

    if column_name not in df.columns:
        logger.error(f"❌ Колонка '{column_name}' не найдена в файле")
        raise ValueError(f"Колонка '{column_name}' не найдена")

    unique_values = df[column_name].dropna().unique().tolist()
    logger.debug(f"📊 Найдено {len(unique_values)} уникальных значений в '{column_name}'")

    return unique_values
