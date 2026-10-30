# Bibliomantic MCP Server

A local, offline [Model Context Protocol](https://modelcontextprotocol.io) server that consults
the *I Ching* (the Chinese *Book of Changes*) with the traditional three-coin method, exploring
the bibliomantic approach described in Philip K. Dick's *The Man in the High Castle*, where
characters cast the oracle and then reason about what it means for their situation.

**The server casts and retrieves; the host model interprets.** It tosses coins with the
operating system's cryptographic RNG, maps them to a hexagram (and a transformed hexagram
when lines change), and returns a complete, auditable record with James Legge's
public-domain translation. It calls no LLM or external API, keeps no state, and never
analyses your question. Your MCP host (Claude Desktop, Claude Code, the MCP Inspector, …)
does the interpreting.

> **For reflection and creativity, not prediction and not advice.** A cast is a prompt for
> thinking about a situation from an unfamiliar angle. It has no predictive power.

Built on the MCP Python SDK v2 (`mcp>=2.3,<3`), speaking protocol revision **2026-07-28**.

## Purpose

This server shows how a traditional wisdom text can be brought into modern AI tools through
MCP, without the server pretending to be the oracle's interpreter. It provides:

- **Educational exploration** of the I Ching, through Legge's complete 1882 translation
- **Literary context** from Philip K. Dick's influential science fiction novel
- **Philosophical reflection tools** for creative thinking and perspective-taking
- **Technical demonstration** of an MCP server: tools, resources, resource templates,
  argument completion and prompts

## Features

- **Traditional I Ching system**: all 64 hexagrams and 8 trigrams, cast with the three-coin
  method, including changing lines and the transformed hexagram
- **Auditable casts**: every result records the coin tosses and line values, so it can be
  checked by hand against a printed I Ching
- **The canonical text**: judgment, image and all six line texts for every hexagram, checked
  for completeness when the server starts
- **Structured output**: tools return typed records with a published schema, plus a short text
  summary for the model
- **Clear framing**: every cast carries a notice that it is for reflection, not prediction or
  advice
- **Resource access**: hexagrams and trigrams by URI, with argument completion
- **Two transports**: stdio for hosts that launch the server, streamable HTTP for everything else

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)**. It fetches Python 3.12 or later if you don't have it.
- **An MCP-compatible host** (Claude Desktop, Claude Code, …)
- **Node.js**, only if you want the MCP Inspector

## Capabilities

This section is checked against the running server by `tests/test_readme.py`: if a tool,
resource or prompt is added, removed or renamed without updating this list, the tests fail.

### Tools

All tools are annotated read-only and closed-world, and return structured output.

| Tool | Arguments | Returns |
|---|---|---|
| `cast_hexagram` | `question` (optional, up to 2,000 characters, echoed verbatim) | A full `Cast`: six coin tosses, line values, primary hexagram, changing lines, transformed hexagram |
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

## Installation

```console
git clone https://github.com/d4nshields/bibliomantic-mcp-server.git
cd bibliomantic-mcp-server
uv sync
uv run bibliomantic-mcp                                           # stdio (the default)
uv run bibliomantic-mcp --transport streamable-http --port 8000   # http://127.0.0.1:8000/mcp
```

Options: `--transport {stdio,streamable-http}`, `--host` (default `127.0.0.1`), `--port`
(default `8000`), `--log-level` (default `INFO`). Logs go to stderr; on stdio, stdout carries
only the protocol. `python -m bibliomantic_mcp` works the same way.

### Claude Desktop

Add this to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`,
Windows: `%APPDATA%\Claude\`), then fully quit and reopen Claude Desktop:

```json
{
  "mcpServers": {
    "bibliomantic": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/bibliomantic-mcp-server", "bibliomantic-mcp"]
    }
  }
}
```

If Claude Desktop cannot find `uv`, use the absolute path from `which uv` as `command`.

### Claude Code

```console
claude mcp add bibliomantic -- uv run --directory /absolute/path/to/bibliomantic-mcp-server bibliomantic-mcp
```

Or, against a server already running over HTTP:

```console
claude mcp add --transport http bibliomantic http://127.0.0.1:8000/mcp
```

Run `/mcp` in a Claude Code session to confirm it is connected.

### MCP Inspector

```console
npx @modelcontextprotocol/inspector uv run --directory "$PWD" bibliomantic-mcp
```

This opens the Inspector UI with the server launched over stdio. For HTTP, start the server
with `--transport streamable-http`, then connect the Inspector to `http://127.0.0.1:8000/mcp`
with transport "Streamable HTTP". The Inspector also has a scriptable CLI mode:

```console
npx @modelcontextprotocol/inspector --cli uv run --directory "$PWD" bibliomantic-mcp --method tools/list
```

(`uv run mcp dev` is not used: it needs a module-level server object, and this project builds
its server in a factory. See [ADR-0004](docs/adr/0004-server-factory-and-inspector.md).)

## Usage examples

### Consultation

Ask Claude:

> *"Can you consult the I Ching for a fresh perspective on my creative projects?"*

### A decision

> *"I'm facing a difficult decision about my career path. Can you consult the I Ching?"*

Or pick the **`consult_decision`** prompt from your host's prompt menu and fill in the
situation and the options.

### Resource access

> *"Load the iching://hexagram/1 resource to understand The Creative."*

### Specific hexagram lookup

> *"Can you tell me about I Ching hexagram number 42?"*

## The bibliomantic approach

In *The Man in the High Castle*, characters consult the I Ching before important decisions and
then work out for themselves what the answer means for them. This server follows that
division of labour:

- **The traditional three-coin method.** Six tosses, bottom line first. Heads count 3, tails 2,
  so each line is 6, 7, 8 or 9; 6 and 9 are changing lines.
- **Cryptographically secure randomness** from the operating system (Python's `secrets`
  module), so the coins are unpredictable and unbiased
- **The text, not a gloss.** The server returns Legge's translation and leaves the
  interpretation to the host model, which knows the user's situation.
- **Transparency.** Every cast shows its coins, line values and changing lines.

## Ethical framework

Every cast carries a notice: *for reflection and creativity only; a cast makes no prediction
and is not advice.* The server's instructions tell every host the same thing, and each
prompt frames the reading as reflection, not prediction.

The server emphasizes:

- Educational exploration of wisdom traditions
- Creative thinking and perspective-taking
- Philosophical reflection rather than prediction
- Respect for both the ancient tradition and modern ethical standards

## Development

```console
uv sync
uv run pytest                       # every warning is an error
uv run ruff check && uv run ruff format --check
uv run mypy src
```

Design notes live in [`docs/`](docs/): the [architecture](docs/ARCHITECTURE.md), the
[SDK notes](docs/SDK-NOTES.md) and the [decision records](docs/adr/). The originating
specification is [`docs/BRIEF.md`](docs/BRIEF.md).

## Technical implementation

Built with:

- **The MCP Python SDK v2** (`MCPServer`), protocol revision 2026-07-28, stateless over HTTP
- **The complete I Ching text**: Legge's translation as JSON data, validated at startup
  (64 hexagrams, unique figures, each one built from its two trigrams)
- **Cryptographic randomness**: the three-coin cast uses `secrets.SystemRandom`
- **Type safety**: Pydantic models and strict mypy. Tool input and output schemas are
  generated from type hints.
- **A clean domain layer**: the casting and text modules never import `mcp`, and a test
  enforces it

## Use cases

- **Educational tool** for learning about the I Ching and Chinese wisdom traditions
- **Creative writing aid** for generating new perspectives and inspiration
- **Philosophical reflection** tool for contemplating decisions and changes
- **Cultural bridge** between an ancient text and modern AI tools
- **Technical demonstration** of MCP server development
- **Literary exploration** of Philip K. Dick's themes and bibliomantic concepts

## Security considerations

- Input validation: questions up to 2,000 characters, hexagram numbers 1–64, trigram names
  checked against the eight
- No network requests, no API keys, no LLM calls
- Over HTTP the server binds to `127.0.0.1` by default and has no authentication. Don't
  expose it on a public interface.
- Cryptographically secure randomness
- No persistent storage or user tracking. A question is echoed back in the cast but never
  stored, analysed or logged.

## Contributing

Contributions are welcome! Please:

1. Follow the existing code style (ruff, strict mypy)
2. Add pytest tests for new functionality
3. Update the documentation in the same change. The Capabilities section above is checked
   by the tests.
4. Stay compatible with the MCP Python SDK v2
5. Maintain the reflective framing and educational focus

## Licence

MIT, © Daniel Shields; see [LICENSE](LICENSE). The I Ching texts are from James Legge's 1882
translation, which is in the public domain. See
[`src/bibliomantic_mcp/data/SOURCES.md`](src/bibliomantic_mcp/data/SOURCES.md).

## Acknowledgments

- **Philip K. Dick** for the literary inspiration and the bibliomantic approach
- **The authors and commentators of the I Ching** across its long tradition
- **James Legge** for the translation this server ships
- **Anthropic and the MCP community** for the Model Context Protocol and its Python SDK

---

*At the close of* The Man in the High Castle, *the oracle answers with hexagram 61,
Chung Fu: "Inner Truth" in the Wilhelm translation the characters use, "Inmost Sincerity"
in Legge's.*
