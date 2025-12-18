"""TOON v2.0 decoder - fully spec-compliant implementation.

Decodes TOON format strings to Python data structures following
the official TOON v2.0 specification.
"""

from typing import Any

from toonverter.core.config import RECURSION_DEPTH_LIMIT, USE_RUST_DECODER, rust_core
from toonverter.core.exceptions import DecodingError, ValidationError
from toonverter.core.spec import (
    ArrayForm,
    Delimiter,
    RootForm,
    ToonDecodeOptions,
    ToonValue,
)

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

    def _skip_ignored_tokens(self) -> None:
        while self.pos < len(self.tokens) and self.tokens[self.pos].type in (
            TokenType.NEWLINE,
            TokenType.COMMENT,
        ):
            self.pos += 1

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
                return rust_core.decode_toon(data_str, self.options.indent_size)
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
            lexer = ToonLexer(data_str, indent_size=self.options.indent_size)
            self.tokens = list(lexer.tokenize())
            self.pos = 0

            # Parse root based on first token
            value: ToonValue
            if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.BRACE_START:
                value = self._parse_braced_object(0)
            else:
                root_form = self._detect_root_form()

                if root_form == RootForm.ARRAY:
                    value = self._parse_root_array()
                elif root_form == RootForm.PRIMITIVE:
                    value = self._parse_root_primitive()
                else:
                    # RootForm.OBJECT
                    value = self._parse_root_object()

            # Check for extra tokens (EOF check)
            self._skip_ignored_tokens()
            # Allow trailing DEDENTs (from lexer balancing)
            while self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.DEDENT:
                self.pos += 1
                self._skip_ignored_tokens()

            if self.pos < len(self.tokens) and self.tokens[self.pos].type != TokenType.EOF:
                msg = f"Extra tokens found after root element. Token: {self.tokens[self.pos]}"
                raise DecodingError(msg)

            return value

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

        self._skip_ignored_tokens()  # self.pos now points to the first non-ignored token
        if self.pos >= len(self.tokens):
            return RootForm.OBJECT

        first = self.tokens[self.pos]

        if first.type == TokenType.INDENT:
            return RootForm.OBJECT

        if first.type in (TokenType.ARRAY_START, TokenType.DASH):
            return RootForm.ARRAY

        # If the first token is an identifier or quoted string,
        # we need to check the *next* meaningful token to see if it's a key or a primitive.
        if first.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
            # Scan for the next non-newline/non-comment token
            temp = self.pos + 1
            while temp < len(self.tokens) and self.tokens[temp].type in (
                TokenType.NEWLINE,
                TokenType.COMMENT,
            ):
                temp += 1

            if temp < len(self.tokens):
                nt = self.tokens[temp]
                # If followed by EOF, it's a single primitive
                if nt.type == TokenType.EOF:
                    return RootForm.PRIMITIVE
                # If followed by anything else (colon, array start, or unexpected token),
                # treat as object so parser can enforce object structure (or fail with specific object error)
                return RootForm.OBJECT

            # If not followed by anything (shouldn't happen with EOF check above), treat as primitive
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
            self._skip_ignored_tokens()

            if self.pos >= len(self.tokens):
                break

            token = self.tokens[self.pos]

            if token.type in (TokenType.EOF, TokenType.DEDENT):
                break

            if token.type in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                key = str(token.value)
                self.pos += 1

                # Check if value is an array (key[N]: syntax)
                if (
                    self.pos < len(self.tokens)
                    and self.tokens[self.pos].type == TokenType.ARRAY_START
                ):
                    value = self._parse_value(0)  # depth 0 for root
                    result[key] = value
                else:  # This is the block that *should* raise the error.
                    # Regular value - expect colon
                    if (
                        self.pos >= len(self.tokens)
                        or self.tokens[self.pos].type != TokenType.COLON
                    ):
                        msg = f"Expected ':' after key '{key}'"
                        raise DecodingError(msg)
                    self.pos += 1  # ONLY ADVANCE IF COLON WAS FOUND

                    # Parse value
                    value = self._parse_value(0)  # depth 0 for root
                    result[key] = value

                # After parsing a key-value pair, skip any trailing newlines before the next key-value pair.
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
                "length": None,
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
        self.pos += 1
        return self._token_to_value(token)

    def _parse_value(self, depth: int) -> Any:
        """Parse a value (primitive, object, or array).

        Args:
            depth: Current nesting depth

        Returns:
            Parsed value
        """
        if depth > RECURSION_DEPTH_LIMIT:
            msg = f"Maximum recursion depth ({RECURSION_DEPTH_LIMIT}) exceeded"
            raise DecodingError(msg)

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

        # Braced object: {key: value, ...}
        if token.type == TokenType.BRACE_START:
            return self._parse_braced_object(depth)

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

    def _parse_braced_object(self, depth: int) -> dict[str, Any]:
        """Parse brace-enclosed object: {key: value, ...}

        Args:
            depth: Current nesting depth

        Returns:
            Dictionary
        """
        result: dict[str, Any] = {}
        self.pos += 1  # Skip {

        while self.pos < len(self.tokens):
            self._skip_ignored_tokens()

            token = self.tokens[self.pos]
            if token.type == TokenType.BRACE_END:
                self.pos += 1
                break

            # Parse key
            if token.type not in (TokenType.IDENTIFIER, TokenType.QUOTED_STRING):
                msg = f"Expected key in braced object, found {token.type}"
                raise DecodingError(msg)

            key = str(token.value)
            self.pos += 1

            self._skip_ignored_tokens()

            # Expect colon
            if self.pos >= len(self.tokens) or self.tokens[self.pos].type != TokenType.COLON:
                msg = f"Expected ':' after key '{key}' in braced object"
                raise DecodingError(msg)
            self.pos += 1

            self._skip_ignored_tokens()

            # Parse value
            value = self._parse_value(depth + 1)
            result[key] = value

            self._skip_ignored_tokens()

            # Check for comma or end
            if self.pos < len(self.tokens):
                token = self.tokens[self.pos]
                if token.type == TokenType.COMMA:
                    self.pos += 1
                elif token.type == TokenType.BRACE_END:
                    pass  # Loop will handle it
                else:
                    msg = f"Expected ',' or '}}' in braced object, found {token.type}"
                    raise DecodingError(msg)

        return result

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
                        error_msg = f"Expected ':' after key '{key}'"
                        raise DecodingError(error_msg)
                    self.pos += 1  # ONLY ADVANCE IF COLON WAS FOUND
                    self._skip_ignored_tokens()

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
                error_msg = f"Expected ':' after key '{key}' in inline object"
                raise DecodingError(error_msg)
            self.pos += 1  # ONLY ADVANCE IF COLON WAS FOUND

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
        length: int | None = None
        if length_token.type == TokenType.NUMBER:
            length = int(length_token.value)  # type: ignore
            self.pos += 1
        elif length_token.type == TokenType.STAR:
            length = None
            self.pos += 1
        else:
            msg = "Expected array length number or '*'"
            raise DecodingError(msg)

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

        self._skip_ignored_tokens()  # Consume newlines/comments after the colon

        # Determine form based on what follows
        if self.pos < len(self.tokens):
            nt = self.tokens[self.pos]
            if nt.type not in (
                TokenType.NEWLINE,
                TokenType.EOF,
                TokenType.COMMENT,
                TokenType.INDENT,
                TokenType.DEDENT,
                TokenType.DASH,
            ):
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
        length = header["length"]

        # Delimiter handling logic

        # We need to handle custom delimiters if specified.
        # Standard lexer produces COMMAs.
        # If the delimiter is something else (e.g. PIPE), the lexer might produce it as an IDENTIFIER "|".
        # Or if it's TAB, it might be consumed as whitespace unless quoted/handled?
        # The Python lexer treats tabs as whitespace. If TAB is delimiter, it might be problematic unless we rely on implicit separation?
        # But let's assume default COMMA for now or handle PIPE if lexer produces it.
        # If header["delimiter"] is PIPE, we expect to see "|" tokens (Identifiers) instead of COMMAs.

        target_delimiter = header["delimiter"]

        for i in range(length):
            # If not the first item, expect delimiter or rely on previous parsing position
            if i > 0:
                self._skip_ignored_tokens()
                if self.pos < len(self.tokens):
                    token = self.tokens[self.pos]

                    if target_delimiter == Delimiter.COMMA:
                        if token.type == TokenType.COMMA:
                            self.pos += 1
                    elif target_delimiter == Delimiter.PIPE:
                        if token.type == TokenType.IDENTIFIER and str(token.value) == "|":
                            self.pos += 1

            # Parse value
            # Check if we are at a delimiter or end, implying empty value
            is_empty = False
            if self.pos < len(self.tokens):
                token = self.tokens[self.pos]
                if (
                    (target_delimiter == Delimiter.COMMA and token.type == TokenType.COMMA)
                    or (
                        target_delimiter == Delimiter.PIPE
                        and token.type == TokenType.IDENTIFIER
                        and str(token.value) == "|"
                    )
                    or token.type in (TokenType.NEWLINE, TokenType.EOF, TokenType.DEDENT)
                ):
                    is_empty = True
            else:
                is_empty = True

            val = None if is_empty else self._parse_value(0)
            values.append(val)

        return values

    def _parse_tabular_array(self, header: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse tabular array: [N]{fields}: with data rows

        Args:
            header: Array header info

        Returns:
            List of dictionaries
        """
        if not header["fields"]:
            error_msg = "Tabular array must have fields"
            raise DecodingError(error_msg)

        fields = header["fields"]
        result: list[dict[str, Any]] = []

        self._skip_ignored_tokens()

        # Consume initial INDENT if present. This is the block indent for the tabular array itself.
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.INDENT:
            self.pos += 1
            self._skip_ignored_tokens()

        # Parse data rows
        for _ in range(header["length"]):
            self._skip_ignored_tokens()

            if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.DEDENT:
                break  # Premature DEDENT means end of array before expected length

            row = {}
            actual_values_parsed = 0
            for i, f in enumerate(fields):
                if i > 0:  # If not the first field
                    # Expect a comma between values
                    if (
                        self.pos < len(self.tokens)
                        and self.tokens[self.pos].type == TokenType.COMMA
                    ):
                        self.pos += 1
                        self._skip_ignored_tokens()
                    elif self.options.strict:
                        # If strict mode and no comma, check if we are at the end of the values for this row.
                        # If the current token is a NEWLINE, EOF, or DEDENT, it means the row ended prematurely.
                        # The ValidationError for row width mismatch will handle this later.
                        current_token_type = self.tokens[self.pos].type
                        if current_token_type not in (
                            TokenType.NEWLINE,
                            TokenType.EOF,
                            TokenType.DEDENT,
                        ):
                            error_msg = f"Expected ',' before field '{f}' value in tabular array. Found: {self.tokens[self.pos]}"
                            raise DecodingError(error_msg)
                        # Fall through to value parsing if row ended prematurely (ValidationError will catch)

                # Check if there's a value to parse
                if self.pos < len(self.tokens) and self.tokens[self.pos].type not in (
                    TokenType.NEWLINE,
                    TokenType.EOF,
                    TokenType.DEDENT,
                    TokenType.COMMA,
                ):
                    row[f] = self._parse_value(0)
                    actual_values_parsed += 1
                elif self.options.strict:
                    # In strict mode, if we are at the end of the row, allow it to fall through
                    # so the row width check can handle it (raising ValidationError).
                    # Only raise DecodingError if we are NOT at the end of the row (e.g. adjacent commas).
                    if self.pos < len(self.tokens) and self.tokens[self.pos].type in (
                        TokenType.NEWLINE,
                        TokenType.EOF,
                        TokenType.DEDENT,
                    ):
                        row[f] = None
                    else:
                        error_msg = f"Missing value for field '{f}' in tabular array row"
                        raise DecodingError(error_msg)
                else:  # Non-strict mode, assign None for missing values
                    row[f] = None

            # After trying to parse all fields in a row, validate the actual count.
            if self.options.strict and actual_values_parsed != len(fields):
                error_msg = f"Row width mismatch: declared {len(fields)} fields, got {actual_values_parsed} values"
                raise ValidationError(error_msg)

            result.append(row)
            self._skip_ignored_tokens()

        # Skip DEDENT token at end of block if present
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.DEDENT:
            self.pos += 1

        return result

    def _parse_list_array(self, header: dict[str, Any], depth: int) -> list[Any]:
        values: list[Any] = []

        self._skip_ignored_tokens()

        # Consume initial INDENT if present. This is the block indent for the list itself.
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == TokenType.INDENT:
            self.pos += 1
            self._skip_ignored_tokens()

        while self.pos < len(self.tokens):
            self._skip_ignored_tokens()
            if self.pos >= len(self.tokens):
                break

            token = self.tokens[self.pos]

            if token.type == TokenType.EOF:
                break
            if token.type == TokenType.DEDENT:
                self.pos += 1
                break

            # Skip indents/newlines
            if token.type in (TokenType.INDENT, TokenType.NEWLINE):
                self.pos += 1
                continue

            # List item marker: -
            if token.type == TokenType.DASH or (
                token.type == TokenType.IDENTIFIER and str(token.value) == "-"
            ):
                self.pos += 1
                self._skip_ignored_tokens()

                # Parse item value
                item_value = self._parse_value(depth + 1)
                values.append(item_value)
            else:
                error_msg = f"Unexpected token in list array: {token.type} value: {token.value!r} at pos: {self.pos}"
                raise DecodingError(error_msg)

        # Validate length in strict mode
        if self.options.strict and header["length"] is not None and len(values) != header["length"]:
            error_msg = f"Array length mismatch: declared {header['length']}, got {len(values)}"
            raise ValidationError(error_msg)

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
