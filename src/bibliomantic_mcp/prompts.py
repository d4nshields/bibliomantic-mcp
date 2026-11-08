"""Prompts: reusable user intents, picked from a menu in the host.

Each prompt renders one user message asking the host model to call the tools
and then interpret the result for the stated situation. Shared guidance supplies
an interpretive method, never a prewritten interpretation or a fixed output form.
"""

from typing import Annotated

from mcp import MCPError
from mcp.server import MCPServer
from mcp.types import INVALID_PARAMS
from pydantic import Field

from bibliomantic_mcp import oracle
from bibliomantic_mcp.state import AppState

FRAMING = "This is for reflection, not prediction."

INTERPRETATION_GUIDANCE = """\
Read the cast in relation to the user's actual question and the surrounding conversation.
Keep the returned cast fixed; reuse it for follow-up interpretation. Do not recast to obtain
a more convenient result. Use lookup tools if more source material is needed.
Begin with what is distinctive in the supplied text: an image, action, relationship, or
tension. Explain unfamiliar wording briefly, then explore how it might illuminate or
unsettle the user's framing.
Give the changing-line texts particular attention. When they pull in different directions,
preserve that tension instead of forcing agreement. Treat the related hexagram as a further
perspective on the change, not a guaranteed future. Do not treat every unchanging line in
the full record as selected guidance. With no changing lines, stay with the primary figure.
Ground the interpretation in identifiable passages. Distinguish what the text says from
the connection you propose. Do not invent quotations, missing facts about the user, or
certainty that the text fits. An uncertain connection may remain uncertain.
Prefer one well-developed interpretation over a catalogue of generic associations. Offer
another reading only when a genuine ambiguity matters. Write naturally, without obligatory
headings or a fixed advice template. Let the user disagree or refine the connection. Ask a
focused question only when its answer would materially change the reading.\
"""


def register(server: MCPServer[AppState]) -> None:
    """Attach the four prompts to `server`."""

    @server.prompt(title="Consult the I Ching")
    def consult(
        question: Annotated[str, Field(description="What you want to reflect on.")],
    ) -> str:
        """Cast a hexagram for a question and reflect on what it suggests."""
        return (
            f"I'd like to consult the I Ching about this: {question}\n\n"
            "Please call the `cast_hexagram` tool with my question, then help me think "
            "about what the primary hexagram, any changing lines, and the transformed "
            f"hexagram might suggest for my situation. {FRAMING}\n\n"
            f"{INTERPRETATION_GUIDANCE}"
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
            "decision as the question. Explore what the reading brings into focus about "
            "the decision, including assumptions my list of options may conceal. Compare "
            "options where the text makes a meaningful distinction; do not force a matching "
            "set of pros and cons for every option. Don't choose for me. "
            f"{FRAMING}\n\n{INTERPRETATION_GUIDANCE}"
        )

    @server.prompt(title="Let a cast influence creative work")
    def consult_creative_work(
        work_context: Annotated[
            str, Field(description="The work in progress and the established facts to preserve.")
        ],
        uncertainty: Annotated[
            str, Field(description="The unresolved creative choice the cast should influence.")
        ],
    ) -> str:
        """Cast once and apply a text-grounded creative constraint to the work itself."""
        return (
            f"The work in progress: {work_context}\n\n"
            f"The unresolved point: {uncertainty}\n\n"
            "Please call `cast_hexagram` once, summarising the unresolved point as the "
            "question. Use a specific image, action, or tension in the returned text to "
            "introduce a consequential creative constraint. Apply that constraint to the "
            "work itself. For fiction, let it affect a character's choice, a relationship, "
            "a discovery, or the sequence of events. Preserve established facts unless I "
            "invite their revision. Briefly identify what in the cast prompted the change. "
            "Avoid merely adding I Ching imagery or explaining how the existing plan "
            f"already matches it. {FRAMING}\n\n{INTERPRETATION_GUIDANCE}"
        )

    @server.prompt(title="Study a hexagram")
    def study_hexagram(
        number: Annotated[str, Field(description="King Wen number, 1 to 64.")],
    ) -> str:
        """Learn one hexagram: its structure, trigrams, judgment, image and lines."""
        # Prompt arguments are strings typed by a person. A bad one rejects the request
        # (JSON-RPC invalid params): there is no model in the loop to read a softer error.
        try:
            n = oracle.parse_hexagram_number(number)
        except oracle.NotInBook as exc:
            raise MCPError(code=INVALID_PARAMS, message=str(exc)) from exc
        return (
            f"Please read the resource `iching://hexagram/{n}` and teach me this "
            "hexagram: how its two trigrams build it (look them up with `get_trigram` if "
            "useful), then its judgment, its image, and what each of the six lines adds, "
            "from the bottom up. Keep the text's own words visible alongside your "
            "explanation."
        )
