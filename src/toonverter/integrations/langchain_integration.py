"""LangChain integration.

This module is resilient to multiple LangChain package layouts (langchain_core,
langchain.schema, langchain.docstore.document). It supports converting a single
Document or a list of Documents to TOON and back, and also provides optional
message/chat conversions (messages_to_toon / toon_to_messages) if LangChain
message classes are available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from toonverter.core.exceptions import ConversionError
from toonverter.core.spec import ToonDecodeOptions
from toonverter.decoders import decode
from toonverter.encoders import encode


# Attempt to detect Document class across various LangChain package layouts.
LANGCHAIN_AVAILABLE = False
LangchainDocument: type | None = None
try:
    # langchain_core (newer layout)
    from langchain_core.documents import Document as _Doc  # type: ignore

    LangchainDocument = _Doc
    LANGCHAIN_AVAILABLE = True
except Exception:
    try:
        # common schema export
        from langchain.schema import Document as _Doc  # type: ignore

        LangchainDocument = _Doc
        LANGCHAIN_AVAILABLE = True
    except Exception:
        try:
            # older classic layout
            from langchain.docstore.document import Document as _Doc  # type: ignore

            LangchainDocument = _Doc
            LANGCHAIN_AVAILABLE = True
        except Exception:
            LANGCHAIN_AVAILABLE = False

# Attempt to detect Message classes for chat conversion support
_LANGCHAIN_MESSAGE_CLASSES: dict[str, type] = {}
try:
    # Try modern schema message classes
    from langchain.schema import (
        AIMessage as _AIMessage,
    )
    from langchain.schema import (
        BaseMessage as _BaseMessage,
    )
    from langchain.schema import (
        HumanMessage as _HumanMessage,
    )
    from langchain.schema import (
        SystemMessage as _SystemMessage,
    )

    _LANGCHAIN_MESSAGE_CLASSES = {
        "human": _HumanMessage,
        "ai": _AIMessage,
        "system": _SystemMessage,
        "base": _BaseMessage,
    }
except Exception:
    try:
        # Older/simpler fallback: BaseMessage only
        from langchain.schema import BaseMessage as _BaseMessage  # type: ignore

        _LANGCHAIN_MESSAGE_CLASSES = {"base": _BaseMessage}
    except Exception:
        # No message classes available
        _LANGCHAIN_MESSAGE_CLASSES = {}

if TYPE_CHECKING:

    from toonverter.core.spec import ToonEncodeOptions, ToonValue
    from toonverter.core.types import DecodeOptions, EncodeOptions


def _doc_to_dict(doc: Any) -> dict[str, Any]:
    """Normalize a LangChain Document to a plain dict.

    Attempts to read common attributes used across different LangChain versions:
    - page_content (modern)
    - content / text (others)
    - metadata (dict-like)
    """
    # content / text
    page_content = getattr(doc, "page_content", None)
    if page_content is None:
        page_content = getattr(doc, "content", None)
    if page_content is None:
        page_content = getattr(doc, "text", None)

    # metadata
    metadata = getattr(doc, "metadata", None)
    if metadata is None:
        # some Document implementations may expose .meta
        metadata = getattr(doc, "meta", None)

    return {"page_content": page_content or "", "metadata": metadata or {}}


def _convert_decode_options(
    options: DecodeOptions | ToonDecodeOptions | None,
) -> ToonDecodeOptions | None:
    """Convert decode options to ToonDecodeOptions.

    Args:
        options: Decoding options

    Returns:
        ToonDecodeOptions if conversion is possible, otherwise None
    """
    if options is None:
        return None
    if isinstance(options, ToonDecodeOptions):
        return options
    # Must be DecodeOptions at this point
    return ToonDecodeOptions(
        strict=options.strict,  # type: ignore[attr-defined]
        type_inference=options.type_inference,  # type: ignore[attr-defined]
    )


def langchain_to_toon(document: Any, options: EncodeOptions | None = None) -> str:
    """Convert LangChain Document or list of Documents to TOON format.

    Args:
        document: LangChain Document instance or list of Documents
        options: Encoding options

    Returns:
        TOON format string

    Raises:
        ImportError: If langchain is not installed
        ConversionError: If conversion fails
    """
    if not LANGCHAIN_AVAILABLE:
        msg = "langchain is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        # Handle list of documents
        if isinstance(document, list) or (
            "collections" in str(type(document)).lower() and not hasattr(document, "page_content")
        ):
            data_list = [_doc_to_dict(doc) for doc in document]
            return encode(cast("ToonValue", data_list), options)

        # Single document
        data = _doc_to_dict(document)
        return encode(cast("ToonValue", data), options)
    except Exception as e:
        msg = "Failed to convert LangChain Document to TOON: " + str(e)
        raise ConversionError(msg) from e


def toon_to_langchain(toon_str: str, options: DecodeOptions | None = None) -> Any:
    """Convert TOON format to LangChain Document.

    Args:
        toon_str: TOON format string
        options: Decoding options

    Returns:
        LangChain Document instance

    Raises:
        ImportError: If langchain is not installed
        ConversionError: If conversion fails
    """
    if not LANGCHAIN_AVAILABLE or LangchainDocument is None:
        msg = "langchain is required. Install with: pip install toon-converter[integrations]"
        raise ImportError(msg)

    try:
        toon_options = _convert_decode_options(options)
        data = decode(toon_str, toon_options)
        if isinstance(data, dict):
            page_content = str(data.get("page_content", ""))
            metadata = data.get("metadata", {})
            # Construct using the detected LangChain Document class
            return LangchainDocument(page_content=page_content, metadata=metadata)  # type: ignore[misc]
        msg = "TOON data must be a dictionary with page_content and metadata"
        raise ConversionError(msg)
    except Exception as e:
        msg = "Failed to convert TOON to LangChain Document: " + str(e)
        raise ConversionError(msg) from e


# ------------------------------
# Message / Chat conversions
# ------------------------------
def _normalize_additional_kwargs(additional: Any) -> dict[str, Any]:
    """Normalize additional_kwargs to a flat mapping of simple scalar values.

    This avoids creating nested maps/lists that can confuse the TOON encoder/parser's
    top-level array counting. Non-scalar values are converted to strings.
    """
    out: dict[str, Any] = {}
    if additional is None:
        return out
    if isinstance(additional, dict):
        for k, v in additional.items():
            # keep simple scalars as-is, convert others to strings
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[str(k)] = v
            else:
                out[str(k)] = str(v)
    else:
        # If it's not a mapping, represent it as a string under a fixed key
        out["value"] = str(additional)
    return out


def _message_to_dict(msg: Any) -> dict[str, Any]:
    """Normalize a LangChain message to a dictionary.

    Normalized keys: 'type', 'content', 'additional_kwargs'
    """
    content = getattr(msg, "content", None) or getattr(msg, "text", "")
    # some implementations use .role or .type
    role = getattr(msg, "role", None) or getattr(msg, "type", None)
    raw_additional = getattr(msg, "additional_kwargs", None) or getattr(msg, "metadata", None) or {}
    additional = _normalize_additional_kwargs(raw_additional)
    return {"type": (role or "unknown"), "content": content, "additional_kwargs": additional}


def _dict_to_message(data: dict[str, Any]) -> Any:
    """Reconstruct a LangChain message instance if we have a class available.

    Falls back to a plain dict if no message class can be constructed.
    """
    msg_type = (data.get("type") or "").lower()
    content = data.get("content", "")
    additional = data.get("additional_kwargs", {}) or {}

    cls = None
    if msg_type and msg_type in _LANGCHAIN_MESSAGE_CLASSES:
        cls = _LANGCHAIN_MESSAGE_CLASSES[msg_type]
    else:
        # fallback to base if available
        cls = _LANGCHAIN_MESSAGE_CLASSES.get("base")

    if cls is None:
        # no LangChain message class available — return dict fallback
        return {"type": msg_type or "unknown", "content": content, "additional_kwargs": additional}

    # try to instantiate with common constructor patterns
    try:
        return cls(content=content, additional_kwargs=additional)  # type: ignore[misc]
    except Exception:
        try:
            # some message classes accept only content
            return cls(content=content)  # type: ignore[misc]
        except Exception:
            # give dict fallback
            return {
                "type": msg_type or "unknown",
                "content": content,
                "additional_kwargs": additional,
            }


def messages_to_toon(messages: list[Any], options: EncodeOptions | None = None) -> str:
    """Convert list of LangChain messages to TOON.

    To avoid array-header parsing issues we wrap the messages list inside a
    top-level object: {"messages": [...]}. This is backwards compatible because
    toon_to_messages also accepts a raw list.
    """
    try:
        data_list = [_message_to_dict(m) for m in messages]
        wrapper = {"messages": data_list}
        return encode(cast("ToonValue", wrapper), options)
    except Exception as e:
        msg = "Failed to convert messages to TOON: " + str(e)
        raise ConversionError(msg) from e


def toon_to_messages(toon_str: str, options: DecodeOptions | None = None) -> list[Any]:
    """Convert TOON to list of LangChain message objects (or dicts if classes not available).

    Accepts either:
      - a bare array (legacy)
      - an object with {"messages": [...]} (safe encoding)
    """
    try:
        toon_options = _convert_decode_options(options)
        data = decode(toon_str, toon_options)

        # Accept legacy list directly
        if isinstance(data, list):
            data_list = data
        # Accept wrapped object
        elif isinstance(data, dict) and "messages" in data and isinstance(data["messages"], list):
            data_list = data["messages"]
        # Try to coerce single items into a list
        elif data is None:
            data_list = []
        else:
            data_list = [data]

        result: list[Any] = []
        for item in data_list:
            # decode() elements may be any ToonValue; ensure we pass dict[str, Any]
            if isinstance(item, dict):
                result.append(_dict_to_message(item))
            else:
                fallback: dict[str, Any] = {
                    "type": "unknown",
                    "content": str(item),
                    "additional_kwargs": {},
                }
                result.append(_dict_to_message(fallback))

        return result
    except Exception as e:
        msg = "Failed to convert TOON to messages: " + str(e)
        raise ConversionError(msg) from e
