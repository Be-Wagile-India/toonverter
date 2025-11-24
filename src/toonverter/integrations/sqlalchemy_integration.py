"""SQLAlchemy integration for toonverter.

Provides seamless conversion between SQLAlchemy ORM models, query results,
and TOON format for efficient database serialization with 40-60% token savings.

Features:
- ORM model instance serialization
- Query result conversion
- Schema export
- Bulk operations with batching
"""

from __future__ import annotations

from collections.abc import Iterator  # noqa: TC003
from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from sqlalchemy import MetaData, Table, inspect
    from sqlalchemy.engine import Result, Row
    from sqlalchemy.orm import DeclarativeMeta, Session
else:
    # Runtime imports - these are only used, never just annotated
    try:
        from sqlalchemy import MetaData, Table, inspect
        from sqlalchemy.engine import Result, Row
        from sqlalchemy.orm import DeclarativeMeta, Session

        SQLALCHEMY_AVAILABLE = True
    except ImportError:
        SQLALCHEMY_AVAILABLE = False
        inspect = None
        # Define dummy types for runtime when SQLAlchemy not installed
        Result = Row = MetaData = Table = Session = DeclarativeMeta = None  # type: ignore

from toonverter.core.exceptions import ConversionError
from toonverter.core.spec import ToonDecodeOptions, ToonEncodeOptions  # noqa: TC001
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder
from toonverter.encoders.toon_encoder import ToonEncoder


def _check_sqlalchemy():
    """Check if SQLAlchemy is available."""
    if not SQLALCHEMY_AVAILABLE:
        msg = "SQLAlchemy is not installed. Install with: pip install toonverter[sqlalchemy]"
        raise ImportError(msg)


# =============================================================================
# 1. ORM MODEL SERIALIZATION
# =============================================================================


def sqlalchemy_to_toon(
    instance: Any,
    include_relationships: bool = False,
    exclude_columns: list[str] | None = None,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert SQLAlchemy model instance to TOON format.

    Args:
        instance: SQLAlchemy model instance
        include_relationships: Whether to include relationship data
        exclude_columns: List of column names to exclude
        options: TOON encoding options

    Returns:
        TOON formatted string

    Raises:
        ConversionError: If conversion fails

    Examples:
        >>> user = User(name="Alice", age=30, email="alice@example.com")
        >>> toon = sqlalchemy_to_toon(user)
        >>> print(toon)
        name: Alice
        age: 30
        email: alice@example.com

        >>> # With relationships
        >>> toon = sqlalchemy_to_toon(user, include_relationships=True)
    """
    _check_sqlalchemy()

    try:
        # Get model inspector
        mapper = inspect(instance.__class__)

        # Build dictionary from model
        data: dict[str, Any] = {}
        exclude_set = set(exclude_columns or [])

        # Add column values
        for column in mapper.columns:
            if column.key in exclude_set:
                continue

            value = getattr(instance, column.key)

            # Convert SQLAlchemy types to JSON-compatible types
            data[column.key] = _convert_sqlalchemy_value(value)

        # Add relationships if requested
        if include_relationships:
            for relationship in mapper.relationships:
                if relationship.key in exclude_set:
                    continue

                rel_value = getattr(instance, relationship.key)

                if rel_value is None:
                    data[relationship.key] = None
                elif isinstance(rel_value, list):
                    # One-to-many or many-to-many
                    data[relationship.key] = [
                        _model_to_dict(item, include_pk=True) for item in rel_value
                    ]
                else:
                    # Many-to-one or one-to-one
                    data[relationship.key] = _model_to_dict(rel_value, include_pk=True)

        # Encode to TOON
        encoder = ToonEncoder(options)
        return encoder.encode(data)

    except Exception as e:
        msg = f"Failed to convert SQLAlchemy model to TOON: {e}"
        raise ConversionError(msg) from e


def toon_to_sqlalchemy(
    toon_str: str, model_class: type, options: ToonDecodeOptions | None = None
) -> Any:
    """Convert TOON format to SQLAlchemy model instance.

    Args:
        toon_str: TOON formatted string
        model_class: SQLAlchemy model class
        options: TOON decoding options

    Returns:
        Model instance

    Raises:
        ConversionError: If conversion fails

    Examples:
        >>> toon = '''
        ... name: Bob
        ... age: 25
        ... email: bob@example.com
        ... '''
        >>> user = toon_to_sqlalchemy(toon, User)
        >>> session.add(user)
        >>> session.commit()
    """
    _check_sqlalchemy()

    try:
        # Decode TOON to dict
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if not isinstance(data, dict):
            msg = "TOON data must be an object for model conversion"
            raise ConversionError(msg)

        # Create model instance
        # Filter data to only include valid columns
        mapper = inspect(model_class)
        column_names = {col.key for col in mapper.columns}

        valid_data = {key: value for key, value in data.items() if key in column_names}

        return model_class(**valid_data)

    except Exception as e:
        msg = f"Failed to convert TOON to SQLAlchemy model: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# 2. QUERY RESULT CONVERSION
# =============================================================================


def query_to_toon(
    result: Result | list[Row] | list[Any], options: ToonEncodeOptions | None = None
) -> str:
    """Convert SQLAlchemy query result to TOON format.

    Optimized for query results with automatic tabular array detection.

    Args:
        result: SQLAlchemy Result object or list of Row/model instances
        options: TOON encoding options

    Returns:
        TOON formatted string

    Raises:
        ConversionError: If conversion fails

    Examples:
        >>> result = session.execute(select(User)).scalars().all()
        >>> toon = query_to_toon(result)

        >>> # Or with Result object
        >>> result = session.execute(select(User.name, User.age))
        >>> toon = query_to_toon(result)
    """
    _check_sqlalchemy()

    try:
        # Convert result to list of dicts
        rows = _result_to_dicts(result)

        # Encode to TOON
        encoder = ToonEncoder(options)
        return encoder.encode(rows)

    except Exception as e:
        msg = f"Failed to convert query result to TOON: {e}"
        raise ConversionError(msg) from e


def bulk_query_to_toon(
    result: Result | list[Any], chunk_size: int = 1000, options: ToonEncodeOptions | None = None
) -> Iterator[str]:
    """Convert large query result to TOON in chunks (streaming).

    Memory-efficient for large datasets.

    Args:
        result: SQLAlchemy Result object or list of instances
        chunk_size: Number of rows per chunk
        options: TOON encoding options

    Yields:
        TOON formatted string for each chunk

    Examples:
        >>> result = session.execute(select(User))
        >>> for toon_chunk in bulk_query_to_toon(result, chunk_size=500):
        ...     process_chunk(toon_chunk)
    """
    _check_sqlalchemy()

    try:
        encoder = ToonEncoder(options)
        chunk = []

        # Process result in chunks
        if hasattr(result, "scalars"):
            # Result object
            for row in result.scalars():
                chunk.append(_model_to_dict(row))

                if len(chunk) >= chunk_size:
                    yield encoder.encode(chunk)
                    chunk = []
        else:
            # List of instances
            for row in result:
                chunk.append(_model_to_dict(row))

                if len(chunk) >= chunk_size:
                    yield encoder.encode(chunk)
                    chunk = []

        # Yield remaining chunk
        if chunk:
            yield encoder.encode(chunk)

    except Exception as e:
        msg = f"Failed to bulk convert query result: {e}"
        raise ConversionError(msg) from e


def stream_query_to_toon(
    result: Result | list[Any], count: int | None = None, options: ToonEncodeOptions | None = None
) -> Iterator[str]:
    """Stream query result to a single valid TOON document.

    Generates a single [N]: array, streaming items as they are processed.
    Requires total count to be known or provided.

    Args:
        result: SQLAlchemy Result object or list of instances
        count: Total number of rows (required if result doesn't support len/rowcount)
        options: TOON encoding options

    Yields:
        Chunks of the TOON document

    Raises:
        ConversionError: If count cannot be determined
    """
    _check_sqlalchemy()

    try:
        # Determine count
        if count is None:
            if isinstance(result, list):
                count = len(result)
            elif hasattr(result, "rowcount") and result.rowcount >= 0:
                count = result.rowcount
            else:
                msg = "Total count required for streaming single document. Pass 'count' argument."
                raise ConversionError(msg)

        # Create iterator of dicts
        def result_iterator():
            # Handle various result types using model-to-dict conversion
            if hasattr(result, "scalars"):
                for row in result.scalars():
                    yield _model_to_dict(row)
            elif isinstance(result, list):
                for row in result:
                    yield _model_to_dict(row)
            else:
                # Result object
                for row in result:
                    yield _model_to_dict(row)

        # Create StreamList wrapper
        stream_data = StreamList(iterator=result_iterator(), length=count)

        # Stream encode
        encoder = ToonStreamEncoder(options)
        return encoder.iterencode(stream_data)

    except Exception as e:
        msg = f"Failed to stream query result: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# 3. SCHEMA EXPORT
# =============================================================================


def schema_to_toon(metadata: MetaData, options: ToonEncodeOptions | None = None) -> str:
    """Export database schema to TOON format.

    Args:
        metadata: SQLAlchemy MetaData object
        options: TOON encoding options

    Returns:
        TOON formatted string with schema information

    Examples:
        >>> from sqlalchemy import MetaData
        >>> metadata = MetaData()
        >>> metadata.reflect(bind=engine)
        >>> toon = schema_to_toon(metadata)
    """
    _check_sqlalchemy()

    try:
        schema_data = {"tables": [_table_to_dict(table) for table in metadata.sorted_tables]}

        encoder = ToonEncoder(options)
        return encoder.encode(schema_data)

    except Exception as e:
        msg = f"Failed to export schema to TOON: {e}"
        raise ConversionError(msg) from e


def table_to_toon(table: Table, options: ToonEncodeOptions | None = None) -> str:
    """Export single table schema to TOON format.

    Args:
        table: SQLAlchemy Table object
        options: TOON encoding options

    Returns:
        TOON formatted string

    Examples:
        >>> from sqlalchemy import Table, MetaData
        >>> metadata = MetaData()
        >>> user_table = Table('users', metadata, autoload_with=engine)
        >>> toon = table_to_toon(user_table)
    """
    _check_sqlalchemy()

    try:
        table_data = _table_to_dict(table)

        encoder = ToonEncoder(options)
        return encoder.encode(table_data)

    except Exception as e:
        msg = f"Failed to export table to TOON: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# 4. BULK OPERATIONS
# =============================================================================


def bulk_insert_from_toon(
    toon_str: str,
    model_class: type,
    session: Session,
    chunk_size: int = 1000,
    options: ToonDecodeOptions | None = None,
) -> int:
    """Bulk insert records from TOON format.

    Memory-efficient batch insertion.

    Args:
        toon_str: TOON formatted string (array of objects)
        model_class: SQLAlchemy model class
        session: SQLAlchemy session
        chunk_size: Number of records per batch
        options: TOON decoding options

    Returns:
        Number of records inserted

    Raises:
        ConversionError: If conversion fails

    Examples:
        >>> toon = '''
        ... [3]{name,age,email}:
        ...   Alice,30,alice@example.com
        ...   Bob,25,bob@example.com
        ...   Carol,35,carol@example.com
        ... '''
        >>> count = bulk_insert_from_toon(toon, User, session)
        >>> print(f"Inserted {count} records")
    """
    _check_sqlalchemy()

    try:
        # Decode TOON to list of dicts
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if not isinstance(data, list):
            msg = "TOON data must be an array for bulk insert"
            raise ConversionError(msg)

        # Get valid column names
        mapper = inspect(model_class)
        column_names = {col.key for col in mapper.columns}

        total_inserted = 0

        # Process in chunks
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]

            # Filter to valid columns and create instances
            instances = []
            for record in chunk:
                if not isinstance(record, dict):
                    continue

                valid_data = {key: value for key, value in record.items() if key in column_names}
                instances.append(model_class(**valid_data))

            # Bulk insert chunk
            session.bulk_save_objects(instances)
            session.commit()
            total_inserted += len(instances)

        return total_inserted

    except Exception as e:
        session.rollback()
        msg = f"Failed to bulk insert from TOON: {e}"
        raise ConversionError(msg) from e


def export_table_to_toon(
    table_name: str,
    session: Session,
    stream: bool = False,
    chunk_size: int = 1000,
    options: ToonEncodeOptions | None = None,
) -> str | Iterator[str]:
    """Export entire table to TOON format.

    Args:
        table_name: Name of table to export
        session: SQLAlchemy session
        stream: If True, returns iterator for large tables
        chunk_size: Rows per chunk (for streaming)
        options: TOON encoding options

    Returns:
        TOON string or iterator of TOON chunks

    Examples:
        >>> # Small table
        >>> toon = export_table_to_toon('users', session)

        >>> # Large table (streaming)
        >>> for chunk in export_table_to_toon('logs', session, stream=True):
        ...     process_chunk(chunk)
    """
    _check_sqlalchemy()

    try:
        # Get model class from table name
        # This is a simplified version - in production, you'd need proper registry
        from sqlalchemy import text

        if stream:
            # Streaming mode for large tables
            def stream_table():
                offset = 0
                while True:
                    query = text(f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}")
                    result = session.execute(query)
                    rows = result.fetchall()

                    if not rows:
                        break

                    # Convert to dicts
                    row_dicts = [dict(row._mapping.items()) for row in rows]

                    encoder = ToonEncoder(options)
                    yield encoder.encode(row_dicts)

                    offset += chunk_size

            return stream_table()
        # Load entire table
        query = text(f"SELECT * FROM {table_name}")
        result = session.execute(query)
        rows = result.fetchall()

        row_dicts = [dict(row._mapping.items()) for row in rows]

        encoder = ToonEncoder(options)
        return encoder.encode(row_dicts)

    except Exception as e:
        msg = f"Failed to export table to TOON: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _convert_sqlalchemy_value(value: Any) -> Any:
    """Convert SQLAlchemy-specific types to JSON-compatible types.

    Args:
        value: Value from SQLAlchemy column

    Returns:
        JSON-compatible value
    """
    if value is None:
        return None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        # Convert bytes to hex string
        return value.hex()
    return value


def _model_to_dict(instance: Any, include_pk: bool = False) -> dict[str, Any]:
    """Convert model instance to dictionary.

    Args:
        instance: SQLAlchemy model instance
        include_pk: Whether to include primary key

    Returns:
        Dictionary representation
    """
    mapper = inspect(instance.__class__)

    data = {}
    for column in mapper.columns:
        if not include_pk and column.primary_key:
            continue

        value = getattr(instance, column.key)
        data[column.key] = _convert_sqlalchemy_value(value)

    return data


def _result_to_dicts(result: Result | list[Any]) -> list[dict[str, Any]]:
    """Convert SQLAlchemy result to list of dictionaries.

    Args:
        result: Query result

    Returns:
        List of dictionaries
    """
    rows = []

    # Check for Result object (has scalars/mappings methods)
    # We check callable because Session also has scalars but we don't want to call it without args if it's a Session.
    # A Result object's scalars() can be called without args.
    # Safe check: if it looks like a Result object (not a Session).
    is_result = (
        hasattr(result, "scalars") and hasattr(result, "fetchall") and not hasattr(result, "commit")
    )

    if is_result:
        # Result object with ORM instances
        # .scalars() returns a ScalarResult which is iterable
        try:
            for instance in result.scalars():
                rows.append(_model_to_dict(instance))
        except TypeError:
            # Fallback if scalars() failed (e.g. old sqlalchemy or wrong object)
            pass
    elif hasattr(result, "mappings") and not hasattr(result, "commit"):
        # Result object with Row mappings
        for row in result.mappings():
            rows.append(dict(row))
    elif isinstance(result, list):
        # List of instances or rows
        if result and hasattr(result[0], "__table__"):
            # List of ORM instances
            rows = [_model_to_dict(instance) for instance in result]
        else:
            # List of Row objects or dicts
            for row in result:
                if hasattr(row, "_mapping"):
                    rows.append(
                        {
                            key: _convert_sqlalchemy_value(value)
                            for key, value in row._mapping.items()
                        }
                    )
                else:
                    rows.append(row)

    return rows


def _table_to_dict(table: Table) -> dict[str, Any]:
    """Convert Table object to dictionary schema.

    Args:
        table: SQLAlchemy Table

    Returns:
        Dictionary with table schema
    """
    return {
        "name": table.name,
        "columns": [
            {
                "name": col.name,
                "type": str(col.type),
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "unique": col.unique,
                "default": str(col.default) if col.default else None,
            }
            for col in table.columns
        ],
        "indexes": [
            {
                "name": idx.name,
                "columns": [col.name for col in idx.columns],
                "unique": idx.unique,
            }
            for idx in table.indexes
        ],
        "foreign_keys": [
            {
                "constrained_columns": [col.name for col in fk.columns],
                "referred_table": fk.column.table.name,
                "referred_columns": [fk.column.name],
            }
            for fk in table.foreign_keys
        ],
    }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

__all__ = [
    # Bulk operations
    "bulk_insert_from_toon",
    "bulk_query_to_toon",
    "export_table_to_toon",
    "stream_query_to_toon",
    # Queries
    "query_to_toon",
    # Schema
    "schema_to_toon",
    # ORM
    "sqlalchemy_to_toon",
    "table_to_toon",
    "toon_to_sqlalchemy",
]
