"""Tests for Gemini Enterprise Agent & Renderer."""

from src.agent import GeminiEnterpriseAgent
from src.config import ge_config
from src.tools import query_enterprise_knowledge, execute_compliance_audit
from src.ge_renderer import GeminiEnterpriseRenderer

def test_ge_agent_initialization():
    agent = GeminiEnterpriseAgent()
    assert agent.model_name == "gemini-2.5-pro"
    assert agent.project_name == "{{PROJECT_TITLE}}"

def test_ge_workflow_execution():
    agent = GeminiEnterpriseAgent()
    card = agent.execute_enterprise_workflow("Test Enterprise Intent")
    assert card.header.startswith("Enterprise Agent:")
    assert len(card.badges) > 0
    assert len(card.actions) > 0
    assert card.actions[0].action_id == "DISPATCH_ENTERPRISE_JOB"

def test_ge_tools():
    kb_res = query_enterprise_knowledge("security policy")
    assert kb_res["status"] == "success"
    audit_res = execute_compliance_audit("res-101")
    assert audit_res["status"] == "PASSED"
