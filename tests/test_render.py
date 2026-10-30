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


def test_index_has_one_row_per_hexagram() -> None:
    rows = [line for line in render.hexagram_index(BOOK).splitlines() if line.startswith("| ")]
    assert len(rows) == 1 + 64  # header + rows
