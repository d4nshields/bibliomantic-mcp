"""Check the judge pipeline with a fake Responses API."""

import json
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "winner, verdict", [("A", "improved"), ("B", "regressed"), ("tie", "no material change")]
)
def test_judge_maps_blinded_results(
    monkeypatch: pytest.MonkeyPatch, winner: str, verdict: str
) -> None:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts/compare"))
    import importlib

    judge = importlib.import_module("judge_mcp")
    record = dict.fromkeys(judge.INVARIANTS)
    baseline = {
        "casts": {case: {"cast": record, "text": "baseline packet"} for case in judge.CASES},
        "prompts": {"consult": {"text": "baseline prompt"}},
        "server_instructions": "baseline guidance",
        "metadata": {"sha": "base"},
    }
    candidate = {
        **baseline,
        "casts": {case: {"cast": record, "text": "candidate packet"} for case in judge.CASES},
        "prompts": {"consult_creative_work": {"text": "creative prompt", "available": True}},
        "metadata": {"sha": "head"},
    }
    prompts = []

    def respond(
        key: str, model: str, instructions: str, data: dict[str, str], *, judge: bool = False
    ) -> str:
        if judge:
            assert model == "judge-model"
            assert (data["A"], data["B"]) == ("candidate packet", "baseline packet")
            return json.dumps({"winner": winner, "evidence": "A follows the Image."})
        prompts.append(data["consultation_prompt"])
        assert model == "reader-model"
        return data["packet"]

    monkeypatch.setattr(judge.random.SystemRandom, "shuffle", lambda _, order: order.reverse())
    monkeypatch.setattr(sys.modules["judge_mcp"], "respond", respond)
    report = judge.evaluate(baseline, candidate, "fake-key", "reader-model", "judge-model")
    assert report["baseline"] == "base"
    assert report["candidate"] == "head"
    assert {result["verdict"] for result in report["cases"].values()} == {verdict}
    assert prompts == ["baseline prompt", "creative prompt"] * len(judge.CASES)
