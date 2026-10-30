"""Prompts: reusable user intents, picked from a menu in the host.

Each prompt renders one user message asking the host model to call the tools
and then interpret the result for the stated situation. The prompts carry no
interpretation of their own, and only a single clause of framing.
"""

from typing import Annotated

from mcp import MCPError
from mcp.server import MCPServer
from mcp.types import INVALID_PARAMS
from pydantic import Field

from bibliomantic_mcp import oracle
from bibliomantic_mcp.state import AppState

FRAMING = "This is for reflection, not prediction."


def register(server: MCPServer[AppState]) -> None:
    """Attach the three prompts to `server`."""

    @server.prompt(title="Consult the I Ching")
    def consult(
        question: Annotated[str, Field(description="What you want to reflect on.")],
    ) -> str:
        """Cast a hexagram for a question and reflect on what it suggests."""
        return (
            f"I'd like to consult the I Ching about this: {question}\n\n"
            "Please call the `cast_hexagram` tool with my question, then help me think "
            "about what the primary hexagram, any changing lines, and the transformed "
            f"hexagram might suggest for my situation. {FRAMING}"
        )

    @server.prompt(title="Consult on a decision")
    def consult_decision(
        situation: Annotated[str, Field(description="The decision you are facing.")],
        options: Annotated[str, Field(description="The choices you are weighing.")],
    ) -> str:
        """Cast a hexagram to reflect on a choice between options."""
        return (
            f"I am choosing between these options: {options}\n\n"
            f"The situation: {situation}\n\n"
            "Please call the `cast_hexagram` tool, passing a one-line summary of my "
            "decision as the question. Then use the reading as a lens on each option: "
            "what it highlights, what it cautions against, and what questions it raises "
            f"for me. Don't choose for me. {FRAMING}"
        )

    @server.prompt(title="Study a hexagram")
    def study_hexagram(
        number: Annotated[str, Field(description="King Wen number, 1 to 64.")],
    ) -> str:
        """Learn one hexagram: its structure, trigrams, judgment, image and lines."""
        # Prompt arguments are strings typed by a person. A bad one rejects the request
        # (JSON-RPC invalid params): there is no model in the loop to read a softer error.
        try:
            number = str(oracle.parse_hexagram_number(number))
        except oracle.NotInBook as exc:
            raise MCPError(code=INVALID_PARAMS, message=str(exc)) from exc
        return (
            f"Please read the resource `iching://hexagram/{number}` and teach me this "
            "hexagram: how its two trigrams build it (look them up with `get_trigram` if "
            "useful), then its judgment, its image, and what each of the six lines adds, "
            "from the bottom up. Keep the text's own words visible alongside your "
            "explanation."
        )
