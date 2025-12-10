"""
Python-эквиваленты Java-методов для SpEL.
Покрывает Date API, String API, бизнес-функции.
"""

from datetime import datetime, timedelta, date
from typing import Any, Optional
import re


class SpelFunctions:
    """
    Класс с методами-эквивалентами Java SpEL функций.

    Используется при транспиляции SpEL → Python для подстановки
    правильных Python-реализаций вместо Java-методов.
    """

    # ========== ДАТЫ ==========

    @staticmethod
    def current_date() -> date:
        """
        currentDate() → T(java.time.LocalDate).now()

        Returns:
            Текущая дата (без времени)
        """
        return date.today()

    @staticmethod
    def to_local_date(date_str: str) -> date:
        """
        Parse ISO 8601 date string → LocalDate

        Args:
            date_str: "2025-12-10" или "2025-12-10T14:30:00"

        Returns:
            date объект
        """
        try:
            # Пробуем с временем
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except ValueError:
            # Пробуем только дату
            return datetime.strptime(date_str, "%Y-%m-%d").date()

    @staticmethod
    def minus_years(dt: date, years: int) -> date:
        """
        date.minusYears(years) → LocalDate

        Args:
            dt: Исходная дата
            years: Количество лет для вычитания

        Returns:
            Новая дата - N лет
        """
        try:
            return dt.replace(year=dt.year - years)
        except ValueError:
            # Обработка 29 февраля в високосном году
            return dt.replace(year=dt.year - years, day=28)

    @staticmethod
    def minus_days(dt: date, days: int) -> date:
        """
        date.minusDays(days) → LocalDate

        Args:
            dt: Исходная дата
            days: Количество дней для вычитания

        Returns:
            Новая дата - N дней
        """
        return dt - timedelta(days=days)

    @staticmethod
    def is_after(dt1: date, dt2: date) -> bool:
        """
        dt1.isAfter(dt2) → boolean

        Args:
            dt1: Первая дата
            dt2: Вторая дата

        Returns:
            True если dt1 > dt2
        """
        return dt1 > dt2

    @staticmethod
    def compare_to(obj1: Any, obj2: Any) -> int:
        """
        Comparable.compareTo() → int

        Returns:
            -1 если obj1 < obj2
             0 если obj1 == obj2
             1 если obj1 > obj2
        """
        if obj1 > obj2:
            return 1
        elif obj1 < obj2:
            return -1
        else:
            return 0

    # ========== СТРОКИ ==========

    @staticmethod
    def length(string: Optional[str]) -> int:
        """
        String.length() → int

        Args:
            string: Строка для измерения

        Returns:
            Длина строки (0 если null)
        """
        return len(string) if string else 0

    # ========== БИЗНЕС-ФУНКЦИИ ==========

    @staticmethod
    def is_valid_tax_num(tax_num: Optional[str]) -> bool:
        """
        isValidTaxNum(string) → boolean

        Проверка ИНН (10 или 12 цифр + контрольные суммы)

        Args:
            tax_num: ИНН для проверки

        Returns:
            True если ИНН валиден
        """
        if not tax_num or not tax_num.isdigit():
            return False

        if len(tax_num) == 10:
            # ИНН ЮЛ (10 цифр)
            coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
            check_sum = sum(int(tax_num[i]) * coefficients[i] for i in range(9))
            control = (check_sum % 11) % 10
            return int(tax_num[9]) == control

        elif len(tax_num) == 12:
            # ИНН ФЛ (12 цифр)
            coefficients_1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            coefficients_2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

            check_sum_1 = sum(int(tax_num[i]) * coefficients_1[i] for i in range(10))
            control_1 = (check_sum_1 % 11) % 10

            check_sum_2 = sum(int(tax_num[i]) * coefficients_2[i] for i in range(11))
            control_2 = (check_sum_2 % 11) % 10

            return int(tax_num[10]) == control_1 and int(tax_num[11]) == control_2

        else:
            return False

    @staticmethod
    def is_valid_uuid(uuid_str: Optional[str]) -> bool:
        """
        isValidUuid(string) → boolean

        Проверка формата UUID (8-4-4-4-12)

        Args:
            uuid_str: UUID для проверки

        Returns:
            True если UUID валиден
        """
        if not uuid_str:
            return False

        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_str))

    @staticmethod
    def digits_check(value: Optional[Any], int_digits: int, frac_digits: int) -> bool:
        """
        digitsCheck(value, intDigits, fracDigits) → boolean

        Проверка количества цифр в числе (до и после запятой)

        Args:
            value: Число для проверки
            int_digits: Максимум цифр до запятой
            frac_digits: Максимум цифр после запятой

        Returns:
            True если число соответствует формату

        Example:
            digitsCheck(1234.56, 9, 2) → True
            digitsCheck(12345678901.5, 9, 2) → False
        """
        if value is None:
            return True  # null считается валидным

        # Конвертируем в строку
        str_value = str(value)

        # Разделяем на целую и дробную части
        if '.' in str_value:
            int_part, frac_part = str_value.split('.')
        else:
            int_part = str_value
            frac_part = ""

        # Убираем минус для подсчета
        int_part = int_part.lstrip('-')

        # Проверяем количество цифр
        return len(int_part) <= int_digits and len(frac_part) <= frac_digits

    @staticmethod
    def is_dictionary_value(
        value: Optional[str],
        dictionary_name: str,
        allow_empty: bool = False
    ) -> bool:
        """
        isDictionaryValue(value, dictionaryName, allowEmpty) → boolean

        Проверка, что значение есть в справочнике.

        ⚠️ Требует загрузки справочника через DictionaryLoader!

        Args:
            value: Значение для проверки
            dictionary_name: Название справочника (например, "SALE_POINT")
            allow_empty: Разрешить пустое значение

        Returns:
            True если значение валидно
        """
        # TODO: Реализовать интеграцию с DictionaryLoader
        # Пока заглушка
        if allow_empty and (value is None or value == ""):
            return True

        # Placeholder: считаем, что все значения валидны
        # В будущем здесь будет обращение к DictionaryLoader
        logger = get_logger(__name__)
        logger.debug(
            f"isDictionaryValue: проверка '{value}' в справочнике '{dictionary_name}' "
            f"(пока заглушка, всегда True)"
        )
        return True


# Singleton instance для удобства использования
spel_functions = SpelFunctions()


# Импорт logger для использования в методах
from src.utils.logger import get_logger
