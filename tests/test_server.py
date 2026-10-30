"""Round-trips through a real MCP client, in memory.

These tests see exactly what a host sees: schemas from `tools/list`, results
from `tools/call`, and errors as the protocol delivers them.
"""

import pytest
from mcp import Client
from mcp.types import TextContent

from bibliomantic_mcp import __version__
from bibliomantic_mcp.models import Cast, Hexagram, MethodDescription, Trigram

pytestmark = pytest.mark.anyio

TOOLS = ["cast_hexagram", "get_hexagram", "get_trigram", "describe_method"]


def text_of(result: object) -> str:
    content = result.content  # type: ignore[attr-defined]
    assert isinstance(content[0], TextContent)
    text: str = content[0].text
    return text


# --- Identity --------------------------------------------------------------


async def test_server_identity(client: Client) -> None:
    info = client.server_info
    assert info is not None
    assert info.name == "bibliomantic"
    assert info.version == __version__
    assert info.title


async def test_speaks_protocol_2026_07_28(client: Client) -> None:
    assert client.protocol_version == "2026-07-28"


# --- tools/list ------------------------------------------------------------


async def test_lists_the_four_tools(client: Client) -> None:
    listed = await client.list_tools()
    assert [t.name for t in listed.tools] == TOOLS


async def test_every_tool_is_annotated_read_only_and_closed_world(client: Client) -> None:
    for tool in (await client.list_tools()).tools:
        assert tool.title
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.open_world_hint is False
        # Only meaningful for tools that write, so deliberately unset (ADR-0003).
        assert tool.annotations.idempotent_hint is None


async def test_every_tool_advertises_an_output_schema(client: Client) -> None:
    for tool in (await client.list_tools()).tools:
        assert tool.output_schema is not None, tool.name


async def test_get_hexagram_schema_enforces_the_range(client: Client) -> None:
    tool = {t.name: t for t in (await client.list_tools()).tools}["get_hexagram"]
    number = tool.input_schema["properties"]["number"]
    assert (number["minimum"], number["maximum"]) == (1, 64)
    assert tool.input_schema["required"] == ["number"]


async def test_context_is_invisible_to_the_model(client: Client) -> None:
    for tool in (await client.list_tools()).tools:
        assert "ctx" not in tool.input_schema.get("properties", {})


# --- cast_hexagram ---------------------------------------------------------


async def test_cast_returns_a_valid_structured_record(client: Client) -> None:
    result = await client.call_tool("cast_hexagram", {"question": "What now?"})
    assert not result.is_error
    cast = Cast.model_validate(result.structured_content)  # re-runs the audit checks
    assert cast.question == "What now?"
    assert cast.notice


async def test_cast_content_is_a_concise_reading(client: Client) -> None:
    result = await client.call_tool("cast_hexagram", {"question": "What now?"})
    cast = Cast.model_validate(result.structured_content)
    text = text_of(result)
    assert text.startswith("Question: What now?")
    assert f"Hexagram {cast.primary.number}: {cast.primary.name}" in text
    assert cast.primary.symbol in text
    assert cast.primary.judgment in text
    if cast.transformed:
        assert f"Becomes {cast.transformed.symbol} Hexagram {cast.transformed.number}" in text
    else:
        assert "No changing lines." in text
    # Concise: not a JSON dump of the whole record.
    assert '"tosses"' not in text


async def test_cast_without_a_question(client: Client) -> None:
    result = await client.call_tool("cast_hexagram", {})
    assert Cast.model_validate(result.structured_content).question is None
    assert not text_of(result).startswith("Question:")


# --- get_hexagram ----------------------------------------------------------


async def test_get_hexagram(client: Client) -> None:
    result = await client.call_tool("get_hexagram", {"number": 1})
    hexagram = Hexagram.model_validate(result.structured_content)
    assert (hexagram.number, hexagram.binary, hexagram.symbol) == (1, "111111", "䷀")


@pytest.mark.parametrize("number", [0, 65])
async def test_get_hexagram_out_of_range_is_a_tool_error(client: Client, number: int) -> None:
    """The schema rejects it before the function runs; the model reads why and can retry."""
    result = await client.call_tool("get_hexagram", {"number": number})
    assert result.is_error
    assert result.structured_content is None
    assert "number" in text_of(result)


# --- get_trigram -----------------------------------------------------------


@pytest.mark.parametrize("name", ["Water", "water", "坎"])
async def test_get_trigram(client: Client, name: str) -> None:
    result = await client.call_tool("get_trigram", {"name": name})
    assert Trigram.model_validate(result.structured_content).binary == "010"


async def test_unknown_trigram_tells_the_model_the_valid_names(client: Client) -> None:
    result = await client.call_tool("get_trigram", {"name": "Sky"})
    assert result.is_error
    message = text_of(result)
    assert "No trigram named 'Sky'" in message
    assert "Heaven, Lake, Fire, Thunder, Wind, Water, Mountain, Earth" in message


# --- describe_method -------------------------------------------------------


async def test_describe_method(client: Client) -> None:
    result = await client.call_tool("describe_method", {})
    method = MethodDescription.model_validate(result.structured_content)
    assert [int(i.value) for i in method.line_values] == [6, 7, 8, 9]
    assert "Legge" in method.source
