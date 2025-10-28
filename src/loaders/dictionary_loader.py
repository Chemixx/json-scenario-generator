"""
Загрузчик справочников из Excel файлов
Парсит файлы со справочниками и преобразует их в Dictionary модели
"""
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from src.models.dictionary_models import Dictionary, DictionaryEntry
from src.utils.excel_utils import load_excel, get_sheet_names
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DictionaryLoader:
    """
    Загрузчик справочников из Excel файлов

    Поддерживает два формата:
    1. Классический: один лист = один справочник (load_dictionary)
    2. Групповой: несколько справочников в одном листе (load_dictionary_by_code)

    Example:
        .. code-block:: python

            loader = DictionaryLoader()

            # Формат 1: один справочник на листе
            dict1 = loader.load_dictionary(
                file_path=Path("data.xlsx"),
                sheet_name="STATUS"
            )

            # Формат 2: несколько справочников в листе
            dict2 = loader.load_dictionary_by_code(
                file_path=Path("dictionaries.xlsx"),
                sheet_name="All",
                dictionary_code="CUSTOMER_FLAG"
            )
    """

    def __init__(self):
        """Инициализация загрузчика"""
        self.logger = get_logger(self.__class__.__name__)
        self._cache: Dict[str, Dictionary] = {}

    # ========================================================================
    # ФОРМАТ 1: Классический (один лист = один справочник)
    # ========================================================================

    def load_dictionary(
            self,
            file_path: Path,
            sheet_name: str,
            code_column: str = "Код",
            name_column: str = "Значение",
            description_column: Optional[str] = None,
            skip_rows: int = 0
    ) -> Dictionary:
        """
        Загрузить справочник из Excel файла (классический формат)

        Формат: один лист = один справочник
        Колонки: Код | Значение | Описание (опционально)

        Args:
            file_path: Путь к Excel файлу
            sheet_name: Название листа со справочником
            code_column: Название колонки с кодами
            name_column: Название колонки с значениями
            description_column: Название колонки с описаниями (опционально)
            skip_rows: Количество строк для пропуска (заголовки)

        Returns:
            Dictionary с загруженными данными

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если лист или колонки не найдены

        Example:
            .. code-block:: python

                loader = DictionaryLoader()
                dictionary = loader.load_dictionary(
                    file_path=Path("data.xlsx"),
                    sheet_name="Statuses",
                    code_column="Code",
                    name_column="Name"
                )
        """
        cache_key = f"{file_path.name}:{sheet_name}"

        # Проверяем кэш
        if cache_key in self._cache:
            self.logger.info(f"📦 Справочник '{sheet_name}' загружен из кэша")
            return self._cache[cache_key]

        self.logger.info(f"📂 Загрузка справочника '{sheet_name}' из {file_path.name}")

        # Загружаем Excel
        df = load_excel(file_path, sheet_name=sheet_name, header=skip_rows)

        # Проверяем наличие обязательных колонок
        self._validate_columns(df, [code_column, name_column])

        # Создаем Dictionary
        dictionary = Dictionary(name=sheet_name, description=f"Справочник из {file_path.name}")

        # Парсим строки
        for _, row in df.iterrows():
            code = row.get(code_column)
            name = row.get(name_column)

            # Пропускаем пустые строки
            if pd.isna(code) or pd.isna(name):
                continue

            # Преобразуем типы
            code = str(code).strip()
            name = str(name).strip()

            # Извлекаем описание (если есть)
            description = None
            if description_column and description_column in df.columns:
                desc_value = row.get(description_column)
                if not pd.isna(desc_value):
                    description = str(desc_value).strip()

            # Создаем запись
            entry = DictionaryEntry(
                code=code,
                name=name,
                dictionary_type=sheet_name,
                description=description
            )

            dictionary.add_entry(entry)

        self.logger.info(f"✅ Справочник '{sheet_name}' загружен: {len(dictionary)} записей")

        # Кэшируем
        self._cache[cache_key] = dictionary

        return dictionary

    def load_all_dictionaries(
            self,
            file_path: Path,
            code_column: str = "Код",
            name_column: str = "Значение",
            description_column: Optional[str] = None,
            skip_rows: int = 0,
            exclude_sheets: Optional[List[str]] = None
    ) -> Dict[str, Dictionary]:
        """
        Загрузить все справочники из файла (классический формат)

        Каждый лист = отдельный справочник

        Args:
            file_path: Путь к Excel файлу
            code_column: Название колонки с кодами
            name_column: Название колонки с значениями
            description_column: Название колонки с описаниями
            skip_rows: Количество строк для пропуска
            exclude_sheets: Список листов для исключения

        Returns:
            Словарь {название_листа: Dictionary}

        Example:
            .. code-block:: python

                loader = DictionaryLoader()
                dictionaries = loader.load_all_dictionaries(
                    file_path=Path("all_dicts.xlsx"),
                    exclude_sheets=["Legend", "Info"]
                )
        """
        if exclude_sheets is None:
            exclude_sheets = []

        self.logger.info(f"📚 Загрузка всех справочников из {file_path.name}")

        sheet_names = get_sheet_names(file_path)
        dictionaries = {}

        for sheet_name in sheet_names:
            if sheet_name in exclude_sheets:
                self.logger.debug(f"⏭️  Пропуск листа '{sheet_name}' (в exclude_sheets)")
                continue

            try:
                dictionary = self.load_dictionary(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    code_column=code_column,
                    name_column=name_column,
                    description_column=description_column,
                    skip_rows=skip_rows
                )
                dictionaries[sheet_name] = dictionary
            except Exception as e:
                self.logger.warning(f"⚠️  Не удалось загрузить лист '{sheet_name}': {e}")
                continue

        self.logger.info(f"✅ Загружено {len(dictionaries)} справочников")
        return dictionaries

    # ========================================================================
    # ФОРМАТ 2: Групповой (несколько справочников в одном листе)
    # ========================================================================

    def load_dictionary_by_code(
            self,
            file_path: Path,
            sheet_name: str,
            dictionary_code: str,
            dictionary_code_column: str = "Код справочника",
            value_code_column: str = "Код РКК",
            value_name_column: str = "Наименование значения",
            skip_rows: int = 0
    ) -> Dictionary:
        """
        Загрузить конкретный справочник по коду (групповой формат)

        Формат: несколько справочников в одном листе
        Каждая строка имеет колонку "Код справочника" (например, "CUSTOMER_FLAG")

        Args:
            file_path: Путь к Excel файлу
            sheet_name: Название листа
            dictionary_code: Код справочника (например, "CUSTOMER_FLAG")
            dictionary_code_column: Колонка с кодом справочника
            value_code_column: Колонка с кодами значений
            value_name_column: Колонка с названиями значений
            skip_rows: Количество строк для пропуска

        Returns:
            Dictionary с записями для указанного справочника

        Example:
            .. code-block:: python

                loader = DictionaryLoader()
                customer_flag = loader.load_dictionary_by_code(
                    file_path=Path("dictionaries.xlsx"),
                    sheet_name="All",
                    dictionary_code="CUSTOMER_FLAG"
                )
        """
        cache_key = f"{file_path.name}:{sheet_name}:{dictionary_code}"

        # Проверяем кэш
        if cache_key in self._cache:
            self.logger.info(f"📦 Справочник '{dictionary_code}' загружен из кэша")
            return self._cache[cache_key]

        self.logger.info(f"📂 Загрузка справочника '{dictionary_code}' из {file_path.name}")

        # Загружаем Excel
        df = load_excel(file_path, sheet_name=sheet_name, header=skip_rows)

        # Проверяем наличие обязательных колонок
        required_cols = [dictionary_code_column, value_code_column, value_name_column]
        self._validate_columns(df, required_cols)

        # Фильтруем по коду справочника
        filtered_df = df[df[dictionary_code_column] == dictionary_code]

        if filtered_df.empty:
            self.logger.warning(f"⚠️  Справочник '{dictionary_code}' не найден в листе '{sheet_name}'")
            return Dictionary(name=dictionary_code, description=f"Пустой справочник {dictionary_code}")

        # Создаем Dictionary
        dictionary = Dictionary(
            name=dictionary_code,
            description=f"Справочник {dictionary_code} из {file_path.name}"
        )

        # Парсим строки
        for _, row in filtered_df.iterrows():
            code = row.get(value_code_column)
            name = row.get(value_name_column)

            # Пропускаем пустые строки
            if pd.isna(code) or pd.isna(name):
                continue

            # Преобразуем типы
            code = str(code).strip()
            name = str(name).strip()

            # Создаем запись
            entry = DictionaryEntry(
                code=code,
                name=name,
                dictionary_type=dictionary_code
            )
            dictionary.add_entry(entry)

        self.logger.info(f"✅ Справочник '{dictionary_code}' загружен: {len(dictionary)} записей")

        # Кэшируем
        self._cache[cache_key] = dictionary

        return dictionary

    def load_all_dictionaries_from_sheet(
            self,
            file_path: Path,
            sheet_name: str,
            dictionary_code_column: str = "Код справочника",
            value_code_column: str = "Код РКК",
            value_name_column: str = "Наименование значения",
            skip_rows: int = 0
    ) -> Dict[str, Dictionary]:
        """
        Загрузить все справочники из одного листа (групповой формат)

        Автоматически находит все уникальные коды справочников и загружает их

        Args:
            file_path: Путь к Excel файлу
            sheet_name: Название листа
            dictionary_code_column: Колонка с кодом справочника
            value_code_column: Колонка с кодами значений
            value_name_column: Колонка с названиями значений
            skip_rows: Количество строк для пропуска

        Returns:
            Словарь {код_справочника: Dictionary}

        Example:
            .. code-block:: python

                loader = DictionaryLoader()
                all_dicts = loader.load_all_dictionaries_from_sheet(
                    file_path=Path("dictionaries.xlsx"),
                    sheet_name="All"
                )
                print(f"Loaded {len(all_dicts)} dictionaries")
        """
        self.logger.info(f"📚 Загрузка всех справочников из листа '{sheet_name}'")

        # Загружаем Excel
        df = load_excel(file_path, sheet_name=sheet_name, header=skip_rows)

        # Проверяем колонки
        required_cols = [dictionary_code_column, value_code_column, value_name_column]
        self._validate_columns(df, required_cols)

        # Находим уникальные коды справочников
        unique_codes = df[dictionary_code_column].dropna().unique()

        self.logger.info(f"📋 Найдено {len(unique_codes)} справочников: {list(unique_codes)[:5]}...")

        dictionaries = {}

        for dict_code in unique_codes:
            dict_code_str = str(dict_code).strip()

            try:
                dictionary = self.load_dictionary_by_code(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    dictionary_code=dict_code_str,
                    dictionary_code_column=dictionary_code_column,
                    value_code_column=value_code_column,
                    value_name_column=value_name_column,
                    skip_rows=skip_rows
                )
                dictionaries[dict_code_str] = dictionary
            except Exception as e:
                self.logger.warning(f"⚠️  Не удалось загрузить справочник '{dict_code_str}': {e}")
                continue

        self.logger.info(f"✅ Загружено {len(dictionaries)} справочников")
        return dictionaries

    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================

    def get_cached_dictionary(self, cache_key: str) -> Optional[Dictionary]:
        """
        Получить справочник из кэша

        Args:
            cache_key: Ключ кэша

        Returns:
            Dictionary или None, если не найдено
        """
        return self._cache.get(cache_key)

    def clear_cache(self):
        """Очистить кэш справочников"""
        self.logger.info("🗑️  Очистка кэша справочников")
        self._cache.clear()

    def get_cache_info(self) -> Dict[str, int]:
        """
        Получить информацию о кэше

        Returns:
            Словарь с информацией о кэше
        """
        return {
            "cached_dictionaries": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }

    @staticmethod
    def _validate_columns(df: pd.DataFrame, required_columns: List[str]):
        """
        Проверить наличие обязательных колонок

        Args:
            df: DataFrame для проверки
            required_columns: Список обязательных колонок

        Raises:
            ValueError: Если какая-то колонка отсутствует
        """
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            available = list(df.columns)
            raise ValueError(
                f"Отсутствуют обязательные колонки: {missing_columns}. "
                f"Доступные колонки: {available}"
            )
