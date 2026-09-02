"""Configuration settings for Gemini Enterprise / Google ADK Agent."""

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class Config:
    """Runtime configuration for the agent service."""
    agent_id: str = "{{PROJECT_NAME}}"
    agent_name: str = "{{PROJECT_TITLE}}"
    agent_description: str = "An intelligent agent with Google ADK and Material A2UI v0.9.1 card rendering capabilities."
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    use_vertexai: bool = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    gcp_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gcp_region: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))

config = Config()
