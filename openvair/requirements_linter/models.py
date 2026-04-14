"""Pydantic models for requirements"""

from typing import List, Optional

from pydantic import Field, BaseModel

# --- Base Abstractions ---


class MethodSpec(BaseModel):
    """Represents a specification for a specific method within a class."""

    name: str


class ClassSpec(BaseModel):
    """Base specification for an architectural class entity."""

    name: str
    description: str = ''


class ClassWithMethodsSpec(ClassSpec):
    """Specification for a class that includes a list of required methods."""

    methods: List[str] = []


# --- Entrypoints Layer ---


class SchemaSpec(ClassSpec):
    """Specification for a Data Transfer Object (DTO) schema."""

    type: str


class EndpointSpec(BaseModel):
    """Specification for a REST API endpoint."""

    path: str
    method: str
    description: str = ''
    statuses: List[int] = []


class EntrypointsLayerSpec(BaseModel):
    """Specification for the Entrypoints layer."""

    schemas: List[SchemaSpec] = []
    crud_adapters: List[ClassWithMethodsSpec] = []
    endpoints: List[EndpointSpec] = []


# --- Domain Layer ---


class DomainLayerSpec(BaseModel):
    """Specification for the Domain layer."""

    models: List[ClassSpec] = []
    managers: List[ClassSpec] = []


# --- Service Layer ---


class ServiceLayerSpec(BaseModel):
    """Specification for the Service layer."""

    managers: List[ClassSpec] = []
    services: List[ClassSpec] = []


# --- Adapters Layer ---


class RepositorySpec(BaseModel):
    """Specification for the Repository pattern."""

    abstract: str
    concrete: str


class AdaptersLayerSpec(BaseModel):
    """Specification for the Adapters layer."""

    orm_models: List[ClassSpec] = []
    repositories: List[RepositorySpec] = []
    serializers: List[ClassSpec] = []
    external: List[ClassSpec] = []


# --- Main Document ---


class RDESpecification(BaseModel):
    """The root document representing the complete specification.

    Defines the expected architectural state for a specific feature across
    all Domain-Driven Design (DDD) layers.
    Used by the linter to verify source code compliance.
    """

    feature: str
    description: str = ''

    domain_layer: Optional[DomainLayerSpec] = Field(
        default_factory=DomainLayerSpec
    )
    service_layer: Optional[ServiceLayerSpec] = Field(
        default_factory=ServiceLayerSpec
    )
    adapters_layer: Optional[AdaptersLayerSpec] = Field(
        default_factory=AdaptersLayerSpec
    )
    entrypoints_layer: Optional[EntrypointsLayerSpec] = Field(
        default_factory=EntrypointsLayerSpec
    )
