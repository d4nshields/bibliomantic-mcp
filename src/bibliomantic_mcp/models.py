"""The domain vocabulary: trigrams, hexagrams, coin tosses and a complete cast.

Plain Pydantic models with no MCP imports. Pydantic does double duty here: it
validates the data file when the book loads, and the same models become the
`output_schema` of the tools that return them.

Conventions used everywhere:
- A *binary* string is read **bottom line first**; "1" is yang (solid), "0" is yin (broken).
- Line *positions* run 1 (bottom) to 6 (top).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Annotated, Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

HEXAGRAM_COUNT = 64
"""Hexagrams are numbered 1..64 in the King Wen sequence."""

TrigramName = Literal["Heaven", "Lake", "Fire", "Thunder", "Wind", "Water", "Mountain", "Earth"]
TRIGRAM_NAMES: tuple[TrigramName, ...] = get_args(TrigramName)
"""The eight trigrams, in Unicode order (U+2630 ☰ to U+2637 ☷)."""

TrigramBinary = Annotated[str, Field(pattern=r"^[01]{3}$", description="Bottom line first.")]
HexagramBinary = Annotated[str, Field(pattern=r"^[01]{6}$", description="Bottom line first.")]
Position = Annotated[int, Field(ge=1, le=6, description="1 is the bottom line, 6 the top.")]
Text = Annotated[str, Field(min_length=1)]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Trigram(_Frozen):
    """One of the eight three-line figures that make up every hexagram."""

    name: TrigramName = Field(description="English name, e.g. 'Heaven'.")
    chinese: Text
    pinyin: Text
    symbol: Text = Field(description="Unicode trigram character, e.g. '☰'.")
    binary: TrigramBinary
    attribute: Text = Field(description="Its quality, e.g. 'strength'.")
    image: Text = Field(description="The natural image, e.g. 'heaven'.")
    family: Text = Field(description="Its family role, e.g. 'father'.")


class LineText(_Frozen):
    """The canonical statement attached to one line of a hexagram."""

    position: Position
    text: Text
    commentary: str | None = None


class Hexagram(_Frozen):
    """One of the 64 six-line figures, with its canonical text."""

    number: int = Field(ge=1, le=HEXAGRAM_COUNT, description="King Wen sequence number.")
    name: Text = Field(description="English name.")
    chinese: Text
    pinyin: Text
    symbol: Text = Field(description="Unicode hexagram character, U+4DC0 to U+4DFF.")
    binary: HexagramBinary
    upper: TrigramName = Field(description="Upper trigram: lines 4 to 6.")
    lower: TrigramName = Field(description="Lower trigram: lines 1 to 3.")
    judgment: Text
    image: Text
    lines: tuple[LineText, ...] = Field(min_length=6, max_length=6)
    commentary: str | None = None

    @property
    def lower_binary(self) -> str:
        return self.binary[:3]

    @property
    def upper_binary(self) -> str:
        return self.binary[3:]

    @model_validator(mode="after")
    def _lines_in_order(self) -> Self:
        positions = [line.position for line in self.lines]
        if positions != [1, 2, 3, 4, 5, 6]:
            raise ValueError(f"hexagram {self.number}: line positions are {positions}")
        return self


class LineValue(IntEnum):
    """The four results of tossing three coins for one line.

    Heads count 3 and tails count 2, so three coins sum to 6, 7, 8 or 9.
    Odd sums are yang, even sums are yin, and the extremes (6, 9) are "old"
    lines that are about to change into their opposite.
    """

    OLD_YIN = 6
    YOUNG_YANG = 7
    YOUNG_YIN = 8
    OLD_YANG = 9

    @property
    def is_yang(self) -> bool:
        return self in (LineValue.YOUNG_YANG, LineValue.OLD_YANG)

    @property
    def is_changing(self) -> bool:
        return self in (LineValue.OLD_YIN, LineValue.OLD_YANG)


HEADS = 3
TAILS = 2


def flip(binary: str, positions: tuple[int, ...]) -> str:
    """Change the lines at the given 1-based positions into their opposites."""
    bits = list(binary)
    for position in positions:
        bits[position - 1] = "0" if bits[position - 1] == "1" else "1"
    return "".join(bits)


class CoinToss(_Frozen):
    """Three coins thrown for one line."""

    heads: tuple[bool, bool, bool] = Field(description="True means that coin landed heads.")

    @property
    def value(self) -> LineValue:
        # 3 heads -> 9, 2 heads -> 8, 1 head -> 7, 0 heads -> 6.
        return LineValue(sum(HEADS if coin else TAILS for coin in self.heads))


class Cast(_Frozen):
    """The complete, auditable record of one consultation.

    Everything here can be checked by hand: the coins give the values, the
    values give the primary hexagram, and flipping the changing lines gives
    the transformed one. The validator below re-checks that chain.
    """

    tosses: tuple[CoinToss, ...] = Field(
        min_length=6, max_length=6, description="Six tosses, bottom line first."
    )
    values: tuple[LineValue, ...] = Field(
        min_length=6, max_length=6, description="Line values 6/7/8/9, bottom line first."
    )
    primary: Hexagram
    changing_lines: tuple[Position, ...] = Field(description="Positions whose value is 6 or 9.")
    transformed: Hexagram | None = Field(description="Primary with changing lines flipped.")
    question: str | None = Field(description="Echoed verbatim. The server never analyses it.")
    source: str = Field(description="Edition and editing provenance of the returned texts.")
    notice: str

    @model_validator(mode="after")
    def _record_is_consistent(self) -> Self:
        if tuple(toss.value for toss in self.tosses) != self.values:
            raise ValueError("values do not match the coin tosses")
        if "".join("1" if v.is_yang else "0" for v in self.values) != self.primary.binary:
            raise ValueError("primary hexagram does not match the line values")
        changing = tuple(i for i, v in enumerate(self.values, start=1) if v.is_changing)
        if changing != self.changing_lines:
            raise ValueError("changing_lines do not match the line values")
        if self.transformed is None:
            if changing:
                raise ValueError("lines change, so a transformed hexagram is required")
        elif not changing:
            raise ValueError("no lines change, so there can be no transformed hexagram")
        elif flip(self.primary.binary, changing) != self.transformed.binary:
            raise ValueError("transformed hexagram is not the primary with its lines flipped")
        return self


class LineValueInfo(_Frozen):
    """How one of the four line values arises and what it means."""

    value: LineValue
    name: str
    heads: int = Field(description="How many of the three coins show heads.")
    probability: str = Field(description="Chance per line, as a fraction.")
    is_yang: bool
    is_changing: bool


class MethodDescription(_Frozen):
    """A structured explanation of the three-coin method and of this server's data."""

    coins: str
    line_values: tuple[LineValueInfo, ...]
    building_the_hexagram: str
    changing_lines: str
    transformed_hexagram: str
    source: str
    licence: str
    notice: str


@dataclass(frozen=True, slots=True)
class Book:
    """The loaded, validated text of the I Ching. Immutable; build it with `book.load_book()`."""

    trigrams: Mapping[str, Trigram]
    hexagrams: Mapping[int, Hexagram]
    by_binary: Mapping[str, int]
    source: str
    licence: str
