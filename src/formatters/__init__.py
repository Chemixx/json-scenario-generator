"""
Форматтеры отчетов

Модуль для преобразования результатов анализа в различные форматы вывода:
- Текстовый (консоль)
- Markdown (документация)
- JSON (API)

Exports:
    ReportFormatter: Основной класс для форматирования отчетов

Examples:
    >>> from src.formatters import ReportFormatter
    >>> from src.models import AnalysisResult
    >>>
    >>> # Предположим, у нас есть результат анализа
    >>> formatter = ReportFormatter()
    >>> # report_text = formatter.format_text(analysis_result)
    >>> # report_md = formatter.format_markdown(analysis_result)
"""

from .report_formatter import ReportFormatter

__all__ = [
    "ReportFormatter",
]
