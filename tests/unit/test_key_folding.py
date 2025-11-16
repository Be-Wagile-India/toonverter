"""Comprehensive tests for key folding."""

from toonverter.encoders.key_folding import KeyFolder


class TestKeyFolderInit:
    """Test KeyFolder initialization."""

    def test_init_default_disabled(self):
        """Test default initialization has folding disabled."""
        folder = KeyFolder()
        assert folder.enabled is False

    def test_init_enabled(self):
        """Test initialization with folding enabled."""
        folder = KeyFolder(enabled=True)
        assert folder.enabled is True

    def test_init_disabled(self):
        """Test initialization with folding disabled."""
        folder = KeyFolder(enabled=False)
        assert folder.enabled is False


class TestCanFoldChain:
    """Test detecting foldable key chains."""

    def test_can_fold_simple_chain(self):
        """Test detecting simple foldable chain."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": {"c": 1}}}

        can_fold, chain = folder.can_fold_chain(obj)

        assert can_fold is True
        assert chain == ["a", "b", "c"]

    def test_can_fold_two_level_chain(self):
        """Test detecting two-level chain."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": 1}}

        can_fold, chain = folder.can_fold_chain(obj)

        assert can_fold is True
        assert chain == ["a", "b"]

    def test_cannot_fold_single_key(self):
        """Test single key cannot be folded."""
        folder = KeyFolder(enabled=True)
        obj = {"a": 1}

        can_fold, _chain = folder.can_fold_chain(obj)

        assert can_fold is False

    def test_cannot_fold_multiple_keys(self):
        """Test multiple keys at same level cannot be folded."""
        folder = KeyFolder(enabled=True)
        obj = {"a": 1, "b": 2}

        can_fold, _chain = folder.can_fold_chain(obj)

        assert can_fold is False

    def test_cannot_fold_when_disabled(self):
        """Test folding is disabled when enabled=False."""
        folder = KeyFolder(enabled=False)
        obj = {"a": {"b": {"c": 1}}}

        can_fold, chain = folder.can_fold_chain(obj)

        assert can_fold is False
        assert chain == []

    def test_cannot_fold_invalid_key_segment(self):
        """Test cannot fold keys with invalid characters."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b-c": {"d": 1}}}  # Hyphen not allowed

        can_fold, _chain = folder.can_fold_chain(obj)

        # Should stop at invalid segment
        assert can_fold is False

    def test_cannot_fold_key_with_separator(self):
        """Test cannot fold key containing separator."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b.c": 1}}  # Contains separator

        can_fold, _chain = folder.can_fold_chain(obj)

        # Should stop at key with separator
        assert can_fold is False

    def test_fold_chain_stops_at_multi_key_level(self):
        """Test folding stops when multiple keys appear."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": {"c": 1, "d": 2}}}

        can_fold, chain = folder.can_fold_chain(obj)

        # Should fold a.b but stop at level with c and d
        assert can_fold is True
        assert chain == ["a", "b"]

    def test_fold_chain_with_non_dict_value(self):
        """Test folding chain ending in non-dict."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": [1, 2, 3]}}

        can_fold, chain = folder.can_fold_chain(obj)

        assert can_fold is True
        assert chain == ["a", "b"]


class TestFoldKeyChain:
    """Test folding key chains into dotted notation."""

    def test_fold_two_keys(self):
        """Test folding two keys."""
        folder = KeyFolder()
        result = folder.fold_key_chain(["a", "b"])
        assert result == "a.b"

    def test_fold_three_keys(self):
        """Test folding three keys."""
        folder = KeyFolder()
        result = folder.fold_key_chain(["a", "b", "c"])
        assert result == "a.b.c"

    def test_fold_many_keys(self):
        """Test folding many keys."""
        folder = KeyFolder()
        result = folder.fold_key_chain(["one", "two", "three", "four"])
        assert result == "one.two.three.four"

    def test_fold_single_key(self):
        """Test folding single key."""
        folder = KeyFolder()
        result = folder.fold_key_chain(["a"])
        assert result == "a"


class TestGetFoldedValue:
    """Test getting value at end of key chain."""

    def test_get_value_simple_chain(self):
        """Test getting value from simple chain."""
        folder = KeyFolder()
        obj = {"a": {"b": {"c": 1}}}

        result = folder.get_folded_value(obj, ["a", "b", "c"])

        assert result == 1

    def test_get_value_two_level(self):
        """Test getting value from two-level chain."""
        folder = KeyFolder()
        obj = {"a": {"b": "value"}}

        result = folder.get_folded_value(obj, ["a", "b"])

        assert result == "value"

    def test_get_value_dict(self):
        """Test getting dict value."""
        folder = KeyFolder()
        obj = {"a": {"b": {"c": 1, "d": 2}}}

        result = folder.get_folded_value(obj, ["a", "b"])

        assert result == {"c": 1, "d": 2}

    def test_get_value_list(self):
        """Test getting list value."""
        folder = KeyFolder()
        obj = {"a": {"b": [1, 2, 3]}}

        result = folder.get_folded_value(obj, ["a", "b"])

        assert result == [1, 2, 3]


class TestDetectFoldableKeys:
    """Test detecting all foldable keys in object."""

    def test_detect_single_foldable(self):
        """Test detecting single foldable chain."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": 1}}

        result = folder.detect_foldable_keys(obj)

        assert len(result) == 1
        assert result[0] == ("a.b", ["a", "b"], 1)

    def test_detect_multiple_foldable(self):
        """Test detecting multiple foldable chains."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": 1}, "c": {"d": {"e": 2}}}

        result = folder.detect_foldable_keys(obj)

        assert len(result) == 2
        folded_keys = [r[0] for r in result]
        assert "a.b" in folded_keys
        assert "c.d.e" in folded_keys

    def test_detect_no_foldable(self):
        """Test detecting when no keys are foldable."""
        folder = KeyFolder(enabled=True)
        obj = {"a": 1, "b": 2, "c": 3}

        result = folder.detect_foldable_keys(obj)

        assert len(result) == 0

    def test_detect_when_disabled(self):
        """Test detection returns empty when disabled."""
        folder = KeyFolder(enabled=False)
        obj = {"a": {"b": 1}}

        result = folder.detect_foldable_keys(obj)

        assert len(result) == 0

    def test_detect_mixed_content(self):
        """Test detecting with mix of foldable and non-foldable."""
        folder = KeyFolder(enabled=True)
        obj = {"foldable": {"key": 1}, "simple": 2, "complex": {"a": 1, "b": 2}}

        result = folder.detect_foldable_keys(obj)

        assert len(result) == 1
        assert result[0][0] == "foldable.key"


class TestUnfoldKey:
    """Test unfolding dotted keys into nested dicts."""

    def test_unfold_two_segments(self):
        """Test unfolding two segments."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b", 1)

        assert result == {"a": {"b": 1}}

    def test_unfold_three_segments(self):
        """Test unfolding three segments."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b.c", "value")

        assert result == {"a": {"b": {"c": "value"}}}

    def test_unfold_many_segments(self):
        """Test unfolding many segments."""
        folder = KeyFolder()
        result = folder.unfold_key("one.two.three.four", 42)

        assert result == {"one": {"two": {"three": {"four": 42}}}}

    def test_unfold_with_dict_value(self):
        """Test unfolding with dict value."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b", {"c": 1, "d": 2})

        assert result == {"a": {"b": {"c": 1, "d": 2}}}

    def test_unfold_with_list_value(self):
        """Test unfolding with list value."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b", [1, 2, 3])

        assert result == {"a": {"b": [1, 2, 3]}}

    def test_unfold_single_segment(self):
        """Test unfolding single segment."""
        folder = KeyFolder()
        result = folder.unfold_key("a", 1)

        assert result == {"a": 1}


class TestShouldFoldKey:
    """Test decision logic for folding specific keys."""

    def test_should_fold_simple_case(self):
        """Test should fold simple single-key dict."""
        folder = KeyFolder(enabled=True)
        key = "a"
        value = {"b": 1}
        siblings = {"a": value}

        result = folder.should_fold_key(key, value, siblings)

        assert result is True

    def test_should_not_fold_when_disabled(self):
        """Test should not fold when disabled."""
        folder = KeyFolder(enabled=False)
        key = "a"
        value = {"b": 1}
        siblings = {"a": value}

        result = folder.should_fold_key(key, value, siblings)

        assert result is False

    def test_should_not_fold_non_dict_value(self):
        """Test should not fold non-dict value."""
        folder = KeyFolder(enabled=True)
        key = "a"
        value = 1  # Not a dict
        siblings = {"a": value}

        result = folder.should_fold_key(key, value, siblings)

        assert result is False

    def test_should_not_fold_multi_key_dict(self):
        """Test should not fold dict with multiple keys."""
        folder = KeyFolder(enabled=True)
        key = "a"
        value = {"b": 1, "c": 2}
        siblings = {"a": value}

        result = folder.should_fold_key(key, value, siblings)

        assert result is False

    def test_should_not_fold_with_collision(self):
        """Test should not fold when collision exists."""
        folder = KeyFolder(enabled=True)
        key = "a"
        value = {"b": 1}
        siblings = {"a": value, "a.b": 2}  # Collision

        result = folder.should_fold_key(key, value, siblings)

        assert result is False


class TestHasCollision:
    """Test collision detection."""

    def test_no_collision_simple(self):
        """Test no collision in simple case."""
        folder = KeyFolder()
        siblings = {"a": 1, "b": 2}

        result = folder._has_collision("a", siblings)

        assert result is False

    def test_has_collision_with_prefix(self):
        """Test collision when sibling has matching prefix."""
        folder = KeyFolder()
        siblings = {"a": 1, "a.b": 2}

        result = folder._has_collision("a", siblings)

        assert result is True

    def test_no_collision_different_prefix(self):
        """Test no collision with different prefix."""
        folder = KeyFolder()
        siblings = {"a": 1, "ab": 2}  # "ab" != "a."

        result = folder._has_collision("a", siblings)

        assert result is False

    def test_has_collision_longer_chain(self):
        """Test collision with longer dotted key."""
        folder = KeyFolder()
        siblings = {"a": 1, "a.b.c": 2}

        result = folder._has_collision("a", siblings)

        assert result is True

    def test_no_collision_with_self(self):
        """Test key doesn't collide with itself."""
        folder = KeyFolder()
        siblings = {"a": 1}

        result = folder._has_collision("a", siblings)

        assert result is False


class TestRoundtrip:
    """Test fold/unfold roundtrip."""

    def test_roundtrip_simple(self):
        """Test fold and unfold roundtrip."""
        folder = KeyFolder(enabled=True)

        # Unfold -> fold
        unfolded = folder.unfold_key("a.b.c", 1)
        can_fold, chain = folder.can_fold_chain(unfolded)

        assert can_fold
        folded = folder.fold_key_chain(chain)
        assert folded == "a.b.c"

    def test_roundtrip_complex(self):
        """Test roundtrip with complex value."""
        folder = KeyFolder(enabled=True)

        value = [1, 2, 3]  # Non-dict value
        unfolded = folder.unfold_key("a.b", value)

        can_fold, chain = folder.can_fold_chain(unfolded)
        assert can_fold

        retrieved = folder.get_folded_value(unfolded, chain)
        assert retrieved == value


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_object(self):
        """Test empty object."""
        folder = KeyFolder(enabled=True)
        obj = {}

        can_fold, _chain = folder.can_fold_chain(obj)
        assert can_fold is False

        result = folder.detect_foldable_keys(obj)
        assert result == []

    def test_deeply_nested_chain(self):
        """Test very deeply nested chain."""
        folder = KeyFolder(enabled=True)
        obj = {"a": {"b": {"c": {"d": {"e": {"f": 1}}}}}}

        can_fold, chain = folder.can_fold_chain(obj)

        assert can_fold is True
        assert len(chain) == 6
        assert chain == ["a", "b", "c", "d", "e", "f"]

    def test_fold_chain_empty_list(self):
        """Test folding empty chain."""
        folder = KeyFolder()
        result = folder.fold_key_chain([])
        assert result == ""

    def test_unfold_with_none_value(self):
        """Test unfolding with None value."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b", None)

        assert result == {"a": {"b": None}}

    def test_unfold_with_boolean_value(self):
        """Test unfolding with boolean value."""
        folder = KeyFolder()
        result = folder.unfold_key("a.b", True)

        assert result == {"a": {"b": True}}
