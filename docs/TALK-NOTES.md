# Talk notes: MCP server internals, by way of the I Ching

A 25–30 minute walkthrough in nine stops. Each stop names the file and
symbol to open, what to say, and the exact command or Inspector clicks to show it. Symbols are
given instead of line numbers so these notes survive edits: in any editor, jump to the symbol.

## Before the talk

```console
cd bibliomantic-mcp
uv sync
uv run pytest -q                       # ~1,000 tests; confirms the demo machine is sane
```

Open three terminals:

| Terminal | Command | Purpose |
|---|---|---|
| A | `npx @modelcontextprotocol/inspector uv run --directory "$PWD" bibliomantic-mcp` | Inspector over **stdio**; opens a browser tab |
| B | `uv run bibliomantic-mcp --transport streamable-http --port 8000 --log-level DEBUG` | the same server over **HTTP**, with its log visible |
| C | editor / shell | code, and Inspector CLI one-liners |

Claude Desktop configured as in the README ("Claude Desktop"), fully restarted.

Inspector basics: the left panel has **Transport Type**, **Command**/**URL**, and **Connect**.
Across the top are the **Resources**, **Prompts** and **Tools** tabs. Each tab has a **List …**
button; select an item to get its form on the right.

---

## 1. `server.py`: one server, identity vs transport (3 min)

Open `src/bibliomantic_mcp/server.py`, function `create_server`.

- One `MCPServer`. The constructor takes **identity**: `name`, `title`, `version`,
  `instructions`, `lifespan`. Nothing about ports.
- Transport is decided later, in `cli.py` → `main()`: `server.run("stdio")` or
  `server.run("streamable-http", host=..., port=..., stateless_http=True)`.
  Say: "Passing `port=` to the constructor is a `TypeError` in SDK v2."
- Read `INSTRUCTIONS` aloud: this is where the server tells *every* host what it is for,
  and the one place the full "reflection, not prediction" statement lives.
- A factory, not a global: tests build a fresh server each time (`tests/conftest.py`).

**Show:** Inspector (terminal A) → **Connect**: the server appears as `bibliomantic` with
its version. The `instructions` travel to the host in the same discovery data. Read them
from the code rather than hunting for them in the UI.

## 2. `tools.py`: a tool is a typed function (4 min)

Open `src/bibliomantic_mcp/tools.py`, `get_hexagram`, then `cast_hexagram`.

- The docstring is the description. The parameters are the `input_schema`:
  `Annotated[int, Field(ge=1, le=64)]` becomes `"minimum": 1, "maximum": 64`.
- The return annotation is the `output_schema`. `-> Hexagram` is a Pydantic model, so the
  result carries both `content` (text for the model) and `structured_content` (data for
  the app).
- `cast_hexagram` returns `Annotated[CallToolResult, Cast]`: it writes its own short text
  for the model, and the SDK still advertises and validates the `Cast` schema.
- `ctx: Context[AppState]` never appears in the schema. The model cannot see or fill it.
- `READ_ONLY_CLOSED_WORLD` annotations: `read_only_hint=True`, `open_world_hint=False`.
  Hosts use these to decide whether to ask before running a tool. `idempotent_hint` is
  deliberately unset: the spec defines it only for tools that write (ADR-0003).

**Show:** Inspector → **Tools** → **List Tools** → select `get_hexagram`. Point at the
number field and its 1–64 bounds. Select `cast_hexagram` → type a question → **Run Tool**.
Show the text block, then expand the structured result. Same thing from the CLI:

```console
npx @modelcontextprotocol/inspector --cli uv run --directory "$PWD" bibliomantic-mcp --method tools/list
```

## 3. `oracle.py`: the domain has no idea MCP exists (4 min)

Open `src/bibliomantic_mcp/oracle.py`, function `cast`, then `models.py` → `CoinToss.value`.

- Read the numbered steps in `cast`: six tosses bottom-up, heads=3/tails=2, so
  6/7/8/9; odd is yang; 6 and 9 change; flip them for the transformed hexagram.
- "The most commonly botched detail": 3 heads is 9 (old yang), 0 heads is 6 (old yin).
- No imports from `mcp`. `tests/test_layers.py` fails the build if that changes.
- `rng` is injectable. The default is `secrets.SystemRandom()`, the OS CSPRNG.
- `Cast._record_is_consistent`: the record re-checks its own chain of evidence.

**Show:** `tests/test_oracle.py` → `test_specific_seeded_cast`. Seed 41 gives
6 8 8 8 7 9 → 000011 = Earth below Wind = **20 Contemplation**; flip lines 1 and 6 →
100010 = Thunder below Water = **3 Difficulty at the Beginning**. Check it against the
`iching://hexagrams` table. Then run it:

```console
uv run pytest -q tests/test_oracle.py -k seeded
```

## 4. `book.py` + lifespan: load once, share safely, no globals (3 min)

Open `src/bibliomantic_mcp/server.py` → `app_lifespan`, then `state.py` → `book_from`,
then `book.py` → `build_book`.

- The lifespan runs **once**, before the first request, under stdio and HTTP alike. It
  yields one immutable `AppState`; every handler reaches it as
  `ctx.request_context.lifespan_context` (wrapped by `book_from(ctx)`).
- `build_book` checks what no single record can: 64 entries, unique binaries, each binary =
  lower trigram + upper trigram, correct Unicode symbols. Bad data stops startup.
- The text is JSON data with a public-domain source (`data/SOURCES.md`, ADR-0002).
- An SDK edge worth admitting: static resources and the completion handler get **no**
  `Context`. So the lifespan publishes the two static resources itself (ADR-0005).

**Show:** terminal B's first log lines: `Loaded 64 hexagrams and 8 trigrams`, logged once,
however many requests follow.

## 5. `resources.py`: data the host pulls vs actions the model invokes (4 min)

Open `src/bibliomantic_mcp/resources.py` → `register` and `complete`.

- A tool runs because the **model** decided; a resource is loaded because the **application**
  decided. Same book, different control.
- `iching://hexagram/{number}` is a **template**: listed under `resources/templates/list`,
  one function serves all 64 URIs.
- `complete`: one completion handler per server. The SDK does not filter, so
  `_starting_with` does. Registering it is what declares the `completions` capability.
- A bad number raises `ResourceNotFoundError` → JSON-RPC `-32602` with the URI in `data`.

**Show:** Inspector → **Resources** → **List Resources** → click `iching://hexagrams`
(Markdown table). **List Templates** → `iching://hexagram/{number}` → type `6` in the
`number` field and watch the suggestions narrow to 6, 60–64 → pick `64` → **Read Resource**.
Then try `iching://trigram/{name}` with `w` (Wind, Water).

## 6. `prompts.py`: prompts as reusable user intents (3 min)

Open `src/bibliomantic_mcp/prompts.py` → `consult_decision`.

- Prompts are **user**-controlled: picked from a menu, arguments typed by a person.
  Arguments are plain strings with descriptions; there is no JSON Schema.
- The prompt asks the host to call `cast_hexagram` and *then* interpret. It carries one
  framing clause ("for reflection, not prediction"), not a disclaimer banner.

**Show:** Inspector → **Prompts** → **List Prompts** → `consult_decision` → fill
`situation` and `options` → **Get Prompt**: one user message. Then, in **Claude Desktop**:
open the composer's **+** menu, choose the **bibliomantic** server's
**Consult on a decision** prompt, fill the form, and send. (Rehearse this click path on the
demo build of Claude Desktop; the menu wording changes between releases.)

## 7. Errors: what the model sees vs what the log sees (3 min)

Open `tools.py` → `get_trigram` (the `except oracle.NotInBook` → `ToolError`), then the
error table in `docs/ARCHITECTURE.md`.

| Raise | Caller gets | Log gets |
|---|---|---|
| `ToolError` | `is_error=True`, your message: the model can retry | one INFO line |
| `MCPError` | a JSON-RPC error; the model sees nothing | (used by `study_hexagram` for bad input) |
| anything else | `is_error=True`, just "Error executing tool …" | ERROR + traceback |

**Show (model's view):** Inspector → **Tools** → `get_trigram` → `name` = `Sky` →
**Run Tool**:
`Error executing tool get_trigram: No trigram named 'Sky'. Valid names: Heaven, Lake, …`.
The model can read that and correct itself.

**Show (log's view):** connect the Inspector to terminal B (Transport **Streamable HTTP**,
URL `http://127.0.0.1:8000/mcp`) and repeat. Terminal B prints
`Tool 'get_trigram' failed: …` at INFO, with no traceback because it was expected.

**Show (the schema as an error):** `get_hexagram` with `number` = `65`. Rejected *before the
function runs*: "Input should be less than or equal to 64".

## 8. Transports: same server, stdio and streamable HTTP (2 min)

- Terminal A is stdio (the Inspector launched the process). Terminal B is HTTP. Same
  `create_server()`, same tools.
- Protocol 2026-07-28 is stateless: no `initialize` handshake, no `Mcp-Session-Id`; each
  request carries its version and capabilities in `_meta`. The server keeps no per-client
  state, so **any replica can serve any request**. `stateless_http=True` gives legacy
  clients the same behaviour.

**Show:** the HTTP server answering without a session:

```console
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:8000/mcp --transport http --method tools/list
```

Optional, for the protocol-curious, a raw 2026-07-28 call with no handshake:

```console
curl -s http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' -H 'Mcp-Method: tools/call' -H 'Mcp-Name: get_trigram' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_trigram","arguments":{"name":"Lake"},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}' -i
```

The response is `200` with no `Mcp-Session-Id` header.

## 9. The thesis: the server casts and retrieves; the model interprets (3 min)

Open `docs/adr/0001-server-does-not-interpret.md` and the README's Capabilities table.

- The server is the book and the coins: small, inspectable, honest about what it is.
  Every result can be checked by hand against a printed I Ching.
- The interpretation comes from the host model, which has the user's context, and it
  improves as models do, with no change to the server.

**Show:** Claude Desktop, end to end. Ask: *"I'm deciding whether to give this talk again
next year. Can you consult the I Ching for me?"* Claude calls `cast_hexagram` (the tool call
is visible, with the read-only annotation), gets the record, and interprets it for the
situation. Expand the tool result to show the coins and line values: the audit trail
behind the interpretation.

Close on: *"Philip K. Dick's characters did the casting and the thinking. Here the server
does the casting, and the thinking happens where the context is."*
