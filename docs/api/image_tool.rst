Image Optimizer API
============================================================

.. autoclass:: toonverter.multimodal.image_tool.ImageOptimizer
   :members:
   :undoc-members:
   :show-inheritance:

The ``ImageOptimizer`` class provides advanced image processing for Vision LLMs,
including EXIF rotation correction, smart transparency handling, iterative compression,
and accurate token estimation.

Example Usage
-------------

Basic Image Processing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    # Create optimizer
    optimizer = ImageOptimizer()

    # Process an image file
    options = ImageOptimizeOptions()
    result = optimizer.process_image("/path/to/image.jpg", options)

    print(f"Format: {result.mime_type}")
    print(f"Token cost: {result.token_cost}")
    print(f"Base64 length: {len(result.data)}")

Custom Optimization Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions, ImageDetail

    optimizer = ImageOptimizer()

    # Custom options for high-quality output
    options = ImageOptimizeOptions(
        max_dimension=2048,
        detail=ImageDetail.HIGH,
        format="PNG",
        quality=95
    )

    result = optimizer.process_image("/path/to/photo.jpg", options)

Size-Constrained Compression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()

    # Limit output size to 100KB
    options = ImageOptimizeOptions(
        max_dimension=1024,
        format="JPEG",
        quality=85,
        max_size_kb=100
    )

    result = optimizer.process_image("/large_image.jpg", options)

    # Image is iteratively compressed to meet size limit

Processing Different Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions
    from PIL import Image
    from pathlib import Path

    optimizer = ImageOptimizer()
    options = ImageOptimizeOptions()

    # From file path (string)
    result1 = optimizer.process_image("/path/to/image.jpg", options)

    # From Path object
    result2 = optimizer.process_image(Path("image.png"), options)

    # From bytes
    with open("image.jpg", "rb") as f:
        image_bytes = f.read()
    result3 = optimizer.process_image(image_bytes, options)

    # From PIL Image object
    pil_img = Image.open("image.jpg")
    result4 = optimizer.process_image(pil_img, options)

    # From URL (returns immediately without downloading)
    result5 = optimizer.process_image("https://example.com/image.jpg", options)
    print(f"URL image: {result5.is_url}")

Low Detail Mode
~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions, ImageDetail

    optimizer = ImageOptimizer()

    # Low detail for thumbnails or icons
    options = ImageOptimizeOptions(
        max_dimension=512,
        detail=ImageDetail.LOW,
        format="WEBP",
        quality=70
    )

    result = optimizer.process_image("/thumbnail.jpg", options)

    # Low detail images have fixed token cost of 85
    print(f"Token cost: {result.token_cost}")  # Always 85

Handling Transparency
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()
    options = ImageOptimizeOptions(format="JPEG")

    # RGBA images are automatically converted to RGB
    # with white background
    result = optimizer.process_image("/logo_with_alpha.png", options)

    # Result is JPEG with white background

Token Cost Estimation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions, ImageDetail

    optimizer = ImageOptimizer()

    # Different detail levels affect token cost
    high_detail = ImageOptimizeOptions(detail=ImageDetail.HIGH)
    low_detail = ImageOptimizeOptions(detail=ImageDetail.LOW)
    auto_detail = ImageOptimizeOptions(detail=ImageDetail.AUTO)

    image_path = "/photo.jpg"

    result_high = optimizer.process_image(image_path, high_detail)
    result_low = optimizer.process_image(image_path, low_detail)
    result_auto = optimizer.process_image(image_path, auto_detail)

    print(f"High detail: {result_high.token_cost} tokens")
    print(f"Low detail: {result_low.token_cost} tokens")  # Always 85
    print(f"Auto detail: {result_auto.token_cost} tokens")

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()
    options = ImageOptimizeOptions(
        max_dimension=800,
        quality=80,
        max_size_kb=50
    )

    image_paths = [
        "/photo1.jpg",
        "/photo2.jpg",
        "/photo3.jpg"
    ]

    results = []
    for path in image_paths:
        result = optimizer.process_image(path, options)
        results.append(result)

    total_tokens = sum(r.token_cost for r in results)
    print(f"Total token cost: {total_tokens}")

Format Conversion
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()

    # Convert PNG to JPEG
    options_jpeg = ImageOptimizeOptions(format="JPEG", quality=85)
    result_jpeg = optimizer.process_image("/image.png", options_jpeg)

    # Convert to WebP for better compression
    options_webp = ImageOptimizeOptions(format="WEBP", quality=80)
    result_webp = optimizer.process_image("/image.png", options_webp)

    print(f"JPEG size: {len(result_jpeg.data)}")
    print(f"WebP size: {len(result_webp.data)}")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()
    options = ImageOptimizeOptions()

    try:
        result = optimizer.process_image("/nonexistent.jpg", options)
    except ValueError as e:
        print(f"Image processing failed: {e}")

    # Check for PIL availability
    try:
        result = optimizer.process_image("/image.jpg", options)
    except ImportError as e:
        print(f"PIL not installed: {e}")

API Response Format
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from toonverter.multimodal.image_tool import ImageOptimizer
    from toonverter.core.types import ImageOptimizeOptions

    optimizer = ImageOptimizer()
    options = ImageOptimizeOptions()

    result = optimizer.process_image("/photo.jpg", options)

    # Convert to API format for OpenAI/Anthropic
    api_block = result.to_api_block()

    # api_block is ready to include in API request
    # {
    #     "type": "image_url",
    #     "image_url": {
    #         "url": "data:image/jpeg;base64,...",
    #         "detail": "auto"
    #     }
    # }

Performance Tips
----------------

* Use ``detail=ImageDetail.LOW`` for thumbnails and icons to reduce token costs
* Set ``max_size_kb`` to enforce size limits for API constraints
* Use WebP format for best compression with good quality
* Cache processed images to avoid reprocessing identical sources
* Process images in parallel for large batches
