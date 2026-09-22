import re
import os
import sys
import shutil
from google.genai import Client

A2UI_BOILERPLATE_PROMPT = r"""
### CRITICAL OUTPUT FORMAT & A2UI SPECIFICATION (MANDATORY):
- ALWAYS output your responses directly as text in the message body.
- When rendering A2UI components, ALWAYS output the JSON strictly as text enclosed within `<a2ui-json>...</a2ui-json>` XML tags.
- The JSON inside `<a2ui-json>...</a2ui-json>` MUST be a single valid JSON array `[ ... ]` containing `createSurface`, `updateComponents`, and `updateDataModel` messages, matching the exact syntax and component hierarchy from the provided example JSON templates.
- **MANDATORY TEMPLATE FIDELITY (Basic Catalog v0.9)**:
  - You MUST refer directly to the provided example JSON files in your system instructions when generating A2UI cards.
  - The `catalogId` in `createSurface` MUST strictly be `"https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"`.
  - You MUST strictly follow the exact component hierarchy, component types (`Card`, `Column`, `Row`, `Text`, `Icon`, `Divider`, `Button`, `Image`), and allowed properties defined in each example JSON file without adding any extra or invalid attributes.
  - **NO STYLING OR SIZING PROPERTIES**: Do NOT include `"style"`, `"padding"`, `"margin"`, `"spacing"`, `"gap"`, `"justifyContent"`, `"alignItems"`, `"width"`, or `"height"` on any components. All components must strictly conform to Basic Catalog schema.
  - `Text`: Valid `variant` values are strictly `"caption"` and `"body"`. (Do NOT use h1, h2, h3, etc.)
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

    # Never let the LLM target a directory we cannot afford to lose
    reserved = {
        "basic_template", "tests", "examples", "frontend", "backend",
        "src", "node_modules", "meta_json",
    }
    if template_dir:
        reserved.add(template_dir)

    if raw in reserved:
        print(f"⚠️  '{raw}' is a reserved directory name - refusing to overwrite it.")
        print(f"   Falling back to '{FALLBACK_AGENT_NAME}'.")
        return FALLBACK_AGENT_NAME

    return raw

TEMPLATE_DIR_NAME = "basic_template"
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
    
    from dotenv import load_dotenv
    load_dotenv()
    client = Client(api_key=os.environ.get("GEMINI_API_KEY"))

    # planner_instruction = "You are the Planner Agent. Ask the user 1 or 2 clarifying questions about their agent idea to gather detailed requirements for tools and UI. Once you have a clear plan, end your message with exactly the phrase '<PLAN_READY>'. Keep your responses very short."
    planner_instruction = """You are the Planner Agent. Your job is to gather requirements and design the user flow.
    1. First, analyze the user's app idea and proactively propose a standard UI flow for it (e.g., List View -> Details Form -> Confirmation). Do not make the user design it from scratch.
    2. Present this proposed flow to the user using a clear ASCII flowchart drawn with pure text characters (e.g. +---, |, ->). DO NOT use Mermaid syntax (```mermaid) or any other markdown diagram language. Only use raw ASCII text.
    3. Ask the user if they approve of this flow or if they want to make changes.
    4. DO NOT output <PLAN_READY> in your first response.
    5. Wait for the user to answer.
    6. Once the user approves the flow and you have a complete understanding, summarize the final plan and then end your message with exactly the phrase '<PLAN_READY>'."""
    chat = client.chats.create(model='gemini-2.5-pro', config={"system_instruction": planner_instruction})
    
    app_idea = input("What kind of agent do you want to build?:\n> ")
    if not app_idea.strip():
        sys.exit(1)

    response = chat.send_message(app_idea)
    while True:
        print(f"\n[Planner Agent]: {response.text}")
        if "<PLAN_READY>" in response.text:
            break
        user_reply = input("> ")
        response = chat.send_message(user_reply)

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


    coder_instruction = """You are the Coder Agent.
Read the user's conversation history (the plan). Generate the Python code for an A2UI backend.
You must output exactly five things: a folder name, and at least four files (`prompt.py`, `tools.py`, `agent.py`, and one or more `.json` templates).

1. Define the folder name wrapped in tags: <folder_name>insert_agent_name_here</folder_name> (use snake_case, derived from the agent's purpose)
2. Wrap the content of EACH file in XML tags: <file name="prompt.py">print('hello')</file>
3. For JSON templates, use the path `examples/v0_9/your_template_name.json`: <file name="examples/v0_9/main_view.json">{ ... }</file>

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
CORRECT:
{"component": "ChoicePicker", "id": "doc", "label": "Select a Doctor", "variant": "mutuallyExclusive",
 "options": [{"label": "Dr. Alice", "value": "alice"}, {"label": "Dr. Bob", "value": "bob"}],
 "value": {"path": "/application/doctor"}}
=========================================

CRITICAL INSTRUCTIONS FOR JSON TEMPLATES:
- **ANTI-HALLUCINATION RULE:** Do NOT rely on your pre-trained web development knowledge to invent JSON layouts. You MUST strictly model your new JSON files after the structural format of standard A2UI v0.9 templates. While your content/use-case will change, the exact schema, component naming, and allowed properties must remain identical to the spec.
- You MUST design perfectly flat JSON arrays matching the A2UI v0.9 `updateComponents` specification defined in the rules above.
- You MUST ensure all components (especially Buttons, TextFields, and CheckBoxes) strictly follow the structural rules above

CRITICAL INSTRUCTIONS FOR prompt.py:
- Define `ROLE_DESCRIPTION` as a string.
- Define `UI_DESCRIPTION` as a raw string (r\"\"\").
- In `UI_DESCRIPTION`, you MUST provide strict English bullet points instructing the child agent on exactly how to use your provided JSON templates!
- You MUST explicitly explain what every Button does, which backend tool it calls, and how the form fields (e.g. text fields, date inputs, radio buttons) map to the tool's arguments via data binding paths.
- Example: "The 'Submit' button MUST have an `action` property that calls the `book_flight` tool. The parameters (`destination`, `date`) MUST be bound to the data paths of the form fields: `\"action\": {\"event\": {\"name\": \"book_flight\", \"context\": {\"destination\": {\"path\": \"/form/dest\"}}}`."
- **CRITICAL:** You MUST explicitly command the agent: "When an event is triggered, you MUST FIRST call the Python tool. Only after the tool returns successfully, you MUST render the new surface."
- DO NOT output the massive 'CRITICAL OUTPUT FORMAT' boilerplate.

CRITICAL INSTRUCTIONS FOR tools.py:
- Write 1 or 2 python functions for backend logic. Provide clear docstrings.
- Python tools MUST NOT use strict date parsing like `date.fromisoformat()` if accepting dates from `DateTimeInput`. Extract the date robustly using `from_date[:10]` or `datetime.fromisoformat()`.
- DO NOT use the `@tool` decorator or import it. Write raw python functions.

CRITICAL INSTRUCTIONS FOR agent.py:
- Take the provided template below and ONLY change the `tools=[...]` array at the bottom to match your new tools. Leave all else exactly as is.

=========================================

=== EXAMPLES TO STRICTLY COPY FROM ===

--- agent.py TEMPLATE ---
""" + template_agent + """

--- tools.py TEMPLATE ---
""" + template_tools + """

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
        model='gemini-2.5-pro',
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
You MUST evaluate the code against EVERY SINGLE ITEM in the checklist. Do not stop at the first error! Write down a step-by-step analysis for each of the 13 rules. If ANY rules were broken, output <FAIL> at the very end of your response, followed by the complete compiled list of ALL errors found.
You must specifically check `prompt.py` and the JSON templates for A2UI hallucinations based on these strict rules:

=== A2UI V0.9 STRICT RULES ===
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
=========================================

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
- Write 1 or 2 python functions for backend logic. Provide clear docstrings.
- Python tools MUST NOT use strict date parsing like `date.fromisoformat()` if accepting dates from `DateTimeInput`. Extract the date robustly using `from_date[:10]` or `datetime.fromisoformat()`.
- DO NOT use the `@tool` decorator or import it. Write raw python functions.

CRITICAL INSTRUCTIONS FOR agent.py:
- Take the provided template below and ONLY change the `tools=[...]` array at the bottom to match your new tools. Leave all else exactly as is.
==============================

Checklist to FAIL the coder:
1. Did the Coder invent components that don't exist? (Only Card, Column, Row, Text, Icon, Divider, Button, TextField, CheckBox, DateTimeInput, Image, ChoicePicker are allowed). (FAIL if others exist).
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
14. **TEMPLATE COMPARISON:** Did the Coder modify anything in `agent.py` OTHER than the `tools=[...]` array at the bottom? (FAIL if they modified the boilerplate).
15. **STRUCTURE AUDIT:** Review the generated `examples/v0_9/*.json` files. While the *use-case* is unique, is the underlying structure, component naming (TitleCase), and strict property usage identical to the A2UI spec? Did they hallucinate CSS properties, wrapper objects, or unapproved keys? (FAIL if yes).
16. **DROPDOWN MENUS (ChoicePicker)**
A2UI v0.9 has NO <select> component. For any dropdown / "pick one from a list" UI you MUST use `ChoicePicker`.
- `options` MUST be a literal JSON array of {"label": "...", "value": "..."} objects. It can NEVER be a "${...}" string.
- `variant` is "mutuallyExclusive" for single-select (default) or "multipleSelection" for multi-select.
- `value` MUST be bound: "value": {"path": "/application/your_field"}
- The frontend writes a string ARRAY to that path (e.g. ["alice_martin"]) even for single-select.
  Therefore any tools.py function receiving it MUST normalize: `if isinstance(x, list): x = x[0] if x else ""`
CORRECT:
{"component": "ChoicePicker", "id": "doc", "label": "Select a Doctor", "variant": "mutuallyExclusive",
 "options": [{"label": "Dr. Alice", "value": "alice"}, {"label": "Dr. Bob", "value": "bob"}],
 "value": {"path": "/application/doctor"}}

If the code is PERFECT, reply with EXACTLY '<PASS>'.
If the code has errors, reply with '<FAIL>' followed by a detailed list of what needs to be fixed.

=== BASELINE A2UI TEMPLATE EXAMPLES TO COMPARE AGAINST ===
""" + template_json + """
"""
    max_retries = 3
    retries = 0
    while retries < max_retries:
        critic_response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=f"Review this generated code:\n\n{generated_code}",
            config={"system_instruction": critic_instruction}
        )

        print(f"\n[Critic Agent]:\n{critic_response.text}")

        if "<FAIL>" in critic_response.text:
            retries += 1
            if retries >= max_retries:
                print(f"\n❌ Critic rejected the code, but max retries ({max_retries}) reached! Writing files anyway...")
                break
                
            print(f"\n❌ Critic rejected the code! Sending back to Coder to fix (Attempt {retries}/{max_retries})...")
            correction_prompt = f"The Critic found errors in your code:\n{critic_response.text}\n\nPlease regenerate all files fixing these errors."
            coder_response = client.models.generate_content(
                model='gemini-2.5-pro',
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
            
            if filename == "prompt.py":
                # Prepend the boilerplate to the file so it sits BEFORE the generated instructions
                content = f'A2UI_BOILERPLATE_PROMPT = r"""\n{A2UI_BOILERPLATE_PROMPT}\n"""\n\n' + content
                # Make sure the UI_DESCRIPTION dynamically prepends the boilerplate when the agent reads it
                content += "\n\nUI_DESCRIPTION = A2UI_BOILERPLATE_PROMPT + '\\n\\n' + UI_DESCRIPTION\n"
            
            
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
