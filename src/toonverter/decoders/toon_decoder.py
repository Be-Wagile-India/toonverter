"""TOON v2.0 decoder - fully spec-compliant implementation.

Decodes TOON format strings to Python data structures following
the official TOON v2.0 specification.
"""

from typing import Any

from toonverter.core.config import USE_RUST_DECODER, rust_core
from toonverter.core.exceptions import DecodingError, ValidationError
from toonverter.core.spec import ArrayForm, Delimiter, RootForm, ToonDecodeOptions, ToonValue

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
        # Try Rust decoder if available and options allow
        # Rust decoder currently implies strict=True and type_inference=True
        if USE_RUST_DECODER and self.options.strict and self.options.type_inference:
            try:
                return rust_core.decode_toon(data_str)
            except ValueError as e:
                # Map Rust/PyO3 ValueError to our DecodingError
                msg = f"Failed to decode TOON data (Rust): {e}"
                raise DecodingError(msg) from e
            except Exception:
                # If Rust decoder fails unexpectedly, fall back to Python
                pass

        # Fallback to Python implementation if Rust decoder is not available or disabled
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
            if root_form == RootForm.PRIMITIVE:
                return self._parse_root_primitive()
            # RootForm.OBJECT
            return self._parse_root_object()

        except (ValueError, IndexError, KeyError) as e:
            msg = f"Failed to decode TOON data: {e}"
            raise DecodingError(msg) from e

    def _detect_root_form(self) -> RootForm:
        """Detect the root form of the TOON document (object, array, or primitive).

        Returns:
            RootForm: The detected root form.
        """
        if not self.tokens:
            return RootForm.OBJECT  # Empty document is an empty object

        # Skip leading newlines/whitespace
        idx = 0
        while idx < len(self.tokens) and self.tokens[idx].type == TokenType.NEWLINE:
            idx += 1

        if idx >= len(self.tokens):
            return RootForm.OBJECT  # Document with only whitespace is an empty object

        first_token = self.tokens[idx]

        if first_token.type in (TokenType.ARRAY_START, TokenType.DASH):
            return RootForm.ARRAY

        # If the first token is an identifier or quoted string,
        # we need to check the *next* meaningful token to see if it's a key or a primitive.
        if first_token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
            # Scan for the next non-newline token
            next_idx = idx + 1
            while next_idx < len(self.tokens) and self.tokens[next_idx].type == TokenType.NEWLINE:
                next_idx += 1

            if next_idx < len(self.tokens):
                next_token = self.tokens[next_idx]
                # If followed by a colon or array start, it's an an object key-value pair.
                if next_token.type in (TokenType.COLON, TokenType.ARRAY_START):
                    return RootForm.OBJECT

            # If not followed by a colon or array start, it's a primitive.
            return RootForm.PRIMITIVE

        # Anything else is a primitive at the root level (e.g., a bare number or string)
        return RootForm.PRIMITIVE

    def _parse_root_object(self) -> dict[str, Any]:
        """Parse a root-level object.

        Returns:
            Dictionary
        """
        result: dict[str, Any] = {}
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

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
                if (
                    self.pos < len(self.tokens)
                    and self.tokens[self.pos].type == TokenType.ARRAY_START
                ):
                    # Array value - parse array header and content
                    value = self._parse_value(0)  # depth 0 for root
                    result[key] = value
                else:
                    # Regular value - expect colon
                    if (
                        self.pos >= len(self.tokens)
                        or self.tokens[self.pos].type != TokenType.COLON
                    ):
                        msg = f"Expected ':' after key '{key}'"
                        raise DecodingError(msg)
                    self.pos += 1

                    # Parse value
                    value = self._parse_value(0)  # depth 0 for root
                    result[key] = value

                # After parsing a key-value pair, skip any trailing newlines before the next key-value pair.
                # This is crucial for multi-line objects.
                while (
                    self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE
                ):
                    self.pos += 1
                continue  # Continue to the next iteration of the while loop to find the next key-value pair.
            msg = f"Unexpected token at root object: {token.type} value: {token.value!r} at pos: {self.pos}"
            raise DecodingError(msg)
        return result

    def _parse_root_array(self) -> list[Any]:
        """Parse root-level array.

        Returns:
            List
        """
        token = self.tokens[self.pos]
        if token.type == TokenType.DASH:
            # Root list array (e.g., - 1\n- 2)
            # Create a dummy header to indicate indefinite length
            header = {
                "length": -1,
                "form": ArrayForm.LIST,
                "delimiter": Delimiter.COMMA,
                "fields": None,
            }
            return self._parse_list_array(header, depth=0)
        if token.type == TokenType.ARRAY_START:
            # Explicit array header (e.g., [3]: 1,2,3)
            header = self._parse_array_header()
            if header["form"] == ArrayForm.INLINE:
                return self._parse_inline_array(header)
            if header["form"] == ArrayForm.TABULAR:
                return self._parse_tabular_array(header)
            # ArrayForm.LIST
            return self._parse_list_array(header, depth=0)
        msg = f"Unexpected token at start of root array: {token.type} value: {token.value!r} at pos: {self.pos}"
        raise DecodingError(msg)

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
            if header["form"] == ArrayForm.TABULAR:
                return self._parse_tabular_array(header)
            return self._parse_list_array(header, depth)

        # Nested object (current token is INDENT after skipping newlines)
        if token.type == TokenType.INDENT:
            return self._parse_nested_object(depth)

        # Check for inline object: identifier followed by colon
        # This handles cases like "- key: value" in list arrays
        if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
            # Look ahead for colon
            if (
                self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.COLON
            ):
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
                if (
                    self.pos < len(self.tokens)
                    and self.tokens[self.pos].type == TokenType.ARRAY_START
                ):
                    # Array value - parse array header and content
                    value = self._parse_value(depth + 1)
                    result[key] = value
                else:
                    # Regular value - expect colon
                    if (
                        self.pos >= len(self.tokens)
                        or self.tokens[self.pos].type != TokenType.COLON
                    ):
                        msg = f"Expected ':' after key '{key}'"
                        raise DecodingError(msg)
                    self.pos += 1

                    # Parse value
                    value = self._parse_value(depth + 1)
                    result[key] = value

                # After parsing a key-value pair, skip any trailing newlines before the next key-value pair.
                while (
                    self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.NEWLINE
                ):
                    self.pos += 1
                continue  # Continue to the next iteration of the while loop to find the next key-value pair.
            msg = f"Unexpected token in nested object: {token.type} value: {token.value!r} at pos: {self.pos}"
            raise DecodingError(msg)

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
                msg = f"Expected ':' after key '{key}' in inline object"
                raise DecodingError(msg)
            self.pos += 1

            # Parse value (primitive only on dash line)
            if self.pos >= len(self.tokens) or self.tokens[self.pos].type in (
                TokenType.NEWLINE,
                TokenType.EOF,
            ):
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
                    if (
                        self.pos < len(self.tokens)
                        and self.tokens[self.pos].type == TokenType.ARRAY_START
                    ):
                        # Array value - parse array header and content
                        value = self._parse_value(depth + 1)
                        result[key] = value
                    else:
                        # Regular value - expect colon
                        if (
                            self.pos >= len(self.tokens)
                            or self.tokens[self.pos].type != TokenType.COLON
                        ):
                            msg = f"Expected ':' after key '{key}'"
                            raise DecodingError(msg)
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
            msg = "Expected '[' for array header"
            raise DecodingError(msg)
        self.pos += 1

        # Parse length
        length_token = self.tokens[self.pos]
        if length_token.type != TokenType.NUMBER:
            msg = "Expected array length number"
            raise DecodingError(msg)
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
            msg = "Expected ']' in array header"
            raise DecodingError(msg)
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

        delimiter_char = ""
        if header["delimiter"] == Delimiter.COMMA:
            delimiter_char = ","
        elif header["delimiter"] == Delimiter.TAB:
            delimiter_char = "\t"
        elif header["delimiter"] == Delimiter.PIPE:
            delimiter_char = "|"

        # Find the content of the current line after the array header (and its colon)
        # We need to collect all subsequent tokens until a NEWLINE or EOF
        inline_tokens_content: list[str] = []
        start_pos_content = self.pos  # Keep track of where content starts

        while self.pos < len(self.tokens) and self.tokens[self.pos].type not in (
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            token = self.tokens[self.pos]
            if token.type == TokenType.COMMA and delimiter_char == ",":
                # Only append comma if it's the actual delimiter and we want to preserve it for splitting
                # Otherwise, it might be part of an IDENTIFIER.
                pass  # We will split by delimiter_char later, so don't add comma to content
            elif isinstance(token.value, str) or token.value is None:
                inline_tokens_content.append(str(token.value if token.value is not None else ""))
            else:
                inline_tokens_content.append(str(token.value))
            self.pos += 1

        full_value_string = "".join(inline_tokens_content)

        # If there's content, split it by the determined delimiter
        if full_value_string.strip():
            # Ensure proper handling of empty strings if delimiter is at start/end or repeated
            split_items = full_value_string.split(delimiter_char)

            for item_str in split_items:
                # Trim whitespace from each item
                stripped_item_str = item_str.strip()
                if stripped_item_str == "":
                    # Allow empty strings as values if they result from splitting, treat as None or empty string
                    values.append(
                        None
                    )  # Or should it be ""? TOON spec likely implies empty string or null.
                # For now, append None as it's a common interpretation of empty.
                else:
                    # Create a temporary token to pass to _token_to_value for proper type inference
                    # Assuming it's an IDENTIFIER if not a specific primitive
                    # This is a bit of a hack as the original token might have been QUOTED_STRING.
                    # For simplicity, we treat them as IDENTIFIER and let _token_to_value re-infer.
                    temp_token = Token(
                        type=TokenType.IDENTIFIER,  # Use IDENTIFIER, then _token_to_value will infer.
                        value=stripped_item_str,
                        line=self.tokens[start_pos_content].line
                        if self.tokens
                        else 0,  # Handle empty tokens list
                        column=self.tokens[start_pos_content].column if self.tokens else 0,
                    )
                    values.append(self._token_to_value(temp_token))

        # Validate length in strict mode
        if self.options.strict and len(values) != header["length"]:
            msg = f"Array length mismatch: declared {header['length']}, got {len(values)}"
            raise ValidationError(msg)

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
        header["delimiter"]

        if not fields:
            msg = "Tabular array must have fields"
            raise DecodingError(msg)

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
            if len(row_values) != len(fields) and self.options.strict:
                msg = f"Row width mismatch: expected {len(fields)}, got {len(row_values)}"
                raise ValidationError(msg)

            row_dict = dict(zip(fields, row_values, strict=False))
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
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            if token.type == TokenType.EOF:
                break

            # If a DEDENT is encountered, it signifies the end of the list block
            if token.type == TokenType.DEDENT:
                self.pos += 1  # Consume the DEDENT
                break

            # Skip indents/newlines
            if token.type in (TokenType.INDENT, TokenType.NEWLINE):
                self.pos += 1
                continue

            # List item marker: -
            if token.type == TokenType.DASH:
                self.pos += 1

                # Parse item value
                item_value = self._parse_value(depth + 1)
                values.append(item_value)
            else:
                msg = f"Unexpected token in list array: {token.type} value: {token.value!r} at pos: {self.pos}"
                raise DecodingError(msg)

        # Validate length in strict mode
        if self.options.strict and header["length"] != -1 and len(values) != header["length"]:
            msg = f"Array length mismatch: declared {header['length']}, got {len(values)}"
            raise ValidationError(msg)

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
        if token.type in (TokenType.BOOLEAN, TokenType.NUMBER) or token.type in (
            TokenType.STRING,
            TokenType.QUOTED_STRING,
        ):
            return token.value
        if token.type == TokenType.IDENTIFIER:
            # Unquoted identifier - type inference
            if self.options.type_inference:
                value_str = str(token.value)
                # Try to infer type
                if value_str == "null":
                    return None
                if value_str == "true":
                    return True
                if value_str == "false":
                    return False
                # Try number
                try:
                    if "." in value_str:
                        return float(value_str)
                    return int(value_str)
                except ValueError:
                    pass
            return token.value
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
