"""The domain layer must not import MCP: protocol layer vs domain layer."""

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).parent.parent / "src" / "bibliomantic_mcp"
DOMAIN = ["oracle.py", "book.py", "models.py", "render.py"]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("module", DOMAIN)
def test_domain_module_does_not_import_mcp(module: str) -> None:
    offenders = {
        name
        for name in imported_modules(PACKAGE / module)
        if name == "mcp" or name.startswith(("mcp.", "mcp_types"))
    }
    assert not offenders, f"{module} imports {offenders}"


@pytest.mark.parametrize("module", DOMAIN)
def test_domain_module_does_not_import_the_protocol_layer(module: str) -> None:
    protocol = {
        f"bibliomantic_mcp.{m}" for m in ("server", "state", "tools", "resources", "prompts", "cli")
    }
    assert not imported_modules(PACKAGE / module) & protocol
