import re

prompt_path = 'src/prompt.py'
with open(prompt_path, 'r') as f:
    prompt_code = f.read()

new_example = '''### EXAMPLE CAPABILITIES A2UI JSON PAYLOAD (Material v0.9.1):
```json
[
  {
    "version": "v0.9",
    "createSurface": {
      "surfaceId": "capabilities-surface-01",
      "catalogId": "https://a2ui.org/specification/v0_9/material_catalog.json"
    }
  },
  {
    "version": "v0.9",
    "updateComponents": {
      "surfaceId": "capabilities-surface-01",
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
          "name": "auto_awesome"
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
          "name": "thumb_up"
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
          "text": "⚡ Dynamic Component Generation: Synthesizes UI widgets on-the-fly.",
          "variant": "body"
        },
        {
          "id": "line_2",
          "component": "Text",
          "text": "🎴 Material A2UI Cards: Renders beautiful, structured cards with responsive layouts.",
          "variant": "body"
        },
        {
          "id": "line_3",
          "component": "Text",
          "text": "🔘 Interactive Buttons: Dispatches contextual user events back to the agent.",
          "variant": "body"
        },
        {
          "id": "line_4",
          "component": "Text",
          "text": "🎨 Material v0.9.1 UI Catalog: Full support for badges, rows, columns, and icons.",
          "variant": "body"
        },
        {
          "id": "line_5",
          "component": "Text",
          "text": "❤️ Delightful Agent Experience: Bridges LLM reasoning with reactive web frontends.",
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
            "name": "like_capabilities_event"
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
            "name": "explore_more_event"
          }
        }
      ]
    }
  }
]
```'''

prompt_code = re.sub(r'### EXAMPLE CAPABILITIES A2UI JSON PAYLOAD \(Material v0\.9\.1\):.*?```json.*?```', new_example, prompt_code, flags=re.DOTALL)
with open(prompt_path, 'w') as f:
    f.write(prompt_code)
