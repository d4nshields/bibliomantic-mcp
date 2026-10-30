"""Human-readable renderings of domain objects. Plain text and Markdown, no MCP.

Structured data goes to the client application as `structured_content`; these
strings are what a model or a person reads.
"""

from bibliomantic_mcp.models import Book, Cast, MethodDescription


def cast_summary(cast: Cast) -> str:
    """A concise reading of a cast: what came up, what changes, the primary judgment."""
    p = cast.primary
    lines = [f"{p.symbol} Hexagram {p.number}: {p.name} ({p.chinese}, {p.pinyin})"]
    if cast.question is not None:
        lines.insert(0, f"Question: {cast.question}")
    lines.append(f"Lines, bottom to top: {' '.join(str(int(v)) for v in cast.values)}")
    lines.append(f"Judgment: {p.judgment}")
    if cast.transformed is None:
        lines.append("No changing lines.")
    else:
        positions = ", ".join(str(n) for n in cast.changing_lines)
        lines.append(f"Changing lines: {positions}")
        for n in cast.changing_lines:
            lines.append(f"  {p.lines[n - 1].text}")
        # Hexagrams 1 and 2 have an extra text for when every line changes.
        if len(cast.changing_lines) == 6 and p.commentary:
            lines.append(f"  {p.commentary}")
        t = cast.transformed
        lines.append(f"Becomes {t.symbol} Hexagram {t.number}: {t.name} ({t.chinese}, {t.pinyin})")
    lines.append(cast.notice)
    return "\n".join(lines)


def hexagram_index(book: Book) -> str:
    rows = [
        "# The 64 hexagrams (King Wen order)",
        "",
        "| # | Symbol | Name | Chinese |",
        "|---|---|---|---|",
    ]
    rows += [
        f"| {h.number} | {h.symbol} | {h.name} | {h.chinese} |" for h in book.hexagrams.values()
    ]
    rows += ["", "Read one in full at `iching://hexagram/{number}`."]
    return "\n".join(rows) + "\n"


def method_markdown(method: MethodDescription) -> str:
    rows = [
        "# The three-coin method",
        "",
        method.coins,
        "",
        "| Sum | Line | Heads | Chance | Yang? | Changing? |",
        "|---|---|---|---|---|---|",
    ]
    rows += [
        f"| {int(i.value)} | {i.name} | {i.heads} | {i.probability} | "
        f"{'yes' if i.is_yang else 'no'} | {'yes' if i.is_changing else 'no'} |"
        for i in method.line_values
    ]
    rows += [
        "",
        "## Building the hexagram",
        "",
        method.building_the_hexagram,
        "",
        "## Changing lines",
        "",
        method.changing_lines,
        "",
        "## The transformed hexagram",
        "",
        method.transformed_hexagram,
        "",
        "## Source",
        "",
        method.source,
        "",
        method.licence,
        "",
        f"*{method.notice}*",
    ]
    return "\n".join(rows) + "\n"
