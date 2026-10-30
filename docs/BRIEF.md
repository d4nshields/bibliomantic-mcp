# Bibliomantic MCP Server — Clean-Room Rebuild Brief

You are building a **new** Python project from this brief alone. There is an older
implementation of this idea; you do **not** have access to it and must not go looking
for it (do not clone, search, or fetch anything from `d4nshields/bibliomantic-mcp-server`
or any package of that name). Everything you need is here. Where this brief is silent,
choose the most idiomatic, current MCP pattern and record the choice in an ADR.

The result will be shown at a conference talk (DevFest 2026 Toronto) as a worked example
of MCP server internals. Every design decision should therefore be *legible*: a reader
should be able to open any file and understand why it exists. Prefer clarity over
cleverness, and small, well-named modules over one big file.

---

## 0. Before writing any code

1. **Read the current SDK docs first.** Your training data about MCP is stale. The
   official Python SDK is on its **v2 line** (targeting the **2026-07-28** protocol
   revision), and v2 renamed and moved things. Fetch and read, in this order:
   - https://py.sdk.modelcontextprotocol.io/ (index)
   - https://py.sdk.modelcontextprotocol.io/whats-new/
   - https://py.sdk.modelcontextprotocol.io/migration/ (for the rename table — useful
     even though we are not migrating, because most web tutorials use v1 names)
   - the server tutorial / API reference pages linked from the index, specifically:
     `MCPServer`, tools (including structured output and annotations), resources and
     resource templates, prompts, completions, `Context`, lifespan, `run()` and
     transports, error handling (`ToolError`, `MCPError`), and the `mcp dev` /
     `mcp run` / `mcp install` CLI.
   - the 2026-07-28 spec changelog: https://modelcontextprotocol.io/specification/2026-07-28/changelog

   Facts to confirm against those pages before you rely on them (they were true at the
   time this brief was written; verify, don't assume):
   - server class is `MCPServer`, imported from `mcp.server`;
     `mcp.server.fastmcp` / `FastMCP` **do not exist** in v2 — never import them.
   - `MCPServer(...)` takes identity only (`name`, and by keyword: `title`,
     `instructions`, `version`, `icons`, `website_url`, `lifespan`, ...). Transport
     options (`host`, `port`, `stateless_http`, `json_response`, ...) go to `run()`.
   - decorators are `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`,
     `@mcp.completion()`; schemas come from type hints / Pydantic models.
   - `get_context()` is gone — declare a `ctx: Context` parameter when you need it.
   - **Roots, Sampling, and MCP-level logging (`ctx.info()` etc.) are deprecated** and
     emit warnings. Do not use them. Use stdlib `logging` to **stderr**.
   - `ToolError` is the only exception whose message reaches the model; raising
     `MCPError` is a protocol-level error the model never sees; any other exception
     becomes an opaque `is_error` result.
   - returning a Pydantic model / dict from a tool produces both `content` and
     `structured_content`, with an `output_schema` advertised in `tools/list`.
   - the experimental Tasks API was removed; the 2026 tasks *extension* is not yet in
     the SDK. Do not build on it.
   - Python ≥ 3.10 is required by the SDK; **target 3.12** for this project.

   **Two version axes — do not conflate them.** The *protocol* is date-versioned
   (`2025-11-25`, `2026-07-28`, …) and is what appears on the wire; the *SDK* is
   semver (`2.0.0` shipped 2026-07-28 alongside the protocol revision; `2.1`, `2.2`,
   `2.3` are library releases that still speak that same protocol). This project
   targets **protocol 2026-07-28** and pins the **SDK to `>=2.3,<3`**. Record both
   numbers — and the exact SDK patch version `uv` resolved — in `SDK-NOTES.md`. If a
   newer SDK 2.x exists when you start, use it; if a newer *protocol* revision exists,
   stop and ask before targeting it.

2. **Pin what you learn.** After reading, write `docs/SDK-NOTES.md`: a one-page summary
   of the v2 API surface this project uses, with the SDK version you installed. This
   is both a teaching artifact and a guard against future drift.

3. **Set up git before the first file.** `git init`, default branch `main`, an initial
   empty commit, then do all work on a branch named `build`. Commit at each milestone
   in §7 with a message that describes the behaviour added. Merge `build` into `main`
   only at the end, when tests pass and docs match code.

---

## 1. Purpose

A **local, offline, deterministic-except-for-the-coins** MCP server that lets an MCP
host (Claude Desktop, Claude Code, the MCP Inspector, any client) consult the
*I Ching* — the Chinese *Book of Changes* — using the traditional three-coin casting
method, in the spirit of the "bibliomantic" consultations in Philip K. Dick's novel
*The Man in the High Castle*, where characters cast the oracle and then reason about
what the result means for their situation.

**Division of labour — this is the central design idea and the talk's thesis:**

| The server does | The server does NOT do |
|---|---|
| Cast coins with a CSPRNG | Interpret the result for the user's situation |
| Map the cast to a hexagram (and a transformed hexagram, if lines change) | Call any LLM or external API |
| Look up and return canonical text for hexagrams, lines, and trigrams | Guess the "domain" of the question by keyword matching |
| Expose that data as **tools**, **resources**, and **prompts** | Keep state between calls, or persist anything |
| Return a full, auditable record of the cast | Claim any predictive power |

The *host model* does the interpreting. The server's job is to be the book and the
coins: small, inspectable, and honest about what it is. Every tool result should be
something a human could verify by hand against a printed I Ching.

**Ethical stance (to be stated once, well, not repeated everywhere):** this is a
reflection and creativity aid, not divination with predictive power and not advice.
That statement belongs in the server `instructions`, in the README, and as a short
`notice` field in structured results — not as a 100-word banner pasted into every
string.

---

## 2. Project shape

```
bibliomantic-mcp/                     ← repo root (name the folder this)
├── pyproject.toml                    ← uv-managed; hatchling or setuptools; src layout
├── uv.lock
├── README.md
├── LICENSE                           ← MIT, author "Daniel Shields"
├── .gitignore
├── src/bibliomantic_mcp/
│   ├── __init__.py                   ← __version__ only
│   ├── __main__.py                   ← `python -m bibliomantic_mcp`
│   ├── cli.py                        ← argparse: --transport {stdio,streamable-http} --port
│   ├── server.py                     ← builds the MCPServer; registers primitives
│   ├── tools.py                      ← @mcp.tool handlers
│   ├── resources.py                  ← @mcp.resource / templates / completions
│   ├── prompts.py                    ← @mcp.prompt handlers
│   ├── models.py                     ← Pydantic models: Trigram, Line, Hexagram, Cast, …
│   ├── oracle.py                     ← pure functions: cast(), transform(), lookup — NO MCP imports
│   ├── book.py                       ← loads + validates the data file into an immutable Book
│   └── data/
│       ├── trigrams.json
│       └── hexagrams.json            ← all 64, see §4
├── tests/
│   ├── test_oracle.py                ← property + unit tests on pure logic
│   ├── test_book.py                  ← data integrity (64 entries, unique binaries, …)
│   └── test_server.py                ← in-process MCP client round-trips
└── docs/
    ├── ARCHITECTURE.md               ← module map + request flow diagram (Mermaid)
    ├── SDK-NOTES.md                  ← from §0.2
    ├── TALK-NOTES.md                 ← see §8
    └── adr/
        ├── 0001-server-does-not-interpret.md
        ├── 0002-data-as-json-not-code.md
        ├── 0003-structured-output.md
        └── …one per non-obvious decision
```

Rules:
- `oracle.py` and `book.py` must import nothing from `mcp`. They are plain Python and
  testable without a server. This separation is a teaching point: *protocol layer vs
  domain layer*.
- No module-level side effects except decorator registration. The `Book` is loaded once
  in the server **lifespan** and reached through `ctx` (or a lifespan-state accessor the
  SDK provides) — never a module global.
- One server instance, one process, no fallbacks, no "compatibility modes", no backup
  copies of anything. Git is the backup.
- Use `uv` for everything (`uv init`, `uv add`, `uv run`). Pin `mcp` to the installed
  major (`mcp>=2.3,<3`). Dev deps: `pytest`, `pytest-asyncio` (if the SDK's test client
  needs it), `ruff`, `mypy` (strict on `src/`).
- Logging: stdlib `logging`, configured **once** in `cli.py`, to **stderr**, level from
  `--log-level`. stdout is the protocol channel in stdio mode — nothing else may write
  to it.

---

## 3. Domain model (`models.py`) — intended logic

Use frozen Pydantic models (or frozen dataclasses where no validation is needed).

- **`Trigram`** — `name` (English, e.g. "Heaven"), `chinese` (e.g. "乾"), `pinyin`
  (e.g. "qián"), `symbol` (Unicode ☰ etc.), `binary` (3 chars, **bottom line first**,
  `"1"`=yang `"0"`=yin), `attribute` (e.g. "the Creative"), `image` (e.g. "heaven"),
  `family` (e.g. "father"). Exactly eight.

- **`LineText`** — `position` (1–6, bottom to top), `text` (the canonical line
  statement), optional `commentary`.

- **`Hexagram`** — `number` (1–64, King Wen order), `name` (English), `chinese`,
  `pinyin`, `symbol` (the Unicode hexagram character U+4DC0–U+4DFF, e.g. ䷀),
  `binary` (6 chars, **bottom line first**), `upper` and `lower` (trigram names),
  `judgment` (text), `image` (text), `lines` (list of six `LineText`), optional
  `commentary`. Add a derived/validated property or validator that asserts
  `binary == lower.binary + upper.binary`.

- **`LineValue`** — an enum of the four three-coin outcomes: `OLD_YIN = 6`,
  `YOUNG_YANG = 7`, `YOUNG_YIN = 8`, `OLD_YANG = 9`. Helpers: `is_yang`,
  `is_changing`.

- **`CoinToss`** — three booleans (heads?) for one line; `value -> LineValue` using
  heads = 3, tails = 2, summed. (3 heads → 9, 2 heads → 8, 1 head → 7, 0 heads → 6.
  Get this right; it is the most commonly botched detail in amateur implementations.)

- **`Cast`** — the complete auditable record of one consultation:
  `tosses` (six `CoinToss`, bottom to top), `values` (six `LineValue`),
  `primary` (Hexagram), `changing_lines` (positions 1–6 that are 6 or 9),
  `transformed` (Hexagram or `None` when nothing changes), `question`
  (optional str, echoed verbatim, never analysed), `notice` (one-sentence
  reflection/entertainment statement).

- **`Book`** — immutable container: `trigrams: dict[str, Trigram]`,
  `hexagrams: dict[int, Hexagram]`, `by_binary: dict[str, int]`. Built by `book.py`.

---

## 4. Data (`data/*.json`) — content requirements

- **All 64 hexagrams complete.** Each must have real `judgment`, `image`, and six real
  `lines` texts. No placeholders, no "Line 3: traditional interpretation", no templated
  filler. If a field cannot be filled with real text, the build is not done.
- **Licensing:** use a **public-domain** source for the canonical texts — James Legge's
  1882 translation (Sacred Books of the East, vol. XVI) is public domain and is the
  safe default. You may modernise Legge's phrasing lightly, or write original concise
  paraphrases, but do **not** reproduce the Wilhelm/Baynes translation (still under
  copyright) or any other modern translation. Record the source and your approach in
  `data/SOURCES.md` and ADR-0002.
- **Correctness checks that `test_book.py` must enforce:**
  - exactly 64 hexagrams, numbers 1..64 contiguous; exactly 8 trigrams;
  - all 64 `binary` strings unique and each decomposes into two valid trigram binaries;
  - King Wen pairing invariant: for each odd n, hexagram n+1 is either the line-reversal
    (read top-to-bottom) of n, or — when n is symmetric under reversal (there are eight
    such pairs: 1/2, 27/28, 29/30, 61/62) — its line-wise complement;
  - the Unicode `symbol` for hexagram n is `chr(0x4DC0 + n - 1)`;
  - six `lines` per hexagram with positions 1..6.
- Keep JSON hand-readable: one hexagram per top-level object, keys in a fixed order,
  2-space indent, UTF-8, trailing newline.

---

## 5. Oracle logic (`oracle.py`) — intended logic, pure functions

- `toss_coins(rng) -> CoinToss` — three draws from a `secrets`-backed or injected RNG.
  Accept an RNG parameter so tests can inject a seeded `random.Random`; the default
  must be `secrets.SystemRandom()`.
- `cast(book, question=None, rng=None) -> Cast` —
  1. six `toss_coins` calls, **bottom line first**;
  2. map each to `LineValue`;
  3. primary binary = `"".join("1" if v.is_yang else "0")` in bottom-to-top order;
  4. look up `book.by_binary` → primary hexagram (raise `KeyError` → this is a data
     bug, let it surface loudly);
  5. changing positions = those with value 6 or 9;
  6. if any change, flip those bits to get the transformed binary → transformed
     hexagram; else `transformed = None`;
  7. return a `Cast`. No formatting, no prose, no keyword analysis of `question`.
- `hexagram_from_binary(book, binary) -> Hexagram` and
  `hexagram_from_number(book, n) -> Hexagram` — thin, validated lookups.
- Optional, nice for the talk: `nuclear_hexagram(book, hex) -> Hexagram` (lines 2-3-4
  as lower, 3-4-5 as upper). Only if cheap.

Tests (`test_oracle.py`): with a seeded RNG, assert specific casts; with many casts,
assert the line-value distribution is 1:3:3:1 (6:7:8:9) within tolerance; assert that
`transformed` is `None` iff no 6/9 present; assert flipping is per-position correct;
assert every hexagram is reachable from some binary.

---

## 6. MCP surface — intended behaviour

Register everything on one `MCPServer` built in `server.py` by a `create_server()`
factory (so tests can construct it). Server identity: name `bibliomantic`, a `title`,
`version` from `__version__`, and `instructions` that explain in ~5 lines what the
server is for, that results are for reflection only, and that the *host* is expected
to do the interpreting.

### Tools (all with **tool annotations** — `read_only_hint=True`,
`idempotent_hint` as appropriate, `open_world_hint=False` — and **structured output**)

1. **`cast_hexagram(question: str | None = None) -> Cast`**
   Perform one consultation. Returns the full `Cast` (structured) and a concise
   human-readable rendering in `content` (hexagram symbol, number, name, changing
   lines, transformed hexagram, judgment of the primary). *Not idempotent.* The
   `question` is echoed, never interpreted.

2. **`get_hexagram(number: int) -> Hexagram`**
   Look up one hexagram by King Wen number. Validate `1 <= number <= 64` with a Pydantic
   `Field(ge=1, le=64)` so the *schema* enforces it; a value that still gets through
   raises `ToolError("Hexagram number must be 1–64")`. Idempotent.

3. **`get_trigram(name: str) -> Trigram`**
   Look up by English name (case-insensitive) or Chinese character. `ToolError` with the
   list of valid names on miss. Idempotent.

4. **`describe_method() -> MethodDescription`**
   Returns a structured explanation of the three-coin method (coin values, the four
   line values, what "changing" means, how the transformed hexagram is derived) plus
   the server's data source and licence note. Idempotent. This exists so a host can
   explain the mechanics to a user without the server having to pad every result.

### Resources

- **`iching://hexagrams`** — index: a compact listing of all 64 (number, symbol, name,
  chinese) as `text/markdown`. Useful for a host to load once as context.
- **`iching://hexagram/{number}`** — resource template; full hexagram as
  `application/json`. Register a **completion** for `{number}` that offers `1`–`64`
  and, if the SDK supports it, filters by prefix.
- **`iching://trigram/{name}`** — template; full trigram JSON. Completion offers the
  eight names.
- **`iching://method`** — the same content as `describe_method`, as markdown.
- Give each resource a `title`, `description`, and correct `mime_type`. A bad `{number}`
  must produce the SDK's standard resource-not-found error (confirm the idiom:
  `ResourceNotFoundError` or the equivalent), not a 200 with an error string.

### Prompts

Each prompt returns a short, well-formed user message that asks the host to **call
`cast_hexagram`** and then interpret the result *for the stated situation*, explicitly
framing the exercise as reflection. Arguments are described (`description=`) so the
host UI can render a form.

- **`consult(question: str)`** — general.
- **`consult_decision(situation: str, options: str)`** — "I am choosing between…".
- **`study_hexagram(number: int)`** — ask the host to read `iching://hexagram/{number}`
  and teach it (structure, trigrams, judgment, image, lines).

Prompts must not contain the full disclaimer text; a single clause ("for reflection,
not prediction") is enough.

### Transport & CLI

- `bibliomantic-mcp` console script → `cli.main()`.
- Default `--transport stdio`. Also support `--transport streamable-http --port N` by
  passing those options to `run()` (not the constructor). Stateless mode is fine and is
  the 2026-07-28 default; note this in ARCHITECTURE.md as the "why any replica can
  serve any request" talking point.
- `uv run bibliomantic-mcp` must start cleanly with zero warnings (no
  `MCPDeprecationWarning`). Treat a deprecation warning as a test failure:
  run pytest with `-W error::DeprecationWarning` (adjust to the SDK's warning class).

### Errors

- Domain validation → `ToolError` with a message the model can act on.
- Never return `"Error: …"` strings from a tool; never catch-all and swallow.
- Let programming errors propagate (they become `is_error` with a logged traceback).

---

## 7. Milestones (commit after each; docs updated in the same commit)

1. **Scaffold** — uv project, src layout, `pyproject.toml`, `.gitignore`, LICENSE,
   README stub, `docs/SDK-NOTES.md`, empty ADR index. Server starts and lists zero
   tools under `mcp dev`.
2. **Data + models + book** — `trigrams.json`, `hexagrams.json` (all 64, real text),
   `models.py`, `book.py`, `test_book.py` green, `data/SOURCES.md`, ADR-0002.
3. **Oracle** — `oracle.py` + `test_oracle.py` green, ADR-0001.
4. **Tools** — four tools with annotations + structured output; `test_server.py`
   round-trips each through the SDK's in-process client; ADR-0003.
5. **Resources + completions + prompts** — tests for each; README "Capabilities"
   section is generated-or-verified against `tools/list`, `resources/list`,
   `resources/templates/list`, `prompts/list` (write a tiny script or test that fails
   if README and server disagree — this is the "docs and code in lockstep" guard).
6. **CLI + transports** — stdio and streamable-http both verified with the MCP
   Inspector (`npx @modelcontextprotocol/inspector`); README install/config section
   for Claude Desktop and Claude Code (use `uv run --directory <path> bibliomantic-mcp`
   as the command); ARCHITECTURE.md with a Mermaid sequence diagram of one
   `cast_hexagram` call from host to `oracle.cast()` and back.
7. **Quality gate** — `ruff check`, `ruff format --check`, `mypy --strict src`,
   `pytest -W error`, all green; TALK-NOTES.md written; merge `build` → `main`, tag
   `v1.0.0`.

If a milestone forces a design change to an earlier one, update the earlier ADR
(status: Superseded) rather than leaving two conflicting stories.

---

## 8. `docs/TALK-NOTES.md` — what the talk needs from the code

Write this as a set of **pointers into the code**, each one a "stop here and show
this" moment, ordered for a 25–30 minute walkthrough:

1. `server.py` — one `MCPServer`, identity vs transport, `instructions`.
2. `tools.py` — a tool is a typed function; show the generated `input_schema` and
   `output_schema` from `tools/list` in the Inspector; annotations and why hosts care.
3. `oracle.py` — the domain has no idea MCP exists; show the test with a seeded RNG.
4. `book.py` + lifespan — load once, share safely, no globals.
5. `resources.py` — resource vs tool: *data the host pulls* vs *action the host
   invokes*; templates and completions live-demoed in the Inspector.
6. `prompts.py` — prompts as reusable user intents; show one rendering in Claude
   Desktop's prompt picker.
7. Errors — trigger a `ToolError` and show what the model sees vs what the log sees.
8. Transports — same server over stdio and over streamable-http; stateless by default
   under 2026-07-28.
9. The thesis — the server casts and retrieves; the model interprets. Show one full
   consultation in Claude Desktop end to end.

Include the exact Inspector clicks / CLI commands for each stop.

---

## 9. Working agreements for this session

- Code and documentation are a transactional pair: no commit changes behaviour without
  updating the affected doc in the same commit; no doc describes behaviour the code
  doesn't have.
- No `_old`/`_new`/`backup`/`.orig` files, no parallel implementations, no fallback
  import chains. One way to do each thing.
- Before any broad restructuring of work already committed, **stop and ask** whether
  now is a good time to commit first.
- When this brief and the SDK docs disagree, the SDK docs win; record the discrepancy
  in `SDK-NOTES.md` and carry on.
- Save a copy of this brief as `docs/BRIEF.md` in the repo as the originating spec.
