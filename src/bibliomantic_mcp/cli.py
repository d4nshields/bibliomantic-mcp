"""Command-line entry point: parse arguments, configure logging, run the server.

This is the only module that touches the process: logging configuration and the
choice of transport live here, so `server.py` can stay a pure description of
*what* the server is.
"""

import argparse
import logging
import sys
from collections.abc import Sequence
from typing import Literal, get_args

from bibliomantic_mcp import __version__
from bibliomantic_mcp.server import create_server

Transport = Literal["stdio", "streamable-http"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

logger = logging.getLogger(__name__)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bibliomantic-mcp",
        description="Consult the I Ching over MCP. Results are for reflection, not prediction.",
    )
    parser.add_argument(
        "--transport",
        choices=get_args(Transport),
        default="stdio",
        help="stdio (default) for a host that launches this process, "
        "or streamable-http to listen on a port.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for streamable-http.")
    parser.add_argument("--port", type=int, default=8000, help="Port for streamable-http.")
    parser.add_argument("--log-level", choices=get_args(LogLevel), default="INFO")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def configure_logging(level: LogLevel) -> None:
    """Send all logs to stderr. In stdio mode stdout is the protocol channel."""
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    # Configure logging before the server exists: MCPServer also calls
    # logging.basicConfig(), which does nothing once a handler is installed.
    configure_logging(args.log_level)
    server = create_server()
    logger.info("Starting bibliomantic %s over %s", __version__, args.transport)
    if args.transport == "stdio":
        server.run("stdio")
    else:
        # Transport options belong to run(), not to the MCPServer constructor.
        # stateless_http=True extends the 2026-07-28 "no sessions" behaviour to
        # legacy (2025-era) clients too: this server keeps no per-client state.
        server.run(
            "streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True,
        )
