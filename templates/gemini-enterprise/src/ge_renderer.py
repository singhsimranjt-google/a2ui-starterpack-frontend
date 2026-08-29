"""Gemini Enterprise (GE) Custom Response & UI Renderer.

Formats raw agent tool outputs and reasoning steps into structured Gemini Enterprise
Action Cards and UI Widgets.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class GEActionButton(BaseModel):
    """Action button rendered inside Gemini Enterprise."""
    label: str
    action_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    style: str = "primary"  # primary, secondary, danger


class GECitation(BaseModel):
    """Enterprise grounding citation."""
    source_title: str
    uri: Optional[str] = None
    snippet: str


class GEEnterpriseCard(BaseModel):
    """Gemini Enterprise Structured Card schema."""
    header: str
    subtitle: Optional[str] = None
    body_markdown: str
    badges: List[str] = Field(default_factory=list)
    citations: List[GECitation] = Field(default_factory=list)
    actions: List[GEActionButton] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class GeminiEnterpriseRenderer:
    """Renderer dedicated to transforming Agent responses for Gemini Enterprise."""

    @staticmethod
    def render_card(
        header: str,
        body: str,
        subtitle: Optional[str] = None,
        badges: Optional[List[str]] = None,
        citations: Optional[List[GECitation]] = None,
        actions: Optional[List[GEActionButton]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GEEnterpriseCard:
        return GEEnterpriseCard(
            header=header,
            subtitle=subtitle,
            body_markdown=body,
            badges=badges or ["Enterprise Verified"],
            citations=citations or [],
            actions=actions or [],
            metadata=metadata or {"renderedBy": "GeminiEnterpriseRenderer"}
        )

    @staticmethod
    def render_error(error_message: str, error_code: str = "AGENT_EXECUTION_ERROR") -> GEEnterpriseCard:
        return GEEnterpriseCard(
            header="Execution Alert",
            subtitle="Error during enterprise tool execution",
            body_markdown=f"**Error Details**: {error_message}",
            badges=["Error", error_code],
            actions=[
                GEActionButton(
                    label="Retry Operation",
                    action_id="RETRY",
                    style="secondary"
                )
            ]
        )
