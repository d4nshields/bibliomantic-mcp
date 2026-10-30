"""Load the JSON data files into one validated, immutable `Book`.

Called once, from the server lifespan. Any inconsistency in the data is a bug in
this project, so it fails loudly at startup instead of surfacing mid-consultation.
"""

import json
from collections.abc import Iterable
from importlib import resources
from types import MappingProxyType
from typing import Any

from pydantic import TypeAdapter

from bibliomantic_mcp.models import HEXAGRAM_COUNT, TRIGRAM_NAMES, Book, Hexagram, Trigram

DATA_DIR = resources.files("bibliomantic_mcp") / "data"

_trigrams = TypeAdapter(tuple[Trigram, ...])
_hexagrams = TypeAdapter(tuple[Hexagram, ...])


class BookError(ValueError):
    """The data files are inconsistent. This is a bug in the data, not in the request."""


def load_book() -> Book:
    """Read `data/trigrams.json` and `data/hexagrams.json` from the installed package."""
    trigram_doc = _read_json("trigrams.json")
    hexagram_doc = _read_json("hexagrams.json")
    return build_book(
        trigrams=_trigrams.validate_python(trigram_doc["trigrams"]),
        hexagrams=_hexagrams.validate_python(hexagram_doc["hexagrams"]),
        source=hexagram_doc["source"],
        licence=hexagram_doc["licence"],
    )


def build_book(
    *,
    trigrams: Iterable[Trigram],
    hexagrams: Iterable[Hexagram],
    source: str,
    licence: str,
) -> Book:
    """Check the cross-record invariants that a single model cannot see, then freeze."""
    trigram_list = list(trigrams)
    hexagram_list = list(hexagrams)

    names = [t.name for t in trigram_list]
    if sorted(names) != sorted(TRIGRAM_NAMES):
        raise BookError(f"expected the eight trigrams {TRIGRAM_NAMES}, got {names}")
    trigram_binaries = {t.binary: t.name for t in trigram_list}
    if len(trigram_binaries) != len(trigram_list):
        raise BookError("two trigrams share a binary")
    by_name: dict[str, Trigram] = {t.name: t for t in trigram_list}

    numbers = [h.number for h in hexagram_list]
    if sorted(numbers) != list(range(1, HEXAGRAM_COUNT + 1)):
        raise BookError(f"expected hexagrams 1..{HEXAGRAM_COUNT}, got {sorted(numbers)}")

    by_binary: dict[str, int] = {}
    for h in hexagram_list:
        if h.binary in by_binary:
            raise BookError(f"hexagrams {by_binary[h.binary]} and {h.number} share {h.binary}")
        by_binary[h.binary] = h.number
        # The core structural fact: lower trigram below, upper trigram above.
        if h.lower_binary != by_name[h.lower].binary or h.upper_binary != by_name[h.upper].binary:
            raise BookError(
                f"hexagram {h.number}: binary {h.binary} is not {h.lower} below {h.upper}"
            )
        if h.symbol != chr(0x4DC0 + h.number - 1):
            raise BookError(f"hexagram {h.number}: wrong Unicode symbol {h.symbol!r}")

    return Book(
        trigrams=MappingProxyType(by_name),
        hexagrams=MappingProxyType({h.number: h for h in sorted(hexagram_list, key=_number)}),
        by_binary=MappingProxyType(by_binary),
        source=source,
        licence=licence,
    )


def _number(h: Hexagram) -> int:
    return h.number


def _read_json(filename: str) -> dict[str, Any]:
    text = (DATA_DIR / filename).read_text(encoding="utf-8")
    data: dict[str, Any] = json.loads(text)
    return data
