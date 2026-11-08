"""Text renderings: what a model or person reads."""

import random

from bibliomantic_mcp import oracle, render
from bibliomantic_mcp.book import load_book

BOOK = load_book()


class AllHeads(random.Random):
    """Every coin lands heads, so every line is an old yang 9."""

    def getrandbits(self, k: int) -> int:
        return 1


def test_all_lines_changing_on_hexagram_1_includes_its_extra_text() -> None:
    cast = oracle.cast(BOOK, rng=AllHeads())
    assert (cast.primary.number, cast.changing_lines) == (1, (1, 2, 3, 4, 5, 6))
    assert cast.transformed is not None and cast.transformed.number == 2
    text = render.cast_summary(cast)
    assert "When all six lines are nines:" in text
    assert "Becomes ䷁ Hexagram 2: The Receptive" in text


def test_summary_without_changing_lines() -> None:
    cast = next(
        c
        for seed in range(100)
        if not (c := oracle.cast(BOOK, rng=random.Random(seed))).changing_lines
    )
    text = render.cast_summary(cast)
    assert "No changing lines." in text
    assert "Becomes" not in text
    assert f"Image: {cast.primary.image}" in text
    assert f"Source: {BOOK.source}" in text
    for line in cast.primary.lines:
        assert f"Line {line.position}: {line.text}" not in text


def test_text_alone_contains_the_selected_reading_material() -> None:
    """A text-only host must not lose imagery or the related figure's meaning."""
    cast = oracle.cast(BOOK, rng=random.Random(41))  # 20.1.6 -> 3
    text = render.cast_summary(cast)
    assert cast.transformed is not None
    for figure in (cast.primary, cast.transformed):
        assert f"Trigrams: {figure.lower} below, {figure.upper} above." in text
        assert f"Judgment: {figure.judgment}" in text
        assert f"Image: {figure.image}" in text
    for line in cast.primary.lines:
        selected_text = f"Line {line.position}: {line.text}"
        assert (selected_text in text) == (line.position in cast.changing_lines)
    for line in cast.transformed.lines:
        assert f"Line {line.position}: {line.text}" not in text
    assert "not a guaranteed future" in text
    assert f"Source: {BOOK.source}" in text
    assert text.count(cast.notice) == 1


def test_all_lines_changing_on_hexagram_2_includes_its_extra_text() -> None:
    class AllTails(random.Random):
        def getrandbits(self, k: int) -> int:
            return 0

    cast = oracle.cast(BOOK, rng=AllTails())
    assert cast.primary.number == 2
    assert cast.transformed is not None and cast.transformed.number == 1
    assert cast.primary.commentary
    assert cast.primary.commentary in render.cast_summary(cast)


def test_index_has_one_row_per_hexagram() -> None:
    rows = [line for line in render.hexagram_index(BOOK).splitlines() if line.startswith("| ")]
    assert len(rows) == 1 + 64  # header + rows
