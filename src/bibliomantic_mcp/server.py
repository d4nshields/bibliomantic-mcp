"""Build the one MCPServer this project exposes.

The constructor takes *identity* only: who the server is and what it is for.
How it is served (stdio, HTTP, which port) is decided later, in `cli.py`,
by the arguments passed to `run()`.
"""

from mcp.server import MCPServer

from bibliomantic_mcp import __version__

INSTRUCTIONS = """\
This server is an I Ching: it casts a hexagram with the traditional three-coin method \
and returns the canonical text (James Legge's public-domain translation).
Call `cast_hexagram` to consult; use `get_hexagram`, `get_trigram` and the `iching://` \
resources to look things up.
The server only casts coins and retrieves text. Interpreting the result for the user's \
situation is your job, as the host.
Treat every result as a prompt for reflection and creativity, not as a prediction or as advice.\
"""


def create_server() -> MCPServer:
    """Construct the server. A factory, not a module global, so tests get a fresh one."""
    return MCPServer(
        "bibliomantic",
        title="Bibliomantic I Ching",
        instructions=INSTRUCTIONS,
        version=__version__,
    )
