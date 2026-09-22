"""Generates a Material v0_9 catalog schema for the A2UI SDK.

Google has not published a machine-readable Material catalog schema
(https://a2ui.org/specification/v0_9/material_catalog.json returns 404), so we
reconstruct one from the official examples in the a2ui-project/a2ui repo.

Strategy: reuse the bundled BASIC catalog's shared plumbing ($defs, functions,
and the common_types.json $refs, all of which are catalog-independent within
v0.9) and substitute hand-authored Material component definitions.

Run from the ge_template directory:
    .venv/bin/python gen_material_catalog.py
"""

import json
import os

from a2ui.basic_catalog.constants import BASIC_CATALOG_PATHS
from a2ui.schema.constants import CATALOG_SCHEMA_KEY, VERSION_0_9
from a2ui.schema.utils import load_from_bundled_resource

CT = "https://a2ui.org/specification/v0_9/common_types.json#/$defs"
MATERIAL_CATALOG_ID = "https://a2ui.org/specification/v0_9/material_catalog.json"


def _component(name, props, required=None, extra_refs=(), description=None):
    """Builds one component schema in the same shape the basic catalog uses."""
    body = {"type": "object", "properties": {"component": {"const": name}, **props}}
    if description:
        body["description"] = description
    body["required"] = ["component"] + list(required or [])
    return {
        "type": "object",
        "allOf": [
            {"$ref": f"{CT}/ComponentCommon"},
            {"$ref": "#/$defs/CatalogComponentCommon"},
            *({"$ref": r} for r in extra_refs),
            body,
        ],
        "unevaluatedProperties": False,
    }


def build_components():
    dyn_str = {"$ref": f"{CT}/DynamicString"}
    child_list = {
        "description": (
            "Child component IDs. Children cannot be defined inline; they must be"
            " referred to by ID."
        ),
        "$ref": f"{CT}/ChildList",
    }
    align = {"type": "string", "enum": ["start", "center", "end", "stretch"]}
    justify = {
        "type": "string",
        "enum": [
            "start",
            "center",
            "end",
            "spaceBetween",
            "spaceAround",
            "spaceEvenly",
        ],
    }
    style = {"type": "object", "description": "Inline CSS-like style overrides."}
    color = {"type": "string", "enum": ["primary", "accent", "warn"]}

    return {
        "MaterialText": _component(
            "MaterialText",
            {
                "text": dyn_str,
                "usageHint": {
                    "type": "string",
                    "description": "A hint for the base text style.",
                    "enum": ["h1", "h2", "h3", "h4", "h5", "caption", "body"],
                    "default": "body",
                },
            },
            required=["text"],
        ),
        "MaterialColumn": _component(
            "MaterialColumn",
            {"children": child_list, "align": align, "style": style},
            description="A layout component that arranges its children vertically.",
        ),
        "MaterialRow": _component(
            "MaterialRow",
            {
                "children": child_list,
                "align": align,
                "justify": justify,
                "style": style,
            },
            description="A layout component that arranges its children horizontally.",
        ),
        "MaterialCard": _component(
            "MaterialCard",
            {
                "children": child_list,
                "appearance": {
                    "type": "string",
                    "enum": ["raised", "outlined", "filled"],
                },
            },
            description=(
                "A surface container. NOTE: unlike the basic catalog's Card, this"
                " takes a `children` ARRAY, not a single `child` string."
            ),
        ),
        "MaterialDivider": _component(
            "MaterialDivider", {}, description="A thin horizontal rule."
        ),
        "MaterialIcon": _component(
            "MaterialIcon",
            {
                "icon": {
                    "type": "string",
                    "description": "The Material Symbols icon name, e.g. 'event'.",
                }
            },
            required=["icon"],
        ),
        "MaterialButton": _component(
            "MaterialButton",
            {
                "label": dyn_str,
                "variant": {
                    "type": "string",
                    "enum": [
                        "basic",
                        "raised",
                        "stroked",
                        "flat",
                        "icon",
                        "fab",
                        "primary",
                    ],
                },
                "color": color,
                "action": {"$ref": f"{CT}/Action"},
            },
            required=["label"],
            extra_refs=(f"{CT}/Checkable",),
            description=(
                "A button. The label is INLINE via the `label` property; do NOT"
                " create a child MaterialText component for it."
            ),
        ),
        "MaterialInput": _component(
            "MaterialInput",
            {
                "label": dyn_str,
                "value": dyn_str,
                "type": {
                    "type": "string",
                    "enum": ["text", "number", "email", "password", "tel", "url"],
                    "default": "text",
                },
            },
            required=["label"],
            extra_refs=(f"{CT}/Checkable",),
        ),
        "MaterialCheckbox": _component(
            "MaterialCheckbox",
            {
                "label": dyn_str,
                "checked": {"$ref": f"{CT}/DynamicBoolean"},
                "color": color,
            },
            required=["label", "checked"],
            description="A checkbox. Bind state to `checked`, NOT `value`.",
        ),
        "MaterialChips": _component(
            "MaterialChips",
            {
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["label", "value"],
                    },
                },
                "value": {"$ref": f"{CT}/DynamicStringList"},
                "ariaLabel": {"type": "string"},
            },
            required=["options", "value"],
            description=(
                "Selectable chips. Has NO `label` property; add a sibling"
                " MaterialText for the caption."
            ),
        ),
        "MaterialDatepicker": _component(
            "MaterialDatepicker",
            {"label": dyn_str, "value": dyn_str},
            required=["value"],
        ),
        "MaterialTimepicker": _component(
            "MaterialTimepicker",
            {"label": dyn_str, "value": dyn_str},
            required=["value"],
        ),
    }


def main():
    basic = load_from_bundled_resource(
        VERSION_0_9, CATALOG_SCHEMA_KEY, BASIC_CATALOG_PATHS
    )
    components = build_components()

    catalog = {
        "$schema": basic.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        ),
        "$id": MATERIAL_CATALOG_ID,
        "title": "A2UI Material Catalog (v0.9, reconstructed)",
        "description": (
            "Reconstructed from official a2ui-project examples. Google has not"
            " published an authoritative Material catalog schema for v0.9."
        ),
        "catalogId": MATERIAL_CATALOG_ID,
        "components": components,
        # Functions are catalog-independent within v0.9 - reuse verbatim.
        "functions": basic["functions"],
        "$defs": {
            "CatalogComponentCommon": basic["$defs"]["CatalogComponentCommon"],
            "theme": basic["$defs"]["theme"],
            "anyComponent": {
                "oneOf": [{"$ref": f"#/components/{n}"} for n in components],
                "discriminator": {"propertyName": "component"},
            },
            "anyFunction": basic["$defs"]["anyFunction"],
        },
    }

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "src", "catalogs"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "material_catalog.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        f.write("\n")

    print(f"Wrote {out_path}")
    print(f"  components: {len(components)}")
    print(f"  functions:  {len(catalog['functions'])}")


if __name__ == "__main__":
    main()
