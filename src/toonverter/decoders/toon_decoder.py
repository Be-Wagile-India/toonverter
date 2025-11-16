"""TOON v2.0 decoder - fully spec-compliant implementation.

Decodes TOON format strings to Python data structures following
the official TOON v2.0 specification.
"""

from typing import Any

from ..core.exceptions import DecodingError, ValidationError
from ..core.spec import ArrayForm, Delimiter, RootForm, ToonDecodeOptions, ToonValue
from .lexer import Token, TokenType, ToonLexer


class ToonDecoder:
    """Official TOON v2.0 decoder.

    Decodes TOON format strings to Python data structures with full
    spec compliance including:
    - Empty documents → {}
    - Three root forms (object, array, primitive)
    - Three array forms (inline, tabular, list)
    - Strict validation mode
    - Proper escape sequence handling
    """

    def __init__(self, options: ToonDecodeOptions | None = None) -> None:
        """Initialize decoder.

        Args:
            options: Decoding options (uses defaults if None)
        """
        self.options = options or ToonDecodeOptions()
        self.tokens: list[Token] = []
        self.pos = 0

    def decode(self, data_str: str) -> ToonValue:
        """Decode TOON string to Python data structure.

        Args:
            data_str: TOON formatted string

        Returns:
            Python data structure (dict, list, or primitive)

        Raises:
            DecodingError: If decoding fails

        Examples:
            >>> decoder = ToonDecoder()
            >>> decoder.decode("name: Alice\\nage: 30")
            {'name': 'Alice', 'age': 30}
            >>> decoder.decode("")
            {}
            >>> decoder.decode("[3]: 1,2,3")
            [1, 2, 3]
        """
        try:
            # Handle empty documents → {}
            if not data_str or not data_str.strip():
                return {}

            # Tokenize input
            lexer = ToonLexer(data_str, indent_size=2)
            self.tokens = lexer.tokenize()
            self.pos = 0

            # Parse root based on first token
            root_form = self._detect_root_form()

            if root_form == RootForm.ARRAY:
                return self._parse_root_array()
            elif root_form == RootForm.PRIMITIVE:
                return self._parse_root_primitive()
            else:  # RootForm.OBJECT
                return self._parse_root_object()

        except (ValueError, IndexError, KeyError) as e:
            raise DecodingError(f"Failed to decode TOON data: {e}") from e

    def _detect_root_form(self) -> RootForm:
        """Detect the form of root document.

        Returns:
            RootForm enum value
        """
        # Skip indent tokens
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.INDENT:
            self.pos += 1

        if self.pos >= len(self.tokens):
            return RootForm.OBJECT

        first_token = self.tokens[self.pos]

        # Array header at root: [N]: or [N]{fields}:
        if first_token.type == TokenType.ARRAY_START:
            return RootForm.ARRAY

        # Check if it's a key:value pair (object) or just a value (primitive)
        # Look ahead for colon - it might be after an array header like: key[N]:
        lookahead_pos = self.pos + 1
        while lookahead_pos < len(self.tokens):
            look_token = self.tokens[lookahead_pos]

            # Found colon - it's an object
            if look_token.type == TokenType.COLON:
                return RootForm.OBJECT

            # Array markers can appear between key and colon
            if look_token.type in (TokenType.ARRAY_START, TokenType.ARRAY_END,
                                  TokenType.BRACE_START, TokenType.BRACE_END,
                                  TokenType.NUMBER, TokenType.COMMA, TokenType.IDENTIFIER):
                lookahead_pos += 1
                continue

            # Hit something else - likely a primitive
            break

        # Single primitive value
        return RootForm.PRIMITIVE

    def _parse_root_object(self) -> dict[str, Any]:
        """Parse root-level object.

        Returns:
            Dictionary
        """
        result: dict[str, Any] = {}

        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            # End of input
            if token.type in (TokenType.EOF, TokenType.DEDENT):
                break

            # Skip newlines and indents at root level
            if token.type in (TokenType.NEWLINE, TokenType.INDENT):
                self.pos += 1
                continue

            # Parse key-value pair
            if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                key = str(token.value)
                self.pos += 1

                # Check if value is an array (key[N]: syntax)
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.ARRAY_START:
                    # Array value - parse array header and content
                    value = self._parse_value(depth=0)
                    result[key] = value
                else:
                    # Regular value - expect colon
                    if self.pos >= len(self.tokens) or self.tokens[self.pos].type != TokenType.COLON:
                        raise DecodingError(f"Expected ':' after key '{key}'")
                    self.pos += 1

                    # Parse value
                    value = self._parse_value(depth=0)
                    result[key] = value
            else:
                self.pos += 1

        return result

    def _parse_root_array(self) -> list[Any]:
        """Parse root-level array.

        Returns:
            List
        """
        # Parse array header
        header = self._parse_array_header()

        # Parse array content based on form
        if header["form"] == ArrayForm.INLINE:
            return self._parse_inline_array(header)
        elif header["form"] == ArrayForm.TABULAR:
            return self._parse_tabular_array(header)
        else:  # ArrayForm.LIST
            return self._parse_list_array(header, depth=0)

    def _parse_root_primitive(self) -> Any:
        """Parse root-level primitive value.

        Returns:
            Primitive value
        """
        token = self.tokens[self.pos]
        return self._token_to_value(token)

    def _parse_value(self, depth: int) -> Any:
        """Parse a value (primitive, object, or array).

        Args:
            depth: Current nesting depth

        Returns:
            Parsed value
        """
        # Skip whitespace/newlines
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE:
            self.pos += 1

        if self.pos >= len(self.tokens):
            return None

        token = self.tokens[self.pos]

        # Array: key[N]: or key[N]{fields}:
        if token.type == TokenType.ARRAY_START:
            header = self._parse_array_header()
            if header["form"] == ArrayForm.INLINE:
                return self._parse_inline_array(header)
            elif header["form"] == ArrayForm.TABULAR:
                return self._parse_tabular_array(header)
            else:
                return self._parse_list_array(header, depth)

        # Nested object (current token is INDENT after skipping newlines)
        if token.type == TokenType.INDENT:
            return self._parse_nested_object(depth)

        # Check for inline object: identifier followed by colon
        # This handles cases like "- key: value" in list arrays
        if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
            # Look ahead for colon
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.COLON:
                # This is an inline object, parse it
                return self._parse_inline_object(depth)

        # Primitive value
        value = self._token_to_value(token)
        self.pos += 1
        return value

    def _parse_nested_object(self, depth: int) -> dict[str, Any]:
        """Parse nested object.

        Args:
            depth: Current nesting depth

        Returns:
            Dictionary
        """
        result: dict[str, Any] = {}

        # Skip to indented content
        self.pos += 1  # Skip INDENT token

        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            # End of nested object
            if token.type == TokenType.DEDENT:
                self.pos += 1
                break

            if token.type == TokenType.EOF:
                break

            # Skip newlines
            if token.type == TokenType.NEWLINE:
                self.pos += 1
                continue

            # Parse key-value pair
            if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                key = str(token.value)
                self.pos += 1

                # Check if value is an array (key[N]: syntax)
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.ARRAY_START:
                    # Array value - parse array header and content
                    value = self._parse_value(depth + 1)
                    result[key] = value
                else:
                    # Regular value - expect colon
                    if self.pos >= len(self.tokens) or self.tokens[self.pos].type != TokenType.COLON:
                        raise DecodingError(f"Expected ':' after key '{key}'")
                    self.pos += 1

                    # Parse value
                    value = self._parse_value(depth + 1)
                    result[key] = value
            else:
                self.pos += 1

        return result

    def _parse_inline_object(self, depth: int) -> dict[str, Any]:
        """Parse inline object (first field on dash line, remaining at depth+1).

        Per TOON spec: "First field on the hyphen line: - key: value
        Remaining fields continue at depth +1"

        Args:
            depth: Current nesting depth

        Returns:
            Dictionary
        """
        result: dict[str, Any] = {}

        # Parse first field on the current line
        token = self.tokens[self.pos]
        if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
            key = str(token.value)
            self.pos += 1

            # Expect colon
            if self.pos >= len(self.tokens) or self.tokens[self.pos].type != TokenType.COLON:
                raise DecodingError(f"Expected ':' after key '{key}' in inline object")
            self.pos += 1

            # Parse value (primitive only on dash line)
            if self.pos >= len(self.tokens) or self.tokens[self.pos].type in (TokenType.NEWLINE, TokenType.EOF):
                result[key] = None
            else:
                value = self._token_to_value(self.tokens[self.pos])
                result[key] = value
                self.pos += 1

        # Skip newline if present
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE:
            self.pos += 1

        # Check for additional fields at depth+1 (INDENT)
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.INDENT:
            self.pos += 1  # Skip INDENT

            # Parse remaining fields at this indentation level
            while self.pos < len(self.tokens):
                token = self.tokens[self.pos]

                # End of object - dedent or EOF
                if token.type == TokenType.DEDENT:
                    self.pos += 1
                    break

                if token.type == TokenType.EOF:
                    break

                # Skip newlines
                if token.type == TokenType.NEWLINE:
                    self.pos += 1
                    continue

                # Another dash means next list item
                if token.type == TokenType.DASH:
                    break

                # Parse key-value pair
                if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                    key = str(token.value)
                    self.pos += 1

                    # Check if value is an array (key[N]: syntax)
                    if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.ARRAY_START:
                        # Array value - parse array header and content
                        value = self._parse_value(depth + 1)
                        result[key] = value
                    else:
                        # Regular value - expect colon
                        if self.pos >= len(self.tokens) or self.tokens[self.pos].type != TokenType.COLON:
                            raise DecodingError(f"Expected ':' after key '{key}'")
                        self.pos += 1

                        # Parse value
                        value = self._parse_value(depth + 1)
                        result[key] = value
                else:
                    self.pos += 1

        return result

    def _parse_array_header(self) -> dict[str, Any]:
        """Parse array header: [N] or [N]{fields}

        Returns:
            Dictionary with header info: {length, fields, form, delimiter}
        """
        # Expect [
        if self.tokens[self.pos].type != TokenType.ARRAY_START:
            raise DecodingError("Expected '[' for array header")
        self.pos += 1

        # Parse length
        length_token = self.tokens[self.pos]
        if length_token.type != TokenType.NUMBER:
            raise DecodingError("Expected array length number")
        length = int(length_token.value)  # type: ignore
        self.pos += 1

        # Check for delimiter marker
        delimiter = Delimiter.COMMA
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token.type == TokenType.IDENTIFIER:
                delimiter_str = str(token.value)
                if delimiter_str == "\t":
                    delimiter = Delimiter.TAB
                elif delimiter_str == "|":
                    delimiter = Delimiter.PIPE
                self.pos += 1

        # Expect ]
        if self.tokens[self.pos].type != TokenType.ARRAY_END:
            raise DecodingError("Expected ']' in array header")
        self.pos += 1

        # Check for field spec {field1,field2}
        fields = None
        form = ArrayForm.LIST  # Default

        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.BRACE_START:
            # Tabular array
            form = ArrayForm.TABULAR
            self.pos += 1  # Skip {

            fields = []
            while self.pos < len(self.tokens):
                token = self.tokens[self.pos]

                if token.type == TokenType.BRACE_END:
                    self.pos += 1
                    break

                if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                    fields.append(str(token.value))
                    self.pos += 1

                # Skip commas
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.COMMA:
                    self.pos += 1

        # Expect :
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.COLON:
            self.pos += 1

        # Determine form based on what follows
        if self.pos < len(self.tokens):
            next_token = self.tokens[self.pos]

            # Inline array: values on same line
            if next_token.type not in (TokenType.NEWLINE, TokenType.EOF):
                form = ArrayForm.INLINE

        return {
            "length": length,
            "fields": fields,
            "form": form,
            "delimiter": delimiter,
        }

    def _parse_inline_array(self, header: dict[str, Any]) -> list[Any]:
        """Parse inline array: [3]: 1,2,3

        Args:
            header: Array header info

        Returns:
            List of values
        """
        values: list[Any] = []
        delimiter = header["delimiter"]

        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            if token.type in (TokenType.NEWLINE, TokenType.EOF):
                break

            # Skip delimiter tokens
            if token.type == TokenType.COMMA:
                self.pos += 1
                continue

            # Parse value
            value = self._token_to_value(token)
            values.append(value)
            self.pos += 1

        # Validate length in strict mode
        if self.options.strict and len(values) != header["length"]:
            raise ValidationError(
                f"Array length mismatch: declared {header['length']}, got {len(values)}"
            )

        return values

    def _parse_tabular_array(self, header: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse tabular array: [N]{fields}: with data rows

        Args:
            header: Array header info

        Returns:
            List of dictionaries
        """
        result: list[dict[str, Any]] = []
        fields = header["fields"]
        delimiter = header["delimiter"]

        if not fields:
            raise DecodingError("Tabular array must have fields")

        # Skip newline after header
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE:
            self.pos += 1

        # Skip single INDENT token at start of block
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.INDENT:
            self.pos += 1

        # Parse data rows
        for _ in range(header["length"]):
            # Parse row values
            row_values: list[Any] = []
            while self.pos < len(self.tokens):
                token = self.tokens[self.pos]

                if token.type in (TokenType.NEWLINE, TokenType.EOF, TokenType.DEDENT):
                    break

                # Skip delimiter tokens
                if token.type == TokenType.COMMA:
                    self.pos += 1
                    continue

                # Parse value
                value = self._token_to_value(token)
                row_values.append(value)
                self.pos += 1

            # Create dict from fields and values
            if len(row_values) != len(fields):
                if self.options.strict:
                    raise ValidationError(
                        f"Row width mismatch: expected {len(fields)}, got {len(row_values)}"
                    )

            row_dict = dict(zip(fields, row_values))
            result.append(row_dict)

            # Skip newline
            if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE:
                self.pos += 1

        # Skip DEDENT token at end of block if present
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.DEDENT:
            self.pos += 1

        return result

    def _parse_list_array(self, header: dict[str, Any], depth: int) -> list[Any]:
        """Parse list array: [N]: with - items

        Args:
            header: Array header info
            depth: Current depth

        Returns:
            List of values
        """
        values: list[Any] = []

        # Skip newline after header
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE:
            self.pos += 1

        # Parse list items
        while len(values) < header["length"] and self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            if token.type == TokenType.EOF:
                break

            # Skip indents/dedents/newlines
            if token.type in (TokenType.INDENT, TokenType.NEWLINE):
                self.pos += 1
                continue

            if token.type == TokenType.DEDENT:
                break

            # List item marker: -
            if token.type == TokenType.DASH:
                self.pos += 1

                # Parse item value
                item_value = self._parse_value(depth + 1)
                values.append(item_value)
            else:
                self.pos += 1

        # Validate length in strict mode
        if self.options.strict and len(values) != header["length"]:
            raise ValidationError(
                f"Array length mismatch: declared {header['length']}, got {len(values)}"
            )

        return values

    def _token_to_value(self, token: Token) -> Any:
        """Convert token to Python value.

        Args:
            token: Token to convert

        Returns:
            Python value
        """
        if token.type == TokenType.NULL:
            return None
        elif token.type == TokenType.BOOLEAN:
            return token.value
        elif token.type == TokenType.NUMBER:
            return token.value
        elif token.type in (TokenType.STRING, TokenType.QUOTED_STRING):
            return token.value
        elif token.type == TokenType.IDENTIFIER:
            # Unquoted identifier - type inference
            if self.options.type_inference:
                value_str = str(token.value)
                # Try to infer type
                if value_str == "null":
                    return None
                elif value_str == "true":
                    return True
                elif value_str == "false":
                    return False
                # Try number
                try:
                    if "." in value_str:
                        return float(value_str)
                    else:
                        return int(value_str)
                except ValueError:
                    pass
            return token.value
        else:
            return token.value


def decode(data_str: str, options: ToonDecodeOptions | None = None) -> ToonValue:
    """Convenience function to decode TOON format.

    Args:
        data_str: TOON string
        options: Decode options

    Returns:
        Python data structure

    Examples:
        >>> decode("name: Alice")
        {'name': 'Alice'}
        >>> decode("")
        {}
        >>> decode("[2]: 1,2")
        [1, 2]
    """
    decoder = ToonDecoder(options)
    return decoder.decode(data_str)
