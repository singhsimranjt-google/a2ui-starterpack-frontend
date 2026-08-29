"""Tool definitions and tool registry for Google ADK Agent."""

from typing import Dict, Any, List, Callable
from pydantic import BaseModel, Field

class ToolDefinition(BaseModel):
    """Metadata describing an ADK agent tool."""
    name: str
    description: str
    parameters: Dict[str, Any]


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """Searches the enterprise knowledge base or mock datastore for relevant documents."""
    return {
        "status": "success",
        "query": query,
        "results": [
            {
                "title": f"Operations Guide: {query}",
                "snippet": f"Found verified operational context matching '{query}'.",
                "score": 0.94
            }
        ]
    }


def query_analytics_metrics(timeframe: str = "30d") -> Dict[str, Any]:
    """Retrieves operational and performance analytics metrics."""
    return {
        "timeframe": timeframe,
        "metrics": {
            "total_requests": 14520,
            "avg_latency_ms": 128,
            "success_rate": 0.998,
            "active_users": 1840
        }
    }


# Tool Registry
TOOL_REGISTRY: Dict[str, Callable[..., Any]] = {
    "search_knowledge_base": search_knowledge_base,
    "query_analytics_metrics": query_analytics_metrics,
}

AVAILABLE_TOOLS: List[ToolDefinition] = [
    ToolDefinition(
        name="search_knowledge_base",
        description="Searches domain knowledge base for relevant context and documentation",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"}
            },
            "required": ["query"]
        }
    ),
    ToolDefinition(
        name="query_analytics_metrics",
        description="Queries telemetry and system analytics metrics",
        parameters={
            "type": "object",
            "properties": {
                "timeframe": {"type": "string", "description": "Metrics timeframe e.g. 7d, 30d"}
            }
        }
    )
]
