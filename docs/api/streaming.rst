Streaming API
=================

The :mod:`toonverter.streaming` module enables incremental processing of large TOON or CSV-like datasets...

.. automodule:: toonverter.streaming
   :no-index:
   :members:
   :exclude-members: StreamingEncoder, StreamingDecoder, RE_KV, RE_TABLE_START

.. autoclass:: toonverter.streaming.StreamingEncoder
   :members:
   :undoc-members:
   :no-index:
   :exclude-members: _indent, write_kv, write_section_start, write_table_header, write_table_row, dump_iterable, __init__

   .. automethod:: toonverter.streaming.StreamingEncoder.__init__
      :no-index:
   .. automethod:: toonverter.streaming.StreamingEncoder.write_kv
   .. automethod:: toonverter.streaming.StreamingEncoder.write_section_start
   .. automethod:: toonverter.streaming.StreamingEncoder.write_table_header
   .. automethod:: toonverter.streaming.StreamingEncoder.write_table_row
   .. automethod:: toonverter.streaming.StreamingEncoder.dump_iterable

.. autoclass:: toonverter.streaming.StreamingDecoder
   :members:
   :undoc-members:
   :no-index:
   :exclude-members: _parse_csv_row, iter_items, __init__ # Added __init__ to exclude list

   .. automethod:: toonverter.streaming.StreamingDecoder.__init__
      :no-index:
   .. automethod:: toonverter.streaming.StreamingDecoder.iter_items