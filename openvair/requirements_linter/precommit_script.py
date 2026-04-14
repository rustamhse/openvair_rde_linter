"""Pre-commit hook wrapper for RDE DDD Linter.

This script automatically maps specification files in docs/reference/modules/
to their respective source code directories in openvair/modules/ and runs
the architectural synchronization check.
"""

import sys
import logging
import subprocess
from pathlib import Path

# Настраиваем базовый логгер для вывода сообщений в консоль
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_linter() -> None:  # noqa: C901
    """Finds all specs and runs the linter against corresponding modules.

    Exits with code 1 if any desynchronization is detected.
    """
    docs_base_path = Path('docs/reference/modules')
    modules_base_path = Path('openvair/modules')
    error_found = False

    # Find all .md files in the specific documentation directory
    spec_files = list(docs_base_path.rglob('*.md'))

    if not spec_files:
        logger.info('[RDE] No specification files found. Skipping check.')
        return

    for spec_path in spec_files:
        # Extract module name from path
        # (e.g., 'scheduler' from '.../modules/scheduler/spec.md')
        module_name = spec_path.parent.name
        target_path = modules_base_path / module_name

        if not target_path.exists():
            logger.warning(
                f'[RDE] Warning: Target module directory {target_path}',
                f'not found for {spec_path}',
            )
            continue

        logger.info(f'[RDE] Checking synchronization: {module_name}...')

        # Run the linter as a module
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                '-m',
                'openvair.requirements_linter.cli',
                '--spec',
                str(spec_path),
                '--target',
                str(target_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            logger.error(result.stdout)
            logger.error(result.stderr)
            error_found = True
        else:
            logger.info(f'[RDE] {module_name}: OK')

    if error_found:
        msg = '\n[RDE Error] Architectural desynchronization detected. Commit blocked.'  # noqa: E501
        logger.error(msg)
        sys.exit(1)


if __name__ == '__main__':
    run_linter()
