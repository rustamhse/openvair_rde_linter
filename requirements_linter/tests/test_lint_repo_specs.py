"""Tests for ``lint_repo_specs`` batch driver."""

from __future__ import annotations

from pathlib import Path

import yaml

from requirements_linter.cli import run_on_openvair_module
from requirements_linter.lint_repo_specs import (
    lint_all_specs,
    module_dir_for_spec,
)


def test_module_dir_for_spec_prefers_feature_key(tmp_path: Path) -> None:
    """``feature:`` in YAML wins over the file stem."""
    yml = tmp_path / 'storage.yaml'
    doc = yaml.safe_load('feature: custom_name\nlayers: {}\n')
    got = module_dir_for_spec(tmp_path, yml, doc)
    assert got == tmp_path / 'openvair' / 'modules' / 'custom_name'


def test_module_dir_fallback_to_stem(tmp_path: Path) -> None:
    """Without ``feature``, use ``<stem>`` as module folder name."""
    yml = tmp_path / 'user.yaml'
    got = module_dir_for_spec(tmp_path, yml, {})
    assert got == tmp_path / 'openvair' / 'modules' / 'user'


def test_lint_all_specs_mini_repo(tmp_path: Path) -> None:
    """Healthy tiny repo exits zero from ``lint_all_specs``."""
    specs = tmp_path / 'specs'
    specs.mkdir()
    feat = tmp_path / 'openvair' / 'modules' / 'tiny'
    (feat / 'domain').mkdir(parents=True)
    body = 'class Foo:\n    def bar(self):\n        pass\n'
    (feat / 'domain' / 'x.py').write_text(body, encoding='utf-8')
    layers = {
        'domain': {
            'required_classes': [{'name': 'Foo', 'methods': ['bar']}],
        },
    }
    doc = {'feature': 'tiny', 'layers': layers}
    dumped = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    (specs / 'tiny.yaml').write_text(dumped, encoding='utf-8')

    code = lint_all_specs(tmp_path)
    assert code == 0


def test_lint_all_specs_reports_mismatch(tmp_path: Path) -> None:
    """Stale spec vs code returns exit code ``1``."""
    specs = tmp_path / 'specs'
    specs.mkdir()
    feat = tmp_path / 'openvair' / 'modules' / 'bad'
    (feat / 'domain').mkdir(parents=True)
    py = 'class Foo:\n    def bar(self):\n        pass\n'
    (feat / 'domain' / 'x.py').write_text(py, encoding='utf-8')

    layers = {
        'domain': {
            'required_classes': [{'name': 'Foo', 'methods': ['nope']}],
        },
    }
    doc = {'feature': 'bad', 'layers': layers}
    dumped = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)
    (specs / 'bad.yaml').write_text(dumped, encoding='utf-8')

    assert lint_all_specs(tmp_path) == 1


def test_run_on_real_user_module_if_present() -> None:
    """Optional smoke test when the real ``user`` module exists."""
    repo = Path(__file__).resolve().parents[2]
    spec = repo / 'specs' / 'user.yaml'
    mod = repo / 'openvair' / 'modules' / 'user'
    if not spec.is_file() or not mod.is_dir():
        return
    _, errs = run_on_openvair_module(spec.resolve(), mod.resolve())
    assert errs == []
