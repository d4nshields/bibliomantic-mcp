> **Tired of watching your LLM queries wander down the wrong path because of random hallucinations?**
>
> Why leave the randomness entirely to the model?

**bibliomantic-mcp** gives an LLM a different source of uncertainty: randomly selected context drawn from the *I Ching*.

The inspiration comes from Philip K. Dick's science-fiction novel *The Man in the High Castle*. Throughout the novel, characters consult the *I Ching* when making decisions. Its influence extends beyond the characters themselves: the oracle affects the direction of the story, the fictional book within the story, and—famously—the process Philip K. Dick used while writing the novel.

This MCP server applies that idea to an LLM.

Rather than asking the model to simply invent another direction when reasoning or writing reaches an uncertain point, the user can explicitly invoke the server to introduce an *I Ching* consultation into the model's context. The resulting hexagram becomes an external, stochastic influence that the LLM can interpret and incorporate into whatever it is doing.

In other words:

**If your LLM is going to hallucinate anyway, you might as well give its hallucinations some ancient Chinese wisdom to work with.**

The server does nothing until it is called, and it is designed to be called **when the end user asks for a consultation**. It is not intended to autonomously interfere with ordinary model responses.

And, importantly, this project does **not** claim that the *I Ching* predicts the future or provides reliable real-world advice. It is an experimental, literary, philosophical, and creative-writing tool—particularly suitable for anyone curious about what happens when an AI system is allowed to wander through the same sort of bibliomantic machinery that helped shape a Philip K. Dick novel.

## What Is This?

**bibliomantic-mcp** is a Model Context Protocol server that allows an MCP-compatible AI application to consult the *I Ching*.

It provides:

* All 64 hexagrams, each with its complete traditional text: judgment, image and all six line texts (see [Content Coverage](#content-coverage))
* Three-coin divination simulation, including changing lines and the hexagram they change into
* Randomized bibliomantic context for LLM reasoning and writing
* Individual hexagram and trigram lookup
* MCP resources containing hexagram data
* Prompts that start a consultation with one click
* Structured consultation records designed for AI use

The interesting part is not merely generating a hexagram.

The interesting part is putting that hexagram **inside an LLM's context** and seeing what the model does with it.

## The Idea

Large language models are probabilistic systems. When confronted with ambiguity, incomplete information, creative choices, or multiple plausible reasoning paths, they must choose among possibilities.

Normally, those choices emerge entirely from the model itself.

Bibliomantic MCP introduces an additional influence.

```text
User question
     │
     ▼
    LLM
     │
     │ user requests bibliomantic consultation
     ▼
bibliomantic-mcp
     │
     ▼
three-coin I Ching simulation
     │
     ▼
hexagram + its traditional text
     │
     ▼
added to LLM context
     │
     ▼
LLM interprets it and continues with a new influence
```

The oracle does not replace the model's reasoning.

It perturbs it.

The server only casts the coins and hands over the book. Every word of interpretation comes from the LLM, which is the one that knows what you are working on.

That makes the server potentially interesting for:

* creative writing
* speculative reasoning
* brainstorming
* narrative generation
* alternative perspectives
* experiments involving stochastic AI behavior
* literary experiments inspired by Philip K. Dick

## Philip K. Dick and *The Man in the High Castle*

The central inspiration for this project is Philip K. Dick's *The Man in the High Castle*.

The *I Ching* occupies an unusual position in the novel. Characters repeatedly consult it when deciding what to do, allowing apparently random divinations to alter their actions and therefore the course of the story.

The idea becomes recursive.

The novel contains a fictional novel, *The Grasshopper Lies Heavy*, whose existence influences the characters living inside Dick's alternate history. Meanwhile, Dick himself used the *I Ching* while writing *The Man in the High Castle*.

The result is an unusual feedback loop between:

* author
* oracle
* story
* characters
* story-within-the-story

**bibliomantic-mcp explores what happens when an LLM is inserted into that loop.**

Instead of:

```text
Author → I Ching → Story
```

we can now experiment with:

```text
Human → LLM → I Ching → LLM → Story
```

## A Note About "Hallucinations"

The term *hallucination* is used somewhat playfully here.

This server does **not** technically prevent LLM hallucinations, improve factual accuracy, or make unreliable model output trustworthy.

In fact, its purpose is almost the opposite.

Bibliomantic MCP deliberately introduces an external, randomly selected conceptual influence when the user asks for one.

For factual questions, this may be completely inappropriate.

For fiction, brainstorming, speculative thinking, and experiments in AI creativity, however, deliberately steering the model toward an unexpected conceptual path can be the entire point.

## Capabilities

This is everything the server offers. The list is checked against the running server by `tests/test_readme.py`, so if a tool, resource or prompt is added, removed or renamed without updating this section, the tests fail.

### Tools

Tools are what the AI calls. `cast_hexagram` is the consultation itself: it tosses the coins and returns the full record, with the coins, the line values, the hexagram, any changing lines and the hexagram they change into. The other tools look things up in the book.

Every tool is marked read-only, and every tool returns structured data as well as a short text summary for the model.

| Tool | Arguments | Returns |
|---|---|---|
| `cast_hexagram` | `question` (optional, up to 2,000 characters, echoed verbatim) | A full `Cast`: six coin tosses, line values, primary hexagram, changing lines, transformed hexagram |
| `get_hexagram` | `number` (1–64) | One `Hexagram` with its judgment, image and six lines |
| `get_trigram` | `name` (English, any case, or Chinese character) | One `Trigram` |
| `describe_method` | none | How the three-coin method works, and the text's source and licence |

### Resources

Resources are reference material your AI application can load into the conversation directly, without a tool call.

| URI | Type | Contents |
|---|---|---|
| `iching://hexagrams` | `text/markdown` | Index of all 64: number, symbol, name, Chinese |
| `iching://method` | `text/markdown` | The method description, as Markdown |

### Resource templates

One hexagram or trigram at a time. For example, `iching://hexagram/1` loads hexagram 1. Hosts that support completion suggest values as you type.

| URI template | Type | Contents |
|---|---|---|
| `iching://hexagram/{number}` | `application/json` | One hexagram. `number` completes to 1–64 |
| `iching://trigram/{name}` | `application/json` | One trigram. `name` completes to the eight names |

### Prompts

Prompts are ready-made requests you pick from your host's menu. Each one asks the AI to consult the oracle and then do something with the result.

| Prompt | Arguments | What it asks the host to do |
|---|---|---|
| `consult` | `question` | Cast, then reflect on the reading for the question |
| `consult_decision` | `situation`, `options` | Cast, then use the reading as a lens on each option |
| `study_hexagram` | `number` (completes to 1–64) | Read `iching://hexagram/{number}` and teach it |

These prompts are examples of how an MCP client can bring bibliomantic context into a larger conversation. They should not be interpreted as endorsements of the *I Ching* as a source of professional or real-world advice.

## Content Coverage

All 64 hexagrams carry their complete traditional text, from James Legge's 1882 translation, which is in the public domain:

| Every hexagram carries | |
| --- | --- |
| Identity | English name, Chinese name, pinyin, Unicode symbol, and its upper and lower trigrams |
| Judgment | The text attached to the hexagram as a whole |
| Image | The "Great Symbolism" commentary on the hexagram's two trigrams |
| Lines | A text for each of the six lines, read when that line is a changing line |
| Commentary | Hexagrams 1 and 2 only: the extra text for when all six lines change |

The eight trigrams carry their attributes, images and family roles from the same volume.

Every judgment, image and line text is Legge's, lightly modernised. **Nothing is generated or paraphrased.** The server checks the whole book when it starts (64 hexagrams, unique figures, each one built from its two trigrams) and refuses to run if anything is missing. The English hexagram names are short titles in common use, not all of them Legge's. [`SOURCES.md`](src/bibliomantic_mcp/data/SOURCES.md) records exactly where each text came from and how it was edited.

## Installation & Configuration

Choose one of the methods below to connect the Bibliomantic server to your MCP host (such as Claude Desktop or Claude Code).

### Option 1: Modern & Automatic (Recommended)

If you have [uv](https://docs.astral.sh/uv/) installed, you do not need to clone or manually install anything. `uvx` fetches the package from GitHub, installs it into a cached environment and runs the `bibliomantic-mcp` entry point. uv also fetches Python 3.12 if you don't have it.

Add the following to your `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "bibliomantic": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/d4nshields/bibliomantic-mcp",
        "bibliomantic-mcp"
      ]
    }
  }
}
```

If Claude Desktop cannot find `uvx`, use the absolute path from `which uvx` as `command`.

For Claude Code, the same thing is one command:

```bash
claude mcp add bibliomantic -- uvx --from git+https://github.com/d4nshields/bibliomantic-mcp bibliomantic-mcp
```

Run `/mcp` in a Claude Code session to confirm it is connected.

To pin to a specific commit instead of following `main`, append `@<commit-sha>` to the URL, e.g. `git+https://github.com/d4nshields/bibliomantic-mcp@<commit-sha>`. To pin to a release, use its tag, e.g. `@v1.0.0`.

#### Staying up to date

`uvx` keeps the installed package in a local cache, so after a new version is published your host may keep launching the build it already has. To make `uvx` check GitHub for this package every time the server starts, add `--refresh-package` before `--from`:

```json
{
  "mcpServers": {
    "bibliomantic": {
      "command": "uvx",
      "args": [
        "--refresh-package",
        "bibliomantic-mcp",
        "--from",
        "git+https://github.com/d4nshields/bibliomantic-mcp",
        "bibliomantic-mcp"
      ]
    }
  }
}
```

Things to know before you add it:

* **It only affects startup.** The check happens once, when the host launches the server. Tool calls are not slowed at all.
* **Every launch then needs the network.** If GitHub or the package index cannot be reached, the server may fail to start where a cached copy would have worked. For everyday use you can leave the flag out and add it only when you want to pick up an update.
* **Prefer `--refresh-package` to `--refresh`.** Plain `--refresh` rechecks every cached dependency, not just this package, and is slower for no benefit here.
* **A pinned commit never needs it.** If you pinned the URL to a commit as described above, that version cannot change. To update, change the commit in the URL.
* **Restart the host afterwards.** The server process is started once and keeps its code in memory. New code is only loaded when the host starts the server again, which for Claude Desktop means quitting it completely (from the system tray on Windows, not just closing the window) and reopening it.

## ⚠️ Security & Supply Chain Notice

Model Context Protocol (MCP) servers run with local system permissions granted by your AI host (like Claude Desktop). Running servers directly from remote sources introduces security risks.

Before installing or running *any* MCP server:
1. **Audit the Source:** Review the codebase to ensure it contains no malicious scripts or unexpected network behaviors.
2. **Understand the Risk of Direct Remote Execution:** Using tools like `uvx --from git+https://...` means you are executing the latest code directly from the web. If a repository is compromised, malicious code could execute on your machine.
3. **Use Content Hashes/Pins:** For maximum security, pin your configurations to specific git commit hashes rather than floating branches like `main`.

---

### Option 2: Local STDIO Setup (Manual Environment)

If you prefer to run the server from your own copy of the code, using standard I/O (STDIO), follow these steps:

1. **Clone the repository and install its environment:**
   ```bash
   git clone https://github.com/d4nshields/bibliomantic-mcp.git
   cd bibliomantic-mcp
   uv sync
   ```
   *(Without uv, `pip install .` in a Python 3.12+ virtual environment also works, and puts a `bibliomantic-mcp` command in that environment.)*

2. **Configure your host:**
   Add the server to your configuration file. Replace `/absolute/path/to/bibliomantic-mcp` with the folder you cloned into:

   ```json
   {
     "mcpServers": {
       "bibliomantic": {
         "command": "uv",
         "args": ["run", "--directory", "/absolute/path/to/bibliomantic-mcp", "bibliomantic-mcp"]
       }
     }
   }
   ```

   Or, for Claude Code:

   ```bash
   claude mcp add bibliomantic -- uv run --directory /absolute/path/to/bibliomantic-mcp bibliomantic-mcp
   ```

3. **Updating later:**
   A manual install does not update itself. To move to a newer version, pull the changes and sync again, then restart your MCP host completely so it launches the new code:
   ```bash
   git pull
   uv sync
   ```

### Option 3: Over HTTP

The server can also listen on a port instead of being launched by the host:

```bash
uv run bibliomantic-mcp --transport streamable-http --port 8000   # http://127.0.0.1:8000/mcp
```

Then point your host at `http://127.0.0.1:8000/mcp`. For Claude Code:

```bash
claude mcp add --transport http bibliomantic http://127.0.0.1:8000/mcp
```

The HTTP server has no authentication. It listens only on your own machine by default, and should stay that way (see [Security and Privacy](#security-and-privacy)).

## Example Usage

### Creative writing

Ask your MCP-enabled AI:

> I'm stuck on what should happen next in this story. Consult the I Ching and use the result as an influence on the next scene.

### Breaking a reasoning deadlock

> There are several plausible ways to approach this fictional problem. Consult the I Ching and use the result to choose an unexpected direction to explore.

### Philip K. Dick-style experiment

> Consult the I Ching using the bibliomantic server. Treat the result as an external influence on the direction of this science-fiction story.

### Weighing options

Pick the **`consult_decision`** prompt from your host's prompt menu, describe the situation, and list the options. The AI casts once and uses the same reading as a lens on each option.

### Basic divination

> Perform an I Ching divination and explain the resulting hexagram.

### Specific hexagram

> Tell me about I Ching hexagram 42.

## How the Divination Works

The server simulates the traditional three-coin method.

Three coins are tossed six times, building the hexagram from the bottom line up. Heads count 3 and tails count 2, so each toss totals 6, 7, 8 or 9:

| Total | Heads | Line | Changing? |
| --- | --- | --- | --- |
| 6 | 0 | yin (broken) | yes: becomes yang |
| 7 | 1 | yang (solid) | no |
| 8 | 2 | yin (broken) | no |
| 9 | 3 | yang (solid) | yes: becomes yin |

The six lines identify one of the 64 hexagrams. Any changing lines are then flipped to give a second, transformed hexagram: the situation the first one is moving towards. The texts for the changing lines are where traditional readings put their weight.

Randomness comes from the operating system's cryptographic random number generator, through Python's `secrets` module.

The important distinction is that the random result is generated **outside the LLM**.

That means the model does not get to quietly choose the supposedly "random" piece of wisdom that happens to fit the answer it was already constructing.

The MCP server chooses first.

The LLM has to deal with what it gets.

And because the record includes every coin toss, you can check the result by hand against any printed *I Ching*.

That constraint is a significant part of the experiment.

## Why External Randomness?

An LLM asked to "pick something random" is still generating tokens according to its learned probability distribution.

Bibliomantic MCP instead introduces a result produced outside the model.

This creates a simple form of stochastic context injection:

```text
LLM state
   +
externally generated random event
   +
the hexagram's traditional text
   =
new model context
```

The result can push a conversation toward concepts or associations that might otherwise have had very low probability of appearing.

For creative applications, that can be useful.

Or at least interesting.

## User Control

Bibliomantic consultation is intended to be **explicitly invoked**.

The server does not need to participate in every query and should not silently inject divinations into unrelated conversations. In MCP, it is the AI that decides when to call a tool, and your host decides whether to ask you first. The server's tools are all marked read-only, and its instructions to the AI describe what the oracle is for, not a reason to consult it unprompted. The prompts are always your choice: they only run when you pick one.

A user might work normally with an LLM for an extended period and invoke the oracle only when they want:

* an unexpected direction
* a narrative disruption
* an alternative interpretation
* a creative constraint
* a deliberate random influence

This keeps the oracle in approximately the role it occupies in *The Man in the High Castle*: something consulted when a character—or in this case, a user—decides to consult it.

## Ethical Framing

Every cast carries a one-line notice, in both the text the AI reads and the structured record:

> For reflection and creativity only: a cast makes no prediction and is not advice.

The server's MCP `instructions` field tells every host the same thing, and leaves the interpreting to the AI. Each prompt frames its reading as reflection, not prediction. The notice is part of the record and cannot be switched off.

Because an MCP tool result is read by the model, which then writes its own reply, the server can frame the result but cannot control how the assistant presents it. To see exactly what the server returned, expand the tool call in your MCP host.

The reasoning behind keeping the server out of interpretation is recorded in [ADR-0001](docs/adr/0001-server-does-not-interpret.md).

## Intended Uses

Good uses include:

* Science-fiction writing
* Philip K. Dick-inspired literary experiments
* Plot generation
* Character decisions
* World-building
* Creative brainstorming
* Perspective shifting
* Generative-art experiments
* Studying human/AI interaction with random external context
* Demonstrating MCP tools, resources and prompts

## Not Intended For

Do not treat output from this server as authoritative guidance for:

* medical decisions
* legal decisions
* financial decisions
* personal safety
* mental-health treatment
* major life decisions
* predictions of future events

The server does not establish that divination works, that an oracle possesses knowledge, or that randomly selected philosophical text provides factual evidence.

**This is an experimental creative tool, not an oracle you should bet your life on.**

If Philip K. Dick-style weirdness emerges from your LLM session, however, the software is probably working as intended.

## Technical Implementation

The project uses:

* **Python 3.12**, managed with **uv**
* **MCP Python SDK v2 (`MCPServer`)**, `mcp>=2.3,<3`
* **Model Context Protocol** revision 2026-07-28, over stdio or streamable HTTP. Over HTTP the server is stateless: it keeps no sessions, so any copy of it can answer any request.
* The complete Legge text as JSON data, validated when the server starts
* Python's `secrets` module for external randomness
* Pydantic models and strict type checking. The tools' input and output schemas are generated from their type hints.
* A domain layer (casting, the book, rendering) that never imports `mcp`. A test enforces it.
* MCP tools, resources, resource templates, completions and prompts

The server requires no external API to perform a consultation, and calls no LLM.

## Development

### Run locally

```bash
uv sync
uv run bibliomantic-mcp                                           # stdio
uv run bibliomantic-mcp --transport streamable-http --port 8000   # HTTP
uv run bibliomantic-mcp --help
```

Logs go to stderr; on stdio, stdout carries only the protocol. `python -m bibliomantic_mcp` works the same way.

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run --directory "$PWD" bibliomantic-mcp
```

This opens the Inspector UI with the server launched over stdio. The Inspector also has a scriptable CLI mode:

```bash
npx @modelcontextprotocol/inspector --cli uv run --directory "$PWD" bibliomantic-mcp --method tools/list
```

(`mcp dev` is not used: it needs a module-level server object, and this project builds its server in a factory. See [ADR-0004](docs/adr/0004-server-factory-and-inspector.md).)

### Tests and checks

```bash
uv run pytest                       # every warning is an error
uv run ruff check && uv run ruff format --check
uv run mypy src
```

Design notes live in [`docs/`](docs/): the [architecture](docs/ARCHITECTURE.md), the [SDK notes](docs/SDK-NOTES.md) and the [decision records](docs/adr/). The originating specification is [`docs/BRIEF.md`](docs/BRIEF.md).

## Security and Privacy

The server is deliberately simple.

* No persistent user tracking, and nothing stored between consultations
* Your question is echoed back in the cast, but never analysed, stored or logged
* No external API dependency, and no network requests of its own
* Input validation for server parameters: questions up to 2,000 characters, hexagram numbers 1–64, trigram names checked against the eight
* Randomness generated locally
* Consultation occurs only when invoked
* Over HTTP, the server listens on `127.0.0.1` by default and has no authentication. Don't expose it on a public network interface.

As with any MCP server, users should review the source code and understand the permissions granted to an MCP server before enabling it in an AI host.

## Contributing

Contributions are welcome.

When contributing:

1. Follow the existing code style (`ruff`, strict `mypy`).
2. Preserve compatibility with MCP clients.
3. Add or update tests when changing behavior.
4. Update documentation in the same change. The [Capabilities](#capabilities) section is checked by the tests.
5. Preserve the distinction between creative bibliomancy and factual or professional advice.
6. Keep the weird part weird.

## License

MIT License. See [LICENSE](LICENSE) for details. The *I Ching* texts are from James Legge's 1882 translation, which is in the public domain; see [`SOURCES.md`](src/bibliomantic_mcp/data/SOURCES.md).

## Acknowledgments

This project owes its existence to an unusual chain of ideas:

* the ancient Chinese *I Ching*
* centuries of bibliomantic practice
* James Legge, whose 1882 translation supplies every word of the text
* Philip K. Dick
* *The Man in the High Castle*
* modern large language models
* Model Context Protocol
* and the questionable but irresistible idea that an AI's random wanderings might benefit from consulting a 3,000-year-old book first.

---
