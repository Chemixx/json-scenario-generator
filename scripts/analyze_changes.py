"""
CLI для анализа изменений между версиями JSON Schema

Usage:
    python scripts/analyze_changes.py <old_schema> <new_schema> [--output <report.json>]

Example:
    python scripts/analyze_changes.py data/V070Call1Rq.json data/V072Call1Rq.json --output output/changes_report.json
"""
import sys
import argparse
from pathlib import Path
import json
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# ИМПОРТЫ (ОБНОВЛЕНО)
# ============================================================================

from src.analyzers import ChangeAnalyzer
from src.models import (
    # AnalyzedChange,  # ← УБРАНО: не используется напрямую
    AnalysisResult,
    # ChangeType,      # ← УБРАНО: используется через .change_type (свойство)
    # BreakingLevel,   # ← УБРАНО: используется через .breaking_level (свойство)
    ImpactLevel,       # ← ОСТАВЛЕНО: используется для сравнения
)
from src.utils import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Анализ изменений между версиями JSON Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Базовый анализ
  python scripts/analyze_changes.py data/V73Call1Rq.json data/V72Call1Rq.json
  
  # С сохранением отчета
  python scripts/analyze_changes.py data/V070Call1Rq.json data/V072Call1Rq.json --output output/report.json
  
  # Только критические изменения
  python scripts/analyze_changes.py data/V070Call1Rq.json data/V072Call1Rq.json --only-critical
  
  # Markdown формат
  python scripts/analyze_changes.py data/V070Call1Rq.json data/V072Call1Rq.json --format markdown
        """
    )

    parser.add_argument(
        "old_schema",
        type=Path,
        help="Путь к старой версии JSON Schema"
    )

    parser.add_argument(
        "new_schema",
        type=Path,
        help="Путь к новой версии JSON Schema"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Путь для сохранения отчета (JSON)"
    )

    parser.add_argument(
        "--only-critical",
        action="store_true",
        help="Показать только критические изменения"
    )

    parser.add_argument(
        "--only-breaking",
        action="store_true",
        help="Показать только breaking changes"
    )

    parser.add_argument(
        "--format",
        choices=["json", "text", "markdown"],
        default="text",
        help="Формат вывода отчета (по умолчанию: text)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод (включая рекомендации)"
    )

    return parser.parse_args()


# ============================================================================
# ФУНКЦИИ ВЫВОДА ОТЧЕТА (ОБНОВЛЕНО)
# ============================================================================

def print_text_report(result: AnalysisResult, verbose: bool = False):
    """Вывести отчет в текстовом формате"""
    print("\n" + "=" * 80)
    print("📊 ОТЧЕТ ОБ ИЗМЕНЕНИЯХ JSON SCHEMA")
    print("=" * 80)

    print(f"\n📁 Старая версия: {result.old_version}")
    print(f"📁 Новая версия: {result.new_version}")

    # Получаем статистику из нового API
    stats = result.statistics

    # Статистика
    print("\n📈 СТАТИСТИКА:")
    print(f"  • Всего изменений: {stats['total_changes']}")
    print(f"  • Добавлено полей: {stats['change_types']['additions']}")
    print(f"  • Удалено полей: {stats['change_types']['removals']}")
    print(f"  • Модифицировано полей: {stats['change_types']['modifications']}")

    print("\n  ОБРАТНАЯ СОВМЕСТИМОСТЬ:")
    print(f"  • Breaking changes: {stats['breaking_level']['breaking']}  ⚠️")
    print(f"  • Non-breaking changes: {stats['breaking_level']['non_breaking']}  ✅")

    print("\n  УРОВЕНЬ ВЛИЯНИЯ:")
    print(f"  • Критические: {stats['impact_level']['critical']}")
    print(f"  • Высокое влияние: {stats['impact_level']['high']}")
    print(f"  • Среднее влияние: {stats['impact_level']['medium']}")
    print(f"  • Низкое влияние: {stats['impact_level']['low']}")

    # Критические изменения
    if result.critical_changes:
        print(f"\n🚨 КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ({len(result.critical_changes)}):")
        for i, change in enumerate(result.critical_changes, 1):
            print(f"\n  {i}. 📍 {change.path}")
            print(f"     Тип изменения: {change.change_type.to_russian()}")
            print(f"     Причина: {change.reason}")

            if verbose and change.recommendations:
                print("     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    # Breaking changes (не критические)
    breaking_non_critical = [
        c for c in result.breaking_changes
        if c.impact_level != ImpactLevel.CRITICAL
    ]
    if breaking_non_critical:
        print(f"\n⚠️  BREAKING CHANGES ({len(breaking_non_critical)}):")
        for i, change in enumerate(breaking_non_critical, 1):
            print(f"\n  {i}. 📍 {change.path}")
            print(f"     Тип изменения: {change.change_type.to_russian()}")
            print(f"     Причина: {change.reason}")

            if verbose and change.recommendations:
                print("     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    # Добавленные поля
    additions = result.additions
    if additions:
        print(f"\n➕ ДОБАВЛЕННЫЕ ПОЛЯ ({len(additions)}):")
        for i, change in enumerate(additions, 1):
            field = change.field_change.new_meta
            if field:
                # Определяем статус поля
                if field.is_required:
                    status = "О"  # Обязательное
                elif field.is_conditional:
                    status = "УО"  # Условно обязательное
                else:
                    status = "Н"  # Необязательное

                impact_icon = change.impact_level.to_emoji()

                print(f"  {i}. {impact_icon} {change.path} [{status}]")
                if verbose:
                    print(f"     Тип: {field.field_type}")
                    if change.reason:
                        print(f"     Причина: {change.reason}")
                    if field.dictionary:
                        print(f"     Справочник: {field.dictionary}")

    # Удаленные поля
    removals = result.removals
    if removals:
        print(f"\n➖ УДАЛЕННЫЕ ПОЛЯ ({len(removals)}):")
        for i, change in enumerate(removals, 1):
            field = change.field_change.old_meta
            if field:
                # Определяем статус поля
                if field.is_required:
                    status = "О"
                elif field.is_conditional:
                    status = "УО"
                else:
                    status = "Н"

                impact_icon = change.impact_level.to_emoji()

                print(f"  {i}. {impact_icon} {change.path} [{status}]")
                if verbose:
                    print(f"     Тип: {field.field_type}")
                    if change.reason:
                        print(f"     Причина: {change.reason}")

    # Non-breaking changes (только модификации)
    non_breaking_modifications = result.modifications_non_breaking
    if non_breaking_modifications:
        print(f"\n✅ NON-BREAKING ИЗМЕНЕНИЯ ({len(non_breaking_modifications)}):")
        for i, change in enumerate(non_breaking_modifications, 1):
            print(f"  {i}. 📍 {change.path}")
            print(f"     {change.reason}")

            if verbose and change.recommendations:
                print("     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    print("\n" + "=" * 80)

    # Итоговая рекомендация
    if result.has_critical_changes():
        print("\n⚠️  ВНИМАНИЕ: Обнаружены критические изменения!")
        print("   Требуется обязательное обновление сценариев.")
    elif result.has_breaking_changes():
        print("\n⚠️  ВНИМАНИЕ: Обнаружены breaking changes!")
        print("   Рекомендуется обновить сценарии.")
    else:
        print("\n✅ Все изменения совместимы с предыдущей версией.")

    print()


def print_markdown_report(result: AnalysisResult):
    """Вывести отчет в Markdown формате"""
    print("# Отчет об изменениях JSON Schema\n")
    print(f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"**Старая версия:** `{result.old_version}`  ")
    print(f"**Новая версия:** `{result.new_version}`\n")

    # Получаем статистику
    stats = result.statistics

    print("## 📈 Статистика\n")
    print(f"- **Всего изменений:** {stats['total_changes']}")
    print(f"- **Breaking changes:** {stats['breaking_level']['breaking']}")
    print(f"- **Non-breaking changes:** {stats['breaking_level']['non_breaking']}")
    print(f"- **Добавлено полей:** {stats['change_types']['additions']}")
    print(f"- **Удалено полей:** {stats['change_types']['removals']}")
    print(f"- **Критические:** {stats['impact_level']['critical']}")
    print(f"- **Высокое влияние:** {stats['impact_level']['high']}\n")

    if result.critical_changes:
        print("## 🚨 Критические изменения\n")
        for i, change in enumerate(result.critical_changes, 1):
            print(f"### {i}. `{change.path}`\n")
            print(f"- **Тип:** {change.change_type.to_russian()}")
            print(f"- **Причина:** {change.reason}")
            if change.recommendations:
                print("- **Рекомендации:**")
                for rec in change.recommendations:
                    print(f"  - {rec}")
            print()

    breaking_non_critical = [
        c for c in result.breaking_changes
        if c.impact_level != ImpactLevel.CRITICAL
    ]
    if breaking_non_critical:
        print("## ⚠️ Breaking Changes\n")
        for i, change in enumerate(breaking_non_critical, 1):
            print(f"### {i}. `{change.path}`\n")
            print(f"- **Тип:** {change.change_type.to_russian()}")
            print(f"- **Причина:** {change.reason}\n")

    if result.additions:
        print("## ➕ Добавленные поля\n")
        for i, change in enumerate(result.additions, 1):
            field = change.field_change.new_meta
            if field:
                status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                print(f"{i}. `{change.path}` [{status}] - {change.reason}")
        print()

    if result.removals:
        print("## ➖ Удаленные поля\n")
        for i, change in enumerate(result.removals, 1):
            field = change.field_change.old_meta
            if field:
                status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                print(f"{i}. `{change.path}` [{status}] - {change.reason}")
        print()


def save_json_report(result: AnalysisResult, output_path: Path):
    """Сохранить отчет в JSON"""
    report = result.to_dict()
    report["generated_at"] = datetime.now().isoformat()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ Отчет сохранен: {output_path}")


def main():
    """Главная функция"""
    args = parse_arguments()

    # Проверка существования файлов
    if not args.old_schema.exists():
        logger.error(f"❌ Файл не найден: {args.old_schema}")
        sys.exit(1)

    if not args.new_schema.exists():
        logger.error(f"❌ Файл не найден: {args.new_schema}")
        sys.exit(1)

    # Анализ изменений
    logger.info("🔍 Анализ изменений между версиями...")
    logger.info(f"   Старая: {args.old_schema}")
    logger.info(f"   Новая: {args.new_schema}")

    try:
        analyzer = ChangeAnalyzer()
        result = analyzer.analyze_changes(args.old_schema, args.new_schema)

        # Вывод отчета
        if args.format == "text":
            # Фильтрация для текстового формата
            if args.only_critical:
                # Показываем только критические
                filtered_result = AnalysisResult(
                    old_version=result.old_version,
                    new_version=result.new_version,
                    analyzed_changes=result.critical_changes,
                    analysis_date=result.analysis_date
                )
                print_text_report(filtered_result, verbose=args.verbose)
            elif args.only_breaking:
                # Показываем только breaking
                filtered_result = AnalysisResult(
                    old_version=result.old_version,
                    new_version=result.new_version,
                    analyzed_changes=result.breaking_changes,
                    analysis_date=result.analysis_date
                )
                print_text_report(filtered_result, verbose=args.verbose)
            else:
                # Показываем все
                print_text_report(result, verbose=args.verbose)

        elif args.format == "markdown":
            print_markdown_report(result)

        elif args.format == "json":
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

        # Сохранение в файл
        if args.output:
            save_json_report(result, args.output)

        # Код возврата
        if result.has_critical_changes():
            logger.warning(f"⚠️  Найдено {len(result.critical_changes)} критических изменений!")
            sys.exit(1)
        else:
            logger.info("✅ Анализ завершен успешно")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
