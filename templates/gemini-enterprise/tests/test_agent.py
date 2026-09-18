"""Tests for Google ADK / Gemini Enterprise Agent."""

import pytest
from src.agent import Agent
from src.config import config
from src.tools import get_agent_capabilities

@pytest.mark.asyncio
async def test_agent_greeting():
    agent = Agent()
    res = await agent.generate_response("Hello!")
    assert "Hello!" in res["text"]
    assert res["a2ui"] is None

@pytest.mark.asyncio
async def test_agent_capabilities_card():
    agent = Agent()
    res = await agent.generate_response("What are your capabilities?")
    assert res["a2ui"] is not None
    assert len(res["a2ui"]) == 2
    create_surface = res["a2ui"][0]["createSurface"]
    assert "material_catalog.json" in create_surface["catalogId"]
    
    update_comps = res["a2ui"][1]["updateComponents"]
    comps = update_comps["components"]
    comp_types = [c["component"] for c in comps]
    assert "MaterialCard" in comp_types
    assert "MaterialText" in comp_types
    assert "MaterialIcon" in comp_types
    assert "MaterialButton" in comp_types

def test_tools():
    caps = get_agent_capabilities()
    assert caps["status"] == "success"
    assert caps["catalog_version"] == "v0.9.1"
    assert len(caps["capabilities"]) >= 5