"""Configuration for Gemini Enterprise (GE) Agent & Custom Renderer."""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class GEConfig(BaseModel):
    """Configuration for Gemini Enterprise backend agent."""
    project_name: str = Field(default="{{PROJECT_TITLE}}", description="Enterprise Project / Agent Name")
    model_name: str = Field(default=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"), description="Model name")
    api_key: str = Field(default=os.getenv("GEMINI_API_KEY", ""), description="Gemini API Key")
    gcp_project: str = Field(default=os.getenv("GOOGLE_CLOUD_PROJECT", ""), description="Google Cloud Project ID")
    gcp_location: str = Field(default=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"), description="GCP Location")
    server_port: int = Field(default=int(os.getenv("PORT", "8080")), description="Serverless container port")

ge_config = GEConfig()
