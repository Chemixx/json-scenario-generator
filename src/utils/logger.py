"""
Модуль логирования с использованием loguru
"""
from loguru import logger
import sys
from pathlib import Path
from config.settings import config


def setup_logger():
    """
    Настройка логгера с использованием loguru

    Создает два handler'а:
    1. Консольный вывод с цветами
    2. Запись в файл с ротацией

    Returns:
        logger: Настроенный экземпляр логгера
    """
    # Удаляем стандартный handler loguru
    logger.remove()

    # ======================================
    # Handler для консоли (с цветами)
    # ======================================
    logger.add(
        sys.stdout,
        format=config.LOG_FORMAT,
        level=config.LOG_LEVEL,
        colorize=True,
        backtrace=True,  # Показывать полный traceback при ошибках
        diagnose=True,  # Показывать значения переменных при ошибках
    )

    # ======================================
    # Handler для файла (без цветов)
    # ======================================
    log_file_path = config.LOG_DIR / config.LOG_FILE
    logger.add(
        log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=config.LOG_LEVEL,
        rotation=config.LOG_ROTATION,  # Ротация при достижении размера
        retention=config.LOG_RETENTION,  # Хранить логи N дней
        compression="zip",  # Сжимать старые логи
        backtrace=True,
        diagnose=True,
    )

    # Логируем успешную инициализацию
    logger.info("=" * 80)
    logger.info(f"🚀 {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"📂 Логи сохраняются в: {log_file_path}")
    logger.info(f"📊 Уровень логирования: {config.LOG_LEVEL}")
    logger.info("=" * 80)

    return logger


# ======================================
# Инициализация логгера
# ======================================
log = setup_logger()


# ======================================
# НОВАЯ ФУНКЦИЯ: Получение логгера для модуля
# ======================================
def get_logger(name: str = __name__):
    """
    Получить логгер для конкретного модуля

    Эта функция позволяет создавать логгеры с уникальными именами для разных модулей,
    что упрощает отладку и поиск источника логов.

    Args:
        name: Имя модуля (обычно передается __name__)

    Returns:
        logger: Настроенный экземпляр логгера с контекстом модуля

    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Сообщение из моего модуля")
    """
    return logger.bind(module=name)


# ======================================
# Декоратор для логирования функций
# ======================================
def log_function_call(func):
    """
    Декоратор для автоматического логирования вызовов функций

    Args:
        func: Функция для декорирования

    Returns:
        wrapper: Обернутая функция

    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return arg1 + arg2
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        log.debug(f"⚙️  Вызов функции: {func_name}() с args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            log.debug(f"✅ Функция {func_name}() завершена. Результат: {result}")
            return result
        except Exception as e:
            log.error(f"❌ Ошибка в функции {func_name}(): {e}")
            raise

    return wrapper


# ======================================
# Контекстный менеджер для логирования блоков кода
# ======================================
class LogBlock:
    """
    Контекстный менеджер для логирования блоков кода

    Args:
        block_name: Название блока для логирования

    Usage:
        with LogBlock("Загрузка данных"):
            data = load_data()
    """

    def __init__(self, block_name: str):
        self.block_name = block_name

    def __enter__(self):
        log.info(f"▶️  Начало: {self.block_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            log.info(f"✅ Завершено: {self.block_name}")
        else:
            log.error(f"❌ Ошибка в блоке '{self.block_name}': {exc_val}")
        return False  # Не подавляем исключение
