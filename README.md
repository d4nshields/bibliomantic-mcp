# bibliomantic-mcp

A local, offline [MCP](https://modelcontextprotocol.io) server that consults the *I Ching*
(the Chinese *Book of Changes*) with the traditional three-coin method and returns the
canonical text. It takes its spirit from the consultations in Philip K. Dick's *The Man in
the High Castle*, where characters cast the oracle and then reason about what it means for
their situation.

**The server casts and retrieves; the host model interprets.** It tosses coins with the
operating system's cryptographic RNG, maps them to a hexagram (and a transformed hexagram
when lines change), and returns a complete, auditable record with James Legge's
public-domain translation. It calls no LLM or external API, keeps no state, and never
analyses your question. Your MCP host (Claude Desktop, Claude Code, the MCP Inspector, …)
does the interpreting.

> **For reflection and creativity, not prediction and not advice.** A cast is a prompt for
> thinking about a situation from an unfamiliar angle. It has no predictive power.

Built on the MCP Python SDK v2 (`mcp>=2.3,<3`), speaking protocol revision **2026-07-28**.

## Capabilities

This section is checked against the running server by `tests/test_readme.py`: if a tool,
resource or prompt is added, removed or renamed without updating this list, the tests fail.

### Tools

All tools are annotated read-only and closed-world, and return structured output.

| Tool | Arguments | Returns |
|---|---|---|
| `cast_hexagram` | `question` (optional, echoed verbatim) | A full `Cast`: six coin tosses, line values, primary hexagram, changing lines, transformed hexagram |
| `get_hexagram` | `number` (1–64) | One `Hexagram` with its judgment, image and six lines |
| `get_trigram` | `name` (English, any case, or Chinese character) | One `Trigram` |
| `describe_method` | none | How the three-coin method works, and the text's source and licence |

### Resources

| URI | Type | Contents |
|---|---|---|
| `iching://hexagrams` | `text/markdown` | Index of all 64: number, symbol, name, Chinese |
| `iching://method` | `text/markdown` | The method description, as Markdown |

### Resource templates

| URI template | Type | Contents |
|---|---|---|
| `iching://hexagram/{number}` | `application/json` | One hexagram. `number` completes to 1–64 |
| `iching://trigram/{name}` | `application/json` | One trigram. `name` completes to the eight names |

### Prompts

| Prompt | Arguments | What it asks the host to do |
|---|---|---|
| `consult` | `question` | Cast, then reflect on the reading for the question |
| `consult_decision` | `situation`, `options` | Cast, then use the reading as a lens on each option |
| `study_hexagram` | `number` (completes to 1–64) | Read `iching://hexagram/{number}` and teach it |

## Run

```console
uv run bibliomantic-mcp            # stdio (default)
```

## Development

```console
uv sync
uv run pytest                       # every warning is an error
uv run ruff check && uv run ruff format --check
uv run mypy src
```

Design notes live in [`docs/`](docs/): the [SDK notes](docs/SDK-NOTES.md) and the
[decision records](docs/adr/). The originating
specification is [`docs/BRIEF.md`](docs/BRIEF.md).

## Licence

MIT, © Daniel Shields. The I Ching texts are from James Legge's 1882 translation, which is
in the public domain. See [`src/bibliomantic_mcp/data/SOURCES.md`](src/bibliomantic_mcp/data/SOURCES.md).
