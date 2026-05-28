"""Tests for minimal JSON Schema fixtures (TD-10.1).

Verifies that SchemaParser correctly parses v070_minimal.json and v072_minimal.json,
covering all field types, constraints, formats, and SpEL conditions.
"""
import pytest
from pathlib import Path

from src.parsers.schema_parser import SchemaParser
from src.core.spel_parser import SpelParser


FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "schemas"
V070_PATH = FIXTURES_DIR / "v070_minimal.json"
V072_PATH = FIXTURES_DIR / "v072_minimal.json"


class TestV070FixtureParsing:
    """Test parsing of v070_minimal.json."""

    @pytest.fixture
    def v070_fields(self) -> dict:
        parser = SchemaParser()
        return parser.load_schema(V070_PATH)

    def test_v070_loads_without_errors(self, v070_fields):
        assert v070_fields is not None
        assert len(v070_fields) > 0

    def test_v070_leaf_field_count(self, v070_fields):
        leaf_fields = {
            k for k, v in v070_fields.items()
            if v.field_type not in ("object",) and not v.is_collection
        }
        assert len(leaf_fields) >= 26, (
            f"Expected >= 26 leaf fields, got {len(leaf_fields)}: "
            f"{sorted(leaf_fields)}"
        )

    def test_v070_total_field_count(self, v070_fields):
        # 26 leaf + 4 containers (loanRequest, sendChannelInfo, creditParameters, guarantors) = 30
        assert len(v070_fields) >= 28, (
            f"Expected >= 28 total fields, got {len(v070_fields)}: "
            f"{sorted(v070_fields.keys())}"
        )

    # --- Обязательность: О (alwaysRequired) ---

    def test_v070_required_fields(self, v070_fields):
        required_paths = [
            k for k, v in v070_fields.items()
            if v.is_required and not v.is_conditional
        ]
        assert "loanRequest/creditAmt" in required_paths
        assert "loanRequest/productCdExt" in required_paths
        assert "loanRequest/channelCdExt" in required_paths

    # --- Обязательность: УО (conditionally required) ---

    def test_v070_conditional_fields(self, v070_fields):
        conditional_paths = [
            k for k, v in v070_fields.items()
            if v.is_conditional
        ]
        assert "loanRequest/firstName" in conditional_paths
        assert "loanRequest/additionalInfo" in conditional_paths
        assert "loanRequest/nstAppTypeCdExt" in conditional_paths
        assert "loanRequest/relatedLoanRequestExtId" in conditional_paths

    def test_v070_simple_condition(self, v070_fields):
        field = v070_fields["loanRequest/firstName"]
        assert field.condition is not None
        assert "notNull" in field.condition.expression
        assert "regionCd" in field.condition.expression

    def test_v070_compound_condition(self, v070_fields):
        field = v070_fields["loanRequest/additionalInfo"]
        assert field.condition is not None
        assert "and" in field.condition.expression
        assert "notNull" in field.condition.expression
        assert "in" in field.condition.expression

    def test_v070_array_reference_condition(self, v070_fields):
        field = v070_fields["loanRequest/nstAppTypeCdExt"]
        assert field.condition is not None
        assert "anyMatch" in field.condition.expression
        assert "#rootBean" in field.condition.expression

    def test_v070_nested_compound_condition(self, v070_fields):
        field = v070_fields["loanRequest/relatedLoanRequestExtId"]
        assert field.condition is not None
        assert "and" in field.condition.expression
        assert "eq" in field.condition.expression
        assert "anyMatch" in field.condition.expression

    # --- Обязательность: Н (optional) ---

    def test_v070_optional_fields(self, v070_fields):
        optional_paths = [
            k for k, v in v070_fields.items()
            if not v.is_required and not v.is_conditional
            and v.field_type not in ("object",)
            and not v.is_collection
        ]
        assert len(optional_paths) >= 12

    # --- Типы данных ---

    def test_v070_integer_fields(self, v070_fields):
        integer_fields = {k for k, v in v070_fields.items() if v.field_type == "integer"}
        assert "loanRequest/creditAmt" in integer_fields
        assert "loanRequest/productCdExt" in integer_fields
        assert "loanRequest/channelCdExt" in integer_fields

    def test_v070_string_fields(self, v070_fields):
        string_fields = {k for k, v in v070_fields.items() if v.field_type == "string"}
        assert "loanRequest/firstName" in string_fields
        assert "loanRequest/comment" in string_fields

    def test_v070_number_fields(self, v070_fields):
        number_fields = {k for k, v in v070_fields.items() if v.field_type == "number"}
        assert "loanRequest/amount" in number_fields
        assert "loanRequest/interestRate" in number_fields

    def test_v070_boolean_fields(self, v070_fields):
        bool_fields = {k for k, v in v070_fields.items() if v.field_type == "boolean"}
        assert "loanRequest/reprocessFlg" in bool_fields

    def test_v070_object_fields(self, v070_fields):
        object_fields = {k for k, v in v070_fields.items() if v.field_type == "object"}
        assert "loanRequest/sendChannelInfo" in object_fields

    def test_v070_array_fields(self, v070_fields):
        array_fields = {k for k, v in v070_fields.items() if v.is_collection}
        assert "loanRequest/creditParameters" in array_fields
        assert "loanRequest/guarantors" in array_fields

    # --- Constraints ---

    def test_v070_pattern_constraint(self, v070_fields):
        inn = v070_fields["loanRequest/inn"]
        assert "pattern" in inn.constraints
        assert inn.constraints["pattern"] == r"^\d{10,12}$"

    def test_v070_length_constraints(self, v070_fields):
        inn = v070_fields["loanRequest/inn"]
        assert inn.constraints.get("minLength") == 10
        assert inn.constraints.get("maxLength") == 12

    def test_v070_numeric_range_constraints(self, v070_fields):
        amount = v070_fields["loanRequest/amount"]
        assert amount.constraints.get("minimum") == 1000
        assert amount.constraints.get("maximum") == 10000000

    def test_v070_enum_constraint(self, v070_fields):
        status = v070_fields["loanRequest/status"]
        assert "enum" in status.constraints
        assert set(status.constraints["enum"]) == {"DRAFT", "APPROVED", "REJECTED"}

    def test_v070_max_int_length_constraint(self, v070_fields):
        credit_amt = v070_fields["loanRequest/creditAmt"]
        assert credit_amt.constraints.get("maxIntLength") == 10

    # --- Format ---

    def test_v070_date_format(self, v070_fields):
        field = v070_fields["loanRequest/agreementDate"]
        assert field.format == "date"

    def test_v070_datetime_format(self, v070_fields):
        field = v070_fields["loanRequest/extCreateDttm"]
        assert field.format == "date-time"

    def test_v070_uuid_format(self, v070_fields):
        field = v070_fields["loanRequest/requestId"]
        assert field.format == "uuid"

    # --- Dictionary ---

    def test_v070_dictionary_fields(self, v070_fields):
        assert v070_fields["loanRequest/productCdExt"].dictionary == "PRODUCT_TYPE"
        assert v070_fields["loanRequest/channelCdExt"].dictionary == "SALE_CHANNEL"
        assert v070_fields["loanRequest/nstAppTypeCdExt"].dictionary == "NST_APP_TYPE"
        assert v070_fields["loanRequest/regionCd"].dictionary == "REGION"

    # --- Nested objects ---

    def test_v070_nested_object(self, v070_fields):
        parent = v070_fields["loanRequest/sendChannelInfo"]
        assert parent.field_type == "object"

        agg = v070_fields["loanRequest/sendChannelInfo/aggregatorCdExt"]
        assert agg.is_required is True
        assert agg.field_type == "integer"

        src = v070_fields["loanRequest/sendChannelInfo/sourceCdExt"]
        assert src.is_required is False
        assert src.dictionary == "SOURCE_CD"

    # --- Arrays ---

    def test_v070_array_with_items(self, v070_fields):
        arr = v070_fields["loanRequest/creditParameters"]
        assert arr.is_collection is True
        assert arr.field_type == "array"

        product = v070_fields["loanRequest/creditParameters[]/productCdExt"]
        assert product.field_type == "integer"
        assert product.dictionary == "PRODUCT_TYPE"

    def test_v070_second_array(self, v070_fields):
        inn = v070_fields["loanRequest/guarantors[]/inn"]
        assert inn.field_type == "string"
        assert "pattern" in inn.constraints


class TestV072FixtureParsing:
    """Test parsing of v072_minimal.json."""

    @pytest.fixture
    def v072_fields(self) -> dict:
        parser = SchemaParser()
        return parser.load_schema(V072_PATH)

    def test_v072_loads_without_errors(self, v072_fields):
        assert v072_fields is not None
        assert len(v072_fields) > 0

    def test_v072_leaf_field_count(self, v072_fields):
        leaf_fields = {
            k for k, v in v072_fields.items()
            if v.field_type not in ("object",) and not v.is_collection
        }
        assert len(leaf_fields) >= 27, (
            f"Expected >= 27 leaf fields, got {len(leaf_fields)}: "
            f"{sorted(leaf_fields)}"
        )

    # --- New fields in v072 ---

    def test_v072_new_required_field_phone(self, v072_fields):
        field = v072_fields["loanRequest/phone"]
        assert field.field_type == "string"
        assert field.is_required is True
        assert field.constraints.get("minLength") == 10
        assert field.constraints.get("maxLength") == 15

    def test_v072_new_conditional_field_purpose(self, v072_fields):
        field = v072_fields["loanRequest/purposeCdExt"]
        assert field.field_type == "integer"
        assert field.is_conditional is True
        assert field.dictionary == "LOAN_PURPOSE"
        assert "notNull" in field.condition.expression

    def test_v072_new_optional_field_middle_name(self, v072_fields):
        field = v072_fields["loanRequest/middleName"]
        assert field.field_type == "string"
        assert field.is_required is False
        assert field.is_conditional is False
        assert field.constraints.get("maxLength") == 100

    # --- Removed field ---

    def test_v072_removed_reprocess_flg(self, v072_fields):
        assert "loanRequest/reprocessFlg" not in v072_fields

    # --- Modified fields ---

    def test_v072_modified_amount_maximum(self, v072_fields):
        field = v072_fields["loanRequest/amount"]
        assert field.constraints.get("maximum") == 50000000

    def test_v072_modified_inn_pattern(self, v072_fields):
        field = v072_fields["loanRequest/inn"]
        assert field.constraints["pattern"] == r"^\d{10}$"

    # --- Renamed field: sendChannelInfo -> channelInfo ---

    def test_v072_renamed_channel_info(self, v072_fields):
        assert "loanRequest/channelInfo" in v072_fields
        assert "loanRequest/sendChannelInfo" not in v072_fields

    def test_v072_channel_info_nested_fields(self, v072_fields):
        assert "loanRequest/channelInfo/aggregatorCdExt" in v072_fields
        assert "loanRequest/channelInfo/sourceCdExt" in v072_fields


class TestSchemaComparatorDiff:
    """Test SchemaComparator diff between v070 and v072."""

    @pytest.fixture
    def v070_fields(self) -> dict:
        parser = SchemaParser()
        return parser.load_schema(V070_PATH)

    @pytest.fixture
    def v072_fields(self) -> dict:
        parser = SchemaParser()
        return parser.load_schema(V072_PATH)

    @pytest.fixture
    def schema_diff(self, v070_fields, v072_fields):
        from src.core.schema_comparator import SchemaComparator
        comparator = SchemaComparator()
        return comparator.compare(v070_fields, v072_fields)

    def test_added_fields_count(self, schema_diff):
        # phone, purposeCdExt, middleName, channelInfo,
        # channelInfo/aggregatorCdExt, channelInfo/sourceCdExt
        assert len(schema_diff.added_fields) >= 5

    def test_removed_fields_count(self, schema_diff):
        # reprocessFlg, sendChannelInfo,
        # sendChannelInfo/aggregatorCdExt, sendChannelInfo/sourceCdExt
        assert len(schema_diff.removed_fields) >= 3

    def test_modified_fields_count(self, schema_diff):
        assert len(schema_diff.modified_fields) == 2

    def test_amount_modified(self, schema_diff):
        amount_changes = [
            f for f in schema_diff.modified_fields
            if f.path == "loanRequest/amount"
        ]
        assert len(amount_changes) == 1
        assert "constraints" in amount_changes[0].changes

    def test_inn_modified(self, schema_diff):
        inn_changes = [
            f for f in schema_diff.modified_fields
            if f.path == "loanRequest/inn"
        ]
        assert len(inn_changes) == 1
        assert "constraints" in inn_changes[0].changes

    def test_new_field_phone_in_added(self, schema_diff):
        added_paths = [f.path for f in schema_diff.added_fields]
        assert "loanRequest/phone" in added_paths

    def test_removed_reprocess_flg(self, schema_diff):
        removed_paths = [f.path for f in schema_diff.removed_fields]
        assert "loanRequest/reprocessFlg" in removed_paths


class TestSpelConditionParsing:
    """Test that SpEL conditions from fixtures parse correctly."""

    @pytest.fixture
    def v070_fields(self) -> dict:
        parser = SchemaParser()
        return parser.load_schema(V070_PATH)

    def test_simple_not_null_parses(self, v070_fields):
        expr = v070_fields["loanRequest/firstName"].condition.expression
        spel_parser = SpelParser()
        ast = spel_parser.parse(expr)
        assert ast is not None

    def test_compound_and_in_parses(self, v070_fields):
        expr = v070_fields["loanRequest/additionalInfo"].condition.expression
        spel_parser = SpelParser()
        ast = spel_parser.parse(expr)
        assert ast is not None

    def test_any_match_parses(self, v070_fields):
        expr = v070_fields["loanRequest/nstAppTypeCdExt"].condition.expression
        spel_parser = SpelParser()
        ast = spel_parser.parse(expr)
        assert ast is not None

    def test_nested_compound_parses(self, v070_fields):
        expr = v070_fields["loanRequest/relatedLoanRequestExtId"].condition.expression
        spel_parser = SpelParser()
        ast = spel_parser.parse(expr)
        assert ast is not None