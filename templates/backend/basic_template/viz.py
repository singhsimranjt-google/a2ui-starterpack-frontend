"""Generic Vega-Lite builders for agent tools: interactive charts and maps.

Tools call these helpers with plain row dicts. Each helper builds a complete
Vega-Lite spec, stores it with ``plot_store`` and returns the short data-model
path ("/plots/<id>") that a ``VegaChart`` component binds to:

    {"component": "VegaChart", "id": "trend_chart", "spec": {"path": plot_path}}

The spec never passes through the LLM, so the number of points does not matter.
Both helpers raise ``ValueError`` with a readable message on bad input; tools
should catch it and return {"status": "error", "error": str(exc)}.
"""

import math
import os
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode
from . import plot_store

SCHEMA = "https://vega.github.io/schema/vega-lite/v6.json"
PALETTE = ["#1a73e8", "#34a853", "#fbbc04", "#ea4335", "#9334e6", "#00acc1", "#ff6d00", "#5f6368"]
WORLD_TOPOJSON = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json"
CHART_TYPES = ("bar", "line", "area", "point")
X_TYPES = ("nominal", "ordinal", "quantitative", "temporal")

_CONFIG: Dict[str, Any] = {
    "font": "Roboto, Arial, sans-serif",
    "view": {"stroke": None},
    "axis": {
        "labelColor": "#3c4043", "titleColor": "#3c4043", "gridColor": "#eef0f2",
        "domainColor": "#dadce0", "tickColor": "#dadce0",
    },
    "legend": {"labelColor": "#3c4043", "titleColor": "#3c4043", "orient": "top", "labelLimit": 160},
    "range": {"category": PALETTE},
}


def _field(name: str) -> str:
    """Escapes '.', '[' and ']', which Vega-Lite would read as nested access."""
    out = str(name).replace("\\", "\\\\")
    for ch in ".[]":
        out = out.replace(ch, "\\" + ch)
    return out


def _to_number(value: Any) -> Optional[float]:
    """Returns a finite float for numbers and numeric strings ("1,200"), else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _title(text: str) -> Dict[str, Any]:
    return {"text": text, "anchor": "start", "fontSize": 14, "fontWeight": 500}


def save_chart(
    rows: Sequence[Dict[str, Any]],
    chart_type: str,
    x: str,
    y: str,
    color: str = "",
    title: str = "",
    x_type: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 260,
) -> str:
    """Builds an interactive bar / line / area / point chart and returns its plot_path.

    Interactions: hover tooltips and highlight; clicking a legend entry isolates
    that series (when ``color`` is set); scroll-zoom and drag-pan when the x axis
    is quantitative or temporal.

    Args:
        rows: Row dicts, e.g. [{"quarter": "Q1", "name": "Alice", "kpi": 90}, ...].
        chart_type: "bar", "line", "area" or "point".
        x: Row key for the x axis.
        y: Numeric row key for the y axis (numeric strings are converted).
        color: Optional row key that splits the data into coloured series.
        title: Optional chart title (usually the card shows the title instead).
        x_type: "nominal", "ordinal", "quantitative" or "temporal". Defaults to
            "nominal" for bar charts and "ordinal" otherwise.
        x_title / y_title: Optional axis titles (default: the field names).
        height: Chart height in pixels. Width always fills the card.
    """
    chart_type = (chart_type or "").strip().lower()
    if chart_type not in CHART_TYPES:
        raise ValueError(f"chart_type must be one of {', '.join(CHART_TYPES)}.")
    data = [dict(r, **{y: _to_number(r.get(y))}) for r in rows or [] if isinstance(r, dict)]
    if not data:
        raise ValueError("There are no rows to plot.")
    missing = [key for key in (x, y, color) if key and key not in data[0]]
    if missing:
        raise ValueError(f"Unknown field(s) {missing}. Available: {sorted(data[0])}.")

    xt = x_type if x_type in X_TYPES else ("nominal" if chart_type == "bar" else "ordinal")
    continuous = xt in ("quantitative", "temporal")
    x_enc: Dict[str, Any] = {"field": _field(x), "type": xt, "title": x_title or x}
    if not continuous:
        x_enc["sort"] = None  # keep the row order
        x_enc["axis"] = {"labelAngle": -35 if len(data) > 6 else 0, "labelLimit": 120}
    y_enc = {"field": _field(y), "type": "quantitative", "title": y_title or y}
    color_enc: Dict[str, Any] = (
        {"field": _field(color), "type": "nominal", "title": color} if color else {"value": PALETTE[0]}
    )
    tooltip: List[Dict[str, Any]] = [
        {"field": _field(x), "type": xt, "title": x_title or x},
        {"field": _field(y), "type": "quantitative", "title": y_title or y, "format": ","},
    ]
    if color and color != x:
        tooltip.append({"field": _field(color), "type": "nominal", "title": color})

    params: List[Dict[str, Any]] = [{
        "name": "hover",
        "select": {"type": "point", "on": "pointerover", "clear": "pointerout", "nearest": chart_type != "bar"},
    }]
    if color:
        params.append({"name": "pick", "select": {"type": "point", "fields": [_field(color)]}, "bind": "legend"})
    if continuous:
        params.append({"name": "zoom", "select": "interval", "bind": "scales"})

    spec: Dict[str, Any] = {
        "$schema": SCHEMA, "data": {"values": data}, "width": "container", "height": height, "config": _CONFIG,
    }
    if title:
        spec["title"] = _title(title)

    if chart_type == "bar":
        spec["params"] = params
        spec["mark"] = {"type": "bar", "cornerRadiusEnd": 3, "cursor": "pointer"}
        spec["encoding"] = {
            "x": x_enc, "y": y_enc, "color": color_enc, "tooltip": tooltip,
            "opacity": {"condition": {"param": "pick" if color else "hover", "value": 1}, "value": 0.3},
        }
        return plot_store.save_plot(spec)

    # line | area | point: optional series layer + a points layer that carries the interactions.
    series: Dict[str, Any] = {"x": x_enc, "y": y_enc, "color": color_enc}
    if color:
        series["opacity"] = {"condition": {"param": "pick", "value": 1}, "value": 0.15}
    layers: List[Dict[str, Any]] = []
    if chart_type == "line":
        layers.append({"mark": {"type": "line", "strokeWidth": 2}, "encoding": series})
    elif chart_type == "area":
        layers.append({"mark": {"type": "area", "opacity": 0.3, "line": True}, "encoding": series})
    layers.append({
        "params": params,
        "mark": {"type": "point", "filled": True, "cursor": "pointer"},
        "encoding": dict(
            series,
            tooltip=tooltip,
            size={"condition": {"param": "hover", "empty": False, "value": 150},
                  "value": 70 if chart_type == "point" else 30},
        ),
    })
    spec["layer"] = layers
    return plot_store.save_plot(spec)


def _fit_projection(points: List[Dict[str, Any]], height: int, width: int = 640) -> Dict[str, Any]:
    """Mercator projection centred on the points and scaled so they all fit."""
    lats = [p["lat"] for p in points]
    lngs = [p["lng"] for p in points]

    def merc_y(lat: float) -> float:
        lat = max(min(lat, 85.0), -85.0)
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    lng_span = math.radians(max(max(lngs) - min(lngs), 2.0))
    lat_span = max(abs(merc_y(max(lats)) - merc_y(min(lats))), math.radians(2.0))
    scale = 0.7 * min(width / lng_span, height / lat_span)
    center = [(max(lngs) + min(lngs)) / 2, (max(lats) + min(lats)) / 2]
    return {"type": "mercator", "center": center, "scale": max(scale, 100.0)}


def save_map(
    points: Sequence[Dict[str, Any]],
    label: str = "name",
    value: str = "",
    color: str = "",
    title: str = "",
    height: int = 380,
) -> str:
    """Builds an interactive point map (world basemap + markers) and returns its plot_path.

    The view auto-centres and zooms to fit the points. Markers show a tooltip on
    hover; marker size follows ``value`` and colour follows ``color`` (clicking a
    legend entry isolates that group). No API key is needed.

    Args:
        points: Row dicts with numeric "lat" and "lng" keys plus any other fields,
            e.g. [{"name": "Austin", "lat": 30.27, "lng": -97.74, "headcount": 12}].
        label: Row key shown as the marker label and first tooltip line.
        value: Optional numeric row key that sets the marker size.
        color: Optional row key that colours markers by category.
        title: Optional map title.
        height: Map height in pixels. Width always fills the card.
    """
    data: List[Dict[str, Any]] = []
    for point in points or []:
        if not isinstance(point, dict):
            continue
        lat, lng = _to_number(point.get("lat")), _to_number(point.get("lng"))
        if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        row = dict(point, lat=lat, lng=lng)
        if value:
            row[value] = _to_number(point.get(value))
        data.append(row)
    if not data:
        raise ValueError("No points with valid numeric 'lat' and 'lng' values.")
    missing = [key for key in (label, value, color) if key and key not in data[0]]
    if missing:
        raise ValueError(f"Unknown field(s) {missing}. Available: {sorted(data[0])}.")

    tooltip: List[Dict[str, Any]] = [{"field": _field(label), "type": "nominal", "title": label}]
    if value:
        tooltip.append({"field": _field(value), "type": "quantitative", "title": value, "format": ","})
    if color and color not in (label, value):
        tooltip.append({"field": _field(color), "type": "nominal", "title": color})
    tooltip += [
        {"field": "lat", "type": "quantitative", "format": ".4f"},
        {"field": "lng", "type": "quantitative", "format": ".4f"},
    ]

    params: List[Dict[str, Any]] = [{"name": "hover", "select": {"type": "point", "on": "pointerover", "clear": "pointerout"}}]
    if color:
        params.append({"name": "pick", "select": {"type": "point", "fields": [_field(color)]}, "bind": "legend"})
    position = {
        "longitude": {"field": "lng", "type": "quantitative"},
        "latitude": {"field": "lat", "type": "quantitative"},
    }
    markers: Dict[str, Any] = {
        "data": {"values": data},
        "params": params,
        "mark": {"type": "circle", "stroke": "#ffffff", "strokeWidth": 1.5, "cursor": "pointer"},
        "encoding": dict(
            position,
            size=({"field": _field(value), "type": "quantitative", "title": value, "scale": {"range": [90, 900]}}
                  if value else {"value": 180}),
            color=({"field": _field(color), "type": "nominal", "title": color} if color else {"value": PALETTE[3]}),
            opacity={"condition": {"param": "pick" if color else "hover", "value": 0.9}, "value": 0.3},
            tooltip=tooltip,
        ),
    }
    layers: List[Dict[str, Any]] = [
        {
            "data": {"url": WORLD_TOPOJSON, "format": {"type": "topojson", "feature": "countries"}},
            "mark": {"type": "geoshape", "fill": "#eef1f4", "stroke": "#c3c9d0", "strokeWidth": 0.5},
        },
        markers,
    ]
    if len(data) <= 15:  # labels get unreadable beyond this
        layers.append({
            "data": {"values": data},
            "mark": {"type": "text", "dy": -14, "fontSize": 11, "color": "#3c4043"},
            "encoding": dict(position, text={"field": _field(label), "type": "nominal"}),
        })

    spec: Dict[str, Any] = {
        "$schema": SCHEMA, "width": "container", "height": height,
        "projection": _fit_projection(data, height), "layer": layers, "config": _CONFIG,
    }
    if title:
        spec["title"] = _title(title)
    return plot_store.save_plot(spec)



def save_google_map(points: Sequence[Dict[str, Any]], size: str = "640x320") -> Optional[str]:
    """Stores a Google Static Maps URL for the points and returns its "/plots/<id>" path.

    Bind an ``Image`` to it: {"component": "Image", "url": {"path": map_path}}.
    The Angular/React renderers upgrade a Static Maps URL to a live, interactive
    Google Map; other renderers (e.g. Gemini Enterprise) show the static image.
    The URL (which contains the API key) never passes through the LLM.

    Returns None when GOOGLE_MAPS_API_KEY is not set - fall back to ``save_map``.
    Raises ValueError when no point has a valid "lat"/"lng".
    """
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        return None
    coords = []
    for point in points:
        lat, lng = _to_number(point.get("lat")), _to_number(point.get("lng"))
        if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        coords.append(f"{lat:.5f},{lng:.5f}")
    if not coords:
        raise ValueError("No valid lat/lng points to put on the map.")
    params = [("size", size), ("scale", "2"), ("markers", "color:red|" + "|".join(coords)), ("key", key)]
    return plot_store.save_plot("https://maps.googleapis.com/maps/api/staticmap?" + urlencode(params, safe=":|,"))
