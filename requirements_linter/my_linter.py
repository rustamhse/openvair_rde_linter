"""Черновой RDE-линтер для OpenVAir и учебный пример в одном файле.

Структура:
    * AstAnalyzer — оборачивает ``build_code_artifacts`` (:mod:`requirements_linter.ast_specs`), чтобы код
      читался либо из словаря «путь → исходник», либо с диска bounded context целиком.
    * Comparator — сравнивает YAML-документ (контракт, который задают мэйнтейнеры) и ``code_artifacts``.

Важное для защиты: спека YAML и линтер согласованы общим кодом экстрактора символов, иначе
«reverse engineering» через генератор давал бы ложную уверенность.
"""

from __future__ import annotations

import argparse
import sys

# pathlib — объектные пути; используется CLI при открытии каталогов OpenVAir.
from pathlib import Path

_REPO_ROOT_PREPEND = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_PREPEND) not in sys.path:
    # Нужно до строк ``from requirements_linter...``, когда скрипт вызывают напрямую:
    # ``python requirements_linter/my_linter.py`` не добавляет репозиторий в PYTHONPATH автоматически.
    sys.path.insert(0, str(_REPO_ROOT_PREPEND))

# PyYAML только читает контракт; запись генератором см. ``generate_openvair_specs``.
import yaml

from requirements_linter.ast_specs import (
    MODULE_FUNCTIONS_BUCKET,
    build_code_artifacts,
    load_module_sources,
    normalize_rel_path,
)


class AstAnalyzer:
    """Парсер исходников bounded context одного модуля OpenVAir.

    После того как вы добавили поддержку нескольких движущихся частей генератора спек,
    анализатор становится простым фасадом: он не дублирует логику слоёв и публичности,
    делегируя работу общей утилите ``build_code_artifacts``.
    """

    def __init__(self, code_files: dict[str, str]):
        """Сохраняет словарь «относительный путь POSIX → текст файла».

        Все ключи считаются **относительно корня** bounded context —
        точно как ``Path.relative_to`` при обходе ``openvair/modules/<контекст>``.

        Args:
            code_files: Словари с исходниками; не читает диск сам — удобно для юнит-тестов заглушками строк.
        """
        self.code_files = code_files
        self.code_artifacts: dict[str, dict[str, object]] = {}

    @classmethod
    def from_bounded_context_dir(cls, module_root: Path) -> AstAnalyzer:
        """Сканирует диск тем же фильтром, что и генератор спек."""
        snapshot = load_module_sources(module_root)
        return cls(snapshot)

    def extract(self) -> dict[str, dict[str, object]]:
        """Строит граф символов, совместимый с ``Comparator``.

        Returns:
            ``code_artifacts`` — см. описание Sentinel ``MODULE_FUNCTIONS_BUCKET`` в модуле ``ast_specs``.
        """
        # Делегирование сохраняет инвариант: что выгружает генератор, то понимает и линтер.
        self.code_artifacts = build_code_artifacts(self.code_files)
        return self.code_artifacts


class Comparator:
    """Сопоставляет YAML-контракт и множества символов на каждом архитектурном слое.

    В контракте допускается два блока на слое:
      * ``required_classes`` — обязательные классы и требуемые публичные методы имен **как они из AST**;
      * ``required_module_functions`` — топ-уровневая публичные функции/корутины по относительному пути файла.
        Это поддержка FastAPI-эндпоинтов declarative модуля ``entrypoints/api.py``.
    """

    def __init__(self, requirements: dict, code_artifacts: dict):
        """Держим ссылку на загруженный YAML и уже извлечённые символы.

        Args:
            requirements: Словарь после ``yaml.safe_load`` (структура с ``layers``).
            code_artifacts: Результат ``AstAnalyzer.extract``.
        """
        self.requirements = requirements
        self.code_artifacts = code_artifacts
        self.errors: list[str] = []

    def compare(self) -> list[str]:
        """Сравнивает по слоям, возвращая список человекочитаемых ошибок.

        Если слой упомянут только внутри блока модульных функций (не в спеках),
        здесь ошибка генерируется только если ключ присутствует в YAML; отсутствующий ключ слоя означает
        «нет требования» только если вы не включаете это слово в файл — комиссии полезно знать, что каждый
        слой в YAML должен содержаться в артефактах когда он заполнен.
        """
        for layer_name, layer_data in self.requirements.get(
            'layers', {}
        ).items():
            if layer_name not in self.code_artifacts:
                self.errors.append(
                    f"Layer '{layer_name}' not found under scanned sources "
                    '(нет файлов внутри этого слоя в bounded context после фильтрации).'
                )
                continue
            layer_bucket = self.code_artifacts[layer_name]

            for req_class in layer_data.get('required_classes', []):
                expected_name = req_class['name']
                expected_methods = req_class['methods']

                if expected_name == MODULE_FUNCTIONS_BUCKET:
                    msg = (
                        f'Спека layer={layer_name!r} задаёт недопустимое имя класса '
                        f'{MODULE_FUNCTIONS_BUCKET!r}: зарезервировано служебным ключом линтера.'
                    )
                    self.errors.append(msg)
                    continue

                if expected_name not in layer_bucket:
                    self.errors.append(
                        f'Layer: {layer_name}\n'
                        f' class {expected_name} not found in code artifacts'
                    )
                    continue
                current_methods_raw = layer_bucket[expected_name]
                if not isinstance(current_methods_raw, list):
                    msg = (
                        f'Внутренний сбой: для класса {expected_name} ожидался список методов, получено '
                        f'{type(current_methods_raw).__name__}.'
                    )
                    self.errors.append(msg)
                    continue
                known_methods_list: list[str] = [str(m) for m in current_methods_raw]

                # Прямое сравнение имён методов строками — простой «контракт по именованию»
                # для студенческой работы без разрешения перегрузок и variance сигнатур.
                for expected_method in expected_methods:
                    if expected_method not in known_methods_list:
                        self.errors.append(
                            f'Layer: {layer_name}\n'
                            f' Class {expected_name} does not contain'
                            f' expected method {expected_method}'
                        )

            mf_actual_raw = layer_bucket.get(MODULE_FUNCTIONS_BUCKET, {})
            mf_actual: dict[str, list[str]]
            mf_actual = mf_actual_raw if isinstance(mf_actual_raw, dict) else {}  # type: ignore[assignment]

            # Проверка FastAPI-хендлеров (и любых топ-уровневых публичных def/async def).
            for mf in layer_data.get('required_module_functions', []):
                rel_path_yaml = mf.get('relative_path', '')
                rel_key = normalize_rel_path(str(rel_path_yaml))
                expected_fns_callables = mf.get('functions', [])

                actual_fns_scan = mf_actual.get(rel_key)
                if actual_fns_scan is None:
                    self.errors.append(
                        f'Layer: {layer_name}\n Module file {rel_key!r} was not scanned for functions '
                        '(нет файла после фильтрации или расположение вне KNOWN_LAYER_NAMES — см. infer_layer()).'
                    )
                    continue

                for expected_fn in expected_fns_callables:
                    if expected_fn not in actual_fns_scan:
                        self.errors.append(
                            f'Layer: {layer_name}\n File {rel_key!r} does not expose expected'
                            f' top-level callable {expected_fn!r}'
                        )

        return self.errors


SYNTHETIC_SPEC_YAML_DEMO = """
meta:
  example: pedagogical_mini_contract
feature: demo_context
layers:
  domain:
    required_classes:
      - name: UserDomainModel
        methods:
          - validate
  service_layer:
    required_classes:
      - name: UserApplicationService
        methods:
          - create_user
          - delete_user
"""

SYNTHETIC_INLINE_SOURCES_DEMO = {
    'domain/models.py': '''
class UserDomainModel:
    def validate(self):
        """Публичный метод контрактного слоя домена."""
''',
    'service_layer/application.py': '''
class UserApplicationService:
    def create_user(self): ...
    def delete_user(self): ...
''',
}


def parse_cli(argv: list[str]) -> argparse.Namespace:
    """Парсинг аргументов CLI после опциональной вставки корня импортов как у генератора спек."""
    repo_default = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description=(
            'RDE lint: загрузить YAML-контракт bounded context '
            '(например specs/storage.yaml) и сравнить с кодом каталога openvair/modules/<feature>.'
        )
    )
    parser.add_argument(
        'spec_yaml',
        type=Path,
        nargs='?',
        default=repo_default / 'specs' / 'storage.yaml',
        help='YAML с секцией layers (default: specs/storage.yaml относительно репозитория)',
    )
    parser.add_argument(
        'module_dir',
        type=Path,
        nargs='?',
        default=repo_default / 'openvair' / 'modules' / 'storage',
        help='Директория bounded context (default: openvair/modules/storage)',
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Не читает диск: прогоняет встроенный учебный микроконтракт синтетическими строками исходника.',
    )
    return parser.parse_args(argv)


def load_spec(path: Path) -> dict:
    """Безопасный yaml.safe_load любого указанного пути пользователем."""
    blob = path.read_text(encoding='utf-8')
    return yaml.safe_load(blob)


def run_on_openvair_module(spec_yaml: Path, module_dir: Path) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Основной сценарий защиты: реальный файл спеки против реальных исходников."""
    reqs = load_spec(spec_yaml)
    analyzer = AstAnalyzer.from_bounded_context_dir(module_dir)
    artifacts = analyzer.extract()
    errs = Comparator(reqs, artifacts).compare()
    return artifacts, errs


def run_demo_pipeline() -> list[str]:
    """Минимальный end-to-end демосценарий без зависимостей от деревьев OpenVAir на диске."""
    reqs = yaml.safe_load(SYNTHETIC_SPEC_YAML_DEMO)
    arts = AstAnalyzer(SYNTHETIC_INLINE_SOURCES_DEMO).extract()
    return Comparator(reqs, arts).compare()


if __name__ == '__main__':
    _opts = parse_cli(sys.argv[1:])

    if _opts.demo:
        _errs = run_demo_pipeline()
    else:
        _errs = run_on_openvair_module(_opts.spec_yaml.resolve(), _opts.module_dir.resolve())[1]

    if _errs:
        print('[RDE-LINTER] SPECS MISMATCH FOUND:')  # noqa: T201
        for err in _errs:
            print(f' - {err}')  # noqa: T201
        sys.exit(1)
    else:
        print('[RDE-LINTER] Specs are fulfilled — no mismatches found.')  # noqa: T201
        sys.exit(0)
