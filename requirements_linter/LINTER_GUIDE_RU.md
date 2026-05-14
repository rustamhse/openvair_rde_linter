# RDE Linter: Полное руководство (RU)

Настоящий документ представляет собой практическое руководство по YAML-линтеру
`requirements_linter`.

Цель линтера:
- сравнить контракт из `specs/<feature>.yaml`;
- с реальным Python-кодом в `openvair/modules/<feature>/`;
- через AST-анализ (без запуска приложения, без тестов, без импорта
  бизнес-логики).

---

## 1. Функциональное назначение линтера

Линтер анализирует YAML-спецификацию и проверяет, что в кодовой базе
**действительно присутствуют**
все объявленные там публичные сущности:
- классы и их публичные методы;
- top-level функции в конкретных файлах;
- FastAPI endpoints (метод, путь, handler, параметры).

Важно:
- линтер проверяет только направление **spec -> code**;
- если в коде есть что-то лишнее, чего нет в YAML, это **не ошибка**;
- если в YAML заявлено что-то, чего нет в коде, это **ошибка**.

---

## 2. Что именно валидируется

Проверка идет по слоям (обычно `domain`, `service_layer`, `adapters`,
`entrypoints`).

### 2.1 `required_classes`

Для каждого класса:
- должен существовать класс с таким именем;
- должны существовать все методы из `methods`.

Ограничение:
- учитываются только публичные имена; 
- методы/функции с `_` как начало имени
  считаются непубличными контрактно.

### 2.2 `required_module_functions`

Проверяются top-level `def`/`async def` в указанном файле:
- `relative_path` задается от корня модуля (`openvair/modules/<feature>/`);
- в `functions` перечисляются ожидаемые callables.

### 2.3 `required_http_endpoints`

Для FastAPI проверяются:
- `method` (GET/POST/PATCH/...),
- `path`,
- `handler`,
- `parameters` (name, kind, required, type_hint).

Сопоставление параметров строгое по сигнатуре.

---

## 3. Минимальная правильная структура YAML

```yaml
meta:
  source: openvair/modules/my_feature
  maintainer_notes: "Contract for RDE linter"

feature: my_feature

layers:
  domain:
    required_classes:
      - name: MyDomainService
        methods:
          - create
          - delete

  entrypoints:
    required_classes:
      - name: MyCrud
        methods:
          - get_items
    required_module_functions:
      - relative_path: entrypoints/api.py
        functions:
          - get_items
    required_http_endpoints:
      - method: GET
        path: /items
        handler: get_items
        parameters:
          - name: crud
            kind: depends
            required: true
            type_hint: MyCrud
```

---

## 4. Как формировать спецификацию для стабильного прохождения проверки

### 4.1 Имена должны совпадать один-в-один

- класс: `SchedulerCRUD` != `SchedulerCrud`;
- функция: `update_job` != `edit_job`;
- type_hint: `schemas.CreateJobRequest` != `CreateJobRequest`.

### 4.2 Для `required_module_functions` путь должен быть реальным

Пример:
- если функция живет в `openvair/modules/user/entrypoints/api.py`,
  то `relative_path` должен быть ровно `entrypoints/api.py`.

### 4.3 Для HTTP важно все сразу

Линтер сверяет endpoint по тройке:
- method + path + handler.

Если не совпало хоть одно, получите:
- `No matching HTTP route in code for ...`

Если endpoint найден, но не совпали параметры:
- `parameter contract mismatch` с `spec:` и `code:` списками.

### 4.4 Учитывайте эвристики по типам параметров

Внутри HTTP-анализатора:
- `Depends(...)` -> `kind: depends`;
- `Body(...)`, `Form(...)`, `File(...)` -> `kind: body`;
- для аннотаций вида `schemas.Model` тоже часто выводится `body`;
- остальное обычно трактуется как `query`.

Поэтому safest-подход:
- сначала сгенерировать спецификацию;
- потом уже вручную подправлять только нужное.

---

## 5. Как запускать

## 5.1 Один модуль (рекомендуется в работе)

Из корня репозитория:

```bash
python requirements_linter/rde_linter.py specs/user.yaml openvair/modules/user
```

Коды возврата:
- `0` - mismatch нет;
- `1` - mismatch есть.

### 5.2 Важно про запуск без аргументов

Если запустить:

```bash
python requirements_linter/rde_linter.py
```

по умолчанию проверится только:
- `specs/storage.yaml`
- `openvair/modules/storage`

Это частая причина "почему мой модуль не проверился".

### 5.3 Проверка всех спецификаций

```bash
python requirements_linter/lint_repo_specs.py
```

Скрипт берет каждый `specs/*.yaml`, определяет feature и проверяет
`openvair/modules/<feature>`.

Если `feature` в YAML нет - берется имя файла.

---

## 6. Как устроено сопоставление feature -> module

В `lint_repo_specs.py`:
- если в YAML есть `feature`, используется он;
- иначе используется имя файла без `.yaml`.

Пример:
- файл `specs/user.yaml` + `feature: user` -> `openvair/modules/user`;
- файл `specs/user.yaml` без `feature` -> тоже `openvair/modules/user`.

---

## 7. Все типовые ошибки и что они означают

Ниже реальные паттерны сообщений из Comparator/CLI.

### 7.1 `Layer '<name>' not found under scanned sources ...`

Причина:
- в слое нет подходящих `.py` после фильтрации;
- или слой называется не как ожидает линтер.

Что делать:
- проверить структуру каталогов модуля;
- проверить, что слой существует и файлы лежат в нем;
- проверить имя слоя в YAML.

### 7.2 `class <Name> not found in code artifacts`

Причина:
- класс с таким именем не найден в указанном слое.

Что делать:
- исправить имя в YAML или коде;
- убедиться, что класс в правильном слое.

### 7.3 `Class <Name> does not contain expected method <method>`

Причина:
- у класса нет такого публичного метода.

Что делать:
- добавить метод;
- или скорректировать спецификацию под фактическое имя.

### 7.4 `File '<relative_path>' does not expose expected top-level callable ...`

Причина:
- в указанном файле нет top-level функции с этим именем;
- функция может быть методом класса, а не top-level.

Что делать:
- сверить путь и имя;
- при необходимости вынести/добавить top-level функцию.

### 7.5 `Module file '<relative_path>' was not scanned for functions ...`

Причина:
- файл отсутствует;
- путь не попал в анализ (например, слой не распознан).

Что делать:
- проверить физический путь;
- проверить первый сегмент пути относительно layer rules.

### 7.6 `No matching HTTP route in code for ...`

Причина:
- не совпали method/path/handler;
- или роут не извлекся AST-анализатором (например, динамический декоратор).

Что делать:
- сделать literal-декоратор `@router.get("/path")`;
- проверить `APIRouter(prefix="...")` literal;
- синхронизировать handler name.

### 7.7 `parameter contract mismatch`

Причина:
- endpoint найден, но отличаются параметры
  (`name/kind/required/type_hint`).

Что делать:
- взять фактическую сигнатуру endpoint из кода;
- выровнять YAML один-в-один.

### 7.8 `required_http_endpoints must be a list`

Причина:
- в YAML это не список.

Что делать:
- исправить структуру YAML.

### 7.9 `required_http_endpoints entry must be a mapping`

Причина:
- один элемент списка endpoints не является объектом `{...}`.

### 7.10
`HTTP endpoint spec must include non-empty method, path, handler`

Причина:
- пропущено одно из обязательных полей.

### 7.11
`Spec layer='<layer>' uses disallowed class name '$module_functions$' ...`

Причина:
- использовано зарезервированное служебное имя класса.

Что делать:
- переименовать класс в YAML.

### 7.12
`skip — bounded context directory missing (openvair/modules/<feature>)`

Причина:
- для спецификации отсутствует каталог модуля.

---

## 8. Ограничения линтера (важно)

Линтер FastAPI extraction поддерживает в MVP:
- `router = APIRouter(prefix="...")` с literal prefix;
- `@router.get/post/put/patch/delete("...")` с literal path;
- top-level handlers.

Не поддерживается (или работает нестабильно):
- динамические пути/префиксы;
- обертки-декораторы вокруг route;
- `include_router(...)` как источник контракта;
- сложная метапрограммная генерация endpoint-ов.

---

## 9. Рекомендуемый рабочий процесс

1. Сгенерировать черновик спецификации:

```bash
python requirements_linter/generate_openvair_specs.py --feature my_feature
```

2. Упростить YAML до публичного контракта.
3. Прогнать проверку конкретного модуля:

```bash
python requirements_linter/rde_linter.py specs/my_feature.yaml openvair/modules/my_feature
```

4. Исправить mismatch.
5. Выполнить проверку всех спецификаций:

```bash
python requirements_linter/lint_repo_specs.py
```

6. Перед коммитом проверить pre-commit hook.

---

## 10. Быстрый FAQ

### "Почему линтер показывает mismatch, хотя endpoint есть?"

Скорее всего:
- не совпадает handler name;
- отличается `type_hint`;
- `kind` определился иначе (`query` vs `body`);
- path/prefix собрался иначе (слэши, prefix).

### "Почему линтер ничего не нашел в слое?"

Проверь:
- правильность директории слоя;
- что файл `.py`;
- что сущности публичные;
- что анализатор действительно сканирует эту папку.

### "Какой наиболее безопасный способ обновить спецификацию после рефакторинга?"

Сначала автогенерация, затем ручная чистка контракта.

---

## 11. Команды-шпаргалка

```bash
# 1) Один модуль
python requirements_linter/rde_linter.py specs/user.yaml openvair/modules/user

# 2) Все спецификации
python requirements_linter/lint_repo_specs.py

# 3) Генерация черновика
python requirements_linter/generate_openvair_specs.py --feature user

# 4) Тесты линтера
python -m pytest requirements_linter/tests -v --override-ini addopts=
```