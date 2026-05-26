"""
Загрузчик справочников из JSON-файлов прод-формата.

Поддерживает формат файлов 1905.64_v1.json и 1905.65_v1_int.json:
{
    "dictionaries": [...],  // Метаданные справочников
    "elements": [...]       // Записи значений
}
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.models.dictionary_models import (
    Dictionary, DictionaryEntry, DictionaryMetadata
)
from src.utils.logger import get_logger
from src.utils.icons import Icon

logger = get_logger(__name__)


class JsonDictionaryLoader:
    """
    Загрузчик справочников из JSON-файлов прод-формата.

    Парсит файлы с секциями "dictionaries" (метаданные) и "elements" (записи).
    Поддерживает фильтрацию по deleted и currentVersion.
    """

    def __init__(self, logger=None):
        self.logger = logger or get_logger(self.__class__.__name__)

    def load(
        self,
        file_path: Path,
        filter_deleted: bool = True,
        filter_current: bool = True
    ) -> Tuple[Dict[str, Dictionary], Dict[str, DictionaryMetadata]]:
        """
        Загрузить все справочники из JSON-файла.

        Args:
            file_path: Путь к JSON-файлу
            filter_deleted: Фильтровать удалённые записи (default: True)
            filter_current: Фильтровать неактуальные записи (default: True)

        Returns:
            Кортеж (словари, метаданные)

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если JSON невалиден или нет обязательных секций
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Невалидный JSON в файле {file_path}: {e}")

        if "dictionaries" not in data:
            raise ValueError(f"Секция 'dictionaries' не найдена в {file_path}")
        if "elements" not in data:
            raise ValueError(f"Секция 'elements' не найдена в {file_path}")

        # Парсинг метаданных
        metadata = self._parse_metadata(data["dictionaries"])

        # Парсинг записей
        dictionaries = self._parse_elements(
            data["elements"],
            metadata,
            filter_deleted=filter_deleted,
            filter_current=filter_current
        )

        self.logger.info(
            f"{Icon.SUCCESS} Загружено {len(dictionaries)} справочников "
            f"из {file_path.name}"
        )

        return dictionaries, metadata

    def _parse_metadata(self, raw_dictionaries: List[Dict]) -> Dict[str, DictionaryMetadata]:
        """Парсинг секции dictionaries -> DictionaryMetadata"""
        result = {}
        for raw in raw_dictionaries:
            meta = DictionaryMetadata(
                code=raw.get("code", ""),
                name=raw.get("name", ""),
                dictionary_type_code=raw.get("dictionaryTypeCode", 1),
                subsystem=raw.get("subsystem", 0),
                hierarchical=raw.get("hierarchical", False),
                form_dict_flg=raw.get("formDictFlg", False),
                attribute_metadata=raw.get("attributeMetadataList", []),
            )
            result[meta.code] = meta
        return result

    def _parse_elements(
        self,
        raw_elements: List[Dict],
        metadata: Dict[str, DictionaryMetadata],
        filter_deleted: bool = True,
        filter_current: bool = True
    ) -> Dict[str, Dictionary]:
        """Парсинг секции elements -> Dictionary"""
        grouped: Dict[str, List[DictionaryEntry]] = {}

        for raw in raw_elements:
            # Фильтрация
            if filter_deleted and raw.get("deleted", False):
                continue
            if filter_current and not raw.get("currentVersion", True):
                continue

            dict_code = raw.get("dictionaryCode", "")
            entry = DictionaryEntry(
                code=raw.get("canonicalCode", 0),
                name=raw.get("name", ""),
                dictionary_type=dict_code,
                description=raw.get("description", ""),
                english_localization=raw.get("englishLocalization"),
                current_version=raw.get("currentVersion", True),
                is_deleted=raw.get("deleted", False),
                attributes=raw.get("attributes", []),
                mappings=raw.get("mappings", []),
            )

            if dict_code not in grouped:
                grouped[dict_code] = []
            grouped[dict_code].append(entry)

        # Создание Dictionary объектов
        dictionaries = {}
        for dict_code, entries in grouped.items():
            dict_name = dict_code
            dict_description = ""
            if dict_code in metadata:
                dict_description = metadata[dict_code].name

            dictionary = Dictionary(name=dict_name, description=dict_description)
            for entry in entries:
                dictionary.add_entry(entry)
            dictionaries[dict_name] = dictionary

        return dictionaries