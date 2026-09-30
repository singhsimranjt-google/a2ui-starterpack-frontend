"""Configuration settings for Google ADK Todo List Agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Runtime configuration for the todo list agent service."""

    agent_id: str = "hotel_portfolio_manager"
    agent_name: str = "Hotel Portfolio Manager"
    agent_description: str = "Generated A2UI Agent."
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8080")))


config = Config()