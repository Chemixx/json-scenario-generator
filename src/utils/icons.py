"""
Централизованный справочник ASCII-иконок для консольного вывода.

Все значения гарантированно кодируются в cp1251 (Windows Cyrillic).
Используются в logger, ReportFormatter.format_text() и CLI.

Для Markdown-формата используйте эмодзи напрямую (format_markdown).
"""


class Icon:
    """
    ASCII-иконки для безопасного вывода в любую кодировку.

    Заменяют эмодзи в runtime-коде, предотвращая UnicodeEncodeError
    на Windows-консолях с cp1251.
    """

    # === Статусы ===
    SUCCESS = "[OK]"
    ERROR = "[ERR]"
    WARNING = "[WARN]"
    INFO = "[INFO]"
    DEBUG = "[DBG]"

    # === Уровни влияния (ImpactLevel) ===
    CRITICAL = "[!!!]"
    HIGH = "[!!]"
    MEDIUM = "[!]"
    LOW = "[.]"

    # === Типы изменений (ChangeType) ===
    ADDITION = "[+]"
    REMOVAL = "[-]"
    MODIFICATION = "[~]"

    # === Данные и файлы ===
    STAT = "[STAT]"
    TREND = "[TREND]"
    FILE = "[FILE]"
    DIRECTORY = "[DIR]"
    SAVE = "[SAVE]"
    LIST = "[LIST]"
    PIN = "[PIN]"
    DICTIONARY = "[DICT]"
    DELETE = "[DEL]"
    PKG = "[PKG]"

    # === Действия ===
    START = "[START]"
    FIND = "[FIND]"
    NOTE = "[NOTE]"
    DONE = "[DONE]"
    STYLE = "[STYLE]"
    BUG = "[BUG]"
    TEST = "[TEST]"
    CONFIG = "[CFG]"
    ARROW = "[>]"