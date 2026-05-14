"""
Генератор значений для полей JSON Schema.

Генерирует тестовые значения на основе метаданных поля (FieldMetadata),
конфигурации (GeneratorConfig) и справочников (DictionaryLoader).
"""
from dataclasses import dataclass, field as dataclass_field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
import random
import re
import uuid as uuid_module

from faker import Faker

from src.models.schema_models import FieldMetadata
from src.models.dictionary_models import Dictionary
from src.loaders.dictionary_loader import DictionaryLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratorConfig:
    """
    Конфигурация генератора значений.

    Attributes:
        locale: Локаль для Faker (по умолчанию ru_RU).
        seed: Сид для воспроизводимости случайных значений.
        default_array_size: Количество элементов в массиве по умолчанию.
        faker: Готовый экземпляр Faker (если None, создается из locale).
        uuid_cache: Внешний кэш UUID (ключ = имя поля).
        strict_inn: Генерировать ИНН с валидной контрольной суммой ФНС.
        strict_snils: Генерировать СНИЛС с контрольной суммой (пока не используется).
    """
    locale: str = "ru_RU"
    seed: Optional[int] = None
    default_array_size: int = 1
    faker: Optional[Faker] = None
    uuid_cache: Dict[str, str] = dataclass_field(default_factory=dict)
    strict_inn: bool = True
    strict_snils: bool = False


class ValueGenerator:
    """
    Генератор значений для leaf-полей JSON Schema.

    Генерирует скалярные значения (string, integer, number, boolean),
    а также массивы и специальные форматы (uuid, date, ИНН, СНИЛС и т.д.).

    Note:
        Генерация вложенных объектов (field_type == "object") не поддерживается
        и вызывает ValueError.
    """

    def __init__(
        self,
        config: Optional[GeneratorConfig] = None,
        dictionary_loader: Optional[DictionaryLoader] = None,
    ) -> None:
        self.config = config or GeneratorConfig()
        self.dictionary_loader = dictionary_loader
        self._random = random.Random()
        if self.config.seed is not None:
            self._random.seed(self.config.seed)
        self._faker = self.config.faker or Faker(self.config.locale)
        if self.config.seed is not None:
            self._faker.seed_instance(self.config.seed)

    def generate(self, field_meta: FieldMetadata) -> Any:
        """
        Генерирует значение для одного leaf-поля.

        Args:
            field_meta: Метаданные поля из JSON Schema.

        Returns:
            Сгенерированное значение (тип зависит от field_type).

        Raises:
            ValueError: Если тип поля не поддерживается или это object.
        """
        if field_meta.field_type == "object":
            raise ValueError("Генерация вложенных объектов (object) не поддерживается")

        # Приоритет: default > dictionary > array > scalar
        if field_meta.default is not None:
            return field_meta.default

        if field_meta.dictionary and self.dictionary_loader:
            return self._generate_from_dictionary(field_meta)

        if field_meta.field_type == "array":
            return self._generate_array(field_meta)

        generator_name = f"_generate_{field_meta.field_type}"
        generator_method = getattr(self, generator_name, None)
        if generator_method is None:
            raise ValueError(f"Неподдерживаемый тип поля: {field_meta.field_type}")

        return generator_method(field_meta)

    def _generate_string(self, field_meta: FieldMetadata) -> str:
        """Генерация строкового значения."""
        fmt = field_meta.format
        if fmt == "uuid":
            return self._generate_uuid(field_meta)
        if fmt == "date":
            return self._faker.date(pattern="%Y-%m-%d")
        if fmt == "date-time":
            dt = self._faker.date_time()
            return dt.isoformat(timespec="milliseconds")
        if fmt == "email":
            return self._faker.email()

        constraints = field_meta.constraints

        # enum имеет приоритет
        enum_values = constraints.get("enum")
        if enum_values:
            return self._random.choice(enum_values)

        # pattern
        pattern = constraints.get("pattern")
        if pattern:
            return self._generate_from_pattern(pattern)

        # Специальные бизнес-форматы
        if fmt == "inn":
            inn_length = constraints.get("inn_length", 10)
            return self._generate_inn(inn_length, self.config.strict_inn)
        if fmt == "snils":
            return self._generate_snils(self.config.strict_snils)
        if fmt == "phone":
            return self._generate_phone()

        # Обычная строка
        max_length = field_meta.get_max_length()
        min_length = field_meta.get_min_length() or 1
        if max_length is not None:
            target_length = self._random.randint(min_length, max_length)
        else:
            target_length = self._random.randint(min_length, 20)

        parts: List[str] = []
        current_len = 0
        while current_len < target_length:
            word = self._faker.word()
            parts.append(word)
            current_len += len(word)
        return "".join(parts)[:target_length]

    def _generate_integer(self, field_meta: FieldMetadata) -> int:
        """Генерация целого числа."""
        constraints = field_meta.constraints
        minimum = constraints.get("minimum")
        maximum = constraints.get("maximum")
        if minimum is not None and maximum is not None:
            return self._random.randint(int(minimum), int(maximum))
        if minimum is not None:
            return self._random.randint(int(minimum), int(minimum) + 1000)
        if maximum is not None:
            return self._random.randint(int(maximum) - 1000, int(maximum))
        return self._random.randint(1, 1000)

    def _generate_number(self, field_meta: FieldMetadata) -> Decimal:
        """Генерация числа с плавающей точкой (с фиксированной дробной частью)."""
        constraints = field_meta.constraints
        minimum = constraints.get("minimum")
        maximum = constraints.get("maximum")
        fraction = constraints.get("fraction", 5)

        if minimum is not None and maximum is not None:
            value = self._random.uniform(float(minimum), float(maximum))
        elif minimum is not None:
            value = self._random.uniform(float(minimum), float(minimum) + 1000.0)
        elif maximum is not None:
            value = self._random.uniform(float(maximum) - 1000.0, float(maximum))
        else:
            value = self._random.uniform(1.0, 1000.0)

        quantizer = Decimal(1) / (Decimal(10) ** fraction)
        decimal_value = Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)
        return decimal_value

    def _generate_boolean(self, field_meta: FieldMetadata) -> bool:
        """Генерация булева значения."""
        return self._random.choice([True, False])

    def _generate_array(self, field_meta: FieldMetadata) -> List[Any]:
        """Генерация массива (списка) значений."""
        constraints = field_meta.constraints
        min_items = constraints.get("minItems", 0)
        max_items = constraints.get("maxItems")
        size = max(min_items, self.config.default_array_size)
        if max_items is not None:
            size = min(size, max_items)

        if field_meta.items is None:
            return []

        result: List[Any] = []
        for _ in range(size):
            result.append(self.generate(field_meta.items))
        return result

    def _generate_uuid(self, field_meta: FieldMetadata) -> str:
        """Генерация UUID с внешним кэшированием."""
        cache_key = field_meta.name
        if cache_key in self.config.uuid_cache:
            return self.config.uuid_cache[cache_key]
        new_uuid = str(uuid_module.uuid4())
        self.config.uuid_cache[cache_key] = new_uuid
        return new_uuid

    def _generate_from_dictionary(self, field_meta: FieldMetadata) -> str:
        """Генерация значения из справочника."""
        dict_name = field_meta.dictionary
        if not dict_name or not self.dictionary_loader:
            raise ValueError("Справочник не указан или загрузчик отсутствует")

        dictionary: Optional[Dictionary] = self.dictionary_loader.get_cached_dictionary(dict_name)
        if dictionary is None:
            cache_info = self.dictionary_loader.get_cache_info()
            for key in cache_info.get("cache_keys", []):
                if key == dict_name or key.endswith(f":{dict_name}"):
                    dictionary = self.dictionary_loader.get_cached_dictionary(key)
                    if dictionary is not None:
                        break

        if dictionary is None:
            raise ValueError(f"Справочник '{dict_name}' не найден в кэше")

        entry = dictionary.get_random()
        return str(entry.code)

    def _generate_from_pattern(self, pattern: str) -> str:
        """Простая генерация строки по регулярному выражению."""
        if pattern == "^[A-Z]{2}$":
            return "".join(self._random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))

        m = re.match(r"^\^?\[([A-Z]+)\]\{(\d+)\}\$?$", pattern)
        if m:
            chars = m.group(1)
            count = int(m.group(2))
            return "".join(self._random.choices(chars, k=count))

        m2 = re.match(r"^\^?\\d\{(\d+)\}\$?$", pattern)
        if m2:
            count = int(m2.group(1))
            return "".join(self._random.choices("0123456789", k=count))

        # Fallback
        return "AA"

    def _generate_inn(self, length: int = 10, strict: bool = True) -> str:
        """Генерация ИНН заданной длины."""
        if not strict:
            return "".join(self._random.choices("0123456789", k=length))
        if length == 10:
            return self._generate_inn_10()
        if length == 12:
            return self._generate_inn_12()
        raise ValueError(f"Неподдерживаемая длина ИНН: {length}")

    def _generate_inn_10(self) -> str:
        """Генерация 10-значного ИНН с валидной КС (физ. лицо)."""
        digits = [self._random.randint(0, 9) for _ in range(9)]
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(d * w for d, w in zip(digits, weights)) % 11
        if checksum == 10:
            checksum = 0
        digits.append(checksum)
        return "".join(str(d) for d in digits)

    def _generate_inn_12(self) -> str:
        """Генерация 12-значного ИНН с валидной КС (юр. лицо / ИП)."""
        digits = [self._random.randint(0, 9) for _ in range(10)]
        weights_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum1 = sum(d * w for d, w in zip(digits, weights_11)) % 11
        if checksum1 == 10:
            checksum1 = 0
        digits.append(checksum1)

        weights_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum2 = sum(d * w for d, w in zip(digits, weights_12)) % 11
        if checksum2 == 10:
            checksum2 = 0
        digits.append(checksum2)

        return "".join(str(d) for d in digits)

    def _generate_snils(self, strict: bool = False) -> str:
        """Генерация СНИЛС (11 цифр, КС не проверяется)."""
        digits = [self._random.randint(0, 9) for _ in range(11)]
        return "".join(str(d) for d in digits)

    def _generate_phone(self) -> str:
        """Генерация российского мобильного номера (7 + 10 цифр)."""
        return "7" + "".join(self._random.choices("0123456789", k=10))
