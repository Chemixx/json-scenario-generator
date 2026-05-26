"""
Unit-тесты для ConditionalValidator.

Покрывает:
- Валидация УО полей
- SpEL-условия различных типов (in, eq, and, or, anyMatch)
- Вложенные пути
- Array-индексы
- Граничные случаи

Требования:
- REQ-5.1: Валидация УО полей по SpEL-условию
- REQ-5.2 to REQ-5.9: Поддержка SpEL операторов
- REQ-5.10 to REQ-5.13: Навигация (#this, #rootBean, #parent)
- REQ-5.14 to REQ-5.18: Генерация ValidationError
- REQ-5.19 to REQ-5.20: Поддержка путей
- REQ-5.21 to REQ-5.24: Code quality
"""

import pytest
from src.core.conditional_validator import ConditionalValidator, ValidationError, get_conditional_validator
from src.models.schema_models import FieldMetadata, ConditionalRequirement
from src.core.condition_evaluator import ConditionEvaluator


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def evaluator():
    """Создать ConditionEvaluator"""
    return ConditionEvaluator()


@pytest.fixture
def validator(evaluator):
    """Создать ConditionalValidator"""
    return ConditionalValidator(evaluator=evaluator)


@pytest.fixture
def simple_field_metadata():
    """Простое поле без условия"""
    return FieldMetadata(
        path="loanRequest/creditAmt",
        name="creditAmt",
        field_type="integer",
        is_required=False,
        is_conditional=False
    )


@pytest.fixture
def conditional_field_metadata():
    """УО поле с condition"""
    return FieldMetadata(
        path="loanRequest/pledges",
        name="pledges",
        field_type="object",
        is_required=False,
        is_conditional=True,
        condition=ConditionalRequirement(
            expression="eq(#root.loanRequest.loanTypeCd, 10340001)",
            message="Залог обязателен для кредита наличными",
            dq_code=12345
        )
    )


@pytest.fixture
def in_condition_field():
    """УО поле с in() условием"""
    return FieldMetadata(
        path="loanRequest/productCdExt",
        name="productCdExt",
        field_type="integer",
        is_required=False,
        is_conditional=True,
        condition=ConditionalRequirement(
            expression="in(#this.productCd, 10410001, 10410002)",
            message="Продукт PACL или TOPUP"
        )
    )


@pytest.fixture
def and_condition_field():
    """УО поле с and() условием"""
    return FieldMetadata(
        path="loanRequest/extField",
        name="extField",
        field_type="string",
        is_required=False,
        is_conditional=True,
        condition=ConditionalRequirement(
            expression="and(eq(#parent.channelCd, 10620001), notNull(#parent.name))",
            message="Поле обязательно при канале 10620001 и заполненном name"
        )
    )


@pytest.fixture
def sample_data_simple():
    """Простые тестовые данные"""
    return {
        "loanRequest": {
            "creditAmt": 100000,
            "loanTypeCd": 10340001
        }
    }


@pytest.fixture
def sample_data_with_pledges():
    """Данные с заполненным залогом"""
    return {
        "loanRequest": {
            "creditAmt": 100000,
            "loanTypeCd": 10340001,
            "pledges": {"type": "realty"}
        }
    }


@pytest.fixture
def sample_data_nested():
    """Вложенные данные"""
    return {
        "loanRequest": {
            "channelCd": 10620001,
            "name": "Test",
            "extField": "value"
        }
    }


# =============================================================================
# Test Class: TestBasicValidation
# =============================================================================

class TestBasicValidation:
    """Базовые тесты валидации УО полей"""

    def test_conditional_field_required_when_condition_met(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.1: УО поле обязательно когда условие выполнено"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert len(errors) == 1
        assert errors[0].path == "loanRequest/pledges"
        assert "Залог обязателен" in errors[0].message

    def test_conditional_field_optional_when_condition_not_met(self, validator, conditional_field_metadata):
        """REQ-5.1: УО поле опционально когда условие не выполнено"""
        data = {"loanRequest": {"loanTypeCd": 99999999}}  # Не 10340001
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 0

    def test_conditional_field_filled_when_condition_met(self, validator, conditional_field_metadata, sample_data_with_pledges):
        """REQ-5.1: УО поле заполнено когда условие выполнено — нет ошибок"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_with_pledges, schema_fields)

        assert len(errors) == 0

    def test_non_conditional_field_ignored(self, validator, simple_field_metadata, sample_data_simple):
        """REQ-5.1: Не УО поля игнорируются"""
        schema_fields = {"loanRequest/creditAmt": simple_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert len(errors) == 0

    def test_empty_schema_fields(self, validator, sample_data_simple):
        """REQ-5.21: Пустые поля схемы — нет ошибок"""
        errors = validator.validate(sample_data_simple, {})
        assert len(errors) == 0

    def test_empty_data(self, validator, conditional_field_metadata):
        """REQ-5.21: Пустые данные — нет ошибок"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate({}, schema_fields)
        assert len(errors) == 0

    def test_none_data(self, validator, conditional_field_metadata):
        """REQ-5.21: None данные — нет ошибок"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(None, schema_fields)
        assert len(errors) == 0


# =============================================================================
# Test Class: TestSpelConditions
# =============================================================================

class TestSpelConditions:
    """Тесты SpEL-условий"""

    def test_in_operator_condition(self, validator, in_condition_field):
        """REQ-5.2: in() оператор — условие выполнено"""
        data = {"loanRequest": {"productCd": 10410001}}
        schema_fields = {"loanRequest/productCdExt": in_condition_field}
        errors = validator.validate(data, schema_fields)

        # Условие выполнено, поле null → ошибка
        assert len(errors) == 1

    def test_in_operator_condition_not_met(self, validator, in_condition_field):
        """REQ-5.2: in() оператор — условие не выполнено"""
        data = {"loanRequest": {"productCd": 99999999}}
        schema_fields = {"loanRequest/productCdExt": in_condition_field}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 0

    def test_eq_operator_condition(self, validator):
        """REQ-5.3: eq() оператор"""
        field = FieldMetadata(
            path="loanRequest/nstReasonCdExt",
            name="nstReasonCdExt",
            field_type="integer",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#parent.loanTypeCd, 10340001)",
                message="Обязателен если loanTypeCd == 10340001"
            )
        )
        # loanTypeCd == 10340001 (условие выполнено), но nstReasonCdExt отсутствует (null)
        data = {"loanRequest": {"loanTypeCd": 10340001}}
        errors = validator.validate(data, {"loanRequest/nstReasonCdExt": field})

        assert len(errors) == 1  # Условие выполнено, поле null

    def test_and_condition(self, validator, and_condition_field, sample_data_nested):
        """REQ-5.4: and() оператор — оба условия истинны"""
        schema_fields = {"loanRequest/extField": and_condition_field}
        errors = validator.validate(sample_data_nested, schema_fields)

        # Условие выполнено, но поле заполнено → нет ошибок
        assert len(errors) == 0

    def test_and_condition_one_false(self, validator, and_condition_field):
        """REQ-5.4: and() оператор — одно условие ложно"""
        data = {"loanRequest": {"channelCd": 99999999, "name": "Test"}}
        schema_fields = {"loanRequest/extField": and_condition_field}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 0  # Условие не выполнено

    def test_or_condition(self, validator):
        """REQ-5.5: or() оператор"""
        field = FieldMetadata(
            path="loanRequest/optionalField",
            name="optionalField",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="or(eq(#parent.channelCd, 10620001), eq(#parent.channelCd, 10620002))",
                message="Обязателен для канала 1 или 2"
            )
        )
        data = {"loanRequest": {"channelCd": 10620001}}
        errors = validator.validate(data, {"loanRequest/optionalField": field})

        assert len(errors) == 1  # Условие выполнено

    def test_not_condition(self, validator):
        """REQ-5.8: not() оператор"""
        field = FieldMetadata(
            path="loanRequest/comment",
            name="comment",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="not(eq(#parent.status, 'active'))",
                message="Обязателен если статус не active"
            )
        )
        data = {"loanRequest": {"status": "inactive"}}
        errors = validator.validate(data, {"loanRequest/comment": field})

        assert len(errors) == 1  # not(true) = false, условие не выполнено... стоп
        # not(eq(status, 'active')) = not(false) = true → условие выполнено


# =============================================================================
# Test Class: TestPathNavigation
# =============================================================================

class TestPathNavigation:
    """Тесты навигации по путям"""

    def test_simple_path(self, validator):
        """REQ-5.19: Простой путь"""
        field = FieldMetadata(
            path="fieldName",
            name="fieldName",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(otherField, 10)",
                message="Обязателен если otherField == 10"
            )
        )
        # otherField == 10 (условие выполнено), но fieldName отсутствует (null)
        data = {"otherField": 10}
        errors = validator.validate(data, {"fieldName": field})

        assert len(errors) == 1

    def test_nested_path(self, validator, conditional_field_metadata):
        """REQ-5.19: Вложенный путь loanRequest/pledges"""
        data = {"loanRequest": {"loanTypeCd": 10340001}}
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 1

    def test_array_path(self, validator):
        """REQ-5.20: Путь с массивом"""
        field = FieldMetadata(
            path="creditParameters[0]/productCdExt",
            name="productCdExt",
            field_type="integer",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#parent.productCd, 10410001)",
                message="Обязателен если productCd == 10410001"
            )
        )
        # productCd == 10410001 (условие выполнено), но productCdExt отсутствует (null)
        data = {"creditParameters": [{"productCd": 10410001}]}
        errors = validator.validate(data, {"creditParameters[0]/productCdExt": field})

        assert len(errors) == 1

    def test_rootBean_navigation(self, validator, conditional_field_metadata):
        """REQ-5.10: Навигация #rootBean.path"""
        # condition.expression использует #root.loanRequest.loanTypeCd
        data = {"loanRequest": {"loanTypeCd": 10340001, "pledges": None}}
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 1

    def test_parent_navigation(self, validator, and_condition_field, sample_data_nested):
        """REQ-5.12: Навигация #parent.field"""
        # and_condition_field использует #parent.channelCd и #parent.name
        schema_fields = {"loanRequest/extField": and_condition_field}
        errors = validator.validate(sample_data_nested, schema_fields)

        assert len(errors) == 0  # Поле заполнено


# =============================================================================
# Test Class: TestErrorReporting
# =============================================================================

class TestErrorReporting:
    """Тесты отчётности об ошибках"""

    def test_error_contains_path(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.14: Ошибка содержит path"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert errors[0].path == "loanRequest/pledges"

    def test_error_contains_message(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.15: Ошибка содержит message из условия"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert "Залог обязателен" in errors[0].message

    def test_error_contains_dq_code(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.16: Ошибка содержит dq_code"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert errors[0].dq_code == 12345

    def test_error_contains_expression(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.17: Ошибка содержит condition.expression"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert "eq(" in errors[0].condition_expression

    def test_error_contains_actual_value(self, validator, conditional_field_metadata, sample_data_simple):
        """REQ-5.18: Ошибка содержит actual_value"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert errors[0].actual_value is None

    def test_error_str_representation(self, validator, conditional_field_metadata, sample_data_simple):
        """ValidationError.__str__()"""
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(sample_data_simple, schema_fields)

        assert "loanRequest/pledges" in str(errors[0])
        assert "Залог обязателен" in str(errors[0])


# =============================================================================
# Test Class: TestEdgeCases
# =============================================================================

class TestEdgeCases:
    """Граничные случаи"""

    def test_null_field_value(self, validator, conditional_field_metadata):
        """REQ-5.21: Null значение поля — ошибка"""
        data = {"loanRequest": {"loanTypeCd": 10340001, "pledges": None}}
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 1

    def test_missing_field_in_data(self, validator, conditional_field_metadata):
        """REQ-5.21: Отсутствующее поле в данных — ошибка"""
        data = {"loanRequest": {"loanTypeCd": 10340001}}  # pledges отсутствует
        schema_fields = {"loanRequest/pledges": conditional_field_metadata}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 1

    def test_multiple_errors(self, validator):
        """REQ-5.21: Несколько ошибок валидации"""
        field1 = FieldMetadata(
            path="field1",
            name="field1",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#this.flag, 1)",
                message="Field1 required"
            )
        )
        field2 = FieldMetadata(
            path="field2",
            name="field2",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#this.flag, 1)",
                message="Field2 required"
            )
        )
        data = {"flag": 1}
        schema_fields = {"field1": field1, "field2": field2}
        errors = validator.validate(data, schema_fields)

        assert len(errors) == 2
        assert errors[0].path == "field1"
        assert errors[1].path == "field2"

    def test_condition_evaluation_error(self, validator):
        """REQ-5.21: Ошибка вычисления условия — поле пропускается"""
        field = FieldMetadata(
            path="invalidField",
            name="invalidField",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="invalidSpEL(",  # Некорректное выражение
                message="Invalid"
            )
        )
        data = {"invalidField": None}
        errors = validator.validate(data, {"invalidField": field})

        # Ошибка логируется, поле пропускается
        assert len(errors) == 0

    def test_field_without_condition_but_marked_conditional(self, validator):
        """REQ-5.21: Поле помечено УО но condition=None"""
        field = FieldMetadata(
            path="brokenField",
            name="brokenField",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=None  # Broken state
        )
        data = {"brokenField": None}
        errors = validator.validate(data, {"brokenField": field})

        # Предупреждение логируется, поле пропускается
        assert len(errors) == 0

    def test_auto_generated_message(self, validator):
        """REQ-5.21: Автогенерация message из expression"""
        field = FieldMetadata(
            path="testField",
            name="testField",
            field_type="string",
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="in(#this.productCd, 10410001, 10410002)"
                # message не указан, должен автогенерироваться
            )
        )
        data = {"testField": None, "productCd": 10410001}
        errors = validator.validate(data, {"testField": field})

        assert len(errors) == 1
        assert errors[0].message is not None


# =============================================================================
# Test Class: TestSingleton
# =============================================================================

class TestSingleton:
    """Тесты singleton pattern"""

    def test_get_conditional_validator_returns_instance(self):
        """REQ-5.21: get_conditional_validator() возвращает instance"""
        validator = get_conditional_validator()
        assert isinstance(validator, ConditionalValidator)

    def test_get_conditional_validator_returns_same_instance(self):
        """REQ-5.21: get_conditional_validator() возвращает тот же instance"""
        validator1 = get_conditional_validator()
        validator2 = get_conditional_validator()
        assert validator1 is validator2

    def test_get_conditional_validator_with_custom_evaluator(self, evaluator):
        """REQ-5.21: get_conditional_validator() с кастомным evaluator"""
        # Сбросим singleton
        import src.core.conditional_validator as cv
        cv._validator_instance = None

        validator = get_conditional_validator(evaluator=evaluator)
        assert validator.evaluator is evaluator


# =============================================================================
# Test Class: TestValidationErrorDataclass
# =============================================================================

class TestValidationErrorDataclass:
    """Тесты ValidationError dataclass"""

    def test_validation_error_creation(self):
        """Создание ValidationError"""
        error = ValidationError(
            path="loanRequest/pledges",
            message="Залог обязателен",
            dq_code=12345,
            condition_expression="eq(...)",
            actual_value=None
        )

        assert error.path == "loanRequest/pledges"
        assert error.message == "Залог обязателен"
        assert error.dq_code == 12345
        assert error.condition_expression == "eq(...)"
        assert error.actual_value is None

    def test_validation_error_repr(self):
        """ValidationError.__repr__()"""
        error = ValidationError(
            path="test",
            message="Test error",
            dq_code=None,
            condition_expression="eq()",
            actual_value=None
        )

        repr_str = repr(error)
        assert "ValidationError" in repr_str
        assert "test" in repr_str


# =============================================================================
# Test Class: TestConditionalValidatorRequirementType
# =============================================================================

class TestConditionalValidatorRequirementType:
    """Тесты различения null vs missing в УО-полях."""

    def test_missing_field_requirement_type(self, validator):
        """Поле полностью отсутствует → requirement_type='missing'"""
        field_meta = FieldMetadata(
            path="loanRequest/pledges",
            name="pledges",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#root.loanRequest.creditAmt, 100000)",
                message="Залог обязателен"
            )
        )
        data = {"loanRequest": {"creditAmt": 100000}}
        errors = validator.validate(data, {"loanRequest/pledges": field_meta})
        assert len(errors) == 1
        assert errors[0].requirement_type == "missing"

    def test_null_field_requirement_type(self, validator):
        """Поле существует со значением null → requirement_type='null'"""
        field_meta = FieldMetadata(
            path="loanRequest/pledges",
            name="pledges",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#root.loanRequest.creditAmt, 100000)",
                message="Залог обязателен"
            )
        )
        data = {"loanRequest": {"creditAmt": 100000, "pledges": None}}
        errors = validator.validate(data, {"loanRequest/pledges": field_meta})
        assert len(errors) == 1
        assert errors[0].requirement_type == "null"

    def test_field_present_and_valid(self, validator):
        """Поле присутствует и заполнено → нет ошибки"""
        field_meta = FieldMetadata(
            path="loanRequest/pledges",
            name="pledges",
            field_type="string",
            is_required=False,
            is_conditional=True,
            condition=ConditionalRequirement(
                expression="eq(#root.loanRequest.creditAmt, 100000)",
                message="Залог обязателен"
            )
        )
        data = {"loanRequest": {"creditAmt": 100000, "pledges": "car"}}
        errors = validator.validate(data, {"loanRequest/pledges": field_meta})
        assert len(errors) == 0
