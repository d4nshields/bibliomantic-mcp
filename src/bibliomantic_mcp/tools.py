"""Tools: the actions a model can invoke.

Each tool is a typed function. The SDK turns its parameters into the
`input_schema` and its return annotation into the `output_schema` that
`tools/list` advertises. The bodies are thin: fetch the book from the lifespan,
call the oracle, translate domain errors into `ToolError`.
"""

import logging
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field

from bibliomantic_mcp import oracle, render
from bibliomantic_mcp.models import HEXAGRAM_COUNT, Cast, Hexagram, MethodDescription, Trigram
from bibliomantic_mcp.state import AppState, book_from

logger = logging.getLogger(__name__)

# Every tool only reads a closed, local book. Per the spec, idempotent_hint and
# destructive_hint only mean something when read_only_hint is False, so they are
# left unset (docs/adr/0003-structured-output.md).
READ_ONLY_CLOSED_WORLD = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def register(server: MCPServer[AppState]) -> None:
    """Attach the four tools to `server`."""

    @server.tool(title="Cast a hexagram", annotations=READ_ONLY_CLOSED_WORLD)
    def cast_hexagram(
        ctx: Context[AppState],
        question: Annotated[
            str | None,
            Field(
                description="The user's question, echoed back verbatim. Optional; "
                "the server never reads or analyses it.",
                max_length=2000,
            ),
        ] = None,
    ) -> Annotated[CallToolResult, Cast]:
        """Consult the I Ching once with the three-coin method.

        Returns the full record of the cast: the six coin tosses, the line values
        (6, 7, 8, 9), the primary hexagram with its complete text, the changing lines,
        and the transformed hexagram if any lines change. Every call casts fresh coins.
        Interpreting the result for the user's situation is up to you.
        """
        result = oracle.cast(book_from(ctx), question)
        logger.info(
            "Cast %d -> %s (changing %s)",
            result.primary.number,
            result.transformed.number if result.transformed else "none",
            list(result.changing_lines) or "none",
        )
        # The model reads a concise summary; the application gets the full record.
        # The Annotated return type keeps `Cast` as the advertised output_schema,
        # and the SDK validates structured_content against it.
        return CallToolResult(
            content=[TextContent(type="text", text=render.cast_summary(result))],
            structured_content=result.model_dump(mode="json"),
        )

    @server.tool(title="Look up a hexagram", annotations=READ_ONLY_CLOSED_WORLD)
    def get_hexagram(
        ctx: Context[AppState],
        number: Annotated[
            int,
            Field(ge=1, le=HEXAGRAM_COUNT, description="King Wen sequence number, 1 to 64."),
        ],
    ) -> Hexagram:
        """Return one hexagram's full text: judgment, image and all six line statements."""
        try:
            return oracle.hexagram_from_number(book_from(ctx), number)
        except oracle.NotInBook as exc:
            raise ToolError(f"Hexagram number must be 1–{HEXAGRAM_COUNT}") from exc

    @server.tool(title="Look up a trigram", annotations=READ_ONLY_CLOSED_WORLD)
    def get_trigram(
        ctx: Context[AppState],
        name: Annotated[
            str,
            Field(
                description="English name in any case (e.g. 'heaven') or the Chinese "
                "character (e.g. '乾')."
            ),
        ],
    ) -> Trigram:
        """Return one of the eight trigrams: its lines, attribute, image and family role."""
        try:
            return oracle.trigram_by_name(book_from(ctx), name)
        except oracle.NotInBook as exc:
            raise ToolError(str(exc)) from exc

    @server.tool(title="Explain the method", annotations=READ_ONLY_CLOSED_WORLD)
    def describe_method(ctx: Context[AppState]) -> MethodDescription:
        """Explain how the three-coin method works and where this server's text comes from.

        Use it when the user asks how a cast works, what changing lines are, or
        how the transformed hexagram is derived.
        """
        return oracle.describe_method(book_from(ctx))
