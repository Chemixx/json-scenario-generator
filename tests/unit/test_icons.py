"""Тесты для модуля ASCII-иконок."""
from src.utils.icons import Icon


class TestIcon:
    """Тесты констант Icon."""

    def test_icon_values_are_ascii_only(self):
        """Все значения Icon должны содержать только ASCII-символы."""
        for attr in dir(Icon):
            if attr.startswith('_'):
                continue
            value = getattr(Icon, attr)
            if isinstance(value, str):
                try:
                    value.encode('cp1251')
                except UnicodeEncodeError:
                    raise AssertionError(
                        f"Icon.{attr} = {value!r} содержит не-ASCII символы"
                    )

    def test_icon_categories(self):
        """Проверить основные категории иконок."""
        # Уровни влияния
        assert Icon.CRITICAL == "[!!!]"
        assert Icon.HIGH == "[!!]"
        assert Icon.MEDIUM == "[!]"
        assert Icon.LOW == "[.]"

        # Статусы
        assert Icon.SUCCESS == "[OK]"
        assert Icon.ERROR == "[ERR]"
        assert Icon.WARNING == "[WARN]"
        assert Icon.INFO == "[INFO]"

        # Типы изменений
        assert Icon.ADDITION == "[+]"
        assert Icon.REMOVAL == "[-]"
        assert Icon.MODIFICATION == "[~]"

        # Файловые операции
        assert Icon.FILE == "[FILE]"
        assert Icon.DIRECTORY == "[DIR]"
        assert Icon.SAVE == "[SAVE]"

        # Действия
        assert Icon.START == "[START]"
        assert Icon.FIND == "[FIND]"
        assert Icon.PKG == "[PKG]"

    def test_icon_all_defined(self):
        """Проверить что все ожидаемые иконки определены."""
        expected_attrs = [
            'SUCCESS', 'ERROR', 'WARNING', 'INFO', 'DEBUG',
            'CRITICAL', 'HIGH', 'MEDIUM', 'LOW',
            'ADDITION', 'REMOVAL', 'MODIFICATION',
            'STAT', 'TREND', 'FILE', 'DIRECTORY', 'SAVE',
            'LIST', 'PIN', 'DICTIONARY', 'DELETE',
            'FIND', 'NOTE', 'DONE', 'STYLE', 'BUG', 'TEST',
            'PKG', 'START', 'CONFIG', 'ARROW',
        ]
        for attr in expected_attrs:
            assert hasattr(Icon, attr), f"Icon.{attr} не определён"
            assert isinstance(getattr(Icon, attr), str), f"Icon.{attr} не строка"