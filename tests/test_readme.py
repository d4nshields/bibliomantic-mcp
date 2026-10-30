"""Docs and code in lockstep: README's Capabilities section must match the live server.

Each table under "## Capabilities" lists names in its first column, in backticks.
They must equal, in order, what the server reports from tools/list,
resources/list, resources/templates/list and prompts/list. Prompt arguments in
the second column are checked too.
"""

import re
from pathlib import Path

import pytest
from mcp import Client

pytestmark = pytest.mark.anyio

README = Path(__file__).parent.parent / "README.md"


def capability_tables() -> dict[str, list[list[str]]]:
    """Map each '### Heading' under '## Capabilities' to its table rows (as cells)."""
    text = README.read_text(encoding="utf-8")
    section = text.split("\n## Capabilities\n", 1)[1].split("\n## ", 1)[0]
    tables: dict[str, list[list[str]]] = {}
    heading = ""
    for line in section.splitlines():
        if line.startswith("### "):
            heading = line[4:].strip()
            tables[heading] = []
        elif line.startswith("| `") and heading:
            tables[heading].append([cell.strip() for cell in line.strip("|").split("|")])
    return tables


def first_code(cell: str) -> str:
    match = re.match(r"`([^`]+)`", cell)
    assert match, cell
    return match.group(1)


def all_codes(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


async def test_readme_tools_match(client: Client) -> None:
    listed = [t.name for t in (await client.list_tools()).tools]
    assert [first_code(row[0]) for row in capability_tables()["Tools"]] == listed


async def test_readme_resources_match(client: Client) -> None:
    listed = [(r.uri, r.mime_type) for r in (await client.list_resources()).resources]
    rows = capability_tables()["Resources"]
    assert [(first_code(row[0]), first_code(row[1])) for row in rows] == listed


async def test_readme_resource_templates_match(client: Client) -> None:
    templates = (await client.list_resource_templates()).resource_templates
    listed = [(t.uri_template, t.mime_type) for t in templates]
    rows = capability_tables()["Resource templates"]
    assert [(first_code(row[0]), first_code(row[1])) for row in rows] == listed


async def test_readme_prompts_match(client: Client) -> None:
    listed = [
        (p.name, [a.name for a in p.arguments or []]) for p in (await client.list_prompts()).prompts
    ]
    rows = capability_tables()["Prompts"]
    assert [(first_code(row[0]), all_codes(row[1])) for row in rows] == listed
