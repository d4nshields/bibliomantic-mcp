# ADR-0005: Reaching the book where the SDK injects no Context

**Status:** Accepted

## Context

The book is loaded once, in the server lifespan, and handlers reach it through an injected
`ctx: Context[AppState]` (`state.book_from(ctx)`). There are no module globals.

Two places in the SDK give a handler **no** `Context`:

1. **Static resources.** A resource whose URI has no `{template}` variables may not declare a
   `Context` parameter. `@server.resource("iching://hexagrams")` on a function taking `ctx`
   raises `ValueError: ... Context injection for static resources is not supported`.
2. **The completion handler.** `@server.completion()` is called as `(ref, argument, context)`,
   where `context` is the already-filled arguments, not a `Context`.

## Decision

1. **Static resources are published by the lifespan.** After loading the book,
   `server.app_lifespan` calls `resources.publish_static(server, book)`, which registers
   `iching://hexagrams` and `iching://method` as `TextResource`s with their Markdown rendered
   from that book. The book is still loaded exactly once, and both resources are in place
   before the first request.
2. **Completion values come from domain constants.** `HEXAGRAM_COUNT` and `TRIGRAM_NAMES` in
   `models.py` are facts about the I Ching, not data: there are 64 hexagrams and these eight
   trigrams. `TRIGRAM_NAMES` is also the `Literal` type of `Trigram.name`, and `book.py`
   refuses to load data that disagrees with either constant, so completions cannot drift
   from the book.

Rejected alternatives:

- Loading the book in `create_server()` and closing over it. That would be a second way to
  reach the book alongside `ctx`.
- Giving the index and method a dummy template variable so they can take `ctx`. That would
  make the URIs worse to work around an SDK rule.

## Consequences

- `resources/list` is populated by the lifespan, so a server that has been built but not
  started lists the templates but not the two fixed resources. Every real client (the
  in-memory test `Client`, stdio, HTTP) starts the lifespan before its first request.
- The lifespan should run once per server object. That is the SDK's model (once at startup,
  shared across sessions), and each test builds a fresh server.
