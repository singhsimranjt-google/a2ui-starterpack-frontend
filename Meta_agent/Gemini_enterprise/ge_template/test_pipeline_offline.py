"""Offline pipeline tests for the MATERIAL build - no LLM, no credentials.

Exercises the real a2ui_utils code paths we changed:
  parse_a2ui_response -> normalize_a2ui_messages -> is_renderable -> _wrap_a2ui_part
and the inbound click path  _summarize_user_action.

This covers everything except "does the model choose to emit good JSON", which
needs live credentials.
"""

import base64
import json
import os
import sys

sys.path.insert(
    0, "/usr/local/google/home/sidchaudhary/Desktop/A2UI/Gemini_enterprise_material_UI"
)
from ge_template.src import a2ui_utils as U  # noqa: E402

RESET = "\033[0m"; G = "\033[92m"; R = "\033[91m"; B = "\033[1m"
results = []


def check(label, cond, detail=""):
    results.append((label, bool(cond)))
    print(f"  [{G}PASS{RESET}] {label}" if cond else f"  [{R}FAIL{RESET}] {label}")
    if detail and not cond:
        print(f"          {detail}")


MATERIAL_ID = "https://a2ui.org/specification/v0_9/material_catalog.json"
BASIC_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"

GOOD_CARD = [
    {"version": "v0.9", "createSurface": {"surfaceId": "s1", "catalogId": MATERIAL_ID}},
    {"version": "v0.9", "updateComponents": {"surfaceId": "s1", "components": [
        {"id": "root", "component": "MaterialColumn", "children": ["card"]},
        {"id": "card", "component": "MaterialCard", "children": ["col"]},
        {"id": "col", "component": "MaterialColumn",
         "children": ["t", "d", "date", "time", "btn"]},
        {"id": "t", "component": "MaterialText", "usageHint": "h3", "text": "Book"},
        {"id": "d", "component": "MaterialDivider"},
        {"id": "date", "component": "MaterialDatepicker", "label": "Date",
         "value": {"path": "/appt_date"}},
        {"id": "time", "component": "MaterialTimepicker", "label": "Time",
         "value": {"path": "/appt_time"}},
        {"id": "btn", "component": "MaterialButton", "label": "Confirm",
         "variant": "primary",
         "action": {"event": {"name": "confirm_appointment",
                              "context": {"appointment_date": {"path": "/appt_date"}}}}},
    ]}},
]

# ======================================================================
print(f"\n{B}1. CATALOG WIRING{RESET}")
# ======================================================================
check("CATALOG_ID points at the Material catalog", U.CATALOG_ID == MATERIAL_ID,
      f"got {U.CATALOG_ID}")
check("BASIC_CATALOG_ID constant is gone", not hasattr(U, "BASIC_CATALOG_ID"))
check("validator was constructible", U._get_validator() is not None,
      "validator is None -> is_renderable fails OPEN, nothing is checked")

# ======================================================================
print(f"\n{B}2. NORMALIZE - the silent-overwrite site{RESET}")
# ======================================================================
n = U.normalize_a2ui_messages(json.loads(json.dumps(GOOD_CARD)), uuid_suffix="deadbeef")
cs = next(m["createSurface"] for m in n if "createSurface" in m)
check("normalize stamps the MATERIAL catalogId", cs["catalogId"] == MATERIAL_ID,
      f"got {cs['catalogId']}")

# a model that wrongly emits the BASIC id must be corrected to Material
wrong = json.loads(json.dumps(GOOD_CARD))
wrong[0]["createSurface"]["catalogId"] = BASIC_ID
n2 = U.normalize_a2ui_messages(wrong, uuid_suffix="deadbeef")
cs2 = next(m["createSurface"] for m in n2 if "createSurface" in m)
check("a stray BASIC catalogId is rewritten to Material", cs2["catalogId"] == MATERIAL_ID,
      f"got {cs2['catalogId']}")
check("surfaceId is uniquified per block", cs["surfaceId"].endswith("-deadbeef"),
      f"got {cs['surfaceId']}")

# ======================================================================
print(f"\n{B}3. VALIDATION - accepts Material, rejects basic{RESET}")
# ======================================================================
check("valid Material card is renderable", U.is_renderable(n))

basic_card = [
    {"version": "v0.9", "createSurface": {"surfaceId": "s1", "catalogId": MATERIAL_ID}},
    {"version": "v0.9", "updateComponents": {"surfaceId": "s1", "components": [
        {"id": "root", "component": "Card", "child": "t"},
        {"id": "t", "component": "Text", "text": "hi"},
    ]}},
]
check("basic-catalog card is rejected", not U.is_renderable(basic_card))

typo = json.loads(json.dumps(n))
typo[1]["updateComponents"]["components"][3]["component"] = "MaterialTxt"
check("typo'd component is rejected", not U.is_renderable(typo))

# ======================================================================
print(f"\n{B}4. FULL RESPONSE PARSE (what the model actually emits){RESET}")
# ======================================================================
raw = ("Here is your booking form.\n"
       f"<a2ui-json>{json.dumps(GOOD_CARD)}</a2ui-json>")
clean, msgs = U.parse_a2ui_response(raw)
check("companion markdown is extracted", clean == "Here is your booking form.",
      f"got {clean!r}")
check("A2UI messages are extracted", msgs is not None and len(msgs) == 2,
      f"got {msgs if msgs is None else len(msgs)}")
if msgs:
    norm = U.normalize_a2ui_messages(msgs)
    check("end-to-end payload is renderable", U.is_renderable(norm))
    parts = [U._wrap_a2ui_part(m) for m in norm]
    check("every message wraps into an inline data part",
          all(getattr(p, "inline_data", None) is not None for p in parts))
    blob = parts[0].inline_data.data.decode()
    check("wrapped part carries the a2a datapart tag",
          "<a2a_datapart_json>" in blob and "application/json+a2ui" in blob)

# ======================================================================
print(f"\n{B}5. BUTTON CLICK -> plain text for the model{RESET}")
# ======================================================================
def click_blob(name, context):
    payload = {"kind": "data", "metadata": {"mimeType": "application/json+a2ui"},
               "data": {"action": {"name": name, "context": context},
                        "surfaceId": "clinic_surface-abc", "timestamp": "2026-09-22T11:00:00Z"}}
    return f"<a2a_datapart_json>{json.dumps(payload)}</a2a_datapart_json>".encode()


s = U._summarize_user_action(click_blob("get_doctors_for_department",
                                        {"department": "Orthopedics"}))
print(f"          -> {s!r}")
check("click summary is produced", s is not None)
check("the CLICKED value survives (Orthopedics)", s and "Orthopedics" in s,
      f"got {s!r}")
check("event name survives", s and "get_doctors_for_department" in s)
check("raw tag is NOT shown to the model", s and "<a2a_datapart_json>" not in s)
check("surfaceId is not leaked to the model", s and "clinic_surface-abc" not in s)

# Material adds a "prompt" key inside context - make sure it does not break parsing
s2 = U._summarize_user_action(click_blob("confirm_appointment", {
    "prompt": "Submit my reservation",
    "patient_name": "Jane Doe",
    "appointment_date": "2026-10-21",
    "appointment_time": "14:30",
}))
print(f"          -> {s2!r}")
check("Material-style context (with 'prompt') still parses", s2 is not None)
check("all form fields survive", s2 and "Jane Doe" in s2 and "2026-10-21" in s2
      and "14:30" in s2, f"got {s2!r}")

check("garbage blob returns None (no crash)",
      U._summarize_user_action(b"not a datapart at all") is None)
check("malformed JSON returns None (no crash)",
      U._summarize_user_action(b"<a2a_datapart_json>{bad</a2a_datapart_json>") is None)

# ======================================================================
print(f"\n{B}6. DATE PARSING - what a datepicker might send{RESET}")
# ======================================================================
from ge_template.src import tools as T  # noqa: E402

DATE_CASES = [
    ("2026-10-21", True, "ISO (what MaterialDatepicker most likely sends)"),
    ("2026-10-21T00:00:00", True, "ISO with midnight time"),
    ("10/21/2026", True, "US slash"),
    ("21-10-2026", True, "EU dash"),
    ("October 21, 2026", True, "long form"),
    ("2026-10-21T00:00:00.000Z", None, "JS toISOString - UNVERIFIED"),
    ("Tue Oct 21 2026", None, "JS Date.toDateString - UNVERIFIED"),
    ("not-a-date", False, "garbage must still be rejected"),
]
for value, expect, note in DATE_CASES:
    got = T._parse_date(value) is not None
    if expect is None:
        tag = f"{G}handled{RESET}" if got else f"{R}NOT handled{RESET}"
        print(f"  [{tag}] {value!r}  ({note})")
    else:
        check(f"date {value!r} -> {'parsed' if expect else 'rejected'}  ({note})",
              got == expect)

TIME_CASES = [
    ("14:30", True, "24h - likely MaterialTimepicker"),
    ("2:30 PM", True, "12h with space"),
    ("2:30PM", True, "12h no space"),
    ("14:30:00", True, "with seconds"),
    ("99:99", False, "garbage must still be rejected"),
]
for value, expect, note in TIME_CASES:
    got = T._parse_time(value) is not None
    check(f"time {value!r} -> {'parsed' if expect else 'rejected'}  ({note})",
          got == expect)

# ======================================================================
print(f"\n{B}7. BLANK SCREEN PATH (what happens when a card is dropped){RESET}")
# ======================================================================
bad_raw = ("Sorry, that date was invalid.\n"
           f"<a2ui-json>{json.dumps(basic_card)}</a2ui-json>")
clean_b, msgs_b = U.parse_a2ui_response(bad_raw)
renderable = U.is_renderable(U.normalize_a2ui_messages(msgs_b)) if msgs_b else False
print(f"          companion text survives : {clean_b!r}")
print(f"          card renderable         : {renderable}")
check("an invalid card is correctly detected as unrenderable", not renderable)
check("companion markdown still exists as a fallback", bool(clean_b),
      "if this is empty AND the card is dropped, the user sees a BLANK SCREEN")

# ======================================================================
print(f"\n{B}{'=' * 68}{RESET}")
passed = sum(1 for _, ok in results if ok)
failed = len(results) - passed
print(f"{B}{passed} passed, {failed} failed{RESET}")
for label, ok in results:
    if not ok:
        print(f"  {R}FAILED:{RESET} {label}")
sys.exit(0 if failed == 0 else 1)
