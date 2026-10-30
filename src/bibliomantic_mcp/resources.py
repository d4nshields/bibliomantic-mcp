"""Resources: data the host application pulls, addressed by `iching://` URIs.

A tool is an action the *model* decides to invoke. A resource is data the
*application* decides to load into context. Same book, different control.

Two kinds of registration happen here:
- `register()` runs when the server is built: the resource templates and the
  server's single completion handler (the SDK allows one per server, so it
  also covers the `number` argument of the `study_hexagram` prompt).
- `publish_static()` runs from the lifespan, once the book is loaded: the two
  fixed resources. The SDK does not inject a Context into a resource whose URI
  has no template variables, so their text is rendered from the loaded book
  at startup instead (ADR-0005).
"""

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ResourceNotFoundError
from mcp.server.mcpserver.resources import TextResource
from mcp.types import (
    Completion,
    CompletionArgument,
    CompletionContext,
    PromptReference,
    ResourceTemplateReference,
)

from bibliomantic_mcp import oracle, render
from bibliomantic_mcp.models import HEXAGRAM_COUNT, TRIGRAM_NAMES, Book, Hexagram, Trigram
from bibliomantic_mcp.state import AppState, book_from

INDEX_URI = "iching://hexagrams"
HEXAGRAM_TEMPLATE = "iching://hexagram/{number}"
TRIGRAM_TEMPLATE = "iching://trigram/{name}"
METHOD_URI = "iching://method"

HEXAGRAM_NUMBERS = tuple(str(n) for n in range(1, HEXAGRAM_COUNT + 1))


def register(server: MCPServer[AppState]) -> None:
    """Attach the resource templates and the completion handler to `server`."""

    @server.resource(
        HEXAGRAM_TEMPLATE,
        name="hexagram",
        title="One hexagram",
        description="The full text of one hexagram by King Wen number (1 to 64), as JSON.",
        mime_type="application/json",
    )
    def hexagram(number: str, ctx: Context[AppState]) -> Hexagram:
        # Parsed here rather than typed `int`: the SDK reports a failed conversion as an
        # internal error (-32603), but "iching://hexagram/abc" is simply not in the book.
        try:
            return oracle.hexagram_from_number(book_from(ctx), oracle.parse_hexagram_number(number))
        except oracle.NotInBook as exc:
            # The standard "resource not found": JSON-RPC -32602 with the URI in error.data.
            raise ResourceNotFoundError(str(exc)) from exc

    @server.resource(
        TRIGRAM_TEMPLATE,
        name="trigram",
        title="One trigram",
        description="One of the eight trigrams by English name or Chinese character, as JSON.",
        mime_type="application/json",
    )
    def trigram(name: str, ctx: Context[AppState]) -> Trigram:
        try:
            return oracle.trigram_by_name(book_from(ctx), name)
        except oracle.NotInBook as exc:
            raise ResourceNotFoundError(str(exc)) from exc

    # MCPServer.completion() is unannotated in SDK 2.3, which strict mypy rejects.
    @server.completion()  # type: ignore[untyped-decorator, no-untyped-call]
    async def complete(
        ref: PromptReference | ResourceTemplateReference,
        argument: CompletionArgument,
        context: CompletionContext | None,
    ) -> Completion | None:
        # The handler gets no Context, so the values come from domain constants
        # that the book loader validates the data against (ADR-0005).
        typed = argument.value
        if isinstance(ref, ResourceTemplateReference):
            if ref.uri == HEXAGRAM_TEMPLATE and argument.name == "number":
                return _starting_with(HEXAGRAM_NUMBERS, typed)
            if ref.uri == TRIGRAM_TEMPLATE and argument.name == "name":
                return _starting_with(TRIGRAM_NAMES, typed)
        if (
            isinstance(ref, PromptReference)
            and ref.name == "study_hexagram"
            and argument.name == "number"
        ):
            return _starting_with(HEXAGRAM_NUMBERS, typed)
        return None


def publish_static(server: MCPServer[AppState], book: Book) -> None:
    """Register the two fixed resources, their text rendered from the loaded book."""
    server.add_resource(
        TextResource(
            uri=INDEX_URI,
            name="hexagram_index",
            title="The 64 hexagrams",
            description="A compact table of all 64 hexagrams: number, symbol, name, Chinese.",
            mime_type="text/markdown",
            text=render.hexagram_index(book),
        )
    )
    server.add_resource(
        TextResource(
            uri=METHOD_URI,
            name="method",
            title="The three-coin method",
            description="How a cast works, and where the text comes from. "
            "The same content as the describe_method tool, as Markdown.",
            mime_type="text/markdown",
            text=render.method_markdown(oracle.describe_method(book)),
        )
    )


def _starting_with(options: tuple[str, ...], typed: str) -> Completion:
    """The SDK does not filter; offer only the options that match what was typed."""
    prefix = typed.strip().casefold()
    return Completion(values=[o for o in options if o.casefold().startswith(prefix)])
