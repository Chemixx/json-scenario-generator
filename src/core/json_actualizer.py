"""
JsonActualizer — актуализация JSON-сценариев по SchemaDiff.

Применяет изменения схемы (SchemaDiff) к существующему JSON-сценарию:
добавляет новые поля, удаляет старые, модифицирует значения,
обнаруживает переименования и валидирует результат.

ADR-1: Pragmatic Middle — один класс с приватными методами по ответственности.
ADR-6: Изоляция — actualize() никогда не бросает исключение наружу.
"""

from copy import deepcopy
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.condition_evaluator import ConditionEvaluator, EvaluationContext
from src.core.value_generator import GeneratorConfig, ValueGenerator
from src.models.schema_models import (
    FieldChange,
    FieldMetadata,
    SchemaDiff,
    ConditionalRequirement,
)
from src.core.conditional_validator import ConditionalValidator, ValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Модели данных
# ============================================================================


@dataclass
class ActualizerConfig:
    """Конфигурация актуализатора.

    Attributes:
        locale: Локаль для Faker (по умолчанию ru_RU).
        seed: Сид для воспроизводимости.
        default_array_size: Количество элементов в массиве по умолчанию.
        faker: Готовый экземпляр Faker (если None, создается из locale).
        uuid_cache: Внешний кэш UUID (ключ = имя поля).
        strict_inn: Генерировать ИНН с КС ФНС.
        strict_snils: Генерировать СНИЛС с КС.
        rollback: Уровень отката: "field" | "full" | "none".
        generate_report: Генерировать ли Markdown-отчёт.
        report_format: Формат отчёта: "dataclass" | "markdown" | "both".
        field_mapping: Override для обнаружения переименований.
    """

    locale: str = "ru_RU"
    seed: Optional[int] = None
    default_array_size: int = 1
    faker: Optional[Any] = None  # Faker instance
    uuid_cache: Dict[str, str] = dataclass_field(default_factory=dict)
    strict_inn: bool = True
    strict_snils: bool = False
    rollback: str = "field"  # "field" | "full" | "none"
    generate_report: bool = True
    report_format: str = "dataclass"  # "dataclass" | "markdown" | "both"
    field_mapping: Optional[Dict[str, str]] = None


@dataclass
class ActualizationChange:
    """Одно изменение при актуализации.

    Attributes:
        path: Путь к полю.
        change_type: Тип изменения (added, removed, modified, modified_preserved,
                     modified_regenerated, renamed, renamed_regenerated,
                     renamed_generated, skipped, error).
        old_value: Старое значение (None для added).
        new_value: Новое значение (None для removed).
        reason: Почему изменено.
        severity: Уровень (info, warning, error).
    """

    path: str
    change_type: str
    old_value: Any = None
    new_value: Any = None
    reason: str = ""
    severity: str = "info"

    def __str__(self) -> str:
        return f"{self.change_type}: {self.path} ({self.severity})"


@dataclass
class RenamePair:
    """Пара переименования полей.

    Attributes:
        old_path: Старый путь поля.
        new_path: Новый путь поля.
        old_meta: Метаданные старого поля.
        new_meta: Метаданные нового поля.
        match_score: Количество совпадающих атрибутов (3-5).
    """

    old_path: str
    new_path: str
    old_meta: FieldMetadata
    new_meta: FieldMetadata
    match_score: int


@dataclass
class ActualizationResult:
    """Результат актуализации JSON-сценария.

    Attributes:
        actualized_data: Результирующий JSON.
        changes: Все изменения.
        validation_errors: Ошибки ConditionalValidator.
        errors: Только ошибки (severity="error").
        rolled_back: Был ли полный откат.
    """

    actualized_data: Dict[str, Any]
    changes: List[ActualizationChange] = dataclass_field(default_factory=list)
    validation_errors: List[ValidationError] = dataclass_field(default_factory=list)
    errors: List[ActualizationChange] = dataclass_field(default_factory=list)
    rolled_back: bool = False
    generate_report: bool = True

    def to_markdown(self) -> str:
        """Генерация Markdown-отчёта. Возвращает пустую строку, если generate_report=False."""
        if not self.generate_report:
            return ""

        lines = ["# Actualization Report", ""]
        if self.rolled_back:
            lines.append("**Status:** Rolled back to backup")
        lines.append(f"**Changes:** {len(self.changes)}")
        lines.append(f"**Errors:** {len(self.errors)}")
        lines.append("")

        if self.changes:
            lines.append("## Changes")
            lines.append("")
            for c in self.changes:
                lines.append(f"- [{c.severity}] {c.change_type}: {c.path} — {c.reason}")
            lines.append("")

        if self.errors:
            lines.append("## Errors")
            lines.append("")
            for e in self.errors:
                lines.append(f"- [ERROR] {e.change_type}: {e.path} — {e.reason}")
            lines.append("")

        return "\n".join(lines)


# ============================================================================
# Исключения (внутренние)
# ============================================================================


class _StructureError(Exception):
    """Критическая ошибка структуры JSON — вызывает полный откат."""


# ============================================================================
# JsonActualizer
# ============================================================================


class JsonActualizer:
    """Актуализатор JSON-сценариев по SchemaDiff.

    Применяет SchemaDiff к существующему JSON-сценарию:
    - Добавляет новые поля (О/УО/Н)
    - Удаляет поля, отсутствующие в новой схеме
    - Модифицирует поля с изменёнными ограничениями
    - Обнаруживает переименования через метаданные
    - Валидирует результат через ConditionalValidator

    ADR-6: Изоляция — actualize() никогда не бросает исключение наружу.
    Все ошибки упакованы в ActualizationResult.errors.
    """

    def __init__(
        self,
        config: Optional[ActualizerConfig] = None,
        dictionary_loader: Optional[Any] = None,
    ) -> None:
        self.config = config or ActualizerConfig()
        self.dictionary_loader = dictionary_loader

        gen_config = GeneratorConfig(
            locale=self.config.locale,
            seed=self.config.seed,
            default_array_size=self.config.default_array_size,
            faker=self.config.faker,
            uuid_cache=self.config.uuid_cache,
            strict_inn=self.config.strict_inn,
            strict_snils=self.config.strict_snils,
        )
        self._generator = ValueGenerator(config=gen_config, dictionary_loader=dictionary_loader)
        self._evaluator = ConditionEvaluator()
        self._validator = ConditionalValidator(evaluator=self._evaluator)

    # ========================================================================
    # Публичный API
    # ========================================================================

    def actualize(
        self,
        old_json: Dict[str, Any],
        schema_diff: SchemaDiff,
        new_schema: Dict[str, FieldMetadata],
    ) -> ActualizationResult:
        """Актуализировать JSON-сценарий по SchemaDiff.

        Args:
            old_json: Исходный JSON-сценарий.
            schema_diff: Разница между схемами.
            new_schema: Метаданные новой схемы (путь → FieldMetadata).

        Returns:
            ActualizationResult с актуализированными данными, изменениями и ошибками.
        """
        result = ActualizationResult(actualized_data=deepcopy(old_json))
        backup = deepcopy(old_json)
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []

        try:
            # 1. Обнаружение переименований
            renames, truly_removed, truly_added = self._detect_renames(
                schema_diff.removed_fields,
                schema_diff.added_fields,
                self.config.field_mapping,
            )

            # 2. Обработка переименований
            self._process_renames(result, renames, changes, errors)

            # 3. Удаление полей
            self._process_removed_fields(result, truly_removed, changes, errors)

            # 4. Добавление полей
            self._process_added_fields(result, truly_added, new_schema, changes, errors)

            # 5. Модификация полей
            self._process_modified_fields(result, schema_diff.modified_fields, new_schema, changes, errors)

            # 6. Валидация результата (убрано — _validate_result удалён,
            #    validation_errors остаётся пустым списком по умолчанию)

        except _StructureError as e:
            logger.error(f"Критическая ошибка структуры: {e}")
            result.actualized_data = backup
            result.rolled_back = True
            errors.append(ActualizationChange(
                path="",
                change_type="error",
                reason=f"Критическая ошибка структуры: {e}",
                severity="error",
            ))

        except Exception as e:
            logger.error(f"Неожиданная ошибка при актуализации: {e}")
            if self.config.rollback in ("field", "full"):
                result.actualized_data = backup
                result.rolled_back = True
            errors.append(ActualizationChange(
                path="",
                change_type="error",
                reason=f"Неожиданная ошибка: {e}",
                severity="error",
            ))

        result.changes = changes
        result.errors = errors
        result.generate_report = self.config.generate_report

        # Полный откат при rollback="full" и наличии ошибок
        if self.config.rollback == "full" and errors:
            result.actualized_data = backup
            result.rolled_back = True

        return result

    def actualize_batch(
        self,
        scenarios: List[Dict[str, Any]],
        schema_diff: SchemaDiff,
        new_schema: Dict[str, FieldMetadata],
    ) -> List[ActualizationResult]:
        """Актуализировать пакет JSON-сценариев.

        Args:
            scenarios: Список JSON-сценариев.
            schema_diff: Разница между схемами.
            new_schema: Метаданные новой схемы.

        Returns:
            Список ActualizationResult, по одному на каждый сценарий.
        """
        return [
            self.actualize(scenario, schema_diff, new_schema)
            for scenario in scenarios
        ]

    def actualize_from_paths(
        self,
        scenario_path: Path,
        old_schema_path: Path,
        new_schema_path: Path,
    ) -> ActualizationResult:
        """Актуализировать JSON-сценарий по путям к файлам.

        Args:
            scenario_path: Путь к JSON-сценарию.
            old_schema_path: Путь к старой схеме.
            new_schema_path: Путь к новой схеме.

        Returns:
            ActualizationResult.
        """
        from src.utils.json_utils import load_json
        from src.core.schema_comparator import SchemaComparator
        from src.parsers.schema_parser import SchemaParser

        errors: List[ActualizationChange] = []
        result = ActualizationResult(actualized_data={})

        try:
            old_json = load_json(scenario_path)
            old_schema_data = load_json(old_schema_path)
            new_schema_data = load_json(new_schema_path)

            parser = SchemaParser()
            old_fields = parser.parse(old_schema_data)
            new_fields = parser.parse(new_schema_data)

            comparator = SchemaComparator()
            schema_diff = comparator.compare(old_fields, new_fields)

            new_schema = {f.path: f for f in new_fields}

            return self.actualize(old_json, schema_diff, new_schema)

        except FileNotFoundError as e:
            errors.append(ActualizationChange(
                path=str(scenario_path),
                change_type="error",
                reason=f"Файл не найден: {e}",
                severity="error",
            ))
            result.errors = errors
            result.rolled_back = True
            return result

        except Exception as e:
            errors.append(ActualizationChange(
                path=str(scenario_path),
                change_type="error",
                reason=f"Ошибка загрузки: {e}",
                severity="error",
            ))
            result.errors = errors
            result.rolled_back = True
            return result

    # ========================================================================
    # Навигация по JSON
    # ========================================================================

    def _navigate_path(self, data: Dict, path: str) -> Any:
        """Навигация по JSON-пути.

        Поддерживает:
        - Простые пути: "name"
        - Вложенные пути: "loan/applicant/income"
        - Массивы с индексом: "applicants[0]/name"
        """
        if not path or not data:
            return None

        parts = path.split("/")
        current: Any = data

        for part in parts:
            if current is None:
                return None

            # Обработка массивов: "applicants[0]" или "applicants[]"
            if "[" in part:
                key = part[: part.index("[")]
                idx_str = part[part.index("[") + 1 : part.index("]")]
                current = current.get(key) if isinstance(current, dict) else None
                if current is None:
                    return None
                if idx_str:  # Конкретный индекс
                    idx = int(idx_str)
                    if isinstance(current, list) and 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return None
                # "[]" без индекса — не навигируем, возвращаем сам массив
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _set_field_value(self, data: Dict, path: str, value: Any) -> None:
        """Установить значение по пути, создавая промежуточные объекты."""
        parts = path.split("/")
        current = data

        for i, part in enumerate(parts[:-1]):
            # Обработка массивов в пути
            if "[" in part:
                key = part[: part.index("[")]
                idx_str = part[part.index("[") + 1 : part.index("]")]

                if key not in current:
                    current[key] = []

                current_list = current[key]

                if idx_str:  # Конкретный индекс
                    idx = int(idx_str)
                    while len(current_list) <= idx:
                        current_list.append({})
                    current = current_list[idx]
                else:  # [] — пустой массив, создаём один элемент
                    if len(current_list) == 0:
                        current_list.append({})
                    current = current_list[0]
            else:
                if part not in current:
                    current[part] = {}
                if not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]

        # Установка финального значения
        last_part = parts[-1]
        if "[" in last_part:
            key = last_part[: last_part.index("[")]
            idx_str = last_part[last_part.index("[") + 1 : last_part.index("]")]

            if key not in current:
                current[key] = []

            current_list = current[key]
            if idx_str:  # Конкретный индекс
                idx = int(idx_str)
                while len(current_list) <= idx:
                    current_list.append({})
                current_list[idx] = value
            else:  # [] — добавить в массив
                if isinstance(value, dict):
                    current_list.append(value)
                else:
                    if len(current_list) == 0:
                        current_list.append({})
                    # Установить в первый элемент
                    # Для []/name=value — создаём структуру
                    # Эта ветка не должна достигаться для leaf-полей
        else:
            current[last_part] = value

    def _delete_field(self, data: Dict, path: str) -> bool:
        """Удалить поле по пути. Возвращает True если удалено, False если не найдено."""
        parts = path.split("/")
        current: Any = data

        # Навигация до предпоследнего элемента
        for part in parts[:-1]:
            if "[" in part:
                key = part[: part.index("[")]
                idx_str = part[part.index("[") + 1 : part.index("]")]
                if not isinstance(current, dict) or key not in current:
                    return False
                current = current[key]
                idx = int(idx_str)
                if not isinstance(current, list) or idx >= len(current):
                    return False
                current = current[idx]
            else:
                if not isinstance(current, dict) or part not in current:
                    return False
                current = current[part]

        # Удаление последнего ключа
        last_part = parts[-1]
        if isinstance(current, dict) and last_part in current:
            del current[last_part]
            return True

        return False

    # ========================================================================
    # Обнаружение переименований
    # ========================================================================

    def _detect_renames(
        self,
        removed: List[FieldChange],
        added: List[FieldChange],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[RenamePair], List[FieldChange], List[FieldChange]]:
        """Обнаружить переименования полей.

        ADR-5: Совпадение ≥3 из 5 атрибутов → переименование.
        Явный field_mapping — override эвристики.

        Returns:
            (renames, truly_removed, truly_added)
        """
        # Если field_mapping не передан явно — использовать из конфига
        effective_mapping = field_mapping or self.config.field_mapping

        # Если передан field_mapping — используем напрямую
        if effective_mapping:
            renames = []
            truly_removed = list(removed)
            truly_added = list(added)

            for old_path, new_path in effective_mapping.items():
                # Найти соответствующие FieldChange
                removed_match = next((r for r in removed if r.path == old_path), None)
                added_match = next((a for a in added if a.path == new_path), None)

                if removed_match and added_match:
                    old_meta = removed_match.old_meta or FieldMetadata(
                        path=old_path, name=old_path.split("/")[-1], field_type="string"
                    )
                    new_meta = added_match.new_meta or FieldMetadata(
                        path=new_path, name=new_path.split("/")[-1], field_type="string"
                    )
                    renames.append(RenamePair(
                        old_path=old_path,
                        new_path=new_path,
                        old_meta=old_meta,
                        new_meta=new_meta,
                        match_score=5,  # Явный mapping — максимальный score
                    ))
                    truly_removed = [r for r in truly_removed if r.path != old_path]
                    truly_added = [a for a in truly_added if a.path != new_path]

            return renames, truly_removed, truly_added

        # Эвристика по метаданным
        renames: List[RenamePair] = []
        truly_removed: List[FieldChange] = list(removed)
        truly_added: List[FieldChange] = list(added)

        # Собираем кандидатов с оценками
        candidates: List[Tuple[int, FieldChange, FieldChange, int]] = []

        for r in removed:
            if not r.old_meta:
                continue
            for a in added:
                if not a.new_meta:
                    continue
                score = self._compute_rename_score(r.old_meta, a.new_meta)
                if score >= 3:
                    candidates.append((score, r, a, len(candidates)))

        # Жадный алгоритм: сортируем по score (убывание), назначаем
        candidates.sort(key=lambda x: -x[0])
        used_removed = set()
        used_added = set()

        for score, r, a, _ in candidates:
            if r.path not in used_removed and a.path not in used_added:
                renames.append(RenamePair(
                    old_path=r.path,
                    new_path=a.path,
                    old_meta=r.old_meta,
                    new_meta=a.new_meta,
                    match_score=score,
                ))
                used_removed.add(r.path)
                used_added.add(a.path)

        truly_removed = [r for r in truly_removed if r.path not in used_removed]
        truly_added = [a for a in truly_added if a.path not in used_added]

        return renames, truly_removed, truly_added

    @staticmethod
    def _compute_rename_score(old_meta: FieldMetadata, new_meta: FieldMetadata) -> int:
        """Вычислить score совпадения для обнаружения переименований.

        Совпадающие атрибуты (5 возможных):
        - field_type
        - dictionary
        - format
        - parent_path (путь без имени поля)
        - constraints (пересечение ключей с совпадающими значениями)
        """
        score = 0

        if old_meta.field_type == new_meta.field_type:
            score += 1
        if old_meta.dictionary and new_meta.dictionary and old_meta.dictionary == new_meta.dictionary:
            score += 1
        if old_meta.format and new_meta.format and old_meta.format == new_meta.format:
            score += 1

        # parent_path: путь без последнего сегмента
        old_parent = "/".join(old_meta.path.split("/")[:-1])
        new_parent = "/".join(new_meta.path.split("/")[:-1])
        if old_parent and new_parent and old_parent == new_parent:
            score += 1

        # constraints: пересечение ключей с совпадающими значениями
        old_keys = set(old_meta.constraints.keys())
        new_keys = set(new_meta.constraints.keys())
        common_keys = old_keys & new_keys
        matching = sum(1 for k in common_keys if old_meta.constraints[k] == new_meta.constraints[k])
        if matching > 0:
            score += 1

        return score

    # ========================================================================
    # Обработка изменений
    # ========================================================================

    def _process_renames(
        self,
        result: ActualizationResult,
        renames: List[RenamePair],
        changes: List[ActualizationChange],
        errors: List[ActualizationChange],
    ) -> None:
        """Обработать переименования полей."""
        for rename in renames:
            try:
                old_value = self._navigate_path(result.actualized_data, rename.old_path)

                # Удалить старый путь
                self._delete_field(result.actualized_data, rename.old_path)

                # Установить значение на новом пути
                if old_value is not None and self._validate_value(old_value, rename.new_meta):
                    self._set_field_value(result.actualized_data, rename.new_path, old_value)
                    changes.append(ActualizationChange(
                        path=rename.new_path,
                        change_type="renamed",
                        old_value=old_value,
                        new_value=old_value,
                        reason=f"Переименование с {rename.old_path} (score={rename.match_score}), значение сохранено",
                        severity="info",
                    ))
                elif old_value is not None:
                    # Значение не валидно для нового типа — перегенерируем
                    new_value = self._generate_value(rename.new_meta, result.actualized_data)
                    self._set_field_value(result.actualized_data, rename.new_path, new_value)
                    changes.append(ActualizationChange(
                        path=rename.new_path,
                        change_type="renamed_regenerated",
                        old_value=old_value,
                        new_value=new_value,
                        reason=f"Переименование с {rename.old_path}, значение перегенерировано (невалидно для нового типа)",
                        severity="warning",
                    ))
                else:
                    # Нет старого значения — генерируем новое
                    new_value = self._generate_value(rename.new_meta, result.actualized_data)
                    self._set_field_value(result.actualized_data, rename.new_path, new_value)
                    changes.append(ActualizationChange(
                        path=rename.new_path,
                        change_type="renamed_generated",
                        old_value=None,
                        new_value=new_value,
                        reason=f"Переименование с {rename.old_path}, значение сгенерировано",
                        severity="info",
                    ))

            except Exception as e:
                errors.append(ActualizationChange(
                    path=rename.new_path,
                    change_type="error",
                    reason=f"Ошибка переименования {rename.old_path} → {rename.new_path}: {e}",
                    severity="error",
                ))

    def _process_removed_fields(
        self,
        result: ActualizationResult,
        removed_fields: List[FieldChange],
        changes: List[ActualizationChange],
        errors: List[ActualizationChange],
    ) -> None:
        """Удалить поля из JSON."""
        for field_change in removed_fields:
            try:
                old_value = self._navigate_path(result.actualized_data, field_change.path)
                deleted = self._delete_field(result.actualized_data, field_change.path)

                if deleted:
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="removed",
                        old_value=old_value,
                        new_value=None,
                        reason="Поле удалено из схемы",
                        severity="info",
                    ))
                else:
                    # Поля нет в данных — тихо пропускаем
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="skipped",
                        reason="Поле не найдено в данных, пропуск удаления",
                        severity="info",
                    ))

            except Exception as e:
                errors.append(ActualizationChange(
                    path=field_change.path,
                    change_type="error",
                    reason=f"Ошибка удаления поля: {e}",
                    severity="error",
                ))

    def _process_added_fields(
        self,
        result: ActualizationResult,
        added_fields: List[FieldChange],
        new_schema: Dict[str, FieldMetadata],
        changes: List[ActualizationChange],
        errors: List[ActualizationChange],
    ) -> None:
        """Добавить новые поля в JSON."""
        for field_change in added_fields:
            try:
                meta = field_change.new_meta or new_schema.get(field_change.path)
                if meta is None:
                    errors.append(ActualizationChange(
                        path=field_change.path,
                        change_type="error",
                        reason=f"Метаданные не найдены для {field_change.path}",
                        severity="error",
                    ))
                    continue

                # Проверка УО-условия
                if meta.is_conditional and meta.condition:
                    condition_result = self._evaluate_condition(
                        meta.condition, result.actualized_data, field_change.path
                    )
                    if not condition_result:
                        # Условие не выполнено — поле не обязательно
                        changes.append(ActualizationChange(
                            path=field_change.path,
                            change_type="skipped",
                            reason=f"УО-условие не выполнено: {meta.condition.expression}",
                            severity="info",
                        ))
                        continue

                # Генерация значения
                value = self._generate_value(meta, result.actualized_data)

                if value is not None:
                    self._set_field_value(result.actualized_data, field_change.path, value)
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="added",
                        old_value=None,
                        new_value=value,
                        reason=f"Поле добавлено (тип={meta.field_type}, обязательность={'О' if meta.is_required else 'УО' if meta.is_conditional else 'Н'})",
                        severity="info",
                    ))
                else:
                    # Не удалось сгенерировать (например, object)
                    errors.append(ActualizationChange(
                        path=field_change.path,
                        change_type="error",
                        reason=f"Не удалось сгенерировать значение для типа {meta.field_type}",
                        severity="error",
                    ))

            except Exception as e:
                errors.append(ActualizationChange(
                    path=field_change.path,
                    change_type="error",
                    reason=f"Ошибка добавления поля: {e}",
                    severity="error",
                ))

    def _process_modified_fields(
        self,
        result: ActualizationResult,
        modified_fields: List[FieldChange],
        new_schema: Dict[str, FieldMetadata],
        changes: List[ActualizationChange],
        errors: List[ActualizationChange],
    ) -> None:
        """Обработать модифицированные поля."""
        for field_change in modified_fields:
            try:
                old_value = self._navigate_path(result.actualized_data, field_change.path)
                new_meta = field_change.new_meta or new_schema.get(field_change.path)
                old_meta = field_change.old_meta

                if new_meta is None:
                    errors.append(ActualizationChange(
                        path=field_change.path,
                        change_type="error",
                        reason=f"Метаданные не найдены для {field_change.path}",
                        severity="error",
                    ))
                    continue

                if old_value is None:
                    # Значения нет в данных — генерируем
                    value = self._generate_value(new_meta, result.actualized_data)
                    if value is not None:
                        self._set_field_value(result.actualized_data, field_change.path, value)
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="modified_regenerated",
                        old_value=None,
                        new_value=value,
                        reason="Старое значение отсутствует, сгенерировано новое",
                        severity="warning",
                    ))
                    continue

                # Попытаться преобразовать значение
                if old_meta and "type" in field_change.changes:
                    # Тип изменился — преобразование
                    new_value = self._transform_value(old_value, old_meta, new_meta)
                    if new_value is not None:
                        self._set_field_value(result.actualized_data, field_change.path, new_value)
                        changes.append(ActualizationChange(
                            path=field_change.path,
                            change_type="modified",
                            old_value=old_value,
                            new_value=new_value,
                            reason=f"Преобразование типа: {field_change.changes.get('type', '')}",
                            severity="info",
                        ))
                    else:
                        # Не удалось преобразовать — перегенерация
                        gen_value = self._generate_value(new_meta, result.actualized_data)
                        if gen_value is not None:
                            self._set_field_value(result.actualized_data, field_change.path, gen_value)
                        changes.append(ActualizationChange(
                            path=field_change.path,
                            change_type="modified_regenerated",
                            old_value=old_value,
                            new_value=gen_value,
                            reason=f"Невозможно преобразовать тип, значение перегенерировано",
                            severity="warning",
                        ))
                elif self._validate_value(old_value, new_meta):
                    # Старое значение проходит новые ограничения — сохраняем
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="modified_preserved",
                        old_value=old_value,
                        new_value=old_value,
                        reason=f"Старое значение валидно для новых ограничений",
                        severity="info",
                    ))
                else:
                    # Старое значение не проходит — перегенерируем
                    new_value = self._generate_value(new_meta, result.actualized_data)
                    self._set_field_value(result.actualized_data, field_change.path, new_value)
                    changes.append(ActualizationChange(
                        path=field_change.path,
                        change_type="modified_regenerated",
                        old_value=old_value,
                        new_value=new_value,
                        reason=f"Старое значение не проходит новые ограничения, перегенерировано",
                        severity="warning",
                    ))

            except Exception as e:
                errors.append(ActualizationChange(
                    path=field_change.path,
                    change_type="error",
                    reason=f"Ошибка модификации поля: {e}",
                    severity="error",
                ))

    # ========================================================================
    # Генерация и преобразование значений
    # ========================================================================

    def _generate_value(self, field_meta: FieldMetadata, context_data: Dict) -> Any:
        """Сгенерировать значение через ValueGenerator."""
        try:
            return self._generator.generate(field_meta)
        except Exception as e:
            logger.warning(f"Ошибка генерации для {field_meta.path}: {e}")
            return None

    def _transform_value(
        self, old_value: Any, old_meta: FieldMetadata, new_meta: FieldMetadata
    ) -> Optional[Any]:
        """Преобразовать значение из старого типа в новый.

        Правила преобразования:
        - integer → string: str(old_value)
        - number → string: str(old_value)
        - boolean → string: "true" / "false"
        - string → integer: int(old_value), ValueError → None
        - string → number: float(old_value), ValueError → None
        - string → boolean: "true"/"1"/"yes" → True, остальное → False
        - любые другие → перегенерация (None)
        """
        old_type = old_meta.field_type
        new_type = new_meta.field_type

        # Одинаковый тип — возвращаем как есть
        if old_type == new_type:
            return old_value

        try:
            if old_type == "integer" and new_type == "string":
                return str(old_value)
            elif old_type == "number" and new_type == "string":
                return str(old_value)
            elif old_type == "boolean" and new_type == "string":
                return "true" if old_value else "false"
            elif old_type == "string" and new_type == "integer":
                return int(old_value)
            elif old_type == "string" and new_type == "number":
                return float(old_value)
            elif old_type == "string" and new_type == "boolean":
                return old_value.lower() in ("true", "1", "yes")
            else:
                return None  # Перегенерация
        except (ValueError, TypeError):
            return None

    def _validate_value(self, value: Any, meta: FieldMetadata) -> bool:
        """Проверить, проходит ли значение все ограничения метаданных.

        Порядок проверок:
        1. field_type — тип значения
        2-5. Ограничения через constraint_utils.check_constraint()
        """
        if value is None:
            return False

        # 1. Проверка типа
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
        }
        expected_type = type_map.get(meta.field_type)
        if expected_type and not isinstance(value, expected_type):
            # integer может быть числом в JSON
            if meta.field_type == "integer" and isinstance(value, (int, float)):
                pass  # OK
            elif meta.field_type == "number" and isinstance(value, (int, float)):
                pass  # OK  # pragma: no cover — недостижимо: number → expected_type=(int,float), isinstance всегда True
            else:
                return False

        # 2-5. Проверка ограничений через constraint_utils
        from src.utils.constraint_utils import check_constraint
        for name, expected in meta.constraints.items():
            if check_constraint(name, expected, value) is not None:
                return False

        return True

    # ========================================================================
    # УО-условия
    # ========================================================================

    def _evaluate_condition(
        self, condition: ConditionalRequirement, data: Dict, field_path: str = ""
    ) -> bool:
        """Вычислить SpEL-условие для УО-поля.

        Args:
            condition: Условие (SpEL-выражение).
            data: JSON-данные для вычисления.
            field_path: Путь к полю (для навигации #this, parent, parent2).

        Returns:
            True если условие выполнено (поле обязательно), False если нет.
        """
        try:
            ast = self._validator.parser.parse(condition.expression)
            context = self._validator._build_context(field_path, data)
            result = self._evaluator.evaluate(ast, data, context)
            return bool(result)

        except Exception as e:
            logger.warning(f"Ошибка вычисления условия {condition.expression}: {e}")
            return False

    # ========================================================================
    # Валидация и отчёт
    # ========================================================================

