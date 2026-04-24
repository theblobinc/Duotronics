"""Registry surfaces (Witness Contract App R + DPFC App H Registries).

Each registry is loaded from a single source-of-truth YAML fixture in
`fixtures/` and exposed through a stable Python API so both the
reference implementation and any external impl can resolve the same
versioned identities.
"""

from .schema import SchemaRegistry, SCHEMA_REGISTRY
from .family import FamilyRegistry, FAMILY_REGISTRY
from .geometry import GeometryRegistry, GEOMETRY_REGISTRY
from .transport import TransportRegistry, TRANSPORT_REGISTRY
from .normalizer import NormalizerRegistry, NORMALIZER_REGISTRY
from .retention import RetentionRegistry, RETENTION_REGISTRY
from .policy import PolicyRegistry, POLICY_REGISTRY
from .migration import MigrationRegistry, MIGRATION_REGISTRY

__all__ = [
    "SchemaRegistry",
    "SCHEMA_REGISTRY",
    "FamilyRegistry",
    "FAMILY_REGISTRY",
    "GeometryRegistry",
    "GEOMETRY_REGISTRY",
    "TransportRegistry",
    "TRANSPORT_REGISTRY",
    "NormalizerRegistry",
    "NORMALIZER_REGISTRY",
    "RetentionRegistry",
    "RETENTION_REGISTRY",
    "PolicyRegistry",
    "POLICY_REGISTRY",
    "MigrationRegistry",
    "MIGRATION_REGISTRY",
]
