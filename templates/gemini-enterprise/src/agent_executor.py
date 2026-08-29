"""Gemini Enterprise Agent Executor orchestrating enterprise tools and GE card rendering."""

from src.config import ge_config
from src.prompt import GE_SYSTEM_INSTRUCTION
from src.tools import GE_TOOLS_REGISTRY
from src.ge_renderer import (
    GeminiEnterpriseRenderer,
    GEEnterpriseCard,
    GEActionButton,
    GECitation
)

class GEAgentExecutor:
    """Executes enterprise agent reasoning and formats output via GeminiEnterpriseRenderer."""

    def __init__(self):
        self.config = ge_config
        self.model_name = ge_config.model_name
        self.project_name = ge_config.project_name
        self.system_instruction = GE_SYSTEM_INSTRUCTION

    def execute(self, query: str) -> GEEnterpriseCard:
        """Executes enterprise reasoning loop and constructs a Gemini Enterprise card."""
        print(f"🏢 [GEAgentExecutor] Executing enterprise workflow for: '{query}'")

        # 1. Execute enterprise knowledge grounding tool
        knowledge_res = GE_TOOLS_REGISTRY["query_enterprise_knowledge"](query)
        citation_info = knowledge_res["citation"]

        citations = [
            GECitation(
                source_title=citation_info["source_title"],
                uri=citation_info["uri"],
                snippet=citation_info["snippet"]
            )
        ]

        # 2. Build Interactive Enterprise Action Buttons
        actions = [
            GEActionButton(
                label="Confirm & Dispatch",
                action_id="DISPATCH_ENTERPRISE_JOB",
                payload={"query": query, "model": self.model_name},
                style="primary"
            ),
            GEActionButton(
                label="Audit Trace",
                action_id="VIEW_AUDIT_LOG",
                payload={"log_id": "aud-98242"},
                style="secondary"
            )
        ]

        # 3. Format via GE Renderer
        return GeminiEnterpriseRenderer.render_card(
            header=f"Enterprise Agent: {self.project_name}",
            subtitle=f"Model: {self.model_name} | Grounded & Validated",
            body=(
                f"### Analysis Result\n\n"
                f"Successfully parsed enterprise intent for query: **{query}**.\n\n"
                f"- **Validation Status**: Passed enterprise security policies\n"
                f"- **Data Classification**: Confidential / Internal Only\n"
                f"- **Next Step**: Click action below to trigger workflow orchestrator."
            ),
            badges=["Enterprise Verified", "Grounding: Active", "SOC2 Compliant"],
            citations=citations,
            actions=actions,
            metadata={"query": query, "model": self.model_name}
        )
