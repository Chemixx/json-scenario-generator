"""
Форматирование отчетов об изменениях между версиями JSON Schema

Этот модуль отвечает за преобразование AnalysisResult в различные форматы:
- Текстовый (консоль) — с ASCII-иконками (Icon) для безопасного вывода
- Markdown — для документации и GitHub
- JSON — для API и интеграций

Принципы:
- Single Responsibility: только форматирование, без логики анализа
- Open/Closed: легко добавить новые форматы (например, HTML)
- Dependency Inversion: зависит от абстракций (AnalysisResult)

Examples:
    >>> from src.formatters import ReportFormatter
    >>> from src.analyzers import ChangeAnalyzer
    >>>
    >>> # Анализ изменений
    >>> analyzer = ChangeAnalyzer()
    >>> result = analyzer.analyze_changes("data/V070.json", "data/V072.json")
    >>>
    >>> # Форматирование
    >>> formatter = ReportFormatter()
    >>> text_report = formatter.format_text(result, verbose=True)
    >>> print(text_report)
    >>>
    >>> markdown_report = formatter.format_markdown(result)
    >>> json_data = formatter.format_json(result)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.models import (
    AnalysisResult,
    AnalyzedChange,
    ImpactLevel,
)
from src.utils.icons import Icon


class ReportFormatter:
    """
    Форматирование отчетов об изменениях

    Преобразует результаты анализа (AnalysisResult) в различные форматы
    для вывода в консоль, документацию или API.

    Attributes:
        _separator_width: Ширина разделителей (по умолчанию 80 символов)

    Methods:
        format_text: Форматирование в текстовый вид (консоль)
        format_markdown: Форматирование в Markdown
        format_json: Форматирование в JSON

    Examples:
        >>> formatter = ReportFormatter()
        >>> text_report = formatter.format_text(analysis_result, verbose=False)
        >>> print(text_report)
    """

    def __init__(self, separator_width: int = 80, registry: Optional[Any] = None):
        """
        Инициализация форматтера

        Args:
            separator_width: Ширина разделительных линий (по умолчанию 80)
            registry: DictionaryRegistry для расшифровки справочных кодов (опционально)
        """
        self._separator_width = separator_width
        self._registry = registry

    # =========================================================================
    # ТЕКСТОВЫЙ ФОРМАТ (КОНСОЛЬ)
    # =========================================================================

    def format_text(
        self,
        result: AnalysisResult,
        verbose: bool = False,
        show_recommendations: bool = True
    ) -> str:
        """
        Форматирование в текстовый вид для консоли

        Args:
            result: Результаты анализа изменений
            verbose: Подробный вывод (включая рекомендации и детали)
            show_recommendations: Показывать рекомендации (только если verbose=True)

        Returns:
            Форматированная строка для вывода в консоль

        Examples:
            >>> report = formatter.format_text(analysis_result, verbose=True)
            >>> print(report)
            ================================================================================
            [STAT] ОТЧЕТ ОБ ИЗМЕНЕНИЯХ JSON SCHEMA
            ================================================================================
            ...
        """
        lines = []

        # === ЗАГОЛОВОК ===
        lines.append("=" * self._separator_width)
        lines.append(f"{Icon.STAT} ОТЧЕТ ОБ ИЗМЕНЕНИЯХ JSON SCHEMA")
        lines.append("=" * self._separator_width)
        lines.append("")

        # === ВЕРСИИ ===
        lines.append(f"{Icon.FILE} Старая версия: {result.old_version}")
        lines.append(f"{Icon.FILE} Новая версия: {result.new_version}")

        # === СТАТИСТИКА ===
        stats = result.statistics
        lines.append(f"\n{Icon.TREND} СТАТИСТИКА:")
        lines.append(f"  • Всего изменений: {stats['total_changes']}")
        lines.append(f"  • Добавлено полей: {stats['change_types']['additions']}")
        lines.append(f"  • Удалено полей: {stats['change_types']['removals']}")
        lines.append(f"  • Модифицировано полей: {stats['change_types']['modifications']}")

        lines.append("\n  ОБРАТНАЯ СОВМЕСТИМОСТЬ:")
        lines.append(f"  • Breaking changes: {stats['breaking_level']['breaking']}  {Icon.WARNING}")
        lines.append(f"  • Non-breaking changes: {stats['breaking_level']['non_breaking']}  {Icon.SUCCESS}")

        lines.append("\n  УРОВЕНЬ ВЛИЯНИЯ:")
        lines.append(f"  • Критические: {stats['impact_level']['critical']}")
        lines.append(f"  • Высокое влияние: {stats['impact_level']['high']}")
        lines.append(f"  • Среднее влияние: {stats['impact_level']['medium']}")
        lines.append(f"  • Низкое влияние: {stats['impact_level']['low']}")

        # === КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ===
        if result.critical_changes:
            lines.append(f"\n{Icon.CRITICAL} КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ({len(result.critical_changes)}):")
            for i, change in enumerate(result.critical_changes, 1):
                lines.extend(self._format_change_block(
                    i, change, verbose, show_recommendations
                ))

        # === BREAKING CHANGES (не критические) ===
        breaking_non_critical = [
            c for c in result.breaking_changes
            if c.impact_level != ImpactLevel.CRITICAL
        ]
        if breaking_non_critical:
            lines.append(f"\n{Icon.WARNING} BREAKING CHANGES ({len(breaking_non_critical)}):")
            for i, change in enumerate(breaking_non_critical, 1):
                lines.extend(self._format_change_block(
                    i, change, verbose, show_recommendations
                ))

        # === ДОБАВЛЕННЫЕ ПОЛЯ ===
        if result.additions:
            lines.append(f"\n{Icon.ADDITION} ДОБАВЛЕННЫЕ ПОЛЯ ({len(result.additions)}):")
            for i, change in enumerate(result.additions, 1):
                lines.extend(self._format_addition_item(i, change, verbose))

        # === УДАЛЕННЫЕ ПОЛЯ ===
        if result.removals:
            lines.append(f"\n{Icon.REMOVAL} УДАЛЕННЫЕ ПОЛЯ ({len(result.removals)}):")
            for i, change in enumerate(result.removals, 1):
                lines.extend(self._format_removal_item(i, change, verbose))

        # === NON-BREAKING ИЗМЕНЕНИЯ (только модификации) ===
        if result.modifications_non_breaking:
            lines.append(f"\n{Icon.SUCCESS} NON-BREAKING ИЗМЕНЕНИЯ ({len(result.modifications_non_breaking)}):")
            for i, change in enumerate(result.modifications_non_breaking, 1):
                lines.extend(self._format_change_block(
                    i, change, verbose, show_recommendations
                ))

        # === ИТОГОВАЯ РЕКОМЕНДАЦИЯ ===
        lines.append("\n" + "=" * self._separator_width)
        if result.has_critical_changes():
            lines.append(f"\n{Icon.WARNING} ВНИМАНИЕ: Обнаружены критические изменения!")
            lines.append("   Требуется обязательное обновление сценариев.")
        elif result.has_breaking_changes():
            lines.append(f"\n{Icon.WARNING} ВНИМАНИЕ: Обнаружены breaking changes!")
            lines.append("   Рекомендуется обновить сценарии.")
        else:
            lines.append(f"\n{Icon.SUCCESS} Все изменения совместимы с предыдущей версией.")

        lines.append("")

        return "\n".join(lines)

    def _format_change_block(
        self,
        index: int,
        change: AnalyzedChange,
        verbose: bool,
        show_recommendations: bool
    ) -> List[str]:
        """
        Форматирование блока изменения (для критических/breaking/non-breaking)

        Args:
            index: Порядковый номер
            change: Изменение для форматирования
            verbose: Подробный вывод
            show_recommendations: Показывать рекомендации

        Returns:
            Список строк для вывода
        """
        lines = []
        lines.append(f"\n  {index}. {Icon.PIN} {change.path}")
        lines.append(f"     Тип изменения: {change.change_type.to_russian()}")
        lines.append(f"     Причина: {change.reason}")

        if verbose and show_recommendations and change.recommendations:
            lines.append("     Рекомендации:")
            for rec in change.recommendations:
                lines.append(f"       {Icon.SUCCESS} {rec}")

        return lines

    def _format_addition_item(
        self,
        index: int,
        change: AnalyzedChange,
        verbose: bool
    ) -> List[str]:
        """
        Форматирование добавленного поля

        Args:
            index: Порядковый номер
            change: Изменение (ADDITION)
            verbose: Подробный вывод

        Returns:
            Список строк для вывода
        """
        lines = []
        field = change.field_change.new_meta

        if field:
            # Определяем статус поля
            if field.is_required:
                status = "О"  # Обязательное
            elif field.is_conditional:
                status = "УО"  # Условно обязательное
            else:
                status = "Н"  # Необязательное

            impact_icon = change.impact_level.to_icon()

            line = f"  {index}. {impact_icon} {change.path} [{status}]"
            lines.append(line)

            if verbose:
                lines.append(f"     Тип: {field.field_type}")
                if change.reason:
                    lines.append(f"     Причина: {change.reason}")
                if field.dictionary:
                    lines.append(f"     Справочник: {field.dictionary}")

        return lines

    def _format_removal_item(
        self,
        index: int,
        change: AnalyzedChange,
        verbose: bool
    ) -> List[str]:
        """
        Форматирование удаленного поля

        Args:
            index: Порядковый номер
            change: Изменение (REMOVAL)
            verbose: Подробный вывод

        Returns:
            Список строк для вывода
        """
        lines = []
        field = change.field_change.old_meta

        if field:
            # Определяем статус поля
            if field.is_required:
                status = "О"
            elif field.is_conditional:
                status = "УО"
            else:
                status = "Н"

            impact_icon = change.impact_level.to_icon()

            line = f"  {index}. {impact_icon} {change.path} [{status}]"
            lines.append(line)

            if verbose:
                lines.append(f"     Тип: {field.field_type}")
                if change.reason:
                    lines.append(f"     Причина: {change.reason}")

        return lines

    # =========================================================================
    # MARKDOWN ФОРМАТ
    # =========================================================================

    def format_markdown(self, result: AnalysisResult) -> str:
        """
        Форматирование в Markdown для документации

        Args:
            result: Результаты анализа изменений

        Returns:
            Строка в формате Markdown

        Examples:
            >>> markdown = formatter.format_markdown(analysis_result)
            >>> with open("CHANGELOG.md", "w") as f:
            ...     f.write(markdown)
        """
        lines = []

        # === ЗАГОЛОВОК ===
        lines.append("# Отчет об изменениях JSON Schema\n")
        lines.append(f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Старая версия:** `{result.old_version}`  ")
        lines.append(f"**Новая версия:** `{result.new_version}`\n")

        # === СТАТИСТИКА ===
        stats = result.statistics
        lines.append("## 📈 Статистика\n")
        lines.append(f"- **Всего изменений:** {stats['total_changes']}")
        lines.append(f"- **Breaking changes:** {stats['breaking_level']['breaking']}")
        lines.append(f"- **Non-breaking changes:** {stats['breaking_level']['non_breaking']}")
        lines.append(f"- **Добавлено полей:** {stats['change_types']['additions']}")
        lines.append(f"- **Удалено полей:** {stats['change_types']['removals']}")
        lines.append(f"- **Критические:** {stats['impact_level']['critical']}")
        lines.append(f"- **Высокое влияние:** {stats['impact_level']['high']}\n")

        # === КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ===
        if result.critical_changes:
            lines.append("## 🚨 Критические изменения\n")
            for i, change in enumerate(result.critical_changes, 1):
                lines.append(f"### {i}. `{change.path}`\n")
                lines.append(f"- **Тип:** {change.change_type.to_russian()}")
                lines.append(f"- **Причина:** {change.reason}")
                if change.recommendations:
                    lines.append("- **Рекомендации:**")
                    for rec in change.recommendations:
                        lines.append(f"  - {rec}")
                lines.append("")

        # === BREAKING CHANGES (не критические) ===
        breaking_non_critical = [
            c for c in result.breaking_changes
            if c.impact_level != ImpactLevel.CRITICAL
        ]
        if breaking_non_critical:
            lines.append("## ⚠️ Breaking Changes\n")
            for i, change in enumerate(breaking_non_critical, 1):
                lines.append(f"### {i}. `{change.path}`\n")
                lines.append(f"- **Тип:** {change.change_type.to_russian()}")
                lines.append(f"- **Причина:** {change.reason}\n")

        # === ДОБАВЛЕННЫЕ ПОЛЯ ===
        if result.additions:
            lines.append("## ➕ Добавленные поля\n")
            for i, change in enumerate(result.additions, 1):
                field = change.field_change.new_meta
                if field:
                    status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                    lines.append(f"{i}. `{change.path}` [{status}] - {change.reason}")
            lines.append("")

        # === УДАЛЕННЫЕ ПОЛЯ ===
        if result.removals:
            lines.append("## ➖ Удаленные поля\n")
            for i, change in enumerate(result.removals, 1):
                field = change.field_change.old_meta
                if field:
                    status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                    lines.append(f"{i}. `{change.path}` [{status}] - {change.reason}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # JSON ФОРМАТ
    # =========================================================================

    def format_json(self, result: AnalysisResult) -> Dict:
        """
        Форматирование в JSON для API/интеграций

        Args:
            result: Результаты анализа изменений

        Returns:
            Словарь с полной информацией об изменениях

        Examples:
            >>> import json
            >>> data = formatter.format_json(analysis_result)
            >>> print(json.dumps(data, ensure_ascii=False, indent=2))
        """
        report = result.to_dict()
        report["generated_at"] = datetime.now().isoformat()

        return report
