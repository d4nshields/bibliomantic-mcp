# ADR-0002: The book is JSON data, not Python code

**Status:** Accepted

## Context

The server needs the text of all 64 hexagrams and 8 trigrams: about 500 passages. They could
live in Python literals, a database, or data files. The texts also need a source that is safe
to redistribute.

## Decision

- The texts live in `src/bibliomantic_mcp/data/hexagrams.json` and `trigrams.json`: one
  object per entry, fixed key order, 2-space indent, UTF-8, trailing newline. A person can
  read them and check them against a printed I Ching.
- `book.py` loads them **once**, in the server lifespan, validates every entry with the
  Pydantic models in `models.py`, checks the cross-record invariants (64 entries, unique
  binaries, each binary equal to lower trigram + upper trigram, correct Unicode symbols), and
  freezes the result into an immutable `Book`. Bad data stops the server at startup.
- `tests/test_book.py` re-checks those invariants and adds the King Wen pairing rule, the
  Nine/Six line labels, and a guard against placeholder text.
- The source is James Legge's 1882 translation (public domain), lightly modernised. The
  Wilhelm/Baynes translation is still under copyright and is not used. Details are in
  `data/SOURCES.md`.

## Consequences

- Correcting a text is a data edit plus a test run. No code changes.
- The same models validate the data and describe the tools' output, so the shape a client
  sees is exactly the shape that was validated.
- Legge's English is Victorian. The light modernisation keeps it faithful; a host model can
  restate it in plain language when it interprets.
