import re

agent_path = 'src/agent.py'
with open(agent_path, 'r') as f:
    agent_code = f.read()

# Replace the entire build_mock_capabilities_card function
new_function = '''    def build_mock_capabilities_card(self, surface_id: str = "capabilities-surface-01") -> List[Dict[str, Any]]:
        """Constructs a deterministic, validated Material A2UI v0.9.1 capabilities card."""
        caps_data = get_agent_capabilities()
        return [
            {
                "version": "v0.9",
                "createSurface": {
                    "surfaceId": surface_id,
                    "catalogId": "https://a2ui.org/specification/v0_9/material_catalog.json"
                }
            },
            {
                "version": "v0.9",
                "updateComponents": {
                    "surfaceId": surface_id,
                    "components": [
                        {
                            "id": "root",
                            "component": "Column",
                            "children": ["capabilities_card"]
                        },
                        {
                            "id": "capabilities_card",
                            "component": "Card",
                            "child": "content_col"
                        },
                        {
                            "id": "content_col",
                            "component": "Column",
                            "children": [
                                "header_row",
                                "divider_1",
                                "capabilities_lines",
                                "divider_2",
                                "actions_row"
                            ]
                        },
                        {
                            "id": "header_row",
                            "component": "Row",
                            "align": "center",
                            "justify": "start",
                            "children": ["header_icon", "header_text_col"]
                        },
                        {
                            "id": "header_icon",
                            "component": "Icon",
                            "name": "auto_awesome"
                        },
                        {
                            "id": "header_text_col",
                            "component": "Column",
                            "children": ["header_title", "header_subtitle"]
                        },
                        {
                            "id": "header_title",
                            "component": "Text",
                            "text": "Capabilities",
                            "variant": "h2"
                        },
                        {
                            "id": "header_subtitle",
                            "component": "Text",
                            "text": "Google ADK & A2UI v0.9.1 Specifications",
                            "variant": "caption"
                        },
                        {
                            "id": "divider_1",
                            "component": "Divider",
                            "axis": "horizontal"
                        },
                        {
                            "id": "capabilities_lines",
                            "component": "Column",
                            "children": ["line_1", "line_2", "line_3", "line_4", "line_5"]
                        },
                        {
                            "id": "line_1",
                            "component": "Text",
                            "text": f"⚡ {caps_data['capabilities'][0]}",
                            "variant": "body"
                        },
                        {
                            "id": "line_2",
                            "component": "Text",
                            "text": f"🎴 {caps_data['capabilities'][1]}",
                            "variant": "body"
                        },
                        {
                            "id": "line_3",
                            "component": "Text",
                            "text": f"🔘 {caps_data['capabilities'][2]}",
                            "variant": "body"
                        },
                        {
                            "id": "line_4",
                            "component": "Text",
                            "text": f"🎨 {caps_data['capabilities'][3]}",
                            "variant": "body"
                        },
                        {
                            "id": "line_5",
                            "component": "Text",
                            "text": f"❤️ {caps_data['capabilities'][4]}",
                            "variant": "body"
                        },
                        {
                            "id": "divider_2",
                            "component": "Divider",
                            "axis": "horizontal"
                        },
                        {
                            "id": "actions_row",
                            "component": "Row",
                            "align": "center",
                            "justify": "start",
                            "children": ["btn_like", "btn_explore"]
                        },
                        {
                            "id": "btn_like_text",
                            "component": "Text",
                            "text": "Like Capabilities"
                        },
                        {
                            "id": "btn_like",
                            "component": "Button",
                            "child": "btn_like_text",
                            "variant": "primary",
                            "action": {
                                "name": "like_capabilities"
                            }
                        },
                        {
                            "id": "btn_explore_text",
                            "component": "Text",
                            "text": "Explore More"
                        },
                        {
                            "id": "btn_explore",
                            "component": "Button",
                            "child": "btn_explore_text",
                            "variant": "default",
                            "action": {
                                "name": "explore_capabilities"
                            }
                        }
                    ]
                }
            }
        ]'''

agent_code = re.sub(r'    def build_mock_capabilities_card.*?(?=\n    def|\Z)', new_function + '\n', agent_code, flags=re.DOTALL)
with open(agent_path, 'w') as f:
    f.write(agent_code)

prompt_path = 'src/prompt.py'
with open(prompt_path, 'r') as f:
    prompt_code = f.read()

new_ui_desc = r'''### MATERIAL CATALOG v0.9.1 COMPONENT RULES:
- Catalog ID: `https://a2ui.org/specification/v0_9/material_catalog.json`
- Supported Components (NEVER use `style`, `appearance`, `usageHint`, or inline children. A2UI uses strict Zod schemas):
  - `Card`: Top-level or nested container. Takes ONLY `child`: string (ID of another component, e.g. a Column). NO `children` or `style`.
  - `Column`: Vertical layout container. Takes `children`: string[] (Array of component IDs), `align`: "start" | "center" | "end" | "stretch", `justify`: "start" | "center" | "end" | "spaceBetween" | "spaceAround" | "spaceEvenly" | "stretch". NO `style`.
  - `Row`: Horizontal layout container. Takes `children`: string[] (Array of component IDs), `align`: "start" | "center" | "end" | "stretch", `justify`: "start" | "center" | "end" | "spaceBetween" | "spaceAround" | "spaceEvenly" | "stretch". NO `style`.
  - `Text`: Displays text. Takes `text`: string, `variant`: "h1" | "h2" | "h3" | "h4" | "h5" | "caption" | "body".
  - `Icon`: Displays a material icon. Takes `name`: string.
  - `Button`: A clickable button. Takes ONLY `child`: string (ID of a Text or Icon component), `variant`: "default" | "primary" | "borderless", and `action`: object (e.g. `{"name": "submit_form"}`). NO `label` or `icon`.
  - `Divider`: Visual separator. Takes `axis`: "horizontal" | "vertical".
'''

prompt_code = re.sub(r'### MATERIAL CATALOG v0\.9\.1 COMPONENT RULES:.*?(?=\n\n|\Z)', new_ui_desc, prompt_code, flags=re.DOTALL)
with open(prompt_path, 'w') as f:
    f.write(prompt_code)
