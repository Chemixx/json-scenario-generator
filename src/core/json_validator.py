"""
JsonValidator — оркестратор валидации JSON-данных против схемы.

Объединяет 5 независимых шагов:
1. Структурная валидация (JSON Schema Draft 2019-09)
2. Обязательные поля (О)
3. Условно обязательные поля (УО) — делегирует ConditionalValidator
4. Ограничения значений (constraints) — через constraint_utils
5. Справочники — через DictionaryLoader
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models.schema_models import ConditionalRequirement, FieldMetadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Конфигурация
# =============================================================================

@dataclass
class ValidatorConfig:
    """Конфигурация валидатора."""
    check_schema: bool = True
    check_required: bool = True
    check_conditional: bool = True
    check_constraints: bool = True
    check_dictionaries: bool = False
    include_dq_codes: bool = False
    strict: bool = False
    output_format: str = "tree"
    show_full_paths: bool = True

    def __post_init__(self):
        if self.output_format not in ("tree", "flat"):
            raise ValueError(f"output_format must be 'tree' or 'flat', got '{self.output_format}'")


# =============================================================================
# Иерархия ошибок
# =============================================================================

@dataclass
class BaseValidationError:
    """Базовая ошибка валидации."""
    path: str
    message: str
    severity: str = "error"
    step: str = ""


@dataclass
class SchemaError(BaseValidationError):
    """Ошибка структурной валидации (Шаг 1)."""
    schema_path: str = ""
    validator: str = ""
    expected: Any = None
    actual: Any = None

    def __post_init__(self):
        self.step = "schema"


@dataclass
class RequiredError(BaseValidationError):
    """Ошибка обязательного поля (Шаг 2)."""
    dq_code: Optional[int] = None
    requirement_type: str = "missing"

    def __post_init__(self):
        self.step = "required"


@dataclass
class ConditionalError(BaseValidationError):
    """Ошибка условно обязательного поля (Шаг 3)."""
    original_error: Optional[Any] = None
    dq_code: Optional[int] = None
    requirement_type: str = "missing"

    def __post_init__(self):
        self.step = "conditional"


@dataclass
class ConstraintError(BaseValidationError):
    """Ошибка ограничения значения (Шаг 4)."""
    constraint_name: str = ""
    constraint_value: Any = None
    actual_value: Any = None

    def __post_init__(self):
        self.step = "constraint"


@dataclass
class DictionaryError(BaseValidationError):
    """Ошибка справочного значения (Шаг 5)."""
    dictionary_name: str = ""
    actual_value: Any = None
    dq_code: Optional[int] = None
    resolved_value: str = ""  # Расшифровка: "PACL (10410001)"

    def __post_init__(self):
        self.step = "dictionary"


# =============================================================================
# Статистика и результат
# =============================================================================

@dataclass
class ValidationStatistics:
    """Статистика валидации."""
    total_fields: int = 0
    required_fields: int = 0
    conditional_fields: int = 0
    constraint_fields: int = 0
    dictionary_fields: int = 0
    schema_error_count: int = 0
    required_error_count: int = 0
    conditional_error_count: int = 0
    constraint_error_count: int = 0
    constraint_warning_count: int = 0
    dictionary_error_count: int = 0
    duration_ms: float = 0.0


@dataclass
class ValidationResult:
    """Результат валидации JSON-данных."""
    is_valid: bool = True
    schema_errors: List[SchemaError] = field(default_factory=list)
    required_errors: List[RequiredError] = field(default_factory=list)
    conditional_errors: List[ConditionalError] = field(default_factory=list)
    constraint_errors: List[ConstraintError] = field(default_factory=list)
    dictionary_errors: List[DictionaryError] = field(default_factory=list)
    statistics: ValidationStatistics = field(default_factory=ValidationStatistics)

    @property
    def all_errors(self) -> List[BaseValidationError]:
        return (
            self.schema_errors + self.required_errors
            + self.conditional_errors + self.constraint_errors
            + self.dictionary_errors
        )

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.all_errors if e.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.all_errors if e.severity == "warning")

    def to_summary(self, format: str = "tree") -> str:
        """Текстовое резюме для CLI."""
        status = "ПРОЙДЕНА" if self.is_valid else "НЕ ПРОЙДЕНА"
        header = f"Валидация {status} ({self.error_count} ошибок, {self.warning_count} предупреждений)"

        if self.error_count == 0 and self.warning_count == 0:
            return f"Валидация {status}"

        if format == "flat":
            lines = [header]
            errors = [e for e in self.all_errors if e.severity == "error"]
            warnings = [e for e in self.all_errors if e.severity == "warning"]
            if errors:
                lines.append("")
                lines.append("ОШИБКИ:")
                for e in errors:
                    lines.append(f"  [{e.step.upper()}]  {e.path} — {e.message}")
            if warnings:
                lines.append("")
                lines.append("ПРЕДУПРЕЖДЕНИЯ:")
                for e in warnings:
                    lines.append(f"  [{e.step.upper()}]  {e.path} — {e.message}")
            return "\n".join(lines)

        # format == "tree"
        lines = [header]
        # Group errors by parent path
        grouped: Dict[str, List] = {}
        for e in self.all_errors:
            parts = e.path.split("/")
            parent = parts[0] if len(parts) > 1 else ""
            grouped.setdefault(parent, []).append(e)

        for parent, errs in sorted(grouped.items()):
            if parent:
                lines.append(f"\n{parent}")
            for e in errs:
                lines.append(f"   [{e.step.upper()}] {e.path} — {e.message}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "schema_errors": len(self.schema_errors),
            "required_errors": len(self.required_errors),
            "conditional_errors": len(self.conditional_errors),
            "constraint_errors": len(self.constraint_errors),
            "dictionary_errors": len(self.dictionary_errors),
            "duration_ms": self.statistics.duration_ms,
        }


# =============================================================================
# Оркестратор валидации
# =============================================================================

class JsonValidator:
    """Оркестратор валидации JSON-данных против схемы."""

    def __init__(
        self,
        config: Optional[ValidatorConfig] = None,
        dictionary_loader: Optional[Any] = None,
        registry: Optional[Any] = None,  # DictionaryRegistry, Any для избежания циклического импорта
    ) -> None:
        self.config = config or ValidatorConfig()
        self._dictionary_loader = dictionary_loader
        self._registry = registry
        self._conditional_validator = None  # lazy init

    def _get_conditional_validator(self):
        if self._conditional_validator is None:
            from src.core.conditional_validator import get_conditional_validator
            self._conditional_validator = get_conditional_validator()
        return self._conditional_validator

    def validate(
        self,
        data: Dict[str, Any],
        raw_schema: Optional[Dict[str, Any]] = None,
        schema_fields: Optional[Dict[str, FieldMetadata]] = None,
    ) -> ValidationResult:
        start_time = time.monotonic()
        result = ValidationResult()

        # Шаг 1: Структурная валидация
        if raw_schema and self.config.check_schema:
            result.schema_errors = self._check_schema(data, raw_schema)

        # Шаги 2-5: На основе метаданных полей
        if schema_fields:
            if self.config.check_required:
                result.required_errors = self._check_required(data, schema_fields)
            if self.config.check_conditional:
                result.conditional_errors = self._check_conditional(data, schema_fields)
            if self.config.check_constraints:
                result.constraint_errors = self._check_constraints(data, schema_fields)
            if self.config.check_dictionaries and (self._dictionary_loader is not None or self._registry is not None):
                result.dictionary_errors = self._check_dictionaries(data, schema_fields)

        # Очистка DQ-кодов если выключены
        if not self.config.include_dq_codes:
            for err in result.required_errors:
                err.dq_code = None
            for err in result.conditional_errors:
                err.dq_code = None
            for err in result.dictionary_errors:
                err.dq_code = None

        # Статистика
        self._collect_statistics(schema_fields, result)
        result.statistics.duration_ms = (time.monotonic() - start_time) * 1000
        result.is_valid = result.error_count == 0
        return result

    def _check_schema(self, data: Dict, raw_schema: Dict) -> List[SchemaError]:
        import jsonschema
        validator_cls = jsonschema.validators.Draft201909Validator
        validator = validator_cls(raw_schema)
        errors = []
        for error in validator.iter_errors(data):
            path = self._normalize_json_path(error.json_path)
            errors.append(SchemaError(
                path=path,
                message=error.message,
                severity="error",
                schema_path=error.json_path,
                validator=error.validator,
                expected=error.validator_value,
                actual=error.instance,
            ))
        return errors

    def _check_required(self, data: Dict, schema_fields: Dict[str, FieldMetadata]) -> List[RequiredError]:
        errors = []
        for path, field_meta in schema_fields.items():
            if not field_meta.is_required:
                continue
            dq = field_meta.always_required_dq_code if self.config.include_dq_codes else None
            if not self._path_exists(data, path):
                errors.append(RequiredError(
                    path=path,
                    message=f"Обязательное поле отсутствует: {path}",
                    severity="error",
                    dq_code=dq,
                    requirement_type="missing",
                ))
            else:
                value = self._get_value_by_path(data, path)
                if value is None:
                    errors.append(RequiredError(
                        path=path,
                        message=f"Обязательное поле = null: {path}",
                        severity="error",
                        dq_code=dq,
                        requirement_type="null",
                    ))
        return errors

    def _check_conditional(self, data: Dict, schema_fields: Dict[str, FieldMetadata]) -> List[ConditionalError]:
        conditional_fields = {
            k: v for k, v in schema_fields.items() if v.is_conditional and v.condition
        }
        if not conditional_fields:
            return []

        cv = self._get_conditional_validator()
        raw_errors = cv.validate(data, conditional_fields)
        errors = []
        for raw in raw_errors:
            requirement_type = "null" if self._path_exists(data, raw.path) else "missing"
            dq = None
            if self.config.include_dq_codes:
                dq = raw.dq_code or self._get_field_dq_code(schema_fields, raw.path, "conditional")
            errors.append(ConditionalError(
                path=raw.path,
                message=raw.message,
                severity="error",
                original_error=raw,
                dq_code=dq,
                requirement_type=requirement_type,
            ))
        return errors

    def _check_constraints(self, data: Dict, schema_fields: Dict[str, FieldMetadata]) -> List[ConstraintError]:
        from src.utils.constraint_utils import check_constraint
        errors = []
        for path, field_meta in schema_fields.items():
            if not field_meta.constraints:
                continue
            value = self._get_value_by_path(data, path)
            if value is None:
                continue
            for constraint_name, constraint_value in field_meta.constraints.items():
                error_msg = check_constraint(constraint_name, constraint_value, value)
                if error_msg is not None:
                    severity = "error" if self.config.strict else "warning"
                    errors.append(ConstraintError(
                        path=path,
                        message=error_msg,
                        severity=severity,
                        constraint_name=constraint_name,
                        constraint_value=constraint_value,
                        actual_value=value,
                    ))
        return errors

    def _check_dictionaries(self, data: Dict, schema_fields: Dict[str, FieldMetadata]) -> List[DictionaryError]:
        errors = []
        for path, field_meta in schema_fields.items():
            if not field_meta.has_dictionary():
                continue
            value = self._get_value_by_path(data, path)
            if value is None:
                continue

            # Prefer Registry (O(1) by name)
            if self._registry is not None:
                dictionary = self._registry.get(field_meta.dictionary)
            elif self._dictionary_loader is not None:
                try:
                    dictionary = self._dictionary_loader.get_cached_dictionary(field_meta.dictionary)
                except Exception:
                    dictionary = None
            else:
                dictionary = None

            if dictionary is not None:
                # Проверяем значение по коду (int) и по названию (str)
                found = False
                try:
                    val_int = int(value)
                    found = dictionary.contains_code(val_int)
                except (ValueError, TypeError):
                    pass
                if not found:
                    val_str = str(value)
                    found = dictionary.contains_name(val_str)
                if not found:
                    dq = field_meta.dictionary_dq_code if self.config.include_dq_codes else None
                    # Resolve value for human-readable output
                    resolved = ""
                    if self._registry is not None:
                        try:
                            val_int = int(value)
                            resolved = self._registry.resolve(field_meta.dictionary, val_int)
                        except (ValueError, TypeError):
                            resolved = str(value)
                    errors.append(DictionaryError(
                        path=path,
                        message=f"Значение '{value}' не найдено в справочнике '{field_meta.dictionary}'",
                        severity="error",
                        dictionary_name=field_meta.dictionary,
                        actual_value=value,
                        dq_code=dq,
                        resolved_value=resolved,
                    ))
        return errors

    # =========================================================================
    # Утилиты
    # =========================================================================

    @staticmethod
    def _normalize_json_path(json_path: str) -> str:
        """$.loanRequest.creditAmt → loanRequest/creditAmt"""
        if not json_path or json_path == "$":
            return ""
        path = json_path
        if path.startswith("$."):
            path = path[2:]
        elif path.startswith("$"):
            path = path[1:]
        return path.replace(".", "/")

    def _path_exists(self, data: Dict, path: str) -> bool:
        """Проверяет наличие ключа по пути (отличает missing от null)."""
        if not path or data is None:
            return False
        parts = path.split("/")
        current = data
        for part in parts:
            if current is None or not isinstance(current, dict):
                return False
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))
                if key not in current:
                    return False
                current = current[key]
                if not isinstance(current, list) or index >= len(current):
                    return False
                current = current[index]
            else:
                if part not in current:
                    return False
                current = current[part]
        return True

    @staticmethod
    def _get_value_by_path(data: Dict, path: str) -> Any:
        """Извлечь значение по пути 'loanRequest/creditAmt'."""
        if not path:
            return None
        parts = path.split("/")
        current = data
        for part in parts:
            if current is None:
                return None
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _get_field_dq_code(self, schema_fields: Dict[str, FieldMetadata], path: str, dq_type: str) -> Optional[int]:
        """Извлечь DQ-код из FieldMetadata по типу."""
        meta = schema_fields.get(path)
        if meta is None:
            return None
        if dq_type == "conditional":
            return meta.conditional_dq_code
        return None

    def _collect_statistics(self, schema_fields: Optional[Dict[str, FieldMetadata]], result: ValidationResult) -> None:
        if schema_fields is None:
            return
        stats = result.statistics
        stats.total_fields = len(schema_fields)
        stats.required_fields = sum(1 for m in schema_fields.values() if m.is_required)
        stats.conditional_fields = sum(1 for m in schema_fields.values() if m.is_conditional)
        stats.constraint_fields = sum(1 for m in schema_fields.values() if m.constraints)
        stats.dictionary_fields = sum(1 for m in schema_fields.values() if m.has_dictionary())
        stats.schema_error_count = len(result.schema_errors)
        stats.required_error_count = len(result.required_errors)
        stats.conditional_error_count = len(result.conditional_errors)
        stats.constraint_error_count = sum(1 for e in result.constraint_errors if e.severity == "error")
        stats.constraint_warning_count = sum(1 for e in result.constraint_errors if e.severity == "warning")
        stats.dictionary_error_count = len(result.dictionary_errors)

    def validate_batch(
        self,
        scenarios: List[Tuple[Dict[str, Any], Optional[Dict[str, Any]], Optional[Dict[str, FieldMetadata]]]],
    ) -> List[ValidationResult]:
        """Валидировать несколько сценариев."""
        return [self.validate(data, raw_schema, schema_fields) for data, raw_schema, schema_fields in scenarios]

    def validate_from_paths(self, json_path: Path, schema_path: Path) -> ValidationResult:
        """Загрузить схему и данные из файлов, валидировать."""
        from src.utils.json_utils import load_json
        from src.parsers.schema_parser import SchemaParser

        raw_schema = load_json(schema_path)
        meta = self._extract_schema_metadata(raw_schema)
        parser = SchemaParser()
        schema_fields = parser.parse_schema(raw_schema)
        data = load_json(json_path)
        return self.validate(data, raw_schema=raw_schema, schema_fields=schema_fields)

    def _extract_schema_metadata(self, raw_schema: Dict) -> Dict[str, Any]:
        """Извлечь stageName, version, direction из корня JSON Schema."""
        return {
            "stage_name": raw_schema.get("stageName", ""),
            "version": raw_schema.get("version", ""),
            "direction": raw_schema.get("direction", ""),
            "data_quality": raw_schema.get("dataQuality", False),
        }