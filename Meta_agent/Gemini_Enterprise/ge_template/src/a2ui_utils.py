"""A2UI v0.9 response parsing and ADK callbacks."""

import json
import uuid
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from google.adk.agents import callback_context as callback_context_lib
from google.adk.models import llm_response as llm_response_lib
from google.genai import types

logger = logging.getLogger(__name__)

_A2UI_V09_KEYS = frozenset(
    {"createSurface", "updateComponents", "updateDataModel", "deleteSurface"}
)

# Matches BOTH tag styles so replayed history is handled too.
_TAG_PATTERN = re.compile(
    r"<(?:a2ui-json|a2a_datapart_json)>(.*?)</(?:a2ui-json|a2a_datapart_json)>",
    re.DOTALL,
)


def extract_v09_messages(payload: Any) -> List[Dict[str, Any]]:
    """Extracts valid A2UI v0.9 message dictionaries from parsed JSON."""
    if isinstance(payload, list):
        messages: List[Dict[str, Any]] = []
        for item in payload:
            messages.extend(extract_v09_messages(item))
        return messages
    if isinstance(payload, dict):
        if any(key in payload for key in _A2UI_V09_KEYS):
            return [payload]
        if "data" in payload and isinstance(payload["data"], (dict, list)):
            return extract_v09_messages(payload["data"])
    return []


def parse_a2ui_response(raw_text: str) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """Splits raw model text into (companion markdown, a2ui messages).

    Retained for local HTTP serving and tests.
    """
    if not raw_text:
        return "", None
    blocks = _TAG_PATTERN.findall(raw_text)
    if not blocks:
        return raw_text.strip(), None

    messages: List[Dict[str, Any]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        try:
            messages.extend(extract_v09_messages(json.loads(block)))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Skipping malformed A2UI block")

    clean_text = _TAG_PATTERN.sub("", raw_text).strip()
    return clean_text, messages or None


A2UI_VERSION = "v0.9"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

_SURFACE_KEYS = ("createSurface", "updateComponents", "updateDataModel", "deleteSurface")


def _message_key(message: Dict[str, Any]) -> Optional[str]:
    """Returns the single A2UI payload key carried by a message."""
    for key in _SURFACE_KEYS:
        if key in message:
            return key
    return None


def normalize_a2ui_messages(
    messages: List[Dict[str, Any]],
    uuid_suffix: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Repairs a model-generated A2UI block so it always satisfies the spec.

    The model produces these payloads freehand and is only probabilistically
    compliant, so the following are enforced in code rather than by prompt:

    1. Every message carries ``version``.
    2. ``createSurface`` always carries the correct ``catalogId``.
    3. All messages in the block share one ``surfaceId`` (the model sometimes
       drifts between the create and the update, which the renderer reports
       as "Surface not found").
    4. A ``createSurface`` is synthesized if the block omits one.
    5. ``deleteSurface`` for a surface not created in this block is dropped;
       the spec requires a prior ``createSurface`` for that id.
    """
    if not messages:
        return messages

    if uuid_suffix is None:
        uuid_suffix = uuid.uuid4().hex[:8]

    # (3) Prefer the id the block creates; otherwise the first content message.
    base_id = None
    for message in messages:
        if _message_key(message) == "createSurface":
            base_id = message["createSurface"].get("surfaceId")
            break
    if not base_id:
        for message in messages:
            key = _message_key(message)
            # A deleteSurface id refers to something we are discarding.
            if key and key != "deleteSurface" and isinstance(message[key], dict):
                base_id = message[key].get("surfaceId")
                if base_id:
                    break
    if not base_id:
        base_id = "a2ui_surface"

    # CRITICAL FIX: The LLM often hallucinates the exact same surfaceId across turns.
    # To prevent A2UI from crashing with "Surface already exists", we MUST override
    # whatever the LLM generated with a globally unique ID for this block.
    if base_id.endswith(f"-{uuid_suffix}"):
        surface_id = base_id
    else:
        surface_id = f"{base_id}-{uuid_suffix}"

    normalized: List[Dict[str, Any]] = []
    has_create = False

    for message in messages:
        key = _message_key(message)
        if not key or not isinstance(message[key], dict):
            continue

        payload = dict(message[key])
        payload["surfaceId"] = surface_id

        if key == "deleteSurface" and not has_create:
            # (5) Nothing to delete; the renderer would reject this.
            logger.warning("Dropping deleteSurface for uncreated surface %s", surface_id)
            continue

        if key == "createSurface":
            if payload.get("catalogId") != BASIC_CATALOG_ID:
                payload["catalogId"] = BASIC_CATALOG_ID  # (2)
            has_create = True

        normalized.append({"version": A2UI_VERSION, key: payload})  # (1)

    # (4) A surface must exist before it can be updated.
    if normalized and not has_create:
        logger.warning("Synthesizing missing createSurface for %s", surface_id)
        normalized.insert(
            0,
            {
                "version": A2UI_VERSION,
                "createSurface": {
                    "surfaceId": surface_id,
                    "catalogId": BASIC_CATALOG_ID,
                },
            },
        )

    return normalized


# --------------------------------------------------------------------------
# L3 - validation
# --------------------------------------------------------------------------

_validator: Any = None
_validator_ready = False


def _get_validator() -> Any:
    """Lazily builds the A2UI validator; returns None if unavailable."""
    global _validator, _validator_ready
    if _validator_ready:
        return _validator
    _validator_ready = True
    try:
        from a2ui.basic_catalog.provider import BasicCatalog
        from a2ui.inference_formats.direct_json import DirectJsonFormat
        from a2ui.schema import constants

        fmt = DirectJsonFormat(
            constants.VERSION_0_9,
            [BasicCatalog.get_config(constants.VERSION_0_9)],
        )
        _validator = fmt._select_catalog(None).validator
    except Exception as err:  # pragma: no cover - environment dependent
        logger.warning("A2UI validator unavailable, skipping validation: %s", err)
        _validator = None
    return _validator


def is_renderable(messages: List[Dict[str, Any]]) -> bool:
    """True if the payload satisfies schema, reference integrity and topology.

    Fails *open*: if the validator itself cannot be constructed we return True,
    so a missing dependency can never stop a working UI from rendering.
    """
    validator = _get_validator()
    if validator is None:
        return True
    try:
        validator.validate(messages)
        return True
    except Exception as err:
        logger.warning("A2UI payload failed validation: %s", err)
        return False

def _wrap_a2ui_part(a2ui_message: Dict[str, Any]) -> types.Part:
    """Wraps a single A2UI message as an A2A inline data blob."""
    datapart_json = json.dumps(
        {
            "kind": "data",
            "metadata": {"mimeType": "application/json+a2ui"},
            "data": a2ui_message,
        }
    )
    blob_data = f"<a2a_datapart_json>{datapart_json}</a2a_datapart_json>".encode("utf-8")
    return types.Part(inline_data=types.Blob(data=blob_data, mime_type="text/plain"))


def _is_local_env() -> bool:
    """True when running locally (keeps companion text alongside data parts)."""
    return os.environ.get("ENVIRONMENT", "local").lower() == "local"


def a2ui_before_model_callback(
    callback_context: callback_context_lib.CallbackContext,
    llm_request: Any,
) -> None:
    """Strips previously emitted A2A data parts out of conversation history.

    Without this the model sees its own data parts replayed as input and starts
    imitating them, so output quality decays over a multi-turn conversation.
    """
    del callback_context
    if not getattr(llm_request, "contents", None):
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
):
    """Converts <a2ui-json> blocks into A2A data parts for Gemini Enterprise."""
    if not llm_response.content or not llm_response.content.parts:
        return None

    raw_text_full = "".join([p.text for p in llm_response.content.parts if getattr(p, "text", None) and not getattr(p, "thought", False)])
    # # print(f"\n🤖 [LLM RESPONSE]:\n{raw_text_full}\n" + "-" * 40)

    transformed_parts = []
    has_a2ui_tags = False
    has_a2ui_parts = False

    for part in llm_response.content.parts:
        if not part.text or part.thought:
            transformed_parts.append(part)
            continue

        raw_text = part.text
        tag_blocks = _TAG_PATTERN.findall(raw_text)
        if not tag_blocks:
            transformed_parts.append(part)
            continue

        has_a2ui_tags = True
        clean_text = _TAG_PATTERN.sub("", raw_text).strip()

        a2ui_parts = []
        tool_result = callback_context.state.get("last_tool_result")
        for block in tag_blocks:
            block_str = block.strip()
            if not block_str:
                continue
            try:
                messages = extract_v09_messages(json.loads(block_str))
                # messages = resolve_placeholders(messages, tool_result)
                normalized_messages = normalize_a2ui_messages(messages)
                                
                # Apply L3 Validation
                if not is_renderable(normalized_messages):
                    logger.warning("Dropping invalid A2UI payload because it failed schema validation.")
                    continue

                for message in normalize_a2ui_messages(messages):
                    a2ui_parts.append(_wrap_a2ui_part(message))
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                # Log the payload so the failure is diagnosable from Cloud Logging.
                logger.warning(
                    "Skipping malformed A2UI block (%s): %s", exc, block_str[:2000]
                )

        if a2ui_parts:
            has_a2ui_parts = True
            if _is_local_env() and clean_text:
                transformed_parts.append(types.Part.from_text(text=clean_text))
            transformed_parts.extend(a2ui_parts)
        elif clean_text:
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


def a2ui_after_tool_callback(*args, **kwargs):
    """Stores the latest tool result in the context state for A2UI placeholder resolution."""
    # ADK passes tool_context and tool_response as kwargs
    callback_context = kwargs.get("tool_context")
    tool_response = kwargs.get("tool_response")
    
    if not callback_context or not tool_response:
        return
        
    payload = getattr(tool_response, "response", None)
    if payload:
        payload = dict(payload)
        inner = payload.get("result")
        if len(payload) == 1 and isinstance(inner, dict):
            payload = inner
        # # print(f"\n✅ [TOOL FINISHED]: Stashing result for placeholder resolution:\n{payload}\n" + "-" * 40)
        callback_context.state["last_tool_result"] = payload


__all__ = [
    "extract_v09_messages",
    "normalize_a2ui_messages",
    "parse_a2ui_response",
    "a2ui_callback",
    "a2ui_before_model_callback",
    "a2ui_after_tool_callback",
    "resolve_placeholders",
]

def _resolve_string(text: str, tool_result: Any) -> str:
    if not tool_result:
        return text
    
    def replacer(match):
        path = match.group(1).strip()
        parts = path.split(".")
        if parts[0] != "result":
            return match.group(0)
        
        current = tool_result
        for part in parts[1:]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
                current = current[int(part)]
            else:
                return match.group(0)
        return str(current)
    
    import re
    return re.sub(r"\$\{([^}]+)\}", replacer, text)


def resolve_placeholders(payload: Any, tool_result: Any) -> Any:
    if isinstance(payload, dict):
        return {k: resolve_placeholders(v, tool_result) for k, v in payload.items()}
    if isinstance(payload, list):
        return [resolve_placeholders(v, tool_result) for v in payload]
    if isinstance(payload, str) and "${" in payload:
        return _resolve_string(payload, tool_result)
    return payload
