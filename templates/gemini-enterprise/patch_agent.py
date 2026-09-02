import re

with open("src/agent.py", "r") as f:
    code = f.read()

new_func = """def build_mock_capabilities_card(self, surface_id: str = "capabilities-surface-01") -> List[Dict[str, Any]]:
        \"\"\"Constructs a deterministic, validated Material A2UI v0.9.1 capabilities card.\"\"\"
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
                            "justify": "spaceBetween",
                            "children": ["title_group", "header_icons"]
                        },
                        {
                            "id": "title_group",
                            "component": "Row",
                            "align": "center",
                            "children": ["sparkle_icon", "title_text"]
                        },
                        {
                            "id": "sparkle_icon",
                            "component": "Icon",
                            "name": "star"
                        },
                        {
                            "id": "title_text",
                            "component": "Text",
                            "text": "Capabilities",
                            "variant": "h2"
                        },
                        {
                            "id": "header_icons",
                            "component": "Row",
                            "align": "center",
                            "children": ["heart_icon", "like_icon"]
                        },
                        {
                            "id": "heart_icon",
                            "component": "Icon",
                            "name": "favorite"
                        },
                        {
                            "id": "like_icon",
                            "component": "Icon",
                            "name": "check"
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
                            "text": "⚡ Dynamic Component Generation",
                            "variant": "body"
                        },
                        {
                            "id": "line_2",
                            "component": "Text",
                            "text": "🎴 Material A2UI Cards",
                            "variant": "body"
                        },
                        {
                            "id": "line_3",
                            "component": "Text",
                            "text": "🔘 Interactive Buttons",
                            "variant": "body"
                        },
                        {
                            "id": "line_4",
                            "component": "Text",
                            "text": "🎨 Material v0.9.1 UI Catalog",
                            "variant": "body"
                        },
                        {
                            "id": "line_5",
                            "component": "Text",
                            "text": "❤️ Delightful Agent Experience",
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
                                "event": {
                                    "name": "like_capabilities_event"
                                }
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
                                "event": {
                                    "name": "explore_more_event"
                                }
                            }
                        }
                    ]
                }
            }
        ]
"""

# Replace exactly from def build_mock_capabilities_card to the line before async def generate_response
import re
code = re.sub(r'def build_mock_capabilities_card.*?\]\n\n', new_func + '\n\n', code, flags=re.DOTALL)

with open("src/agent.py", "w") as f:
    f.write(code)

