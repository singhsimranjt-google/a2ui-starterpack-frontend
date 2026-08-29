"""Google ADK Agent implementation with Agent-to-User Interface (A2UI) generation."""

import json
from typing import List
from src.config import config
from src.agent_executor import AgentExecutor, A2UIWidget


class ADKAgent:
    """Google ADK Agent capable of reasoning and synthesizing A2UI components."""

    def __init__(self):
        self.config = config
        self.agent_name = config.agent_name
        self.model_name = config.model_name
        self.executor = AgentExecutor()

    def execute_intent(self, user_prompt: str) -> List[A2UIWidget]:
        """Process user intent via AgentExecutor and return synthesized A2UI widgets."""
        print(f"🤖 [{self.agent_name}] Processing intent: '{user_prompt}'...")
        return self.executor.execute(user_prompt)


def main():
    """CLI execution entrypoint."""
    print("=" * 60)
    print("🚀 Google ADK Agent - A2UI CLI Runner")
    print("=" * 60)

    agent = ADKAgent()
    sample_prompt = "Generate quarterly analytics breakdown and recommended next actions"
    print(f"\n[Test Prompt]: {sample_prompt}")

    widgets = agent.execute_intent(sample_prompt)
    print(f"\n[Emitted A2UI Schemas ({len(widgets)} widgets)]:\n")
    for w in widgets:
        print(json.dumps(w.model_dump(), indent=2))
        print("-" * 40)


if __name__ == "__main__":
    main()
