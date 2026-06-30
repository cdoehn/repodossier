import pytest

from repodossier.splitter import split_text


def test_split_text_returns_single_part_when_text_fits_limit():
    text = "small export"

    parts = split_text(text, max_chars=100)

    assert parts == [text]


def test_split_text_handles_empty_text():
    assert split_text("", max_chars=10) == [""]


def test_plain_split_uses_fixed_character_boundaries():
    parts = split_text("abcdef", max_chars=2, strategy="plain")

    assert parts == ["ab", "cd", "ef"]


def test_plain_split_preserves_original_text_when_joined():
    text = "abc\ndef\nghi\n"

    parts = split_text(text, max_chars=4, strategy="plain")

    assert "".join(parts) == text
    assert all(len(part) <= 4 for part in parts)


def test_heading_split_prefers_markdown_heading_boundaries():
    text = "# First\nabc\n# Second\ndef\n# Third\nghi\n"

    parts = split_text(text, max_chars=18, strategy="heading")

    assert "".join(parts) == text
    assert parts == ["# First\nabc\n", "# Second\ndef\n", "# Third\nghi\n"]


def test_heading_split_keeps_leading_preamble_before_first_heading():
    text = "Preamble\n# First\nabc\n# Second\ndef\n"

    parts = split_text(text, max_chars=22, strategy="heading")

    assert "".join(parts) == text
    assert parts[0] == "Preamble\n# First\nabc\n"
    assert parts[1] == "# Second\ndef\n"


def test_heading_split_combines_sections_while_they_fit():
    text = "# A\n1\n# B\n2\n# C\n3\n"

    parts = split_text(text, max_chars=14, strategy="heading")

    assert "".join(parts) == text
    assert parts == ["# A\n1\n# B\n2\n", "# C\n3\n"]


def test_heading_split_falls_back_to_plain_split_for_oversized_section():
    text = "# Long\nabcdefghij\n# Next\nok\n"

    parts = split_text(text, max_chars=8, strategy="heading")

    assert "".join(parts) == text
    assert all(len(part) <= 8 for part in parts)
    assert "# Next\n" in parts
    assert parts[-2:] == ["# Next\n", "ok\n"]


def test_heading_split_handles_very_small_limits():
    text = "# A\nabcdef"

    parts = split_text(text, max_chars=1, strategy="heading")

    assert "".join(parts) == text
    assert parts == list(text)


def test_heading_split_is_deterministic():
    text = "# A\nabc\n# B\ndef\n"

    first = split_text(text, max_chars=12, strategy="heading")
    second = split_text(text, max_chars=12, strategy="heading")

    assert first == second


@pytest.mark.parametrize("bad_limit", [0, -1, "10", True, None])
def test_split_text_rejects_invalid_max_chars(bad_limit):
    with pytest.raises(ValueError, match="max_chars"):
        split_text("abc", max_chars=bad_limit)


@pytest.mark.parametrize("bad_strategy", ["smart", "", 123, None])
def test_split_text_rejects_invalid_strategy(bad_strategy):
    with pytest.raises(ValueError, match="strategy"):
        split_text("abc", max_chars=10, strategy=bad_strategy)


def test_split_text_rejects_non_string_text():
    with pytest.raises(TypeError, match="text"):
        split_text(123, max_chars=10)
