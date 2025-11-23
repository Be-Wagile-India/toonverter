Hybrid Serializer API
============================================================

.. autoclass:: toonverter.multimodal.hybrid_serializer.HybridSerializer
   :members:
   :undoc-members:
   :show-inheritance:

The ``HybridSerializer`` class handles the conversion of mixed text and image data
into optimized payloads for Vision LLMs, with support for image deduplication and
path tracking.

.. autoclass:: toonverter.multimodal.hybrid_serializer.SerializationContext
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

Basic Serialization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer
    from toonverter.core.types import ImageOptimizeOptions

    # Create serializer
    serializer = HybridSerializer()

    # Data with images
    data = {
        "title": "User Profile",
        "user": {
            "name": "Alice",
            "avatar": "/path/to/avatar.jpg"
        }
    }

    # Serialize mixed content
    payload = serializer.serialize(
        data,
        image_keys=["avatar"]
    )

    # Payload contains text strings and ToonImage objects
    for item in payload:
        if isinstance(item, str):
            print(f"Text: {item[:50]}...")
        else:
            print(f"Image: {item.mime_type}, {item.token_cost} tokens")

With Custom Options
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer
    from toonverter.core.types import ImageOptimizeOptions, ImageDetail

    serializer = HybridSerializer()

    # Configure image optimization
    options = ImageOptimizeOptions(
        max_dimension=512,
        detail=ImageDetail.LOW,
        format="WEBP",
        quality=75,
        max_size_kb=50
    )

    data = {
        "article": {
            "title": "AI in 2024",
            "hero_image": "/path/to/hero.jpg",
            "content": "Article text..."
        }
    }

    payload = serializer.serialize(
        data,
        image_keys=["hero_image"],
        optimize_options=options
    )

Multiple Images
~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer

    serializer = HybridSerializer()

    # Multiple users with photos
    data = {
        "users": [
            {"name": "Alice", "photo": "/alice.jpg"},
            {"name": "Bob", "photo": "/bob.jpg"},
            {"name": "Charlie", "photo": "/charlie.jpg"}
        ]
    }

    payload = serializer.serialize(
        data,
        image_keys=["photo"]
    )

    # Images are automatically deduplicated if same path used multiple times
    print(f"Payload has {len(payload)} parts")

Nested Data Structures
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer

    serializer = HybridSerializer()

    # Complex nested structure
    data = {
        "company": {
            "name": "TechCorp",
            "logo": "/logo.png",
            "departments": [
                {
                    "name": "Engineering",
                    "team_photo": "/eng_team.jpg",
                    "lead": {
                        "name": "Alice",
                        "headshot": "/alice.jpg"
                    }
                },
                {
                    "name": "Sales",
                    "team_photo": "/sales_team.jpg"
                }
            ]
        }
    }

    # Specify all image keys
    payload = serializer.serialize(
        data,
        image_keys=["logo", "team_photo", "headshot"]
    )

Image Deduplication
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer

    serializer = HybridSerializer()

    # Same image used multiple times
    data = {
        "header_logo": "/company_logo.png",
        "footer_logo": "/company_logo.png",
        "sidebar_logo": "/company_logo.png"
    }

    payload = serializer.serialize(
        data,
        image_keys=["header_logo", "footer_logo", "sidebar_logo"]
    )

    # Image is processed only once and reused
    # Markers reference the same optimized image

Working with URLs
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer

    serializer = HybridSerializer()

    # Images can be URLs
    data = {
        "profile": {
            "name": "Alice",
            "avatar": "https://example.com/avatar.jpg"
        }
    }

    payload = serializer.serialize(
        data,
        image_keys=["avatar"]
    )

    # URL images are handled efficiently

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.hybrid_serializer import HybridSerializer
    import logging

    # Enable logging to see errors
    logging.basicConfig(level=logging.WARNING)

    serializer = HybridSerializer()

    # Data with invalid image path
    data = {
        "user": {
            "name": "Alice",
            "photo": "/nonexistent/path.jpg"
        }
    }

    payload = serializer.serialize(
        data,
        image_keys=["photo"]
    )

    # Errors are logged, and error placeholders are inserted
    # Processing continues for other valid images
