"""
Модели данных для JSON-сценариев
"""
from dataclasses import dataclass, field as dataclass_field
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


# ============================================================================
# DATACLASS: Метаданные сценария
# ============================================================================

@dataclass
class ScenarioMetadata:
    """
    Метаданные JSON-сценария

    Attributes:
        name: Название сценария
        version: Версия контракта (например, "072")
        call: Тип Call'а (например, "Call1")
        adapter: Название адаптера (например, "front-adapter")
        created_at: Время создания
        updated_at: Время последнего обновления
        source_file: Путь к исходному файлу
        description: Описание сценария
        tags: Теги для поиска

    Example:
        >>> metadata = ScenarioMetadata(
        ...     name="Call1_v072_КН_success",
        ...     version="072",
        ...     call="Call1",
        ...     description="Успешный сценарий для КН"
        ... )
        >>> str(metadata)
        'Call1_v072_КН_success (v072, Call1)'
    """
    name: str
    version: str
    call: str
    adapter: str = "front-adapter"
    created_at: datetime = dataclass_field(default_factory=datetime.now)
    updated_at: datetime = dataclass_field(default_factory=datetime.now)
    source_file: Optional[Path] = None
    description: str = ""
    tags: List[str] = dataclass_field(default_factory=list)

    def add_tag(self, tag: str) -> None:
        """
        Добавить тег

        Args:
            tag: Тег для добавления
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        """
        Проверка наличия тега

        Args:
            tag: Тег для проверки

        Returns:
            True, если тег существует
        """
        return tag in self.tags

    def update_timestamp(self) -> None:
        """Обновить timestamp последнего изменения"""
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразовать метаданные в словарь

        Returns:
            Словарь с метаданными
        """
        return {
            "name": self.name,
            "version": self.version,
            "call": self.call,
            "adapter": self.adapter,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_file": str(self.source_file) if self.source_file else None,
            "description": self.description,
            "tags": self.tags,
        }

    def __str__(self) -> str:
        return f"{self.name} (v{self.version}, {self.call})"

    def __repr__(self) -> str:
        return (
            f"ScenarioMetadata(name='{self.name}', "
            f"version='{self.version}', "
            f"call='{self.call}')"
        )


# ============================================================================
# DATACLASS: JSON-сценарий
# ============================================================================

@dataclass
class Scenario:
    """
    JSON-сценарий для тестирования

    Attributes:
        metadata: Метаданные сценария
        data: JSON-данные сценария

    Example:
        >>> scenario = Scenario(
        ...     metadata=ScenarioMetadata(
        ...         name="test_scenario",
        ...         version="072",
        ...         call="Call1"
        ...     ),
        ...     data={"loanRequest": {"creditAmt": 100000}}
        ... )
        >>> scenario.get_field_value("loanRequest/creditAmt")
        100000
    """
    metadata: ScenarioMetadata
    data: Dict[str, Any]

    def get_field_value(self, path: str) -> Any:
        """
        Получить значение поля по пути

        Args:
            path: Путь к полю (например, "loanRequest/creditAmt")

        Returns:
            Значение поля

        Raises:
            KeyError: Если поле не найдено
            IndexError: Если индекс массива вне диапазона

        Example:
            >>> scenario = Scenario(metadata=..., data={"loanRequest": {"creditAmt": 100000}})
            >>> scenario.get_field_value("loanRequest/creditAmt")
            100000
        """
        parts = path.split("/")
        current = self.data

        for part in parts:
            # Обработка массивов: "items[0]"
            if "[" in part and "]" in part:
                key, index_str = part.split("[")
                index = int(index_str.rstrip("]"))
                current = current[key][index]
            else:
                current = current[part]

        return current

    def set_field_value(self, path: str, value: Any) -> None:
        """
        Установить значение поля по пути

        Args:
            path: Путь к полю
            value: Новое значение

        Example:
            >>> scenario = Scenario(metadata=..., data={})
            >>> scenario.set_field_value("loanRequest/creditAmt", 100000)
            >>> scenario.data
            {'loanRequest': {'creditAmt': 100000}}
        """
        parts = path.split("/")
        current = self.data

        # Проходим до предпоследнего элемента
        for part in parts[:-1]:
            if "[" in part and "]" in part:
                key, index_str = part.split("[")
                index = int(index_str.rstrip("]"))

                # Создаем массив, если его нет
                if key not in current:
                    current[key] = []

                # Расширяем массив при необходимости
                while len(current[key]) <= index:
                    current[key].append({})

                current = current[key][index]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Устанавливаем значение
        last_part = parts[-1]
        if "[" in last_part and "]" in last_part:
            key, index_str = last_part.split("[")
            index = int(index_str.rstrip("]"))

            if key not in current:
                current[key] = []

            while len(current[key]) <= index:
                current[key].append(None)

            current[key][index] = value
        else:
            current[last_part] = value

        # Обновляем timestamp
        self.metadata.update_timestamp()

    def has_field(self, path: str) -> bool:
        """
        Проверка наличия поля по пути

        Args:
            path: Путь к полю

        Returns:
            True, если поле существует

        Example:
            >>> scenario = Scenario(metadata=..., data={"loanRequest": {"creditAmt": 100000}})
            >>> scenario.has_field("loanRequest/creditAmt")
            True
            >>> scenario.has_field("loanRequest/nonExistentField")
            False
        """
        try:
            self.get_field_value(path)
            return True
        except (KeyError, IndexError, TypeError):
            return False

    def delete_field(self, path: str) -> bool:
        """
        Удалить поле по пути

        Args:
            path: Путь к полю

        Returns:
            True, если поле было удалено

        Example:
            >>> scenario = Scenario(metadata=..., data={"loanRequest": {"creditAmt": 100000}})
            >>> scenario.delete_field("loanRequest/creditAmt")
            True
            >>> scenario.has_field("loanRequest/creditAmt")
            False
        """
        if not self.has_field(path):
            return False

        parts = path.split("/")
        current = self.data

        # Проходим до предпоследнего элемента
        for part in parts[:-1]:
            if "[" in part and "]" in part:
                key, index_str = part.split("[")
                index = int(index_str.rstrip("]"))
                current = current[key][index]
            else:
                current = current[part]

        # Удаляем последний элемент
        last_part = parts[-1]
        if "[" in last_part and "]" in last_part:
            key, index_str = last_part.split("[")
            index = int(index_str.rstrip("]"))
            del current[key][index]
        else:
            del current[last_part]

        self.metadata.update_timestamp()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Получить JSON-данные сценария

        Returns:
            Словарь с данными сценария
        """
        return self.data.copy()

    def to_full_dict(self) -> Dict[str, Any]:
        """
        Получить полные данные сценария (метаданные + данные)

        Returns:
            Словарь с метаданными и данными
        """
        return {
            "metadata": self.metadata.to_dict(),
            "data": self.data,
        }

    def __str__(self) -> str:
        return f"Scenario({self.metadata.name})"

    def __repr__(self) -> str:
        return (
            f"Scenario(name='{self.metadata.name}', "
            f"version='{self.metadata.version}')"
        )
