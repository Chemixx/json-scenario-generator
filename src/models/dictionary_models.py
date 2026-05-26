"""
Модели данных для справочников
"""
from dataclasses import dataclass, field as dataclass_field
from typing import List, Optional, Dict, Any
import random


# ============================================================================
# DATACLASS: Запись справочника
# ============================================================================

@dataclass
class DictionaryEntry:
    """
    Запись справочника

    Attributes:
        code: Код РКК (например, 10410001)
        name: Наименование значения (например, "PACL")
        dictionary_type: Тип справочника (например, "PRODUCT_TYPE")
        description: Описание (опционально)
        metadata: Дополнительные метаданные (опционально)
        english_localization: Английская локализация из prod-JSON (опционально)
        current_version: Флаг текущей версии (default: True)
        is_deleted: Флаг удаления (default: False)
        attributes: Атрибуты из prod-JSON (опционально)
        mappings: Маппинги из prod-JSON (опционально)

    Example:
        >>> entry = DictionaryEntry(
        ...     code=10410001,
        ...     name="PACL",
        ...     dictionary_type="PRODUCT_TYPE",
        ...     description="Потребительский кредит наличными"
        ... )
        >>> str(entry)
        'PACL (10410001)'
    """
    code: int
    name: str
    dictionary_type: str
    description: str = ""
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)
    english_localization: Optional[str] = None
    current_version: bool = True
    is_deleted: bool = False
    attributes: List[Dict[str, Any]] = dataclass_field(default_factory=list)
    mappings: List[Dict[str, Any]] = dataclass_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать запись в словарь

        Returns:
            Словарь с данными записи
        """
        result: Dict[str, Any] = {
            "code": self.code,
            "name": self.name,
            "dictionary_type": self.dictionary_type,
            "description": self.description,
            "metadata": self.metadata,
        }
        if self.english_localization is not None:
            result["english_localization"] = self.english_localization
        if not self.current_version:
            result["current_version"] = self.current_version
        if self.is_deleted:
            result["is_deleted"] = self.is_deleted
        if self.attributes:
            result["attributes"] = self.attributes
        if self.mappings:
            result["mappings"] = self.mappings
        return result

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def __repr__(self) -> str:
        return (
            f"DictionaryEntry(code={self.code}, "
            f"name='{self.name}', "
            f"type='{self.dictionary_type}')"
        )


# ============================================================================
# DATACLASS: Справочник
# ============================================================================

@dataclass
class Dictionary:
    """
    Справочник

    Attributes:
        name: Название справочника (например, "PRODUCT_TYPE")
        entries: Список записей справочника
        description: Описание справочника (опционально)
        _code_index: Хеш-индекс по коду для поиска O(1)
        _name_index: Хеш-индекс по названию для поиска O(1)
        _metadata: Метаданные справочника (опционально)

    Example:
        >>> dictionary = Dictionary(
        ...     name="PRODUCT_TYPE",
        ...     entries=[
        ...         DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE"),
        ...         DictionaryEntry(code=10410002, name="TOPUP", dictionary_type="PRODUCT_TYPE"),
        ...     ]
        ... )
        >>> entry = dictionary.get_by_code(10410001)
        >>> entry.name
        'PACL'
    """
    name: str
    entries: List[DictionaryEntry] = dataclass_field(default_factory=list)
    description: str = ""
    _code_index: Dict[int, DictionaryEntry] = dataclass_field(default_factory=dict, repr=False)
    _name_index: Dict[str, DictionaryEntry] = dataclass_field(default_factory=dict, repr=False)
    _metadata: Optional[Any] = None

    def __post_init__(self) -> None:
        """Построить индексы из начального списка entries."""
        for entry in self.entries:
            self._code_index[entry.code] = entry
            self._name_index[entry.name] = entry

    def get_by_code(self, code: int) -> Optional[DictionaryEntry]:
        """
        Получить запись по коду (O(1) через хеш-индекс)

        Args:
            code: Код РКК

        Returns:
            DictionaryEntry если найден, иначе None

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> entry = dictionary.get_by_code(10410001)
            >>> entry.name if entry else None
            'PACL'
        """
        return self._code_index.get(code)

    def get_by_name(self, name: str) -> Optional[DictionaryEntry]:
        """
        Получить запись по названию (O(1) через хеш-индекс)

        Args:
            name: Название значения

        Returns:
            DictionaryEntry если найден, иначе None

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> entry = dictionary.get_by_name("PACL")
            >>> entry.code if entry else None
            10410001
        """
        return self._name_index.get(name)

    def get_random(self) -> DictionaryEntry:
        """
        Получить случайную запись

        Returns:
            Случайная запись из справочника

        Raises:
            ValueError: Если справочник пустой

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> random_entry = dictionary.get_random()
            >>> random_entry.dictionary_type
            'PRODUCT_TYPE'
        """
        if not self.entries:
            raise ValueError(f"Справочник {self.name} пуст")
        return random.choice(self.entries)

    def get_all_codes(self) -> List[int]:
        """
        Получить список всех кодов

        Returns:
            Список кодов РКК

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> codes = dictionary.get_all_codes()
            >>> 10410001 in codes
            True
        """
        return [entry.code for entry in self.entries]

    def get_all_names(self) -> List[str]:
        """
        Получить список всех названий

        Returns:
            Список названий значений

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> names = dictionary.get_all_names()
            >>> 'PACL' in names
            True
        """
        return [entry.name for entry in self.entries]

    def size(self) -> int:
        """
        Получить количество записей в справочнике

        Returns:
            Количество записей
        """
        return len(self.entries)

    def is_empty(self) -> bool:
        """
        Проверка, пуст ли справочник

        Returns:
            True, если справочник пустой
        """
        return len(self.entries) == 0

    def add_entry(self, entry: DictionaryEntry) -> None:
        """
        Добавить запись в справочник (также обновляет хеш-индексы)

        Args:
            entry: Запись для добавления

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE")
            >>> entry = DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")
            >>> dictionary.add_entry(entry)
            >>> dictionary.size()
            1
        """
        self.entries.append(entry)
        self._code_index[entry.code] = entry
        self._name_index[entry.name] = entry

    def contains_code(self, code: int) -> bool:
        """
        Проверка наличия кода в справочнике

        Args:
            code: Код для проверки

        Returns:
            True, если код существует
        """
        return self.get_by_code(code) is not None

    def contains_name(self, name: str) -> bool:
        """
        Проверка наличия названия в справочнике

        Args:
            name: Название для проверки

        Returns:
            True, если название существует
        """
        return self.get_by_name(name) is not None

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать справочник в словарь

        Returns:
            Словарь с данными справочника
        """
        return {
            "name": self.name,
            "description": self.description,
            "size": self.size(),
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def __str__(self) -> str:
        return f"Dictionary(name='{self.name}', size={self.size()})"

    def __repr__(self) -> str:
        return f"Dictionary(name='{self.name}', entries={self.size()})"

    def __len__(self) -> int:
        """Поддержка len(dictionary)"""
        return self.size()

    def __iter__(self):
        """Поддержка итерации: for entry in dictionary"""
        return iter(self.entries)

    def __contains__(self, item) -> bool:
        """
        Поддержка оператора 'in'

        Example:
            >>> dictionary = Dictionary(name="PRODUCT_TYPE", entries=[...])
            >>> 10410001 in dictionary  # По коду
            True
            >>> "PACL" in dictionary  # По названию
            True
        """
        if isinstance(item, int):
            return self.contains_code(item)
        elif isinstance(item, str):
            return self.contains_name(item)
        elif isinstance(item, DictionaryEntry):
            return item in self.entries
        return False


# ============================================================================
# DATACLASS: Метаданные справочника
# ============================================================================

@dataclass
class DictionaryMetadata:
    """
    Метаданные справочника из секции dictionaries JSON-файла.

    Attributes:
        code: Код справочника (например, "PRODUCT_TYPE")
        name: Наименование справочника (например, "Тип продукта")
        dictionary_type_code: Код типа справочника (default: 1)
        subsystem: Код подсистемы (default: 0)
        hierarchical: Признак иерархического справочника (default: False)
        form_dict_flg: Признак форм-справочника (default: False)
        attribute_metadata: Метаданные атрибутов справочника

    Example:
        >>> meta = DictionaryMetadata(code="PRODUCT_TYPE", name="Тип продукта")
        >>> str(meta)
        'PRODUCT_TYPE: Тип продукта'
    """
    code: str
    name: str
    dictionary_type_code: int = 1
    subsystem: int = 0
    hierarchical: bool = False
    form_dict_flg: bool = False
    attribute_metadata: List[Dict[str, Any]] = dataclass_field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.code}: {self.name}"


# ============================================================================
# DATACLASS: Результат расшифровки кода
# ============================================================================

@dataclass
class ResolveResult:
    """
    Результат расшифровки кода справочника.

    Attributes:
        code: Код РКК (например, 10410001)
        name: Наименование значения (например, "PACL")
        dictionary_type: Тип справочника (например, "PRODUCT_TYPE")
        description: Описание (опционально)
        english_localization: Английская локализация (опционально)

    Example:
        >>> result = ResolveResult(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")
        >>> str(result)
        'PACL (10410001)'
        >>> result.format("{name} [{eng}]")
        'PACL []'
    """
    code: int
    name: str
    dictionary_type: str
    description: str = ""
    english_localization: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def format(self, fmt: str = "{name} ({code})") -> str:
        """
        Форматировать результат по шаблону.

        Args:
            fmt: Шаблон форматирования. Доступные плейсхолдеры:
                {name}, {code}, {description}, {eng}

        Returns:
            Отформатированная строка

        Example:
            >>> result = ResolveResult(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")
            >>> result.format("{name} [{code}]")
            'PACL [10410001]'
        """
        return fmt.format(
            name=self.name,
            code=self.code,
            description=self.description,
            eng=self.english_localization or "",
        )
