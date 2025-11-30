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

from src.analyzers.change_analyzer import (
    ChangeAnalyzer,
    ChangeClassification,
    ChangeImpact
)
from src.utils.logger import get_logger


logger = get_logger(__name__)


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Анализ изменений между версиями JSON Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Базовый анализ
  python scripts/analyze_changes.py data/V070Call1Rq.json data/V072Call1Rq.json
  
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


def print_text_report(result, verbose=False):
    """Вывести отчет в текстовом формате"""
    print("\n" + "=" * 80)
    print(f"📊 ОТЧЕТ ОБ ИЗМЕНЕНИЯХ JSON SCHEMA")
    print("=" * 80)

    print(f"\n📁 Старая версия: {result.old_schema.name}")
    print(f"📁 Новая версия: {result.new_schema.name}")

    # Получаем статистику
    additions = result.get_changes_by_classification(ChangeClassification.ADDITION)
    removals = result.get_changes_by_classification(ChangeClassification.REMOVAL)

    # Статистика
    print(f"\n📈 СТАТИСТИКА:")
    print(f"  • Всего изменений: {len(result.analyzed_changes)}")
    print(f"  • Breaking changes: {len(result.breaking_changes)}")
    print(f"  • Non-breaking changes: {len(result.non_breaking_changes)}")
    print(f"  • Добавлено полей: {len(additions)}")
    print(f"  • Удалено полей: {len(removals)}")
    print(f"  • Критические: {len(result.critical_changes)}")
    print(f"  • Высокое влияние: {len(result.high_impact_changes)}")

    # Критические изменения
    if result.critical_changes:
        print(f"\n🚨 КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ({len(result.critical_changes)}):")
        for i, change in enumerate(result.critical_changes, 1):
            print(f"\n  {i}. 📍 {change.field_change.path}")
            print(f"     Тип изменения: {change.field_change.change_type}")
            print(f"     Причина: {change.reason}")

            if verbose and change.recommendations:
                print(f"     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    # Breaking changes (не критические)
    breaking_non_critical = [
        c for c in result.breaking_changes
        if c not in result.critical_changes
    ]
    if breaking_non_critical:
        print(f"\n⚠️  BREAKING CHANGES ({len(breaking_non_critical)}):")
        for i, change in enumerate(breaking_non_critical, 1):
            print(f"\n  {i}. 📍 {change.field_change.path}")
            print(f"     Тип изменения: {change.field_change.change_type}")
            print(f"     Причина: {change.reason}")

            if verbose and change.recommendations:
                print(f"     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    # Добавленные поля
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

                impact_icon = {
                    ChangeImpact.CRITICAL: "🔴",
                    ChangeImpact.HIGH: "🟠",
                    ChangeImpact.MEDIUM: "🟡",
                    ChangeImpact.LOW: "🟢"
                }.get(change.impact, "⚪")

                print(f"  {i}. {impact_icon} {change.field_change.path} [{status}]")
                if verbose:
                    print(f"     Тип: {field.field_type}")
                    if change.reason:
                        print(f"     Причина: {change.reason}")
                    if field.dictionary:
                        print(f"     Справочник: {field.dictionary}")

    # Удаленные поля
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

                impact_icon = {
                    ChangeImpact.CRITICAL: "🔴",
                    ChangeImpact.HIGH: "🟠",
                    ChangeImpact.MEDIUM: "🟡",
                    ChangeImpact.LOW: "🟢"
                }.get(change.impact, "⚪")

                print(f"  {i}. {impact_icon} {change.field_change.path} [{status}]")
                if verbose:
                    print(f"     Тип: {field.field_type}")
                    if change.reason:
                        print(f"     Причина: {change.reason}")

    # Non-breaking changes (только модификации)
    non_breaking_modifications = [
        c for c in result.non_breaking_changes
        if c.field_change.change_type == "modified"
    ]
    if non_breaking_modifications:
        print(f"\n✅ NON-BREAKING ИЗМЕНЕНИЯ ({len(non_breaking_modifications)}):")
        for i, change in enumerate(non_breaking_modifications, 1):
            print(f"  {i}. 📍 {change.field_change.path}")
            print(f"     {change.reason}")

            if verbose and change.recommendations:
                print(f"     Рекомендации:")
                for rec in change.recommendations:
                    print(f"       ✓ {rec}")

    print("\n" + "=" * 80)

    # Итоговая рекомендация
    if result.critical_changes:
        print("\n⚠️  ВНИМАНИЕ: Обнаружены критические изменения!")
        print("   Требуется обязательное обновление сценариев.")
    elif result.breaking_changes:
        print("\n⚠️  ВНИМАНИЕ: Обнаружены breaking changes!")
        print("   Рекомендуется обновить сценарии.")
    else:
        print("\n✅ Все изменения совместимы с предыдущей версией.")

    print()


def print_markdown_report(result):
    """Вывести отчет в Markdown формате"""
    print(f"# Отчет об изменениях JSON Schema\n")
    print(f"**Дата анализа:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"**Старая версия:** `{result.old_schema.name}`  ")
    print(f"**Новая версия:** `{result.new_schema.name}`\n")

    # Получаем статистику
    additions = result.get_changes_by_classification(ChangeClassification.ADDITION)
    removals = result.get_changes_by_classification(ChangeClassification.REMOVAL)

    print("## 📈 Статистика\n")
    print(f"- **Всего изменений:** {len(result.analyzed_changes)}")
    print(f"- **Breaking changes:** {len(result.breaking_changes)}")
    print(f"- **Non-breaking changes:** {len(result.non_breaking_changes)}")
    print(f"- **Добавлено полей:** {len(additions)}")
    print(f"- **Удалено полей:** {len(removals)}")
    print(f"- **Критические:** {len(result.critical_changes)}")
    print(f"- **Высокое влияние:** {len(result.high_impact_changes)}\n")

    if result.critical_changes:
        print("## 🚨 Критические изменения\n")
        for i, change in enumerate(result.critical_changes, 1):
            print(f"### {i}. `{change.field_change.path}`\n")
            print(f"- **Тип:** {change.field_change.change_type}")
            print(f"- **Причина:** {change.reason}")
            if change.recommendations:
                print(f"- **Рекомендации:**")
                for rec in change.recommendations:
                    print(f"  - {rec}")
            print()

    breaking_non_critical = [
        c for c in result.breaking_changes
        if c not in result.critical_changes
    ]
    if breaking_non_critical:
        print("## ⚠️ Breaking Changes\n")
        for i, change in enumerate(breaking_non_critical, 1):
            print(f"### {i}. `{change.field_change.path}`\n")
            print(f"- **Тип:** {change.field_change.change_type}")
            print(f"- **Причина:** {change.reason}\n")

    if additions:
        print("## ➕ Добавленные поля\n")
        for i, change in enumerate(additions, 1):
            field = change.field_change.new_meta
            if field:
                status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                print(f"{i}. `{change.field_change.path}` [{status}] - {change.reason}")
        print()

    if removals:
        print("## ➖ Удаленные поля\n")
        for i, change in enumerate(removals, 1):
            field = change.field_change.old_meta
            if field:
                status = "О" if field.is_required else ("УО" if field.is_conditional else "Н")
                print(f"{i}. `{change.field_change.path}` [{status}] - {change.reason}")
        print()


def save_json_report(result, output_path: Path):
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
    logger.info(f"🔍 Анализ изменений между версиями...")
    logger.info(f"   Старая: {args.old_schema}")
    logger.info(f"   Новая: {args.new_schema}")

    try:
        analyzer = ChangeAnalyzer()
        result = analyzer.analyze_changes(args.old_schema, args.new_schema)

        # Фильтрация по флагам
        if args.only_critical:
            result.analyzed_changes = result.critical_changes
        elif args.only_breaking:
            result.analyzed_changes = result.breaking_changes

        # Вывод отчета
        if args.format == "text":
            print_text_report(result, verbose=args.verbose)
        elif args.format == "markdown":
            print_markdown_report(result)
        elif args.format == "json":
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

        # Сохранение в файл
        if args.output:
            save_json_report(result, args.output)

        # Код возврата
        if result.critical_changes:
            logger.warning(f"⚠️  Найдено {len(result.critical_changes)} критических изменений!")
            sys.exit(1)
        else:
            logger.info(f"✅ Анализ завершен успешно")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
