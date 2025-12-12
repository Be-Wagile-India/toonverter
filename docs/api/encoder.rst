Encoder API
============================================================

The Encoder module handles data serialization.

Facade Encoder
--------------

.. autoclass:: toonverter.Encoder
   :members:
   :undoc-members:
   :show-inheritance:

Encoder Implementation
----------------------

The underlying encoding logic is largely implemented in pure Python. However, for critical performance paths,
an optional `Rust backend` is utilized by the `toonverter.encoders.toon_encoder` module.
The Python `Encoder` class transparently leverages this Rust implementation if the Rust extension is installed and enabled.

For configuration options related to enabling/disabling the Rust encoder, refer to the
:doc:`../guides/configuration` guide.

.. automodule:: toonverter.encoders
   :members:
   :undoc-members:
   :show-inheritance: