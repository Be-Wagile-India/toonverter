"""DSPy Integration for toonverter.

Provides efficient TOON serialization for DSPy examples, predictions, and datasets.
Perfect for prompt optimization, few-shot learning, and LM program development.

Key benefits:
- 40-60% token savings for training examples and datasets
- Preserves input/output structure and metadata
- Efficient storage for large example collections
- Seamless integration with DSPy workflows

Install dependencies:
    pip install toonverter[dspy]

Basic usage:
    from toonverter.integrations.dspy import dspy_to_toon, toon_to_dspy

    # Convert example to TOON
    toon_str = dspy_to_toon(example)

    # Convert back to example
    example = toon_to_dspy(toon_str)
"""

from typing import Any, Dict, List, Optional, Iterator, Union
from ..encoders.toon_encoder import ToonEncoder
from ..decoders.toon_decoder import ToonDecoder
from ..core.spec import ToonEncodeOptions, ToonDecodeOptions
from ..core.exceptions import ConversionError

try:
    import dspy
    from dspy import Example, Prediction

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


def _check_dspy():
    """Check if DSPy is available."""
    if not DSPY_AVAILABLE:
        raise ImportError(
            "DSPy is not installed. "
            "Install with: pip install toonverter[dspy]"
        )


# =============================================================================
# EXAMPLE CONVERSION
# =============================================================================

def dspy_to_toon(
    obj: Union['Example', 'Prediction', Dict[str, Any]],
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert DSPy Example, Prediction, or dict to TOON format.

    Args:
        obj: DSPy Example, Prediction, or dictionary
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> example = dspy.Example(question="What is 2+2?", answer="4")
        >>> toon = dspy_to_toon(example)
        >>> print(toon)
        question: What is 2+2?
        answer: 4
    """
    _check_dspy()

    try:
        encoder = ToonEncoder(options)

        if isinstance(obj, Example):
            data = _example_to_dict(obj)
        elif isinstance(obj, Prediction):
            data = _prediction_to_dict(obj)
        elif isinstance(obj, dict):
            data = obj
        else:
            raise ConversionError(f"Unsupported type: {type(obj)}")

        return encoder.encode(data)

    except Exception as e:
        raise ConversionError(f"Failed to convert DSPy object to TOON: {e}")


def toon_to_dspy(
    toon_str: str,
    obj_type: str = "example",
    with_inputs: Optional[List[str]] = None,
    options: Optional[ToonDecodeOptions] = None
) -> Union['Example', 'Prediction', Dict[str, Any]]:
    """Convert TOON format to DSPy Example, Prediction, or dict.

    Args:
        toon_str: TOON formatted string
        obj_type: Type of object to create ("example", "prediction", or "dict")
        with_inputs: List of field names to mark as inputs (for Example)
        options: TOON decoding options

    Returns:
        DSPy Example, Prediction, or dictionary

    Example:
        >>> toon = "question: What is 2+2?\\nanswer: 4"
        >>> example = toon_to_dspy(toon, with_inputs=["question"])
        >>> print(example.question)
        What is 2+2?
    """
    _check_dspy()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if obj_type == "example":
            return _dict_to_example(data, with_inputs)
        elif obj_type == "prediction":
            return _dict_to_prediction(data)
        elif obj_type == "dict":
            return data
        else:
            raise ConversionError(f"Unsupported object type: {obj_type}")

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to DSPy object: {e}")


# =============================================================================
# DATASET CONVERSION
# =============================================================================

def dataset_to_toon(
    examples: List['Example'],
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert DSPy dataset (list of Examples) to TOON array format.

    Args:
        examples: List of DSPy Example instances
        options: TOON encoding options

    Returns:
        TOON formatted string with array of examples

    Example:
        >>> examples = [
        ...     dspy.Example(question="Q1", answer="A1"),
        ...     dspy.Example(question="Q2", answer="A2")
        ... ]
        >>> toon = dataset_to_toon(examples)
        >>> print(toon)
        [2]:
          - question: Q1
            answer: A1
          - question: Q2
            answer: A2
    """
    _check_dspy()

    try:
        encoder = ToonEncoder(options)
        data_list = [_example_to_dict(ex) for ex in examples]
        return encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to convert dataset to TOON: {e}")


def toon_to_dataset(
    toon_str: str,
    with_inputs: Optional[List[str]] = None,
    options: Optional[ToonDecodeOptions] = None
) -> List['Example']:
    """Convert TOON array format to DSPy dataset (list of Examples).

    Args:
        toon_str: TOON formatted string (array)
        with_inputs: List of field names to mark as inputs
        options: TOON decoding options

    Returns:
        List of DSPy Example instances

    Example:
        >>> toon = "[2]:\\n  - question: Q1\\n    answer: A1\\n  - question: Q2\\n    answer: A2"
        >>> examples = toon_to_dataset(toon, with_inputs=["question"])
        >>> len(examples)
        2
    """
    _check_dspy()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            raise ConversionError("Expected TOON array format")

        return [_dict_to_example(data, with_inputs) for data in data_list]

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to dataset: {e}")


# =============================================================================
# STREAMING OPERATIONS
# =============================================================================

def stream_dataset_to_toon(
    examples: List['Example'],
    chunk_size: int = 100,
    options: Optional[ToonEncodeOptions] = None
) -> Iterator[str]:
    """Stream large datasets to TOON in chunks.

    Memory-efficient for processing large example collections.

    Args:
        examples: List of DSPy Example instances
        chunk_size: Number of examples per chunk
        options: TOON encoding options

    Yields:
        TOON formatted strings (one per chunk)

    Example:
        >>> examples = [dspy.Example(q=f"Q{i}", a=f"A{i}") for i in range(1000)]
        >>> for chunk_toon in stream_dataset_to_toon(examples, chunk_size=100):
        ...     save_chunk(chunk_toon)  # Process 100 examples at a time
    """
    _check_dspy()

    try:
        encoder = ToonEncoder(options)

        for i in range(0, len(examples), chunk_size):
            chunk = examples[i:i + chunk_size]
            data_list = [_example_to_dict(ex) for ex in chunk]
            yield encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to stream dataset to TOON: {e}")


# =============================================================================
# PREDICTIONS CONVERSION
# =============================================================================

def predictions_to_toon(
    predictions: List['Prediction'],
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert DSPy Prediction objects to TOON format.

    Useful for caching model predictions.

    Args:
        predictions: List of Prediction instances
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> predictions = [
        ...     dspy.Prediction(answer="Paris", confidence=0.95),
        ...     dspy.Prediction(answer="London", confidence=0.82)
        ... ]
        >>> toon = predictions_to_toon(predictions)
    """
    _check_dspy()

    try:
        encoder = ToonEncoder(options)
        data_list = [_prediction_to_dict(pred) for pred in predictions]
        return encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to convert predictions to TOON: {e}")


def toon_to_predictions(
    toon_str: str,
    options: Optional[ToonDecodeOptions] = None
) -> List['Prediction']:
    """Convert TOON format to DSPy Prediction objects.

    Args:
        toon_str: TOON formatted string (array)
        options: TOON decoding options

    Returns:
        List of Prediction instances
    """
    _check_dspy()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            raise ConversionError("Expected TOON array format")

        return [_dict_to_prediction(data) for data in data_list]

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to predictions: {e}")


# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

def few_shot_to_toon(
    examples: List['Example'],
    max_examples: Optional[int] = None,
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert few-shot examples to compact TOON format.

    Optimized for minimal token usage in prompts.

    Args:
        examples: List of few-shot Example instances
        max_examples: Maximum number of examples to include
        options: TOON encoding options

    Returns:
        TOON formatted string optimized for few-shot learning

    Example:
        >>> examples = [
        ...     dspy.Example(input="2+2", output="4"),
        ...     dspy.Example(input="3+5", output="8"),
        ...     dspy.Example(input="7-2", output="5")
        ... ]
        >>> toon = few_shot_to_toon(examples, max_examples=3)
    """
    _check_dspy()

    try:
        if max_examples:
            examples = examples[:max_examples]

        encoder = ToonEncoder(options)
        data_list = [_example_to_dict(ex) for ex in examples]
        return encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to convert few-shot examples to TOON: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _example_to_dict(example: 'Example') -> Dict[str, Any]:
    """Convert DSPy Example to dictionary."""
    # Example objects store data in their __dict__
    data = {}

    # Get all attributes except internal ones
    for key, value in example.__dict__.items():
        if not key.startswith('_'):
            data[key] = value

    return data


def _dict_to_example(data: Dict[str, Any], with_inputs: Optional[List[str]] = None) -> 'Example':
    """Convert dictionary to DSPy Example."""
    if with_inputs:
        # Create example with specified inputs
        return Example(**data).with_inputs(*with_inputs)
    else:
        # Create example without specifying inputs
        return Example(**data)


def _prediction_to_dict(prediction: 'Prediction') -> Dict[str, Any]:
    """Convert DSPy Prediction to dictionary."""
    data = {}

    # Get all attributes except internal ones
    for key, value in prediction.__dict__.items():
        if not key.startswith('_'):
            data[key] = value

    return data


def _dict_to_prediction(data: Dict[str, Any]) -> 'Prediction':
    """Convert dictionary to DSPy Prediction."""
    return Prediction(**data)


# =============================================================================
# SIGNATURE OPERATIONS
# =============================================================================

def signature_examples_to_toon(
    signature_name: str,
    examples: List['Example'],
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert signature examples to TOON with metadata.

    Args:
        signature_name: Name of the signature
        examples: List of examples for this signature
        options: TOON encoding options

    Returns:
        TOON formatted string with signature metadata

    Example:
        >>> examples = [dspy.Example(question="Q1", answer="A1")]
        >>> toon = signature_examples_to_toon("QA", examples)
    """
    _check_dspy()

    try:
        encoder = ToonEncoder(options)

        data = {
            "signature": signature_name,
            "count": len(examples),
            "examples": [_example_to_dict(ex) for ex in examples]
        }

        return encoder.encode(data)

    except Exception as e:
        raise ConversionError(f"Failed to convert signature examples to TOON: {e}")


# =============================================================================
# OPTIMIZATION TRACES
# =============================================================================

def optimization_trace_to_toon(
    trace: List[Dict[str, Any]],
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert DSPy optimization trace to TOON format.

    Useful for storing optimization history.

    Args:
        trace: List of optimization steps (dicts with metrics)
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> trace = [
        ...     {"step": 1, "score": 0.65, "params": {...}},
        ...     {"step": 2, "score": 0.78, "params": {...}},
        ...     {"step": 3, "score": 0.85, "params": {...}}
        ... ]
        >>> toon = optimization_trace_to_toon(trace)
    """
    try:
        encoder = ToonEncoder(options)
        return encoder.encode(trace)

    except Exception as e:
        raise ConversionError(f"Failed to convert optimization trace to TOON: {e}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
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
