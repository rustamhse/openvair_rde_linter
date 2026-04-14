"""Comparison logic engine that verifies requirements and implementation"""

from typing import Any, Dict, List

from openvair.requirements_linter.models import RDESpecification


class Comparator:
    """Comparison Engine.

    It validates the extracted DDD code state against the formal Specification
    and also the existence of required classes, methods, and architectural
    boundaries across Domain, Service, Adapters, and Entrypoints layers.
    """

    def __init__(
        self, requirements: RDESpecification, code_state: Dict[str, Any]
    ):
        """Initialization of comparator"""
        self.requirements = requirements
        self.code_state = code_state
        self.report: List[str] = []

    def compare(self) -> List[str]:
        """Executes all layer comparisons."""
        self._compare_domain_layer()
        self._compare_service_layer()
        self._compare_adapters_layer()
        self._compare_entrypoints_layer()
        return self.report

    def _check_class_existence(
        self,
        required_classes: List[Any],
        actual_classes: List[Dict[str, Any]],
        layer_name: str,
        entity_type: str,
    ) -> None:
        """Helper method to check if specified classes exist in the code."""
        actual_names = {c['name'] for c in actual_classes}
        for req_class in required_classes:
            if req_class.name not in actual_names:
                self.report.append(
                    f"[DDD Violation] {layer_name}: {entity_type} '{req_class.name}' "  # noqa: E501
                    f'is required by specification but not found in the code.'
                )

    def _compare_domain_layer(self) -> None:
        """Validates Domain Models and Domain Managers."""
        if not self.requirements.domain_layer:
            return

        actual_domain = self.code_state.get('domain_layer', {})
        req_domain = self.requirements.domain_layer

        self._check_class_existence(
            req_domain.models,
            actual_domain.get('models', []),
            'Domain Layer',
            'Model',
        )
        self._check_class_existence(
            req_domain.managers,
            actual_domain.get('managers', []),
            'Domain Layer',
            'Manager',
        )

    def _compare_service_layer(self) -> None:
        """Validates Service Layer Managers and Services."""
        if not self.requirements.service_layer:
            return

        actual_service = self.code_state.get('service_layer', {})
        req_service = self.requirements.service_layer

        self._check_class_existence(
            req_service.managers,
            actual_service.get('managers', []),
            'Service Layer',
            'Manager',
        )
        self._check_class_existence(
            req_service.services,
            actual_service.get('services', []),
            'Service Layer',
            'Service/UseCase',
        )

    def _compare_adapters_layer(self) -> None:
        """Validates ORM Models, Repositories, and Serializers."""
        if not self.requirements.adapters_layer:
            return

        actual_adapters = self.code_state.get('adapters_layer', {})
        req_adapters = self.requirements.adapters_layer

        self._check_class_existence(
            req_adapters.orm_models,
            actual_adapters.get('orm_models', []),
            'Adapters Layer',
            'ORM Model',
        )
        self._check_class_existence(
            req_adapters.serializers,
            actual_adapters.get('serializers', []),
            'Adapters Layer',
            'Serializer',
        )
        self._check_class_existence(
            req_adapters.external,
            actual_adapters.get('external', []),
            'Adapters Layer',
            'External Adapter',
        )

        # Special check for Repositories (Abstract + Concrete)
        actual_repos = {
            c['name'] for c in actual_adapters.get('repositories', [])
        }
        for req_repo in req_adapters.repositories:
            if req_repo.abstract not in actual_repos:
                self.report.append(
                    f"[DDD Violation] Adapters Layer: Abstract Repository '{req_repo.abstract}' not found."  # noqa: E501
                )
            if req_repo.concrete not in actual_repos:
                self.report.append(
                    f"[DDD Violation] Adapters Layer: Concrete Repository '{req_repo.concrete}' not found."  # noqa: E501
                )

    def _compare_entrypoints_layer(self) -> None:  # noqa: C901
        """Validates DTO Schemas, CRUD adapters, and REST Endpoints."""
        if not self.requirements.entrypoints_layer:
            return

        actual_entrypoints = self.code_state.get('entrypoints_layer', {})
        req_entrypoints = self.requirements.entrypoints_layer

        # 1. Check Schemas
        self._check_class_existence(
            req_entrypoints.schemas,
            actual_entrypoints.get('schemas', []),
            'Entrypoints Layer',
            'Schema',
        )

        # 2. Check CRUD Adapters and their methods
        actual_cruds = {
            c['name']: c for c in actual_entrypoints.get('crud_adapters', [])
        }
        for req_crud in req_entrypoints.crud_adapters:
            if req_crud.name not in actual_cruds:
                self.report.append(
                    f"[DDD Violation] Entrypoints Layer: CRUD Adapter '{req_crud.name}' not found."  # noqa: E501
                )
                continue

            actual_methods = actual_cruds[req_crud.name].get('methods', [])
            for required_method in req_crud.methods:
                if required_method not in actual_methods:
                    self.report.append(
                        f"[DDD Violation] Entrypoints Layer: Method '{required_method}()' "  # noqa: E501
                        f"is missing in CRUD Adapter '{req_crud.name}'."
                    )

        # 3. Check API Endpoints
        actual_endpoints = {
            f'{e["method"]} {e["path"]}'
            for e in actual_entrypoints.get('endpoints', [])
        }
        for req_endpoint in req_entrypoints.endpoints:
            endpoint_key = f'{req_endpoint.method.upper()} {req_endpoint.path}'
            if endpoint_key not in actual_endpoints:
                self.report.append(
                    f"[DDD Violation] Entrypoints Layer: REST Endpoint '{endpoint_key}' "  # noqa: E501
                    f'is required but not implemented in the routers.'
                )
