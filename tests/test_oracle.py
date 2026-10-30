"""The casting rules, tested as plain Python with no server in sight."""

import random
from collections import Counter
from itertools import product

import pytest
from pydantic import ValidationError

from bibliomantic_mcp import oracle
from bibliomantic_mcp.book import load_book
from bibliomantic_mcp.models import HEXAGRAM_COUNT, Cast, CoinToss, LineValue

BOOK = load_book()


# --- Coins -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("heads", "expected"),
    [
        ((True, True, True), LineValue.OLD_YANG),  # 3+3+3 = 9
        ((True, True, False), LineValue.YOUNG_YIN),  # 3+3+2 = 8
        ((True, False, False), LineValue.YOUNG_YANG),  # 3+2+2 = 7
        ((False, False, False), LineValue.OLD_YIN),  # 2+2+2 = 6
    ],
)
def test_coin_values(heads: tuple[bool, bool, bool], expected: LineValue) -> None:
    assert CoinToss(heads=heads).value is expected


def test_only_the_number_of_heads_matters() -> None:
    for coins in product((True, False), repeat=3):
        assert CoinToss(heads=coins).value == 6 + sum(coins)


def test_line_value_helpers() -> None:
    assert [v.is_yang for v in LineValue] == [False, True, False, True]
    assert [v.is_changing for v in LineValue] == [True, False, False, True]


# --- A seeded cast is reproducible -----------------------------------------


def test_seeded_cast_is_reproducible() -> None:
    first = oracle.cast(BOOK, "Should I?", rng=random.Random(2026))
    second = oracle.cast(BOOK, "Should I?", rng=random.Random(2026))
    assert first == second


def test_specific_seeded_cast() -> None:
    """Pin one cast so any change to the casting rules shows up as a test failure."""
    result = oracle.cast(BOOK, rng=random.Random(41))
    assert [int(v) for v in result.values] == [6, 8, 8, 8, 7, 9]
    # yin yin yin | yin yang yang: Earth (000) below, Wind (011) above.
    assert result.primary.binary == "000011"
    assert result.primary.number == 20  # Contemplation
    assert result.changing_lines == (1, 6)
    # Flip lines 1 and 6: Thunder (100) below, Water (010) above.
    assert result.transformed is not None
    assert result.transformed.binary == "100010"
    assert result.transformed.number == 3  # Difficulty at the Beginning


def test_question_is_echoed_verbatim() -> None:
    question = "  Will the **meeting** go well?\n"
    assert oracle.cast(BOOK, question, rng=random.Random(1)).question == question
    assert oracle.cast(BOOK, rng=random.Random(1)).question is None


def test_cast_carries_the_notice() -> None:
    assert oracle.cast(BOOK, rng=random.Random(1)).notice == oracle.NOTICE


def test_default_rng_is_the_system_csprng(monkeypatch: pytest.MonkeyPatch) -> None:
    used: list[str] = []

    class Spy(random.SystemRandom):
        def getrandbits(self, k: int) -> int:
            used.append("system")
            return super().getrandbits(k)

    monkeypatch.setattr(oracle.secrets, "SystemRandom", Spy)
    oracle.cast(BOOK)
    assert len(used) == 18  # 6 lines x 3 coins


# --- Statistics ------------------------------------------------------------


def test_line_values_follow_1_3_3_1() -> None:
    """Three fair coins give 6:7:8:9 in the ratio 1:3:3:1."""
    rng = random.Random(7)
    trials = 80_000
    counts = Counter(oracle.toss_coins(rng).value for _ in range(trials))
    for value, share in {6: 1 / 8, 7: 3 / 8, 8: 3 / 8, 9: 1 / 8}.items():
        assert counts[LineValue(value)] / trials == pytest.approx(share, abs=0.01)


# --- Changing lines and the transformed hexagram ---------------------------


@pytest.mark.parametrize("seed", range(300))
def test_transformed_iff_changing_lines(seed: int) -> None:
    result = oracle.cast(BOOK, rng=random.Random(seed))
    has_old = any(v in (LineValue.OLD_YIN, LineValue.OLD_YANG) for v in result.values)
    assert (result.transformed is not None) == has_old


@pytest.mark.parametrize("seed", range(300))
def test_flipping_is_per_position(seed: int) -> None:
    result = oracle.cast(BOOK, rng=random.Random(seed))
    if result.transformed is None:
        return
    for position, (before, after) in enumerate(
        zip(result.primary.binary, result.transformed.binary, strict=True), start=1
    ):
        assert (before != after) == (position in result.changing_lines)


def test_flip() -> None:
    assert oracle.flip("111111", (1,)) == "011111"
    assert oracle.flip("111111", (6,)) == "111110"
    assert oracle.flip("101010", (1, 2, 3, 4, 5, 6)) == "010101"
    assert oracle.flip("101010", ()) == "101010"


def test_every_hexagram_is_reachable() -> None:
    reached = {
        oracle.hexagram_from_binary(BOOK, "".join(bits)).number for bits in product("01", repeat=6)
    }
    assert reached == set(range(1, HEXAGRAM_COUNT + 1))


def test_cast_record_rejects_tampering() -> None:
    """The Cast model re-checks its own chain of evidence."""
    good = oracle.cast(BOOK, rng=random.Random(42))
    data = good.model_dump()
    data["primary"] = BOOK.hexagrams[1].model_dump()
    with pytest.raises(ValidationError, match="primary hexagram does not match"):
        Cast.model_validate(data)


# --- Lookups ---------------------------------------------------------------


def test_lookup_by_number() -> None:
    assert oracle.hexagram_from_number(BOOK, 1).binary == "111111"
    for bad in (0, 65, -1):
        with pytest.raises(oracle.NotInBook, match="1–64"):
            oracle.hexagram_from_number(BOOK, bad)


def test_lookup_by_binary() -> None:
    assert oracle.hexagram_from_binary(BOOK, "000000").number == 2
    for bad in ("", "1111111", "11a111"):
        with pytest.raises(oracle.NotInBook):
            oracle.hexagram_from_binary(BOOK, bad)


@pytest.mark.parametrize("name", ["Heaven", "heaven", "HEAVEN", " Heaven ", "乾"])
def test_trigram_lookup(name: str) -> None:
    assert oracle.trigram_by_name(BOOK, name).binary == "111"


def test_trigram_miss_lists_valid_names() -> None:
    with pytest.raises(oracle.NotInBook, match="Valid names: Heaven, Lake"):
        oracle.trigram_by_name(BOOK, "Sky")


@pytest.mark.parametrize(
    ("number", "nuclear"),
    [(1, 1), (2, 2), (3, 23), (63, 64), (64, 63)],
)
def test_nuclear_hexagram(number: int, nuclear: int) -> None:
    hexagram = BOOK.hexagrams[number]
    assert oracle.nuclear_hexagram(BOOK, hexagram).number == nuclear


# --- Method description ----------------------------------------------------


def test_method_probabilities_are_computed() -> None:
    method = oracle.describe_method(BOOK)
    assert [(i.value, i.heads, i.probability) for i in method.line_values] == [
        (6, 0, "1/8"),
        (7, 1, "3/8"),
        (8, 2, "3/8"),
        (9, 3, "1/8"),
    ]
    assert "Legge" in method.source


@pytest.mark.parametrize(("text", "number"), [("1", 1), (" 64 ", 64), ("07", 7)])
def test_parse_hexagram_number(text: str, number: int) -> None:
    assert oracle.parse_hexagram_number(text) == number


@pytest.mark.parametrize("text", ["0", "65", "abc", "", "-1", "1.5", "٣"])
def test_parse_hexagram_number_rejects(text: str) -> None:
    with pytest.raises(oracle.NotInBook, match="1–64"):
        oracle.parse_hexagram_number(text)
