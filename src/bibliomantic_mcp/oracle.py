"""The oracle: cast coins, build hexagrams, look things up. Pure functions.

This module knows nothing about MCP. It takes a `Book` and (optionally) a random
number generator and returns plain models, so every rule here can be tested
without starting a server.

It deliberately does not format prose, guess what a question is about, or
interpret anything. That is the host model's job (ADR-0001).
"""

import random
import secrets
from collections import Counter
from itertools import product

from bibliomantic_mcp.models import (
    HEXAGRAM_COUNT,
    Book,
    Cast,
    CoinToss,
    Hexagram,
    LineValue,
    LineValueInfo,
    MethodDescription,
    Trigram,
    flip,
)

NOTICE = "For reflection and creativity only: a cast makes no prediction and is not advice."


class NotInBook(LookupError):
    """A lookup asked for something the book does not contain (e.g. hexagram 65).

    The protocol layer maps this to whatever error its primitive uses: a
    `ToolError` for a tool, a `ResourceNotFoundError` for a resource, and an
    `MCPError(INVALID_PARAMS)` for a prompt argument.
    """


def toss_coins(rng: random.Random | None = None) -> CoinToss:
    """Throw three coins. The default source is the OS CSPRNG."""
    rng = rng or secrets.SystemRandom()
    heads = (bool(rng.getrandbits(1)), bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))
    return CoinToss(heads=heads)


def cast(book: Book, question: str | None = None, rng: random.Random | None = None) -> Cast:
    """Perform one consultation and return the complete record of it."""
    rng = rng or secrets.SystemRandom()
    # 1-2. Six tosses, bottom line first, each giving a line value.
    tosses = tuple(toss_coins(rng) for _ in range(6))
    values = tuple(toss.value for toss in tosses)
    # 3-4. The primary hexagram reads each line as yang or yin. A missing binary
    #      would be a data bug, so the KeyError is allowed to surface loudly.
    primary_binary = "".join("1" if v.is_yang else "0" for v in values)
    primary = book.hexagrams[book.by_binary[primary_binary]]
    # 5-6. Old lines (6 and 9) change into their opposites.
    changing = tuple(i for i, v in enumerate(values, start=1) if v.is_changing)
    transformed = None
    if changing:
        transformed_binary = flip(primary_binary, changing)
        transformed = book.hexagrams[book.by_binary[transformed_binary]]
    # 7. The record. `question` is carried through untouched.
    return Cast(
        tosses=tosses,
        values=values,
        primary=primary,
        changing_lines=changing,
        transformed=transformed,
        question=question,
        notice=NOTICE,
    )


def hexagram_from_number(book: Book, number: int) -> Hexagram:
    if not 1 <= number <= HEXAGRAM_COUNT:
        raise NotInBook(f"Hexagram number must be 1–{HEXAGRAM_COUNT}, not {number}")
    return book.hexagrams[number]


def parse_hexagram_number(text: str) -> int:
    """Read a hexagram number typed as text (a URI segment, a prompt argument)."""
    stripped = text.strip()
    # Leading zeros are fine ("07"). Dropping them and capping the length before int()
    # matters: int() raises ValueError on strings past 4,300 digits, which would surface
    # as an internal error instead of "not in the book".
    digits = stripped.lstrip("0")
    if (
        not (stripped.isascii() and stripped.isdigit())
        or len(digits) > len(str(HEXAGRAM_COUNT))
        or not 1 <= int(digits or "0") <= HEXAGRAM_COUNT
    ):
        raise NotInBook(f"Hexagram number must be 1–{HEXAGRAM_COUNT}, not {text!r}")
    return int(digits)


def hexagram_from_binary(book: Book, binary: str) -> Hexagram:
    if len(binary) != 6 or set(binary) - {"0", "1"}:
        raise NotInBook(f"A hexagram binary is six 0/1 characters, bottom first: {binary!r}")
    return book.hexagrams[book.by_binary[binary]]


def trigram_by_name(book: Book, name: str) -> Trigram:
    """Find a trigram by English name (any case) or by its Chinese character."""
    wanted = name.strip()
    for trigram in book.trigrams.values():
        if wanted.casefold() == trigram.name.casefold() or wanted == trigram.chinese:
            return trigram
    valid = ", ".join(book.trigrams)
    raise NotInBook(f"No trigram named {name!r}. Valid names: {valid}")


def nuclear_hexagram(book: Book, hexagram: Hexagram) -> Hexagram:
    """The hidden figure inside a hexagram: lines 2-3-4 below, lines 3-4-5 above.

    A traditional extra for study. Not exposed as a tool; kept as a small worked
    example of how much structure a six-bit string carries.
    """
    b = hexagram.binary
    return hexagram_from_binary(book, b[1:4] + b[2:5])


def describe_method(book: Book) -> MethodDescription:
    """Explain the three-coin method. The numbers are computed, not typed in."""
    # Enumerate all eight equally likely outcomes of three coins.
    outcomes = Counter(CoinToss(heads=coins).value for coins in product((True, False), repeat=3))
    names = {
        LineValue.OLD_YIN: "old yin",
        LineValue.YOUNG_YANG: "young yang",
        LineValue.YOUNG_YIN: "young yin",
        LineValue.OLD_YANG: "old yang",
    }
    line_values = tuple(
        LineValueInfo(
            value=value,
            name=names[value],
            heads=(value - 6),  # each head adds 1 over the all-tails sum of 6
            probability=f"{outcomes[value]}/8",
            is_yang=value.is_yang,
            is_changing=value.is_changing,
        )
        for value in LineValue
    )
    return MethodDescription(
        coins="Three coins are tossed for each line. Heads count 3, tails count 2, "
        "so each toss sums to 6, 7, 8 or 9.",
        line_values=line_values,
        building_the_hexagram="Six tosses build the figure from the bottom line up. "
        "Odd sums (7, 9) give a solid yang line, even sums (6, 8) a broken yin line.",
        changing_lines="A 6 (old yin) or 9 (old yang) is a changing line: it has reached "
        "its extreme and turns into its opposite. Read the line texts for changing lines only.",
        transformed_hexagram="If any lines change, flip each changing line (yin to yang, "
        "yang to yin) to get a second, transformed hexagram: where the situation is heading. "
        "With no changing lines there is only the primary hexagram.",
        source=book.source,
        licence=book.licence,
        notice=NOTICE,
    )
