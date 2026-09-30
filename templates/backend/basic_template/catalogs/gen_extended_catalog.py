"""Build extended_catalog.json = A2UI Basic catalog v0.9 + Table + Chart.

Run from the backend/ folder:
    uv run python manager_dashboard/catalogs/gen_extended_catalog.py
"""
import copy
import json
import os
from importlib import resources

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "extended_catalog.json")
COMMON = "https://a2ui.org/specification/v0_9/common_types.json#/$defs/"


def _component(name: str, props: dict, required: list) -> dict:
    """Same envelope every Basic component uses (common props + strict keys)."""
    return {
        "type": "object",
        "allOf": [
            {"$ref": COMMON + "ComponentCommon"},
            {"$ref": "#/$defs/CatalogComponentCommon"},
            {
                "type": "object",
                "properties": {"component": {"const": name}, **props},
                "required": ["component", *required],
            },
        ],
        "unevaluatedProperties": False,
    }


TABLE = _component(
    "Table",
    {
        "title": {"$ref": COMMON + "DynamicString", "description": "Optional table title."},
        "columns": {
            "type": "array",
            "description": "Column definitions, in display order.",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Field name in each row object."},
                    "label": {"type": "string", "description": "Column header text."},
                    "type": {"type": "string", "enum": ["text", "number"], "default": "text"},
                    "editable": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "If true, the user can edit this column's cells. Edits are written "
                            "back to the bound rows path, so rows MUST be a {\"path\": ...} binding."
                        ),
                    },
                },
                "required": ["key", "label"],
                "additionalProperties": False,
            },
        },
        "rows": {
            "$ref": COMMON + "DynamicValue",
            "description": "Array of row objects, or {\"path\": \"/...\"} bound to an array in the data model.",
        },
        "pageSize": {"type": "number", "description": "Rows per page (default 5)."},
    },
    ["columns", "rows"],
)

CHART = _component(
    "Chart",
    {
        "title": {"$ref": COMMON + "DynamicString", "description": "Optional chart title."},
        "chartType": {
            "type": "string",
            "enum": ["bar", "line", "area", "point", "pie"],
            "description": "Kind of chart to draw.",
        },
        "data": {
            "$ref": COMMON + "DynamicValue",
            "description": "Array of row objects, or {\"path\": \"/...\"} bound to an array in the data model.",
        },
        "x": {"type": "string", "description": "Field for the x axis (category field for pie)."},
        "y": {"type": "string", "description": "Numeric field for the y axis (value field for pie)."},
        "color": {"type": "string", "description": "Optional field used to colour series."},
    },
    ["chartType", "data", "x", "y"],
)

VEGA_CHART = _component(
    "VegaChart",
    {
        "title": {"$ref": COMMON + "DynamicString", "description": "Optional chart title."},
        "spec": {
            "$ref": COMMON + "DataBinding",
            "description": (
                "Complete Vega-Lite spec built by a tool. Always a data binding: "
                "{\"path\": plot_path} using the plot_path returned by the tool."
            ),
        },
    },
    ["spec"],
)

GRID = _component(
    "Grid",
    {
        "children": {
            "$ref": COMMON + "ChildList",
            "description": "The items, laid out in a responsive grid (left to right, then top to bottom). "
            "Use a template {\"componentId\": ..., \"path\": ...} to render one item per data-list entry.",
        },
        "columns": {
            "type": "integer",
            "minimum": 1,
            "maximum": 4,
            "description": "OPTIONAL. Only when the user explicitly asks for N columns. "
            "Omit it and the renderer picks the column count from the available width.",
        },
    },
    ["children"],
)

def main() -> None:
    base_path = resources.files("a2ui") / "assets" / "0.9" / "catalog.json"
    catalog = copy.deepcopy(json.loads(base_path.read_text(encoding="utf-8")))
    catalog["title"] = "A2UI Basic catalog + Table + Chart + VegaChart"
    catalog["components"]["Grid"] = GRID
    catalog["components"]["Table"] = TABLE
    catalog["components"]["Chart"] = CHART
    catalog["components"]["VegaChart"] = VEGA_CHART
    # The validator only accepts components listed in $defs.anyComponent.oneOf,
    # so the new components must be registered there too.
    any_component = catalog["$defs"]["anyComponent"]["oneOf"]
    for name in ("Table", "Chart", "VegaChart", "Grid"):
        ref = {"$ref": f"#/components/{name}"}
        if ref not in any_component:
            any_component.append(ref)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    print(f"Wrote {OUT} with {len(catalog['components'])} components")


if __name__ == "__main__":
    main()
