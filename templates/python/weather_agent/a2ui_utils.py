"""A2UI v0.9 response parsing and ADK callbacks."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_A2UI_V09_KEYS = frozenset(
    {
        "createSurface",
        "updateComponents",
        "updateDataModel",
        "deleteSurface",
    }
)

_TAG_PATTERN = re.compile(
    r"<a2ui-json>(.*?)</a2ui-json>",
    re.DOTALL,
)


def extract_v09_messages(payload: Any) -> List[Dict[str, Any]]:
    """Extracts valid A2UI v0.9 message dictionaries from parsed JSON."""
    if isinstance(payload, list):
        messages = []
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
    """Extracts companion markdown text and structured A2UI v0.9 components from model text."""
    if not raw_text:
        return "", None

    tag_blocks = _TAG_PATTERN.findall(raw_text)
    if not tag_blocks:
        return raw_text.strip(), None

    clean_text = _TAG_PATTERN.sub("", raw_text).strip()
    a2ui_messages: List[Dict[str, Any]] = []

    for index, block in enumerate(tag_blocks, start=1):
        block_str = block.strip()
        if not block_str:
            continue
        try:
            parsed = json.loads(block_str)
            extracted = extract_v09_messages(parsed)
            a2ui_messages.extend(extracted)
        except (json.JSONDecodeError, ValueError, TypeError) as err:
            logger.warning("Failed to parse A2UI JSON in block %d: %s", index, err)

    return clean_text, a2ui_messages if a2ui_messages else None


def a2ui_callback(callback_context: Any, llm_response: Any) -> Any:
    """Processes LLM responses to ensure clean text and A2UI data parts."""
    del callback_context
    return llm_response


__all__ = [
    "extract_v09_messages",
    "parse_a2ui_response",
    "a2ui_callback",
]
