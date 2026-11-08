# ADR-0006: Self-contained reading context and shared interpretation guidance

**Status:** Accepted

## Context

The previous text summary omitted the primary Image and gave only the transformed
hexagram's identity. Although the structured record held those passages, host delivery to
the model varies. The prompts also asked for reflection with little direction about how
the actual text should influence the response. A comparison for every option encouraged
formulaic output. There was no prompt dedicated to changing an ongoing creative work.

## Decision

- Keep the casting algorithm and the server/host boundary of ADR-0001 unchanged.
- Render both figures' identities, upper/lower trigrams, Judgments and Images, and the
  primary figure's selected changing-line texts. Retain the special all-changing texts
  for hexagrams 1 and 2. No-change casts contain only the primary figure.
- Carry `source` from the loaded book into `Cast` and its text rendering. This is an
  additive output-schema field; consumers constructing Cast records must supply it.
- Keep full line sets and coin faces in `structured_content` for audit and study.
  The text result alone suffices for the intended interpretation.
- Define `INTERPRETATION_GUIDANCE` once in `prompts.py`. Include it in server instructions
  for direct tool use and in each consultation prompt for explicit prompt selection.
  Host support determines how instructions are used; they are not an enforcement layer.
- Prioritise concrete source images, contextual relevance and unresolved tensions. Separate
  source statements from proposed applications. Do not impose a response template.
- Frame the transformed figure as a related perspective, not a promised outcome.
- Add `consult_creative_work(work_context, uncertainty)`: apply a passage-grounded creative
  constraint to the work, preserve established facts, and identify the motivating passage.
- Explicitly request user-initiated casting and reuse of a cast during follow-up discussion.
  Lookup tools retrieve more text; repeated casting must not be used to shop for an answer.

## Consequences

Packets and consultation prompts are longer, but contain material relevant to interpretation
rather than just a title. Tests check coverage and entry-path consistency instead of an
arbitrary 600-character prompt ceiling. No new model, service, persistence or interpretation
engine is added. The protocol model and historical texts remain structured and auditable.

This is one proposed reading approach, not a universal traditional rule. Mechanical tests
cannot prove richer or more useful interpretations; the manual protocol in
[Reading evaluation](../READING-EVALUATION.md) keeps casts fixed when comparing outputs.
