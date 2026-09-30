"""A2UI v0.9 response parsing, normalization and data resolution.

Design note
-----------
The LLM is treated as an untrusted source of structure. It decides *which*
view to show and *what* the copy says; everything required for protocol
validity is enforced here, in code, so behaviour does not vary by model.

Pipeline:  extract -> resolve placeholders -> normalize -> frontend
"""

import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

A2UI_VERSION = "v0.9"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

_A2UI_V09_KEYS = frozenset(
    {
        "createSurface",
        "updateComponents",
        "updateDataModel",
        "deleteSurface",
    }
)

_SURFACE_KEYS = ("createSurface", "updateComponents", "updateDataModel", "deleteSurface")

_TAG_PATTERN = re.compile(
    r"<a2ui-json>(.*?)</a2ui-json>",
    re.DOTALL,
)

_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _loads_lenient(text: str) -> Any:
    """json.loads, retried once after removing trailing commas (a common LLM slip)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _TRAILING_COMMA.sub(r"\1", text)
        if repaired == text:
            raise
        logger.warning("Repaired trailing commas in A2UI JSON")
        return json.loads(repaired)


# A2UI v0.9 has NO string interpolation: DynamicString is a literal string, a
# {"path": ...} DataBinding, or a FunctionCall. Any "${...}" the model emits is
# therefore dead text, and we substitute it server-side before it reaches the UI.
_PLACEHOLDER = re.compile(r"\$\{([^}]+)\}")
_PATH_TOKEN = re.compile(r"[^.\[\]]+|\[\d+\]")


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


# --------------------------------------------------------------------------
# L2 - data resolution
# --------------------------------------------------------------------------


def _lookup(expression: str, tool_result: Any) -> Any:
    """Resolves "result.appointments[0].doctor" against a tool result dict."""
    tokens = _PATH_TOKEN.findall(expression.strip())
    current = tool_result
    for index, token in enumerate(tokens):
        if index == 0 and token == "result":
            continue
        if token.startswith("["):
            position = int(token[1:-1])
            if isinstance(current, list) and 0 <= position < len(current):
                current = current[position]
            else:
                return None
        else:
            if isinstance(current, dict) and token in current:
                current = current[token]
            else:
                return None
    return current


def _resolve_string(value: str, tool_result: Any) -> str:
    """Substitutes every ${...} in a string, blanking anything unresolvable."""

    def substitute(match: "re.Match[str]") -> str:
        resolved = _lookup(match.group(1), tool_result)
        if resolved is None:
            logger.warning("Unresolvable A2UI placeholder: %s", match.group(0))
            return ""
        return str(resolved)

    return _PLACEHOLDER.sub(substitute, value)


def resolve_placeholders(payload: Any, tool_result: Any) -> Any:
    """Recursively substitutes ${...} expressions using the latest tool result.

    Safety net only. With correct examples the model writes literal values, but
    a model that ignores that instruction must not leak "${result.doctor}" to
    the user.
    """
    if isinstance(payload, dict):
        # FunctionCalls (e.g. formatString) carry client-side ${...} expressions
        # that the renderer evaluates against the data model. Leave them intact.
        if "call" in payload:
            return payload
        return {k: resolve_placeholders(v, tool_result) for k, v in payload.items()}
    if isinstance(payload, list):
        return [resolve_placeholders(v, tool_result) for v in payload]
    if isinstance(payload, str) and "${" in payload:
        return _resolve_string(payload, tool_result)
    return payload


# --------------------------------------------------------------------------
# L1 - protocol normalization
# --------------------------------------------------------------------------


def _message_key(message: Dict[str, Any]) -> Optional[str]:
    """Returns the single A2UI payload key carried by a message."""
    for key in _SURFACE_KEYS:
        if key in message:
            return key
    return None


EXTENDED_CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), "catalogs", "extended_catalog.json"
)


def get_catalog_config(examples_path: Optional[str] = None) -> Any:
    """Basic catalog + Table + Chart. Used by the agent prompt AND the runtime validator."""
    from a2ui.schema.catalog import CatalogConfig

    return CatalogConfig.from_path(
        "extended_basic", EXTENDED_CATALOG_PATH, examples_path=examples_path
    )


def _refs(c: Dict[str, Any]) -> List[str]:
    """Every component id that component `c` points at (children, child, Modal, Tabs)."""
    out: List[str] = []
    children = c.get("children")
    if isinstance(children, list):
        out += [r for r in children if isinstance(r, str)]
    elif isinstance(children, dict) and isinstance(children.get("componentId"), str):
        out.append(children["componentId"])
    for key in ("child", "trigger", "content"):
        if isinstance(c.get(key), str):
            out.append(c[key])
    for tab in c.get("tabs") or []:
        if isinstance(tab, dict) and isinstance(tab.get("child"), str):
            out.append(tab["child"])
    return out


def _repair_modals(components: List[Any]) -> None:
    """Puts every Modal exactly where its trigger would otherwise be.

    A Modal draws its own trigger, so a parent must list the Modal, never the
    trigger. The model makes two mistakes here:
      a) the parent lists the trigger and the Modal floats unreferenced
         -> the payload is dropped ("not reachable from 'root'").
      b) the parent lists BOTH the trigger and the Modal
         -> the trigger is drawn twice ("View details" appears two times).
    """
    comps = [c for c in components if isinstance(c, dict)]
    for modal in comps:
        mid, trigger = modal.get("id"), modal.get("trigger")
        if modal.get("component") != "Modal" or not mid or not isinstance(trigger, str):
            continue
        placed = any(mid in _refs(p) for p in comps if p is not modal)
        for parent in comps:
            if parent is modal:
                continue
            children = parent.get("children")
            if isinstance(children, list) and trigger in children:
                if placed:  # (b) the Modal already draws it - drop the duplicate
                    parent["children"] = [r for r in children if r != trigger]
                    logger.warning("Removed duplicate Modal trigger %s from %s", trigger, parent.get("id"))
                else:  # (a) the Modal takes the trigger's slot
                    parent["children"] = [mid if r == trigger else r for r in children]
                    placed = True
                    logger.warning("Repaired orphan Modal %s (placed where trigger %s was)", mid, trigger)
            elif parent.get("child") == trigger and not placed:
                parent["child"] = mid
                placed = True
                logger.warning("Repaired orphan Modal %s (placed where trigger %s was)", mid, trigger)


def _repair_missing_ids(components: List[Any]) -> None:
    """Restores a dropped component id when it is unambiguous.

    If exactly one component lacks an "id" and exactly one child reference
    points at an undefined id, that id belongs to the orphan component.
    """
    ids = {c.get("id") for c in components if isinstance(c, dict)}
    referenced = [r for c in components if isinstance(c, dict) for r in _refs(c)]
    dangling = [r for r in dict.fromkeys(referenced) if r not in ids]
    missing = [c for c in components if isinstance(c, dict) and not c.get("id")]
    if len(dangling) == 1 and len(missing) == 1:
        logger.warning("Repaired missing component id -> %s", dangling[0])
        missing[0]["id"] = dangling[0]


def normalize_a2ui_messages(
    messages: List[Dict[str, Any]],
    uuid_suffix: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Repairs a model-generated block so it always satisfies the A2UI spec.

    Enforced in code rather than by prompt, because prompt rules are honoured
    differently by different models:

    1. Every message carries ``version``.
    2. ``createSurface`` always carries the correct ``catalogId``.
    3. All messages share one ``surfaceId``, suffixed with a per-turn UUID so
       it is unique across turns without the model having to remember anything.
    4. A ``createSurface`` is synthesized when the model omits one.
    5. ``deleteSurface`` for a surface not created here is dropped; the spec
       requires a prior ``createSurface`` for that id.
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

    # Idempotent: a second pass must not append the suffix twice.
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

        if key == "updateComponents" and isinstance(payload.get("components"), list):
            _repair_missing_ids(payload["components"])
            _repair_modals(payload["components"])

        if key == "deleteSurface" and not has_create:
            logger.warning("Dropping deleteSurface for uncreated surface %s", surface_id)
            continue

        if key == "createSurface":
            if payload.get("catalogId") != BASIC_CATALOG_ID:
                payload["catalogId"] = BASIC_CATALOG_ID  # (2)
            has_create = True

        normalized.append({"version": A2UI_VERSION, key: payload})  # (1)

    # (4) A surface must exist before it can be updated.
    if normalized and not has_create:
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
        from a2ui.inference_formats.direct_json import DirectJsonFormat
        from a2ui.schema import constants

        fmt = DirectJsonFormat(
            constants.VERSION_0_9,
            [get_catalog_config()],
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


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def parse_a2ui_response(
    raw_text: str,
    tool_result: Any = None,
) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """Extracts companion markdown and a guaranteed-valid A2UI message list.

    Args:
        raw_text: The model's raw reply.
        tool_result: The most recent tool return value, used to resolve any
            ``${...}`` expressions the model emitted despite instructions.
    """
    if not raw_text:
        return "", None

    tag_blocks = _TAG_PATTERN.findall(raw_text)
    if not tag_blocks:
        return raw_text.strip(), None

    clean_text = _TAG_PATTERN.sub("", raw_text).strip()
    a2ui_messages: List[Dict[str, Any]] = []

    # One suffix per turn so every block in this reply shares a surface.
    uuid_suffix = uuid.uuid4().hex[:8]

    for index, block in enumerate(tag_blocks, start=1):
        block_str = block.strip()
        if not block_str:
            continue
        try:
            # parsed = json.loads(block_str)
            parsed = _loads_lenient(block_str)
            extracted = extract_v09_messages(parsed)
            extracted = resolve_placeholders(extracted, tool_result)  # L2
            a2ui_messages.extend(normalize_a2ui_messages(extracted, uuid_suffix))  # L1
        except (json.JSONDecodeError, ValueError, TypeError) as err:
            logger.warning(
                "Failed to parse A2UI JSON in block %d: %s | payload=%s",
                index,
                err,
                # block_str[:2000],
                block_str,
            )

    return clean_text, a2ui_messages if a2ui_messages else None


def a2ui_callback(callback_context: Any, llm_response: Any) -> Any:
    """Processes LLM responses to ensure clean text and A2UI data parts."""
    del callback_context
    return llm_response


__all__ = [
    "extract_v09_messages",
    "resolve_placeholders",
    "normalize_a2ui_messages",
    "is_renderable",
    "parse_a2ui_response",
    "a2ui_callback",
]
