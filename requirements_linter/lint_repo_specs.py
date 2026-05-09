"""Lint each ``specs/*.yaml`` against ``openvair/modules/<feature>``.

Run from the repository root (pre-commit entry).
"""

from __future__ import annotations

import sys
from pathlib import Path

_PRE_BOOT = Path(__file__).resolve().parent.parent
if str(_PRE_BOOT) not in sys.path:
    sys.path.insert(0, str(_PRE_BOOT))

import yaml  # noqa: E402

from requirements_linter.cli import run_on_openvair_module  # noqa: E402
from requirements_linter._paths import REPO_ROOT  # noqa: E402


def module_dir_for_spec(repo_root: Path, yaml_path: Path, doc: dict) -> Path:
    """Resolve ``openvair/modules/<feature>`` for one spec file."""
    feat = doc.get('feature')
    if isinstance(feat, str) and feat.strip():
        return repo_root / 'openvair' / 'modules' / feat.strip()
    return repo_root / 'openvair' / 'modules' / yaml_path.stem


def _rel_module_posix(root: Path, mod: Path) -> str:
    """Best-effort posix path of ``mod`` relative to ``root``."""
    if not mod.is_dir():
        return mod.as_posix()
    return mod.resolve().relative_to(root.resolve()).as_posix()


def _lint_one_yaml(root: Path, yml: Path) -> int:
    """Lint a single spec file; return ``1`` if failed, else ``0``."""
    doc = yaml.safe_load(yml.read_text(encoding='utf-8')) or {}
    mod = module_dir_for_spec(root, yml, doc)
    rel_mod = _rel_module_posix(root, mod)

    if not mod.is_dir():
        tag = '[RDE-LINTER]'
        msg = (
            f'{tag} {yml.name}: skip — bounded context directory missing '
            f'({rel_mod})'
        )
        print(msg, file=sys.stderr)  # noqa: T201
        return 1

    feature = doc.get('feature', yml.stem)
    _, errs = run_on_openvair_module(yml.resolve(), mod.resolve())

    if errs:
        head = f'[RDE-LINTER] {yml.name} (feature={feature!r})'
        print(f'{head} SPECS MISMATCH FOUND:')  # noqa: T201
        for err in errs:
            print(f' - {err}')  # noqa: T201
        return 1

    print(f'[RDE-LINTER] OK {yml.name} (feature={feature!r})')  # noqa: T201
    return 0


def lint_all_specs(repo_root: Path | None = None) -> int:
    """Lint every ``*.yaml`` in ``specs/``; ``0`` when all pass."""
    root = repo_root or REPO_ROOT
    specs_dir = root / 'specs'
    if not specs_dir.is_dir():
        print(  # noqa: T201
            f'[RDE-LINTER] Specs directory not found: {specs_dir}',
            file=sys.stderr,
        )
        return 0

    exit_code = 0
    for yml in sorted(specs_dir.glob('*.yaml')):
        if _lint_one_yaml(root, yml):
            exit_code = 1
    return exit_code


if __name__ == '__main__':
    raise SystemExit(lint_all_specs())
