"""Data integrity: the shipped JSON is a complete, structurally correct I Ching."""

import json
import re

import pytest

from bibliomantic_mcp.book import DATA_DIR, BookError, build_book, load_book
from bibliomantic_mcp.models import HEXAGRAM_COUNT, TRIGRAM_NAMES, Book, Hexagram

BOOK = load_book()


def reverse(binary: str) -> str:
    """The figure turned upside down (read top to bottom)."""
    return binary[::-1]


def complement(binary: str) -> str:
    """Every line changed into its opposite."""
    return "".join("0" if bit == "1" else "1" for bit in binary)


def test_exactly_64_hexagrams_numbered_contiguously() -> None:
    assert list(BOOK.hexagrams) == list(range(1, HEXAGRAM_COUNT + 1))


def test_exactly_eight_trigrams() -> None:
    assert sorted(BOOK.trigrams) == sorted(TRIGRAM_NAMES)


def test_trigram_binaries_are_unique_and_cover_all_eight_patterns() -> None:
    assert sorted(t.binary for t in BOOK.trigrams.values()) == [format(i, "03b") for i in range(8)]


def test_trigram_symbols_are_the_unicode_trigram_characters() -> None:
    for offset, name in enumerate(TRIGRAM_NAMES):
        assert BOOK.trigrams[name].symbol == chr(0x2630 + offset)


def test_hexagram_binaries_are_unique() -> None:
    binaries = [h.binary for h in BOOK.hexagrams.values()]
    assert len(set(binaries)) == HEXAGRAM_COUNT
    assert sorted(BOOK.by_binary) == sorted(binaries)


@pytest.mark.parametrize("number", range(1, HEXAGRAM_COUNT + 1))
def test_binary_decomposes_into_its_two_trigrams(number: int) -> None:
    h = BOOK.hexagrams[number]
    assert h.binary == BOOK.trigrams[h.lower].binary + BOOK.trigrams[h.upper].binary


@pytest.mark.parametrize("odd", range(1, HEXAGRAM_COUNT + 1, 2))
def test_king_wen_pairs(odd: int) -> None:
    """Each pair (n, n+1) is a figure and its reversal; symmetric figures pair with their
    complement instead. Exactly four pairs are symmetric: 1/2, 27/28, 29/30, 61/62."""
    first, second = BOOK.hexagrams[odd].binary, BOOK.hexagrams[odd + 1].binary
    if reverse(first) == first:
        assert odd in (1, 27, 29, 61)
        assert second == complement(first)
    else:
        assert second == reverse(first)


@pytest.mark.parametrize("number", range(1, HEXAGRAM_COUNT + 1))
def test_unicode_symbol(number: int) -> None:
    assert BOOK.hexagrams[number].symbol == chr(0x4DC0 + number - 1)


@pytest.mark.parametrize("number", range(1, HEXAGRAM_COUNT + 1))
def test_six_lines_in_order(number: int) -> None:
    assert [line.position for line in BOOK.hexagrams[number].lines] == [1, 2, 3, 4, 5, 6]


PLACE = {1: "at the beginning", 2: "in the second place", 3: "in the third place",
         4: "in the fourth place", 5: "in the fifth place", 6: "at the top"}  # fmt: skip


@pytest.mark.parametrize("number", range(1, HEXAGRAM_COUNT + 1))
def test_line_labels_agree_with_the_figure(number: int) -> None:
    """'Nine' marks a yang line and 'Six' a yin line, so each label is checkable."""
    h = BOOK.hexagrams[number]
    for line, bit in zip(h.lines, h.binary, strict=True):
        label = f"{'Nine' if bit == '1' else 'Six'} {PLACE[line.position]}:"
        assert line.text.startswith(label), (number, line.position)


PLACEHOLDER = re.compile(r"TODO|TBD|placeholder|lorem|traditional interpretation", re.I)


@pytest.mark.parametrize("number", range(1, HEXAGRAM_COUNT + 1))
def test_texts_are_real(number: int) -> None:
    h = BOOK.hexagrams[number]
    texts = [h.judgment, h.image, *(line.text for line in h.lines)]
    for text in texts:
        assert len(text) >= 30
        assert not PLACEHOLDER.search(text)
    # A line must say more than its label.
    for line in h.lines:
        assert len(line.text.split(":", 1)[1].strip()) >= 15


def test_line_texts_are_not_duplicated() -> None:
    texts = [line.text for h in BOOK.hexagrams.values() for line in h.lines]
    assert len(set(texts)) == len(texts)


def test_json_is_hand_readable() -> None:
    """2-space indent, UTF-8 characters unescaped, fixed key order, trailing newline."""
    for name in ("trigrams.json", "hexagrams.json"):
        raw = (DATA_DIR / name).read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert raw == json.dumps(json.loads(raw), ensure_ascii=False, indent=2) + "\n"
    keys = list(Hexagram.model_fields)
    for entry in json.loads((DATA_DIR / "hexagrams.json").read_text(encoding="utf-8"))["hexagrams"]:
        assert list(entry) == [k for k in keys if k in entry]


def test_book_is_immutable() -> None:
    with pytest.raises(TypeError):
        BOOK.hexagrams[1] = BOOK.hexagrams[2]  # type: ignore[index]


def _rebuild(book: Book, hexagrams: list[Hexagram]) -> Book:
    return build_book(
        trigrams=book.trigrams.values(),
        hexagrams=hexagrams,
        source=book.source,
        licence=book.licence,
    )


def test_loader_rejects_a_missing_hexagram() -> None:
    with pytest.raises(BookError, match="expected hexagrams"):
        _rebuild(BOOK, list(BOOK.hexagrams.values())[:-1])


def test_loader_rejects_a_binary_that_contradicts_the_trigrams() -> None:
    hexagrams = list(BOOK.hexagrams.values())
    hexagrams[0] = hexagrams[0].model_copy(update={"lower": "Earth"})
    with pytest.raises(BookError, match="is not Earth below Heaven"):
        _rebuild(BOOK, hexagrams)
