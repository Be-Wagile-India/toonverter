"""FastAPI integration."""

from typing import Any

from toonverter.core.types import EncodeOptions
from toonverter.encoders import encode


# Optional dependency
try:
    from fastapi.responses import Response

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Response = Any  # type: ignore


class TOONResponse(Response):
    """FastAPI Response class for TOON format.

    Automatically encodes response data to TOON format with proper
    content-type header.
    """

    media_type = "application/toon"

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        encode_options: EncodeOptions | None = None,
    ) -> None:
        """Initialize TOON response.

        Args:
            content: Data to encode (will be converted to TOON)
            status_code: HTTP status code
            headers: Additional headers
            media_type: Override media type
            encode_options: TOON encoding options

        Raises:
            ImportError: If fastapi is not installed
        """
        if not FASTAPI_AVAILABLE:
            msg = "fastapi is required. Install with: pip install toon-converter[integrations]"
            raise ImportError(msg)

        # Encode content to TOON format
        toon_content = content if isinstance(content, str) else encode(content, encode_options)

        super().__init__(
            content=toon_content, status_code=status_code, headers=headers, media_type=media_type
        )

    def render(self, content: Any) -> bytes:
        """Render content to bytes.

        Args:
            content: Content to render

        Returns:
            UTF-8 encoded bytes
        """
        if isinstance(content, bytes):
            return content
        return content.encode("utf-8")
