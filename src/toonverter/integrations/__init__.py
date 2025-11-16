"""Integrations module for third-party libraries."""

# Pandas integration
try:
    from .pandas_integration import pandas_to_toon, toon_to_pandas

    __all_pandas__ = ["pandas_to_toon", "toon_to_pandas"]
except ImportError:
    __all_pandas__ = []

# Pydantic integration
try:
    from .pydantic import pydantic_to_toon, toon_to_pydantic

    __all_pydantic__ = ["pydantic_to_toon", "toon_to_pydantic"]
except ImportError:
    __all_pydantic__ = []

# LangChain integration
try:
    from .langchain import langchain_to_toon, toon_to_langchain

    __all_langchain__ = ["langchain_to_toon", "toon_to_langchain"]
except ImportError:
    __all_langchain__ = []

# FastAPI integration
try:
    from .fastapi import TOONResponse

    __all_fastapi__ = ["TOONResponse"]
except ImportError:
    __all_fastapi__ = []

# SQLAlchemy integration
try:
    from .sqlalchemy import (
        bulk_insert_from_toon,
        bulk_query_to_toon,
        export_table_to_toon,
        query_to_toon,
        schema_to_toon,
        sqlalchemy_to_toon,
        table_to_toon,
        toon_to_sqlalchemy,
    )

    __all_sqlalchemy__ = [
        "sqlalchemy_to_toon",
        "toon_to_sqlalchemy",
        "query_to_toon",
        "bulk_query_to_toon",
        "schema_to_toon",
        "table_to_toon",
        "bulk_insert_from_toon",
        "export_table_to_toon",
    ]
except ImportError:
    __all_sqlalchemy__ = []

# MCP Server integration
try:
    from .mcp_server import ToonverterMCPServer

    __all_mcp__ = ["ToonverterMCPServer"]
except ImportError:
    __all_mcp__ = []

# LlamaIndex integration
try:
    from .llamaindex import (
        bulk_documents_to_toon,
        bulk_toon_to_documents,
        extract_metadata_to_toon,
        index_to_toon,
        llamaindex_to_toon,
        stream_documents_to_toon,
        toon_to_llamaindex,
    )

    __all_llamaindex__ = [
        "llamaindex_to_toon",
        "toon_to_llamaindex",
        "bulk_documents_to_toon",
        "bulk_toon_to_documents",
        "stream_documents_to_toon",
        "index_to_toon",
        "extract_metadata_to_toon",
    ]
except ImportError:
    __all_llamaindex__ = []

# Haystack integration
try:
    from .haystack import (
        answers_to_toon,
        haystack_to_toon,
        toon_to_answers,
        toon_to_haystack,
    )

    # Note: Avoid name conflicts with LlamaIndex by using module-qualified imports
    __all_haystack__ = [
        "haystack_to_toon",
        "toon_to_haystack",
        "answers_to_toon",
        "toon_to_answers",
    ]
except ImportError:
    __all_haystack__ = []

# DSPy integration
try:
    from .dspy import (
        dataset_to_toon,
        dspy_to_toon,
        few_shot_to_toon,
        optimization_trace_to_toon,
        predictions_to_toon,
        signature_examples_to_toon,
        stream_dataset_to_toon,
        toon_to_dataset,
        toon_to_dspy,
        toon_to_predictions,
    )

    __all_dspy__ = [
        "dspy_to_toon",
        "toon_to_dspy",
        "dataset_to_toon",
        "toon_to_dataset",
        "stream_dataset_to_toon",
        "predictions_to_toon",
        "toon_to_predictions",
        "few_shot_to_toon",
        "signature_examples_to_toon",
        "optimization_trace_to_toon",
    ]
except ImportError:
    __all_dspy__ = []

# Instructor integration
try:
    from .instructor_integration import (
        bulk_responses_to_toon,
        bulk_toon_to_responses,
        cache_response,
        extraction_batch_to_toon,
        response_to_toon,
        schema_to_toon,
        stream_responses_to_toon,
        toon_to_extraction_batch,
        toon_to_response,
        validation_results_to_toon,
    )

    __all_instructor__ = [
        "response_to_toon",
        "toon_to_response",
        "bulk_responses_to_toon",
        "bulk_toon_to_responses",
        "stream_responses_to_toon",
        "schema_to_toon",
        "validation_results_to_toon",
        "extraction_batch_to_toon",
        "toon_to_extraction_batch",
        "cache_response",
    ]
except ImportError:
    __all_instructor__ = []

__all__ = (
    __all_pandas__
    + __all_pydantic__
    + __all_langchain__
    + __all_fastapi__
    + __all_sqlalchemy__
    + __all_mcp__
    + __all_llamaindex__
    + __all_haystack__
    + __all_dspy__
    + __all_instructor__
)
