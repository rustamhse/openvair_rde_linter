#!/usr/bin/env python3

"""Генерирует YAML-спецификацию bounded context из исходников OpenVAir.

Путь модуля: ``<repo_root>/openvair/modules/<feature>/``.

Алгоритм:
    1) ``load_module_sources`` читает все ``*.py`` (не ``tests``, не ``__pycache__``).
    2) ``build_code_artifacts`` восстанавливает те же символы, что увидит линтер позже.

Так файл спеки является «контравариантным» описанием к проверке: если перегенерировать и
ничего не менять в коде — ``Comparator`` после этого должен сообщать об успехе.
"""

from __future__ import annotations

import argparse

# pathlib и sys: см. ниже вставку корня репозитория в sys.path, чтобы находился пакет requirements_linter
# при запуске ``python requirements_linter/generate_openvair_specs.py``.
import sys
from pathlib import Path

_REPO_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_IMPORTS))

# YAML — человекочитаемый язык описания архитектурного контракта; safe_dump ограничивает типы сериализации.
import yaml

from requirements_linter.ast_specs import MODULE_FUNCTIONS_BUCKET, build_code_artifacts, load_module_sources


def artifacts_to_contract_layers(artifacts: dict[str, dict[str, object]]) -> dict[str, dict]:
    """Превращает внутренний ``code_artifacts`` в структуру, которую понимает ``Comparator``.

    Внутренний формат смешивает классы и ``MODULE_FUNCTIONS_BUCKET``; YAML разделяет их ключами:
    ``required_classes`` vs ``required_module_functions``.

    Args:
        artifacts: Результат build_code_artifacts.

    Returns:
        Словарь ``layers.<layer_name>: { required_classes, optional required_module_functions }``.
    """
    layers_out: dict[str, dict] = {}
    for layer_name in sorted(artifacts.keys()):
        layer_bucket = artifacts[layer_name]

        mf_raw = layer_bucket.get(MODULE_FUNCTIONS_BUCKET, {})
        mf_map: dict[str, list[str]] = mf_raw if isinstance(mf_raw, dict) else {}  # type: ignore[assignment]

        # Все ключи второго уровня, кроме служебного ведра — имена классов.
        classes: dict[str, list[str]] = {}
        for k, v_obj in sorted(layer_bucket.items(), key=lambda item: item[0]):
            if k == MODULE_FUNCTIONS_BUCKET:
                continue
            if isinstance(v_obj, list):
                classes[str(k)] = [str(x) for x in v_obj]  # type: ignore[list-item]

        required_classes_block = [{'name': cname, 'methods': methods} for cname, methods in sorted(classes.items())]

        layer_doc: dict = {'required_classes': required_classes_block}

        mf_entries = [
            {'relative_path': rel_path_norm, 'functions': fn_list}
            for rel_path_norm, fn_list in sorted(mf_map.items())
        ]
        # Пишем ключ только когда есть топ-уровневые функции (например entrypoints/api.py).
        if mf_entries:
            layer_doc['required_module_functions'] = mf_entries

        layers_out[layer_name] = layer_doc

    return layers_out


def build_spec_document(feature_name: str, module_root: Path, repo_root: Path) -> dict:
    """Читает диск целикого bounded context и формирует документ перед записью YAML.

    Args:
        feature_name: Имя папки контекста (storage, network, …) — становится ключом ``feature``.
        module_root: Каталог ``openvair/modules/<feature>``.
        repo_root: Корень репозитория для ``meta.source`` в относительной форме — пересборка воспроизводима между машинами.

    Returns:
        Словарь готовый к ``yaml.safe_dump``.
    """
    sources = load_module_sources(module_root)
    artifacts = build_code_artifacts(sources)
    try:
        source_meta = module_root.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        source_meta = str(module_root.resolve())
    return {
        # meta — для мэйнтейнеров: автоген не заменяет осмысленный контракт без ревью.
        'meta': {
            'source': source_meta,
            'maintainer_notes': (
                'Снимок символов с диска. Удалите лишнее и оставьте только публичный контракт модуля.'
            ),
        },
        'feature': feature_name,
        'layers': artifacts_to_contract_layers(artifacts),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI-парсинг: поддерживаются явные или дефолтные пути внутри рабочей копии."""
    repo_default = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description=(
            'Сгенерировать YAML-архитектурный контракт для bounded context '
            '(поддиректория openvair/modules/<feature>).'
        )
    )
    parser.add_argument(
        '--feature',
        metavar='NAME',
        required=True,
        help='Имя директории контекста, например storage или virtual_machines',
    )
    parser.add_argument(
        '--repo-root',
        type=Path,
        default=repo_default,
        help='Корень репозитория с подкаталогом openvair/ (default: родитель этого пакета)',
    )
    parser.add_argument(
        '--out-dir',
        type=Path,
        default=repo_default / 'specs',
        help='Куда сохранять <feature>.yaml (default: specs/ в корне репозитория)',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Точка входа: строим документ, печатаем файл, сообщаем путь пользователю."""
    opts = parse_args(argv if argv is not None else sys.argv[1:])

    module_root = opts.repo_root / 'openvair' / 'modules' / opts.feature
    doc = build_spec_document(opts.feature, module_root.resolve(), opts.repo_root.resolve())

    opts.out_dir.mkdir(parents=True, exist_ok=True)
    out_file = opts.out_dir / f'{opts.feature}.yaml'

    dumps = yaml.safe_dump(
        doc,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    # Path.write_text блокирующая запись целиком маленьких YAML — достаточно для задачи.
    out_file.write_text(dumps, encoding='utf-8')
    print(f'Wrote {out_file}')  # noqa: T201
    return 0


if __name__ == '__main__':
    sys.exit(main())
