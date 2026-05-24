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
# ИМПОРТЫ
# ============================================================================

from src.analyzers import ChangeAnalyzer
from src.models import AnalysisResult, ImpactLevel
from src.utils import get_logger
from src.utils.icons import Icon
from src.formatters import ReportFormatter

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


def save_json_report(result: AnalysisResult, output_path: Path):
    """Сохранить отчет в JSON"""
    formatter = ReportFormatter()
    report = formatter.format_json(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"{Icon.SUCCESS} Отчет сохранен: {output_path}")


def main():
    """Главная функция"""
    # Encoding safety: предотвратить UnicodeEncodeError на cp1251
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except (OSError, ValueError):
            pass

    args = parse_arguments()

    # Проверка существования файлов
    if not args.old_schema.exists():
        logger.error(f"{Icon.ERROR} Файл не найден: {args.old_schema}")
        sys.exit(1)

    if not args.new_schema.exists():
        logger.error(f"{Icon.ERROR} Файл не найден: {args.new_schema}")
        sys.exit(1)

    # Анализ изменений
    logger.info(f"{Icon.INFO} Анализ изменений между версиями...")
    logger.info(f"   Старая: {args.old_schema}")
    logger.info(f"   Новая: {args.new_schema}")

    try:
        analyzer = ChangeAnalyzer()
        result = analyzer.analyze_changes(args.old_schema, args.new_schema)

        # =====================================================================
        # ИСПОЛЬЗУЕМ FORMATTER
        # =====================================================================
        formatter = ReportFormatter()

        # Вывод отчета
        if args.format == "text":
            # Фильтрация для текстового формата
            if args.only_critical:
                filtered_result = AnalysisResult(
                    old_version=result.old_version,
                    new_version=result.new_version,
                    analyzed_changes=result.critical_changes,
                    analysis_date=result.analysis_date
                )
                report = formatter.format_text(
                    filtered_result,
                    verbose=args.verbose,
                    show_recommendations=args.verbose
                )
            elif args.only_breaking:
                filtered_result = AnalysisResult(
                    old_version=result.old_version,
                    new_version=result.new_version,
                    analyzed_changes=result.breaking_changes,
                    analysis_date=result.analysis_date
                )
                report = formatter.format_text(
                    filtered_result,
                    verbose=args.verbose,
                    show_recommendations=args.verbose
                )
            else:
                report = formatter.format_text(
                    result,
                    verbose=args.verbose,
                    show_recommendations=args.verbose
                )
            print(report)

        elif args.format == "markdown":
            markdown = formatter.format_markdown(result)
            print(markdown)

        elif args.format == "json":
            json_data = formatter.format_json(result)
            print(json.dumps(json_data, ensure_ascii=False, indent=2))

        # Сохранение в файл
        if args.output:
            save_json_report(result, args.output)

        # Код возврата
        if result.has_critical_changes():
            logger.warning(f"{Icon.WARNING} Найдено {len(result.critical_changes)} критических изменений!")
            sys.exit(1)
        else:
            logger.info(f"{Icon.SUCCESS} Анализ завершен успешно")
            sys.exit(0)

    except Exception as e:
        logger.error(f"{Icon.ERROR} Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
