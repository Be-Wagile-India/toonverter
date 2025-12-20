"""Tests for core type definitions and data classes."""

from toonverter.core.types import (
    ComparisonReport,
    ConversionResult,
    DecodeOptions,
    DeduplicationResult,
    DuplicateItem,
    EncodeOptions,
    TokenAnalysis,
)
from toonverter.rag.models import Chunk


class TestEncodeOptions:
    """Test EncodeOptions dataclass."""

    def test_default_values(self):
        """Test EncodeOptions with default values."""
        options = EncodeOptions()
        assert options.indent == 2
        assert options.delimiter == ","
        assert options.length_marker is None
        assert not options.compact
        assert not options.sort_keys
        assert not options.ensure_ascii
        assert options.max_line_length is None
        assert options.token_budget is None
        assert options.optimization_policy is None

    def test_custom_values(self):
        """Test EncodeOptions with custom values."""
        options = EncodeOptions(
            indent=4,
            delimiter="|",
            length_marker="len:",
            compact=True,
            sort_keys=True,
            ensure_ascii=True,
            max_line_length=80,
            token_budget=1000,
            optimization_policy="policy",  # type: ignore
        )
        assert options.indent == 4
        assert options.delimiter == "|"
        assert options.length_marker == "len:"
        assert options.compact
        assert options.sort_keys
        assert options.ensure_ascii
        assert options.max_line_length == 80
        assert options.token_budget == 1000
        assert options.optimization_policy == "policy"

    def test_create_compact(self):
        """Test create_compact class method."""
        options = EncodeOptions.create_compact()
        assert options.indent == 0
        assert options.compact
        assert options.delimiter == ","
        assert not options.sort_keys

    def test_readable(self):
        """Test readable class method."""
        options = EncodeOptions.readable()
        assert options.indent == 2
        assert not options.compact
        assert options.delimiter == ","
        assert options.sort_keys

    def test_tabular(self):
        """Test tabular class method."""
        options = EncodeOptions.tabular()
        assert options.indent == 0
        assert options.compact
        assert options.delimiter == ","
        assert not options.sort_keys


class TestDecodeOptions:
    """Test DecodeOptions dataclass."""

    def test_default_values(self):
        """Test DecodeOptions with default values."""
        options = DecodeOptions()
        assert options.strict
        assert options.type_inference
        assert options.delimiter == ","

    def test_custom_values(self):
        """Test DecodeOptions with custom values."""
        options = DecodeOptions(strict=False, type_inference=False, delimiter=";")
        assert not options.strict
        assert not options.type_inference
        assert options.delimiter == ";"


class TestConversionResult:
    """Test ConversionResult dataclass."""

    def test_post_init_calculates_savings_percentage(self):
        """Test __post_init__ calculates savings percentage correctly."""
        result = ConversionResult(
            success=True,
            source_format="json",
            target_format="toon",
            source_tokens=100,
            target_tokens=50,
        )
        assert result.savings_percentage == 50.0

    def test_post_init_no_savings_if_source_tokens_none(self):
        """Test __post_init__ does not calculate savings if source_tokens is None."""
        result = ConversionResult(
            success=True, source_format="json", target_format="toon", target_tokens=50
        )
        assert result.savings_percentage is None

    def test_post_init_no_savings_if_target_tokens_none(self):
        """Test __post_init__ does not calculate savings if target_tokens is None."""
        result = ConversionResult(
            success=True, source_format="json", target_format="toon", source_tokens=100
        )
        assert result.savings_percentage is None

    def test_post_init_no_savings_if_source_tokens_zero(self):
        """Test __post_init__ does not calculate savings if source_tokens is zero."""
        result = ConversionResult(
            success=True,
            source_format="json",
            target_format="toon",
            source_tokens=0,
            target_tokens=50,
        )
        assert result.savings_percentage is None

    def test_metadata_default_factory(self):
        """Test metadata field uses default_factory."""
        result = ConversionResult(success=True, source_format="json", target_format="toon")
        assert result.metadata == {}
        result.metadata["key"] = "value"
        assert result.metadata == {"key": "value"}


class TestTokenAnalysis:
    """Test TokenAnalysis dataclass."""

    def test_default_values(self):
        """Test TokenAnalysis with default values."""
        analysis = TokenAnalysis(format="json", token_count=100)
        assert analysis.format == "json"
        assert analysis.token_count == 100
        assert analysis.model == "cl100k_base"
        assert analysis.encoding == "utf-8"
        assert analysis.metadata == {}

    def test_custom_values(self):
        """Test TokenAnalysis with custom values."""
        analysis = TokenAnalysis(
            format="yaml",
            token_count=50,
            model="gpt-3.5-turbo",
            encoding="latin-1",
            metadata={"source": "test"},
        )
        assert analysis.format == "yaml"
        assert analysis.token_count == 50
        assert analysis.model == "gpt-3.5-turbo"
        assert analysis.encoding == "latin-1"
        assert analysis.metadata == {"source": "test"}

    def test_metadata_default_factory(self):
        """Test metadata field uses default_factory."""
        analysis = TokenAnalysis(format="json", token_count=10)
        assert analysis.metadata == {}
        analysis.metadata["version"] = 1
        assert analysis.metadata == {"version": 1}


class TestComparisonReport:
    """Test ComparisonReport dataclass."""

    def test_instantiation(self):
        """Test ComparisonReport instantiation."""
        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=50),
        ]
        report = ComparisonReport(
            analyses=analyses,
            best_format="toon",
            worst_format="json",
            recommendations=["use toon"],
        )
        assert report.analyses == analyses
        assert report.best_format == "toon"
        assert report.worst_format == "json"
        assert report.recommendations == ["use toon"]

    def test_recommendations_default_factory(self):
        """Test recommendations field uses default_factory."""
        analyses = [TokenAnalysis(format="json", token_count=100)]
        report = ComparisonReport(analyses=analyses, best_format="json", worst_format="json")
        assert report.recommendations == []
        report.recommendations.append("new rec")
        assert report.recommendations == ["new rec"]

    def test_max_savings_percentage_empty_analyses(self):
        """Test max_savings_percentage with empty analyses."""
        report = ComparisonReport(analyses=[], best_format="", worst_format="")
        assert report.max_savings_percentage == 0.0

    def test_max_savings_percentage_no_difference(self):
        """Test max_savings_percentage when best and worst are the same."""
        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="yaml", token_count=100),
        ]
        report = ComparisonReport(analyses=analyses, best_format="json", worst_format="yaml")
        assert report.max_savings_percentage == 0.0

    def test_max_savings_percentage_positive_savings(self):
        """Test max_savings_percentage with positive savings."""
        analyses = [
            TokenAnalysis(format="json", token_count=200),
            TokenAnalysis(format="toon", token_count=100),
        ]
        report = ComparisonReport(analyses=analyses, best_format="toon", worst_format="json")
        assert report.max_savings_percentage == 50.0

    def test_max_savings_percentage_worst_zero(self):
        """Test max_savings_percentage when worst token count is zero."""
        analyses = [
            TokenAnalysis(format="json", token_count=0),
            TokenAnalysis(format="toon", token_count=0),
        ]
        report = ComparisonReport(analyses=analyses, best_format="json", worst_format="toon")
        assert report.max_savings_percentage == 0.0

    def test_max_savings_percentage_single_analysis(self):
        """Test max_savings_percentage with a single analysis."""
        analyses = [TokenAnalysis(format="json", token_count=100)]
        report = ComparisonReport(analyses=analyses, best_format="json", worst_format="json")
        assert report.max_savings_percentage == 0.0


class TestDuplicateItem:
    """Test DuplicateItem dataclass."""

    def test_instantiation(self):
        """Test DuplicateItem instantiation."""
        item = DuplicateItem(original_index=0, duplicate_index=1, item={"data": "test"})
        assert item.original_index == 0
        assert item.duplicate_index == 1
        assert item.item == {"data": "test"}


class TestDeduplicationResult:
    """Test DeduplicationResult dataclass."""

    def test_default_values(self):
        """Test DeduplicationResult with default values."""
        result = DeduplicationResult(unique_items=["item1"], duplicate_count=0)
        assert result.unique_items == ["item1"]
        assert result.duplicate_count == 0
        assert result.duplicates == []
        assert result.reduction_percentage == 0.0

    def test_custom_values(self):
        """Test DeduplicationResult with custom values."""
        duplicate_item = DuplicateItem(original_index=0, duplicate_index=1, item="dup")
        result = DeduplicationResult(
            unique_items=["item1"],
            duplicate_count=1,
            duplicates=[duplicate_item],
            reduction_percentage=50.0,
        )
        assert result.unique_items == ["item1"]
        assert result.duplicate_count == 1
        assert result.duplicates == [duplicate_item]
        assert result.reduction_percentage == 50.0

    def test_duplicates_default_factory(self):
        """Test duplicates field uses default_factory."""
        result = DeduplicationResult(unique_items=["item1"], duplicate_count=0)
        assert result.duplicates == []
        result.duplicates.append(DuplicateItem(0, 1, "dup"))
        assert len(result.duplicates) == 1


class TestChunk:
    """Test Chunk dataclass."""

    def test_default_values(self):
        """Test Chunk with default values."""
        chunk = Chunk(content="test content")
        assert chunk.content == "test content"
        assert chunk.path == []
        assert chunk.metadata == {}
        assert chunk.token_count == 0

    def test_custom_values(self):
        """Test Chunk with custom values."""
        chunk = Chunk(
            content="custom content",
            path=["doc1", "section2"],
            metadata={"source": "file.txt"},
            token_count=10,
        )
        assert chunk.content == "custom content"
        assert chunk.path == ["doc1", "section2"]
        assert chunk.metadata == {"source": "file.txt"}
        assert chunk.token_count == 10

    def test_path_string_empty_path(self):
        """Test path_string property when path is empty."""
        chunk = Chunk(content="test")
        assert chunk.path_string == ""

    def test_path_string_single_element_path(self):
        """Test path_string property when path has a single element."""
        chunk = Chunk(content="test", path=["root"])
        assert chunk.path_string == "root"

    def test_path_string_multiple_element_path(self):
        """Test path_string property when path has multiple elements."""
        chunk = Chunk(content="test", path=["root", "child", "grandchild"])
        assert chunk.path_string == "root.child.grandchild"

    def test_metadata_default_factory(self):
        """Test metadata field uses default_factory."""
        chunk = Chunk(content="test")
        assert chunk.metadata == {}
        chunk.metadata["new_key"] = "new_value"
        assert chunk.metadata == {"new_key": "new_value"}

    def test_path_default_factory(self):
        """Test path field uses default_factory."""
        chunk = Chunk(content="test")
        assert chunk.path == []
        chunk.path.append("element")
        assert chunk.path == ["element"]
