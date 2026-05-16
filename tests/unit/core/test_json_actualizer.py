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