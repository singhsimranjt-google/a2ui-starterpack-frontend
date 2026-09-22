"""Converts the basic-catalog v0_9 example JSONs to the Material catalog.

Reads from a source directory and writes converted copies to an output
directory; the originals are never modified.

Transformations
---------------
  catalogId                     -> material_catalog.json
  Column/Row/Divider            -> Material* equivalents
  Card.child: "x"               -> MaterialCard.children: ["x"]
  Text.variant                  -> MaterialText.usageHint
  Icon.name                     -> MaterialIcon.icon
  CheckBox.value                -> MaterialCheckbox.checked
  TextField.variant             -> MaterialInput.type  (mapped, see INPUT_TYPE_MAP)
  Button.child -> Text          -> MaterialButton.label (orphan Text deleted)
  ChoicePicker                  -> MaterialChips; its `label` becomes a sibling
                                   MaterialText caption, since MaterialChips has
                                   no label property
  DateTimeInput                 -> MaterialDatepicker | MaterialTimepicker
                                   (chosen by enableDate/enableTime; flags dropped)
"""

import argparse
import json
import os
import sys

MATERIAL_CATALOG_ID = "https://a2ui.org/specification/v0_9/material_catalog.json"

SIMPLE_RENAMES = {
    "Column": "MaterialColumn",
    "Row": "MaterialRow",
    "Divider": "MaterialDivider",
}

# basic TextField.variant -> MaterialInput.type
INPUT_TYPE_MAP = {
    "shortText": "text",
    "longText": "text",
    "number": "number",
    "obscured": "password",
}


def _convert_components(components):
    """Returns (new_components, notes). Mutates nothing in place."""
    notes = []
    by_id = {c["id"]: c for c in components if isinstance(c, dict) and "id" in c}
    drop_ids = set()
    # chips id -> caption component to insert before it
    captions = {}
    out = []

    for comp in components:
        if not isinstance(comp, dict):
            continue
        kind = comp.get("component")
        new = dict(comp)

        if kind in SIMPLE_RENAMES:
            new["component"] = SIMPLE_RENAMES[kind]

        elif kind == "TextField":
            new["component"] = "MaterialInput"
            variant = new.pop("variant", None)
            if variant is not None:
                mapped = INPUT_TYPE_MAP.get(variant, "text")
                new["type"] = mapped
                notes.append(f"  {comp['id']}: variant {variant!r} -> type {mapped!r}")

        elif kind == "Card":
            new["component"] = "MaterialCard"
            if "child" in new:
                new["children"] = [new.pop("child")]

        elif kind == "Text":
            new["component"] = "MaterialText"
            if "variant" in new:
                new["usageHint"] = new.pop("variant")

        elif kind == "Icon":
            new["component"] = "MaterialIcon"
            if "name" in new:
                new["icon"] = new.pop("name")

        elif kind == "CheckBox":
            new["component"] = "MaterialCheckbox"
            if "value" in new:
                new["checked"] = new.pop("value")

        elif kind == "ChoicePicker":
            new["component"] = "MaterialChips"
            # MaterialChips has no `label`; preserve it as a sibling caption so
            # the user does not silently lose the field's meaning.
            label = new.pop("label", None)
            if label:
                cap_id = f"{comp['id']}_caption"
                captions[comp["id"]] = {
                    "component": "MaterialText",
                    "id": cap_id,
                    "usageHint": "caption",
                    "text": label,
                }
                notes.append(
                    f"  {comp['id']}: label {label!r} -> sibling MaterialText '{cap_id}'"
                )
            for gone in ("displayStyle", "filterable", "variant"):
                if gone in new:
                    notes.append(
                        f"  {comp['id']}: dropped {gone!r} (MaterialChips has no such property)"
                    )
                    new.pop(gone)

        elif kind == "DateTimeInput":
            enable_date = new.pop("enableDate", True)
            enable_time = new.pop("enableTime", True)
            if enable_time and not enable_date:
                new["component"] = "MaterialTimepicker"
            else:
                new["component"] = "MaterialDatepicker"
            for gone in ("min", "max"):
                new.pop(gone, None)
            notes.append(f"  {comp['id']}: DateTimeInput -> {new['component']}")

        elif kind == "Button":
            new["component"] = "MaterialButton"
            child_id = new.pop("child", None)
            if child_id is not None:
                child = by_id.get(child_id)
                if child and child.get("component") == "Text":
                    new["label"] = child.get("text", "")
                    drop_ids.add(child_id)
                    notes.append(
                        f"  {comp['id']}: inlined label {new['label']!r}, "
                        f"removed orphan Text '{child_id}'"
                    )
                else:
                    notes.append(
                        f"  {comp['id']}: WARNING child '{child_id}' is not a Text; "
                        "label left unset"
                    )
            if "variant" not in new:
                new["variant"] = "primary"

        out.append(new)

    # Second pass: remove the now-inlined button label Texts.
    out = [c for c in out if c.get("id") not in drop_ids]

    # Third pass: splice caption components in just before their chips, both in
    # the component list and in whichever parent references the chips.
    if captions:
        for comp in out:
            kids = comp.get("children")
            if not isinstance(kids, list):
                continue
            new_kids = []
            for k in kids:
                if k in captions:
                    new_kids.append(captions[k]["id"])
                new_kids.append(k)
            comp["children"] = new_kids

        spliced = []
        for comp in out:
            cap = captions.get(comp.get("id"))
            if cap:
                spliced.append(cap)
            spliced.append(comp)
        out = spliced

    # Safety: nothing may still reference a dropped id.
    for comp in out:
        kids = comp.get("children")
        if isinstance(kids, list):
            bad = [k for k in kids if k in drop_ids]
            if bad:
                notes.append(f"  {comp['id']}: WARNING still references dropped {bad}")
    return out, notes


def convert_document(doc):
    notes = []
    out = []
    for msg in doc:
        msg = dict(msg)
        if "createSurface" in msg:
            cs = dict(msg["createSurface"])
            cs["catalogId"] = MATERIAL_CATALOG_ID
            msg["createSurface"] = cs
        if "updateComponents" in msg:
            uc = dict(msg["updateComponents"])
            comps, n = _convert_components(uc.get("components", []))
            uc["components"] = comps
            msg["updateComponents"] = uc
            notes.extend(n)
        out.append(msg)
    return out, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("out_dir")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(args.src_dir) if f.endswith(".json"))
    if not files:
        print(f"No JSON files in {args.src_dir}")
        return 1

    for fn in files:
        with open(os.path.join(args.src_dir, fn), encoding="utf-8") as f:
            doc = json.load(f)
        converted, notes = convert_document(doc)
        with open(os.path.join(args.out_dir, fn), "w", encoding="utf-8") as f:
            json.dump(converted, f, indent=2)
            f.write("\n")
        print(f"{fn}")
        for n in notes:
            print(n)
    print(f"\nConverted {len(files)} files -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
