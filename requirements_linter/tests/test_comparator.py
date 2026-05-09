"""Unit tests for ``Comparator`` YAML vs code mismatches."""

from __future__ import annotations

import yaml

from requirements_linter.analyzer import AstAnalyzer
from requirements_linter.ast_specs import MODULE_FUNCTIONS_BUCKET
from requirements_linter.comparator import Comparator

SOURCES_OK = {
    'domain/models.py': '''
class UserDomainModel:
    def validate(self): ...
''',
}


def test_missing_class_error() -> None:
    """Missing class produces one descriptive error."""
    reqs = yaml.safe_load(
        """
layers:
  domain:
    required_classes:
      - name: MissingClass
        methods: []
"""
    )
    arts = AstAnalyzer(SOURCES_OK).extract()
    errs = Comparator(reqs, arts).compare()
    assert len(errs) == 1
    assert 'MissingClass not found in code artifacts' in errs[0]


def test_missing_method_error() -> None:
    """Missing method on an existing class is reported."""
    reqs = yaml.safe_load(
        """
layers:
  domain:
    required_classes:
      - name: UserDomainModel
        methods:
          - phantom_method
"""
    )
    arts = AstAnalyzer(SOURCES_OK).extract()
    errs = Comparator(reqs, arts).compare()
    assert len(errs) == 1
    assert 'phantom_method' in errs[0]


def test_sentinel_class_name_rejected() -> None:
    """YAML must not reuse internal sentinel bucket names as classes."""
    reqs = yaml.safe_load(
        f"""
layers:
  domain:
    required_classes:
      - name: {MODULE_FUNCTIONS_BUCKET}
        methods: []
"""
    )
    arts = AstAnalyzer(SOURCES_OK).extract()
    errs = Comparator(reqs, arts).compare()
    assert len(errs) == 1
    assert 'disallowed class name' in errs[0]


def test_missing_module_functions_file_error() -> None:
    """Required module_functions path absent from disk triggers error."""
    reqs = yaml.safe_load(
        """
layers:
  entrypoints:
    required_classes: []
    required_module_functions:
      - relative_path: entrypoints/ghost.py
        functions:
          - foo
"""
    )
    snippet = {'entrypoints/api.py': 'async def bar():\n    pass\n'}
    arts = AstAnalyzer(snippet).extract()
    errs = Comparator(reqs, arts).compare()
    assert len(errs) == 1
    assert 'ghost.py' in errs[0]


def test_missing_top_level_callable_error() -> None:
    """Missing callable name in scanned file yields one error."""
    reqs = yaml.safe_load(
        """
layers:
  entrypoints:
    required_classes: []
    required_module_functions:
      - relative_path: entrypoints/api.py
        functions:
          - expected_fn_missing
"""
    )
    snippet = {'entrypoints/api.py': 'async def real_handler():\n    pass\n'}
    arts = AstAnalyzer(snippet).extract()
    errs = Comparator(reqs, arts).compare()
    assert len(errs) == 1
    assert 'expected_fn_missing' in errs[0]
