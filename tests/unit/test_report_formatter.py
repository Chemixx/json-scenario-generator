"""
Тесты для ReportFormatter

Покрытие:
- format_text() — консольный формат
- format_markdown() — Markdown формат
- format_json() — JSON формат
- Фильтрация изменений
- Verbose режим
"""

import pytest
from datetime import datetime

from src.formatters import ReportFormatter
from src.utils.icons import Icon
from src.models import (
    AnalysisResult,
    AnalyzedChange,
    FieldChange,
    FieldMetadata,
    ChangeType,
    BreakingLevel,
    ImpactLevel,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_changes():
    """Примеры изменений для тестов"""
    # Критическое изменение (Н → О)
    critical_change = AnalyzedChange(
        field_change=FieldChange(
            path="loanRequest/amount",
            change_type="modification",  # ← ДОБАВЛЕНО
            old_meta=FieldMetadata(
                name="amount",
                path="loanRequest/amount",
                field_type="number",
                is_required=False,
            ),
            new_meta=FieldMetadata(
                name="amount",
                path="loanRequest/amount",
                field_type="number",
                is_required=True,
            ),
        ),
        change_type=ChangeType.MODIFICATION,
        breaking_level=BreakingLevel.BREAKING,
        impact_level=ImpactLevel.CRITICAL,
        reason="Поле стало обязательным (Н → О)",
        recommendations=["Обновить все сценарии", "Добавить валидацию"],
    )

    # Добавление условно обязательного поля
    addition_change = AnalyzedChange(
        field_change=FieldChange(
            path="customerForm/email",
            change_type="addition",  # ← ДОБАВЛЕНО
            old_meta=None,
            new_meta=FieldMetadata(
                name="email",
                path="customerForm/email",
                field_type="string",
                is_required=False,
                is_conditional=True,
            ),
        ),
        change_type=ChangeType.ADDITION,
        breaking_level=BreakingLevel.BREAKING,
        impact_level=ImpactLevel.HIGH,
        reason="Добавлено условно обязательное поле (УО)",
        recommendations=["Добавить в сценарии для соответствующих условий"],
    )

    # Удаление необязательного поля
    removal_change = AnalyzedChange(
        field_change=FieldChange(
            path="customerForm/oldField",
            change_type="removal",  # ← ДОБАВЛЕНО
            old_meta=FieldMetadata(
                name="oldField",
                path="customerForm/oldField",
                field_type="string",
                is_required=False,
            ),
            new_meta=None,
        ),
        change_type=ChangeType.REMOVAL,
        breaking_level=BreakingLevel.BREAKING,
        impact_level=ImpactLevel.MEDIUM,
        reason="Удалено необязательное поле (Н)",
        recommendations=["Удалить из сценариев"],
    )

    # Non-breaking модификация
    non_breaking_change = AnalyzedChange(
        field_change=FieldChange(
            path="customerForm/phone",
            change_type="modification",  # ← ДОБАВЛЕНО
            old_meta=FieldMetadata(
                name="phone",
                path="customerForm/phone",
                field_type="string",
                is_required=False,
                is_conditional=True,
            ),
            new_meta=FieldMetadata(
                name="phone",
                path="customerForm/phone",
                field_type="string",
                is_required=False,
            ),
        ),
        change_type=ChangeType.MODIFICATION,
        breaking_level=BreakingLevel.NON_BREAKING,
        impact_level=ImpactLevel.LOW,
        reason="Поле перестало быть условно обязательным (УО → Н)",
        recommendations=[],
    )

    return [critical_change, addition_change, removal_change, non_breaking_change]


@pytest.fixture
def sample_result(sample_changes):
    """Пример AnalysisResult"""
    return AnalysisResult(
        old_version="V072Call1Rq",
        new_version="V073Call1Rq",
        analyzed_changes=sample_changes,
        analysis_date=datetime(2025, 12, 10, 0, 0, 0),
    )


# =============================================================================
# ТЕСТЫ format_text()
# =============================================================================

def test_format_text_basic(sample_result):
    """Тест базового текстового форматирования"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result, verbose=False)

    # Проверяем заголовок
    assert f"{Icon.STAT} ОТЧЕТ ОБ ИЗМЕНЕНИЯХ JSON SCHEMA" in report
    assert "V072Call1Rq" in report
    assert "V073Call1Rq" in report

    # Проверяем статистику
    assert "Всего изменений: 4" in report
    assert "Добавлено полей: 1" in report
    assert "Удалено полей: 1" in report
    assert "Модифицировано полей: 2" in report

    # Проверяем breaking/non-breaking
    assert "Breaking changes: 3" in report
    assert "Non-breaking changes: 1" in report


def test_format_text_verbose(sample_result):
    """Тест подробного форматирования с рекомендациями"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result, verbose=True)

    # Проверяем наличие рекомендаций
    assert "Рекомендации:" in report
    assert "Обновить все сценарии" in report
    assert "Добавить валидацию" in report


def test_format_text_critical_section(sample_result):
    """Тест секции критических изменений"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result)

    # Проверяем секцию критических изменений
    assert f"{Icon.CRITICAL} КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ (1):" in report
    assert "loanRequest/amount" in report
    assert "Поле стало обязательным (Н → О)" in report


def test_format_text_additions_section(sample_result):
    """Тест секции добавленных полей"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result)

    # Проверяем секцию добавлений
    assert f"{Icon.ADDITION} ДОБАВЛЕННЫЕ ПОЛЯ (1):" in report
    assert "customerForm/email" in report
    assert "[УО]" in report  # Условно обязательное


def test_format_text_removals_section(sample_result):
    """Тест секции удаленных полей"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result)

    # Проверяем секцию удалений
    assert f"{Icon.REMOVAL} УДАЛЕННЫЕ ПОЛЯ (1):" in report
    assert "customerForm/oldField" in report
    assert "[Н]" in report  # Необязательное


def test_format_text_non_breaking_section(sample_result):
    """Тест секции non-breaking изменений"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result)

    # Проверяем секцию non-breaking
    assert f"{Icon.SUCCESS} NON-BREAKING ИЗМЕНЕНИЯ (1):" in report
    assert "customerForm/phone" in report


def test_format_text_final_recommendation_critical(sample_result):
    """Тест итоговой рекомендации при критических изменениях"""
    formatter = ReportFormatter()
    report = formatter.format_text(sample_result)

    # Проверяем итоговую рекомендацию
    assert f"{Icon.WARNING} ВНИМАНИЕ: Обнаружены критические изменения!" in report
    assert "Требуется обязательное обновление сценариев." in report


# =============================================================================
# ТЕСТЫ format_markdown()
# =============================================================================

def test_format_markdown_basic(sample_result):
    """Тест базового Markdown форматирования"""
    formatter = ReportFormatter()
    markdown = formatter.format_markdown(sample_result)

    # Проверяем заголовки
    assert "# Отчет об изменениях JSON Schema" in markdown
    assert "## 📈 Статистика" in markdown

    # Проверяем метаданные
    assert "`V072Call1Rq`" in markdown
    assert "`V073Call1Rq`" in markdown


def test_format_markdown_statistics(sample_result):
    """Тест статистики в Markdown"""
    formatter = ReportFormatter()
    markdown = formatter.format_markdown(sample_result)

    # Проверяем статистику
    assert "**Всего изменений:** 4" in markdown
    assert "**Breaking changes:** 3" in markdown
    assert "**Non-breaking changes:** 1" in markdown


def test_format_markdown_critical_section(sample_result):
    """Тест секции критических изменений в Markdown"""
    formatter = ReportFormatter()
    markdown = formatter.format_markdown(sample_result)

    # Проверяем секцию критических изменений
    assert "## 🚨 Критические изменения" in markdown
    assert "`loanRequest/amount`" in markdown
    assert "**Причина:** Поле стало обязательным (Н → О)" in markdown


# =============================================================================
# ТЕСТЫ format_json()
# =============================================================================

def test_format_json_structure(sample_result):
    """Тест структуры JSON"""
    formatter = ReportFormatter()
    json_data = formatter.format_json(sample_result)

    # Проверяем основные поля
    assert "old_version" in json_data
    assert "new_version" in json_data
    assert "statistics" in json_data
    assert "changes" in json_data
    assert "generated_at" in json_data

    # Проверяем значения
    assert json_data["old_version"] == "V072Call1Rq"
    assert json_data["new_version"] == "V073Call1Rq"
    assert len(json_data["changes"]) == 4


def test_format_json_statistics(sample_result):
    """Тест статистики в JSON"""
    formatter = ReportFormatter()
    json_data = formatter.format_json(sample_result)

    stats = json_data["statistics"]
    assert stats["total_changes"] == 4
    assert stats["change_types"]["additions"] == 1
    assert stats["change_types"]["removals"] == 1
    assert stats["breaking_level"]["breaking"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
