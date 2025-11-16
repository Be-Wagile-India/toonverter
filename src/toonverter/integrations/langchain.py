"""LangChain integration."""

from typing import Any, Optional

from ..core.exceptions import ConversionError
from ..core.types import DecodeOptions, EncodeOptions
from ..decoders import decode
from ..encoders import encode

# Optional dependency
try:
    from langchain.schema import Document

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Document = Any  # type: ignore


def langchain_to_toon(
    document: "Document", options: Optional[EncodeOptions] = None
) -> str:
    """Convert LangChain Document to TOON format.

    Args:
        document: LangChain Document instance
        options: Encoding options

    Returns:
        TOON format string

    Raises:
        ImportError: If langchain is not installed
        ConversionError: If conversion fails

    Examples:
        >>> from langchain.schema import Document
        >>> doc = Document(page_content="Hello", metadata={"source": "test.txt"})
        >>> toon_str = langchain_to_toon(doc)
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "langchain is required. Install with: pip install toon-converter[integrations]"
        )

    try:
        data = {"page_content": document.page_content, "metadata": document.metadata}
        return encode(data, options)
    except Exception as e:
        raise ConversionError(f"Failed to convert LangChain Document to TOON: {e}") from e


def toon_to_langchain(
    toon_str: str, options: Optional[DecodeOptions] = None
) -> "Document":
    """Convert TOON format to LangChain Document.

    Args:
        toon_str: TOON format string
        options: Decoding options

    Returns:
        LangChain Document instance

    Raises:
        ImportError: If langchain is not installed
        ConversionError: If conversion fails

    Examples:
        >>> toon_str = "{page_content:Hello,metadata:{source:test.txt}}"
        >>> doc = toon_to_langchain(toon_str)
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "langchain is required. Install with: pip install toon-converter[integrations]"
        )

    try:
        data = decode(toon_str, options)
        if isinstance(data, dict):
            page_content = data.get("page_content", "")
            metadata = data.get("metadata", {})
            return Document(page_content=page_content, metadata=metadata)
        else:
            raise ConversionError("TOON data must be a dictionary with page_content and metadata")
    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to LangChain Document: {e}") from e
