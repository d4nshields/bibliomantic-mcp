# Comparing reading quality

The server tests check casting, source coverage and protocol behavior. They cannot establish
whether a host model's interpretation feels specific, surprising or useful. Evaluate that
separately with fixed casts and the same conversation.

## First smoke test in your MCP host

Restart the host with this branch, then try both paths:

1. Select `consult_creative_work`. Use this work context: "An investigator has evidence
   implicating her mentor. She has never met the missing witness. The next scene takes
   place in the archive." Set uncertainty to: "Should she publish the evidence or first
   investigate its origin?"
2. In a separate conversation, supply the same context and ask directly: "Consult the
   I Ching once and let the reading change the next scene."
3. Expand each tool result. It should contain the primary Image, selected changing-line
   texts, and the related figure's Judgment and Image when lines change, plus the source.
4. Ask a follow-up about the interpretation. The model should use the existing cast or
   lookup tools, not cast again unless you request a new consultation.

The two fresh casts will differ. This smoke test checks delivery and workflow, not which
prompt gives a better interpretation.

## Controlled comparison

Generate a fixed packet without invoking the live random-casting tool:

```bash
uv run python - <<'PY'
import random
from bibliomantic_mcp import oracle, render
from bibliomantic_mcp.book import load_book

cast = oracle.cast(
    load_book(),
    question="Should the investigator publish or investigate the evidence's origin?",
    rng=random.Random(41),
)
print(render.cast_summary(cast))
PY
```

Seed 41 gives 20, changing at lines 1 and 6, related to 3. Paste the packet into a
fresh host conversation with the story context and explicitly say to interpret this
existing cast without using the casting tool. Keep the model, conversation, length request,
and any controllable sampling settings constant. Use fresh conversations per condition:

| Condition | Source packet | Instructions |
|---|---|---|
| A | Previous summary: primary Judgment, changing lines, related figure's title | Previous generic consultation request |
| B | Complete packet | Same generic request |
| C | Complete packet | Revised guidance and creative-work request |

For a clean baseline, do not attach this branch's server instructions to condition A or B.
Repeat each condition a few times; a single pleasing response is not reliable evidence.

Score the results in a shuffled order, without showing the condition labels:

| Criterion | What to look for |
|---|---|
| Source grounding | Specific, correctly attributed images or line statements |
| Context fit | Connections to facts actually provided, without invented personal facts |
| Tension | Differences between selected lines survive instead of becoming generic reassurance |
| Creative consequence | Something meaningful changes in the work; established facts survive |
| Uncertainty | Proposed applications are distinguishable from source text and prediction |
| Naturalness | Coherent reading without a compulsory list of generic advice |

Then substitute a substantially different fixed cast while preserving the story and
instructions. Does the creative consequence change in a source-grounded way? Also vary
the story while holding the cast fixed: does the application respond to the new context?
Record failures as well as successes. Do not treat model fluency or mystical tone as proof
that a reading is grounded.

Include no-changing-line cases, one and multiple changing lines, and the all-changing
cases of hexagrams 1 and 2. No-changing-line responses must not invent a second figure.
For decision prompts, check that the output can question the framing without selecting a
life decision for the user or forcing equal pros and cons for every option.

## Automated checks

```bash
uv sync --locked
uv run pytest -W error
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src
```

These checks require the project's MCP 2.x SDK and development dependencies. Passing them
does not replace the host-model comparisons above.
