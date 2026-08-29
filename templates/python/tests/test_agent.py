"""Tests for Google ADK Agent."""

from src.agent import ADKAgent
from src.config import config
from src.tools import AVAILABLE_TOOLS, search_knowledge_base, query_analytics_metrics
from src.agent_executor import AgentExecutor

def test_agent_initialization():
    agent = ADKAgent()
    assert agent.model_name == "gemini-2.5-flash"
    assert agent.agent_name == "{{PROJECT_TITLE}}"

def test_agent_execute_intent():
    agent = ADKAgent()
    widgets = agent.execute_intent("Test query")
    assert len(widgets) >= 2
    assert widgets[0].type == "metric_card"
    assert widgets[1].type == "action_panel"

def test_tools():
    search_res = search_knowledge_base("analytics")
    assert search_res["status"] == "success"
    metrics_res = query_analytics_metrics("7d")
    assert metrics_res["metrics"]["success_rate"] > 0.9
