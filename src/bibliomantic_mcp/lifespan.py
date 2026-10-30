"""Server lifespan: load the book once, share it with every handler.

The lifespan runs once when the server starts (under stdio and under Streamable
HTTP alike) and yields one `AppState`. Handlers reach it through their injected
`Context`, never through a module global.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from bibliomantic_mcp.book import load_book
from bibliomantic_mcp.models import Book

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppState:
    """Everything the server holds for its whole life. Immutable, so sharing it is safe."""

    book: Book


@asynccontextmanager
async def app_lifespan(server: MCPServer[AppState]) -> AsyncIterator[AppState]:
    book = load_book()
    logger.info("Loaded %d hexagrams and %d trigrams", len(book.hexagrams), len(book.trigrams))
    yield AppState(book=book)
    # Nothing to close: the book is plain immutable data.


def book_from(ctx: Context[AppState]) -> Book:
    """The book loaded at startup, as seen from inside a handler."""
    return ctx.request_context.lifespan_context.book
