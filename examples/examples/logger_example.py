"""
Пример использования логгера
"""
from src.utils.logger import log, log_function_call, LogBlock
from src.utils.icons import Icon


def main():
    """Демонстрация различных возможностей логирования"""

    # ======================================
    # 1. Обычное логирование
    # ======================================
    log.info("=" * 80)
    log.info(f"{Icon.NOTE} Примеры логирования")
    log.info("=" * 80)

    log.debug(f"{Icon.BUG} Debug: детальная информация для отладки")
    log.info(f"{Icon.INFO}  Info: общая информация о работе приложения")
    log.warning(f"{Icon.WARNING}  Warning: предупреждение о потенциальной проблеме")
    log.error(f"{Icon.ERROR} Error: ошибка, которая не останавливает приложение")
    log.success(f"{Icon.SUCCESS} Success: успешное выполнение операции")

    # ======================================
    # 2. Использование декоратора
    # ======================================
    log.info("\n" + "=" * 80)
    log.info(f"{Icon.STYLE} Пример декоратора @log_function_call")
    log.info("=" * 80)

    @log_function_call
    def calculate_sum(a: int, b: int) -> int:
        """Вычисляет сумму двух чисел"""
        return a + b

    result = calculate_sum(10, 20)
    log.info(f"Результат: {result}")

    # ======================================
    # 3. Использование контекстного менеджера
    # ======================================
    log.info("\n" + "=" * 80)
    log.info(f"{Icon.PKG} Пример контекстного менеджера LogBlock")
    log.info("=" * 80)

    with LogBlock("Загрузка и обработка данных"):
        log.info("Шаг 1: Загрузка данных...")
        import time
        time.sleep(0.3)
        log.info("Шаг 2: Валидация данных...")
        time.sleep(0.3)
        log.info("Шаг 3: Обработка данных...")
        time.sleep(0.3)

    # ======================================
    # 4. Логирование структурированных данных
    # ======================================
    log.info("\n" + "=" * 80)
    log.info(f"{Icon.STAT} Логирование структурированных данных")
    log.info("=" * 80)

    schema_info = {
        "version": "072",
        "call": "Call1",
        "fields_count": 150,
        "status": "validated"
    }
    log.info(f"Информация о схеме: {schema_info}")

    # ======================================
    # 5. Обработка ошибок
    # ======================================
    log.info("\n" + "=" * 80)
    log.info(f"{Icon.CRITICAL} Пример логирования ошибок")
    log.info("=" * 80)

    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        log.error(f"Произошла ошибка: {e}")
        log.exception("Полная информация об ошибке:")

    # ======================================
    # Финал
    # ======================================
    log.info("\n" + "=" * 80)
    log.success(f"{Icon.DONE} Все примеры выполнены успешно!")
    log.info(f"{Icon.DIRECTORY} Логи сохранены в: {config.LOG_DIR / config.LOG_FILE}")
    log.info("=" * 80)


if __name__ == "__main__":
    from config.settings import config

    main()
