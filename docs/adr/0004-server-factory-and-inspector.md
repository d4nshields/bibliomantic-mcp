# ADR-0004: Build the server in a factory; inspect it through the console script

**Status:** Accepted

## Context

The SDK's examples put the server in a module-level global (`mcp = MCPServer(...)`), and the
`mcp dev` / `mcp run` CLI finds a server by importing a file and looking for a global named
`mcp`, `server` or `app`. It cannot call a factory function.

This project's brief rules out module-level side effects other than decorator registration,
and tests need a fresh server each time.

## Decision

- `server.create_server()` builds and returns the `MCPServer`. Nothing is constructed at import.
- Each primitive module (`tools`, `resources`, `prompts`) exposes `register(server)`, which
  applies the decorators to the server it is given.
- For interactive inspection we launch the **console script** under the MCP Inspector, which
  is what `mcp dev` does underneath:

  ```console
  npx @modelcontextprotocol/inspector uv run --directory /path/to/repo bibliomantic-mcp
  ```

## Consequences

- `uv run mcp dev src/bibliomantic_mcp/server.py` does **not** work and is not documented.
- Tests and the CLI use the same `create_server()`, so what we test is what we ship.
- The Inspector command needs Node.js (`npx`), exactly as `mcp dev` would.
