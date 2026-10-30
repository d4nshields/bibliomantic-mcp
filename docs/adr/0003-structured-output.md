# ADR-0003: Every tool returns structured output, and is annotated read-only

**Status:** Accepted

## Context

A tool result has two channels: `content`, the text the model reads, and
`structured_content`, typed data for the host application, described in advance by the
tool's `output_schema`. Tools can also carry annotations: hints that help a host decide
whether to ask the user before running a tool.

## Decision

**Structured output everywhere.** Each tool's return annotation is a Pydantic model from
`models.py`, so `tools/list` advertises an `output_schema` and the SDK validates every result
against it before it is sent.

| Tool | Returns | `content` (for the model) |
|---|---|---|
| `cast_hexagram` | `Cast` | a concise reading written by `render.cast_summary` |
| `get_hexagram` | `Hexagram` | the SDK's JSON rendering of the model |
| `get_trigram` | `Trigram` | the SDK's JSON rendering of the model |
| `describe_method` | `MethodDescription` | the SDK's JSON rendering of the model |

`cast_hexagram` is the one exception to "let the SDK render it". A full `Cast` holds two
complete hexagrams, so as JSON it is long and repetitive for a model to read. The tool
returns `Annotated[CallToolResult, Cast]`: it writes `content` itself (symbol, number, name,
line values, judgment, changing lines and their texts, transformed hexagram, notice). The
annotation keeps `Cast` as the advertised `output_schema`, and the SDK still validates
`structured_content` against it.

**Annotations.** Every tool gets `read_only_hint=True` and `open_world_hint=False`: they
read a closed local book and change nothing.

The brief asked for `idempotent_hint` "as appropriate". The MCP spec and the SDK's Tools
page define `idempotent_hint` (and `destructive_hint`) only for tools that are **not**
read-only: "is calling it twice the same as calling it once, *for the environment*?". A
read-only tool has no effect on the environment either way, so the hint says nothing, and
setting it would suggest that hosts read it. We leave it unset. That `cast_hexagram` gives a
different answer each time is stated in its description instead ("Every call casts fresh
coins"), which is where a model looks.

**Errors.** Domain misses become `ToolError` with a message the model can act on (for
example, the list of valid trigram names). Out-of-range input such as `get_hexagram(65)` is
rejected by the input schema (`Field(ge=1, le=64)`) before the function runs. The `ToolError`
behind it is defence in depth. Nothing returns an "Error: …" string, and nothing catches
everything.

## Consequences

- A host can render casts natively (draw the figure, highlight changing lines) from
  `structured_content` without parsing text.
- The `Cast` model checks its own consistency, so a client that re-validates the structured
  content (as `tests/test_server.py` does) re-runs the audit for free.
- If a model is added or changed, the published schema changes with it automatically.
