"""Abstract syntax tree node visitor that gathers code artifacts"""

import ast
from typing import Any, Dict, List


class DDDParser(ast.NodeVisitor):
    """Advanced AST NodeVisitor that categorizes extracted entities into DDD layers."""  # noqa: E501

    def __init__(self, filepath: str):
        """Initializes the parser for a specific file.

        Args:
            filepath (str): The absolute or relative path to the Python file.
        """
        super().__init__()
        self.filepath = filepath
        self.normalized_path = filepath.replace('\\', '/')

        # --- Entrypoints Layer ---
        self.schemas: List[Dict[str, Any]] = []
        self.crud_adapters: List[Dict[str, Any]] = []
        self.endpoints: List[Dict[str, Any]] = []

        # --- Domain Layer ---
        self.domain_models: List[Dict[str, Any]] = []
        self.domain_managers: List[Dict[str, Any]] = []

        # --- Service Layer ---
        self.service_managers: List[Dict[str, Any]] = []
        self.services: List[Dict[str, Any]] = []

        # --- Adapters Layer ---
        self.orm_models: List[Dict[str, Any]] = []
        self.repositories: List[Dict[str, Any]] = []
        self.serializers: List[Dict[str, Any]] = []
        self.external_adapters: List[Dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: C901, PLR0912
        """Extracts and categorizes classes."""
        name = node.name
        base_classes = [
            base.id for base in node.bases if isinstance(base, ast.Name)
        ]
        methods = [
            n.name
            for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith('__')
        ]

        # ==========================================
        # 1. ENTRYPOINTS LAYER
        # ==========================================
        if '/entrypoints/' in self.normalized_path:
            known_schema_bases = {
                'BaseModel',
                'APIConfigRequestModel',
                'APIConfigResponseModel',
            }
            if any(b in known_schema_bases for b in base_classes):
                self.schemas.append({'name': name, 'filepath': self.filepath})
            elif name.lower().endswith('crud'):
                self.crud_adapters.append(
                    {
                        'name': name,
                        'methods': methods,
                        'filepath': self.filepath,
                    }
                )

        # ==========================================
        # 2. DOMAIN LAYER
        # ==========================================
        elif '/domain/' in self.normalized_path:
            if name.lower().endswith('manager'):
                self.domain_managers.append(
                    {'name': name, 'filepath': self.filepath}
                )
            elif not name.lower().endswith('exception'):
                self.domain_models.append(
                    {'name': name, 'filepath': self.filepath}
                )

        # ==========================================
        # 3. SERVICE LAYER
        # ==========================================
        elif '/service_layer/' in self.normalized_path:
            if name.lower().endswith('manager'):
                self.service_managers.append(
                    {'name': name, 'filepath': self.filepath}
                )
            elif not name.lower().endswith('exception'):
                self.services.append({'name': name, 'filepath': self.filepath})

        # ==========================================
        # 4. ADAPTERS LAYER (Слой адаптеров)
        # ==========================================
        elif '/adapters/' in self.normalized_path:
            if 'orm' in self.normalized_path or 'Base' in base_classes:
                self.orm_models.append(
                    {'name': name, 'filepath': self.filepath}
                )
            elif 'repository' in name.lower():
                self.repositories.append(
                    {'name': name, 'filepath': self.filepath}
                )
            elif 'serializer' in name.lower():
                self.serializers.append(
                    {'name': name, 'filepath': self.filepath}
                )
            elif not name.lower().endswith('exception'):
                self.external_adapters.append(
                    {'name': name, 'filepath': self.filepath}
                )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Parses sync functions."""
        if (
            '/service_layer/' in self.normalized_path
            and 'services' in self.normalized_path
        ):
            self.services.append({'name': node.name, 'filepath': self.filepath})

        self._parse_endpoint(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Parses async functions."""
        if (
            '/service_layer/' in self.normalized_path
            and 'services' in self.normalized_path
        ):
            self.services.append({'name': node.name, 'filepath': self.filepath})

        self._parse_endpoint(node)
        self.generic_visit(node)

    def _parse_endpoint(self, node: ast.AST) -> None:  # noqa: C901
        """Extracts FastAPI routes. Only applies to the entrypoints layer."""
        if '/entrypoints/' not in self.normalized_path:
            return

        for decorator in getattr(node, 'decorator_list', []):
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
            ):
                base_name = decorator.func.value.id
                if base_name in ['router', 'app']:
                    endpoint_method = decorator.func.attr.upper()
                    endpoint_path = None

                    if decorator.args and isinstance(
                        decorator.args[0], ast.Constant
                    ):
                        endpoint_path = decorator.args[0].value

                    if endpoint_path and endpoint_method:
                        self.endpoints.append(
                            {
                                'path': endpoint_path,
                                'method': endpoint_method,
                                'filepath': self.filepath,
                            }
                        )


def parse_source_code(source_text: str, filepath: str) -> dict:
    """Entry point for the AST parsing mechanism.

    Args:
        source_text (str): The raw Python source code.
        filepath (str): The path to the file for DDD layer categorization.

    Returns:
        dict: A structured dictionary mapping extracted entities to DDD layers.
    """
    tree = ast.parse(source_text)
    parser = DDDParser(filepath=filepath)
    parser.visit(tree)

    return {
        'domain_layer': {
            'models': parser.domain_models,
            'managers': parser.domain_managers,
        },
        'service_layer': {
            'managers': parser.service_managers,
            'services': parser.services,
        },
        'adapters_layer': {
            'orm_models': parser.orm_models,
            'repositories': parser.repositories,
            'serializers': parser.serializers,
            'external': parser.external_adapters,
        },
        'entrypoints_layer': {
            'schemas': parser.schemas,
            'crud_adapters': parser.crud_adapters,
            'endpoints': parser.endpoints,
        },
    }
