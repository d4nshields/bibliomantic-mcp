"""Capture fixed-coin responses from the target checkout through MCP."""

import argparse
import asyncio
import json
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any
from unittest.mock import patch

from mcp import Client
from mcp.types import CallToolResult
from pydantic import BaseModel

import bibliomantic_mcp
from bibliomantic_mcp.models import CoinToss
from bibliomantic_mcp.server import INSTRUCTIONS, create_server

FIXTURES = {
    "no_change": (7, 8, 7, 8, 7, 8),
    "one_change": (9, 8, 7, 8, 7, 8),
    "contemplation_20_1_6_to_3": (6, 8, 8, 8, 7, 9),
    "all_yang_changing": (9, 9, 9, 9, 9, 9),
    "all_yin_changing": (6, 6, 6, 6, 6, 6),
    "still_mountain": (8, 8, 7, 8, 8, 7),
}
QUESTION = "Should the investigator publish the evidence or investigate its origin?"
PROMPTS = {
    "consult": {"question": QUESTION},
    "consult_decision": {
        "situation": "Evidence implicates the investigator's mentor.",
        "options": "Publish the evidence, or investigate its origin first.",
    },
    "consult_creative_work": {
        "work_context": (
            "An investigator has evidence implicating her mentor. She has never met "
            "the missing witness. The next scene takes place in the archive."
        ),
        "uncertainty": QUESTION,
    },
    "study_hexagram": {"number": "20"},
}


def dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json", by_alias=True)


def text_of(result: CallToolResult) -> str:
    return "\n".join(block.text for block in result.content if block.type == "text")


def coins_for(value: int) -> CoinToss:
    # Heads = 3, tails = 2. Three tails total 6; each head adds 1.
    heads = (value >= 7, value >= 8, value >= 9)
    return CoinToss(heads=heads)


async def capture(output_dir: Path) -> None:
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    package_file = Path(bibliomantic_mcp.__file__).resolve()
    if not package_file.is_relative_to(root / "src"):
        raise ValueError(f"Expected the editable package from {root}, imported {package_file}")
    output_dir.mkdir(parents=True, exist_ok=False)
    capture_data: dict[str, Any] = {
        "metadata": {
            "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "mcp_version": version("mcp"),
            "package_file": str(package_file),
        },
        # Configuration exported by the module, not a claim about host ingestion.
        "server_instructions": INSTRUCTIONS,
        "casts": {},
        "prompts": {},
    }
    async with Client(create_server(), raise_exceptions=True) as client:
        tools = await client.list_tools()
        prompt_list = await client.list_prompts()
        capture_data["tools_list"] = dump(tools)
        capture_data["prompts_list"] = dump(prompt_list)
        capture_data["resources_list"] = dump(await client.list_resources())
        available = {p.name for p in prompt_list.prompts}

        for name, values in FIXTURES.items():
            with patch(
                "bibliomantic_mcp.oracle.toss_coins",
                side_effect=[coins_for(v) for v in values],
            ) as fixed_coins:
                response = await client.call_tool("cast_hexagram", {"question": QUESTION})
            structured = response.structured_content
            if (
                fixed_coins.call_count != 6
                or response.is_error
                or structured is None
                or structured["values"] != list(values)
            ):
                raise ValueError(f"{name}: cast did not return the expected fixed values")
            text = text_of(response)
            capture_data["casts"][name] = {
                "response": dump(response),
                "cast": structured,
                "text": text,
                "text_characters": len(text),
            }
            (output_dir / f"{name}.txt").write_text(text + "\n", encoding="utf-8")

        for name, arguments in PROMPTS.items():
            if name not in available:
                capture_data["prompts"][name] = {"available": False}
                continue
            prompt_response = await client.get_prompt(name, arguments)
            text = "\n".join(
                message.content.text
                for message in prompt_response.messages
                if message.content.type == "text"
            )
            capture_data["prompts"][name] = {
                "available": True,
                "response": dump(prompt_response),
                "text": text,
            }
            (output_dir / f"prompt-{name}.txt").write_text(text + "\n", encoding="utf-8")
        for key, tool, tool_arguments in (
            ("method", "describe_method", {}),
            ("lookup_20", "get_hexagram", {"number": 20}),
        ):
            response = await client.call_tool(tool, tool_arguments)
            if response.is_error:
                raise ValueError(f"{tool}: {text_of(response)}")
            capture_data[key] = dump(response)

    (output_dir / "server-instructions.txt").write_text(INSTRUCTIONS + "\n", encoding="utf-8")
    (output_dir / "capture.json").write_text(
        json.dumps(capture_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(capture_data["metadata"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    asyncio.run(asyncio.wait_for(capture(args.output.resolve()), timeout=60))
