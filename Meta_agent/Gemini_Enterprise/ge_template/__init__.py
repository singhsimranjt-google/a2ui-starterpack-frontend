"""Clinic Scheduling Agent package.

ADK discovers agents by looking for `root_agent` in either
`<agents_dir>/<agent_name>/agent.py` or `<agents_dir>/<agent_name>/__init__.py`.

Because this project keeps its code one level deeper in `src/`, we re-export
`root_agent` here so `adk web` / `adk run` can find it:

    cd /usr/local/google/home/sidchaudhary/Desktop/A2UI/Gemini_enterprise
    adk web .
"""

from .src.agent import root_agent

__all__ = ["root_agent"]
