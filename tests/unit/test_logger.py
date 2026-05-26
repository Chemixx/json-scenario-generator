"""
Тесты для модуля логирования
"""
import pytest
from src.utils.logger import log, log_function_call, LogBlock
from src.utils.icons import Icon
from config.settings import config


def test_logger_exists():
    """Тест наличия логгера"""
    assert log is not None


def test_log_file_created():
    """Тест создания файла логов"""
    log_file = config.LOG_DIR / config.LOG_FILE
    assert log_file.exists(), f"Файл логов не создан: {log_file}"


def test_log_levels():
    """Тест различных уровней логирования"""
    # Логируем сообщения разных уровней
    log.debug(f"{Icon.BUG} Debug message for test")
    log.info(f"{Icon.INFO} Info message for test")
    log.warning(f"{Icon.WARNING} Warning message for test")
    log.error(f"{Icon.ERROR} Error message for test")
    log.success(f"{Icon.SUCCESS} Success message for test")

    # Если дошли сюда, значит логирование работает
    assert True


def test_log_function_call_decorator():
    """Тест декоратора log_function_call"""

    @log_function_call
    def add_numbers(a: int, b: int) -> int:
        """Тестовая функция сложения"""
        return a + b

    result = add_numbers(2, 3)
    assert result == 5


def test_log_function_call_decorator_with_exception():
    """Тест декоратора log_function_call при исключении"""

    @log_function_call
    def divide(a: int, b: int) -> float:
        """Тестовая функция деления"""
        return a / b

    # Нормальный вызов
    result = divide(10, 2)
    assert result == 5.0

    # Вызов с ошибкой должен выбросить исключение
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)


def test_log_block_context_manager():
    """Тест контекстного менеджера LogBlock"""

    with LogBlock("Тестовый блок"):
        x = 1 + 1
        assert x == 2


def test_log_block_context_manager_with_exception():
    """Тест контекстного менеджера LogBlock при исключении"""

    with pytest.raises(ValueError):
        with LogBlock("Блок с ошибкой"):
            raise ValueError("Тестовая ошибка")


def test_log_to_file():
    """Тест записи логов в файл"""
    test_message = f"{Icon.TEST} Тестовое сообщение для проверки записи в файл"
    log.info(test_message)

    # Читаем файл логов
    log_file = config.LOG_DIR / config.LOG_FILE
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем, что сообщение записалось
    assert "Тестовое сообщение для проверки записи в файл" in content
