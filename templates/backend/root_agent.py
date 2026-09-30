import re
import os
import sys
import shutil
from google.genai import Client
from dotenv import load_dotenv

# Load .env BEFORE the config block below, so every setting can be overridden
# from .env without touching this file.
load_dotenv()

# ===========================================================================
#  CONFIGURATION - change things here, not further down the file.
#
#  SECRETS NEVER LIVE IN THIS FILE.
#  Credentials (GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT, ...) are read from .env
#  at runtime. Everything below is either a non-sensitive default or the NAME
#  of an environment variable - never a value. Safe to commit.
#
#  Every setting follows the same pattern:
#      CONSTANT = os.getenv("CONSTANT", "<default>")
#  so you can change it here, or override it in .env, without editing code.
# ===========================================================================

# --- Models ----------------------------------------------------------------
# One knob per stage so you can, for example, run a cheaper Critic.
# Override in .env with PLANNER_MODEL=... / CODER_MODEL=... / CRITIC_MODEL=...
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gemini-2.5-pro")
CODER_MODEL = os.getenv("CODER_MODEL", "gemini-2.5-pro")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gemini-2.5-pro")

# --- Credentials (names only - the VALUES stay in .env) ---------------------
# Direct Gemini API mode.
API_KEY_ENV_VAR = "GEMINI_API_KEY"
# Vertex AI mode. When GOOGLE_GENAI_USE_VERTEXAI is true the google-genai SDK
# authenticates via Application Default Credentials + the project/location
# below, and NO api key is required.
VERTEX_FLAG_ENV_VAR = "GOOGLE_GENAI_USE_VERTEXAI"
VERTEX_PROJECT_ENV_VAR = "GOOGLE_CLOUD_PROJECT"
VERTEX_LOCATION_ENV_VAR = "GOOGLE_CLOUD_LOCATION"

# --- Generation loop -------------------------------------------------------
# How many times the Coder is sent back to fix its output before giving up.
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# --- Directories -----------------------------------------------------------
# The golden template that every new agent is cloned from.
TEMPLATE_DIR_NAME = os.getenv("TEMPLATE_DIR_NAME", "basic_template")

# Used when the Coder emits a missing / unsafe / reserved folder name.
FALLBACK_AGENT_NAME = os.getenv("FALLBACK_AGENT_NAME", "generated_agent")

# Directories the generator must never delete or overwrite.
RESERVED_DIR_NAMES = {
    "basic_template", "tests", "examples", "frontend", "backend",
    "src", "node_modules", "meta_json",
}

# --- Features --------------------------------------------------------------
# Master switch for the greeting / capabilities card in every generated agent.
# True  = always injected, unless the Planner records an explicit user opt-out
#         via the <WELCOME_VIEW>off</WELCOME_VIEW> sentinel.
# False = never injected, regardless of what the user or the Planner say.
WELCOME_VIEW_ENABLED = os.getenv("WELCOME_VIEW_ENABLED", "true").lower() not in (
    "false", "0", "no",
)

# ===========================================================================


# ---------------------------------------------------------------------------
# VALID ICON NAMES - read from the installed a2ui catalog so this can never
# drift from the spec.
#
# This exists because the catalog uses camelCase names ("calendarToday") while
# LLMs reliably hallucinate Material Design snake_case ("calendar_month").
# The React frontend hard-fails validation on a bad name; Angular silently
# renders a broken glyph. Both are caught here instead.
# ---------------------------------------------------------------------------
_FALLBACK_ICON_NAMES = {
    "accountCircle", "add", "arrowBack", "arrowForward", "attachFile",
    "calendarToday", "call", "camera", "check", "close", "delete", "download",
    "edit", "event", "error", "fastForward", "favorite", "favoriteOff",
    "folder", "help", "home", "info", "locationOn", "lock", "lockOpen", "mail",
    "menu", "moreVert", "moreHoriz", "notificationsOff", "notifications",
    "pause", "payment", "person", "phone", "photo", "play", "print", "refresh",
    "rewind", "search", "send", "settings", "share", "shoppingCart",
    "skipNext", "skipPrevious", "star", "starHalf", "starOff", "stop",
    "upload", "visibility", "visibilityOff", "volumeDown", "volumeMute",
    "volumeOff", "volumeUp", "warning",
}


def _find_icon_enum(node):
    """Recursively locate the Icon name enum inside the catalog schema."""
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list) and "accountCircle" in enum:
            return enum
        for value in node.values():
            found = _find_icon_enum(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_icon_enum(value)
            if found:
                return found
    return None


def _load_valid_icon_names():
    try:
        import inspect
        import json as _json
        from a2ui.basic_catalog import provider

        a2ui_root = os.path.dirname(os.path.dirname(inspect.getfile(provider)))
        catalog_path = os.path.join(a2ui_root, "assets", "0.9", "catalog.json")
        with open(catalog_path) as handle:
            enum = _find_icon_enum(_json.load(handle))
        if enum:
            return set(enum)
    except Exception as exc:  # noqa: BLE001 - never block generation on this
        print(f"⚠️  Could not read Icon enum from the a2ui catalog ({exc}).")
        print("   Falling back to the built-in icon list.")
    return set(_FALLBACK_ICON_NAMES)


VALID_ICON_NAMES = _load_valid_icon_names()


A2UI_BOILERPLATE_PROMPT = r"""
### CRITICAL OUTPUT FORMAT & A2UI SPECIFICATION (MANDATORY):
- ALWAYS output your responses directly as text in the message body.
- When rendering A2UI components, ALWAYS output the JSON strictly as text enclosed within `<a2ui-json>...</a2ui-json>` XML tags.
- The JSON inside `<a2ui-json>...</a2ui-json>` MUST be a single valid JSON array `[ ... ]` containing `createSurface`, `updateComponents`, and `updateDataModel` messages, matching the exact syntax and component hierarchy from the provided example JSON templates.
- **MANDATORY TEMPLATE FIDELITY (Basic Catalog v0.9)**:
  - You MUST refer directly to the provided example JSON files in your system instructions when generating A2UI cards.
  - The `catalogId` in `createSurface` MUST strictly be `"https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"`.
  - EVERY message object in the array (`createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`) MUST include `"version": "v0.9"` as a top-level key, e.g. `{"version": "v0.9", "createSurface": {...}}`. Omitting it fails schema validation and the server will not start.
  - You MUST strictly follow the exact component hierarchy, component types (`Card`, `Column`, `Row`, `List`, `Grid`, `Tabs`, `Modal`, `Text`, `Icon`, `Divider`, `Button`, `Image`, `TextField`, `CheckBox`, `DateTimeInput`, `ChoicePicker`, `Slider`, `Table`, `Chart`, `VegaChart`), and allowed properties defined in each example JSON file without adding any extra or invalid attributes.
  - **NO STYLING OR SIZING PROPERTIES**: Do NOT include `"style"`, `"padding"`, `"margin"`, `"spacing"`, `"gap"`, `"justifyContent"`, `"alignItems"`, `"width"`, or `"height"` on any components. All components must strictly conform to Basic Catalog schema.
  - `Text`: Valid `variant` values are strictly `"h1"`, `"h2"`, `"h3"`, `"h4"`, `"h5"`, `"caption"`, `"body"` (this is the exact enum from the v0.9 catalog schema; `"body"` is the default). Use headings for titles and `"body"`/`"caption"` for content. Do NOT invent any other variant.
  - `Icon`: Valid `name` values must be strictly chosen from this list: "accountCircle", "add", "arrowBack", "arrowForward", "attachFile", "calendarToday", "call", "camera", "check", "close", "delete", "download", "edit", "event", "error", "favorite", "home", "info", "mail", "menu", "person", "phone", "search", "settings", "star", "warning". Do not use variants like "check_circle".
- **NEVER OUTPUT INTERNAL AGENT INSTRUCTIONS**: Statements such as `(Stop here and wait for the user's response)` or `[Instruction: ...]` are internal model orchestration directives. You MUST NEVER output these instruction statements to the user.
- **STRICT ASCII CHARACTERS IN A2UI JSON**: Inside all `<a2ui-json>...</a2ui-json>` blocks, you MUST use ONLY standard ASCII characters.
- **Surface ID Generation**: Every response MUST use a NEW, UNIQUE `surfaceId`. Do NOT reuse a `surfaceId` across turns. Generate a fresh, descriptive id each time, e.g. `qual-practices-a7f3c9`, `qual-subregion-9b21`, `qual-effort-4e12`, `qual-report-8c34`.
- **Surface Management**: You must use a stable `surfaceId`. If you are redrawing the UI by emitting a `createSurface` message that shares an ID with a previously emitted surface, you MUST emit a `deleteSurface` message for that ID BEFORE the new `createSurface` message in the JSON array.
- **MANDATORY COMPANION MARKDOWN RULE**: In every turn where you output an `<a2ui-json>` block, you MUST ALSO write a concise companion fallback Markdown message outside the `<a2ui-json>` tag block. Keep the companion Markdown concise to ensure the payload is never truncated. NEVER output an empty message body.
- **NEVER OUTPUT `<a2a_datapart_json>` TAGS**: You MUST NEVER use `<a2a_datapart_json>` or wrap messages in `{"kind": "data", ...}` envelopes. ALWAYS output standard `<a2ui-json>...</a2ui-json>` blocks.
- **STRICT COMPLIANCE WITH A2UI V0.9 SPECIFICATION:** You MUST strictly adhere to the A2UI V0.9 Basic Catalog specification for component properties and schemas. Review the provided template JSON files for precise details. Ensure all component properties, data bindings, and catalog references are valid and correctly formatted according to the A2UI specification.
- **HANDLING EMPTY INPUTS**: If the user sends an empty message, or triggers an action without filling in the required form fields, you MUST NOT hallucinate data or crash. Instead, respond with a polite companion Markdown message asking them to provide the missing information.
- **MANDATORY CARD ON TOOL FAILURE**: If a tool returns an `error` (or any failure result), you MUST STILL output a full `<a2ui-json>` block. Re-render the CURRENT view onto a BRAND NEW, UNIQUE `surfaceId` using its original JSON template, and surface the error text to the user inside that card (for example, as a `Text` component with `variant` `"caption"`, optionally preceded by an `Icon` named `"error"`). You MUST NEVER respond to a tool failure with companion Markdown alone. A reply without an `<a2ui-json>` block leaves the user with a blank screen.

"""

# ---------------------------------------------------------------------------
# Shared policy: how to reconcile the default flow with the user's own wishes.
# Injected into BOTH the Planner and the Coder so they cannot disagree.
# ---------------------------------------------------------------------------
FLOW_PRECEDENCE_RULES = r"""
=== FLOW PRECEDENCE POLICY (MUST OBEY) ===
There is a DEFAULT REFERENCE FLOW for every A2UI agent:

    Welcome / Capabilities  ->  List or Menu View  ->  Detail or Selection View
    ->  Input Form View  ->  Confirmation View (with Cancel returning to the List View)

Apply this policy, in this exact priority order:
1. EXPLICIT USER INSTRUCTION WINS. If the user clearly specifies a different flow,
   different steps, different ordering, or explicitly removes a step, you MUST follow
   the user and MUST NOT silently re-add the default steps.
2. CONTRADICTION => FOLLOW THE USER. When the user's request conflicts with the default
   reference flow, the user's instruction always overrides it. State the override in one
   short sentence so the user can see it was intentional.
3. AMBIGUITY / SILENCE => FOLLOW THE DEFAULT FLOW. If the user says nothing about a step,
   or their instruction is vague, incomplete, or open to more than one reading, you MUST
   fall back to the default reference flow above instead of inventing a new structure or
   asking an unnecessary question.
4. NEVER DROP THE WELCOME VIEW. It is the entry point of every agent and is only removed
   if the user explicitly asks for it to be removed.
5. Adapt the NAMES of the steps to the domain (e.g. "Pizza Menu", "Doctor List",
   "Ticket List"), but keep the underlying shape unless rule 1 or 2 applies.
"""

# ---------------------------------------------------------------------------
# Every generated agent must open with a self-describing welcome card that also
# teaches the user exactly what to type next.
#
# TWO LAYERS, DELIBERATELY:
#   1. WELCOME_VIEW_SPEC  -> instructs the Coder to author a domain-specific
#      welcome step + welcome_view.json. Best quality, but LLM-dependent.
#   2. WELCOME_VIEW_BLOCK -> injected verbatim into EVERY generated prompt.py at
#      write time (like the boilerplate). Cannot be dropped by any LLM, and is
#      written so the child agent can derive the card at RUNTIME from its own
#      tools even if layer 1 failed completely.
# ---------------------------------------------------------------------------
WELCOME_VIEW_SPEC = r"""
=== MANDATORY WELCOME VIEW (STEP 1 OF EVERY GENERATED AGENT) ===
You MUST emit a file `examples/v0_9/welcome_view.json`.

- Use the `=== welcome_view.json ===` entry in the JSON TEMPLATES section below as your
  GOLDEN STRUCTURAL EXAMPLE. Copy its component structure, ids, and property usage
  EXACTLY. Change ONLY the wording so it matches THIS agent's domain and real tools.
- Keep the same shape: root Column -> welcome_card -> welcome_content, with a title,
  a subtitle, a Divider, 3-5 capability Rows (Icon + Text), a Divider, a "Try saying:"
  label, and EXACTLY ONE starter-prompt Row.
- The 3-5 capabilities MUST describe real actions backed by this agent's tools.
  No filler like "help you with tasks".
- The ONE starter prompt MUST be the concrete phrase that moves the user to step 2,
  in domain nouns (e.g. "Show me the pizza menu"). Never "Get started" / "Help".
- `UI_DESCRIPTION` must make this Welcome View STEP 1 of the UI Flow: on the first turn
  the agent renders ONLY this card, calls NO tool, and then waits for the user.
"""

# Injected verbatim into every generated prompt.py. Addressed to the CHILD agent
# (not the Coder), so it must be self-contained at runtime: the child agent has no
# "JSON TEMPLATES section" and never emits files.
WELCOME_VIEW_BLOCK = r"""
### STEP 0 - WELCOME VIEW (FIRST TURN ONLY)
On the FIRST turn of a conversation - including an empty message or a generic
opener such as "hi", "hello", or "start" - render ONLY the welcome card, then stop.
- Do NOT render the main list/menu view on this turn.
- Do NOT call any tool on this turn.
- Create the surface using the normal surface rules already given above.
Card structure:
  * root `Column` has exactly one child: `welcome_card`
  * `Card` id `welcome_card` -> `child` is `Column` id `welcome_content`
  * `welcome_content` children, in order:
      1. `Text` `welcome_title`, variant "h3" - names your role
      2. `Text` `welcome_subtitle`, variant "body" - "Here's what I can do for you:"
      3. `Divider` `welcome_div_1`
      4. 3-5 capability `Row`s, each an `Icon` + a `Text` (variant "body"),
         each describing a REAL action backed by one of your tools
      5. `Divider` `welcome_div_2`
      6. `Text` `welcome_try_label`, variant "h5" - "Try saying:"
      7. ONE starter `Row`: an `Icon` + a `Text` (variant "body") holding a
         concrete domain phrase in double quotes
After rendering, WAIT for the user. When they express that intent in any phrasing,
move to the first step of the UI flow below.
"""

# ---------------------------------------------------------------------------
# SINGLE SOURCE OF TRUTH for the A2UI v0.9 rules.
# Previously this block was pasted into BOTH coder_instruction and
# critic_instruction, and the two copies had already drifted apart (the Coder
# knew 19 rules, the Critic only 18) - so the Critic could not enforce a rule
# the Coder was given. Edit here once and both stages stay in sync.
# ---------------------------------------------------------------------------
A2UI_STRICT_RULES = r"""
=== A2UI V0.9 STRICT RULES (MUST OBEY) ===
A2UI v0.9 Basic Catalog - Critical Rules for Meta-Agent Prompt Generation

When writing system prompts for A2UI agents, the Meta-Agent MUST enforce the following strict framework rules to prevent UI crashes:

1. THE FLATTENED COMPONENT REQUIREMENT (Fixes "Component root not found")
In A2UI v0.9, the `createSurface` payload DOES NOT accept a `"layout"` or nested component tree. It strictly accepts ONLY `surfaceId` and `catalogId`.
To render components, you MUST send a completely separate `updateComponents` mutation containing a FLAT array of components. The very first component in this flat array MUST have `"id": "root"`. Component nesting is achieved by passing string IDs into the `children` arrays of parent components, rather than nesting JSON objects.
INCORRECT:
`{"createSurface": {"surfaceId": "...", "layout": {"component": "Column", "id": "root", ...}}}`
CORRECT:
`{"createSurface": {"surfaceId": "...", "catalogId": "..."}}`
`{"updateComponents": {"surfaceId": "...", "components": [{"component": "Column", "id": "root", "children": ["btn1"]}, {"component": "Button", "id": "btn1", ...}]}}`

2. BUTTON TEXT (Fixes "Validation failed: Unrecognized key 'text'")
In A2UI v0.9, a `Button` component DOES NOT accept a `"text"` or `"label"` property. It strictly requires a `"child"` property containing the string ID of a separate Text component.
INCORRECT: `{ "component": "Button", "text": "Submit" }`
CORRECT: 
`{ "component": "Button", "id": "my_btn", "child": "my_btn_txt" }`
`{ "component": "Text", "id": "my_btn_txt", "text": "Submit" }`

3. CAPITALIZED COMPONENT NAMES (Fixes "Component type not found")
All component type names must be strictly TitleCased exactly as defined in the catalog.
CORRECT: `Column`, `Row`, `Text`, `Button`, `TextField`, `DateTimeInput`, `Card`.
INCORRECT: `column`, `row`, `text`

4. FEW-SHOT JSON TEMPLATING
The most robust way to guarantee the LLM follows these strict rules is to provide a complete, valid, perfectly flat JSON example file in the agent's system prompt and instruct the LLM to strictly output that exact structure. Relying purely on English layout instructions often leads to LLM hallucinations.

5. ROBUST BACKEND DATE PARSING FOR DateTimeInput (Fixes tool crashes)
When the user submits a form using `DateTimeInput`, the frontend sends the date as a full ISO-8601 string (e.g., `"2026-09-10T20:20:20.456Z"`). When this is bound to a tool parameter using A2UI data bindings (like `{"path": "/application/from_date"}`), the python backend receives the full timestamp verbatim.
Python tools MUST NOT use strict date parsing like `date.fromisoformat(from_date)`. They must robustly extract the date, either by slicing the string (`from_date[:10]`) or using `datetime.fromisoformat(...)`, otherwise the backend will crash and the LLM will get confused.

6. BUTTON ACTION SCHEMA (Fixes "Validation failed for component 'Button': action: Invalid input")
In A2UI v0.9, the `action` property on a Button MUST strictly be wrapped in an `event` object. It cannot be flattened.
INCORRECT: `"action": { "tool": "add_todo", "context": { ... } }`
CORRECT: `"action": { "event": { "name": "add_todo", "context": { ... } } }`

7. SURFACE REDRAWING LIFECYCLE (Fixes "Surface not found for message")
When dynamically adding or removing elements from the UI (like adding an item to a list), the LLM must completely redraw the UI surface with a NEW surface ID. It MUST NOT reuse the old surface ID across turns.
To do this safely, the LLM must be explicitly instructed in the system prompt to output three mutations in order when updating: 
1. `deleteSurface` for the OLD surface ID.
2. `createSurface` for a BRAND NEW, UNIQUE surface ID.
3. `updateComponents` rendering the entire updated UI into the new surface ID.

8. EXPLICIT VALUE BINDING ON INPUTS (Fixes "context: {parameter: undefined}")
In A2UI v0.9, an input component (like `TextField` or `DateTimeInput`) DOES NOT automatically sync its value to the data model just by existing. You MUST explicitly provide a `"value": {"path": "/..."}` data binding on the input component itself so the frontend knows where to store the text the user types.
INCORRECT:
`{"component": "TextField", "id": "my_input"}`
CORRECT:
`{"component": "TextField", "id": "my_input", "value": {"path": "/application/my_input"}}`

9. NO "PROPS" WRAPPER OBJECT (CRITICAL)
In A2UI v0.9, there is NO `props` wrapper. All properties like `alignItems`, `variant`, `weight`, etc., MUST be placed directly at the ROOT of the component object.
INCORRECT:
`{"component": "Column", "id": "root", "props": {"alignItems": "center"}}`
CORRECT:
`{"component": "Column", "id": "root", "alignItems": "center"}`

10. TEXTFIELD PLACEHOLDERS
`TextField` components in A2UI v0.9 do NOT support a `placeholder` property. Instead, you MUST use the `"label"` property placed at the root of the component.
INCORRECT:
`{"component": "TextField", "id": "input", "placeholder": "Enter text"}`
CORRECT:
`{"component": "TextField", "id": "input", "label": "Enter text"}`

11. NO CSS, SIZING, OR ALIGNMENT PROPERTIES
A2UI v0.9 Basic Catalog does NOT support `padding`, `margin`, `spacing`, `gap`, `justifyContent`, `alignItems`, `width`, or `height` properties on ANY components. Do NOT hallucinate these properties.
INCORRECT: `{"component": "Column", "padding": "medium", "justifyContent": "center"}`
CORRECT: `{"component": "Column"}`

12. IMAGE COMPONENTS
The `Image` component strictly accepts ONLY `id` and `url`. Do NOT hallucinate `width`, `height`, `alt`, or styling.
INCORRECT: `{"component": "Image", "id": "img", "url": "...", "width": "100px"}`
CORRECT: `{"component": "Image", "id": "img", "url": "..."}`

13. NUMBER FIELDS
Whenever a form requires a number (like quantity or age), you MUST use a TextField with the variant set to number. Example: {"component": "TextField", "id": "qty", "variant": "number", "label": "Quantity"}

14. TIME FIELDS
Whenever a form requires a time selection, you MUST strictly use the DateTimeInput component with enableTime set to true and enableDate set to false. NOTE: DateTimeInput does not support a label property in A2UI v0.9, so you must place a separate Text component above it to act as its label. Example: {"component": "DateTimeInput", "id": "time_picker", "enableTime": true, "enableDate": false}

15. BUTTON ALIGNMENT IN LISTS (Flexbox Symmetry) 
When designing a list item (like a Row) containing text on the left and an action button on the right, you MUST make the layout symmetrical by pushing the button to the far right edge. You achieve this by wrapping the text in a Column and adding "weight": 1 to that Column. This makes the text column fill the empty space. Example: {"component": "Column", "id": "text_col", "weight": 1, "children": [...]}

16. STATELESS CHAT BUG (Fixes LLM hallucinating fallback UIs or ignoring tools)
- If the backend creates a brand new `chat` session (e.g., `genai_client.chats.create(...)`) for every single HTTP request, the LLM loses all memory of the conversation. 
- Solution: Maintain persistent chat sessions across requests. 
- The generated `server.py` MUST contain the `active_sessions = {}` dictionary and `session_id` logic to maintain conversation history across button clicks!

17. PROMPT ENGINEERING FOR TOOL CALLS (Fixes LLM skipping tool execution)
- System prompts that heavily command the LLM to output text or provide comprehensive JSON examples might make the LLM think it doesn't need to use the tool.
- Solution: Explicitly inject overriding instructions in the agent's prompt to force tool execution first.

18. THE @TOOL DECORATOR
- Do NOT import `@tool` from `google.adk.tools`. When using `genai_client.chats.create(...)`, you must pass raw, undecorated Python functions directly into the `tools=[...]` array.

19. DROPDOWN MENUS (ChoicePicker)
A2UI v0.9 has NO <select> component. For any dropdown / "pick one from a list" UI you MUST use `ChoicePicker`.
- `options` MUST be a literal JSON array of {"label": "...", "value": "..."} objects. It can NEVER be a "${...}" string.
- `variant` is "mutuallyExclusive" for single-select (default) or "multipleSelection" for multi-select.
- `value` MUST be bound: "value": {"path": "/application/your_field"}
- The frontend writes a string ARRAY to that path (e.g. ["alice_martin"]) even for single-select.
  Therefore any tools.py function receiving it MUST normalize: `if isinstance(x, list): x = x[0] if x else ""`
- CRITICAL: annotate that parameter as plain `str`, NEVER `str | List[str]` or any
  union containing a subscripted generic. ADK runs isinstance() against the annotation,
  and `isinstance(["x"], str | List[str])` raises
  "TypeError: Subscripted generics cannot be used with class and instance checks".
  Declare `category: str` and do the list normalization inside the function body.

CORRECT:
{"component": "ChoicePicker", "id": "doc", "label": "Select a Doctor", "variant": "mutuallyExclusive",
 "options": [{"label": "Dr. Alice", "value": "alice"}, {"label": "Dr. Bob", "value": "bob"}],
 "value": {"path": "/application/doctor"}}
20. COMPONENT VARIANTS
`variant` is a strict enum per component. NEVER invent values, and NEVER borrow
Material Design names such as "outlined", "contained", "filled", "elevated", or "tonal".
The ONLY legal values are:
- Text:          h1, h2, h3, h4, h5, caption, body
- Button:        default, primary, borderless   (use "borderless" for secondary/cancel actions)
- TextField:     longText, number, shortText, obscured
- ChoicePicker:  multipleSelection, mutuallyExclusive
- Image:         icon, avatar, smallFeature, mediumFeature, largeFeature, header
If unsure, OMIT the variant property entirely - every component has a sane default.

=========================================
"""

# Rule 20 is generated from the live catalog enum rather than hand-written, so
# the allow-list can never drift from the installed spec.
#
# This rule was missing entirely: the icon allow-list lived only in
# A2UI_BOILERPLATE_PROMPT (which is injected into the GENERATED agent), so the
# Coder writing the JSON templates had never been told which names are legal.
A2UI_STRICT_RULES += (
    "\n20. ICON NAMES (Fixes \"Field validation failed for component 'Icon': name: Invalid input\")\n"
    "The `Icon` component's `name` MUST be one of the catalog's camelCase names.\n"
    "Material Design snake_case names DO NOT EXIST in A2UI and will crash the React\n"
    "frontend and render a broken glyph in Angular.\n"
    'INCORRECT: "calendar_month", "medical_services", "play_arrow", "check_circle", "local_hospital"\n'
    'CORRECT:   "calendarToday", "favorite", "play", "check", "accountCircle"\n'
    "The COMPLETE list of valid names - you MUST pick from these and nothing else:\n"
    + ", ".join(sorted(VALID_ICON_NAMES))
    + "\nIf no icon fits your domain exactly, choose the closest generic one\n"
    '(e.g. "info", "check", "star", "event"). NEVER invent a name.\n'
    "=========================================\n"
)


def extract_file_content(response_text, filename):
    pattern = f"<file name=\"{filename}\">(.*?)</file>"
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def extract_folder_name(response_text, template_dir=None):
    """Extract <folder_name>. Falls back to FALLBACK_AGENT_NAME on anything unsafe."""
    match = re.search(r"<folder_name>(.*?)</folder_name>", response_text, re.DOTALL)
    raw = match.group(1).strip() if match else ""

    # Must be plain snake_case: blocks ".", "..", "../Meta_agent", "/etc", ".hidden"
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,49}", raw):
        print(f"⚠️  Invalid or missing <folder_name> (got: '{raw}').")
        print(f"   Falling back to '{FALLBACK_AGENT_NAME}'.")
        return FALLBACK_AGENT_NAME

    # Never let the LLM target a directory we cannot afford to lose.
    # set(...) copies, so we never mutate the module-level constant.
    reserved = set(RESERVED_DIR_NAMES)
    if template_dir:
        reserved.add(template_dir)

    if raw in reserved:
        print(f"⚠️  '{raw}' is a reserved directory name - refusing to overwrite it.")
        print(f"   Falling back to '{FALLBACK_AGENT_NAME}'.")
        return FALLBACK_AGENT_NAME

    return raw


def welcome_view_enabled(*texts):
    """The welcome view is ALWAYS on unless the Planner recorded an explicit opt-out.

    The user's wish still wins, but it travels as a single deterministic sentinel
    (<WELCOME_VIEW>off</WELCOME_VIEW>) instead of relying on three LLMs agreeing.
    """
    for text in texts:
        if not text:
            continue
        match = re.search(r"<WELCOME_VIEW>\s*(\w+)\s*</WELCOME_VIEW>", text, re.IGNORECASE)
        if match and match.group(1).strip().lower() == "off":
            return False
    return True


PROMPT_BLOCK_NAMES = {"WELCOME_VIEW_BLOCK", "A2UI_BOILERPLATE_PROMPT", "VISUAL_COMPONENTS_BLOCK"}

def build_generated_prompt(content, welcome_enabled):
    """Rebuild the Coder's prompt.py around the template's prompt_blocks.py.

    Whatever the Coder copied (block definitions, imports, its own
    "UI_DESCRIPTION = A2UI_BOILERPLATE_PROMPT + ..." line) is removed via the AST,
    then the shared blocks are imported and concatenated exactly once.
    """
    import ast

    tree = ast.parse(content)
    drop = set()
    for node in tree.body:
        remove = False
        if isinstance(node, ast.ImportFrom):
            remove = (node.module or "").endswith("prompt_blocks") or bool(
                {a.name for a in node.names} & PROMPT_BLOCK_NAMES)
        elif isinstance(node, ast.Assign):
            targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if targets & PROMPT_BLOCK_NAMES:
                remove = True
            elif "UI_DESCRIPTION" in targets:
                remove = any(isinstance(n, ast.Name) and n.id in PROMPT_BLOCK_NAMES
                             for n in ast.walk(node.value))
        if remove:
            drop.update(range(node.lineno, node.end_lineno + 1))
    lines = content.splitlines()
    body = "\n".join(l for i, l in enumerate(lines, 1) if i not in drop).strip()

    parts = ["A2UI_BOILERPLATE_PROMPT", "VISUAL_COMPONENTS_BLOCK"]
    if welcome_enabled:
        parts.append("WELCOME_VIEW_BLOCK")
    parts.append("UI_DESCRIPTION")
    return (
        "from .prompt_blocks import A2UI_BOILERPLATE_PROMPT, VISUAL_COMPONENTS_BLOCK, WELCOME_VIEW_BLOCK\n\n"
        + body
        + "\n\nUI_DESCRIPTION = (\n    " + "\n    + '\\n\\n' + ".join(parts) + "\n)\n"
    )


def _schema_errors(filename, parsed):
    """Validate one example with the SAME a2ui validator the generated server runs at startup."""
    import importlib
    import json
    import tempfile

    try:
        from a2ui.schema import common_modifiers, constants, manager
        utils = importlib.import_module(f"{TEMPLATE_DIR_NAME}.a2ui_utils")
    except Exception as exc:  # noqa: BLE001 - never block generation on tooling
        print(f"⚠️  Schema check skipped ({exc}).")
        return []
    tmp = tempfile.mkdtemp(prefix="a2ui_check_")
    try:
        with open(os.path.join(tmp, os.path.basename(filename)), "w") as f:
            json.dump(parsed, f)
        mgr = manager.A2uiSchemaManager(
            version=constants.VERSION_0_9,
            catalogs=[utils.get_catalog_config(examples_path=tmp)],
            schema_modifiers=[common_modifiers.remove_strict_validation],
        )
        mgr.generate_system_prompt(role_description="x", ui_description="x",
                                   include_schema=False, include_examples=True,
                                   validate_examples=True)
        return []
    except Exception as exc:  # noqa: BLE001
        return [f"{filename}: SCHEMA ERROR - {str(exc).split(': ', 1)[-1]}"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def validate_generated_code(response_text):
    """Deterministically validate the Coder's output. Returns a list of error strings.

    These are facts, not opinions, so they are checked in code rather than being
    delegated to the Critic LLM: a syntax error is a syntax error.
    """
    import ast
    import json

    errors = []

    for filename in ["prompt.py", "tools.py", "agent.py"]:
        content = extract_file_content(response_text, filename)
        if not content:
            errors.append(f"{filename}: MISSING - no <file name=\"{filename}\"> block was emitted.")
            continue
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```$", "", content).strip()
        try:
            ast.parse(content)
        except SyntaxError as exc:
            errors.append(
                f"{filename}: PYTHON SYNTAX ERROR on line {exc.lineno}: {exc.msg}. "
                f"Offending line: {(exc.text or '').strip()!r}"
            )

    prompt_src = extract_file_content(response_text, "prompt.py") or ""
    prompt_src = re.sub(r"^```[a-zA-Z]*\n", "", prompt_src)
    prompt_src = re.sub(r"\n```$", "", prompt_src).strip()
    try:
        assigned = {t.id for n in ast.parse(prompt_src).body if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name)}
        for name in ("ROLE_DESCRIPTION", "UI_DESCRIPTION"):
            if prompt_src and name not in assigned:
                errors.append(f"prompt.py: {name} is not defined.")
    except SyntaxError:
        pass  # already reported above

    json_files = [
        f for f in re.findall(r'<file name="([^"]+)">', response_text) if f.endswith(".json")
    ]
    if not json_files:
        errors.append("examples/v0_9/*.json: MISSING - no JSON template files were emitted.")

    for filename in json_files:
        content = extract_file_content(response_text, filename)
        if not content:
            continue
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```$", "", content).strip()
        try:
            parsed = json.loads(content)
        except ValueError as exc:
            errors.append(f"{filename}: INVALID JSON - {exc}")
            continue

        # Every A2UI message must carry "version": "v0.9"; the SDK's
        # validate_examples=True rejects the file (and the server won't boot).
        messages = parsed if isinstance(parsed, list) else [parsed]
        for idx, msg in enumerate(messages):
            if isinstance(msg, dict) and msg.get("version") != "v0.9":
                kind = next((k for k in msg if k != "version"), "message")
                errors.append(
                    f'{filename}: messages[{idx}] ({kind}) MISSING "version": "v0.9" '
                    f"- add it as a top-level key next to \"{kind}\"."
                )

        # Icon names must come from the catalog enum. LLMs habitually emit
        # Material Design snake_case ("calendar_month") instead of the
        # catalog's camelCase ("calendarToday"), which hard-fails the React
        # frontend and renders a broken glyph in Angular.
        for bad_name in _collect_invalid_icon_names(parsed):
            hint = _suggest_icon_name(bad_name)
            errors.append(
                f'{filename}: INVALID ICON NAME "{bad_name}" - not in the A2UI '
                f"catalog enum. Use {hint} instead. Valid names are camelCase, "
                f"never snake_case."
            )
        
        # Validate full A2UI Schema
        errors.extend(_schema_errors(filename, parsed))

        # Templates must stay responsive: `columns` is a runtime choice only.
        for node in _iter_components(parsed):
            if node.get("component") == "Grid" and "columns" in node:
                errors.append(f'{filename}: Grid "{node.get("id")}" sets "columns" - '
                              "remove it; example templates must stay responsive.")
            if node.get("component") != "Button" and "action" in node:
                errors.append(f'{filename}: {node.get("component")} "{node.get("id")}" has '
                              '"action" - only Button supports action.')


    return errors


def _iter_components(parsed):
    """Yield every component dict from every updateComponents message."""
    for msg in parsed if isinstance(parsed, list) else [parsed]:
        if isinstance(msg, dict):
            for comp in (msg.get("updateComponents") or {}).get("components", []):
                if isinstance(comp, dict):
                    yield comp


def _collect_invalid_icon_names(node, found=None):
    """Return every Icon `name` in the tree that is not in the catalog enum."""
    if found is None:
        found = []
    if isinstance(node, dict):
        if node.get("component") == "Icon":
            name = node.get("name")
            if isinstance(name, str) and name not in VALID_ICON_NAMES:
                found.append(name)
        for value in node.values():
            _collect_invalid_icon_names(value, found)
    elif isinstance(node, list):
        for value in node:
            _collect_invalid_icon_names(value, found)
    return found


def _suggest_icon_name(bad_name):
    """Best-effort nearest valid icon name, so the retry is a one-token fix."""
    import difflib

    # "calendar_month" -> "calendarMonth" catches most snake_case mistakes.
    head, *rest = bad_name.split("_")
    camel = head + "".join(part.capitalize() for part in rest)

    for candidate in (camel, head):
        if candidate in VALID_ICON_NAMES:
            return f'"{candidate}"'

    close = difflib.get_close_matches(camel, sorted(VALID_ICON_NAMES), n=3, cutoff=0.5)
    if not close:
        close = difflib.get_close_matches(head, sorted(VALID_ICON_NAMES), n=3, cutoff=0.4)
    if close:
        return "one of " + ", ".join(f'"{c}"' for c in close)
    return 'a valid name such as "info", "check" or "star"'

END_MARKER = "END"

def read_multiline(prompt_text=""):
    """Read lines until a line containing only END (or Ctrl-D).

    Blank lines are kept, so a pasted prompt with paragraphs arrives as ONE message.
    """
    if prompt_text:
        print(prompt_text)
    print(f"  (paste freely; finish with a line containing only {END_MARKER}, or Ctrl-D)")
    lines = []
    while True:
        try:
            line = input("> " if not lines else "  ")
        except EOFError:
            break
        if line.strip() == END_MARKER:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def find_template_dir():
    """Locate the golden template. Fails loudly instead of guessing."""
    if os.path.isdir(TEMPLATE_DIR_NAME) and os.path.exists(
        os.path.join(TEMPLATE_DIR_NAME, "agent.py")
    ):
        return TEMPLATE_DIR_NAME
    
    print(f"\n❌ FATAL: Could not find the golden template '{TEMPLATE_DIR_NAME}/'.")
    sys.exit(1)

def main():
    print("==================================================")
    print("🚀 Welcome to the 3-Stage Dynamic A2UI Meta-Agent! 🚀")
    print("==================================================")
    
    template_dir = find_template_dir()
    if not template_dir:
        print("❌ Error: Could not find template.")
        sys.exit(1)
        
    print(f"✅ Found template directory: {template_dir}")
    
    # ----------------------------------------------------------------
    # STAGE 1: PLANNER
    # ----------------------------------------------------------------
    print("\n--- STAGE 1: PLANNER ---")
    print("I will help you design your A2UI Agent. Let's discuss your requirements.")
    
    # --- Auth: Vertex AI or direct Gemini API, both configured via .env -------
    # NOTE: no credential value is ever read from this source file. The SDK picks
    # up GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION / ADC for Vertex, or the
    # API key for direct mode - all of it from your .env.
    use_vertex = os.environ.get(VERTEX_FLAG_ENV_VAR, "").strip().lower() in (
        "1", "true", "yes",
    )
    api_key = os.environ.get(API_KEY_ENV_VAR)

    if use_vertex:
        project = os.environ.get(VERTEX_PROJECT_ENV_VAR)
        location = os.environ.get(VERTEX_LOCATION_ENV_VAR)
        if not project:
            print(f"\n❌ FATAL: {VERTEX_FLAG_ENV_VAR} is enabled but "
                  f"{VERTEX_PROJECT_ENV_VAR} is not set in your .env.")
            sys.exit(1)
        print(f"🔐 Auth: Vertex AI (project from {VERTEX_PROJECT_ENV_VAR}, "
              f"location: {location or 'SDK default'})")
        # Let the SDK read project/location/ADC from the environment itself.
        client = Client()
    elif api_key:
        print(f"🔐 Auth: Gemini API key (from {API_KEY_ENV_VAR})")
        client = Client(api_key=api_key)
    else:
        print(f"\n❌ FATAL: no credentials found in your environment/.env.")
        print(f"   Either set {API_KEY_ENV_VAR}=... for direct Gemini API access,")
        print(f"   or set {VERTEX_FLAG_ENV_VAR}=true together with "
              f"{VERTEX_PROJECT_ENV_VAR}=... for Vertex AI.")
        sys.exit(1)

    # planner_instruction = "You are the Planner Agent. Ask the user 1 or 2 clarifying questions about their agent idea to gather detailed requirements for tools and UI. Once you have a clear plan, end your message with exactly the phrase '<PLAN_READY>'. Keep your responses very short."
    planner_instruction = """You are the Planner Agent. Your job is to gather requirements and design the user flow.
    1. First, analyze the user's app idea and proactively propose a UI flow for it, adapting the DEFAULT REFERENCE FLOW below to their domain. Do not make the user design it from scratch.
    2. The proposed flow MUST always start with a "Welcome / Capabilities" step, because every generated agent opens by introducing itself and showing one suggested starter prompt.
    3. Present this proposed flow to the user using a clear ASCII flowchart drawn with pure text characters (e.g. +---, |, ->). DO NOT use Mermaid syntax (```mermaid) or any other markdown diagram language. Only use raw ASCII text.
    4. Ask the user if they approve of this flow or if they want to make changes.
    5. DO NOT output <PLAN_READY> in your first response.
    6. Wait for the user to answer.
    7. Apply the FLOW PRECEDENCE POLICY below on every turn: the user's explicit instruction always beats the default flow, but anything vague, missing, or ambiguous falls back to the default flow rather than a question or an invention.
    8. The Welcome / Capabilities step is ON by default and you must keep it. ONLY if the user EXPLICITLY asks to remove it (e.g. "no welcome screen", "skip the intro", "don't show capabilities"), you MUST include the exact sentinel tag <WELCOME_VIEW>off</WELCOME_VIEW> in your final summary message. Never emit this tag otherwise, and never mention it to the user.
    9. Once the user approves the flow and you have a complete understanding, summarize the final plan - including the exact wording of the single suggested starter prompt - and then end your message with exactly the phrase '<PLAN_READY>'.
    10. Whenever the user requests ANY change, you MUST redraw the COMPLETE updated ASCII flowchart (every view, every arrow, including the ones that did not change) and ask for approval again. Never answer a change request with a text summary only, and do NOT output <PLAN_READY> in that message.
    11. Output <PLAN_READY> only after the user approves the latest flowchart. That final message MUST contain the final ASCII flowchart first, then the plan summary, then <PLAN_READY>.
""" + FLOW_PRECEDENCE_RULES
    chat = client.chats.create(model=PLANNER_MODEL, config={"system_instruction": planner_instruction})
    
    # app_idea = input("What kind of agent do you want to build?:\n> ")
    # if not app_idea.strip():
    #     sys.exit(1)
    
    # Accept the idea from argv (Node CLI passes it) and fall back to a prompt
    # for standalone `python root_agent.py` usage.
    # if len(sys.argv) > 1 and sys.argv[1].strip():
    #     app_idea = sys.argv[1].strip()
    #     print(f"What kind of agent do you want to build?:\n> {app_idea}")
    # else:
    #     app_idea = read_multiline("What kind of agent do you want to build?:")

    arg = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if arg and os.path.isfile(arg):
        with open(arg, "r") as f:
            app_idea = f.read().strip()
        print(f"What kind of agent do you want to build?:\n(loaded {len(app_idea)} chars from {arg})")
    elif arg:
        app_idea = arg
        print(f"What kind of agent do you want to build?:\n> {app_idea}")
    else:
        app_idea = read_multiline("What kind of agent do you want to build?:")


    response = chat.send_message(app_idea)
    planner_transcript = response.text
    while True:
        print(f"\n[Planner Agent]: {response.text}")
        # a code guard so a missing diagram can never slip through
        if "<PLAN_READY>" in response.text:
            if re.search(r"\+-{3,}", response.text):
                break
            # Final plan without a flowchart: ask once more, deterministically.
            response = chat.send_message(
                "Your final plan is missing the ASCII flowchart. Reply again with the COMPLETE "
                "final flowchart, then the summary, then <PLAN_READY>."
            )
            planner_transcript += "\n" + response.text
            continue
        user_reply = read_multiline()
        response = chat.send_message(user_reply)
        planner_transcript += "\n" + response.text

    # The welcome view is ON unless the Planner recorded an explicit opt-out.
    welcome_enabled = WELCOME_VIEW_ENABLED and welcome_view_enabled(planner_transcript)
    if welcome_enabled:
        print("\n✅ Welcome/Capabilities view: ENABLED (default).")
    else:
        print("\n⚠️  Welcome/Capabilities view: DISABLED by explicit user request.")

    # ----------------------------------------------------------------
    # STAGE 2: CODER
    # ----------------------------------------------------------------
    print("\n--- STAGE 2: CODER ---")
    print("Generating code based on the finalized plan...")
    
    with open(os.path.join(template_dir, "agent.py"), "r") as f:
        template_agent = f.read()

    with open(os.path.join(template_dir, "prompt.py"), "r") as f:
        template_prompt = f.read()
        
    with open(os.path.join(template_dir, "tools.py"), "r") as f:
        template_tools = f.read()

    import glob
    json_files = glob.glob(os.path.join(template_dir, "examples", "v0_9", "*.json"))
    template_json = ""
    for jf in json_files:
        with open(jf, "r") as f:
            template_json += f"\n=== {os.path.basename(jf)} ===\n" + f.read() + "\n"

    # Shared runtime rules + viz helper, so the Coder/Critic know the Table /
    # Chart / VegaChart / Google-map rules the generated agent receives.
    template_blocks = {}
    with open(os.path.join(template_dir, "prompt_blocks.py"), "r") as f:
        exec(f.read(), template_blocks)
    visual_rules = (
        "\n=== DATA VISUALISATION COMPONENTS (ALLOWED - the generated agent receives these rules automatically) ===\n"
        + template_blocks["VISUAL_COMPONENTS_BLOCK"]
        + "\n- REQUIRED FIELDS: to keep a submit Button disabled until a form is valid, use a `checks` array exactly like `discount_form_view.json`. NEVER emit `disabled` on a Button.\n"
    )
    with open(os.path.join(template_dir, "viz.py"), "r") as f:
        template_viz = f.read()

    coder_instruction = """You are the Coder Agent.
Read the user's conversation history (the plan). Generate the Python code for an A2UI backend.
You must output exactly five things: a folder name, and at least four files (`prompt.py`, `tools.py`, `agent.py`, and one or more `.json` templates).

1. Define the folder name wrapped in tags: <folder_name>insert_agent_name_here</folder_name> (use snake_case, derived from the agent's purpose)
2. Wrap the content of EACH file in XML tags: <file name="prompt.py">print('hello')</file>
3. For JSON templates, use the path `examples/v0_9/your_template_name.json`: <file name="examples/v0_9/main_view.json">{ ... }</file>

""" + A2UI_STRICT_RULES + visual_rules + """

CRITICAL INSTRUCTIONS FOR JSON TEMPLATES:
- **ANTI-HALLUCINATION RULE:** Do NOT rely on your pre-trained web development knowledge to invent JSON layouts. You MUST strictly model your new JSON files after the structural format of standard A2UI v0.9 templates. While your content/use-case will change, the exact schema, component naming, and allowed properties must remain identical to the spec.
- You MUST design perfectly flat JSON arrays matching the A2UI v0.9 `updateComponents` specification defined in the rules above.
- You MUST ensure all components (especially Buttons, TextFields, and CheckBoxes) strictly follow the structural rules above

CRITICAL INSTRUCTIONS FOR prompt.py:
- Define `ROLE_DESCRIPTION` as a string.
- Define `UI_DESCRIPTION` as a raw string (r\"\"\").
- In `UI_DESCRIPTION`, you MUST provide strict English bullet points instructing the child agent on exactly how to use your provided JSON templates!
- `UI_DESCRIPTION` MUST contain a numbered "**UI Flow:**" section whose STEP 1 is the mandatory Welcome View specified below, followed by the remaining steps of the approved plan.
- You MUST explicitly explain what every Button does, which backend tool it calls, and how the form fields (e.g. text fields, date inputs, radio buttons) map to the tool's arguments via data binding paths.
- Example: "The 'Submit' button MUST have an `action` property that calls the `book_flight` tool. The parameters (`destination`, `date`) MUST be bound to the data paths of the form fields: `\"action\": {\"event\": {\"name\": \"book_flight\", \"context\": {\"destination\": {\"path\": \"/form/dest\"}}}`."
- **CRITICAL:** You MUST explicitly command the agent: "When an event is triggered, you MUST FIRST call the Python tool. Only after the tool returns successfully, you MUST render the new surface."
- DO NOT output the massive 'CRITICAL OUTPUT FORMAT' boilerplate.
- DO NOT define or import `A2UI_BOILERPLATE_PROMPT`, `VISUAL_COMPONENTS_BLOCK` or `WELCOME_VIEW_BLOCK`, and DO NOT write the final `UI_DESCRIPTION = (...)` concatenation - the generator adds them from `prompt_blocks.py`. Define ONLY `ROLE_DESCRIPTION` and your own `UI_DESCRIPTION = r\"\"\"...\"\"\"`.

CRITICAL INSTRUCTIONS FOR tools.py:
- Write ONE python function per data view or action in the approved plan (typically 3-8), each with a clear docstring. Keep mock data as module-level constants in tools.py.
- For visuals, `from . import viz` and follow the template tools.py exactly: `viz.save_chart(rows, ...)` -> return `plot_path` (VegaChart); `viz.save_google_map(points)` -> return `map_path` only when it is not None, and ALWAYS also return `plot_path` from `viz.save_map(points, ...)` as the key-less fallback; `Table`/`Chart` tools return `rows` (a list of flat dicts). Catch `ValueError` from viz and return `{"status": "error", "error": str(exc)}`.
- A save tool for an editable `Table` takes `rows: list[dict]`, validates it and returns what changed.
- Python tools MUST NOT use strict date parsing like `date.fromisoformat()` if accepting dates from `DateTimeInput`. Extract the date robustly using `from_date[:10]` or `datetime.fromisoformat()`.
- DO NOT use the `@tool` decorator or import it. Write raw python functions.

CRITICAL INSTRUCTIONS FOR agent.py:
- Take the provided template below and ONLY change the `tools=[...]` array to match your new tools, and remove `from . import well_logs` if none of your tools come from it. Leave all else exactly as is.

=========================================
""" + WELCOME_VIEW_SPEC + FLOW_PRECEDENCE_RULES + """
=========================================


=== EXAMPLES TO STRICTLY COPY FROM ===

--- agent.py TEMPLATE ---
""" + template_agent + """

--- tools.py TEMPLATE ---
""" + template_tools + """

--- viz.py (READ-ONLY helper already in the package - use it with `from . import viz`, NEVER re-emit it) ---
""" + template_viz + """

--- prompt.py TEMPLATE ---
""" + template_prompt + """

--- JSON TEMPLATES (STRICT STRUCTURAL REFERENCE) ---
""" + template_json + """
=========================
"""
    
    # Serialize the chat history to pass to the coder
    history_text = "\n".join([f"{msg.role}: {msg.parts[0].text}" for msg in chat.get_history()])
    prompt = f"Plan History:\n{history_text}\n\nGenerate the folder name and modify the 4 files."
    
    coder_response = client.models.generate_content(
        model=CODER_MODEL,
        contents=prompt,
        config={"system_instruction": coder_instruction}
    )
    
    generated_code = coder_response.text

    # ----------------------------------------------------------------
    # STAGE 3: CRITIC
    # ----------------------------------------------------------------
    print("\n--- STAGE 3: CRITIC ---")
    print("Validating the generated code for A2UI faults...")

    critic_instruction = """You are the Critic Agent. Your job is to review the code generated by the Coder Agent.
You MUST evaluate the code against EVERY SINGLE ITEM in the checklist below, in order. Do not stop at the first error! Write down a step-by-step analysis for EACH numbered checklist item (there are 19). If ANY rules were broken, output <FAIL> at the very end of your response, followed by the complete compiled list of ALL errors found.
You must specifically check `prompt.py` and the JSON templates for A2UI hallucinations based on these strict rules:

""" + A2UI_STRICT_RULES + visual_rules + """

CRITICAL INSTRUCTIONS FOR JSON TEMPLATES:
- You MUST design perfectly flat JSON arrays matching the A2UI v0.9 `updateComponents` specification defined in the rules above.
- You MUST ensure all components (especially Buttons, TextFields, and CheckBoxes) strictly follow the structural rules above.

CRITICAL INSTRUCTIONS FOR prompt.py:
- Define `ROLE_DESCRIPTION` as a string.
- Define `UI_DESCRIPTION` as a raw string (r\"\"\").
- In `UI_DESCRIPTION`, you MUST provide strict English bullet points instructing the child agent on exactly how to use your provided JSON templates!
- You MUST explicitly explain what every Button does, which backend tool it calls, and how the form fields (e.g. text fields, date inputs, radio buttons) map to the tool's arguments via data binding paths.
- Example: "The 'Submit' button MUST have an `action` property that calls the `book_flight` tool. The parameters (`destination`, `date`) MUST be bound to the data paths of the form fields: `\"action\": {\"event\": {\"name\": \"book_flight\", \"context\": {\"destination\": {\"path\": \"/form/dest\"}}}`."
- **CRITICAL:** You MUST explicitly command the agent: "When an event is triggered, you MUST FIRST call the Python tool. Only after the tool returns successfully, you MUST render the new surface."
- **CRITICAL:** Make sure you write robust backend tools in `tools.py` without using `Annotated` or `Dict`, and properly connect all the buttons and form fields to the tools!
- DO NOT output the massive 'CRITICAL OUTPUT FORMAT' boilerplate.

CRITICAL INSTRUCTIONS FOR tools.py:
- Write ONE python function per data view or action in the approved plan (typically 3-8), each with a clear docstring. Keep mock data as module-level constants in tools.py.
- For visuals, `from . import viz` and follow the template tools.py exactly: `viz.save_chart(rows, ...)` -> return `plot_path` (VegaChart); `viz.save_google_map(points)` -> return `map_path` only when it is not None, and ALWAYS also return `plot_path` from `viz.save_map(points, ...)` as the key-less fallback; `Table`/`Chart` tools return `rows` (a list of flat dicts). Catch `ValueError` from viz and return `{"status": "error", "error": str(exc)}`.
- A save tool for an editable `Table` takes `rows: list[dict]`, validates it and returns what changed.
- Python tools MUST NOT use strict date parsing like `date.fromisoformat()` if accepting dates from `DateTimeInput`. Extract the date robustly using `from_date[:10]` or `datetime.fromisoformat()`.
- DO NOT use the `@tool` decorator or import it. Write raw python functions.

CRITICAL INSTRUCTIONS FOR agent.py:
- Take the provided template below and ONLY change the `tools=[...]` array to match your new tools, and remove `from . import well_logs` if none of your tools come from it. Leave all else exactly as is.
- **WELCOME VIEW IS REQUIRED:** One of your emitted JSON files MUST be
  `examples/v0_9/welcome_view.json`, modeled directly on the `=== welcome_view.json ===`
  golden example provided below, rewritten for this agent's domain.
==============================

Checklist to FAIL the coder:
1. Did the Coder invent components that don't exist? (Only Card, Column, Row, Text, Icon, Divider, Button, TextField, CheckBox, DateTimeInput, Image, ChoicePicker, Table, Chart, VegaChart are allowed). (FAIL if others exist).
2. Did the Coder nest components inside `createSurface.layout` instead of using a flat `updateComponents` array? (FAIL if yes).
3. Did the Coder use `"text"` or `"label"` on a Button instead of `"child"`? (FAIL if yes).
4. Did the Coder instruct the use of 'spacing' or 'gap' on a Column or Row? (FAIL if yes).
5. Did the Coder instruct the use of `on_click` or `on_change` on any component? (FAIL if yes. Components only use `action`).
6. Did the Coder omit explicit English instructions in `prompt.py` explaining exactly which tools the buttons trigger and what data paths they map to? (FAIL if omitted).
7. Did the Coder use strict date parsing like `date.fromisoformat()` in `tools.py` instead of slicing `[:10]` or using `datetime`? (FAIL if yes).
8. Did the Coder instruct the use of an `action` on a Button? If yes, verify that it strictly follows the `{"event": {"name": "...", "context": ...}}` wrapper. (FAIL if it omits the event wrapper, like `{"tool": "..."}`).
9. If the UI is being dynamically updated/redrawn, did the Coder explicitly instruct the child agent to emit three mutations in order: `deleteSurface` (old id), `createSurface` (new id), and `updateComponents` (new id)? (FAIL if it reused surface IDs across turns).
10. Did the Coder include an input component (like TextField or DateTimeInput)? If yes, verify that it has a `"value": {"path": "..."}` property. (FAIL if the value property is missing).
11. Did the Coder hallucinate a `"props"` object inside any component? (FAIL if `"props"` exists. All layout/styling properties must be at the root of the component).
12. If the Coder included a TextField, did it use `"label"` instead of `"placeholder"`? (FAIL if `"placeholder"` is used).
13. Did the Coder hallucinate `padding`, `margin`, `spacing`, or `gap` on any component? (FAIL if yes, these do not exist).
14. **TEMPLATE COMPARISON:** Did the Coder modify anything in `agent.py` OTHER than the `tools=[...]` array (and removing an unused `well_logs` import)? (FAIL if they modified the boilerplate).
15. **STRUCTURE AUDIT:** Review the generated `examples/v0_9/*.json` files. While the *use-case* is unique, is the underlying structure, component naming (TitleCase), and strict property usage identical to the A2UI spec? Did they hallucinate CSS properties, wrapper objects, or unapproved keys? (FAIL if yes).
16. **DROPDOWN MENUS (ChoicePicker)**
A2UI v0.9 has NO <select> component. For any dropdown / "pick one from a list" UI you MUST use `ChoicePicker`.
- `options` MUST be a literal JSON array of {"label": "...", "value": "..."} objects. It can NEVER be a "${...}" string.
- `variant` is "mutuallyExclusive" for single-select (default) or "multipleSelection" for multi-select.
- `value` MUST be bound: "value": {"path": "/application/your_field"}
- The frontend writes a string ARRAY to that path (e.g. ["alice_martin"]) even for single-select.
  Therefore any tools.py function receiving it MUST normalize: `if isinstance(x, list): x = x[0] if x else ""`
- CRITICAL: annotate that parameter as plain `str`, NEVER `str | List[str]` or any
  union containing a subscripted generic. ADK runs isinstance() against the annotation,
  and `isinstance(["x"], str | List[str])` raises
  "TypeError: Subscripted generics cannot be used with class and instance checks".
  Declare `category: str` and do the list normalization inside the function body.

CORRECT:
{"component": "ChoicePicker", "id": "doc", "label": "Select a Doctor", "variant": "mutuallyExclusive",
 "options": [{"label": "Dr. Alice", "value": "alice"}, {"label": "Dr. Bob", "value": "bob"}],
 "value": {"path": "/application/doctor"}}

17. **WELCOME VIEW FILE EMITTED:** Is there a `<file name="examples/v0_9/welcome_view.json">`block? Does its structure match the golden `welcome_view.json` example (root Column -> welcome_card -> welcome_content; title; subtitle; Divider; 3-5 capability Rows each with an Icon + Text; Divider; "Try saying:" label; exactly ONE starter Row)? (FAIL if the file is missing or the structure deviates).
18. **WELCOME VIEW CONTENT + WIRING:** Are the 3-5 capabilities real, tool-derived actions (not filler), and is there EXACTLY ONE concrete domain-specific starter prompt (not "Get started"/"Help")? Does `UI_DESCRIPTION` make this STEP 1, rendering ONLY this card on the first turn with NO tool call, then waiting for the user? (FAIL if any are missing).
19. **ICON NAMES:** Are ALL `Icon` `name` values camelCase entries from the catalog list in Rule 20? (FAIL on any snake_case such as `check_circle` or `play_arrow`).
20. **MESSAGE VERSION:** Does EVERY top-level message object in EVERY `examples/v0_9/*.json` file contain `"version": "v0.9"`? (FAIL if any `createSurface` / `updateComponents` / `updateDataModel` message is missing it).
21. **VISUALS WIRING:** For every `Table`/`Chart`, is the data sent in an `updateDataModel` BEFORE `updateComponents` and bound as `{"path": "/<name>/rows"}` (never inlined)? Is every `VegaChart` `spec` and every map `Image` `url` exactly `{"path": "/plots/..."}`, backed by a tool that returns `plot_path` / `map_path` from `viz`? Does every submit Button that needs required fields use `checks` (never `disabled`)? (FAIL if not).
22. **GRID / MODAL / TABS:** Does every `Grid` use a template `{"componentId", "path"}` with RELATIVE bindings inside, and NO `columns` in the example files? Is every `Modal` referenced by a parent (inside a Grid it must live IN the item template, in place of its trigger), with a non-Button trigger, and does ONLY `Button` carry `action`? Does every `Tabs` `child` id exist in the same `updateComponents`? (FAIL if not).
""" + WELCOME_VIEW_SPEC + """

If the code is PERFECT, reply with EXACTLY '<PASS>'.
If the code has errors, reply with '<FAIL>' followed by a detailed list of what needs to be fixed.

=== BASELINE A2UI TEMPLATE EXAMPLES TO COMPARE AGAINST ===
""" + template_json + """
"""
    retries = 0
    while retries < MAX_RETRIES:
        # -- Gate 1: deterministic checks (free, exact). A syntax error is a fact,
        # so don't pay an LLM to have an opinion about it.
        hard_errors = validate_generated_code(generated_code)
        if hard_errors:
            retries += 1
            print("\n❌ Deterministic validation failed:")
            for err in hard_errors:
                print(f"   - {err}")
            if retries >= MAX_RETRIES:
                print(f"\n❌ Still invalid after {MAX_RETRIES} attempts. Aborting before writing anything.")
                sys.exit(1)

            print(f"\n   Sending back to Coder to fix (Attempt {retries}/{MAX_RETRIES})...")
            correction_prompt = (
                "Your output failed automated validation with these EXACT errors:\n"
                + "\n".join(f"- {e}" for e in hard_errors)
                + "\n\nRegenerate ALL files, fixing these errors. Emit every file in full."
            )
            coder_response = client.models.generate_content(
                model=CODER_MODEL,
                contents=[prompt, coder_response.text, correction_prompt],
                config={"system_instruction": coder_instruction}
            )
            generated_code = coder_response.text
            continue

        # -- Gate 2: the Critic (judgement calls the validator cannot make)
        critic_response = client.models.generate_content(
            model=CRITIC_MODEL,
            contents=f"Review this generated code:\n\n{generated_code}",
            config={"system_instruction": critic_instruction}
        )

        print(f"\n[Critic Agent]:\n{critic_response.text}")

        if "<FAIL>" in critic_response.text:
            retries += 1
            if retries >= MAX_RETRIES:
                print(f"\n❌ Critic rejected the code, but max retries ({MAX_RETRIES}) reached! Writing files anyway...")
                break
                
            print(f"\n❌ Critic rejected the code! Sending back to Coder to fix (Attempt {retries}/{MAX_RETRIES})...")
            correction_prompt = f"The Critic found errors in your code:\n{critic_response.text}\n\nPlease regenerate all files fixing these errors."
            coder_response = client.models.generate_content(
                model=CODER_MODEL,
                contents=[prompt, coder_response.text, correction_prompt], 
                config={"system_instruction": coder_instruction}
            )
            generated_code = coder_response.text
            print("\n[Coder Agent]: Code regenerated. Resubmitting to Critic...")
        else:
            print("\n✅ Critic approved the code!")
            break

    # ----------------------------------------------------------------
    # FILE WRITING (COPY WHOLE FOLDER, OVERWRITE 4 FILES)
    # ----------------------------------------------------------------
    text = generated_code
    output_dir = extract_folder_name(text, template_dir)

    # ----------------------------------------------------------------
    # PRE-FLIGHT VALIDATION - hard-fail BEFORE touching the filesystem
    # ----------------------------------------------------------------
    REQUIRED_FILES = ["prompt.py", "tools.py", "agent.py"]
    generated_json_files = [
        f for f in re.findall(r'<file name="([^"]+)">', text) if f.endswith(".json")
    ]
    missing = [fn for fn in REQUIRED_FILES if not extract_file_content(text, fn)]
    if missing:
        print(f"\n❌ FATAL: The Coder Agent did not emit these required files: {missing}")
        print("   If we continued, the copied template's files would silently survive")
        print("   (e.g. your new agent would ship with the pizza-ordering tools).")
        print("   Aborting. Nothing was written or deleted.")
        sys.exit(1)
    if not generated_json_files:
        print("\n❌ FATAL: The Coder Agent emitted no examples/v0_9/*.json templates.")
        print("   Aborting. Nothing was written or deleted.")
        sys.exit(1)
    print(f"\n✅ Pre-flight OK: {', '.join(REQUIRED_FILES)} "
          f"+ {len(generated_json_files)} JSON template(s) found.")

    # ----------------------------------------------------------------
    # FILE WRITING
    # ----------------------------------------------------------------
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    print(f"\n✅ Copying full template directory to '{output_dir}'...")
    shutil.copytree(template_dir, output_dir)
    
    print("✅ Deleting old JSON templates from the copied directory...")
    examples_dir = os.path.join(output_dir, "examples", "v0_9")
    if os.path.exists(examples_dir):
        import glob
        for f in glob.glob(os.path.join(examples_dir, "*.json")):
            os.remove(f)
            
    print(f"✅ Injecting modified files...")
    for filename in ["prompt.py", "tools.py", "agent.py"] + [f for f in re.findall(r'<file name="([^"]+)">', text) if f.endswith(".json")]:
        content = extract_file_content(text, filename)
        if content:
            # Strip markdown code blocks if the LLM included them inside the tags
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
            content = content.strip()
            
            # if filename == "prompt.py":
            #     # The Coder sees the template prompt.py (which already defines the
            #     # boilerplate and the concat line) and often copies them verbatim.
            #     # Strip any copy so we never define it twice or prepend it twice.
            #     content = re.sub(
            #         r'^A2UI_BOILERPLATE_PROMPT\s*=\s*r?""".*?"""\s*',
            #         "",
            #         content,
            #         flags=re.DOTALL,
            #     )
            #     content = re.sub(
            #         r"^\s*UI_DESCRIPTION\s*=\s*A2UI_BOILERPLATE_PROMPT\s*\+.*$",
            #         "",
            #         content,
            #         flags=re.MULTILINE,
            #     )
            #     content = content.strip()
            if filename == "prompt.py":
                content = build_generated_prompt(content, welcome_enabled)
            file_path = os.path.join(output_dir, filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:

                f.write(content)
            print(f"  -> Successfully updated {filename}")
    
    # ----------------------------------------------------------------
    # 1. Manually patch config.py using Regex (Works with ANY template)
    # ----------------------------------------------------------------
    config_path = os.path.join(output_dir, "config.py")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_text = f.read()
            
        agent_title = output_dir.replace("_", " ").title()
        
        # Safely overwrite id and name no matter what they previously were
        config_text = re.sub(r'agent_id:\s*str\s*=\s*"[^"]+"', f'agent_id: str = "{output_dir}"', config_text)
        config_text = re.sub(r'agent_name:\s*str\s*=\s*"[^"]+"', f'agent_name: str = "{agent_title}"', config_text)
        
        # Replace description (handles both single line and multi-line parenthesis formats)
        config_text = re.sub(r'agent_description:\s*str\s*=\s*\([^)]+\)', 'agent_description: str = "Generated A2UI Agent."', config_text)
        config_text = re.sub(r'agent_description:\s*str\s*=\s*"[^"]+"', 'agent_description: str = "Generated A2UI Agent."', config_text)
        
        with open(config_path, "w") as f:
            f.write(config_text)
        print("  -> Successfully dynamically patched config.py")

    # ----------------------------------------------------------------
    # 2. Frontend title
    # ----------------------------------------------------------------
    # Nothing to do. Both frontends read the agent name at runtime from
    # GET /api/agent/info, which is served straight from config.agent_name.
    # The frontends are generic shells and are never modified by the generator.

    print(f"\n🎉 DONE! Run: uv run uvicorn {output_dir}.server:app --reload --port 8080")

if __name__ == "__main__":
    main()
