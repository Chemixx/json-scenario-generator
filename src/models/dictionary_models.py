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

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать запись в словарь

        Returns:
            Словарь с данными записи
        """
        return {
            "code": self.code,
            "name": self.name,
            "dictionary_type": self.dictionary_type,
            "description": self.description,
            "metadata": self.metadata,
        }

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

    def get_by_code(self, code: int) -> Optional[DictionaryEntry]:
        """
        Получить запись по коду

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
        for entry in self.entries:
            if entry.code == code:
                return entry
        return None

    def get_by_name(self, name: str) -> Optional[DictionaryEntry]:
        """
        Получить запись по названию

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
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

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
        Добавить запись в справочник

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
