Decoder API
============================================================

The Decoder module handles data deserialization.

Facade Decoder
--------------

.. autoclass:: toonverter.Decoder
   :members:
   :undoc-members:
   :show-inheritance:

Decoder Implementation
----------------------

The underlying decoding logic is largely implemented in pure Python. However, for critical performance paths,
an optional `Rust backend` is utilized by the `toonverter.decoders` module.
The Python `Decoder` class transparently leverages this Rust implementation if the Rust extension is installed and enabled.

**Note**: The Rust decoder is now enabled by default, as previous issues with indented list parsing have been resolved. The system will gracefully fall back to the Python decoder if the Rust extension fails to load.

For configuration options related to enabling/disabling the Rust decoder, refer to the
:doc:`../guides/configuration` guide.

.. automodule:: toonverter.decoders
   :members:
   :undoc-members:
   :show-inheritance: