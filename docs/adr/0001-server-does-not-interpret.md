# ADR-0001: The server casts and retrieves; the host interprets

**Status:** Accepted

## Context

An I Ching consultation has two halves. One is mechanical: toss coins, build a figure, look
up the text. The other is interpretive: what does this text mean for *this* person's
situation? A server could try to do both, by calling an LLM, keyword-matching the question
to a "domain", or templating advice.

The host it runs inside (Claude Desktop, Claude Code, any MCP client) already has a capable
model in the loop, with the user's full context.

## Decision

The server does only the mechanical half.

- `oracle.cast()` tosses coins with a CSPRNG (`secrets.SystemRandom`, injectable for tests),
  maps the lines to a primary hexagram and, when lines change, to a transformed one. It
  returns a complete `Cast` record: tosses, values, hexagrams, changing lines.
- The `question` is echoed verbatim and never analysed.
- No LLM calls, no network, no state between calls, no persistence.
- Results carry one short `notice`: for reflection and creativity, not prediction or advice.
  The fuller statement is in the server `instructions` and the README, not in every string.
- `oracle.py` and `book.py` import nothing from `mcp`. The domain layer can be read and
  tested without knowing MCP exists.

## Consequences

- Every result is something a person can verify by hand against a printed I Ching. The
  `Cast` model re-checks its own chain (coins → values → hexagram → transformation) when built.
- Interpretation quality is the host model's, and gets better as models do, with no change here.
- The server is small, offline and deterministic except for the coins. With a seeded RNG it is
  fully deterministic, which is how `tests/test_oracle.py` pins casts.
- Prompts (`prompts.py`) ask the host to interpret; they never contain an interpretation.
