"""Server-side store for large UI payloads such as Vega-Lite specs.

Why this exists
---------------
An LLM cannot (and should not) copy thousands of numbers into its reply. Tools
therefore save big payloads here and give the model only a short data-model
path such as "/plots/p1a2b3c4d5". The model binds a component to that path,
e.g. {"component": "VegaChart", "spec": {"path": "/plots/p1a2b3c4d5"}}, and
after the model replies ``attach_plot_data`` writes the stored payload into the
surface's data model with an ``updateDataModel`` message.
"""

import logging
import uuid
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PLOT_PREFIX = "/plots/"
_MAX_PLOTS = 50  # keep memory bounded; old plots are already on the client

_PLOTS: "OrderedDict[str, Any]" = OrderedDict()


def save_plot(payload: Any) -> str:
    """Stores a payload and returns the data-model path the UI should bind to."""
    plot_id = "p" + uuid.uuid4().hex[:10]
    _PLOTS[plot_id] = payload
    while len(_PLOTS) > _MAX_PLOTS:
        _PLOTS.popitem(last=False)
    return PLOT_PREFIX + plot_id


def get_plot(path: Any) -> Optional[Any]:
    """Returns the payload stored for "/plots/<id>", or None."""
    if not isinstance(path, str) or not path.startswith(PLOT_PREFIX):
        return None
    plot_id = path[len(PLOT_PREFIX):].split("/", 1)[0]
    return _PLOTS.get(plot_id)


def _collect_plot_bindings(node: Any, found: List[str]) -> List[str]:
    """Finds every {"path": "/plots/..."} data binding inside a component tree."""
    if isinstance(node, dict):
        path = node.get("path")
        if len(node) == 1 and isinstance(path, str) and path.startswith(PLOT_PREFIX):
            found.append(path)
        for value in node.values():
            _collect_plot_bindings(value, found)
    elif isinstance(node, list):
        for value in node:
            _collect_plot_bindings(value, found)
    return found


def _is_plot_write(message: Dict[str, Any]) -> bool:
    """True for an updateDataModel the model wrote to /plots/ (never trusted)."""
    payload = message.get("updateDataModel")
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("path"), str)
        and payload["path"].startswith(PLOT_PREFIX)
    )


def _data_message(surface_id: str, path: str, value: Any) -> Dict[str, Any]:
    return {
        "version": "v0.9",
        "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value},
    }


def _repair_vega_specs(messages: List[Dict[str, Any]], fallback_path: Optional[str]) -> None:
    """Points VegaChart.spec at the latest plot when the model got the binding wrong.

    The catalog only accepts {"path": ...} for VegaChart.spec. If the model inlined
    a spec, left it out, or bound it to a path that holds no stored plot, the
    binding is rewritten to the plot_path of the latest tool result (in place).
    """
    if not fallback_path or get_plot(fallback_path) is None:
        return
    for message in messages:
        update = message.get("updateComponents")
        if not isinstance(update, dict):
            continue
        for component in update.get("components") or []:
            if not isinstance(component, dict) or component.get("component") != "VegaChart":
                continue
            spec = component.get("spec")
            path = spec.get("path") if isinstance(spec, dict) else None
            if not (isinstance(spec, dict) and len(spec) == 1 and get_plot(path) is not None):
                logger.warning("Rebinding VegaChart %s to %s", component.get("id"), fallback_path)
                component["spec"] = {"path": fallback_path}


def attach_plot_data(
    messages: Optional[List[Dict[str, Any]]],
    tool_result: Any = None,
) -> Optional[List[Dict[str, Any]]]:
    """Injects stored plot payloads into the data model of the surfaces using them.

    Args:
        messages: Normalized A2UI messages produced from the model reply.
        tool_result: Latest tool result. If the model mistypes a plot id, the
            ``plot_path`` from this result is used as a fallback.
    """
    if not messages:
        return messages

    fallback_path = tool_result.get("plot_path") if isinstance(tool_result, dict) else None
    kept = [m for m in messages if not _is_plot_write(m)]
    _repair_vega_specs(kept, fallback_path)

    injections: List[Tuple[str, str, Any]] = []
    for message in kept:
        update = message.get("updateComponents")
        if not isinstance(update, dict):
            continue
        surface_id = update.get("surfaceId")
        paths = _collect_plot_bindings(update.get("components", []), [])
        for path in dict.fromkeys(paths):  # de-duplicate, keep order
            payload = get_plot(path)
            if payload is None:
                logger.warning("No stored plot for %s; the chart will stay empty", path)
                continue
            injections.append((surface_id, path, payload))

    if not injections:
        return kept

    # Put each data update right after its surface's createSurface message so
    # the data is present before the components that read it.
    result: List[Dict[str, Any]] = []
    pending = list(injections)
    for message in kept:
        result.append(message)
        create = message.get("createSurface")
        if isinstance(create, dict):
            for item in [i for i in pending if i[0] == create.get("surfaceId")]:
                result.append(_data_message(*item))
                pending.remove(item)
    # Surfaces created in an earlier turn: send their data first.
    return [_data_message(*item) for item in pending] + result
