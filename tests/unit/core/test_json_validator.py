"""
Unit-тесты для JsonValidator.
Покрывает: ValidatorConfig, иерархия ошибок, ValidationResult, 5 шагов валидации.
"""
import json

import pytest
from src.core.json_validator import (
    ValidatorConfig,
    BaseValidationError,
    SchemaError,
    RequiredError,
    ConditionalError,
    ConstraintError,
    DictionaryError,
    ValidationResult,
    ValidationStatistics,
    JsonValidator,
)
from src.models.schema_models import FieldMetadata, ConditionalRequirement


class TestValidatorConfig:
    def test_default_values(self):
        config = ValidatorConfig()
        assert config.check_schema is True
        assert config.check_required is True
        assert config.check_conditional is True
        assert config.check_constraints is True
        assert config.check_dictionaries is False
        assert config.include_dq_codes is False
        assert config.strict is False
        assert config.output_format == "tree"
        assert config.show_full_paths is True

    def test_all_steps_disabled(self):
        config = ValidatorConfig(
            check_schema=False,
            check_required=False,
            check_conditional=False,
            check_constraints=False,
        )
        assert config.check_schema is False
        assert config.check_required is False
        assert config.check_conditional is False
        assert config.check_constraints is False

    def test_invalid_output_format_raises(self):
        with pytest.raises(ValueError):
            ValidatorConfig(output_format="invalid")


class TestErrorHierarchy:
    def test_schema_error_step(self):
        err = SchemaError(path="x/y", message="test")
        assert err.step == "schema"
        assert err.severity == "error"

    def test_required_error_step(self):
        err = RequiredError(path="x/y", message="test", requirement_type="null")
        assert err.step == "required"
        assert err.requirement_type == "null"

    def test_conditional_error_step(self):
        err = ConditionalError(path="x/y", message="test", requirement_type="missing")
        assert err.step == "conditional"
        assert err.requirement_type == "missing"

    def test_constraint_error_step(self):
        err = ConstraintError(path="x/y", message="test", constraint_name="maxLength")
        assert err.step == "constraint"

    def test_dictionary_error_step(self):
        err = DictionaryError(path="x/y", message="test", dictionary_name="DICT")
        assert err.step == "dictionary"


class TestValidationResult:
    def test_is_valid_no_errors(self):
        result = ValidationResult()
        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_is_valid_with_errors(self):
        result = ValidationResult(
            required_errors=[RequiredError(path="x", message="test")]
        )
        result.is_valid = False
        assert result.is_valid is False
        assert result.error_count == 1

    def test_all_errors_property(self):
        result = ValidationResult(
            schema_errors=[SchemaError(path="a", message="s")],
            required_errors=[RequiredError(path="b", message="r")],
        )
        assert len(result.all_errors) == 2

    def test_to_dict(self):
        result = ValidationResult()
        d = result.to_dict()
        assert "is_valid" in d
        assert "error_count" in d


# =============================================================================
# Тесты JsonValidator: 5 шагов валидации
# =============================================================================


class TestStep1SchemaValidation:
    """Шаг 1: Структурная валидация JSON Schema."""

    def test_valid_data(self):
        validator = JsonValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        result = validator.validate({"name": "test"}, raw_schema=schema)
        assert result.is_valid is True
        assert len(result.schema_errors) == 0

    def test_invalid_type(self):
        validator = JsonValidator()
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer"}},
            "required": ["age"]
        }
        result = validator.validate({"age": "not_int"}, raw_schema=schema, schema_fields={})
        assert len(result.schema_errors) >= 1
        assert result.schema_errors[0].validator == "type"

    def test_missing_required_in_schema(self):
        validator = JsonValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        result = validator.validate({}, raw_schema=schema, schema_fields={})
        assert len(result.schema_errors) >= 1

    def test_nested_error(self):
        validator = JsonValidator()
        schema = {
            "type": "object",
            "properties": {
                "loanRequest": {
                    "type": "object",
                    "properties": {"creditAmt": {"type": "integer"}},
                    "required": ["creditAmt"]
                }
            },
            "required": ["loanRequest"]
        }
        result = validator.validate({"loanRequest": {}}, raw_schema=schema, schema_fields={})
        assert len(result.schema_errors) >= 1

    def test_json_path_normalization(self):
        validator = JsonValidator()
        assert validator._normalize_json_path("$.loanRequest.creditAmt") == "loanRequest/creditAmt"
        assert validator._normalize_json_path("$") == ""

    def test_step1_disabled(self):
        validator = JsonValidator(config=ValidatorConfig(check_schema=False))
        schema = {"type": "object", "required": ["x"]}
        result = validator.validate({}, raw_schema=schema, schema_fields={})
        assert len(result.schema_errors) == 0


class TestStep2RequiredFields:
    """Шаг 2: Обязательные поля (О)."""

    def test_field_present(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
        }
        result = validator.validate({"name": "test"}, schema_fields=fields)
        assert len(result.required_errors) == 0

    def test_field_null(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert len(result.required_errors) == 1
        assert result.required_errors[0].requirement_type == "null"

    def test_field_missing(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
        }
        result = validator.validate({}, schema_fields=fields)
        assert len(result.required_errors) == 1
        assert result.required_errors[0].requirement_type == "missing"

    def test_not_required_field(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=False)
        }
        result = validator.validate({}, schema_fields=fields)
        assert len(result.required_errors) == 0

    def test_nested_required_field(self):
        validator = JsonValidator()
        fields = {
            "loanRequest/creditAmt": FieldMetadata(
                path="loanRequest/creditAmt", name="creditAmt", field_type="integer", is_required=True
            )
        }
        result = validator.validate({"loanRequest": {}}, schema_fields=fields)
        assert len(result.required_errors) == 1
        assert result.required_errors[0].requirement_type == "missing"

    def test_dq_code_included(self):
        validator = JsonValidator(config=ValidatorConfig(include_dq_codes=True))
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=True, always_required_dq_code=12750001
            )
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert result.required_errors[0].dq_code == 12750001


class TestStep3ConditionalFields:
    """Шаг 3: Условно обязательные поля (УО)."""

    def test_delegates_to_conditional_validator(self):
        validator = JsonValidator()
        fields = {
            "loanRequest/pledges": FieldMetadata(
                path="loanRequest/pledges", name="pledges", field_type="string",
                is_required=False, is_conditional=True,
                condition=ConditionalRequirement(
                    expression="eq(#root.loanRequest.creditAmt, 100000)",
                    message="Залог обязателен"
                )
            )
        }
        data = {"loanRequest": {"creditAmt": 100000, "pledges": None}}
        result = validator.validate(data, schema_fields=fields)
        assert len(result.conditional_errors) == 1

    def test_wrapping_in_conditional_error(self):
        validator = JsonValidator()
        fields = {
            "loanRequest/pledges": FieldMetadata(
                path="loanRequest/pledges", name="pledges", field_type="string",
                is_required=False, is_conditional=True,
                condition=ConditionalRequirement(
                    expression="eq(#root.loanRequest.creditAmt, 100000)",
                    message="Залог обязателен"
                )
            )
        }
        data = {"loanRequest": {"creditAmt": 100000, "pledges": None}}
        result = validator.validate(data, schema_fields=fields)
        assert result.conditional_errors[0].step == "conditional"
        assert result.conditional_errors[0].original_error is not None

    def test_dq_code_included(self):
        validator = JsonValidator(config=ValidatorConfig(include_dq_codes=True))
        fields = {
            "loanRequest/pledges": FieldMetadata(
                path="loanRequest/pledges", name="pledges", field_type="string",
                is_required=False, is_conditional=True,
                condition=ConditionalRequirement(
                    expression="eq(#root.loanRequest.creditAmt, 100000)",
                    message="Залог обязателен",
                    dq_code=12750037
                )
            )
        }
        data = {"loanRequest": {"creditAmt": 100000, "pledges": None}}
        result = validator.validate(data, schema_fields=fields)
        assert result.conditional_errors[0].dq_code == 12750037

    def test_null_vs_missing(self):
        validator = JsonValidator()
        fields = {
            "loanRequest/pledges": FieldMetadata(
                path="loanRequest/pledges", name="pledges", field_type="string",
                is_required=False, is_conditional=True,
                condition=ConditionalRequirement(
                    expression="eq(#root.loanRequest.creditAmt, 100000)",
                    message="Залог обязателен"
                )
            )
        }
        # missing
        data_missing = {"loanRequest": {"creditAmt": 100000}}
        result = validator.validate(data_missing, schema_fields=fields)
        assert result.conditional_errors[0].requirement_type == "missing"

    def test_no_conditional_fields(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=False)
        }
        result = validator.validate({"name": "test"}, schema_fields=fields)
        assert len(result.conditional_errors) == 0

    def test_spel_error_continues(self):
        """Ошибка SpEL не должна падать — ConditionalValidator пропускает поле."""
        validator = JsonValidator()
        fields = {
            "loanRequest/pledges": FieldMetadata(
                path="loanRequest/pledges", name="pledges", field_type="string",
                is_required=False, is_conditional=True,
                condition=ConditionalRequirement(
                    expression="invalid_spel_syntax((",
                    message="Залог обязателен"
                )
            )
        }
        data = {"loanRequest": {"pledges": None}}
        result = validator.validate(data, schema_fields=fields)
        # ConditionalValidator catches the error and skips
        assert result.is_valid is True


class TestStep4Constraints:
    """Шаг 4: Ограничения значений."""

    def test_min_length_valid(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"minLength": 3}
            )
        }
        result = validator.validate({"name": "abc"}, schema_fields=fields)
        assert len(result.constraint_errors) == 0

    def test_min_length_invalid(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"minLength": 5}
            )
        }
        result = validator.validate({"name": "ab"}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_max_length_invalid(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"maxLength": 3}
            )
        }
        result = validator.validate({"name": "abcdef"}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_pattern_invalid(self):
        validator = JsonValidator()
        fields = {
            "code": FieldMetadata(
                path="code", name="code", field_type="string",
                is_required=False, constraints={"pattern": r"^\d+$"}
            )
        }
        result = validator.validate({"code": "abc"}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_minimum_invalid(self):
        validator = JsonValidator()
        fields = {
            "amount": FieldMetadata(
                path="amount", name="amount", field_type="integer",
                is_required=False, constraints={"minimum": 0}
            )
        }
        result = validator.validate({"amount": -5}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_maximum_invalid(self):
        validator = JsonValidator()
        fields = {
            "amount": FieldMetadata(
                path="amount", name="amount", field_type="integer",
                is_required=False, constraints={"maximum": 100}
            )
        }
        result = validator.validate({"amount": 200}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_enum_invalid(self):
        validator = JsonValidator()
        fields = {
            "status": FieldMetadata(
                path="status", name="status", field_type="string",
                is_required=False, constraints={"enum": ["A", "B"]}
            )
        }
        result = validator.validate({"status": "X"}, schema_fields=fields)
        assert len(result.constraint_errors) == 1

    def test_null_field_skipped(self):
        """null-поля пропускаются в Шаге 4."""
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"minLength": 5}
            )
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert len(result.constraint_errors) == 0

    def test_strict_mode(self):
        """strict=True: constraint ошибки = error."""
        validator = JsonValidator(config=ValidatorConfig(strict=True))
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"maxLength": 3}
            )
        }
        result = validator.validate({"name": "abcdef"}, schema_fields=fields)
        assert result.constraint_errors[0].severity == "error"
        assert result.is_valid is False

    def test_lenient_mode(self):
        """strict=False (default): constraint ошибки = warning."""
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=False, constraints={"maxLength": 3}
            )
        }
        result = validator.validate({"name": "abcdef"}, schema_fields=fields)
        assert result.constraint_errors[0].severity == "warning"
        assert result.is_valid is True  # warnings не влияют


class TestStep5Dictionaries:
    """Шаг 5: Валидация справочников."""

    def test_valid_value_by_name(self):
        from src.models.dictionary_models import Dictionary, DictionaryEntry
        from src.loaders.dictionary_loader import DictionaryLoader

        dict_obj = Dictionary(
            name="PRODUCT_TYPE",
            entries=[DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")]
        )
        loader = DictionaryLoader()
        loader._cache["PRODUCT_TYPE"] = dict_obj

        validator = JsonValidator(
            config=ValidatorConfig(check_dictionaries=True),
            dictionary_loader=loader
        )
        fields = {
            "productCd": FieldMetadata(
                path="productCd", name="productCd", field_type="string",
                is_required=False, dictionary="PRODUCT_TYPE"
            )
        }
        result = validator.validate({"productCd": "PACL"}, schema_fields=fields)
        assert len(result.dictionary_errors) == 0

    def test_valid_value_by_code(self):
        from src.models.dictionary_models import Dictionary, DictionaryEntry
        from src.loaders.dictionary_loader import DictionaryLoader

        dict_obj = Dictionary(
            name="PRODUCT_TYPE",
            entries=[DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")]
        )
        loader = DictionaryLoader()
        loader._cache["PRODUCT_TYPE"] = dict_obj

        validator = JsonValidator(
            config=ValidatorConfig(check_dictionaries=True),
            dictionary_loader=loader
        )
        fields = {
            "productCd": FieldMetadata(
                path="productCd", name="productCd", field_type="integer",
                is_required=False, dictionary="PRODUCT_TYPE"
            )
        }
        result = validator.validate({"productCd": 10410001}, schema_fields=fields)
        assert len(result.dictionary_errors) == 0

    def test_invalid_value(self):
        from src.models.dictionary_models import Dictionary, DictionaryEntry
        from src.loaders.dictionary_loader import DictionaryLoader

        dict_obj = Dictionary(
            name="PRODUCT_TYPE",
            entries=[DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")]
        )
        loader = DictionaryLoader()
        loader._cache["PRODUCT_TYPE"] = dict_obj

        validator = JsonValidator(
            config=ValidatorConfig(check_dictionaries=True),
            dictionary_loader=loader
        )
        fields = {
            "productCd": FieldMetadata(
                path="productCd", name="productCd", field_type="string",
                is_required=False, dictionary="PRODUCT_TYPE"
            )
        }
        result = validator.validate({"productCd": "X"}, schema_fields=fields)
        assert len(result.dictionary_errors) == 1
        assert result.dictionary_errors[0].dictionary_name == "PRODUCT_TYPE"

    def test_loader_none(self):
        """dictionary_loader=None: Шаг 5 пропускается."""
        validator = JsonValidator(config=ValidatorConfig(check_dictionaries=True))
        fields = {
            "productCd": FieldMetadata(
                path="productCd", name="productCd", field_type="string",
                is_required=False, dictionary="PRODUCT_TYPE"
            )
        }
        result = validator.validate({"productCd": "X"}, schema_fields=fields)
        assert len(result.dictionary_errors) == 0

    def test_no_dictionary_field(self):
        """Поля без dictionary пропускаются."""
        validator = JsonValidator(config=ValidatorConfig(check_dictionaries=True))
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=False)
        }
        result = validator.validate({"name": "test"}, schema_fields=fields)
        assert len(result.dictionary_errors) == 0

    def test_null_field_skipped(self):
        """null-поля пропускаются в Шаге 5."""
        from src.models.dictionary_models import Dictionary, DictionaryEntry
        from src.loaders.dictionary_loader import DictionaryLoader

        dict_obj = Dictionary(
            name="PRODUCT_TYPE",
            entries=[DictionaryEntry(code=10410001, name="PACL", dictionary_type="PRODUCT_TYPE")]
        )
        loader = DictionaryLoader()
        loader._cache["PRODUCT_TYPE"] = dict_obj

        validator = JsonValidator(
            config=ValidatorConfig(check_dictionaries=True),
            dictionary_loader=loader
        )
        fields = {
            "productCd": FieldMetadata(
                path="productCd", name="productCd", field_type="string",
                is_required=False, dictionary="PRODUCT_TYPE"
            )
        }
        result = validator.validate({"productCd": None}, schema_fields=fields)
        assert len(result.dictionary_errors) == 0


class TestDQCodes:
    def test_dq_codes_disabled(self):
        """include_dq_codes=False (default): dq_code=None во всех ошибках."""
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=True, always_required_dq_code=12750001
            )
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert result.required_errors[0].dq_code is None

    def test_dq_codes_enabled(self):
        validator = JsonValidator(config=ValidatorConfig(include_dq_codes=True))
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=True, always_required_dq_code=12750001
            )
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert result.required_errors[0].dq_code == 12750001

    def test_dq_codes_fallback_to_none(self):
        """Если DQ-код отсутствует в FieldMetadata — None."""
        validator = JsonValidator(config=ValidatorConfig(include_dq_codes=True))
        fields = {
            "name": FieldMetadata(
                path="name", name="name", field_type="string",
                is_required=True  # no always_required_dq_code
            )
        }
        result = validator.validate({"name": None}, schema_fields=fields)
        assert result.required_errors[0].dq_code is None


class TestValidationResultIntegration:
    def test_both_inputs(self):
        """raw_schema + schema_fields → Шаг 1 + Шаги 2-5."""
        validator = JsonValidator()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
        }
        result = validator.validate({"name": "test"}, raw_schema=schema, schema_fields=fields)
        assert result.is_valid is True

    def test_no_inputs(self):
        """raw_schema=None, schema_fields=None → is_valid=True."""
        validator = JsonValidator()
        result = validator.validate({})
        assert result.is_valid is True

    def test_statistics(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True),
            "age": FieldMetadata(
                path="age", name="age", field_type="integer",
                is_required=False, constraints={"minimum": 0}
            ),
        }
        result = validator.validate({"name": "test", "age": 25}, schema_fields=fields)
        assert result.statistics.total_fields == 2
        assert result.statistics.required_fields == 1
        assert result.statistics.constraint_fields == 1


class TestValidateBatch:
    def test_multiple_scenarios(self):
        validator = JsonValidator()
        fields = {
            "name": FieldMetadata(path="name", name="name", field_type="string", is_required=True)
        }
        scenarios = [
            ({"name": "test"}, None, fields),
            ({}, None, fields),
        ]
        results = validator.validate_batch(scenarios)
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False

    def test_empty_list(self):
        validator = JsonValidator()
        results = validator.validate_batch([])
        assert len(results) == 0


class TestValidateFromPaths:
    def test_happy_path(self, tmp_path):
        """Полный цикл: загрузка схемы → парсинг → валидация."""
        validator = JsonValidator()
        schema = {
            "type": "object",
            "stageName": "call1",
            "version": "072",
            "direction": "request",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        data = {"name": "test"}
        schema_file = tmp_path / "schema.json"
        data_file = tmp_path / "data.json"
        schema_file.write_text(json.dumps(schema), encoding="utf-8")
        data_file.write_text(json.dumps(data), encoding="utf-8")
        result = validator.validate_from_paths(data_file, schema_file)
        assert result.is_valid is True

    def test_schema_metadata_extraction(self):
        validator = JsonValidator()
        schema = {"stageName": "call1", "version": "072", "direction": "request"}
        meta = validator._extract_schema_metadata(schema)
        assert meta["stage_name"] == "call1"
        assert meta["version"] == "072"
        assert meta["direction"] == "request"


class TestToSummary:
    def test_tree_format(self):
        result = ValidationResult(
            required_errors=[
                RequiredError(path="loanRequest/productCd", message="Обязательное поле отсутствует")
            ]
        )
        result.is_valid = False
        summary = result.to_summary(format="tree")
        assert "НЕ ПРОЙДЕНА" in summary

    def test_flat_format(self):
        result = ValidationResult(
            required_errors=[
                RequiredError(path="loanRequest/productCd", message="Обязательное поле отсутствует")
            ]
        )
        result.is_valid = False
        summary = result.to_summary(format="flat")
        assert "REQUIRED" in summary

    def test_success_summary(self):
        result = ValidationResult()
        summary = result.to_summary(format="tree")
        assert "ПРОЙДЕНА" in summary