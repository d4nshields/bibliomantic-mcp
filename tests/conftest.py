"""Shared fixtures: an in-memory MCP client connected to a fresh server."""

from collections.abc import AsyncIterator

import pytest
from mcp import Client

from bibliomantic_mcp.server import create_server


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    # No subprocess, no port: the SDK's Client talks to the server object directly.
    async with Client(create_server(), raise_exceptions=True) as connected:
        yield connected
