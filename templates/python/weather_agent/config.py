"""Configuration settings for Google ADK Weather Agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Runtime configuration for the weather agent service."""

    agent_id: str = "weather_agent"
    agent_name: str = "Weather Agent"
    agent_description: str = (
        "Google ADK Agent providing real-time weather information and A2UI Basic Catalog components."
    )
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))


config = Config()
