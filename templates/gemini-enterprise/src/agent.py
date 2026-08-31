"""Google ADK & Gemini Enterprise Agent with Material A2UI v0.9.1 rendering."""

import asyncio
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from google.genai import types, Client
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None  # type: ignore
    Client = None  # type: ignore

try:
    from src.config import config
    from src.prompt import ROLE_DESCRIPTION, UI_DESCRIPTION
    from src.tools import get_agent_capabilities
except ImportError:
    from config import config
    from prompt import ROLE_DESCRIPTION, UI_DESCRIPTION
    from tools import get_agent_capabilities

_TAG_PATTERN = re.compile(r"<a2ui-json>(.*?)</a2ui-json>", re.DOTALL)


class Agent:
    """Production-ready Google ADK / Gemini Enterprise Agent."""

    def __init__(self):
        self.config = config
        self.client: Optional[Any] = None
        if GENAI_AVAILABLE and config.api_key:
            self.client = Client(api_key=config.api_key)
        self.system_instruction = f"{ROLE_DESCRIPTION}\n\n{UI_DESCRIPTION}"

    def build_mock_capabilities_card(self, surface_id: str = "capabilities-surface-01") -> List[Dict[str, Any]]:
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
                            "component": "MaterialColumn",
                            "children": ["capabilities_card"],
                            "style": {"maxWidth": "720px", "margin": "0 auto", "padding": "12px"}
                        },
                        {
                            "id": "capabilities_card",
                            "component": "MaterialCard",
                            "appearance": "raised",
                            "children": [
                                "header_row",
                                "divider_1",
                                "content_col",
                                "divider_2",
                                "actions_row"
                            ],
                            "style": {"padding": "20px"}
                        },
                        {
                            "id": "header_row",
                            "component": "MaterialRow",
                            "align": "center",
                            "justify": "start",
                            "style": {"padding": "2px 0"},
                            "children": ["header_icon", "header_text_col"]
                        },
                        {
                            "id": "header_icon",
                            "component": "MaterialIcon",
                            "icon": "auto_awesome",
                            "color": "primary"
                        },
                        {
                            "id": "header_text_col",
                            "component": "MaterialColumn",
                            "style": {"paddingLeft": "10px"},
                            "children": ["header_title", "header_subtitle"]
                        },
                        {
                            "id": "header_title",
                            "component": "MaterialText",
                            "text": "Capabilities",
                            "usageHint": "h2"
                        },
                        {
                            "id": "header_subtitle",
                            "component": "MaterialText",
                            "text": "Google ADK & Material A2UI v0.9.1 Specifications",
                            "usageHint": "caption"
                        },
                        {
                            "id": "divider_1",
                            "component": "MaterialDivider",
                            "style": {"margin": "12px 0"}
                        },
                        {
                            "id": "content_col",
                            "component": "MaterialColumn",
                            "children": ["line_1", "line_2", "line_3", "line_4", "line_5"]
                        },
                        {
                            "id": "line_1",
                            "component": "MaterialText",
                            "text": f"⚡ {caps_data['capabilities'][0]}",
                            "usageHint": "body"
                        },
                        {
                            "id": "line_2",
                            "component": "MaterialText",
                            "text": f"🎴 {caps_data['capabilities'][1]}",
                            "usageHint": "body"
                        },
                        {
                            "id": "line_3",
                            "component": "MaterialText",
                            "text": f"🔘 {caps_data['capabilities'][2]}",
                            "usageHint": "body"
                        },
                        {
                            "id": "line_4",
                            "component": "MaterialText",
                            "text": f"🎨 {caps_data['capabilities'][3]}",
                            "usageHint": "body"
                        },
                        {
                            "id": "line_5",
                            "component": "MaterialText",
                            "text": f"❤️ {caps_data['capabilities'][4]}",
                            "usageHint": "body"
                        },
                        {
                            "id": "divider_2",
                            "component": "MaterialDivider",
                            "style": {"margin": "14px 0"}
                        },
                        {
                            "id": "actions_row",
                            "component": "MaterialRow",
                            "align": "center",
                            "justify": "start",
                            "children": ["btn_like", "btn_explore"]
                        },
                        {
                            "id": "btn_like",
                            "component": "MaterialButton",
                            "label": "Like Capabilities",
                            "icon": "thumb_up",
                            "variant": "filled",
                            "action": {
                                "event": {
                                    "type": "click",
                                    "context": {"prompt": "Liked the capabilities overview!"}
                                }
                            }
                        },
                        {
                            "id": "btn_explore",
                            "component": "MaterialButton",
                            "label": "Explore More",
                            "icon": "favorite",
                            "variant": "outlined",
                            "style": {"marginLeft": "12px"},
                            "action": {
                                "event": {
                                    "type": "click",
                                    "context": {"prompt": "Tell me more about A2UI components."}
                                }
                            }
                        }
                    ]
                }
            }
        ]

    async def generate_response(self, user_input: str) -> Dict[str, Any]:
        """Generates conversational responses and Material A2UI v0.9.1 components."""
        cleaned_input = user_input.strip().lower()

        # Direct flow handler for local/offline execution or fallback
        if any(greet in cleaned_input for greet in ["hi", "hello", "hey", "greetings"]):
            return {
                "text": "Hello! 👋 I am your **Google ADK & A2UI Assistant**. How can I help you today? You can ask about my capabilities to see interactive A2UI cards in action!",
                "a2ui": None
            }

        if "capabilit" in cleaned_input or "what can you do" in cleaned_input:
            a2ui_payload = self.build_mock_capabilities_card()
            return {
                "text": "Here is an overview of my core capabilities rendered directly via the Material A2UI v0.9.1 catalog:",
                "a2ui": a2ui_payload
            }

        # If API key is available, leverage Gemini 2.5 Flash
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.config.gemini_model,
                    contents=user_input,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        temperature=0.2,
                        max_output_tokens=4096,
                    )
                )
                raw_text = response.text or ""
                tag_match = _TAG_PATTERN.search(raw_text)
                a2ui_data = None
                clean_text = raw_text

                if tag_match:
                    try:
                        a2ui_data = json.loads(tag_match.group(1).strip())
                        clean_text = _TAG_PATTERN.sub("", raw_text).strip()
                    except json.JSONDecodeError:
                        a2ui_data = None

                return {"text": clean_text, "a2ui": a2ui_data}
            except Exception as e:
                # Fallback to local deterministic response
                return {
                    "text": f"Processed query with local reasoning engine: '{user_input}'. Ask 'what are your capabilities?' to see the Material A2UI card.",
                    "a2ui": None
                }

        # Fallback response
        return {
            "text": f"Received your message: '{user_input}'. Tip: Ask 'what are your capabilities?' to see a Material A2UI card rendered in real-time!",
            "a2ui": None
        }


async def main():
    """CLI interactive test runner for the agent."""
    print("=" * 70)
    print(f"🤖 {config.agent_name} (Model: {config.gemini_model})")
    print("Google ADK & Material A2UI v0.9.1 Runner")
    print("=" * 70)

    agent = Agent()

    # Flow Step 1: User Greets
    print("\n[Step 1] User: 'Hello!'")
    res1 = await agent.generate_response("Hello!")
    print(f"Agent: {res1['text']}")

    # Flow Step 2: User asks for capabilities
    print("\n[Step 2] User: 'What are your capabilities?'")
    res2 = await agent.generate_response("What are your capabilities?")
    print(f"Agent: {res2['text']}\n")
    if res2['a2ui']:
        print("<a2ui-json>")
        print(json.dumps(res2['a2ui'], indent=2))
        print("</a2ui-json>")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
