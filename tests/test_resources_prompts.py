"""Resources, resource templates, completions and prompts, through a real client."""

import json

import pytest
from mcp import Client, MCPError
from mcp.types import INVALID_PARAMS, PromptReference, ResourceTemplateReference, TextContent

from bibliomantic_mcp.models import Hexagram, Trigram
from bibliomantic_mcp.prompts import FRAMING, INTERPRETATION_GUIDANCE
from bibliomantic_mcp.server import INSTRUCTIONS

pytestmark = pytest.mark.anyio


def text_of(contents: object) -> str:
    text: str = contents.contents[0].text  # type: ignore[attr-defined]
    return text


# --- Listing ---------------------------------------------------------------


async def test_static_resources_are_listed_with_title_and_mime_type(client: Client) -> None:
    listed = {r.uri: r for r in (await client.list_resources()).resources}
    assert list(listed) == ["iching://hexagrams", "iching://method"]
    for resource in listed.values():
        assert resource.title
        assert resource.description
        assert resource.mime_type == "text/markdown"


async def test_templates_are_listed_with_title_and_mime_type(client: Client) -> None:
    listed = {
        t.uri_template: t for t in (await client.list_resource_templates()).resource_templates
    }
    assert list(listed) == ["iching://hexagram/{number}", "iching://trigram/{name}"]
    for template in listed.values():
        assert template.title
        assert template.description
        assert template.mime_type == "application/json"


# --- Reading ---------------------------------------------------------------


async def test_index_lists_all_64(client: Client) -> None:
    result = await client.read_resource("iching://hexagrams")
    assert result.contents[0].mime_type == "text/markdown"
    text = text_of(result)
    assert "| 1 | ䷀ | The Creative | 乾 |" in text
    assert "| 64 | ䷿ |" in text
    assert text.count("\n| ") == 64 + 1  # header row + one row per hexagram


async def test_read_hexagram_json(client: Client) -> None:
    result = await client.read_resource("iching://hexagram/29")
    assert result.contents[0].mime_type == "application/json"
    hexagram = Hexagram.model_validate(json.loads(text_of(result)))
    assert (hexagram.number, hexagram.upper, hexagram.lower) == (29, "Water", "Water")


async def test_read_trigram_json(client: Client) -> None:
    result = await client.read_resource("iching://trigram/Fire")
    assert Trigram.model_validate(json.loads(text_of(result))).binary == "101"


async def test_method_resource_matches_the_tool(client: Client) -> None:
    text = text_of(await client.read_resource("iching://method"))
    assert text.startswith("# The three-coin method")
    tool = await client.call_tool("describe_method", {})
    assert tool.structured_content is not None
    assert tool.structured_content["coins"] in text
    assert tool.structured_content["source"] in text


@pytest.mark.parametrize(
    "uri",
    [
        "iching://hexagram/0",
        "iching://hexagram/65",
        "iching://hexagram/abc",
        pytest.param("iching://hexagram/" + "9" * 5000, id="past-int-digit-limit"),
    ],
)
async def test_bad_hexagram_is_resource_not_found(client: Client, uri: str) -> None:
    with pytest.raises(MCPError) as caught:
        await client.read_resource(uri)
    assert caught.value.error.code == INVALID_PARAMS  # -32602, the 2026-07-28 not-found code
    assert caught.value.error.data == {"uri": uri}


async def test_bad_trigram_is_resource_not_found(client: Client) -> None:
    with pytest.raises(MCPError) as caught:
        await client.read_resource("iching://trigram/Sky")
    assert caught.value.error.code == INVALID_PARAMS
    assert "Valid names" in caught.value.error.message


# --- Completions -----------------------------------------------------------


async def test_completions_capability_is_declared(client: Client) -> None:
    assert client.server_capabilities is not None
    assert client.server_capabilities.completions is not None


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("", [str(n) for n in range(1, 65)]),
        ("6", ["6", "60", "61", "62", "63", "64"]),
        ("64", ["64"]),
        ("9", ["9"]),
        ("x", []),
    ],
)
async def test_hexagram_number_completion(client: Client, typed: str, expected: list[str]) -> None:
    ref = ResourceTemplateReference(uri="iching://hexagram/{number}")
    result = await client.complete(ref, {"name": "number", "value": typed})
    assert result.completion.values == expected


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("", ["Heaven", "Lake", "Fire", "Thunder", "Wind", "Water", "Mountain", "Earth"]),
        ("w", ["Wind", "Water"]),
        ("MOUN", ["Mountain"]),
    ],
)
async def test_trigram_name_completion(client: Client, typed: str, expected: list[str]) -> None:
    ref = ResourceTemplateReference(uri="iching://trigram/{name}")
    result = await client.complete(ref, {"name": "name", "value": typed})
    assert result.completion.values == expected


async def test_study_prompt_number_completion(client: Client) -> None:
    ref = PromptReference(name="study_hexagram")
    result = await client.complete(ref, {"name": "number", "value": "5"})
    assert result.completion.values == [
        "5",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
    ]


async def test_unknown_argument_gets_no_suggestions(client: Client) -> None:
    ref = PromptReference(name="consult")
    result = await client.complete(ref, {"name": "question", "value": "W"})
    assert result.completion.values == []


# --- Prompts ---------------------------------------------------------------


async def test_prompts_are_listed_with_described_arguments(client: Client) -> None:
    prompts = {p.name: p for p in (await client.list_prompts()).prompts}
    assert list(prompts) == [
        "consult",
        "consult_decision",
        "consult_creative_work",
        "study_hexagram",
    ]
    expected_args = {
        "consult": ["question"],
        "consult_decision": ["situation", "options"],
        "consult_creative_work": ["work_context", "uncertainty"],
        "study_hexagram": ["number"],
    }
    for name, prompt in prompts.items():
        assert prompt.title
        assert prompt.description
        arguments = prompt.arguments or []
        assert [a.name for a in arguments] == expected_args[name]
        for argument in arguments:
            assert argument.required
            assert argument.description


def message_text(result: object) -> str:
    [message] = result.messages  # type: ignore[attr-defined]
    assert message.role == "user"
    assert isinstance(message.content, TextContent)
    text: str = message.content.text
    return text


async def test_consult_asks_the_host_to_cast_and_interpret(client: Client) -> None:
    text = message_text(await client.get_prompt("consult", {"question": "Should I move?"}))
    assert "Should I move?" in text
    assert "`cast_hexagram`" in text
    assert "for reflection, not prediction" in text


async def test_consult_decision_includes_situation_and_options(client: Client) -> None:
    result = await client.get_prompt(
        "consult_decision", {"situation": "A job offer abroad", "options": "stay, or go"}
    )
    text = message_text(result)
    assert "A job offer abroad" in text
    assert "stay, or go" in text
    assert "`cast_hexagram`" in text
    assert "for reflection, not prediction" in text


async def test_creative_prompt_preserves_context_and_requests_application(client: Client) -> None:
    result = await client.get_prompt(
        "consult_creative_work",
        {
            "work_context": "The investigator has never met the missing witness.",
            "uncertainty": "Should she publish the evidence or investigate its origin?",
        },
    )
    text = message_text(result)
    assert "The investigator has never met the missing witness." in text
    assert "Should she publish the evidence or investigate its origin?" in text
    assert "`cast_hexagram` once" in text
    assert "Apply that constraint to the work itself" in text
    assert "Preserve established facts" in text


async def test_consultation_guidance_reaches_both_entry_paths(client: Client) -> None:
    """Prompt selection and direct tool use share the same interpretive method."""
    assert INTERPRETATION_GUIDANCE in INSTRUCTIONS
    assert "only when the user requests" in INSTRUCTIONS
    for name, args in {
        "consult": {"question": "q"},
        "consult_decision": {"situation": "s", "options": "o"},
        "consult_creative_work": {"work_context": "w", "uncertainty": "u"},
    }.items():
        text = message_text(await client.get_prompt(name, args))
        assert text.count(INTERPRETATION_GUIDANCE) == 1
        assert text.count(FRAMING) == 1
    tool = next(t for t in (await client.list_tools()).tools if t.name == "cast_hexagram")
    assert tool.description
    assert "only when the user requests" in tool.description
    assert "Reuse this cast" in tool.description


async def test_study_hexagram_points_at_the_resource(client: Client) -> None:
    text = message_text(await client.get_prompt("study_hexagram", {"number": "11"}))
    assert "iching://hexagram/11" in text


@pytest.mark.parametrize(
    "number", ["0", "65", "eleven", pytest.param("9" * 5000, id="past-int-digit-limit")]
)
async def test_study_hexagram_rejects_a_bad_number(client: Client, number: str) -> None:
    with pytest.raises(MCPError) as caught:
        await client.get_prompt("study_hexagram", {"number": number})
    assert caught.value.error.code == INVALID_PARAMS
    assert "1–64" in caught.value.error.message


async def test_prompts_do_not_carry_the_full_disclaimer(client: Client) -> None:
    """One framing clause is enough; the long statement lives in instructions and README."""
    for name, args in {
        "consult": {"question": "q"},
        "consult_decision": {"situation": "s", "options": "o"},
        "consult_creative_work": {"work_context": "w", "uncertainty": "u"},
        "study_hexagram": {"number": "1"},
    }.items():
        text = message_text(await client.get_prompt(name, args))
        assert "not advice" not in text
