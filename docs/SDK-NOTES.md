# SDK notes: the MCP Python SDK v2 surface this project uses

A one-page record of what was checked against the official docs
(<https://py.sdk.modelcontextprotocol.io/>) and the installed source before writing code.
It works as a teaching aid and as a guard against drift: if the SDK changes, this page says
what we relied on.

## Versions: two separate axes

| Axis | Value | Notes |
|---|---|---|
| Protocol revision (on the wire) | **2026-07-28** | Newest revision in `mcp_types.version.KNOWN_PROTOCOL_VERSIONS` for the installed SDK. |
| SDK pin (`pyproject.toml`) | `mcp>=2.3,<3` | Semver library line. 2.0.0 shipped with the 2026-07-28 protocol; 2.1–2.3 speak the same protocol. |
| SDK version resolved by `uv` | **mcp 2.3.0** (with `mcp-types 2.3.0`) | Check with `uv run mcp version`. |
| Python | 3.12 (`requires-python >=3.12`) | The SDK itself needs 3.11+. |

## The API surface we use

| What | v2 spelling | Where we use it |
|---|---|---|
| Server class | `from mcp.server import MCPServer` (`FastMCP` / `mcp.server.fastmcp` do not exist) | `server.py` |
| Identity | `MCPServer(name, title=, instructions=, version=, lifespan=)` | `server.py` |
| Transport options | `server.run("streamable-http", host=, port=, stateless_http=)`; passing `port=` to the constructor raises `TypeError` | `cli.py` |
| Tools | `@mcp.tool(title=, annotations=ToolAnnotations(...))`; input schema from type hints and `Annotated[..., Field(...)]` | `tools.py` |
| Structured output | Return type annotation **is** the `output_schema`; a returned model fills both `content` (JSON text) and `structured_content` | `tools.py` |
| Custom text plus a schema | Return `Annotated[CallToolResult, Model]`: you write `content`, the SDK still advertises `Model` as `output_schema` and validates `structured_content` against it | `tools.py` (`cast_hexagram`) |
| Resources | `@mcp.resource(uri, title=, description=, mime_type=)`; `{param}` makes a template, listed under `resources/templates/list`; template values are converted to the parameter's type | `resources.py` |
| Completions | One `@mcp.completion()` per server: `async def (ref, argument, context) -> Completion \| None`. The SDK does **not** filter by prefix; we do | `resources.py` |
| Prompts | `@mcp.prompt(title=)`; argument descriptions from `Annotated[str, Field(description=)]`; a returned `str` becomes one user message | `prompts.py` |
| Context | Declare `ctx: Context[AppState]` (from `mcp.server.mcpserver`); `get_context()` is gone | every handler |
| Lifespan | `@asynccontextmanager` receiving the server, yielding one object; reached as `ctx.request_context.lifespan_context`. Runs once per server, also under Streamable HTTP | `lifespan.py` |
| Errors | `ToolError` (model sees it), `MCPError` (protocol error, model never sees it), anything else (opaque `is_error` result, traceback logged) | `tools.py` |
| Missing resource | `ResourceNotFoundError` → JSON-RPC `-32602` with the URI in `error.data` | `resources.py` |
| Imports | `from mcp.server.mcpserver.exceptions import ToolError, ResourceNotFoundError`; `from mcp.types import ToolAnnotations, CallToolResult, TextContent, Completion, ...` | |
| Testing | `async with Client(server, raise_exceptions=True) as client:` in memory, with anyio's pytest plugin (`@pytest.mark.anyio`) | `tests/test_server.py` |

## Deliberately not used

- **Roots, Sampling, MCP-level logging (`ctx.info()` …)**: deprecated by SEP-2577; they emit
  `MCPDeprecationWarning`. We log with stdlib `logging` to stderr.
- **Elicitation / multi-round-trip requests**: nothing here needs to ask the user anything.
- **Tasks**: the experimental API was removed in v2, and the 2026 tasks extension is not in the SDK.
- **SSE transport**: superseded by Streamable HTTP.

## Where the brief and the SDK docs disagree (the docs win)

1. **Python floor.** The brief says the SDK needs Python 3.10+. The installation page says
   3.11+. We target 3.12 either way.
2. **The warning class.** `MCPDeprecationWarning` subclasses `UserWarning`, *not*
   `DeprecationWarning`, so `-W error::DeprecationWarning` would let it through. `pyproject.toml`
   sets pytest `filterwarnings = ["error"]`, which fails on every warning.
3. **`pytest-asyncio`.** Not needed. The SDK's docs and test client use anyio's own pytest
   plugin, which ships with `anyio`.
4. **`idempotent_hint` on read-only tools.** The brief asks for `idempotent_hint` "as
   appropriate". The spec and the SDK's Tools page say `idempotent_hint` and `destructive_hint`
   mean something only when `read_only_hint` is false. Every tool here is read-only, so we set
   `read_only_hint=True` and `open_world_hint=False` and leave `idempotent_hint` unset.
   See ADR-0003.
5. **`mcp dev` needs a module-level server.** `mcp dev` / `mcp run` import a file and look for
   a module-level `mcp`, `server` or `app` object; they cannot call a factory. This project
   builds its server in `create_server()` (no globals), so we run the Inspector against the
   console script instead: `npx @modelcontextprotocol/inspector uv run --directory <repo> bibliomantic-mcp`.
   That is what `mcp dev` does underneath, minus the import. See ADR-0004.
6. **Completion handlers get no `Context`.** The `@mcp.completion()` handler is called as
   `(ref, argument, context)` with no lifespan access. Completion values therefore come from
   domain constants (`HEXAGRAM_COUNT`, `TRIGRAM_NAMES` in `models.py`), which the book loader
   validates the data against. See ADR-0005.
7. **`ToolError` text gets a prefix.** The model sees
   `Error executing tool <name>: <your message>`, not just your message.
8. **`MCPServer(...)` configures logging.** The constructor calls `logging.basicConfig()` at
   `log_level`. `basicConfig` does nothing once a handler exists, so `cli.py` configures logging
   first and its configuration wins.
