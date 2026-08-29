"""Configuration management for Google ADK & A2UI Agent."""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class AgentConfig(BaseModel):
    """Runtime configuration for the agent service."""
    agent_name: str = Field(default="{{PROJECT_TITLE}}", description="Human-readable agent title")
    model_name: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        description="Google Gemini model identifier"
    )
    api_key: str = Field(
        default=os.getenv("GEMINI_API_KEY", ""),
        description="Google Gemini API Key"
    )
    server_host: str = Field(
        default=os.getenv("SERVER_HOST", "0.0.0.0"),
        description="Backend server host"
    )
    server_port: int = Field(
        default=int(os.getenv("SERVER_PORT", "8000")),
        description="Backend server port"
    )
    use_vertex_ai: bool = Field(
        default=os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true",
        description="Whether to route through Vertex AI"
    )
    gcp_project: str = Field(
        default=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        description="Google Cloud Project ID"
    )
    gcp_location: str = Field(
        default=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        description="Google Cloud Location"
    )

config = AgentConfig()
