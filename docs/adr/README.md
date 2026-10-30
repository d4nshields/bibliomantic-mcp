# Architecture decision records

One file per decision that a reader could reasonably ask "why?" about. Format: context,
decision, consequences. If a later decision replaces one, the old record is marked
**Superseded** and links to its replacement, so there is never more than one live story.

| # | Decision | Status |
|---|---|---|
| [0001](0001-server-does-not-interpret.md) | The server casts and retrieves; the host interprets | Accepted |
| [0002](0002-data-as-json-not-code.md) | The book is JSON data, not Python code | Accepted |
| [0003](0003-structured-output.md) | Every tool returns structured output, and is annotated read-only | Accepted |
| [0004](0004-server-factory-and-inspector.md) | Build the server in a factory; inspect it through the console script | Accepted |
