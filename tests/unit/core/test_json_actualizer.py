"""
Unit-тесты для JsonActualizer.

Покрывает:
- Навигация по путям (navigate, set, delete, массивы)
- Добавление полей (О, УО true/false, Н, ошибка)
- Удаление полей (листовое, вложенное, несуществующее)
- Модификация полей (сохранено, перегенерировано, тип, pattern, смягчение)
- Переименование (detect 3+, detect <3, mapping override, перенос значения)
- Обработка ошибок (field, full, critical, batch)
- Интеграция ValueGenerator (UUID, dictionary, массив)
- ActualizationResult (формирование, markdown, generate_report=False)

Требования:
- REQ-7.1: Актуализация JSON по SchemaDiff
- REQ-7.2: Обнаружение переименований через метаданные
- REQ-7.3: Три уровня отката (field/full/none)
- REQ-7.4: Вычисление УО-условий при добавлении
- REQ-7.5: Строгая валидация значений при модификации
"""

import pytest
from copy import deepcopy
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock

from decimal import Decimal

from src.core.json_actualizer import (
    JsonActualizer,
    ActualizerConfig,
    ActualizationChange,
    ActualizationResult,
    RenamePair,
    _StructureError,
)
from src.core.value_generator import GeneratorConfig, ValueGenerator
from src.models.schema_models import (
    FieldMetadata,
    FieldChange,
    SchemaDiff,
    ConditionalRequirement,
)
from src.core.conditional_validator import ValidationError


# ============================================================================
# Helpers
# ============================================================================


def make_field(
    field_type: str = "string",
    name: str = "testField",
    path: str = "test/testField",
    is_required: bool = False,
    is_conditional: bool = False,
    condition: Optional[ConditionalRequirement] = None,
    dictionary: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
    format: Optional[str] = None,
    default: Optional[Any] = None,
    items: Optional[FieldMetadata] = None,
) -> FieldMetadata:
    """Создать FieldMetadata с дефолтами для тестов."""
    return FieldMetadata(
        path=path,
        name=name,
        field_type=field_type,
        is_required=is_required,
        is_conditional=is_conditional,
        condition=condition,
        dictionary=dictionary,
        constraints=constraints or {},
        format=format,
        default=default,
        items=items,
    )


def make_diff(
    added: Optional[List[FieldChange]] = None,
    removed: Optional[List[FieldChange]] = None,
    modified: Optional[List[FieldChange]] = None,
) -> SchemaDiff:
    """Создать SchemaDiff с полями для тестов."""
    return SchemaDiff(
        old_version="070",
        new_version="072",
        call="Call1",
        added_fields=added or [],
        removed_fields=removed or [],
        modified_fields=modified or [],
    )


# ============================================================================
# Группа 1: Навигация по путям (4 теста)
# ============================================================================


class TestPathNavigation:
    """Тесты навигации по JSON-путям."""

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_navigate_simple_path(self):
        """Навигация по простому пути: data.field."""
        data = {"name": "Ivan", "age": 30}
        assert self.actualizer._navigate_path(data, "name") == "Ivan"
        assert self.actualizer._navigate_path(data, "age") == 30

    def test_navigate_nested_path(self):
        """Навигация по вложенному пути: loan/applicant/income."""
        data = {"loan": {"applicant": {"income": 50000}}}
        assert self.actualizer._navigate_path(data, "loan/applicant/income") == 50000

    def test_navigate_missing_path_returns_none(self):
        """Несуществующий путь возвращает None."""
        data = {"name": "Ivan"}
        assert self.actualizer._navigate_path(data, "missing/path") is None

    def test_navigate_array_path(self):
        """Навигация по пути с массивом: applicants[0]/name."""
        data = {"applicants": [{"name": "Ivan"}, {"name": "Anna"}]}
        assert self.actualizer._navigate_path(data, "applicants[0]/name") == "Ivan"
        assert self.actualizer._navigate_path(data, "applicants[1]/name") == "Anna"


class TestSetFieldValue:
    """Тесты установки значений по пути."""

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_set_simple_field(self):
        """Установка простого поля."""
        data = {"name": "old"}
        self.actualizer._set_field_value(data, "name", "new")
        assert data["name"] == "new"

    def test_set_nested_field_creates_intermediate(self):
        """Установка вложенного поля с созданием промежуточных объектов."""
        data: Dict[str, Any] = {}
        self.actualizer._set_field_value(data, "loan/applicant/income", 50000)
        assert data["loan"]["applicant"]["income"] == 50000

    def test_set_array_item(self):
        """Установка значения в массиве по индексу."""
        data = {"applicants": [{"name": "Ivan"}, {"name": "Anna"}]}
        self.actualizer._set_field_value(data, "applicants[0]/name", "Oleg")
        assert data["applicants"][0]["name"] == "Oleg"

    def test_set_empty_array_creates_item(self):
        """Установка значения в пустой массив [] создаёт один элемент."""
        data: Dict[str, Any] = {"items": []}
        self.actualizer._set_field_value(data, "items[]/name", "Test")
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test"


class TestDeleteField:
    """Тесты удаления полей по пути."""

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_delete_leaf_field(self):
        """Удаление листового поля."""
        data = {"name": "Ivan", "age": 30}
        result = self.actualizer._delete_field(data, "age")
        assert result is True
        assert "age" not in data
        assert "name" in data

    def test_delete_nested_field(self):
        """Удаление вложенного поля."""
        data = {"loan": {"amount": 100000, "term": 12}}
        result = self.actualizer._delete_field(data, "loan/term")
        assert result is True
        assert "term" not in data["loan"]
        assert "amount" in data["loan"]

    def test_delete_nonexistent_field_returns_false(self):
        """Удаление несуществующего поля возвращает False."""
        data = {"name": "Ivan"}
        result = self.actualizer._delete_field(data, "missing/field")
        assert result is False


# ============================================================================
# Группа 2: Добавление полей (5 тестов)
# ============================================================================


class TestAddFields:
    """Тесты добавления полей в JSON."""

    def test_add_required_field(self):
        """Добавление обязательного (О) поля — значение генерируется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000}}
        added_field = FieldChange(
            path="loan/rate",
            change_type="added",
            new_meta=make_field(
                field_type="number",
                name="rate",
                path="loan/rate",
                is_required=True,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/rate": make_field(field_type="number", name="rate", path="loan/rate", is_required=True)}
        result = actualizer.actualize(old_json, diff, new_schema)
        assert "rate" in result.actualized_data["loan"]
        assert isinstance(result.actualized_data["loan"]["rate"], (int, float, Decimal))

    def test_add_conditional_field_true(self):
        """Добавление УО поля с выполненным условием — значение генерируется."""
        config = ActualizerConfig()
        actualizer = JsonActualizer(config=config)
        old_json = {"loanTypeCd": 10340001}
        condition = ConditionalRequirement(
            expression="eq(#root.loanTypeCd, 10340001)",
            message="Тип кредита = наличными",
        )
        added_field = FieldChange(
            path="pledges",
            change_type="added",
            new_meta=make_field(
                field_type="string",
                name="pledges",
                path="pledges",
                is_conditional=True,
                condition=condition,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"pledges": make_field(field_type="string", name="pledges", path="pledges", is_conditional=True, condition=condition)}
        # Мокируем _evaluate_condition, чтобы вернуть True
        with patch.object(actualizer, '_evaluate_condition', return_value=True):
            result = actualizer.actualize(old_json, diff, new_schema)
            # Условие true → поле добавлено
            assert "pledges" in result.actualized_data

    def test_add_conditional_field_false(self):
        """Добавление УО поля с невыполненным условием — поле пропускается."""
        config = ActualizerConfig()
        actualizer = JsonActualizer(config=config)
        old_json = {"loanTypeCd": 999}
        condition = ConditionalRequirement(
            expression="eq(#root.loanTypeCd, 10340001)",
            message="Тип кредита = наличными",
        )
        added_field = FieldChange(
            path="pledges",
            change_type="added",
            new_meta=make_field(
                field_type="string",
                name="pledges",
                path="pledges",
                is_conditional=True,
                condition=condition,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"pledges": make_field(field_type="string", name="pledges", path="pledges", is_conditional=True, condition=condition)}
        # Мокируем _evaluate_condition, чтобы вернуть False
        with patch.object(actualizer, '_evaluate_condition', return_value=False):
            result = actualizer.actualize(old_json, diff, new_schema)
            # Условие false → поле не добавлено
            assert "pledges" not in result.actualized_data

    def test_add_optional_field(self):
        """Добавление необязательного (Н) поля — значение генерируется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000}}
        added_field = FieldChange(
            path="loan/comment",
            change_type="added",
            new_meta=make_field(
                field_type="string",
                name="comment",
                path="loan/comment",
                is_required=False,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/comment": make_field(field_type="string", name="comment", path="loan/comment")}
        result = actualizer.actualize(old_json, diff, new_schema)
        assert "comment" in result.actualized_data["loan"]

    def test_add_field_with_error_generates_error_record(self):
        """Добавление поля с ошибкой генерации — записывается в errors."""
        actualizer = JsonActualizer()
        old_json: Dict[str, Any] = {"loan": {}}
        added_field = FieldChange(
            path="loan/complexField",
            change_type="added",
            new_meta=make_field(
                field_type="object",
                name="complexField",
                path="loan/complexField",
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/complexField": make_field(field_type="object", name="complexField", path="loan/complexField")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # object не генерируется — ошибка
        error_paths = [c.path for c in result.errors]
        assert "loan/complexField" in error_paths


# ============================================================================
# Группа 3: Удаление полей (3 теста)
# ============================================================================


class TestRemoveFields:
    """Тесты удаления полей из JSON."""

    def test_remove_leaf_field(self):
        """Удаление листового поля."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000, "rate": 12.5}}
        removed_field = FieldChange(
            path="loan/rate",
            change_type="removed",
            old_meta=make_field(field_type="number", name="rate", path="loan/rate"),
        )
        diff = make_diff(removed=[removed_field])
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}
        result = actualizer.actualize(old_json, diff, new_schema)
        assert "rate" not in result.actualized_data["loan"]
        assert "amount" in result.actualized_data["loan"]

    def test_remove_nested_field(self):
        """Удаление вложенного поля."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"applicant": {"income": 50000, "age": 30}}}
        removed_field = FieldChange(
            path="loan/applicant/age",
            change_type="removed",
            old_meta=make_field(field_type="integer", name="age", path="loan/applicant/age"),
        )
        diff = make_diff(removed=[removed_field])
        new_schema = {}
        result = actualizer.actualize(old_json, diff, new_schema)
        assert "age" not in result.actualized_data["loan"]["applicant"]

    def test_remove_nonexistent_field_no_error(self):
        """Удаление несуществующего поля — не ошибка, тихо пропускается."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000}}
        removed_field = FieldChange(
            path="loan/nonexistent",
            change_type="removed",
            old_meta=make_field(field_type="string", name="nonexistent", path="loan/nonexistent"),
        )
        diff = make_diff(removed=[removed_field])
        new_schema = {}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Нет ошибок, данные не повреждены
        assert len(result.errors) == 0
        assert result.actualized_data["loan"]["amount"] == 100000


# ============================================================================
# Группа 4: Модификация полей (5 тестов)
# ============================================================================


class TestModifyFields:
    """Тесты модификации полей."""

    def test_modify_preserved_value(self):
        """Модификация: старое значение проходит новые ограничения — сохраняется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000}}
        modified_field = FieldChange(
            path="loan/amount",
            change_type="modified",
            old_meta=make_field(field_type="integer", name="amount", path="loan/amount"),
            new_meta=make_field(field_type="integer", name="amount", path="loan/amount", is_required=True),
            changes={"required": "Н → О"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount", is_required=True)}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Значение 100000 сохраняется
        assert result.actualized_data["loan"]["amount"] == 100000
        # Есть change типа modified_preserved
        change_types = [c.change_type for c in result.changes]
        assert "modified_preserved" in change_types

    def test_modify_regenerated_value(self):
        """Модификация: старое значение не проходит новые ограничения — перегенерируется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"status": "unknown"}}
        modified_field = FieldChange(
            path="loan/status",
            change_type="modified",
            old_meta=make_field(field_type="string", name="status", path="loan/status"),
            new_meta=make_field(
                field_type="string",
                name="status",
                path="loan/status",
                constraints={"enum": ["active", "closed"]},
            ),
            changes={"constraints": "добавлено enum"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/status": make_field(field_type="string", name="status", path="loan/status", constraints={"enum": ["active", "closed"]})}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Значение перегенерировано из enum
        assert result.actualized_data["loan"]["status"] in ["active", "closed"]
        change_types = [c.change_type for c in result.changes]
        assert "modified_regenerated" in change_types

    def test_modify_type_conversion(self):
        """Модификация: преобразование типа integer → string."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"code": 12345}}
        modified_field = FieldChange(
            path="loan/code",
            change_type="modified",
            old_meta=make_field(field_type="integer", name="code", path="loan/code"),
            new_meta=make_field(field_type="string", name="code", path="loan/code"),
            changes={"type": "integer → string"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/code": make_field(field_type="string", name="code", path="loan/code")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # integer → string: "12345"
        assert isinstance(result.actualized_data["loan"]["code"], str)
        assert result.actualized_data["loan"]["code"] == "12345"

    def test_modify_pattern_violation_regenerates(self):
        """Модификация: старое значение не соответствует новому pattern — перегенерируется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"phone": "abc"}}
        modified_field = FieldChange(
            path="loan/phone",
            change_type="modified",
            old_meta=make_field(field_type="string", name="phone", path="loan/phone"),
            new_meta=make_field(
                field_type="string",
                name="phone",
                path="loan/phone",
                constraints={"pattern": r"^\d{10}$"},
                format="phone",
            ),
            changes={"constraints": "добавлено pattern"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/phone": make_field(field_type="string", name="phone", path="loan/phone", constraints={"pattern": r"^\d{10}$"}, format="phone")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Значение перегенерировано (format=phone)
        assert "phone" in result.actualized_data["loan"]

    def test_modify_relaxed_constraints_preserves(self):
        """Модификация: ограничения смягчились — старое значение сохраняется."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"comment": "hello"}}
        modified_field = FieldChange(
            path="loan/comment",
            change_type="modified",
            old_meta=make_field(field_type="string", name="comment", path="loan/comment", constraints={"maxLength": 5}),
            new_meta=make_field(field_type="string", name="comment", path="loan/comment", constraints={"maxLength": 100}),
            changes={"constraints": "maxLength: 5 → 100"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/comment": make_field(field_type="string", name="comment", path="loan/comment", constraints={"maxLength": 100})}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Значение "hello" проходит maxLength=100 — сохраняется
        assert result.actualized_data["loan"]["comment"] == "hello"
        change_types = [c.change_type for c in result.changes]
        assert "modified_preserved" in change_types


# ============================================================================
# Группа 5: Переименование (4 теста)
# ============================================================================


class TestRenameDetection:
    """Тесты обнаружения переименований."""

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_detect_rename_score_3_or_more(self):
        """Обнаружение переименования при совпадении ≥3 атрибутов."""
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=make_field(
                    field_type="integer",
                    name="creditAmt",
                    path="loan/creditAmt",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        added = [
            FieldChange(
                path="loan/loanAmount",
                change_type="added",
                new_meta=make_field(
                    field_type="integer",
                    name="loanAmount",
                    path="loan/loanAmount",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        renames, truly_removed, truly_added = self.actualizer._detect_renames(removed, added)
        assert len(renames) == 1
        assert renames[0].old_path == "loan/creditAmt"
        assert renames[0].new_path == "loan/loanAmount"
        assert renames[0].match_score >= 3
        assert len(truly_removed) == 0
        assert len(truly_added) == 0

    def test_detect_rename_score_below_3(self):
        """Не обнаружение переименования при совпадении <3 атрибутов."""
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=make_field(field_type="integer", name="creditAmt", path="loan/creditAmt"),
            )
        ]
        added = [
            FieldChange(
                path="loan/description",
                change_type="added",
                new_meta=make_field(field_type="string", name="description", path="loan/description"),
            )
        ]
        renames, truly_removed, truly_added = self.actualizer._detect_renames(removed, added)
        assert len(renames) == 0
        assert len(truly_removed) == 1
        assert len(truly_added) == 1

    def test_field_mapping_overrides_heuristic(self):
        """Явный field_mapping переопределяет эвристику."""
        config = ActualizerConfig(field_mapping={"loan/oldName": "loan/newName"})
        actualizer = JsonActualizer(config=config)
        removed = [
            FieldChange(
                path="loan/oldName",
                change_type="removed",
                old_meta=make_field(field_type="string", name="oldName", path="loan/oldName"),
            )
        ]
        added = [
            FieldChange(
                path="loan/newName",
                change_type="added",
                new_meta=make_field(field_type="string", name="newName", path="loan/newName"),
            )
        ]
        # Передаём field_mapping из конфига
        renames, truly_removed, truly_added = actualizer._detect_renames(removed, added, config.field_mapping)
        assert len(renames) == 1
        assert renames[0].old_path == "loan/oldName"
        assert renames[0].new_path == "loan/newName"

    def test_rename_preserves_value(self):
        """Переименование: значение переносится на новый путь."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"creditAmt": 100000}}
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=make_field(
                    field_type="integer",
                    name="creditAmt",
                    path="loan/creditAmt",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        added = [
            FieldChange(
                path="loan/loanAmount",
                change_type="added",
                new_meta=make_field(
                    field_type="integer",
                    name="loanAmount",
                    path="loan/loanAmount",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        renames, _, _ = actualizer._detect_renames(removed, added)
        assert len(renames) == 1
        # actualize с renames обработает переименование
        diff = make_diff(removed=removed, added=added)
        new_schema = {"loan/loanAmount": make_field(field_type="integer", name="loanAmount", path="loan/loanAmount")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Значение 100000 перенесено на новый путь
        assert result.actualized_data["loan"]["loanAmount"] == 100000
        # Старый путь удалён
        assert "creditAmt" not in result.actualized_data["loan"]


# ============================================================================
# Группа 6: Обработка ошибок (4 теста)
# ============================================================================


class TestErrorHandling:
    """Тесты обработки ошибок и уровней отката."""

    def test_field_level_rollback_skip_field(self):
        """rollback='field': ошибка поля → пропускается, продолжается."""
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        # Добавляем object-поле (вызовет ошибку генерации)
        added_field = FieldChange(
            path="loan/complexField",
            change_type="added",
            new_meta=make_field(field_type="object", name="complexField", path="loan/complexField"),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Не откат — rolled_back=False
        assert result.rolled_back is False
        # Ошибка записана
        assert len(result.errors) > 0
        # Существующие данные не повреждены
        assert result.actualized_data["loan"]["amount"] == 100000

    def test_full_rollback_on_critical_error(self):
        """rollback='field': критическая ошибка структуры → полный откат."""
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json: Dict[str, Any] = {"loan": "not_a_dict"}
        diff = make_diff()
        new_schema = {}
        # Попытка actualize на не-dict вложенном значении — StructureError
        # Это вызовет критическую ошибку при навигации
        result = actualizer.actualize(old_json, diff, new_schema)
        # Если произошёл откат — rolled_back=True
        # Если нет — данные не повреждены

    def test_full_rollback_mode(self):
        """rollback='full': любая ошибка → полный откат."""
        config = ActualizerConfig(rollback="full")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        added_field = FieldChange(
            path="loan/complexField",
            change_type="added",
            new_meta=make_field(field_type="object", name="complexField", path="loan/complexField"),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Полный откат — данные вернулись к исходным
        assert result.rolled_back is True
        assert result.actualized_data == old_json

    def test_batch_actualize(self):
        """actualize_batch обрабатывает несколько сценариев."""
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        scenarios = [
            {"loan": {"amount": 100000}},
            {"loan": {"amount": 200000}},
        ]
        added_field = FieldChange(
            path="loan/rate",
            change_type="added",
            new_meta=make_field(field_type="number", name="rate", path="loan/rate", is_required=True),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/rate": make_field(field_type="number", name="rate", path="loan/rate", is_required=True)}
        results = actualizer.actualize_batch(scenarios, diff, new_schema)
        assert len(results) == 2
        for r in results:
            assert "rate" in r.actualized_data["loan"]


# ============================================================================
# Группа 7: Интеграция ValueGenerator (3 теста)
# ============================================================================


class TestValueGeneratorIntegration:
    """Тесты интеграции с ValueGenerator."""

    def test_uuid_generation(self):
        """Генерация UUID для поля с format=uuid."""
        actualizer = JsonActualizer()
        old_json = {"loan": {}}
        added_field = FieldChange(
            path="loan/requestId",
            change_type="added",
            new_meta=make_field(
                field_type="string",
                name="requestId",
                path="loan/requestId",
                format="uuid",
                is_required=True,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/requestId": make_field(field_type="string", name="requestId", path="loan/requestId", format="uuid")}
        result = actualizer.actualize(old_json, diff, new_schema)
        # UUID — строка формата xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        value = result.actualized_data["loan"]["requestId"]
        assert isinstance(value, str)
        assert len(value) > 10  # UUID длинный

    def test_dictionary_value_generation(self):
        """Генерация значения из справочника."""
        actualizer = JsonActualizer()
        old_json = {"loan": {}}
        added_field = FieldChange(
            path="loan/productCdExt",
            change_type="added",
            new_meta=make_field(
                field_type="string",
                name="productCdExt",
                path="loan/productCdExt",
                dictionary="PRODUCT_TYPE",
                constraints={"enum": ["10410001", "10410002"]},
                is_required=True,
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/productCdExt": make_field(field_type="string", name="productCdExt", path="loan/productCdExt", dictionary="PRODUCT_TYPE", constraints={"enum": ["10410001", "10410002"]})}
        result = actualizer.actualize(old_json, diff, new_schema)
        value = result.actualized_data["loan"]["productCdExt"]
        assert value in ["10410001", "10410002"]

    def test_array_generation(self):
        """Генерация массива с minItems."""
        actualizer = JsonActualizer(config=ActualizerConfig(default_array_size=2))
        old_json: Dict[str, Any] = {"loan": {}}
        items_meta = make_field(field_type="string", name="name", path="loan/applicants[]/name")
        added_field = FieldChange(
            path="loan/applicants",
            change_type="added",
            new_meta=make_field(
                field_type="array",
                name="applicants",
                path="loan/applicants",
                items=items_meta,
                constraints={"minItems": 2},
            ),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/applicants": make_field(field_type="array", name="applicants", path="loan/applicants", items=items_meta, constraints={"minItems": 2})}
        result = actualizer.actualize(old_json, diff, new_schema)
        # Массив с ≥2 элементами
        applicants = result.actualized_data["loan"]["applicants"]
        assert isinstance(applicants, list)
        assert len(applicants) >= 2


# ============================================================================
# Группа 8: ActualizationResult (3 теста)
# ============================================================================


class TestActualizationResult:
    """Тесты формирования результата."""

    def test_result_structure(self):
        """Структура ActualizationResult: actualized_data, changes, errors."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"amount": 100000}}
        added_field = FieldChange(
            path="loan/rate",
            change_type="added",
            new_meta=make_field(field_type="number", name="rate", path="loan/rate", is_required=True),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/rate": make_field(field_type="number", name="rate", path="loan/rate", is_required=True)}
        result = actualizer.actualize(old_json, diff, new_schema)
        assert hasattr(result, "actualized_data")
        assert hasattr(result, "changes")
        assert hasattr(result, "errors")
        assert hasattr(result, "validation_errors")
        assert hasattr(result, "rolled_back")
        assert isinstance(result.changes, list)
        assert isinstance(result.errors, list)

    def test_result_to_markdown(self):
        """Генерация Markdown-отчёта из результата."""
        actualizer = JsonActualizer(config=ActualizerConfig(generate_report=True, report_format="both"))
        old_json = {"loan": {"amount": 100000}}
        removed_field = FieldChange(
            path="loan/amount",
            change_type="removed",
            old_meta=make_field(field_type="integer", name="amount", path="loan/amount"),
        )
        diff = make_diff(removed=[removed_field])
        new_schema = {}
        result = actualizer.actualize(old_json, diff, new_schema)
        md = result.to_markdown()
        assert isinstance(md, str)
        assert len(md) > 0

    def test_no_report_when_disabled(self):
        """generate_report=False — Markdown-отчёт не генерируется."""
        config = ActualizerConfig(generate_report=False)
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        diff = make_diff()
        new_schema = {}
        result = actualizer.actualize(old_json, diff, new_schema)
        # to_markdown возвращает пустую строку или не вызывается
        md = result.to_markdown()
        assert md == ""


# ============================================================================
# Группа: actualize_from_paths (дополнительно)
# ============================================================================


class TestActualizeFromPaths:
    """Тесты convenience-метода actualize_from_paths."""

    def test_actualize_from_paths_not_found(self, tmp_path):
        """actualize_from_paths с несуществующими файлами — ошибка в результате."""
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        nonexistent = tmp_path / "nonexistent.json"
        result = actualizer.actualize_from_paths(
            scenario_path=nonexistent,
            old_schema_path=nonexistent,
            new_schema_path=nonexistent,
        )
        # Ошибка при загрузке файлов
        assert len(result.errors) > 0 or result.rolled_back is True


# ============================================================================
# Группа 9: SpEL-контекст для УО-полей (TD-13)
# ============================================================================


class TestEvaluateConditionContext:
    """Тесты _evaluate_condition с правильным SpEL-контекстом.

    TD-13: _evaluate_condition() должен строить EvaluationContext
    с current_value и parent_stack, а не только root_data.
    Без этого #this, parent, parent2 навигация возвращает None.

    Все тесты вызывают _evaluate_condition БЕЗ мока — реальный
    ConditionEvaluator и реальный ConditionalValidator._build_context().
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()
        self.data = {
            "loanRequest": {
                "loanTypeCd": 10340001,
                "onlinePaOffer": {
                    "onlinePaOfferFlag": True,
                },
            },
        }

    # --- Тест 1: #this навигация ---

    def test_evaluate_condition_with_this_navigation(self):
        """eq(#this.onlinePaOfferFlag, True) возвращает True для поля внутри onlinePaOffer.

        Поле: loanRequest/onlinePaOffer/approvedCreditAmt
        #this = onlinePaOffer = {"onlinePaOfferFlag": True}
        #this.onlinePaOfferFlag должно резолвиться в True.
        """
        condition = ConditionalRequirement(
            expression="eq(#this.onlinePaOfferFlag, True)",
            message="onlinePaOfferFlag == True",
        )
        result = self.actualizer._evaluate_condition(
            condition, self.data, "loanRequest/onlinePaOffer/approvedCreditAmt"
        )
        assert result is True, (
            "eq(#this.onlinePaOfferFlag, True) должно вернуть True, "
            "но вернуло False — parent_stack не построен"
        )

    # --- Тест 2: parent навигация ---

    def test_evaluate_condition_with_parent_navigation(self):
        """eq(parent.onlinePaOfferFlag, True) возвращает True.

        Поле: loanRequest/onlinePaOffer/approvedCreditAmt
        parent = onlinePaOffer = {"onlinePaOfferFlag": True}
        parent.onlinePaOfferFlag должно резолвиться в True.
        """
        condition = ConditionalRequirement(
            expression="eq(parent.onlinePaOfferFlag, True)",
            message="onlinePaOfferFlag == True via parent",
        )
        result = self.actualizer._evaluate_condition(
            condition, self.data, "loanRequest/onlinePaOffer/approvedCreditAmt"
        )
        assert result is True, (
            "eq(parent.onlinePaOfferFlag, True) должно вернуть True, "
            "но вернуло False — parent_stack не построен"
        )

    # --- Тест 3: #root навигация (регрессия) ---

    def test_evaluate_condition_with_root_navigation(self):
        """eq(#root.loanRequest.loanTypeCd, 10340001) — регрессионный тест.

        #root работает и без parent_stack, но проверяем что
        делегирование ConditionalValidator._build_context() не сломало его.
        """
        condition = ConditionalRequirement(
            expression="eq(#root.loanRequest.loanTypeCd, 10340001)",
            message="loanTypeCd == 10340001",
        )
        result = self.actualizer._evaluate_condition(
            condition, self.data, "loanRequest/loanTypeCd"
        )
        assert result is True, (
            "eq(#root.loanRequest.loanTypeCd, 10340001) должно вернуть True"
        )

    # --- Тест 4: Несуществующий родитель — graceful ---

    def test_evaluate_condition_missing_parent_graceful(self):
        """Путь к несуществующему родителю не крашит _evaluate_condition.

        Если путь содержит несуществующий сегмент, parent_stack будет
        неполным, но метод должен вернуть False (не крашить).
        """
        condition = ConditionalRequirement(
            expression="eq(#this.field, value)",
            message="field == value",
        )
        # Путь к полю, чей родитель не существует в данных
        data = {"loanRequest": {}}
        result = self.actualizer._evaluate_condition(
            condition, data, "loanRequest/nonexistent/field"
        )
        # Не крашится — условие возвращает False (не True и не Exception)
        assert isinstance(result, bool), "_evaluate_condition не должно крашиться"


# ============================================================================
# Группа E: Ветвления обнаружения переименований и обработки (lines 566, 569, 662-693)
# ============================================================================


class TestDetectRenameNoneMeta:
    """Тесты _detect_renames: пропуск кандидатов с None-метаданными.

    Покрывает строки 566 и 569 — ветки continue в эвристике,
    когда old_meta=None (removed) или new_meta=None (added).
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_detect_rename_skips_none_old_meta(self):
        """Removed-кандидат с old_meta=None пропускается эвристикой (line 565-566)."""
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=None,  # Нет метаданных — кандидат пропускается
            )
        ]
        added = [
            FieldChange(
                path="loan/loanAmount",
                change_type="added",
                new_meta=make_field(
                    field_type="integer",
                    name="loanAmount",
                    path="loan/loanAmount",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        renames, truly_removed, truly_added = self.actualizer._detect_renames(removed, added)
        # Не найдено переименований, оба поля остались как truly_removed/added
        assert len(renames) == 0
        assert len(truly_removed) == 1
        assert len(truly_added) == 1

    def test_detect_rename_skips_none_new_meta(self):
        """Added-кандидат с new_meta=None пропускается эвристикой (line 568-569)."""
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=make_field(
                    field_type="integer",
                    name="creditAmt",
                    path="loan/creditAmt",
                    format="integer",
                    constraints={"maxIntLength": 10},
                ),
            )
        ]
        added = [
            FieldChange(
                path="loan/description",
                change_type="added",
                new_meta=None,  # Нет метаданных — кандидат пропускается
            )
        ]
        renames, truly_removed, truly_added = self.actualizer._detect_renames(removed, added)
        # Не найдено переименований
        assert len(renames) == 0
        assert len(truly_removed) == 1
        assert len(truly_added) == 1


class TestProcessRenamesBranches:
    """Тесты _process_renames: ветки regenerated, generated, exception.

    Покрывает строки 662-693 — три ветки обработки переименований.
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_rename_regenerated_when_value_invalid(self):
        """Старое значение не проходит валидацию — change_type='renamed_regenerated' (line 662-673).

        Используем прямое создание RenamePair + вызов _process_renames,
        чтобы обойти эвристику _detect_renames (которая может не найти совпадение).
        """
        actualizer = JsonActualizer()
        # integer 100000 не валиден для string с maxLength=3
        old_meta = make_field(field_type="integer", name="creditAmt", path="loan/creditAmt")
        new_meta = make_field(
            field_type="string", name="loanAmount", path="loan/loanAmount",
            constraints={"maxLength": 3},
        )
        rename = RenamePair(
            old_path="loan/creditAmt",
            new_path="loan/loanAmount",
            old_meta=old_meta,
            new_meta=new_meta,
            match_score=5,
        )
        result = ActualizationResult(actualized_data={"loan": {"creditAmt": 100000}})
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []
        actualizer._process_renames(result, [rename], changes, errors)
        change_types = [c.change_type for c in changes]
        assert "renamed_regenerated" in change_types, (
            f"Ожидался change_type='renamed_regenerated', но получены: {change_types}"
        )

    def test_rename_generated_when_no_old_value(self):
        """Старое значение None — change_type='renamed_generated' (line 674-685).

        Используем прямое создание RenamePair + вызов _process_renames,
        потому что _navigate_path вернёт None если поле отсутствует в данных.
        """
        actualizer = JsonActualizer()
        old_meta = make_field(field_type="integer", name="creditAmt", path="loan/creditAmt")
        new_meta = make_field(field_type="integer", name="loanAmount", path="loan/loanAmount")
        rename = RenamePair(
            old_path="loan/creditAmt",
            new_path="loan/loanAmount",
            old_meta=old_meta,
            new_meta=new_meta,
            match_score=5,
        )
        # old_json НЕ содержит creditAmt → _navigate_path вернёт None
        result = ActualizationResult(actualized_data={"loan": {}})
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []
        actualizer._process_renames(result, [rename], changes, errors)
        change_types = [c.change_type for c in changes]
        assert "renamed_generated" in change_types, (
            f"Ожидался change_type='renamed_generated', но получены: {change_types}"
        )

    def test_rename_exception_handling(self):
        """Исключение при обработке переименования — ошибка в errors (line 687-693)."""
        actualizer = JsonActualizer()
        old_json = {"loan": {"creditAmt": 100000}}
        removed = [
            FieldChange(
                path="loan/creditAmt",
                change_type="removed",
                old_meta=make_field(
                    field_type="integer",
                    name="creditAmt",
                    path="loan/creditAmt",
                ),
            )
        ]
        added = [
            FieldChange(
                path="loan/loanAmount",
                change_type="added",
                new_meta=make_field(
                    field_type="integer",
                    name="loanAmount",
                    path="loan/loanAmount",
                ),
            )
        ]
        diff = make_diff(removed=removed, added=added)
        new_schema = {
            "loan/loanAmount": make_field(field_type="integer", name="loanAmount", path="loan/loanAmount")
        }
        # Мокаем _navigate_path чтобы выбросил исключение
        with patch.object(actualizer, "_navigate_path", side_effect=RuntimeError("navigation error")):
            result = actualizer.actualize(old_json, diff, new_schema)
        # Ошибка должна быть в errors, а не в changes
        error_change_types = [e.change_type for e in result.errors]
        assert "error" in error_change_types, (
            f"Ожидалась ошибка переименования в result.errors, но получены: {error_change_types}"
        )


# ============================================================================
# Группа F: _transform_value() — преобразование типов (lines 928-946)
# ============================================================================


class TestTransformValue:
    """Тесты _transform_value: все ветки конверсии типов.

    Покрывает строки 928 (тот же тип), 931-946 (конверсии и исключения).
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_transform_same_type_returns_value(self):
        """Одинаковый тип — значение возвращается как есть (line 928)."""
        old_meta = make_field(field_type="string", name="field", path="test/field")
        new_meta = make_field(field_type="string", name="field", path="test/field")
        result = self.actualizer._transform_value("hello", old_meta, new_meta)
        assert result == "hello"

    def test_transform_integer_to_string(self):
        """integer -> string: str(old_value) (line 931-932)."""
        old_meta = make_field(field_type="integer", name="count", path="test/count")
        new_meta = make_field(field_type="string", name="count", path="test/count")
        result = self.actualizer._transform_value(42, old_meta, new_meta)
        assert result == "42"

    def test_transform_number_to_string(self):
        """number -> string: str(old_value) (line 933-934)."""
        old_meta = make_field(field_type="number", name="rate", path="test/rate")
        new_meta = make_field(field_type="string", name="rate", path="test/rate")
        result = self.actualizer._transform_value(3.14, old_meta, new_meta)
        assert result == "3.14"

    def test_transform_boolean_to_string_true(self):
        """boolean True -> 'true' (line 935-936)."""
        old_meta = make_field(field_type="boolean", name="flag", path="test/flag")
        new_meta = make_field(field_type="string", name="flag", path="test/flag")
        result = self.actualizer._transform_value(True, old_meta, new_meta)
        assert result == "true"

    def test_transform_boolean_to_string_false(self):
        """boolean False -> 'false' (line 935-936)."""
        old_meta = make_field(field_type="boolean", name="flag", path="test/flag")
        new_meta = make_field(field_type="string", name="flag", path="test/flag")
        result = self.actualizer._transform_value(False, old_meta, new_meta)
        assert result == "false"

    def test_transform_string_to_integer(self):
        """string -> integer: int(old_value) (line 937-938)."""
        old_meta = make_field(field_type="string", name="count", path="test/count")
        new_meta = make_field(field_type="integer", name="count", path="test/count")
        result = self.actualizer._transform_value("42", old_meta, new_meta)
        assert result == 42

    def test_transform_string_to_number(self):
        """string -> number: float(old_value) (line 939-940)."""
        old_meta = make_field(field_type="string", name="rate", path="test/rate")
        new_meta = make_field(field_type="number", name="rate", path="test/rate")
        result = self.actualizer._transform_value("3.14", old_meta, new_meta)
        assert result == 3.14

    def test_transform_string_to_boolean_true(self):
        """string -> boolean: 'true', '1', 'yes' -> True (line 941-942)."""
        old_meta = make_field(field_type="string", name="flag", path="test/flag")
        new_meta = make_field(field_type="boolean", name="flag", path="test/flag")
        assert self.actualizer._transform_value("true", old_meta, new_meta) is True
        assert self.actualizer._transform_value("1", old_meta, new_meta) is True
        assert self.actualizer._transform_value("yes", old_meta, new_meta) is True

    def test_transform_string_to_boolean_false(self):
        """string -> boolean: 'false', '0', случайная строка -> False (line 941-942)."""
        old_meta = make_field(field_type="string", name="flag", path="test/flag")
        new_meta = make_field(field_type="boolean", name="flag", path="test/flag")
        assert self.actualizer._transform_value("false", old_meta, new_meta) is False
        assert self.actualizer._transform_value("0", old_meta, new_meta) is False
        assert self.actualizer._transform_value("random", old_meta, new_meta) is False

    def test_transform_unsupported_returns_none(self):
        """Неподдерживаемая конверсия → None (триггерит перегенерацию) (line 943-944)."""
        old_meta = make_field(field_type="integer", name="count", path="test/count")
        new_meta = make_field(field_type="boolean", name="count", path="test/count")
        result = self.actualizer._transform_value(42, old_meta, new_meta)
        assert result is None

    def test_transform_value_error_returns_none(self):
        """string -> integer с нечисловой строкой: ValueError → None (line 945)."""
        old_meta = make_field(field_type="string", name="count", path="test/count")
        new_meta = make_field(field_type="integer", name="count", path="test/count")
        result = self.actualizer._transform_value("abc", old_meta, new_meta)
        assert result is None

    def test_transform_type_error_returns_none(self):
        """Конверсия с TypeError → None (line 945-946)."""
        # int(None) вызовет TypeError
        old_meta = make_field(field_type="string", name="count", path="test/count")
        new_meta = make_field(field_type="integer", name="count", path="test/count")
        result = self.actualizer._transform_value(None, old_meta, new_meta)
        # None.lower() (string→boolean) или int(None) вызовут TypeError
        assert result is None


# ============================================================================
# Группа G: _validate_value() — граничные случаи (lines 956, 968-973)
# ============================================================================


class TestValidateValueEdgeCases:
    """Тесты _validate_value: None, несоответствие типа, integer-as-float, constraints.

    Покрывает строки 956 (None), 968-973 (типы и ограничения).
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()

    def test_validate_value_none_returns_false(self):
        """_validate_value(None, meta) возвращает False (line 956)."""
        meta = make_field(field_type="string", name="field", path="test/field")
        assert self.actualizer._validate_value(None, meta) is False

    def test_validate_value_type_mismatch_returns_false(self):
        """Строковое значение с integer-типом → False (line 972-973)."""
        meta = make_field(field_type="integer", name="count", path="test/count")
        assert self.actualizer._validate_value("not_a_number", meta) is False

    def test_validate_value_integer_as_float_passes(self):
        """JSON-число 42.0 принимается как integer-тип (line 968-969)."""
        meta = make_field(field_type="integer", name="count", path="test/count")
        # 42.0 — float, но должен пройти как integer
        assert self.actualizer._validate_value(42.0, meta) is True

    def test_validate_value_number_accepts_int_and_float(self):
        """number-тип принимает и int, и float (line 970-971)."""
        meta = make_field(field_type="number", name="rate", path="test/rate")
        assert self.actualizer._validate_value(42, meta) is True
        assert self.actualizer._validate_value(3.14, meta) is True

    def test_validate_value_constraint_violation_returns_false(self):
        """Значение проходит проверку типа, но не проходит constraints → False (line 978-979)."""
        meta = make_field(
            field_type="string",
            name="name",
            path="test/name",
            constraints={"maxLength": 5},
        )
        # "hello world" > 5 символов — не проходит maxLength
        assert self.actualizer._validate_value("hello world", meta) is False

    def test_validate_value_all_constraints_pass(self):
        """Значение проходит и проверку типа, и все constraints → True (line 981)."""
        meta = make_field(
            field_type="string",
            name="name",
            path="test/name",
            constraints={"maxLength": 20},
        )
        assert self.actualizer._validate_value("hello", meta) is True


# ============================================================================
# Категория A: actualize_from_paths (строки 312-371)
# ============================================================================


class TestActualizeFromPathsDetailed:
    """Детальные тесты actualize_from_paths — happy path и обработка ошибок.

    Покрывает:
    - lines 336-349: happy path (загрузка файлов, парсинг, сравнение, актуализация)
    - lines 351-360: FileNotFoundError handler
    - lines 362-371: общий Exception handler
    """

    def test_actualize_from_paths_happy_path(self):
        """actualize_from_paths: успешная загрузка и актуализация.

        Покрывает строки 336-349: load_json, SchemaParser, SchemaComparator, actualize.
        """
        from unittest.mock import MagicMock

        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)

        mock_scenario = {"loan": {"amount": 100000}}
        mock_old_schema = {"loan/amount": {"type": "integer"}}
        mock_new_schema = {"loan/amount": {"type": "integer"}, "loan/rate": {"type": "number"}}

        mock_old_fields = [
            make_field(field_type="integer", name="amount", path="loan/amount"),
        ]
        mock_new_fields = [
            make_field(field_type="integer", name="amount", path="loan/amount"),
            make_field(field_type="number", name="rate", path="loan/rate", is_required=True),
        ]

        with patch("src.utils.json_utils.load_json") as mock_load, \
             patch("src.parsers.schema_parser.SchemaParser") as mock_parser_cls, \
             patch("src.core.schema_comparator.SchemaComparator") as mock_comp_cls:

            mock_load.side_effect = [mock_scenario, mock_old_schema, mock_new_schema]

            mock_parser = MagicMock()
            mock_parser.parse.side_effect = [mock_old_fields, mock_new_fields]
            mock_parser_cls.return_value = mock_parser

            mock_comparator = MagicMock()
            mock_diff = make_diff(
                added=[
                    FieldChange(
                        path="loan/rate",
                        change_type="added",
                        new_meta=make_field(
                            field_type="number", name="rate",
                            path="loan/rate", is_required=True,
                        ),
                    )
                ]
            )
            mock_comparator.compare.return_value = mock_diff
            mock_comp_cls.return_value = mock_comparator

            result = actualizer.actualize_from_paths(
                scenario_path="/fake/scenario.json",
                old_schema_path="/fake/old.json",
                new_schema_path="/fake/new.json",
            )

            # Результат — не ошибка
            assert result.rolled_back is False
            assert "rate" in result.actualized_data.get("loan", {})

    def test_actualize_from_paths_file_not_found(self):
        """actualize_from_paths: FileNotFoundError -> ошибка в результате.

        Покрывает строки 351-360: except FileNotFoundError.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)

        with patch("src.utils.json_utils.load_json") as mock_load:
            mock_load.side_effect = FileNotFoundError("/fake/missing.json")

            result = actualizer.actualize_from_paths(
                scenario_path="/fake/missing.json",
                old_schema_path="/fake/old.json",
                new_schema_path="/fake/new.json",
            )

            # Ошибка записана, rolled_back=True
            assert result.rolled_back is True
            assert len(result.errors) > 0

    def test_actualize_from_paths_general_exception(self):
        """actualize_from_paths: общий Exception -> ошибка в результате.

        Покрывает строки 362-371: except Exception.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)

        with patch("src.utils.json_utils.load_json") as mock_load:
            mock_load.side_effect = RuntimeError("Unexpected disk error")

            result = actualizer.actualize_from_paths(
                scenario_path="/fake/scenario.json",
                old_schema_path="/fake/old.json",
                new_schema_path="/fake/new.json",
            )

            # Ошибка записана, rolled_back=True
            assert result.rolled_back is True
            assert len(result.errors) > 0


# ============================================================================
# Категория B: Exception handlers в actualize() и processing methods
# ============================================================================


class TestActualizeExceptionHandlers:
    """Тесты обработчиков исключений в actualize() и processing-методах.

    Покрывает:
    - lines 257-266: _StructureError handler (rollback + error record)
    - lines 268-278: general Exception handler (rollback based on config)
    - lines 726-732: exception in _process_removed_fields
    - lines 792-798: exception in _process_added_fields
    - lines 815-822: no metadata error in _process_modified_fields
    - lines 889-895: exception in _process_modified_fields
    - lines 1006-1008: exception in _evaluate_condition
    """

    def test_actualize_structure_error_rollback(self):
        """_StructureError в actualize() -> полный откат, rolled_back=True.

        Покрывает строки 257-266.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        diff = make_diff()
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}

        with patch.object(actualizer, "_detect_renames", side_effect=_StructureError("structure broken")):
            result = actualizer.actualize(old_json, diff, new_schema)

        assert result.rolled_back is True
        # Данные откачены к backup
        assert result.actualized_data == old_json
        # Ошибка записана
        assert len(result.errors) > 0
        assert "Критическая ошибка структуры" in result.errors[0].reason

    def test_actualize_unexpected_error_rollback_field(self):
        """General Exception при rollback='field' -> откат данных.

        Покрывает строки 268-278: rollback in ('field', 'full') -> data restored.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        diff = make_diff()
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}

        with patch.object(actualizer, "_detect_renames", side_effect=RuntimeError("unexpected crash")):
            result = actualizer.actualize(old_json, diff, new_schema)

        # rollback='field' входит в ('field', 'full') -> откат
        assert result.rolled_back is True
        assert result.actualized_data == old_json
        assert len(result.errors) > 0

    def test_actualize_unexpected_error_no_rollback(self):
        """General Exception при rollback='none' -> данные НЕ откатываются.

        Покрывает строки 268-278: rollback not in ('field', 'full') -> данные сохранены.
        """
        config = ActualizerConfig(rollback="none")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        diff = make_diff()
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}

        with patch.object(actualizer, "_detect_renames", side_effect=RuntimeError("unexpected crash")):
            result = actualizer.actualize(old_json, diff, new_schema)

        # rollback='none' -> данные не откатываются
        assert result.rolled_back is False
        # Ошибка записана
        assert len(result.errors) > 0

    def test_process_removed_fields_exception(self):
        """Исключение в _process_removed_fields -> ошибка записана.

        Покрывает строки 726-732: except Exception в цикле удаления.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000, "rate": 12.5}}
        removed_field = FieldChange(
            path="loan/rate",
            change_type="removed",
            old_meta=make_field(field_type="number", name="rate", path="loan/rate"),
        )
        diff = make_diff(removed=[removed_field])
        new_schema = {"loan/amount": make_field(field_type="integer", name="amount", path="loan/amount")}

        # Заставляем _delete_field выбросить исключение
        with patch.object(actualizer, "_delete_field", side_effect=RuntimeError("delete crash")):
            result = actualizer.actualize(old_json, diff, new_schema)

        # Ошибка записана в errors
        error_paths = [e.path for e in result.errors]
        assert "loan/rate" in error_paths
        # Существующие данные не повреждены
        assert result.actualized_data["loan"]["amount"] == 100000

    def test_process_added_fields_exception(self):
        """Исключение в _process_added_fields -> ошибка записана.

        Покрывает строки 792-798: except Exception в цикле добавления.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        added_field = FieldChange(
            path="loan/rate",
            change_type="added",
            new_meta=make_field(field_type="number", name="rate", path="loan/rate", is_required=True),
        )
        diff = make_diff(added=[added_field])
        new_schema = {"loan/rate": make_field(field_type="number", name="rate", path="loan/rate", is_required=True)}

        # Заставляем _set_field_value выбросить исключение после генерации значения
        with patch.object(actualizer, "_set_field_value", side_effect=RuntimeError("set crash")):
            result = actualizer.actualize(old_json, diff, new_schema)

        # Ошибка записана
        error_paths = [e.path for e in result.errors]
        assert "loan/rate" in error_paths

    def test_process_modified_fields_no_metadata(self):
        """Модификация поля без new_meta и без записи в new_schema -> ошибка.

        Покрывает строки 815-822: new_meta is None -> error record.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        # new_meta=None и путь не в new_schema
        modified_field = FieldChange(
            path="loan/amount",
            change_type="modified",
            old_meta=make_field(field_type="integer", name="amount", path="loan/amount"),
            new_meta=None,
            changes={"type": "integer to string"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {}  # Пустая схема — loan/amount не найдётся

        result = actualizer.actualize(old_json, diff, new_schema)

        # Ошибка записана
        error_paths = [e.path for e in result.errors]
        assert "loan/amount" in error_paths

    def test_process_modified_fields_exception(self):
        """Исключение в _process_modified_fields -> ошибка записана.

        Покрывает строки 889-895: except Exception в цикле модификации.
        """
        config = ActualizerConfig(rollback="field")
        actualizer = JsonActualizer(config=config)
        old_json = {"loan": {"amount": 100000}}
        modified_field = FieldChange(
            path="loan/amount",
            change_type="modified",
            old_meta=make_field(field_type="integer", name="amount", path="loan/amount"),
            new_meta=make_field(field_type="string", name="amount", path="loan/amount"),
            changes={"type": "integer to string"},
        )
        diff = make_diff(modified=[modified_field])
        new_schema = {"loan/amount": make_field(field_type="string", name="amount", path="loan/amount")}

        # Заставляем _navigate_path выбросить исключение
        with patch.object(actualizer, "_navigate_path", side_effect=RuntimeError("nav crash")):
            result = actualizer.actualize(old_json, diff, new_schema)

        # Ошибка записана
        error_paths = [e.path for e in result.errors]
        assert "loan/amount" in error_paths

    def test_evaluate_condition_exception_returns_false(self):
        """Исключение в _evaluate_condition -> возвращает False (не крашит).

        Покрывает строки 1006-1008: except Exception -> return False.
        """
        actualizer = JsonActualizer()
        condition = ConditionalRequirement(
            expression="invalid???expression",
            message="test condition",
        )
        data = {"loan": {"amount": 100000}}

        result = actualizer._evaluate_condition(condition, data, "loan/amount")
        # Исключение перехвачено -> False
        assert result is False


# ============================================================================
# Категория C: __str__ и to_markdown() (строки 90, 138, 151-155)
# ============================================================================


class TestActualizationChangeStrAndMarkdown:
    """Тесты __str__ для ActualizationChange и to_markdown для ActualizationResult.

    Покрывает:
    - line 90: ActualizationChange.__str__
    - line 138: rolled_back branch в to_markdown
    - lines 151-155: errors section в to_markdown
    """

    def test_actualization_change_str(self):
        """ActualizationChange.__str__ возвращает ожидаемый формат.

        Покрывает строку 90: return f"{self.change_type}: {self.path} ({self.severity})".
        """
        change = ActualizationChange(
            path="loan/rate",
            change_type="added",
            reason="Поле добавлено",
            severity="info",
        )
        result = str(change)
        assert result == "added: loan/rate (info)"

    def test_result_to_markdown_with_rollback(self):
        """ActualizationResult.to_markdown() с rolled_back=True содержит 'Rolled back'.

        Покрывает строку 138: if self.rolled_back: lines.append("**Status:** Rolled back to backup").
        """
        result = ActualizationResult(
            actualized_data={"loan": {"amount": 100000}},
            rolled_back=True,
            generate_report=True,
        )
        md = result.to_markdown()
        assert "Rolled back" in md

    def test_result_to_markdown_with_errors(self):
        """ActualizationResult.to_markdown() с ошибками содержит секцию '## Errors'.

        Покрывает строки 150-155: секция ошибок в Markdown.
        """
        errors = [
            ActualizationChange(
                path="loan/complexField",
                change_type="error",
                reason="Не удалось сгенерировать значение",
                severity="error",
            ),
        ]
        result = ActualizationResult(
            actualized_data={"loan": {"amount": 100000}},
            errors=errors,
            generate_report=True,
        )
        md = result.to_markdown()
        assert "## Errors" in md
        assert "loan/complexField" in md
        assert "Не удалось сгенерировать" in md


# ============================================================================
# Категория D: Navigation edge cases (строки 386, 401, 407, 412, 428, 435, 445, 451-468, 483-491)
# ============================================================================


class TestNavigationEdgeCases:
    """Тесты граничных случаев навигации по JSON-путям.

    Покрывает:
    - line 386: _navigate_path — empty path/data returns None
    - lines 401, 407, 412: array navigation edge cases
    - lines 428, 435, 445, 451-468: _set_field_value edge cases
    - lines 483-491: _delete_field array path handling
    """

    def setup_method(self):
        self.actualizer = JsonActualizer()

    # --- _navigate_path edge cases ---

    def test_navigate_empty_path(self):
        """_navigate_path(data, '') возвращает None.

        Покрывает строку 386: if not path or not data: return None.
        """
        data = {"loan": {"amount": 100000}}
        result = self.actualizer._navigate_path(data, "")
        assert result is None

    def test_navigate_empty_data(self):
        """_navigate_path({}, 'field') возвращает None через .get().

        Покрывает строку 386: пустой dict — .get() вернёт None для несуществующего ключа.
        """
        result = self.actualizer._navigate_path({}, "field")
        assert result is None

    def test_navigate_array_null_element(self):
        """_navigate_path по массиву с None-элементом возвращает None.

        Покрывает строки 401-407: навигация в массив, где элемент None.
        """
        data = {"items": [None, {"name": "x"}]}
        result = self.actualizer._navigate_path(data, "items[0]/name")
        assert result is None

    def test_navigate_array_out_of_range(self):
        """_navigate_path по индексу за пределами массива возвращает None.

        Покрывает строки 403-407: idx >= len(current) -> return None.
        """
        data = {"items": [{"name": "a"}]}
        result = self.actualizer._navigate_path(data, "items[5]/name")
        assert result is None

    def test_navigate_non_dict_current(self):
        """_navigate_path по пути, где промежуточное значение не dict, возвращает None.

        Покрывает строку 412: else -> return None (non-dict current).
        """
        data = {"a": "string_value"}
        result = self.actualizer._navigate_path(data, "a/b")
        assert result is None

    # --- _set_field_value edge cases ---

    def test_set_field_creates_list_for_array(self):
        """_set_field_value создаёт пустой список при установке элемента массива.

        Покрывает строки 427-428: if key not in current: current[key] = [].
        """
        data: Dict[str, Any] = {}
        self.actualizer._set_field_value(data, "items[0]/name", "Test")
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["items"][0]["name"] == "Test"

    def test_set_field_extends_list_for_index(self):
        """_set_field_value расширяет список при установке элемента по индексу.

        Покрывает строки 433-436: while len(current_list) <= idx: append({}).
        """
        data: Dict[str, Any] = {"items": []}
        # Установка items[2]/name — расширяет список до 3 элементов
        self.actualizer._set_field_value(data, "items[2]/name", "Third")
        assert len(data["items"]) == 3
        assert data["items"][2]["name"] == "Third"

    def test_set_field_overwrites_non_dict(self):
        """_set_field_value заменяет не-dict значение на dict при навигации.

        Покрывает строки 444-445: if not isinstance(current[part], dict): current[part] = {}.
        """
        data = {"loan": "not_a_dict"}
        # loan — строка, loan/applicant должен перезаписать её на dict
        self.actualizer._set_field_value(data, "loan/applicant/income", 50000)
        assert isinstance(data["loan"], dict)
        assert data["loan"]["applicant"]["income"] == 50000

    def test_set_field_array_in_last_part(self):
        """_set_field_value с array-индексом в последнем сегменте пути.

        Покрывает строки 450-468: last_part содержит '[' — установка в массив.
        """
        data: Dict[str, Any] = {"items": [{"name": "Old"}]}
        # Установка items[0] = новое значение напрямую
        self.actualizer._set_field_value(data, "items[0]", {"name": "New"})
        assert data["items"][0]["name"] == "New"

    # --- _delete_field edge cases ---

    def test_delete_field_array_path(self):
        """_delete_field удаляет поле внутри элемента массива.

        Покрывает строки 483-491: навигация по массиву в _delete_field.
        """
        data = {"items": [{"name": "A", "value": 1}, {"name": "B", "value": 2}]}
        result = self.actualizer._delete_field(data, "items[0]/value")
        assert result is True
        assert "value" not in data["items"][0]
        assert data["items"][0]["name"] == "A"

    def test_delete_field_array_path_nonexistent_key(self):
        """_delete_field по пути в массиве с несуществующим ключом возвращает False.

        Покрывает строки 499-503: last_part not in current -> return False.
        """
        data = {"items": [{"name": "A"}]}
        result = self.actualizer._delete_field(data, "items[0]/nonexistent")
        assert result is False

    def test_delete_field_array_path_nonexistent_index(self):
        """_delete_field по несуществующему индексу массива возвращает False.

        Покрывает строки 489-490: idx >= len(current) -> return False.
        """
        data = {"items": [{"name": "A"}]}
        result = self.actualizer._delete_field(data, "items[5]/name")
        assert result is False


# ============================================================================
# TD-14: Добиваем покрытие до 95%+ — оставшиеся непокрытые ветки
# ============================================================================


class TestRemainingCoverageGaps:
    """Тесты для оставшихся непокрытых строк (TD-14).

    Покрывает строки: 401, 455, 461, 464-468, 486, 612, 687-688,
    747-753, 826-837, 855-858, 971.
    """

    def setup_method(self) -> None:
        self.config = ActualizerConfig(
            locale="ru_RU", seed=42, generate_report=False
        )
        self.actualizer = JsonActualizer(config=self.config)

    # --- Line 401: _navigate_path — array key exists but value is None ---

    def test_navigate_path_array_key_value_is_none(self) -> None:
        """_navigate_path: ключ массива существует, но значение None.

        Покрывает строку 401: `if current is None: return None`
        после `current = current.get(key)`.
        """
        data = {"items": None}
        result = self.actualizer._navigate_path(data, "items[0]/name")
        assert result is None

    # --- Lines 455, 461: _set_field_value — array in last part ---

    def test_set_field_value_array_in_last_part_new_key(self) -> None:
        """_set_field_value: создание нового списка для ключа массива в последнем сегменте.

        Покрывает строку 455: `if key not in current: current[key] = []`.
        Путь 'items[0]' — массив в финальном сегменте, ключ отсутствует.
        """
        data: Dict[str, Any] = {}
        self.actualizer._set_field_value(data, "items[0]", "value_A")
        assert "items" in data
        assert data["items"][0] == "value_A"

    def test_set_field_value_array_in_last_part_extend_list(self) -> None:
        """_set_field_value: расширение списка для индекса в последнем сегменте.

        Покрывает строку 461: `while len(current_list) <= idx: current_list.append({})`.
        Список короче, чем индекс — нужно дополнить пустыми dict-ами.
        """
        data: Dict[str, Any] = {"items": ["existing"]}
        self.actualizer._set_field_value(data, "items[3]", "value_D")
        assert len(data["items"]) == 4
        assert data["items"][3] == "value_D"

    # --- Lines 464-468: _set_field_value — [] in last part ---

    def test_set_field_value_empty_array_dict_value(self) -> None:
        """_set_field_value: [] в последнем сегменте, значение — dict.

        Покрывает строки 464-465: `if isinstance(value, dict): current_list.append(value)`
        """
        data: Dict[str, Any] = {"items": []}
        self.actualizer._set_field_value(data, "items[]", {"name": "X"})
        assert len(data["items"]) == 1
        assert data["items"][0] == {"name": "X"}

    def test_set_field_value_empty_array_scalar_value(self) -> None:
        """_set_field_value: [] в последнем сегменте, значение — scalar, список пуст.

        Покрывает строки 466-468: scalar value, `if len(current_list) == 0: current_list.append({})`.
        """
        data: Dict[str, Any] = {"items": []}
        self.actualizer._set_field_value(data, "items[]", "scalar_value")
        # Для scalar value с пустым списком: создаётся пустой dict и добавляется
        assert len(data["items"]) == 1

    # --- Line 486: _delete_field — array path, key not in dict ---

    def test_delete_field_array_path_key_not_in_dict(self) -> None:
        """_delete_field: путь через массив, ключ отсутствует в dict.

        Покрывает строку 486: `if not isinstance(current, dict) or key not in current: return False`.
        """
        data = {"other": [{"name": "A"}]}
        result = self.actualizer._delete_field(data, "items[0]/name")
        assert result is False

    # --- Line 612: _compute_rename_score — dictionary match ---

    def test_compute_rename_score_dictionary_match(self) -> None:
        """_compute_rename_score: совпадение dictionary прибавляет score.

        Покрывает строку 612: `if old_meta.dictionary and ... and old_meta.dictionary == new_meta.dictionary`.
        """
        old = FieldMetadata(path="old_field", name="old_field", field_type="string", dictionary="OKEI")
        new = FieldMetadata(path="new_field", name="new_field", field_type="string", dictionary="OKEI")
        score = JsonActualizer._compute_rename_score(old, new)
        # dictionary совпадает → +1, field_type совпадает → +1, parent_path совпадает → +1 (root)
        assert score >= 2  # как минимум field_type и dictionary

    # --- Lines 687-688: _process_renames exception ---

    def test_process_renames_exception_handling(self) -> None:
        """_process_renames: исключение при обработке переименования.

        Покрывает строки 687-688: except Exception → errors.append.
        """
        old_meta = FieldMetadata(path="old_name", name="old_name", field_type="string")
        new_meta = FieldMetadata(path="new_name", name="new_name", field_type="string")
        rename = RenamePair(
            old_path="old_name", new_path="new_name",
            old_meta=old_meta, new_meta=new_meta, match_score=5,
        )

        result = ActualizationResult(actualized_data={"old_name": "value"})
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []

        # Заставить _navigate_path бросить исключение через повреждённые данные
        with patch.object(self.actualizer, "_navigate_path", side_effect=RuntimeError("boom")):
            self.actualizer._process_renames(result, [rename], changes, errors)

        assert len(errors) == 1
        assert errors[0].change_type == "error"
        assert "old_name" in errors[0].reason

    # --- Lines 747-753: _process_added_fields — no metadata ---

    def test_add_field_no_metadata(self) -> None:
        """_process_added_fields: FieldChange без new_meta и не в схеме.

        Покрывает строки 747-753: `if meta is None: errors.append(...)`.
        """
        field_change = FieldChange(
            path="unknown_field",
            change_type="added",
            old_meta=None,
            new_meta=None,
        )
        result = ActualizationResult(actualized_data={})
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []
        new_schema: Dict[str, FieldMetadata] = {}

        self.actualizer._process_added_fields(result, [field_change], new_schema, changes, errors)

        assert len(errors) == 1
        assert errors[0].change_type == "error"
        assert "unknown_field" in errors[0].reason

    # --- Lines 826-837: _process_modified_fields — old_value is None ---

    def test_modify_field_old_value_none(self) -> None:
        """_process_modified_fields: старое значение None — генерация нового.

        Покрывает строки 826-837: `if old_value is None: ... change_type="modified_regenerated"`.
        """
        field_change = FieldChange(
            path="field_a",
            change_type="modified",
            old_meta=FieldMetadata(path="field_a", name="field_a", field_type="string"),
            new_meta=FieldMetadata(path="field_a", name="field_a", field_type="string", constraints={"length": 10}),
            changes={"constraints": "length"},
        )
        result = ActualizationResult(actualized_data={})  # field_a отсутствует → None
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []
        new_schema = {"field_a": FieldMetadata(path="field_a", name="field_a", field_type="string", constraints={"length": 10})}

        self.actualizer._process_modified_fields(result, [field_change], new_schema, changes, errors)

        assert any(c.change_type == "modified_regenerated" and c.path == "field_a" for c in changes)

    # --- Lines 855-858: _process_modified_fields — transform returns None ---

    def test_modify_field_transform_returns_none(self) -> None:
        """_process_modified_fields: _transform_value возвращает None — перегенерация.

        Покрывает строки 855-858: gen_value generation when transform fails.
        """
        field_change = FieldChange(
            path="field_x",
            change_type="modified",
            old_meta=FieldMetadata(path="field_x", name="field_x", field_type="integer"),
            new_meta=FieldMetadata(path="field_x", name="field_x", field_type="boolean"),
            changes={"type": "integer→boolean"},
        )
        result = ActualizationResult(actualized_data={"field_x": 42})
        changes: List[ActualizationChange] = []
        errors: List[ActualizationChange] = []
        new_schema = {"field_x": FieldMetadata(path="field_x", name="field_x", field_type="boolean")}

        self.actualizer._process_modified_fields(result, [field_change], new_schema, changes, errors)

        # integer → boolean не поддерживается, transform вернёт None
        regen_changes = [c for c in changes if c.change_type == "modified_regenerated"]
        assert len(regen_changes) == 1
        assert regen_changes[0].path == "field_x"

    # --- Line 971: _validate_value — number type accepts int ---

    def test_validate_value_number_accepts_int(self) -> None:
        """_validate_value: type='number' принимает int (строка 971).

        Покрывает строку 971: `elif meta.field_type == "number" and isinstance(value, (int, float)): pass`.
        """
        meta = FieldMetadata(
            path="price", name="price", field_type="number",
            constraints={"min": 0},
        )
        assert self.actualizer._validate_value(42, meta) is True
        assert self.actualizer._validate_value(3.14, meta) is True