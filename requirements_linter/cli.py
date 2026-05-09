"""CLI: arguments, YAML loading, and lint entrypoints."""

from __future__ import annotations

import sys
import argparse
from typing import Any, cast
from pathlib import Path

import yaml

from requirements_linter._paths import REPO_ROOT, ensure_repo_root_on_syspath

ensure_repo_root_on_syspath()

from requirements_linter.analyzer import AstAnalyzer  # noqa: E402
from requirements_linter.comparator import Comparator  # noqa: E402

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
        """Public domain-layer contract method."""
''',
    'service_layer/application.py': '''
class UserApplicationService:
    def create_user(self): ...
    def delete_user(self): ...
''',
}


def parse_cli(argv: list[str]) -> argparse.Namespace:
    """Define and parse linter CLI ``argv``."""
    parser = argparse.ArgumentParser(
        description=(
            'RDE lint: load YAML contract (e.g. specs/storage.yaml) '
            'and compare against openvair/modules/<feature>.'
        )
    )
    parser.add_argument(
        'spec_yaml',
        type=Path,
        nargs='?',
        default=REPO_ROOT / 'specs' / 'storage.yaml',
        help=(
            'YAML layers contract (default: specs/storage.yaml under repo root)'
        ),
    )
    parser.add_argument(
        'module_dir',
        type=Path,
        nargs='?',
        default=REPO_ROOT / 'openvair' / 'modules' / 'storage',
        help='Bounded context root (default: openvair/modules/storage)',
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='In-memory demo contract; no disk reads.',
    )
    return parser.parse_args(argv)


def load_spec(path: Path) -> dict[str, Any]:
    """Load YAML from ``path`` with UTF-8 text."""
    blob = path.read_text(encoding='utf-8')
    return cast('dict[str, Any]', yaml.safe_load(blob))


def run_on_openvair_module(
    spec_yaml: Path,
    module_dir: Path,
) -> tuple[dict[str, dict[str, object]], list[str]]:
    """Load ``spec_yaml`` and diff it against Python under ``module_dir``."""
    reqs = load_spec(spec_yaml)
    analyzer = AstAnalyzer.from_bounded_context_dir(module_dir)
    artifacts = analyzer.extract()
    errs = Comparator(reqs, artifacts).compare()
    return artifacts, errs


def run_demo_pipeline() -> list[str]:
    """Run Comparator on the built-in pedagogical YAML and sources."""
    reqs = yaml.safe_load(SYNTHETIC_SPEC_YAML_DEMO)
    arts = AstAnalyzer(SYNTHETIC_INLINE_SOURCES_DEMO).extract()
    return Comparator(reqs, arts).compare()


def main(argv: list[str] | None = None) -> int:
    """CLI entry: demo mode or filesystem spec vs module roots."""
    opts = parse_cli(argv if argv is not None else sys.argv[1:])

    if opts.demo:
        errs = run_demo_pipeline()
    else:
        spec_res = opts.spec_yaml.resolve()
        mod_res = opts.module_dir.resolve()
        errs = run_on_openvair_module(spec_res, mod_res)[1]

    if errs:
        print('[RDE-LINTER] SPECS MISMATCH FOUND:')  # noqa: T201
        for err in errs:
            print(f' - {err}')  # noqa: T201
        return 1
    print('[RDE-LINTER] Specs are fulfilled — no mismatches found.')  # noqa: T201
    return 0
