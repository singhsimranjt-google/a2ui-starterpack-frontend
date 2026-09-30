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

A2UI_BOILERPLATE_PROMPT = r"""

### CRITICAL OUTPUT FORMAT & A2UI SPECIFICATION (MANDATORY):
- ALWAYS output your responses directly as text in the message body.
- When rendering A2UI components, ALWAYS output the JSON strictly as text enclosed within `<a2ui-json>...</a2ui-json>` XML tags.
- The JSON inside `<a2ui-json>...</a2ui-json>` MUST be a single valid JSON array `[ ... ]` containing `createSurface`, `updateComponents`, and `updateDataModel` messages, matching the exact syntax and component hierarchy from the provided example JSON templates.
- **MANDATORY TEMPLATE FIDELITY (Basic Catalog v0.9)**:
  - You MUST refer directly to the provided example JSON files in your system instructions when generating A2UI cards.
  - The `catalogId` in `createSurface` MUST strictly be `"https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"`.
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
- **ACTION PROMPT (MANDATORY)**: Every `Button` `action.event.context` MUST include a `"prompt"` key: ONE short past-tense sentence, written from the user's point of view, describing what they just did with real domain words (e.g. `"Submitted the bonus allocation for the selected employees."`, `"Selected the North America subregion."`). It is shown in the chat as the user's message. The `prompt` value is display text only - NEVER pass it as a tool argument.
- When the sentence should include values the user entered, make `prompt` a formatString call instead of a literal: `{"call": "formatString", "args": {"value": "Submitted a ${/application/budget} budget."}}`. Inside `value`, reference form fields ONLY as `${/absolute/path}` (the same paths bound to the inputs), optionally wrapped as `${formatCurrency(value:${/path}, currency:'USD')}` or `${formatDate(value:${/path}, format:'MMM d, yyyy')}`. Never use `${result...}` inside formatString.
- **REQUIRED FIELDS / DISABLED BUTTON**: To keep a submit `Button` disabled until the form is valid, give it a `checks` array (as in `discount_form_view.json`) using `length` (text / multi-select, `min`), `numeric` (numbers, `min`/`max`), `required`, `email` or `regex` on the bound field paths. NEVER emit a `disabled` property on a Button - it is not part of the catalog and the whole card will be rejected.

"""

VISUAL_COMPONENTS_BLOCK = r"""

### DATA VISUALISATION COMPONENTS (Table, Chart, VegaChart)
These three components are part of this catalog in addition to the basic ones. Pick by intent:

| User wants | Component | Tool must return | How to bind |
|---|---|---|---|
| a list of records / "table" / "list all" | `Table` | `rows` (list of flat dicts) | `updateDataModel` `{"path": "/<name>", "value": {"rows": <rows>}}`, then `"rows": {"path": "/<name>/rows"}` |
| a simple bar / line / area / point / pie chart of those rows | `Chart` | same `rows` | `"data": {"path": "/<name>/rows"}`, `x` and `y` are row keys |
| a rich interactive chart (multi-series, zoom, legend filter) | `VegaChart` | `plot_path` (from `viz.save_chart`) | `"spec": {"path": "<plot_path>"}` |
| locations / places / "where" / "map" (real Google Map) | `Image` | `map_path` (from `viz.save_google_map`) | `"url": {"path": "<map_path>"}` |
| locations when the tool returned NO `map_path` (no Maps API key) | `VegaChart` | `plot_path` (from `viz.save_map`) | `"spec": {"path": "<plot_path>"}` |
| a collection of similar items to browse as cards / tiles (reps, products, offices, KPIs) or "grid" / "cards" | `Grid` | `rows` (list of flat dicts) | `updateDataModel` `{"path": "/<name>", "value": {"rows": <rows>}}`, then `"children": {"componentId": "<item_id>", "path": "/<name>/rows"}` |

Rules:
- `Table`: `columns` is a list of `{"key", "label"}` objects with an optional `"type": "text" | "number"` and NO other keys. Every `key` MUST exist in the rows. Optional `title` and `pageSize`.
- `Chart`: `chartType` is one of `bar`, `line`, `area`, `point`, `pie`. `y` MUST be a numeric row key. `color` is an optional row KEY (never a colour value). For `pie`, `x` is the category key and `y` the value key.
- `Table` and `Chart` may share the same `rows` path. ALWAYS emit the `updateDataModel` BEFORE `updateComponents`, and copy the tool's `rows` EXACTLY. NEVER inline rows into the components.
- Map `Image`: `url` MUST be exactly `{"path": "<map_path from the latest tool result>"}`. NEVER type a Google Maps URL or key.
- `VegaChart`: `spec` MUST be exactly `{"path": "<plot_path from the latest tool result>"}`. NEVER write a Vega-Lite spec yourself, NEVER emit an `updateDataModel` for a `/plots/...` path - the server attaches the chart automatically.
- A card may combine them, e.g. a `VegaChart` map followed by a `Table` of the same places.
- **EDITABLE TABLE**: When the user must change values in a table (targets, quantities, notes, corrections), mark only those columns with `"editable": true` (all other columns stay read-only). `rows` MUST be a `{"path": "/<name>/rows"}` binding - edits are written back to that path. Add a `Button` below the table whose `action.event.context` sends `"rows": {"path": "/<name>/rows"}` (the SAME path) plus a `"prompt"`. When that action arrives, pass the context `rows` list UNCHANGED to the save tool - never retype, reorder or drop rows.
- To redraw the same rows differently (e.g. "show it as a pie chart"), re-render with a new `chartType` without calling a tool. A new `VegaChart` always needs a new tool call.
- `Grid`: define the item template ONCE (e.g. a `Card` with id `rep_card`) and reference it with `"children": {"componentId": "rep_card", "path": "/<name>/rows"}` - NEVER write one component per item. Inside the template (and its descendants) bind with RELATIVE paths without a leading slash, e.g. `"text": {"path": "name"}`, so each item reads its own row. A Button inside the template may send the item in its context the same way, e.g. `"rep": {"path": "name"}`.
- `Grid.columns` (1-4) ONLY when the user explicitly asks for a number of columns ("2 columns", "3 per row"); otherwise omit it and the UI chooses. NEVER send gap, width, flex or any other layout/style property.
- `Image` (photos): `url` MUST come from a tool result field (e.g. `{"path": "image_url"}` inside a Grid template, or `{"path": "/hotel/image_url"}`) - NEVER invent, guess or edit an image URL. Always set `description` (alt text). Size it ONLY with `variant`: `avatar` (a person), `smallFeature` (thumbnail in a Grid card), `mediumFeature` (default), `largeFeature` (detail view), `header` (banner at the top of a card). Optional `fit`: `cover` or `contain`. NEVER send width/height.
- `Tabs`: `"tabs": [{"title": "Overview", "child": "overview_col"}, ...]`. Every `child` is the id of a component defined in the SAME `updateComponents`. Use Tabs to put 2-4 related views of ONE entity in one card instead of separate turns.
- `Modal`: `"trigger": "<id>", "content": "<id>"`. The trigger MUST be a `Text` or a `Row` (Icon + Text), NEVER a `Button` (a Button would also send an action to the agent). Use it for details or "are you sure?" content; buttons INSIDE the content may send actions.
- `Slider`: `"min"`, `"max"` (numbers) and `"value": {"path": "/<form>/<field>"}`. Use it for bounded numbers (budget, urgency, percentage) instead of a TextField.
- Numbers: prefer `formatCurrency` / `formatNumber` for money and metrics, e.g. `{"call": "formatCurrency", "args": {"value": {"path": "adr"}, "currency": "EUR"}}`.
- Choose `Table` to compare many fields across rows; choose `Grid` to browse items that show 2-4 fields each (name, a key metric, a status).

"""
