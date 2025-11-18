"""Comprehensive tests for indentation management."""

import pytest

from toonverter.encoders.indentation import IndentationManager, calculate_depth, detect_indentation


class TestIndentationManagerInit:
    """Test IndentationManager initialization."""

    def test_init_default_indent_size(self):
        """Test default indent size is 2."""
        mgr = IndentationManager()
        assert mgr.indent_size == 2
        assert mgr.current_depth == 0

    def test_init_custom_indent_size(self):
        """Test custom indent size."""
        mgr = IndentationManager(indent_size=4)
        assert mgr.indent_size == 4

    def test_init_indent_size_zero_allowed(self):
        """Test indent size of 0 is allowed for compact mode."""
        mgr = IndentationManager(indent_size=0)
        assert mgr.indent_size == 0
        assert mgr.indent(1) == ""  # No indentation in compact mode

    def test_init_negative_indent_size_raises_error(self):
        """Test negative indent size raises ValueError."""
        with pytest.raises(ValueError, match="must be at least 0"):
            IndentationManager(indent_size=-1)

    def test_init_indent_size_one(self):
        """Test indent size of 1 is valid."""
        mgr = IndentationManager(indent_size=1)
        assert mgr.indent_size == 1


class TestIndent:
    """Test indent() method."""

    def test_indent_zero_depth(self):
        """Test zero depth returns empty string."""
        mgr = IndentationManager(indent_size=2)
        assert mgr.indent(0) == ""

    def test_indent_one_level(self):
        """Test one level indentation."""
        mgr = IndentationManager(indent_size=2)
        assert mgr.indent(1) == "  "

    def test_indent_two_levels(self):
        """Test two levels indentation."""
        mgr = IndentationManager(indent_size=2)
        assert mgr.indent(2) == "    "

    def test_indent_many_levels(self):
        """Test many levels indentation."""
        mgr = IndentationManager(indent_size=2)
        assert mgr.indent(5) == "          "  # 10 spaces

    def test_indent_custom_size(self):
        """Test indentation with custom indent size."""
        mgr = IndentationManager(indent_size=4)
        assert mgr.indent(1) == "    "
        assert mgr.indent(2) == "        "

    def test_indent_negative_depth(self):
        """Test negative depth is treated as zero."""
        mgr = IndentationManager(indent_size=2)
        assert mgr.indent(-1) == ""
        assert mgr.indent(-5) == ""


class TestPush:
    """Test push() method."""

    def test_push_increases_depth(self):
        """Test push increases current depth."""
        mgr = IndentationManager()
        assert mgr.current_depth == 0

        result = mgr.push()

        assert result == 1
        assert mgr.current_depth == 1

    def test_push_multiple_times(self):
        """Test pushing multiple times."""
        mgr = IndentationManager()

        mgr.push()
        mgr.push()
        result = mgr.push()

        assert result == 3
        assert mgr.current_depth == 3

    def test_push_returns_new_depth(self):
        """Test push returns new depth."""
        mgr = IndentationManager()
        mgr.current_depth = 5

        result = mgr.push()

        assert result == 6


class TestPop:
    """Test pop() method."""

    def test_pop_decreases_depth(self):
        """Test pop decreases current depth."""
        mgr = IndentationManager()
        mgr.current_depth = 2

        result = mgr.pop()

        assert result == 1
        assert mgr.current_depth == 1

    def test_pop_at_zero_stays_zero(self):
        """Test pop at depth 0 stays at 0."""
        mgr = IndentationManager()
        mgr.current_depth = 0

        result = mgr.pop()

        assert result == 0
        assert mgr.current_depth == 0

    def test_pop_multiple_times(self):
        """Test popping multiple times."""
        mgr = IndentationManager()
        mgr.current_depth = 5

        mgr.pop()
        mgr.pop()
        result = mgr.pop()

        assert result == 2
        assert mgr.current_depth == 2

    def test_pop_below_zero_clamps(self):
        """Test popping below zero clamps at zero."""
        mgr = IndentationManager()
        mgr.current_depth = 1

        mgr.pop()
        mgr.pop()  # Should stay at 0
        mgr.pop()  # Should stay at 0

        assert mgr.current_depth == 0


class TestReset:
    """Test reset() method."""

    def test_reset_sets_depth_to_zero(self):
        """Test reset sets depth to 0."""
        mgr = IndentationManager()
        mgr.current_depth = 5

        mgr.reset()

        assert mgr.current_depth == 0

    def test_reset_at_zero_stays_zero(self):
        """Test reset when already at 0."""
        mgr = IndentationManager()
        mgr.current_depth = 0

        mgr.reset()

        assert mgr.current_depth == 0


class TestGetCurrentIndent:
    """Test get_current_indent() method."""

    def test_get_current_indent_at_zero(self):
        """Test getting indent at depth 0."""
        mgr = IndentationManager(indent_size=2)
        mgr.current_depth = 0

        result = mgr.get_current_indent()

        assert result == ""

    def test_get_current_indent_at_level_one(self):
        """Test getting indent at depth 1."""
        mgr = IndentationManager(indent_size=2)
        mgr.current_depth = 1

        result = mgr.get_current_indent()

        assert result == "  "

    def test_get_current_indent_at_level_three(self):
        """Test getting indent at depth 3."""
        mgr = IndentationManager(indent_size=2)
        mgr.current_depth = 3

        result = mgr.get_current_indent()

        assert result == "      "  # 6 spaces

    def test_get_current_indent_with_custom_size(self):
        """Test getting indent with custom indent size."""
        mgr = IndentationManager(indent_size=4)
        mgr.current_depth = 2

        result = mgr.get_current_indent()

        assert result == "        "  # 8 spaces


class TestDetectIndentation:
    """Test detect_indentation() function."""

    def test_detect_no_indentation(self):
        """Test detecting no indentation."""
        result = detect_indentation("name: Alice")
        assert result == 0

    def test_detect_two_spaces(self):
        """Test detecting 2 spaces."""
        result = detect_indentation("  age: 30")
        assert result == 2

    def test_detect_four_spaces(self):
        """Test detecting 4 spaces."""
        result = detect_indentation("    city: NYC")
        assert result == 4

    def test_detect_many_spaces(self):
        """Test detecting many spaces."""
        result = detect_indentation("          value")
        assert result == 10

    def test_detect_empty_line(self):
        """Test detecting indentation of empty line."""
        result = detect_indentation("")
        assert result == 0

    def test_detect_only_spaces(self):
        """Test detecting line with only spaces."""
        result = detect_indentation("    ")
        assert result == 4

    def test_detect_tab_raises_error(self):
        """Test tab character raises ValueError."""
        with pytest.raises(ValueError, match="Tab characters are not allowed"):
            detect_indentation("\tvalue")

    def test_detect_tab_after_spaces_raises_error(self):
        """Test tab after spaces raises ValueError."""
        with pytest.raises(ValueError, match="Tab characters are not allowed"):
            detect_indentation("  \tvalue")

    def test_detect_with_content(self):
        """Test detecting indentation ignores content."""
        result = detect_indentation("  key: value with spaces")
        assert result == 2


class TestCalculateDepth:
    """Test calculate_depth() function."""

    def test_calculate_depth_zero_spaces(self):
        """Test calculating depth from 0 spaces."""
        result = calculate_depth(0, indent_size=2)
        assert result == 0

    def test_calculate_depth_one_level(self):
        """Test calculating depth for one level."""
        result = calculate_depth(2, indent_size=2)
        assert result == 1

    def test_calculate_depth_two_levels(self):
        """Test calculating depth for two levels."""
        result = calculate_depth(4, indent_size=2)
        assert result == 2

    def test_calculate_depth_many_levels(self):
        """Test calculating depth for many levels."""
        result = calculate_depth(10, indent_size=2)
        assert result == 5

    def test_calculate_depth_custom_indent_size(self):
        """Test calculating depth with custom indent size."""
        result = calculate_depth(8, indent_size=4)
        assert result == 2

    def test_calculate_depth_non_multiple_truncates(self):
        """Test non-exact multiple truncates down."""
        result = calculate_depth(3, indent_size=2)
        assert result == 1  # 3 // 2 = 1

    def test_calculate_depth_odd_spaces(self):
        """Test odd number of spaces."""
        result = calculate_depth(5, indent_size=2)
        assert result == 2  # 5 // 2 = 2

    def test_calculate_depth_zero_with_custom_size(self):
        """Test zero spaces with custom indent size."""
        result = calculate_depth(0, indent_size=4)
        assert result == 0


class TestWorkflow:
    """Test common workflow scenarios."""

    def test_push_pop_workflow(self):
        """Test typical push/pop workflow."""
        mgr = IndentationManager(indent_size=2)

        # Start at root
        assert mgr.get_current_indent() == ""

        # Enter first level
        mgr.push()
        assert mgr.get_current_indent() == "  "

        # Enter second level
        mgr.push()
        assert mgr.get_current_indent() == "    "

        # Exit one level
        mgr.pop()
        assert mgr.get_current_indent() == "  "

        # Exit to root
        mgr.pop()
        assert mgr.get_current_indent() == ""

    def test_nested_structure(self):
        """Test managing nested structure indentation."""
        mgr = IndentationManager(indent_size=2)

        # Object at root
        assert mgr.indent(mgr.current_depth) == ""

        # First property
        mgr.push()
        assert mgr.indent(mgr.current_depth) == "  "

        # Nested object
        mgr.push()
        assert mgr.indent(mgr.current_depth) == "    "

        # Exit nested object
        mgr.pop()
        # Next property at first level
        assert mgr.indent(mgr.current_depth) == "  "

        mgr.pop()
        # Back to root
        assert mgr.indent(mgr.current_depth) == ""

    def test_reset_workflow(self):
        """Test using reset in workflow."""
        mgr = IndentationManager()

        mgr.push()
        mgr.push()
        mgr.push()
        assert mgr.current_depth == 3

        mgr.reset()
        assert mgr.current_depth == 0
        assert mgr.get_current_indent() == ""

    def test_detect_and_calculate_workflow(self):
        """Test detecting and calculating depth."""
        line = "    value"

        spaces = detect_indentation(line)
        assert spaces == 4

        depth = calculate_depth(spaces, indent_size=2)
        assert depth == 2


class TestEdgeCases:
    """Test edge cases."""

    def test_large_indent_size(self):
        """Test with large indent size."""
        mgr = IndentationManager(indent_size=8)
        mgr.push()
        assert mgr.get_current_indent() == "        "

    def test_many_depth_levels(self):
        """Test with many depth levels."""
        mgr = IndentationManager(indent_size=2)
        for _ in range(20):
            mgr.push()

        assert mgr.current_depth == 20
        assert len(mgr.get_current_indent()) == 40  # 20 * 2

    def test_detect_line_starting_with_non_space(self):
        """Test detecting line starting with non-space."""
        result = detect_indentation("abc")
        assert result == 0

    def test_calculate_depth_large_numbers(self):
        """Test calculating depth with large numbers."""
        result = calculate_depth(100, indent_size=2)
        assert result == 50
