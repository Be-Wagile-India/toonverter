CLI Reference
=============

The TOON Converter command-line interface (CLI) provides a comprehensive set of tools for file conversion, analysis, and optimization.

Global Options
--------------
* ``--version``: Show the version and exit.
* ``--help``: Show help message and exit.

Commands
--------

convert
^^^^^^^
Convert data between formats.

.. code-block:: bash

    toon convert input.json output.toon --from json --to toon

    # Use compact encoding
    toon convert data.json data.toon --from json --to toon --compact

encode
^^^^^^
Encode a file to TOON format. Automatically detects input format from extension.

.. code-block:: bash

    toon encode input.yaml -o output.toon

    # Print to stdout
    toon encode input.json

decode
^^^^^^
Decode a TOON file to another format (default JSON).

.. code-block:: bash

    toon decode data.toon -o data.json
    toon decode data.toon --format yaml

analyze
^^^^^^^
Compare token usage across multiple formats.

.. code-block:: bash

    toon analyze data.json
    
    # Compare specific formats
    toon analyze data.json -c json -c yaml -c toon -c xml

deduplicate
^^^^^^^^^^^
(New in v2.1) Semantic deduplication of lists within data.

.. code-block:: bash

    toon deduplicate data.json -o clean.json --threshold 0.9

infer
^^^^^
Infer a schema from a data file.

.. code-block:: bash

    toon infer data.json -o schema.json

validate
^^^^^^^^
Validate data against a schema.

.. code-block:: bash

    toon validate data.json --schema schema.json

schema-merge
^^^^^^^^^^^^
(New in v2.1) Merge multiple schema files into a single unified schema.

.. code-block:: bash

    toon schema-merge s1.json s2.json -o merged.json

diff
^^^^
Compare two data files structurally.

.. code-block:: bash

    toon diff file1.json file2.json

compress / decompress
^^^^^^^^^^^^^^^^^^^^^
Apply Smart Dictionary Compression (SDC) to data.

.. code-block:: bash

    toon compress big_data.json -o compressed.json
    toon decompress compressed.json -o original.json

formats
^^^^^^^
List all supported formats.

.. code-block:: bash

    toon formats