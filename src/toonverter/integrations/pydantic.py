"""Pydantic model integration."""

from typing import Any, Optional, Type, TypeVar

from ..core.exceptions import ConversionError
from ..core.types import DecodeOptions, EncodeOptions
from ..decoders import decode
from ..encoders import encode

# Optional dependency
try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = Any  # type: ignore

T = TypeVar("T", bound="BaseModel")


def pydantic_to_toon(
    model: "BaseModel", options: Optional[EncodeOptions] = None
) -> str:
    """Convert Pydantic model to TOON format.

    Args:
        model: Pydantic BaseModel instance
        options: Encoding options

    Returns:
        TOON format string

    Raises:
        ImportError: If pydantic is not installed
        ConversionError: If conversion fails

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> user = User(name="Alice", age=30)
        >>> toon_str = pydantic_to_toon(user)
    """
    if not PYDANTIC_AVAILABLE:
        raise ImportError(
            "pydantic is required. Install with: pip install toon-converter[integrations]"
        )

    try:
        data = model.model_dump()
        return encode(data, options)
    except Exception as e:
        raise ConversionError(f"Failed to convert Pydantic model to TOON: {e}") from e


def toon_to_pydantic(
    toon_str: str, model_class: Type[T], options: Optional[DecodeOptions] = None
) -> T:
    """Convert TOON format to Pydantic model.

    Args:
        toon_str: TOON format string
        model_class: Pydantic model class
        options: Decoding options

    Returns:
        Pydantic model instance

    Raises:
        ImportError: If pydantic is not installed
        ConversionError: If conversion fails

    Examples:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> toon_str = "{name:Alice,age:30}"
        >>> user = toon_to_pydantic(toon_str, User)
    """
    if not PYDANTIC_AVAILABLE:
        raise ImportError(
            "pydantic is required. Install with: pip install toon-converter[integrations]"
        )

    try:
        data = decode(toon_str, options)
        return model_class(**data)
    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to Pydantic model: {e}") from e
