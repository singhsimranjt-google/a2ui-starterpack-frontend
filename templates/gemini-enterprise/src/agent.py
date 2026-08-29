"""Gemini Enterprise (GE) Agent Implementation."""

import json
from src.config import ge_config
from src.agent_executor import GEAgentExecutor
from src.ge_renderer import GEEnterpriseCard


class GeminiEnterpriseAgent:
    """Enterprise Agent designed for native Gemini Enterprise UI rendering."""

    def __init__(self):
        self.config = ge_config
        self.model_name = ge_config.model_name
        self.project_name = ge_config.project_name
        self.executor = GEAgentExecutor()

    def execute_enterprise_workflow(self, query: str) -> GEEnterpriseCard:
        """Executes reasoning workflow via executor and returns a GE card."""
        return self.executor.execute(query)


def main():
    """CLI runner to test Gemini Enterprise Agent output."""
    print("=" * 65)
    print("🏢 Gemini Enterprise (GE) Agent & Renderer Runner")
    print("=" * 65)

    agent = GeminiEnterpriseAgent()
    sample_query = "Summarize compliance policy for multi-cloud deployment"
    print(f"\n[Enterprise Query]: {sample_query}\n")

    card = agent.execute_enterprise_workflow(sample_query)
    print("=" * 20 + " [Generated GE UI Card] " + "=" * 20)
    print(json.dumps(card.model_dump(), indent=2))
    print("=" * 65)


if __name__ == "__main__":
    main()
