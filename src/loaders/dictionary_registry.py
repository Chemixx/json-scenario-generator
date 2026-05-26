"""
Центральное хранилище справочников с O(1) поиском по коду и названию.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.models.dictionary_models import (
    Dictionary,
    DictionaryEntry,
    DictionaryMetadata,
    ResolveResult,
)
from src.utils.icons import Icon
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DictionaryRegistry:
    """Центральное хранилище справочников с O(1) поиском по коду и названию."""

    def __init__(self) -> None:
        self._dictionaries: Dict[str, Dictionary] = {}
        self._metadata: Dict[str, DictionaryMetadata] = {}

    def register(
        self,
        dictionary: Dictionary,
        metadata: Optional[DictionaryMetadata] = None,
    ) -> None:
        """Зарегистрировать справочник. Ключ = dictionary.name.

        Args:
            dictionary: Справочник для регистрации.
            metadata: Метаданные справочника (опционально).
        """
        name = dictionary.name
        self._dictionaries[name] = dictionary
        if metadata is not None:
            self._metadata[name] = metadata
        logger.info(
            f"{Icon.SUCCESS} Справочник '{name}' зарегистрирован: "
            f"{dictionary.size()} записей"
        )

    def get(self, name: str) -> Optional[Dictionary]:
        """Получить справочник по имени. O(1).

        Args:
            name: Название справочника.

        Returns:
            Справочник если найден, иначе None.
        """
        return self._dictionaries.get(name)

    def get_entry(self, dict_name: str, code: int) -> Optional[DictionaryEntry]:
        """Получить запись по коду. O(1) через хэш-индекс.

        Args:
            dict_name: Название справочника.
            code: Код записи.

        Returns:
            Запись если найдена, иначе None.
        """
        dictionary = self._dictionaries.get(dict_name)
        if dictionary is None:
            return None
        return dictionary.get_by_code(code)

    def get_entry_by_name(
        self, dict_name: str, name: str
    ) -> Optional[DictionaryEntry]:
        """Получить запись по названию. O(1) через хэш-индекс.

        Args:
            dict_name: Название справочника.
            name: Название записи.

        Returns:
            Запись если найдена, иначе None.
        """
        dictionary = self._dictionaries.get(dict_name)
        if dictionary is None:
            return None
        return dictionary.get_by_name(name)

    def resolve(
        self, dict_name: str, code: int, fmt: str = "{name} ({code})"
    ) -> str:
        """Расшифровать код справочника в человекочитаемый формат.

        Fallback: 'Неизвестный ({code})' если не найден.

        Args:
            dict_name: Название справочника.
            code: Код записи.
            fmt: Шаблон форматирования.

        Returns:
            Отформатированная строка или fallback.
        """
        entry = self.get_entry(dict_name, code)
        if entry is not None:
            result = ResolveResult(
                code=entry.code,
                name=entry.name,
                dictionary_type=entry.dictionary_type,
                description=entry.description,
                english_localization=entry.english_localization,
            )
            return result.format(fmt)
        return f"Неизвестный ({code})"

    def resolve_name(self, dict_name: str, code: int) -> Optional[str]:
        """Получить только название по коду.

        Args:
            dict_name: Название справочника.
            code: Код записи.

        Returns:
            Название записи или None.
        """
        entry = self.get_entry(dict_name, code)
        return entry.name if entry else None

    def is_valid_value(self, dict_name: str, value: Any) -> bool:
        """Проверить, есть ли значение в справочнике.

        Проверяет по code (int) и по name (str).
        Fallback: True если справочник не загружен.

        Args:
            dict_name: Название справочника.
            value: Значение для проверки (код или название).

        Returns:
            True если значение валидно или справочник не загружен.
        """
        dictionary = self._dictionaries.get(dict_name)
        if dictionary is None:
            logger.debug(
                f"is_valid_value: справочник '{dict_name}' не загружен, пропускаем"
            )
            return True
        # Проверка по числовому коду
        try:
            code_int = int(value)
            if dictionary.contains_code(code_int):
                return True
        except (ValueError, TypeError):
            pass
        # Проверка по строковому названию
        if isinstance(value, str) and dictionary.contains_name(value):
            return True
        return False

    def list_dictionaries(self) -> List[str]:
        """Список имён загруженных справочников.

        Returns:
            Список названий справочников.
        """
        return list(self._dictionaries.keys())

    def get_metadata(self, name: str) -> Optional[DictionaryMetadata]:
        """Получить метаданные справочника.

        Args:
            name: Название справочника.

        Returns:
            Метаданные если найдены, иначе None.
        """
        return self._metadata.get(name)

    def clear(self) -> None:
        """Очистить все справочники и метаданные."""
        self._dictionaries.clear()
        self._metadata.clear()
        logger.info(f"{Icon.DELETE} Registry очищен")

    def load_from_json(
        self,
        file_path: Path,
        filter_deleted: bool = True,
        filter_current: bool = True,
    ) -> Dict[str, Dictionary]:
        """Загрузить все справочники из JSON-файла (прод-формат).

        Args:
            file_path: Путь к JSON-файлу.
            filter_deleted: Фильтровать удалённые записи.
            filter_current: Фильтровать по current_version.

        Returns:
            Словарь загруженных справочников.
        """
        from src.loaders.json_dictionary_loader import JsonDictionaryLoader

        loader = JsonDictionaryLoader(logger=self._get_logger())
        dictionaries, metadata = loader.load(
            file_path,
            filter_deleted=filter_deleted,
            filter_current=filter_current,
        )
        for name, dictionary in dictionaries.items():
            self.register(dictionary, metadata=metadata.get(name))
        return dictionaries

    def load_from_excel(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Dictionary]:
        """Загрузить справочники из Excel через DictionaryLoader.

        Args:
            file_path: Путь к Excel-файлу.
            sheet_name: Имя листа (опционально, иначе все листы).
            **kwargs: Дополнительные параметры загрузчика.

        Returns:
            Словарь загруженных справочников.
        """
        from src.loaders.dictionary_loader import DictionaryLoader

        loader = DictionaryLoader()
        if sheet_name:
            result = {
                sheet_name: loader.load_dictionary(
                    file_path, sheet_name=sheet_name, **kwargs
                )
            }
        else:
            result = loader.load_all_dictionaries(file_path, **kwargs)
        for name, dictionary in result.items():
            self.register(dictionary)
        return result

    def _get_logger(self):
        """Получить логгер для делегирования загрузчикам.

        Returns:
            Логгер модуля.
        """
        return logger

    def __len__(self) -> int:
        return len(self._dictionaries)

    def __contains__(self, name: str) -> bool:
        return name in self._dictionaries