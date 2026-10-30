"""The state the server holds for its whole life, and how a handler reaches it.

`server.app_lifespan` builds one `AppState` at startup. Handlers declare a
`ctx: Context[AppState]` parameter and call `book_from(ctx)`: no module globals.
"""

from dataclasses import dataclass

from mcp.server.mcpserver import Context

from bibliomantic_mcp.models import Book


@dataclass(frozen=True, slots=True)
class AppState:
    """Everything the server holds for its whole life. Immutable, so sharing it is safe."""

    book: Book


def book_from(ctx: Context[AppState]) -> Book:
    """The book loaded at startup, as seen from inside a handler."""
    return ctx.request_context.lifespan_context.book
