"""Well-log (LAS) tools that render as interactive Vega-Lite charts in A2UI.

Flow
----
1. The model calls ``plot_well_log`` (optionally ``list_well_logs`` first).
2. The tool reads the LAS file with ``lasio`` and builds a complete Vega-Lite
   spec: depth tracks, curves, scales, fills, hover tooltips and depth zoom.
   The spec is parked in ``plot_store``; only a short summary plus
   ``plot_path`` (e.g. "/plots/p1a2b3c4d5") goes back to the model.
3. The model renders a ``VegaChart`` component with ``"spec": {"path": plot_path}``.
4. ``server.py`` calls ``plot_store.attach_plot_data`` which writes the spec
   into the surface's data model, so the samples never pass through the LLM.

LAS files are read from $WELL_LOG_DIR (default: manager_dashboard/data/well_logs).
"""

import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from . import plot_store

_DEFAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "well_logs")
_MAX_POINTS = 2000   # depth samples sent to the browser per plot
_PLOT_HEIGHT = 560   # px
_PLOT_WIDTH = 470    # px shared by all tracks (fits the 600px chat card)

_DEPTH = "DEPTH"              # depth field in the plot rows
_NEXT = "__next"              # depth of the following sample (fill rectangles)
_NPHI_ON_RHOB = "__nphi_rho"  # neutron re-scaled onto the density axis

# Mnemonic aliases -> curve family.
_FAMILY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "gr": ("GR", "SGR", "CGR", "GRC", "GRD", "GAM", "GAMMA", "HSGR", "ECGR", "GR_EDTC"),
    "sp": ("SP", "SSP", "SPBR"),
    "cal": ("CALI", "CAL", "DCAL", "HCAL", "C1", "C2", "CALS", "CALX", "CALY"),
    "res_deep": ("RILD", "ILD", "LLD", "RLLD", "RD", "RDEP", "RT", "AT90", "AHT90", "RLA5", "HDRS", "M2R9"),
    "res_med": ("RILM", "ILM", "RM", "RMED", "AT30", "AHT30", "RLA3", "HMRS", "M2R3"),
    "res_shallow": ("RLL3", "LL3", "SFL", "SFLU", "SFLA", "LLS", "RS", "RSHAL", "MSFL", "RXO",
                    "RLA1", "AT10", "AHT10"),
    "nphi": ("NPHI", "CNPOR", "TNPH", "NPOR", "CNC", "CN", "CNCF", "NPHI_LS", "NPLS", "PHIN", "NEU"),
    "rhob": ("RHOB", "RHOZ", "DEN", "ZDEN", "DENS", "RHOM"),
    "dt": ("DT", "DTC", "DTCO", "AC", "DT4P", "SONIC"),
    "pe": ("PE", "PEF", "PEFZ"),
}

# Display style per family. "group": curves in the same group share one x axis.
_STYLE: Dict[str, Dict[str, Any]] = {
    "gr": {"color": "#2e7d32", "domain": (0.0, 150.0)},
    "sp": {"color": "#1565c0"},
    "cal": {"color": "#6d4c41", "domain": (6.0, 16.0), "dash": [4, 2]},
    "res_deep": {"color": "#c62828", "log": True, "group": "res"},
    "res_med": {"color": "#1565c0", "log": True, "group": "res", "dash": [6, 3]},
    "res_shallow": {"color": "#2e7d32", "log": True, "group": "res", "dash": [2, 2]},
    "res_other": {"color": "#6a1b9a", "log": True, "group": "res", "dash": [1, 3]},
    "nphi": {"color": "#1565c0", "reverse": True, "dash": [6, 3]},
    "rhob": {"color": "#b71c1c", "domain": (1.95, 2.95)},
    "dt": {"color": "#6a1b9a", "domain": (40.0, 140.0), "reverse": True},
    "pe": {"color": "#ef6c00", "domain": (0.0, 10.0)},
}
_PALETTE = ("#00897b", "#5e35b1", "#f9a825", "#6d4c41", "#d81b60", "#546e7a")
_SAND, _SHALE = "#fff59d", "#a5d6a7"        # gamma-ray lithology fill
_CROSSOVER, _SEPARATION = "#ef9a9a", "#bbdefb"  # neutron-density fill

_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}


# --------------------------------------------------------------------------
# LAS loading
# --------------------------------------------------------------------------


def _log_dir() -> str:
    return os.path.abspath(os.path.expanduser(os.getenv("WELL_LOG_DIR", _DEFAULT_DIR)))


def _las_files() -> List[str]:
    folder = _log_dir()
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(".las"))


def _available() -> str:
    return ", ".join(_las_files()) or f"none (put .las files in {_log_dir()})"


def _resolve_file(file_name: Any) -> str:
    files = _las_files()
    name = os.path.basename(str(file_name or "").strip())
    if not name:
        if len(files) == 1:
            return os.path.join(_log_dir(), files[0])
        raise ValueError(f"Please choose a LAS file. Available: {_available()}")
    wanted = name.lower() if name.lower().endswith(".las") else name.lower() + ".las"
    for candidate in files:
        if candidate.lower() == wanted:
            return os.path.join(_log_dir(), candidate)
    raise ValueError(f"LAS file '{name}' not found. Available: {_available()}")


def _to_float(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _header(las: Any, key: str) -> str:
    try:
        return str(las.well[key].value).strip()
    except Exception:  # missing header item
        return ""


def _field_key(mnemonic: str, used: set) -> str:
    """Vega-safe field name (no dots/brackets), unique within the file."""
    base = re.sub(r"[^A-Za-z0-9_]", "_", str(mnemonic or "CURVE")) or "CURVE"
    key, n = base, 2
    while key in used:
        key, n = f"{base}_{n}", n + 1
    used.add(key)
    return key


def _load(path: str) -> Dict[str, Any]:
    """Reads a LAS file (cached by modification time)."""
    mtime = os.path.getmtime(path)
    cached = _CACHE.get(path)
    if cached and cached[0] == mtime:
        return cached[1]

    import lasio  # lazy import so the rest of the agent works without it

    las = lasio.read(path)  # NULL values such as -999.25 become NaN
    used = {_DEPTH, _NEXT, _NPHI_ON_RHOB}
    curves = []
    for item in las.curves[1:]:
        curves.append({
            "key": _field_key(item.mnemonic, used),
            "mnemonic": str(item.mnemonic),
            "unit": str(item.unit or "").strip(),
            "descr": str(item.descr or "").strip(),
            "values": [_to_float(v) for v in item.data],
        })
    info = {
        "file": os.path.basename(path),
        "well": _header(las, "WELL"),
        "company": _header(las, "COMP"),
        "field": _header(las, "FLD"),
        "depth_unit": str(las.curves[0].unit or "").strip() or "FT",
        "depth": [_to_float(v) for v in las.index],
        "curves": curves,
    }
    _CACHE[path] = (mtime, info)
    return info


# --------------------------------------------------------------------------
# Curve selection and scales
# --------------------------------------------------------------------------


def _family(curve: Dict[str, Any]) -> Optional[str]:
    name = curve["mnemonic"].upper().split(":")[0]
    for family, aliases in _FAMILY_ALIASES.items():
        if name in aliases:
            return family
    if "OHM" in curve["unit"].upper():
        return "res_other"
    return None


def _has_data(curve: Dict[str, Any]) -> bool:
    return any(v is not None for v in curve["values"])


def _default_tracks(curves: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Classic triple combo: GR/SP | resistivity | neutron/density."""
    found: Dict[str, Dict[str, Any]] = {}
    for curve in curves:
        family = _family(curve)
        if family and family not in found and _has_data(curve):
            found[family] = curve
    track1 = [found[f] for f in ("gr", "sp") if f in found]
    if len(track1) < 2 and "cal" in found:
        track1.append(found["cal"])
    tracks = [
        track1,
        [found[f] for f in ("res_deep", "res_med", "res_shallow") if f in found],
        [found[f] for f in ("nphi", "rhob") if f in found],
    ]
    tracks = [t for t in tracks if t]
    if not tracks:  # unfamiliar mnemonics: first three curves that have data
        tracks = [[c] for c in curves if _has_data(c)][:3]
    return tracks


def _parse_tracks(text: str, curves: List[Dict[str, Any]]) -> Tuple[List[List[Dict[str, Any]]], List[str]]:
    """Parses "GR,SP|RILD,RILM,RLL3|CNPOR,RHOB" into tracks of curves."""
    lookup: Dict[str, Dict[str, Any]] = {}
    for curve in curves:
        lookup.setdefault(curve["mnemonic"].upper(), curve)
        lookup.setdefault(curve["key"].upper(), curve)
    text = re.sub(r"\]\s*,\s*\[", "|", text)  # tolerate [["GR","SP"],["RILD"]]
    tracks, unknown = [], []
    for chunk in re.split(r"[|;\n]+", text):
        track: List[Dict[str, Any]] = []
        for raw in chunk.split(","):
            name = raw.strip(" []'\"")
            if not name:
                continue
            curve = lookup.get(name.upper())
            if curve is None:
                unknown.append(name)
            elif curve not in track:
                track.append(curve)
        if track:
            tracks.append(track)
    return tracks, unknown


def _number(value: Any) -> float:
    """Lenient float parsing ("3,500 ft" -> 3500.0); 0.0 when absent."""
    if isinstance(value, (list, tuple)):
        value = value[0] if value else 0
    match = re.search(r"-?\d+(?:\.\d+)?", str(value if value is not None else "").replace(",", ""))
    return float(match.group()) if match else 0.0


def _pct(sorted_values: List[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = int(round(q * (len(sorted_values) - 1)))
    return sorted_values[min(len(sorted_values) - 1, max(0, index))]


def _nice_bounds(lo: float, hi: float) -> List[float]:
    span = hi - lo
    if span <= 0:
        return [lo - 1.0, hi + 1.0]
    step = 10 ** math.floor(math.log10(span))
    if span / step < 3:
        step /= 2
    return [math.floor(lo / step) * step, math.ceil(hi / step) * step]


def _sig(value: Optional[float], digits: int = 5) -> Optional[float]:
    return None if value is None else float(f"{value:.{digits}g}")


def _is_percent(curve: Dict[str, Any], values: List[float]) -> bool:
    unit = curve["unit"].upper().replace(".", "")
    return unit in ("PU", "%", "PERCENT", "PCT") or (bool(values) and _pct(values, 0.9) > 1.5)


def _domain(family: Optional[str], group_curves: List[Dict[str, Any]], values: List[float], log: bool) -> List[float]:
    """x-axis domain for a group of curves (values are sorted, window only)."""
    style = _STYLE.get(family or "", {})
    if log:
        positive = [v for v in values if v > 0]
        if not positive:
            return [0.2, 2000.0]
        lo = 10 ** math.floor(math.log10(max(_pct(positive, 0.01), 0.01)))
        hi = 10 ** math.ceil(math.log10(max(_pct(positive, 0.99), lo * 10)))
        return [lo, min(hi, 100000.0)]
    if family == "nphi":
        return [-15.0, 45.0] if _is_percent(group_curves[0], values) else [-0.15, 0.45]
    if "domain" in style:
        lo, hi = style["domain"]
        if family != "rhob" and values:  # widen a standard scale if data overflows it
            if _pct(values, 0.99) > hi:
                hi = _nice_bounds(lo, _pct(values, 0.99))[1]
            if _pct(values, 0.01) < lo:
                lo = _nice_bounds(_pct(values, 0.01), hi)[0]
        return [lo, hi]
    if not values:
        return [0.0, 1.0]
    lo, hi = _pct(values, 0.01), _pct(values, 0.99)
    pad = (hi - lo) * 0.05 or 1.0
    return _nice_bounds(lo - pad, hi + pad)


def _groups(track: List[Dict[str, Any]], window_values: Dict[str, List[float]]) -> List[Dict[str, Any]]:
    """Splits a track into scale groups (curves sharing one x axis)."""
    groups: Dict[str, Dict[str, Any]] = {}
    for curve in track:
        family = _family(curve)
        style = _STYLE.get(family or "", {})
        gid = style.get("group") or family or curve["key"]
        group = groups.setdefault(gid, {
            "family": family, "log": bool(style.get("log")),
            "reverse": bool(style.get("reverse")), "curves": [],
        })
        group["curves"].append(curve)
    for index, group in enumerate(groups.values()):
        values = sorted(v for c in group["curves"] for v in window_values[c["key"]])
        group["domain"] = _domain(group["family"], group["curves"], values, group["log"])
        for n, curve in enumerate(group["curves"]):
            style = _STYLE.get(_family(curve) or "", {})
            curve["color"] = style.get("color") or _PALETTE[(index + n) % len(_PALETTE)]
            curve["dash"] = style.get("dash")
    return list(groups.values())


# --------------------------------------------------------------------------
# Vega-Lite spec
# --------------------------------------------------------------------------


def _q(key: str) -> str:
    """datum accessor for Vega expressions."""
    return f"datum[{json.dumps(key)}]"


def _unit(unit: str) -> str:
    return f" ({unit})" if unit else ""


def _x_axis(group: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    if index > 1:  # only two axes fit (bottom + top); extra groups rely on the tooltip
        return None
    curves = group["curves"]
    if group["family"] and group["family"].startswith("res"):
        title = "Resistivity" + _unit(curves[0]["unit"])
    else:
        title = " / ".join(c["mnemonic"] for c in curves) + _unit(curves[0]["unit"])
    axis: Dict[str, Any] = {
        "orient": "bottom" if index == 0 else "top",
        "title": title,
        "titleColor": curves[0]["color"] if len(curves) == 1 else "#3c4043",
        "grid": index == 0,
        "labelFlush": True,
        "labelOverlap": True,
        "tickCount": 4,
    }
    if group["log"]:
        lo, hi = group["domain"]
        axis["values"] = [10.0 ** k for k in range(round(math.log10(lo)), round(math.log10(hi)) + 1)]
        axis["format"] = "~g"
    return axis


def _x_scale(group: Dict[str, Any]) -> Dict[str, Any]:
    scale: Dict[str, Any] = {"domain": group["domain"], "nice": False}
    if group["log"]:
        scale["type"] = "log"
    else:
        scale["zero"] = False
    if group["reverse"]:
        scale["reverse"] = True
    return scale


def _curve_layers(group: Dict[str, Any], axis: Optional[Dict[str, Any]], y: Dict[str, Any],
                  width: int) -> List[Dict[str, Any]]:
    scale, curves = _x_scale(group), group["curves"]
    order = {"field": _DEPTH, "type": "quantitative"}
    if len(curves) == 1:
        curve = curves[0]
        mark: Dict[str, Any] = {"type": "line", "clip": True, "strokeWidth": 1.3, "color": curve["color"]}
        if curve["dash"]:
            mark["strokeDash"] = curve["dash"]
        return [{
            "mark": mark,
            "encoding": {
                "x": {"field": curve["key"], "type": "quantitative", "scale": scale, "axis": axis},
                "y": y,
                "order": order,
            },
        }]
    keys = [c["key"] for c in curves]
    # ~50px per legend entry; wrap so the legend never gets wider than its track.
    legend = {"orient": "top", "title": None, "direction": "horizontal", "symbolType": "stroke",
              "columns": max(1, min(len(curves), width // 50)), "columnPadding": 6,
              "symbolSize": 120, "labelLimit": 44, "rowPadding": 2}
    return [{
        "transform": [{"fold": keys, "as": ["__curve", "__value"]}],
        "mark": {"type": "line", "clip": True, "strokeWidth": 1.3},
        "encoding": {
            "x": {"field": "__value", "type": "quantitative", "scale": scale, "axis": axis},
            "y": y,
            "order": order,
            "color": {"field": "__curve", "type": "nominal", "legend": legend,
                      "scale": {"domain": keys, "range": [c["color"] for c in curves]}},
            "strokeDash": {"field": "__curve", "type": "nominal", "legend": legend,
                           "scale": {"domain": keys, "range": [c["dash"] or [1, 0] for c in curves]}},
        },
    }]


def _gr_fill(group: Dict[str, Any], axis: Optional[Dict[str, Any]], y: Dict[str, Any],
             cutoff: float) -> Dict[str, Any]:
    key = group["curves"][0]["key"]
    return {
        "mark": {"type": "rect", "clip": True, "strokeWidth": 0, "opacity": 0.9},
        "encoding": {
            # Same axis as the curve: layers that share a scale merge their axes.
            "x": {"field": key, "type": "quantitative", "scale": _x_scale(group), "axis": axis},
            "x2": {"value": 0},
            "y": y,
            "y2": {"field": _NEXT},
            "color": {"condition": {"test": f"{_q(key)} < {cutoff}", "value": _SAND}, "value": _SHALE},
        },
    }


def _crossover_fill(rhob_group: Dict[str, Any], axis: Optional[Dict[str, Any]],
                    y: Dict[str, Any]) -> Dict[str, Any]:
    key = rhob_group["curves"][0]["key"]
    return {
        "transform": [{"filter": f"isValid({_q(key)}) && isValid({_q(_NPHI_ON_RHOB)})"}],
        "mark": {"type": "rect", "clip": True, "strokeWidth": 0, "opacity": 0.8},
        "encoding": {
            "x": {"field": key, "type": "quantitative", "scale": _x_scale(rhob_group), "axis": axis},
            "x2": {"field": _NPHI_ON_RHOB},
            "y": y,
            "y2": {"field": _NEXT},
            "color": {"condition": {"test": f"{_q(key)} < {_q(_NPHI_ON_RHOB)}", "value": _CROSSOVER},
                      "value": _SEPARATION},
        },
    }


def _hover_layer(curves: List[Dict[str, Any]], y: Dict[str, Any], depth_unit: str) -> Dict[str, Any]:
    """Invisible nearest-depth selector: crosshair + tooltip with every curve."""
    calcs = [{"calculate": f"format({_q(_DEPTH)}, '.1f')", "as": "__tt_depth"}]
    tooltip = [{"field": "__tt_depth", "type": "nominal", "title": f"Depth{_unit(depth_unit)}"}]
    for curve in curves:
        field = f"__tt_{curve['key']}"
        calcs.append({"calculate": f"isValid({_q(curve['key'])}) ? format({_q(curve['key'])}, '.4~r') : '-'",
                      "as": field})
        tooltip.append({"field": field, "type": "nominal", "title": curve["mnemonic"] + _unit(curve["unit"])})
    return {
        "transform": calcs,
        "mark": {"type": "rule", "color": "#202124", "strokeWidth": 1, "strokeDash": [3, 2]},
        "encoding": {
            "y": y,
            "opacity": {"condition": {"param": "hover", "empty": False, "value": 0.8}, "value": 0},
            "tooltip": tooltip,
        },
        "params": [
            {"name": "hover", "select": {"type": "point", "fields": [_DEPTH], "nearest": True,
                                         "on": "pointerover", "clear": "pointerout"}},
            {"name": "depth_zoom", "select": {"type": "interval", "encodings": ["y"]}, "bind": "scales"},
        ],
    }


def _build_spec(tracks_groups, curves, top, base, depth_unit, rows, cutoff) -> Dict[str, Any]:
    n = len(tracks_groups)
    width = max(90, min(170, int((_PLOT_WIDTH - 50 - 6 * (n - 1)) / n)))
    views = []
    for t_index, groups in enumerate(tracks_groups):
        y_axis: Dict[str, Any] = (
            {"title": f"Depth{_unit(depth_unit)}", "grid": True, "tickCount": 10, "labelFlush": True,
             "format": "~r"}
            if t_index == 0 else
            # Grid lines only. Vega-Lite reserves 30px for every y axis unless told otherwise.
            {"title": None, "labels": False, "ticks": False, "domain": False, "grid": True, "tickCount": 10,
             "minExtent": 0, "maxExtent": 0}
        )
        y = {"field": _DEPTH, "type": "quantitative", "axis": y_axis,
             "scale": {"domain": [top, base], "reverse": True, "nice": False, "zero": False}}
        families = [g["family"] for g in groups]
        group_layers = []
        for g_index, group in enumerate(groups):
            axis = _x_axis(group, g_index)
            layers = []
            if group["family"] == "gr" and cutoff is not None:
                layers.append(_gr_fill(group, axis, y, cutoff))
            if group["family"] == "rhob" and "nphi" in families:
                layers.append(_crossover_fill(group, axis, y))
            layers += _curve_layers(group, axis, y, width)
            group_layers.append({"layer": layers} if len(layers) > 1 else layers[0])
        views.append({
            "width": width,
            "height": _PLOT_HEIGHT,
            "layer": group_layers + [_hover_layer(curves, y, depth_unit)],
            "resolve": {"scale": {"x": "independent"}, "axis": {"x": "independent"}},
        })
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": {"values": rows},
        "hconcat": views,
        "spacing": 6,
        # Shared depth scale (zoom/pan moves every track); legends stay with their track.
        "resolve": {
            "scale": {"y": "shared", "color": "independent", "strokeDash": "independent"},
            "legend": {"color": "independent", "strokeDash": "independent"},
        },
        "config": {
            "font": "Roboto, Arial, sans-serif",
            "view": {"stroke": "#9aa0a6"},
            "style": {"cell": {"strokeForeground": True}},  # track border above the grid lines
            "axis": {"labelFontSize": 10, "titleFontSize": 11, "titleFontWeight": "normal",
                     "labelColor": "#3c4043", "gridColor": "#e8eaed",
                     "domainColor": "#9aa0a6", "tickColor": "#9aa0a6"},
            "legend": {"labelFontSize": 10, "symbolStrokeWidth": 2},
        },
    }


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------


def list_well_logs() -> dict:
    """
    Lists the LAS well-log files that can be plotted, with well name, depth range
    and available curves (mnemonic, unit, description).

    Returns:
        A dictionary with the log folder and one entry per LAS file.
    """
    files = []
    for name in _las_files():
        try:
            info = _load(os.path.join(_log_dir(), name))
            depth = [d for d in info["depth"] if d is not None]
            files.append({
                "file": name,
                "well": info["well"],
                "company": info["company"],
                "field": info["field"],
                "depth_range": [min(depth), max(depth)] if depth else None,
                "depth_unit": info["depth_unit"],
                "curves": [f"{c['mnemonic']}{_unit(c['unit'])}: {c['descr']}" for c in info["curves"]],
            })
        except Exception as err:  # unreadable file: report, keep going
            files.append({"file": name, "error": str(err)})
    return {"status": "success", "folder": _log_dir(), "files": files}


def plot_well_log(file_name: str, top_depth: float, base_depth: float, tracks: str) -> dict:
    """
    Builds an interactive well-log plot (Vega-Lite) from a LAS file.

    Args:
        file_name: LAS file name, e.g. "1028645889.las". Use "" when only one file exists.
        top_depth: Top of the depth interval. Use 0 for the top of the logged data.
        base_depth: Base of the depth interval. Use 0 for the bottom of the logged data.
        tracks: Curve mnemonics per track: commas inside a track, "|" between tracks,
            e.g. "GR,SP|RILD,RILM,RLL3|CNPOR,RHOB". Use "" for the default triple combo.

    Returns:
        A short summary plus "plot_path". Render a VegaChart whose spec is
        {"path": plot_path}; the server attaches the plot data automatically.
    """
    try:
        info = _load(_resolve_file(file_name))
        curves_all = info["curves"]
        ignored: List[str] = []
        if str(tracks or "").strip():
            layout, ignored = _parse_tracks(str(tracks), curves_all)
            if not layout:
                raise ValueError("None of the requested curves exist. Available curves: "
                                 + ", ".join(c["mnemonic"] for c in curves_all))
        else:
            layout = _default_tracks(curves_all)
        if not layout:
            raise ValueError("This LAS file has no curves with data.")
        layout = [[dict(c) for c in t] for t in layout]  # per-plot copies (styles are set below)
        curves = list({c["key"]: c for t in layout for c in t}.values())

        # Depth window: explicit request, else the extent of the plotted data.
        depth = info["depth"]
        with_data = [i for i, d in enumerate(depth)
                     if d is not None and any(c["values"][i] is not None for c in curves)]
        if not with_data:
            raise ValueError("The selected curves contain only NULL values.")
        lo = min(depth[i] for i in with_data)
        hi = max(depth[i] for i in with_data)
        top = _number(top_depth) or lo
        base = _number(base_depth) or hi
        if top > base:
            top, base = base, top
        top, base = max(top, min(d for d in depth if d is not None)), min(base, max(d for d in depth if d is not None))
        window = sorted((i for i, d in enumerate(depth) if d is not None and top <= d <= base),
                        key=lambda i: depth[i])
        if len(window) < 2:
            raise ValueError(f"No samples between {top} and {base} {info['depth_unit']}.")

        window_values = {c["key"]: [c["values"][i] for i in window if c["values"][i] is not None]
                         for c in curves}
        tracks_groups = [_groups(t, window_values) for t in layout]

        # Gamma-ray sand/shale cutoff: midpoint of the 5th-95th percentile.
        cutoff = None
        gr = next((c for c in curves if _family(c) == "gr"), None)
        if gr and window_values[gr["key"]]:
            values = sorted(window_values[gr["key"]])
            cutoff = float(min(120, max(30, 5 * round((_pct(values, 0.05) + _pct(values, 0.95)) / 10))))

        # Neutron on the density scale, for the crossover fill.
        nphi_rhob = None
        for groups in tracks_groups:
            by_family = {g["family"]: g for g in groups}
            if "nphi" in by_family and "rhob" in by_family:
                n_lo, n_hi = by_family["nphi"]["domain"]
                r_lo, r_hi = by_family["rhob"]["domain"]
                nphi_rhob = (by_family["nphi"]["curves"][0], n_lo, n_hi, r_lo, r_hi)
                break

        # Decimate to at most _MAX_POINTS samples.
        stride = max(1, math.ceil(len(window) / _MAX_POINTS))
        picked = window[::stride]
        rows = []
        for k, i in enumerate(picked):
            nxt = depth[picked[k + 1]] if k + 1 < len(picked) else depth[i] + (depth[i] - depth[picked[k - 1]])
            row: Dict[str, Any] = {_DEPTH: round(depth[i], 3), _NEXT: round(nxt, 3)}
            for curve in curves:
                row[curve["key"]] = _sig(curve["values"][i])
            if nphi_rhob:
                neutron, n_lo, n_hi, r_lo, r_hi = nphi_rhob
                value = neutron["values"][i]
                row[_NPHI_ON_RHOB] = None if value is None else _sig(
                    r_lo + (n_hi - value) / (n_hi - n_lo) * (r_hi - r_lo))
            rows.append(row)

        spec = _build_spec(tracks_groups, curves, top, base, info["depth_unit"], rows, cutoff)
        summary = {}
        for curve in curves:
            values = window_values[curve["key"]]
            summary[curve["mnemonic"]] = {
                "unit": curve["unit"],
                "description": curve["descr"],
                "min": _sig(min(values), 4) if values else None,
                "max": _sig(max(values), 4) if values else None,
                "mean": _sig(sum(values) / len(values), 4) if values else None,
            }
        result = {
            "status": "success",
            "plot_path": plot_store.save_plot(spec),
            "file": info["file"],
            "well": info["well"],
            "company": info["company"],
            "field": info["field"],
            "depth_unit": info["depth_unit"],
            "top_depth": top,
            "base_depth": base,
            "tracks": [" + ".join(c["mnemonic"] for c in t) for t in layout],
            "samples_plotted": len(rows),
            "curve_summary": summary,
            "available_curves": [c["mnemonic"] for c in curves_all],
        }
        if cutoff is not None:
            result["gr_sand_shale_cutoff"] = cutoff
        if ignored:
            result["ignored_curves"] = ignored
        return result
    except Exception as err:
        return {"status": "error", "error": str(err), "available_files": _las_files()}
