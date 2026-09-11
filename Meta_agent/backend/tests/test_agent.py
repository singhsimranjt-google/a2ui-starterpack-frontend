"""Tests for Google ADK & A2UI Weather Agent."""

import pytest
from weather_agent.agent import root_agent
from weather_agent.config import config
from weather_agent.tools import get_current_weather


def test_agent_initialization():
    assert root_agent is not None
    assert root_agent.name == config.agent_id
    assert root_agent.model == config.gemini_model


def test_tools():
    weather = get_current_weather("Delhi")
    assert weather["status"] == "success"
    assert weather["city"] == "Delhi"
    assert "temperature" in weather
    assert "condition" in weather
