"""Command line interface to operate the linter."""

import re
import sys
import logging
import argparse
from pathlib import Path

import yaml

from openvair.requirements_linter.models import RDESpecification
from openvair.requirements_linter.parser import parse_source_code
from openvair.requirements_linter.comparator import Comparator

# Setup basic logging for CLI output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def load_requirements(spec_path: str) -> RDESpecification:
    """Loads and parses the specification from a Markdown or YAML file."""
    target_path = Path(spec_path)
    if not target_path.exists():
        logger.error(f'[ERROR] Specification file {spec_path} not found.')
        sys.exit(1)

    try:
        with target_path.open('r', encoding='utf-8') as f:
            content = f.read()

        if target_path.suffix.lower() == '.md':
            match = re.search(
                r'```yaml\s*rde-spec\n(.*?)\n```', content, re.DOTALL
            )
            if not match:
                logger.error(
                    f'[ERROR] No RDE-block (```yaml rde-spec) '
                    f'found in {spec_path}'
                )
                sys.exit(1)
            yaml_content = match.group(1)
            data = yaml.safe_load(yaml_content)
        else:
            data = yaml.safe_load(content)

        return RDESpecification(**data)

    except Exception as e:  # noqa: BLE001
        logger.error(f'[ERROR] Failed to parse specification: {e}')
        sys.exit(1)


def scan_directory(target_dir: str) -> dict:
    """Recursively scans dir and merges AST data into a global DDD state."""
    global_state = {
        'domain_layer': {'models': [], 'managers': []},
        'service_layer': {'managers': [], 'services': []},
        'adapters_layer': {
            'orm_models': [],
            'repositories': [],
            'serializers': [],
            'external': [],
        },
        'entrypoints_layer': {
            'schemas': [],
            'crud_adapters': [],
            'endpoints': [],
        },
    }

    target_path = Path(target_dir)
    if not target_path.exists() or not target_path.is_dir():
        logger.error(f'[ERROR] Target directory {target_dir} not found.')
        sys.exit(1)

    for py_file in target_path.rglob('*.py'):
        try:
            with py_file.open('r', encoding='utf-8') as f:
                source_text = f.read()

            # Pass the filepath to the parser for DDD categorization
            file_state = parse_source_code(source_text, filepath=str(py_file))

            # Merge Domain
            global_state['domain_layer']['models'].extend(
                file_state['domain_layer']['models']
            )
            global_state['domain_layer']['managers'].extend(
                file_state['domain_layer']['managers']
            )
            # Merge Service
            global_state['service_layer']['managers'].extend(
                file_state['service_layer']['managers']
            )
            global_state['service_layer']['services'].extend(
                file_state['service_layer']['services']
            )
            # Merge Adapters
            global_state['adapters_layer']['orm_models'].extend(
                file_state['adapters_layer']['orm_models']
            )
            global_state['adapters_layer']['repositories'].extend(
                file_state['adapters_layer']['repositories']
            )
            global_state['adapters_layer']['serializers'].extend(
                file_state['adapters_layer']['serializers']
            )
            global_state['adapters_layer']['external'].extend(
                file_state['adapters_layer']['external']
            )
            # Merge Entrypoints
            global_state['entrypoints_layer']['schemas'].extend(
                file_state['entrypoints_layer']['schemas']
            )
            global_state['entrypoints_layer']['crud_adapters'].extend(
                file_state['entrypoints_layer']['crud_adapters']
            )
            global_state['entrypoints_layer']['endpoints'].extend(
                file_state['entrypoints_layer']['endpoints']
            )

        except Exception as e:  # noqa: BLE001
            logger.warning(f'[WARNING] Error reading file {py_file}: {e}')

    return global_state


def main() -> None:
    """Execute the main flow of the RDE DDD Linter."""
    parser = argparse.ArgumentParser(
        description='DDD Requirements Linter for Open vAIR'
    )
    parser.add_argument(
        '--spec',
        required=True,
        help='Path to the .md or .yml specification file',
    )
    parser.add_argument(
        '--target',
        required=True,
        help="Path to the module's source code directory",
    )
    args = parser.parse_args()

    logger.info(f'=== STAGE 1: Loading specification from {args.spec} ===')
    requirements = load_requirements(args.spec)
    logger.info(f"[OK] Specification for '{requirements.feature}' loaded.\n")

    logger.info(f'=== STAGE 2: Static Code Analysis in {args.target} ===')
    code_state = scan_directory(args.target)

    domain_cnt = sum(len(v) for v in code_state['domain_layer'].values())
    service_cnt = sum(len(v) for v in code_state['service_layer'].values())
    adapters_cnt = sum(len(v) for v in code_state['adapters_layer'].values())
    entry_cnt = sum(len(v) for v in code_state['entrypoints_layer'].values())

    logger.info('[OK] DDD Reality Snapshot collected:')
    logger.info(f'  - Domain Layer:      {domain_cnt} entities')
    logger.info(f'  - Service Layer:     {service_cnt} entities')
    logger.info(f'  - Adapters Layer:    {adapters_cnt} entities')
    logger.info(f'  - Entrypoints Layer: {entry_cnt} entities\n')

    logger.info('=== STAGE 3: Verification (Comparison Engine) ===')
    comparator = Comparator(requirements, code_state)
    report = comparator.compare()

    logger.info('\n==================================================')
    logger.info('           [ DESYNCHRONIZATION REPORT ]           ')
    logger.info('==================================================')

    if not report:
        logger.info(
            '✅ Perfect match! No architectural boundary violations found.'
        )
        sys.exit(0)
    else:
        for error in report:
            logger.error(f'❌ {error}')
        logger.info('--------------------------------------------------')
        logger.error('STATUS: Contract violations detected.')
        logger.info('==================================================')
        sys.exit(1)


if __name__ == '__main__':
    main()
