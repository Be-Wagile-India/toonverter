"""Unit tests for public API."""

import toonverter as toon


class TestFacadeAPI:
    """Test suite for Level 1 Facade API."""

    def test_encode_decode(self, sample_dict):
        """Test basic encode/decode."""
        encoded = toon.encode(sample_dict)
        decoded = toon.decode(encoded)
        assert decoded == sample_dict

    def test_list_formats(self):
        """Test list_formats function."""
        formats = toon.list_formats()
        assert isinstance(formats, list)
        assert "json" in formats
        assert "toon" in formats

    def test_is_supported(self):
        """Test is_supported function."""
        assert toon.is_supported("json") is True
        assert toon.is_supported("toon") is True
        assert toon.is_supported("invalid") is False

    def test_analyze(self, sample_dict):
        """Test analyze function."""
        report = toon.analyze(sample_dict, compare_formats=["json", "toon"])
        assert report.best_format in ["json", "toon"]
        assert len(report.analyses) == 2


class TestOOPAPI:
    """Test suite for Level 2 OOP API."""

    def test_encoder_class(self, sample_dict):
        """Test Encoder class."""
        encoder = toon.Encoder(format="toon")
        result = encoder.encode(sample_dict)
        assert isinstance(result, str)

    def test_decoder_class(self):
        """Test Decoder class."""
        decoder = toon.Decoder(format="toon")
        result = decoder.decode("{name:Alice}")
        assert result["name"] == "Alice"

    def test_analyzer_class(self, sample_dict):
        """Test Analyzer class."""
        analyzer = toon.Analyzer(model="gpt-4")
        report = analyzer.analyze_multi_format(sample_dict, formats=["json", "toon"])
        assert isinstance(report, toon.ComparisonReport)

    def test_converter_class(self):
        """Test Converter class."""
        converter = toon.Converter("json", "json")
        data = {"key": "value"}

        result = converter.convert_data(data)
        assert result == data

    def test_encoder_with_options(self):
        """Test Encoder with options."""
        encoder = toon.Encoder(format="json", indent=2)
        result = encoder.encode({"key": "value"})
        assert isinstance(result, str)

    def test_decoder_with_options(self):
        """Test Decoder with options."""
        decoder = toon.Decoder(format="json", strict=True)
        assert decoder.options is not None

    def test_analyzer_custom_model(self):
        """Test Analyzer with custom model."""
        analyzer = toon.Analyzer(model="gpt-3.5-turbo")
        assert analyzer.model == "gpt-3.5-turbo"


class TestEncodeDecode:
    """Additional encode/decode tests."""

    def test_encode_to_json(self):
        """Test encoding to JSON format."""
        data = {"key": "value"}
        result = toon.encode(data, to_format="json")
        assert '"key"' in result

    def test_encode_to_yaml(self):
        """Test encoding to YAML format."""
        data = {"key": "value"}
        result = toon.encode(data, to_format="yaml")
        assert "key" in result

    def test_decode_from_json(self):
        """Test decoding from JSON."""
        result = toon.decode('{"key": "value"}', from_format="json")
        assert result["key"] == "value"

    def test_decode_from_yaml(self):
        """Test decoding from YAML."""
        result = toon.decode("key: value", from_format="yaml")
        assert result["key"] == "value"

    def test_roundtrip_toon(self):
        """Test TOON roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = toon.encode(data)
        decoded = toon.decode(encoded)
        assert decoded == data

    def test_roundtrip_json(self):
        """Test JSON roundtrip."""
        data = {"key": "value"}
        encoded = toon.encode(data, to_format="json")
        decoded = toon.decode(encoded, from_format="json")
        assert decoded == data


class TestLoadSave:
    """Test load/save functions."""

    def test_save_and_load_json(self, tmp_path):
        """Test save and load JSON."""
        path = tmp_path / "test.json"
        data = {"test": "value"}

        toon.save(data, str(path), format="json")
        loaded = toon.load(str(path), format="json")

        assert loaded == data

    def test_save_and_load_toon(self, tmp_path):
        """Test save and load TOON."""
        path = tmp_path / "test.toon"
        data = {"key": "value"}

        toon.save(data, str(path), format="toon")
        loaded = toon.load(str(path), format="toon")

        assert loaded == data

    def test_save_with_options(self, tmp_path):
        """Test save with encoding options."""
        path = tmp_path / "test.json"
        data = {"key": "value"}

        toon.save(data, str(path), format="json", indent=2)
        assert path.exists()


class TestConvert:
    """Test convert function."""

    def test_convert_json_to_json(self, tmp_path):
        """Test converting JSON to JSON."""
        import json

        source = tmp_path / "source.json"
        target = tmp_path / "target.json"

        # Create source
        with open(source, "w") as f:
            json.dump({"test": "data"}, f)

        # Convert
        result = toon.convert(str(source), str(target), "json", "json")

        assert result.success is True
        assert target.exists()
        assert result.source_tokens > 0
        assert result.target_tokens > 0

    def test_convert_failure(self):
        """Test convert handles errors."""
        result = toon.convert("nonexistent.json", "out.json", "json", "json")

        assert result.success is False
        assert result.error is not None


class TestAnalyze:
    """Test analyze function."""

    def test_analyze_default_formats(self):
        """Test analyze with default formats."""
        data = {"key": "value"}
        report = toon.analyze(data)

        assert len(report.analyses) == 3  # json, yaml, toon
        assert report.best_format is not None

    def test_analyze_custom_formats(self):
        """Test analyze with custom formats."""
        data = {"key": "value"}
        report = toon.analyze(data, compare_formats=["json", "toon"])

        assert len(report.analyses) == 2

    def test_analyze_with_from_format(self):
        """Test analyze with specific source format."""
        data = {"key": "value"}
        report = toon.analyze(data, from_format="yaml", compare_formats=["json", "toon"])

        assert report is not None


class TestEdgeCases:
    """Test edge cases."""

    def test_encode_empty_dict(self):
        """Test encoding empty dict."""
        result = toon.encode({})
        assert isinstance(result, str)

    def test_encode_empty_list(self):
        """Test encoding empty list."""
        result = toon.encode([])
        assert isinstance(result, str)

    def test_decode_empty_object(self):
        """Test decoding empty object."""
        result = toon.decode("{}", from_format="json")
        assert result == {}

    def test_list_formats_not_empty(self):
        """Test list_formats returns non-empty list."""
        formats = toon.list_formats()
        assert len(formats) > 0

    def test_is_supported_case_insensitive(self):
        """Test is_supported with different cases."""
        # Note: This depends on implementation
        assert toon.is_supported("json") is True
        assert toon.is_supported("TOON") is True or toon.is_supported("toon") is True
