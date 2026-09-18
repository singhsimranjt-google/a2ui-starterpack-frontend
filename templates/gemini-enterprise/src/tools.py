"""Tool definitions for Gemini Enterprise / Google ADK Agent."""

from typing import Any, Dict

def get_agent_capabilities(scope: str = "all") -> Dict[str, Any]:
    """Retrieves the official system capabilities, components, and supported A2UI v0.9.1 features.
    
    Args:
        scope: The scope of capabilities to retrieve (e.g. 'all', 'ui', 'reasoning').
        
    Returns:
        A dictionary containing capabilities, supported widgets, and catalog version.
    """
    return {
        "status": "success",
        "scope": scope,
        "catalog_version": "v0.9.1",
        "capabilities": [
            "Dynamic Material Card generation & streaming",
            "Rich interactive buttons and event dispatching",
            "Multi-column responsive layouts with MaterialColumn & MaterialRow",
            "Material UI icons (heart, favorite, thumb_up, verified) and visual badges",
            "Two-way state binding and form input processing"
        ],
        "highlights": {
            "developer_experience": "Instant scaffolding with zero external CLI dependencies",
            "enterprise_ready": "Gemini 2.5 Flash / Pro reasoning engine integration",
            "ui_catalog": "Material Design v0.9.1 specification"
        }
    }