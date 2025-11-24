"""Pydantic model integration."""

from typing import Any, TypeVar

from toonverter.core.exceptions import ConversionError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.decoders import decode
from toonverter.encoders import encode


# Optional dependency
try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = Any  # type: ignore

T = TypeVar("T", bound="BaseModel")


def pydantic_to_toon(
    model: "BaseModel | list[BaseModel]", options: EncodeOptions | None = None
) -> str:
    """Convert Pydantic model or list of models to TOON format.

    Args:
        model: Pydantic BaseModel instance or list of instances
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
        msg = "pydantic is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        data = [m.model_dump() for m in model] if isinstance(model, list) else model.model_dump()
        return encode(data, options)  # type: ignore
    except Exception as e:
        msg = f"Failed to convert Pydantic model to TOON: {e}"
        raise ConversionError(msg) from e


def toon_to_pydantic(
    toon_str: str, model_class: type[T], options: DecodeOptions | None = None
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
        msg = "pydantic is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        data = decode(toon_str, options)  # type: ignore
        return model_class(**data)  # type: ignore
    except Exception as e:
        msg = f"Failed to convert TOON to Pydantic model: {e}"
        raise ConversionError(msg) from e
