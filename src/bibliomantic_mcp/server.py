"""Build the one MCPServer this project exposes.

The constructor takes *identity* only: who the server is and what it is for.
How it is served (stdio, HTTP, which port) is decided later, in `cli.py`,
by the arguments passed to `run()`.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server import MCPServer

from bibliomantic_mcp import __version__, prompts, resources, tools
from bibliomantic_mcp.book import load_book
from bibliomantic_mcp.state import AppState

logger = logging.getLogger(__name__)

INSTRUCTIONS = """\
This server is an I Ching: it casts a hexagram with the traditional three-coin method \
and returns the canonical text (James Legge's public-domain translation).
Call `cast_hexagram` to consult; use `get_hexagram`, `get_trigram` and the `iching://` \
resources to look things up.
The server only casts coins and retrieves text. Interpreting the result for the user's \
situation is your job, as the host.
Treat every result as a prompt for reflection and creativity, not as a prediction or as advice.\
"""


@asynccontextmanager
async def app_lifespan(server: MCPServer[AppState]) -> AsyncIterator[AppState]:
    """Runs once, before the first request: load and validate the book, share it.

    Handlers reach the result through `ctx` (see `state.book_from`). The two fixed
    resources, which the SDK gives no `ctx`, are rendered from the same book here.
    """
    book = load_book()
    logger.info("Loaded %d hexagrams and %d trigrams", len(book.hexagrams), len(book.trigrams))
    resources.publish_static(server, book)
    yield AppState(book=book)
    # Nothing to close: the book is plain immutable data.


def create_server() -> MCPServer[AppState]:
    """Construct the server. A factory, not a module global, so tests get a fresh one."""
    server = MCPServer(
        "bibliomantic",
        title="Bibliomantic I Ching",
        instructions=INSTRUCTIONS,
        version=__version__,
        lifespan=app_lifespan,
    )
    tools.register(server)
    resources.register(server)
    prompts.register(server)
    return server
