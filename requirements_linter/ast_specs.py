"""Разделяемая логика AST и слоёв для RDE-линтера и генератора YAML-контрактов.

Переиспользуется:
  * построением ``code_artifacts`` в линтере;
  * выгрузкой спецификации из кода генератором.

Так имена слоёв и правило «что считать публичным символом» живут в одном месте.
"""

from __future__ import annotations

import ast

# pathlib — объектный способ собирать пути к .py без ручной склейки строк;
# нужен генератором при обходе каталогов модуля (bounded context).
from pathlib import Path

# Белый список имён директорий первого уровня внутри openvair/modules/<контекст>/,
# которые в OpenVAir соответствуют «слоям» гексагональной/DDD-раскладки.
# Если файл лежит, например, в storage/domain/foo/bar.py — слой = первый сегмент: domain.
# Файлы config.py в корне модуля без префикса слоя здесь игнорируются (нет контрактного слоя).
KNOWN_LAYER_NAMES = frozenset({
    'domain',
    'service_layer',
    'adapters',
    'entrypoints',
})

# Под ключом с этим именем в словаре слоя хранятся топ-уровневые функции файлов модуля
# (формат: относительный путь файла от корня bounded context → список имён).
# Так мы не смешиваем карту «класс → методы» с картой «файл → функции»
# без отдельного типа данных.
MODULE_FUNCTIONS_BUCKET = '$module_functions$'


def normalize_rel_path(path_str: str) -> str:
    """Приводит ключ пути к виду posix (слэши '/') без ведущих './'.

    Используется, чтобы и генератор YAML, и Analyzer смотрели на одинаковые строки ключей.

    Args:
        path_str: Относительный путь файла или как к нему пришёл вызывающий код.

    Returns:
        Нормализованная строка POSIX-пути.
    """
    p = Path(path_str)
    parts = []
    # Path приводит внутреннее представление ОС к единым компонентам.
    for part in p.parts:
        if part in ('.',):
            continue
        parts.append(part)
    out = Path(*parts).as_posix() if parts else ''
    return out


def infer_layer(rel_path_normalized: str) -> str | None:
    """Возвращает имя слоя по первой компоненте относительного пути файла или None.

    Пример:
        infer_layer('domain/model.py') -> 'domain'
        infer_layer('config.py') -> None (нет в KNOWN_LAYER_NAMES).

    Args:
        rel_path_normalized: Путь от корня bounded context уже в posix-форме.

    Returns:
        Имя слоя из KNOWN_LAYER_NAMES или None, если файл вне архитектурных папок.
    """
    if not rel_path_normalized:
        return None
    first = Path(rel_path_normalized).parts[0]
    return first if first in KNOWN_LAYER_NAMES else None


def is_contract_public_name(name: str) -> bool:
    """Признак публичного имени метода или функции в смысле контракта.

    По соглашению для линтера (и для защиты магистерской) всё, что начинается с '_' —
    считаем внутренним API класса или модуля и не включаем в автогенерацию без явного желания мэйнтейнера.
    То же отсекает __init__, __repr__ и прочие дандеры (они все начинаются с '__', а значит с '_' тоже).

    Args:
        name: Идентификатор Python из AST.

    Returns:
        True, если имя должно попадать в описание публичного контракта.
    """
    return not name.startswith('_')


def iter_public_methods(class_node: ast.ClassDef) -> list[str]:
    """Список синхронных и асинхронных методов класса первого уровня тела класса.

    Почему только прямые дети класса (child в node.body): вложенные классы объявлены там же —
    они обрабатываются отдельным ast.ClassDef на ast.walk дереве; здесь нужны методы этого класса,
    а не вложенного.

    Почему FunctionDef И AsyncFunctionDef: в сервисах OpenVAir есть async методы корутин —
    если собирать только FunctionDef, линтер ложно сочтёт, что метод «отсутствует».

    Args:
        class_node: Узел AST описания класса.

    Returns:
        Отсортированный список уникальных публичных имён методов.
    """
    names: list[str] = []
    # Перебираем только прямых «детей» тела класса.
    for child in class_node.body:
        if isinstance(child, ast.FunctionDef) or isinstance(child, ast.AsyncFunctionDef):
            if is_contract_public_name(child.name):
                names.append(child.name)
    return sorted(set(names))


def iter_public_module_functions(module_node: ast.Module) -> list[str]:
    """Имена публичных функций верхнего уровня модуля (как FastAPI-хендлеры в api.py).

    Обходится только module_node.body — не ast.walk всего дерева — чтобы не подцепить
    вложенные функции внутри других функций или классов (они не считаются публичным API модуля).

    Args:
        module_node: Корневой узел после ast.parse(...).

    Returns:
        Отсортированный список имён топ-уровневых публичных функций и корутин.
    """
    names: list[str] = []
    for node in module_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_contract_public_name(node.name):
                names.append(node.name)
    return sorted(set(names))


def _merge_functions_for_file(
    bucket: dict[str, list[str]],
    rel_file: str,
    functions: list[str],
) -> None:
    """Объединяет найденные функции для одного и того же relative_path между проходами (если бы было).

    На практике один файл обрабатывается один раз; функция сохранена для симметрии с классами.

    Args:
        bucket: Словарь «относительный путь файла от корня модуля → имена функций».
        rel_file: Ключ вида ``entrypoints/api.py``.
        functions: Новые имена функций этого файла.
    """
    if rel_file not in bucket:
        bucket[rel_file] = sorted(set(functions))
        return
    merged = set(bucket[rel_file])
    merged.update(functions)
    bucket[rel_file] = sorted(merged)


def _merge_class_methods_layer_inplace(
    layer_dict: dict[str, object],
    class_name: str,
    methods: list[str],
) -> None:
    """Вливает методы найденного класса в уже существующий словарь слоя (на месте)."""
    if class_name == MODULE_FUNCTIONS_BUCKET:
        raise ValueError(
            f'Class name clashes with sentinel {MODULE_FUNCTIONS_BUCKET!r}'
        )

    prev_raw = layer_dict.get(class_name, [])
    if not prev_raw:
        layer_dict[class_name] = sorted(set(methods))
        return
    prev: set[str] = set(prev_raw)  # type: ignore[arg-type]
    prev.update(methods)
    layer_dict[class_name] = sorted(prev)


def build_code_artifacts(code_files: dict[str, str]) -> dict[str, dict[str, object]]:
    """Строит словарь артефактов кода bounded context для Comparator.

    Ключ первого уровня — строка имени архитектурного слоя (KNOWN_LAYER_NAMES).

    На каждом слое два вида ключей второго уровня:
      - строки без '$' — имена классов → списки методов;
      - зарезервированный ключ ``MODULE_FUNCTIONS_BUCKET`` → словарь путей файлов на списки функций.

    Аргумент ``code_files`` — отображение *(относительный путь от корня модуля POSIX, исходник)*.
    Пути должны начинаться с имени слоя (``domain/...``), чтобы infer_layer нашёл контекст.

    Args:
        code_files: Словарь путём к тексту каждого .py участвующего в проверке.

    Returns:
        Вложенные структуры, готовые для Comparator (вместе с проверкой модульных функций).
    """
    artifacts: dict[str, dict[str, object]] = {}

    for raw_path, text in sorted(code_files.items()):
        norm = normalize_rel_path(raw_path)
        layer = infer_layer(norm)
        if layer is None:
            # Например: ``config.py`` или ``libs/utils.py`` — вне whitelist слоёв, пропускаем.
            continue

        layer_dict = artifacts.setdefault(layer, {})
        mf_raw = layer_dict.setdefault(MODULE_FUNCTIONS_BUCKET, {})
        if not isinstance(mf_raw, dict):
            mf_raw = {}
            layer_dict[MODULE_FUNCTIONS_BUCKET] = mf_raw
        mf_bucket_inner: dict[str, list[str]] = mf_raw  # type: ignore[assignment]

        tree = ast.parse(text)

        funcs_here = iter_public_module_functions(tree)
        if funcs_here:
            _merge_functions_for_file(mf_bucket_inner, norm, funcs_here)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = iter_public_methods(node)
                _merge_class_methods_layer_inplace(layer_dict, node.name, methods)

    return artifacts


def load_module_sources(module_root: Path) -> dict[str, str]:
    """Читает все ``*.py`` под корнем bounded context, отфильтровывая тестовый код.

    Пропускаются сегменты пути ``tests`` и каталог ``__pycache__``.
    Никакая эвристика не отбрасывает ``mibs``: подмодули со слоями останутся, прочее — где нет
    KNOWN_LAYER_NAMES первым сегментом — просто игнорируется на этапе infer_layer в build_code_artifacts.

    Args:
        module_root: Каталог ``openvair/modules/<контекст>``.

    Returns:
        Относительные POSIX-пути внутрь module_root на полный текст файла UTF-8.
    """
    out: dict[str, str] = {}
    if not module_root.is_dir():
        return out
    # rglob('*') затем фильтруем суффикс — так проще, чем **/*.py совместимость.
    for path in sorted(module_root.rglob('*.py')):
        if '__pycache__' in path.parts:
            continue
        if 'tests' in path.parts:
            continue
        rel = path.relative_to(module_root).as_posix()
        out[rel] = path.read_text(encoding='utf-8')
    return out
