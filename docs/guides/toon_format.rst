TOON Format Specification v2.0
==============================

TOON (Token-Optimized Object Notation) is designed for maximum token efficiency while maintaining readability.
This guide covers the TOON v2.0 specification as implemented in toonverter.

Overview
--------

TOON reduces token usage by 30-60% compared to JSON through:

* Minimal syntax (no unnecessary braces, quotes, commas)
* Tabular format for uniform arrays
* Indentation-based structure
* Smart quoting rules

Three Root Forms
----------------

Every TOON document has one of three root forms:

1. Object Form (Default)
^^^^^^^^^^^^^^^^^^^^^^^^^

Key-value pairs, one per line:

.. code-block:: yaml

   name: Alice
   age: 30
   city: NYC

2. Array Form
^^^^^^^^^^^^^

Collection with length annotation:

.. code-block:: yaml

   [3]:
     - Alice
     - Bob
     - Charlie

3. Primitive Form
^^^^^^^^^^^^^^^^^

Single value (string, number, boolean, null):

.. code-block:: yaml

   Hello World

Three Array Forms
-----------------

Arrays can be encoded in three different forms depending on their content:

1. Inline Array
^^^^^^^^^^^^^^^

For primitive values on a single line:

.. code-block:: yaml

   tags[3]: python,llm,optimization

**Requirements**:
- All elements must be primitives (string, number, boolean, null)
- No nested structures

2. Tabular Array
^^^^^^^^^^^^^^^^

For uniform objects with primitive values:

.. code-block:: yaml

   users[3]{name,age,city}:
     Alice,30,NYC
     Bob,25,LA
     Charlie,35,SF

**Requirements**:
- All elements must be objects
- All objects must have the same keys
- All values must be primitives (no nested objects/arrays)

**Benefits**:
- Highest compression ratio (40-60% savings)
- CSV-like efficiency
- Perfect for DataFrame-like data

3. List Array
^^^^^^^^^^^^^

For complex or mixed structures:

.. code-block:: yaml

   items[2]:
     - name: Item1
       price: 19.99
       tags[2]: sale,new
     - name: Item2
       price: 29.99
       nested:
         key: value

**Requirements**:
- Used when inline or tabular forms don't apply
- Supports nested objects and arrays
- Each item starts with ``-`` marker

**Inline Objects**:
First field on dash line, remaining fields indented:

.. code-block:: yaml

   users[2]:
     - name: Alice
       age: 30
     - name: Bob
       age: 25

String Quoting Rules
--------------------

Strings need quotes in these cases:

1. **Empty or Whitespace-Only**

   .. code-block:: yaml

      empty: ""
      spaces: "   "

2. **Leading or Trailing Whitespace**

   .. code-block:: yaml

      text: "  leading"
      text: "trailing  "

3. **Reserved Words**

   .. code-block:: yaml

      value: "true"    # Would be parsed as boolean without quotes
      value: "false"
      value: "null"

4. **Numeric-Looking Strings**

   .. code-block:: yaml

      id: "123"        # Would be parsed as number without quotes
      code: "3.14"
      ref: "-42"

5. **Special Characters**

   .. code-block:: yaml

      path: "test:value"    # Contains colon
      expr: "test[0]"       # Contains brackets
      data: "test{key}"     # Contains braces
      item: "a,b,c"         # Contains comma
      cmd: "a|b"            # Contains pipe

6. **Hyphen at Start**

   .. code-block:: yaml

      value: "-test"
      value: "-"
      value: "--option"

7. **Contains Delimiter**

   The delimiter varies based on context (comma by default):

   .. code-block:: yaml

      text: "a,b,c"    # Comma delimiter
      text: "a\\tb\\tc"  # Tab delimiter
      text: "a|b|c"    # Pipe delimiter

Strings That Don't Need Quotes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   # Simple strings
   name: hello
   value: test

   # Alphanumeric with underscores
   key: user_name
   field: my_var123

   # Hyphens in middle (not at start)
   name: test-value
   key: multi-word-string

Number Canonical Form
---------------------

Numbers must follow canonical form rules:

Valid Numbers
^^^^^^^^^^^^^

.. code-block:: yaml

   count: 42
   price: 19.99
   negative: -3.14
   zero: 0

Normalization Rules
^^^^^^^^^^^^^^^^^^^

These are normalized (not allowed in strict mode):

.. code-block:: yaml

   # 1.0 → 1 (remove unnecessary decimal)
   # 1e5 → 100000 (no exponential notation)
   # -0 → 0 (normalize negative zero)
   # NaN → null (special values become null)
   # Infinity → null
   # -Infinity → null

Delimiters
----------

TOON supports three delimiters with different markers:

Comma (Default)
^^^^^^^^^^^^^^^

No marker needed:

.. code-block:: yaml

   a: 1
   b: 2
   c: 3

   tags[3]: one,two,three

Tab
^^^

Marked with ``{TAB}`` at document start:

.. code-block:: yaml

   {TAB}
   a: 1	b: 2	c: 3

   tags[3]: one	two	three

Pipe
^^^^

Marked with ``{PIPE}`` at document start:

.. code-block:: yaml

   {PIPE}
   a: 1|b: 2|c: 3

   tags[3]: one|two|three

Escape Sequences
----------------

Only 5 escape sequences are allowed in TOON:

.. list-table::
   :header-rows: 1

   * - Escape
     - Meaning
     - Example
   * - ``\\\\``
     - Backslash
     - ``path: "C:\\\\Users"``
   * - ``\\"``
     - Double quote
     - ``text: "He said \\"hi\\""``
   * - ``\\n``
     - Newline
     - ``text: "Line1\\nLine2"``
   * - ``\\r``
     - Carriage return
     - ``text: "Windows\\r\\n"``
   * - ``\\t``
     - Tab
     - ``text: "Col1\\tCol2"``

**Note**: Other common escape sequences like ``\\u0041`` are **not supported** in TOON.

Indentation
-----------

TOON uses indentation to represent nesting:

Rules
^^^^^

1. Use spaces only (tabs forbidden as whitespace)
2. Default indent: 2 spaces
3. Must be consistent throughout document
4. Each nesting level adds one indent level

Example
^^^^^^^

.. code-block:: yaml

   user:
     name: Alice
     address:
       city: NYC
       zip: "10001"
     contacts[2]:
       - type: email
         value: alice@example.com
       - type: phone
         value: "555-1234"

Type Annotations
----------------

Optional type annotations using pipe syntax:

.. code-block:: yaml

   count: 100|int
   price: 19.99|float
   active: true|bool
   updated: 2025-01-15T10:30:00|datetime
   data: null|None

**Note**: Most types are inferred automatically, so annotations are rarely needed.

Complete Example
----------------

.. code-block:: yaml

   # User database (TOON format)

   users[3]{id,name,age,city}:
     1,Alice,30,NYC
     2,Bob,25,LA
     3,Charlie,35,SF

   metadata:
     created: 2025-01-15T10:30:00
     version: 1.0
     tags[4]: users,database,production,v1

   settings:
     max_users: 1000
     enable_auth: true
     features[3]:
       - name: notifications
         enabled: true
       - name: analytics
         enabled: false
       - name: export
         enabled: true

Token Savings
-------------

Real-World Examples
^^^^^^^^^^^^^^^^^^^

Simple Object:

.. list-table::
   :header-rows: 1

   * - Format
     - Tokens
     - Savings
   * - JSON
     - 24
     - 0%
   * - YAML
     - 20
     - 16%
   * - **TOON**
     - **16**
     - **33%**

Tabular Data (100 rows, 3 columns):

.. list-table::
   :header-rows: 1

   * - Format
     - Tokens
     - Savings
   * - JSON
     - 1200
     - 0%
   * - YAML
     - 900
     - 25%
   * - **TOON**
     - **600**
     - **50%**

Reference
---------

For the complete official specification:

* `TOON v2.0 Spec <https://github.com/toon-format/spec>`_
* `Official Python Implementation <https://github.com/toon-format/toon-python>`_

See Also
--------

* :doc:`quick_start` - Start using TOON format
* :doc:`configuration` - Configure encoding options
* :doc:`../examples/tabular_data` - Tabular array examples
