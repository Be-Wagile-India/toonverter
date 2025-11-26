"""FastAPI integration."""

from typing import Any

from toonverter.core.types import EncodeOptions
from toonverter.encoders import encode
from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder
from toonverter.encoders.toon_encoder import _convert_options


# Optional dependency
try:
    from fastapi.responses import Response, StreamingResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Response = Any  # type: ignore
    StreamingResponse = Any  # type: ignore


class TOONStreamingResponse(StreamingResponse):
    """FastAPI Streaming Response for TOON format.

    Streams TOON content generator with proper media type.
    """

    media_type = "application/toon"

    def __init__(
        self,
        content: Any,
        count: int | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        encode_options: EncodeOptions | None = None,
        background: Any | None = None,
    ) -> None:
        """Initialize TOON streaming response.

        Args:
            content: Iterator/Generator of data to stream
            count: Total count (if content is a generator) for valid header
            status_code: HTTP status code
            headers: Additional headers
            media_type: Override media type
            encode_options: TOON encoding options
            background: Background task to run after response
        """
        if not FASTAPI_AVAILABLE:
            msg = "fastapi is required. Install with: pip install toon-converter[integrations]"
            raise ImportError(msg)

        # Wrap in StreamList if count provided
        data_to_encode = content
        if count is not None:
            data_to_encode = StreamList(iterator=content, length=count)

        # Create stream generator
        toon_options = _convert_options(encode_options)
        encoder = ToonStreamEncoder(toon_options)

        # iterencode yields strings, StreamingResponse expects bytes or strings.
        # It handles strings by encoding to utf-8.
        stream_generator = encoder.iterencode(data_to_encode)

        super().__init__(
            content=stream_generator,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


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
        background: Any | None = None,
    ) -> None:
        """Initialize TOON response.

        Args:
            content: Data to encode (will be converted to TOON)
            status_code: HTTP status code
            headers: Additional headers
            media_type: Override media type
            encode_options: TOON encoding options
            background: Background task to run after response

        Raises:
            ImportError: If fastapi is not installed
        """
        if not FASTAPI_AVAILABLE:
            msg = "fastapi is required. Install with: pip install toon-converter[integrations]"
            raise ImportError(msg)

        # Encode content to TOON format
        toon_content = content if isinstance(content, str) else encode(content, encode_options)

        super().__init__(
            content=toon_content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
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
