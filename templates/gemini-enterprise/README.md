# {{PROJECT_TITLE}} (Gemini Enterprise / Google ADK Agent)

This project contains the Python agent implementation for **Gemini Enterprise** with **Material A2UI v0.9.1** card rendering.

## Architecture
- `src/agent.py`: Core agent reasoning loop, conversation router, and Material A2UI schema builder.
- `src/config.py`: Environment configuration and Gemini model selector (`gemini-2.5-flash`).
- `src/prompt.py`: System prompt, role instructions, and Material v0.9.1 schema guidelines.
- `src/tools.py`: Tool definitions (e.g. `get_agent_capabilities`).
- `pyproject.toml`: Modern Python project specification (managed with `uv`).

## Quick Start

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY (optional for local deterministic mode)
```

### 2. Install & Sync Dependencies
```bash
uv sync
```

### 3. Run Interactive Agent
```bash
uv run python src/agent.py
```

### 4. Run Test Suite
```bash
uv run pytest
```
