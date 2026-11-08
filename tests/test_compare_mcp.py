"""Exercise the comparator without requiring the reading branch."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/compare/compare_mcp.py"


@pytest.mark.parametrize(
    ("profile", "enriched", "changed", "exit_code"),
    [
        (False, False, False, 0),
        (True, True, False, 0),
        (True, False, False, 1),
        (False, False, True, 1),
    ],
)
def test_compare_cli(
    tmp_path: Path, profile: bool, enriched: bool, changed: bool, exit_code: int
) -> None:
    baseline, candidate = tmp_path / "before.json", tmp_path / "after.json"
    cast: dict[str, Any] = {
        "tosses": [{"heads": [True, False, False]}] * 6,
        "values": [7] * 6,
        "primary": {
            "number": 1,
            "judgment": "Judgment text",
            "image": "Image text",
            "lower": "Heaven",
            "upper": "Heaven",
            "lines": [{"position": 1, "text": "Unselected line"}],
        },
        "changing_lines": [],
        "transformed": None,
        "question": None,
        "notice": "For reflection.",
    }
    capture: dict[str, Any] = {
        "metadata": {},
        "casts": {"steady": {"cast": cast, "text": "Judgment text"}},
        "lookup_20": {"structuredContent": {"number": 20}},
        "prompts": {},
    }
    baseline.write_text(json.dumps(capture), encoding="utf-8")
    if enriched:
        cast["source"] = "Legge"
        capture["casts"]["steady"]["text"] = (
            "Judgment text\nImage text\nTrigrams: Heaven below, Heaven above.\n"
            "No changing lines.\nLegge"
        )
        capture["prompts"]["consult_creative_work"] = {"available": True}
    if changed:
        cast["question"] = "A different question"
    candidate.write_text(json.dumps(capture), encoding="utf-8")
    command = [sys.executable, str(SCRIPT), str(baseline), str(candidate)]
    if profile:
        command.append("--expect-reading-improvements")
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == exit_code, result.stdout + result.stderr
    if changed:
        assert "question changed" in result.stderr
    elif profile and not enriched:
        assert "missing source" in result.stderr
