"""Vendor-specific payload formatters for Vision LLMs."""

import base64
from typing import Any


class VendorAdapter:
    """Base class for vendor adapters."""

    def format(self, image_data: bytes, mime_type: str, detail: str = "auto") -> dict[str, Any]:
        """Format image data into vendor-specific payload."""
        raise NotImplementedError


class OpenAIAdapter(VendorAdapter):
    """Adapter for OpenAI GPT-4 Vision."""

    def format(self, image_data: bytes, mime_type: str, detail: str = "auto") -> dict[str, Any]:
        """Format for OpenAI content array."""
        b64_data = base64.b64encode(image_data).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{b64_data}",
                "detail": detail,
            },
        }


class AnthropicAdapter(VendorAdapter):
    """Adapter for Anthropic Claude 3 Vision."""

    def format(self, image_data: bytes, mime_type: str, _detail: str = "auto") -> dict[str, Any]:
        """Format for Anthropic content block."""
        b64_data = base64.b64encode(image_data).decode("utf-8")
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": b64_data,
            },
        }


_ADAPTERS = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
}


def get_vendor_adapter(provider: str) -> VendorAdapter:
    """Get adapter for provider."""
    adapter_cls = _ADAPTERS.get(provider.lower())
    if not adapter_cls:
        msg = f"Unsupported vision provider: {provider}"
        raise ValueError(msg)
    return adapter_cls()
