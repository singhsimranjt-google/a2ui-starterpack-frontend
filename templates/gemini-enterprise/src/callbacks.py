"""A2UI v0.9 utilities and callbacks for Gemini Enterprise Agent."""

import json
import os
import re
from typing import Any

from google.adk.agents import callback_context as callback_context_lib
from google.adk.models import llm_response as llm_response_lib
from google.genai import types

_A2UI_V09_KEYS = frozenset({
    "createSurface",
    "updateComponents",
    "updateDataModel",
    "deleteSurface",
})

_TAG_PATTERN = re.compile(
    r"<(?:a2ui-json|a2a_datapart_json)>(.*?)</(?:a2ui-json|a2a_datapart_json)>",
    re.DOTALL,
)


def _wrap_a2ui_part(a2ui_message: dict[str, Any]) -> types.Part:
    """Wraps an A2UI message as an A2A inline data blob."""
    datapart_json = json.dumps({
        "kind": "data",
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": a2ui_message,
    })
    blob_data = (
        f"<a2a_datapart_json>{datapart_json}</a2a_datapart_json>".encode("utf-8")
    )
    return types.Part(
        inline_data=types.Blob(
            data=blob_data,
            mime_type="text/plain",
        )
    )


def _extract_v09_messages(payload: Any) -> list[dict[str, Any]]:
    """Extracts A2UI message dictionaries from a parsed JSON payload."""
    if isinstance(payload, list):
        messages = []
        for item in payload:
            messages.extend(_extract_v09_messages(item))
        return messages
    if isinstance(payload, dict):
        if any(key in payload for key in _A2UI_V09_KEYS):
            return [payload]
        if "data" in payload and isinstance(payload["data"], (dict, list)):
            return _extract_v09_messages(payload["data"])
    return []


def _is_local_env() -> bool:
    """Checks if the agent is running in a local environment."""
    return os.environ.get("ENVIRONMENT", "local").lower() == "local"


def a2ui_before_model_callback(
    callback_context: callback_context_lib.CallbackContext,
    llm_request: Any,
) -> None:
    """Sanitizes history before sending to the LLM to prevent tag pollution."""
    del callback_context
    if not hasattr(llm_request, "contents") or not llm_request.contents:
        return

    for content in llm_request.contents:
        if not content.parts:
            continue
        cleaned_parts = []
        for part in content.parts:
            if part.inline_data and part.inline_data.data:
                if b"<a2a_datapart_json>" in part.inline_data.data:
                    continue
            if part.text and "<a2a_datapart_json>" in part.text:
                cleaned_text = re.sub(
                    r"<a2a_datapart_json>.*?</a2a_datapart_json>",
                    "",
                    part.text,
                    flags=re.DOTALL,
                ).strip()
                if cleaned_text:
                    cleaned_parts.append(types.Part.from_text(text=cleaned_text))
                continue
            cleaned_parts.append(part)
        content.parts = cleaned_parts or [types.Part.from_text(text=" ")]


def a2ui_callback(
    callback_context: callback_context_lib.CallbackContext,
    llm_response: llm_response_lib.LlmResponse,
) -> llm_response_lib.LlmResponse | None:
    """Processes LLM responses to extract clean text and A2UI data parts."""
    del callback_context
    if not llm_response.content or not llm_response.content.parts:
        return None

    transformed_parts = []
    has_a2ui_tags = False
    has_a2ui_parts = False

    for part in llm_response.content.parts:
        if not part.text or part.thought:
            transformed_parts.append(part)
            continue

        raw_text = part.text
        tag_blocks = _TAG_PATTERN.findall(raw_text)

        # Simple text content with no A2UI tags
        if not tag_blocks:
            transformed_parts.append(part)
            continue

        has_a2ui_tags = True
        clean_text = _TAG_PATTERN.sub("", raw_text).strip()

        # Parse and extract A2UI messages from all blocks
        a2ui_parts = []
        for index, block in enumerate(tag_blocks, start=1):
            block_str = block.strip()
            if not block_str:
                continue
            try:
                parsed = json.loads(block_str)
                messages = _extract_v09_messages(parsed)
                for message in messages:
                    a2ui_parts.append(_wrap_a2ui_part(message))
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        is_local = _is_local_env()
        if a2ui_parts:
            has_a2ui_parts = True
            if is_local:
                if clean_text:
                    transformed_parts.append(types.Part.from_text(text=clean_text))
                transformed_parts.extend(a2ui_parts)
            else:
                transformed_parts.extend(a2ui_parts)
        else:
            if clean_text:
                transformed_parts.append(types.Part.from_text(text=clean_text))

    if not has_a2ui_tags:
        return None

    custom_metadata = getattr(llm_response, "custom_metadata", None) or {}
    if has_a2ui_parts:
        custom_metadata["a2a:response"] = True

    return llm_response.model_copy(
        update={
            "content": types.Content(role="model", parts=transformed_parts),
            "custom_metadata": custom_metadata,
        }
    )