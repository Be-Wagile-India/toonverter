"""Comprehensive tests for string quoting rules."""

from toonverter.core.spec import Delimiter
from toonverter.encoders.string_encoder import StringEncoder


class TestQuotingRequired:
    """Test cases where quoting is required."""

    def setup_method(self):
        """Set up encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_empty_string_quoted(self):
        """Empty string must be quoted."""
        result = self.encoder.encode("")
        assert result == '""'

    def test_whitespace_only_quoted(self):
        """Whitespace-only strings must be quoted."""
        assert self.encoder.encode("   ") == '"   "'
        assert self.encoder.encode("\t") == '"\\t"'
        assert self.encoder.encode("\n") == '"\\n"'

    def test_leading_whitespace_quoted(self):
        """Strings with leading whitespace must be quoted."""
        assert self.encoder.encode(" test").startswith('"')
        assert self.encoder.encode("\ttest").startswith('"')

    def test_trailing_whitespace_quoted(self):
        """Strings with trailing whitespace must be quoted."""
        assert self.encoder.encode("test ").startswith('"')
        assert self.encoder.encode("test\t").startswith('"')

    def test_reserved_words_quoted(self):
        """Reserved words must be quoted."""
        assert self.encoder.encode("true") == '"true"'
        assert self.encoder.encode("false") == '"false"'
        assert self.encoder.encode("null") == '"null"'

    def test_numeric_strings_quoted(self):
        """Numeric-looking strings must be quoted."""
        assert self.encoder.encode("123").startswith('"')
        assert self.encoder.encode("3.14").startswith('"')
        assert self.encoder.encode("-42").startswith('"')

    def test_special_chars_quoted(self):
        """Strings with special chars must be quoted."""
        assert self.encoder.encode("test:value").startswith('"')
        assert self.encoder.encode("test[0]").startswith('"')
        assert self.encoder.encode("test{key}").startswith('"')
        assert self.encoder.encode("test,value").startswith('"')

    def test_hyphen_at_start_quoted(self):
        """Strings starting with hyphen must be quoted."""
        assert self.encoder.encode("-").startswith('"')
        assert self.encoder.encode("-test").startswith('"')
        assert self.encoder.encode("--double").startswith('"')

    def test_delimiter_quoted(self):
        """Strings containing delimiter must be quoted."""
        comma_enc = StringEncoder(Delimiter.COMMA)
        assert comma_enc.encode("a,b").startswith('"')

        tab_enc = StringEncoder(Delimiter.TAB)
        assert tab_enc.encode("a\tb").startswith('"')

        pipe_enc = StringEncoder(Delimiter.PIPE)
        assert pipe_enc.encode("a|b").startswith('"')


class TestQuotingNotRequired:
    """Test cases where quoting is not required."""

    def setup_method(self):
        """Set up encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_simple_string_not_quoted(self):
        """Simple strings don't need quotes."""
        assert self.encoder.encode("hello") == "hello"
        assert self.encoder.encode("test") == "test"

    def test_alphanumeric_not_quoted(self):
        """Alphanumeric strings don't need quotes."""
        assert self.encoder.encode("test123") == "test123"
        assert self.encoder.encode("ABC") == "ABC"

    def test_underscore_not_quoted(self):
        """Strings with underscores don't need quotes."""
        assert self.encoder.encode("user_name") == "user_name"
        assert self.encoder.encode("my_var") == "my_var"

    def test_hyphen_in_middle_not_quoted(self):
        """Hyphens in middle don't require quotes."""
        assert self.encoder.encode("test-value") == "test-value"
        assert self.encoder.encode("multi-word-string") == "multi-word-string"


class TestEscapeSequences:
    """Test escape sequence handling."""

    def setup_method(self):
        """Set up encoder."""
        self.encoder = StringEncoder(Delimiter.COMMA)

    def test_backslash_escaped(self):
        """Backslashes must be escaped."""
        result = self.encoder.encode("path\\to\\file")
        assert "\\\\" in result

    def test_quote_escaped(self):
        """Quotes must be escaped."""
        result = self.encoder.encode('He said "hello"')
        assert '\\"' in result

    def test_newline_escaped(self):
        """Newlines must be escaped."""
        result = self.encoder.encode("line1\nline2")
        assert "\\n" in result

    def test_tab_escaped(self):
        """Tabs must be escaped."""
        result = self.encoder.encode("col1\tcol2")
        assert "\\t" in result

    def test_carriage_return_escaped(self):
        """Carriage returns must be escaped."""
        result = self.encoder.encode("text\rmore")
        assert "\\r" in result
