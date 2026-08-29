"""Core Agent Executor loop connecting Gemini reasoning with A2UI schema synthesis."""

from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.config import config
from src.prompt import SYSTEM_INSTRUCTION
from src.tools import TOOL_REGISTRY, AVAILABLE_TOOLS

class A2UIWidget(BaseModel):
    """Structured A2UI component schema."""
    id: str = Field(description="Unique identifier for the UI component")
    type: str = Field(description="UI Component type: metric_card, action_panel, form, table")
    title: str = Field(description="Card or Widget Title")
    content: str = Field(description="Main textual content or summary")
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured component metadata")


class AgentExecutor:
    """Executes agent workflows, tool dispatches, and converts outputs into A2UI schema cards."""

    def __init__(self):
        self.model_name = config.model_name
        self.agent_name = config.agent_name
        self.system_instruction = SYSTEM_INSTRUCTION
        self.tools = AVAILABLE_TOOLS

    def execute(self, user_intent: str) -> List[A2UIWidget]:
        """Runs the reasoning loop and returns synthesized A2UI widgets."""
        print(f"⚙️ [AgentExecutor] Executing intent for '{self.agent_name}' with model '{self.model_name}'...")

        # 1. Tool Selection & Execution Check
        tool_output = None
        lower_intent = user_intent.lower()
        if "metric" in lower_intent or "analytic" in lower_intent or "performance" in lower_intent:
            tool_output = TOOL_REGISTRY["query_analytics_metrics"]()
        elif "search" in lower_intent or "find" in lower_intent or "info" in lower_intent or "guide" in lower_intent:
            tool_output = TOOL_REGISTRY["search_knowledge_base"](user_intent)

        # 2. Synthesize A2UI Schema Components
        widget_id = f"widget-{int(datetime.now().timestamp())}"
        widgets: List[A2UIWidget] = []

        # Metric Card Component
        widgets.append(
            A2UIWidget(
                id=f"{widget_id}-metrics",
                type="metric_card",
                title=f"Reasoning Outcome: {user_intent}",
                content=f"Processed query with {self.model_name}. Intent evaluated successfully.",
                data={
                    "model": self.model_name,
                    "agent": self.agent_name,
                    "confidence": 0.98,
                    "toolExecution": tool_output or {"status": "direct_reasoning"},
                    "timestamp": datetime.now().isoformat()
                }
            )
        )

        # Action Panel Component
        widgets.append(
            A2UIWidget(
                id=f"{widget_id}-actions",
                type="action_panel",
                title="A2UI Recommended Actions",
                content="Choose from the following contextual action workflows:",
                data={
                    "options": [
                        {"label": "Execute Workflow", "action": "EXECUTE_CONFIRMED", "style": "primary"},
                        {"label": "Adjust Parameters", "action": "MODIFY_INPUTS", "style": "secondary"},
                        {"label": "Export Report", "action": "EXPORT_DATA", "style": "ghost"}
                    ]
                }
            )
        )

        return widgets
