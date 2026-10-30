"""The process boundary: argument parsing, and the real server over stdio."""

import sys

import pytest
from mcp import Client, StdioServerParameters

from bibliomantic_mcp.cli import parse_args


def test_defaults_to_stdio() -> None:
    args = parse_args([])
    assert (args.transport, args.host, args.port, args.log_level) == (
        "stdio",
        "127.0.0.1",
        8000,
        "INFO",
    )


def test_streamable_http_options() -> None:
    args = parse_args(["--transport", "streamable-http", "--port", "9000", "--log-level", "DEBUG"])
    assert (args.transport, args.port, args.log_level) == ("streamable-http", 9000, "DEBUG")


def test_rejects_unknown_transport() -> None:
    with pytest.raises(SystemExit):
        parse_args(["--transport", "sse"])


@pytest.mark.anyio
async def test_real_process_over_stdio() -> None:
    """Launch `python -m bibliomantic_mcp` as a host would, with warnings as errors."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-W", "error", "-m", "bibliomantic_mcp", "--log-level", "WARNING"],
    )
    async with Client(params) as client:
        tools = [t.name for t in (await client.list_tools()).tools]
        assert "cast_hexagram" in tools
        result = await client.call_tool("cast_hexagram", {"question": "over stdio"})
        assert not result.is_error
        assert result.structured_content is not None
        assert result.structured_content["question"] == "over stdio"
