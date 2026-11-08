"""Compare two complete captures from capture_mcp.py."""

import argparse
import json
from pathlib import Path
from typing import Any

INVARIANTS = ("tosses", "values", "primary", "changing_lines", "transformed", "question", "notice")


def require(condition: object, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def check_reading(name: str, cast: dict[str, Any], text: str) -> None:
    source = cast.get("source")
    require(source and source in text, f"{name}: missing source")
    figures = [cast["primary"]]
    if cast["transformed"] is None:
        require("No changing lines." in text and "Becomes" not in text, f"{name}: extra figure")
    else:
        figures.append(cast["transformed"])
    for figure in figures:
        for field in ("judgment", "image"):
            require(figure[field] in text, f"{name}: missing {field} for {figure['number']}")
        trigrams = f"Trigrams: {figure['lower']} below, {figure['upper']} above."
        require(trigrams in text, f"{name}: missing trigrams for {figure['number']}")
    for line in cast["primary"]["lines"]:
        position = line["position"]
        label = f"Line {position}: {line['text']}"
        require((label in text) == (position in cast["changing_lines"]), f"{name}: line {position}")
    if name in ("all_yang_changing", "all_yin_changing"):
        require(cast["primary"]["commentary"] in text, f"{name}: missing all-changing statement")


def compare(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    expect_reading_improvements: bool = False,
) -> None:
    require(baseline["casts"], "no casts to compare")
    require(baseline["casts"].keys() == candidate["casts"].keys(), "cast fixture sets differ")
    for name, before in baseline["casts"].items():
        after = candidate["casts"][name]
        for field in INVARIANTS:
            require(before["cast"][field] == after["cast"][field], f"{name}: {field} changed")
        if expect_reading_improvements:
            check_reading(name, after["cast"], after["text"])
        print(f"{name}: PASS ({len(before['text'])} -> {len(after['text'])} characters)")

    require(baseline["lookup_20"] == candidate["lookup_20"], "hexagram 20 lookup changed")
    if expect_reading_improvements:
        creative = candidate["prompts"].get("consult_creative_work", {})
        require(creative.get("available"), "creative consultation prompt unavailable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--expect-reading-improvements", action="store_true")
    args = parser.parse_args()
    try:
        baseline, candidate = [
            json.loads(path.read_text(encoding="utf-8")) for path in (args.baseline, args.candidate)
        ]
        print("Baseline:", baseline["metadata"])
        print("Candidate:", candidate["metadata"])
        compare(baseline, candidate, expect_reading_improvements=args.expect_reading_improvements)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        parser.exit(1, f"Comparison failed: {exc}\n")
    print("PASS: cast invariants and lookup")
    if args.expect_reading_improvements:
        print("PASS: reading-improvement expectations")


if __name__ == "__main__":
    main()
