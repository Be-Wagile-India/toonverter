Optimization API
============================================================

The Optimization module provides compression and context optimization.

Context Optimization
--------------------

.. class:: toonverter.optimization.ContextOptimizer(budget: int, policy: OptimizationPolicy | None = None, apply_lightweight_prepass: bool = False)

   Optimizes data structure to fit within a token budget.

   :param budget: The target token budget (in tokens).
   :param policy: Optional :class:`OptimizationPolicy` to guide degradation decisions.
   :param apply_lightweight_prepass: If ``True``, runs a lightweight optimization pass (rounding, truncating) even if the data is within budget. Defaults to ``False``.

   .. method:: optimize(data: Any) -> Any

      Main entry point. Returns a modified copy of data fitting the budget.

Smart Compression
-----------------

.. class:: toonverter.optimization.SmartCompressor(min_length: int = 4, min_occurrences: int = 2, prefix: str = "@")

   Optimizes data structure size using frequency-based dictionary compression.

   :param min_length: Minimum string length to consider for compression.
   :param min_occurrences: Minimum number of times a string must appear.
   :param prefix: Symbol prefix (default: "@").

   .. method:: compress(data: Any) -> dict[str, Any]

      Compress data by extracting common strings into a symbol table.

   .. method:: decompress(compressed_data: dict[str, Any]) -> Any

      Decompress data using the embedded symbol table.

.. automodule:: toonverter.optimization
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:
