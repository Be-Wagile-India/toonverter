"""Schema engine for automatic inference and validation.

This module provides tools to:
1. Infer schema from data instances (learn structure).
2. Validate data against learned schemas.
3. Generate schema definitions compatible with TOON optimization.
"""

from .inferrer import SchemaInferrer
from .models import SchemaField, SchemaType
from .validator import SchemaValidator, ValidationError


__all__ = [
    "SchemaInferrer",
    "SchemaField",
    "SchemaType",
    "SchemaValidator",
    "ValidationError",
]
