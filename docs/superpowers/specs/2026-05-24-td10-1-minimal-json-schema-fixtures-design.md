# TD-10.1: Минимальные JSON Schema фикстуры (v070, v072)

**Дата:** 2026-05-24
**Статус:** Утверждён
**Приоритет:** P2 (предпосылка для TD-9 и TD-22)

---

## 1. Контекст и мотивация

`tests/fixtures/schemas/` содержит устаревшие `V070Call1Rq.json` (28 строк) и `V072Call1Rq.json` (40 строк), которые:
- Не содержат `condition` (SpEL-выражения для УО-полей)
- Не содержат `dictionary` (справочники)
- Не содержат constraints (`pattern`, `minLength`, `maxLength`, `minimum`, `maximum`, `enum`)
- Не содержат `format` (`date`, `date-time`, `uuid`)
- Не содержат `array` с `items`
- V072 не содержит diff-паттернов (новые/удалённые/модифицированные/переименованные поля)

Продакшн-схемы `data/V72Call1Rq.json` (1535 строк, 245 полей) слишком громоздки для unit/integration тестов. TD-22 (E2E) будет использовать полные схемы.

**Решение:** Создать минимальные управляемые схемы ~27 полей, покрывающие все значимые типы.

---

## 2. Дизайн-решения

| Решение | Выбор | Обоснование |
|---------|-------|-------------|
| Структура корня | Вложенная (`loanRequest` → поля) | Как в продакшн-схемах, тестирует вложенные пути |
| Подход | Ручная мастерская | Полный контроль над составом полей |
| v072 формат | Полная схема (v070 + diff) | SchemaParser ожидает полную JSON Schema |
| Размер | ~27 полей (расширенный набор) | Покрывает все типы для интеграционных тестов |
| SpEL условия | Реалистичные (из продакшна, упрощённые) | Тестирует реальный парсинг ConditionEvaluator |
| Старые фикстуры | Заменить новыми | V070Call1Rq/V072Call1Rq не несут ценности |

---

## 3. Состав полей v070_minimal.json

### Формат файла

JSON Schema `draft/2019-09`, с метаданными продакшн-формата:

```json
{
  "$schema": "https://json-schema.org/draft/2019-09/schema",
  "direction": "request",
  "stageName": "call1",
  "version": "070",
  "subVersion": "",
  "dataQuality": false,
  "type": "object",
  "properties": { ... },
  "required": ["loanRequest"]
}
```

### Обязательность полей (О/УО/Н)

- **О** — поле в `required` массиве родителя
- **УО** — поле НЕ в `required`, имеет `condition: {expression, message}`
- **Н** — поле НЕ в `required`, нет `condition`

### 3.1 Обязательные поля (О)

| # | Путь | Тип | Constraints | Примечание |
|---|------|-----|-------------|------------|
| 1 | `loanRequest/creditAmt` | integer | `maxIntLength: 10` | Сумма кредита |
| 2 | `loanRequest/productCdExt` | integer | `dictionary: "PRODUCT_TYPE"`, `maxIntLength: 10` | Справочник |
| 3 | `loanRequest/channelCdExt` | integer | `dictionary: "SALE_CHANNEL"`, `maxIntLength: 10` | Справочник |

### 3.2 Условно-обязательные поля (УО)

| # | Путь | Тип | Condition | Примечание |
|---|------|-----|-----------|------------|
| 4 | `loanRequest/firstName` | string, `maxLength: 100` | `notNull(#this.regionCd)` | Простое условие |
| 5 | `loanRequest/additionalInfo` | string, `maxLength: 500` | `and(notNull(#parent.regionCd), in(#parent.channelCdExt, 10620002, 10620013))` | Составное условие |
| 6 | `loanRequest/nstAppTypeCdExt` | integer, `maxIntLength: 10`, `dictionary: "NST_APP_TYPE"` | `anyMatch(#rootBean.loanRequest.creditParameters, eq(productCdExt, 10410053))` | Ссылка на массив |
| 7 | `loanRequest/relatedLoanRequestExtId` | string, `maxLength: 50` | `and(eq(#parent.channelCdExt, 10620014), anyMatch(#rootBean.loanRequest.creditParameters, eq(productCdExt, 10410017)))` | Сложное вложенное условие |

### 3.3 Опциональные поля (Н)

| # | Путь | Тип | Constraints/Format | Примечание |
|---|------|-----|--------------------|------------|
| 8 | `loanRequest/comment` | string | `maxLength: 200` | Простая строка |
| 9 | `loanRequest/agreementDate` | string | `format: "date"` | Дата |
| 10 | `loanRequest/requestId` | string | `format: "uuid"`, `maxLength: 36` | UUID |
| 11 | `loanRequest/extCreateDttm` | string | `format: "date-time"` | Дата-время |
| 12 | `loanRequest/inn` | string | `pattern: "^\\d{10,12}$"`, `minLength: 10`, `maxLength: 12` | ИНН с regex |
| 13 | `loanRequest/amount` | number | `minimum: 1000`, `maximum: 10000000` | Числовой диапазон |
| 14 | `loanRequest/status` | string | `enum: ["DRAFT", "APPROVED", "REJECTED"]` | Перечисление |
| 15 | `loanRequest/loanTerm` | integer | `minimum: 1`, `maximum: 360`, `maxIntLength: 3` | Целочисленный диапазон |
| 16 | `loanRequest/interestRate` | number | `minimum: 0.1` | Дробное число |
| 17 | `loanRequest/loanRequestExtId` | string | `maxLength: 50` | Идентификатор |
| 18 | `loanRequest/reprocessFlg` | boolean | — | Булево поле |
| 19 | `loanRequest/regionCd` | integer | `dictionary: "REGION"`, `maxIntLength: 10` | Регион (ссылка в SpEL) |

### 3.4 Вложенные объекты

**loanRequest/sendChannelInfo** (object):

| # | Путь | Тип | Обязательность | Примечание |
|---|------|-----|----------------|------------|
| 20 | `sendChannelInfo/aggregatorCdExt` | integer, `maxIntLength: 10` | О | Вложенное обязательное |
| 21 | `sendChannelInfo/sourceCdExt` | integer, `dictionary: "SOURCE_CD"`, `maxIntLength: 10` | Н | Вложенное опциональное |

**loanRequest/creditParameters** (array):

| # | Путь | Тип | Примечание |
|---|------|-----|------------|
| 22 | `creditParameters[]/productCdExt` | integer, `dictionary: "PRODUCT_TYPE"`, `maxIntLength: 10` | Поле элемента массива |
| 23 | `creditParameters[]/creditAmt` | integer, `maxIntLength: 10` | Поле элемента массива |
| 24 | `creditParameters[]/term` | integer, `minimum: 1`, `maximum: 360` | Поле элемента массива |

**loanRequest/guarantors** (array):

| # | Путь | Тип | Примечание |
|---|------|-----|------------|
| 25 | `guarantors[]/fullName` | string, `maxLength: 200` | Поле элемента массива |
| 26 | `guarantors[]/inn` | string, `pattern: "^\\d{10,12}$"`, `minLength: 10`, `maxLength: 12` | Поле элемента массива |

**Итого: ~26 уникальных путей полей**

### Покрытие типов

| Категория | Покрытие |
|-----------|----------|
| Обязательность | О (3), УО (4), Н (11) |
| Типы данных | integer (6), string (8), number (2), boolean (1), object (1), array (2) |
| Constraints | `minLength`, `maxLength`, `minimum`, `maximum`, `pattern`, `enum`, `maxIntLength` |
| Format | `date`, `date-time`, `uuid` |
| Dictionary | `PRODUCT_TYPE`, `SALE_CHANNEL`, `NST_APP_TYPE`, `SOURCE_CD`, `REGION` |
| SpEL условия | `notNull(#this)`, `and(notNull, in)`, `anyMatch(#rootBean, eq)`, `and(eq, anyMatch)` |
| Вложенность | object (2 уровня), array (2 массива) |

---

## 4. Diff v070 → v072

v072_minimal.json — полная схема (копия v070 + изменения). Не delta-формат.

### 4.1 +3 новых поля

| # | Путь | Тип | Обязательность | Constraints | Примечание |
|---|------|-----|----------------|-------------|------------|
| 1 | `loanRequest/phone` | string | О (required) | `minLength: 10`, `maxLength: 15` | Новое обязательное |
| 2 | `loanRequest/purposeCdExt` | integer | УО | `dictionary: "LOAN_PURPOSE"`, `maxIntLength: 10`, `condition: notNull(#this.loanAmt)` | Новое УО |
| 3 | `loanRequest/middleName` | string | Н (опциональное) | `maxLength: 100` | Новое опциональное |

### 4.2 -1 удалённое поле

| # | Путь | Примечание |
|---|------|------------|
| 1 | `loanRequest/reprocessFlg` | Удалено в v072 |

### 4.3 2 модифицированных поля

| # | Путь | Атрибут | v070 | v072 | Тип изменения |
|---|------|---------|------|------|---------------|
| 1 | `loanRequest/amount` | `maximum` | `10000000` | `50000000` | Constraint ослаблен |
| 2 | `loanRequest/inn` | `pattern` | `^\\d{10,12}$` | `^\\d{10}$` | Pattern сужен |

### 4.4 1 переименование

| # | v070 | v072 | Примечание |
|---|------|------|------------|
| 1 | `loanRequest/sendChannelInfo` | `loanRequest/channelInfo` | Объект переименован, внутренние поля сохранены |

**Итог v072:** 26 полей v070 + 3 новых - 1 удалённое = 28 уникальных путей.

---

## 5. Файловая структура

```
tests/fixtures/schemas/
├── __init__.py                  # Существует
├── v070_minimal.json            # НОВЫЙ — минимальная схема v070 (~27 полей)
└── v072_minimal.json            # НОВЫЙ — минимальная схема v072 (diff от v070)
```

**Удалить:**
- `tests/fixtures/schemas/V070Call1Rq.json` — заменён на `v070_minimal.json`
- `tests/fixtures/schemas/V072Call1Rq.json` — заменён на `v072_minimal.json`

---

## 6. Критерии готовности

1. `SchemaParser.load_schema(Path("tests/fixtures/schemas/v070_minimal.json"))` — парсит без ошибок
2. `SchemaParser.load_schema(Path("tests/fixtures/schemas/v072_minimal.json"))` — парсит без ошибок
3. Проверка покрытия: количество полей v070 ≈ 26, v072 ≈ 28
4. Наличие всех типов: О/УО/Н, condition, dictionary, constraints, format, array, object
5. SchemaComparator корректно находит diff между v070 и v072 (3 добавленных, 1 удалённое, 2 изменённых, 1 переименование)
6. ConditionEvaluator корректно парсит SpEL-условия из condition-блоков

---

## 7. За рамками (не входит в TD-10.1)

- Словари (`tests/fixtures/dictionaries/`) — TD-10.2
- Сценарии (`tests/fixtures/scenarios/`) — TD-10.2
- Integration conftest.py — TD-10.3
- E2E-тесты на полных продакшн-схемах — TD-22
- Обновление существующих unit-тестов для использования новых фикстур (отдельная задача)