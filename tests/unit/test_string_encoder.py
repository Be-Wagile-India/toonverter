"""Comprehensive tests for string encoder."""

import pytest
from toonverter.encoders.string_encoder import StringEncoder
from toonverter.core.spec import Delimiter


class TestStringEncoderEncoding:
    """Test string encoding functionality."""

    def setup_method(self):
        """Set up string encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_simple_string_no_quotes(self):
        """Test simple string doesn't need quotes."""
        assert self.encoder.encode("hello") == "hello"
        assert self.encoder.encode("world") == "world"

    def test_empty_string_needs_quotes(self):
        """Test empty string needs quotes."""
        assert self.encoder.encode("") == '""'

    def test_reserved_words_need_quotes(self):
        """Test reserved words need quotes."""
        assert self.encoder.encode("true") == '"true"'
        assert self.encoder.encode("false") == '"false"'
        assert self.encoder.encode("null") == '"null"'
        assert self.encoder.encode("TRUE") == '"TRUE"'
        assert self.encoder.encode("False") == '"False"'

    def test_number_like_strings_need_quotes(self):
        """Test strings that look like numbers need quotes."""
        assert self.encoder.encode("42") == '"42"'
        assert self.encoder.encode("3.14") == '"3.14"'
        assert self.encoder.encode("-10") == '"-10"'
        assert self.encoder.encode("0") == '"0"'

    def test_leading_whitespace_needs_quotes(self):
        """Test leading whitespace needs quotes."""
        assert self.encoder.encode(" hello") == '" hello"'
        assert self.encoder.encode("\thello") == '"\\thello"'  # Tab is escaped

    def test_trailing_whitespace_needs_quotes(self):
        """Test trailing whitespace needs quotes."""
        assert self.encoder.encode("hello ") == '"hello "'
        assert self.encoder.encode("hello\t") == '"hello\\t"'  # Tab is escaped

    def test_string_with_colon_needs_quotes(self):
        """Test string with colon needs quotes."""
        assert self.encoder.encode("key:value") == '"key:value"'

    def test_string_with_delimiter_needs_quotes(self):
        """Test string containing delimiter needs quotes."""
        result = self.encoder.encode("a,b")
        assert result == '"a,b"'

    def test_string_with_pipe_delimiter(self):
        """Test string with pipe delimiter."""
        encoder = StringEncoder(Delimiter.PIPE)
        assert encoder.encode("a|b") == '"a|b"'
        assert encoder.encode("a,b") == "a,b"  # Comma is OK with pipe delimiter

    def test_dash_needs_quotes(self):
        """Test dash alone needs quotes."""
        assert self.encoder.encode("-") == '"-"'

    def test_string_starting_with_dash_needs_quotes(self):
        """Test string starting with dash needs quotes."""
        assert self.encoder.encode("-hello") == '"-hello"'
        assert self.encoder.encode("-item") == '"-item"'

    def test_escape_backslash(self):
        """Test backslash is escaped."""
        result = self.encoder.encode("back\\slash")
        assert result == '"back\\\\slash"'

    def test_escape_double_quote(self):
        """Test double quote is escaped."""
        result = self.encoder.encode('say "hi"')
        assert result == '"say \\"hi\\""'

    def test_escape_newline(self):
        """Test newline is escaped."""
        result = self.encoder.encode("line1\nline2")
        assert result == '"line1\\nline2"'

    def test_escape_carriage_return(self):
        """Test carriage return is escaped."""
        result = self.encoder.encode("line1\rline2")
        assert result == '"line1\\rline2"'

    def test_escape_tab(self):
        """Test tab is escaped."""
        result = self.encoder.encode("col1\tcol2")
        assert result == '"col1\\tcol2"'

    def test_multiple_escape_sequences(self):
        """Test multiple escape sequences."""
        result = self.encoder.encode('test\n"quote"\ttab\\slash')
        assert result == '"test\\n\\"quote\\"\\ttab\\\\slash"'

    def test_normal_string_with_spaces(self):
        """Test normal string with spaces needs quotes (contains space)."""
        # Spaces are in QUOTE_REQUIRED_CHARS, so strings with spaces are quoted
        assert self.encoder.encode("hello world") == '"hello world"'

    def test_string_without_special_chars(self):
        """Test string without special chars doesn't need quotes."""
        assert self.encoder.encode("helloworld") == "helloworld"
        assert self.encoder.encode("test123") == "test123"


class TestStringEncoderDecoding:
    """Test string decoding functionality."""

    def setup_method(self):
        """Set up string encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_decode_unquoted_string(self):
        """Test decoding unquoted string."""
        assert self.encoder.decode("hello") == "hello"
        assert self.encoder.decode("world") == "world"

    def test_decode_quoted_string(self):
        """Test decoding quoted string."""
        assert self.encoder.decode('"hello"') == "hello"
        assert self.encoder.decode('"world"') == "world"

    def test_decode_empty_quoted_string(self):
        """Test decoding empty quoted string."""
        assert self.encoder.decode('""') == ""

    def test_decode_escaped_backslash(self):
        """Test decoding escaped backslash."""
        assert self.encoder.decode('"back\\\\slash"') == "back\\slash"

    def test_decode_escaped_quote(self):
        """Test decoding escaped double quote."""
        assert self.encoder.decode('"say \\"hi\\""') == 'say "hi"'

    def test_decode_escaped_newline(self):
        """Test decoding escaped newline."""
        assert self.encoder.decode('"line1\\nline2"') == "line1\nline2"

    def test_decode_escaped_carriage_return(self):
        """Test decoding escaped carriage return."""
        assert self.encoder.decode('"line1\\rline2"') == "line1\rline2"

    def test_decode_escaped_tab(self):
        """Test decoding escaped tab."""
        assert self.encoder.decode('"col1\\tcol2"') == "col1\tcol2"

    def test_decode_multiple_escapes(self):
        """Test decoding multiple escape sequences."""
        result = self.encoder.decode('"test\\n\\"quote\\"\\ttab\\\\slash"')
        assert result == 'test\n"quote"\ttab\\slash'

    def test_decode_invalid_escape_raises_error(self):
        """Test decoding invalid escape sequence raises error."""
        with pytest.raises(ValueError, match="Invalid escape sequence"):
            self.encoder.decode('"test\\x"')

    def test_decode_unterminated_escape_raises_error(self):
        """Test unterminated escape sequence raises error."""
        with pytest.raises(ValueError, match="Unterminated escape sequence"):
            self.encoder.decode('"test\\"')

    def test_decode_single_quote_not_quoted(self):
        """Test single quote character is not treated as quoted."""
        # String with only opening quote is not quoted
        assert self.encoder.decode('"') == '"'


class TestStringEncoderRoundtrip:
    """Test encode/decode roundtrip."""

    def setup_method(self):
        """Set up string encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_roundtrip_simple_strings(self):
        """Test roundtrip for simple strings."""
        for s in ["hello", "world", "test123"]:
            encoded = self.encoder.encode(s)
            decoded = self.encoder.decode(encoded)
            assert decoded == s

    def test_roundtrip_reserved_words(self):
        """Test roundtrip for reserved words."""
        for s in ["true", "false", "null"]:
            encoded = self.encoder.encode(s)
            decoded = self.encoder.decode(encoded)
            assert decoded == s

    def test_roundtrip_numbers(self):
        """Test roundtrip for number-like strings."""
        for s in ["42", "3.14", "-10", "0"]:
            encoded = self.encoder.encode(s)
            decoded = self.encoder.decode(encoded)
            assert decoded == s

    def test_roundtrip_with_escapes(self):
        """Test roundtrip for strings with escape sequences."""
        for s in ["test\nline", 'say "hi"', "tab\there", "back\\slash", "cr\rhere"]:
            encoded = self.encoder.encode(s)
            decoded = self.encoder.decode(encoded)
            assert decoded == s

    def test_roundtrip_empty_string(self):
        """Test roundtrip for empty string."""
        s = ""
        encoded = self.encoder.encode(s)
        decoded = self.encoder.decode(encoded)
        assert decoded == s

    def test_roundtrip_whitespace_strings(self):
        """Test roundtrip for strings with leading/trailing whitespace."""
        for s in [" hello", "world ", " both "]:
            encoded = self.encoder.encode(s)
            decoded = self.encoder.decode(encoded)
            assert decoded == s

    def test_roundtrip_complex_string(self):
        """Test roundtrip for complex string."""
        s = 'Complex: "quoted", with\nnewlines\tand tabs\\backslash'
        encoded = self.encoder.encode(s)
        decoded = self.encoder.decode(encoded)
        assert decoded == s
