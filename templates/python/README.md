# {{PROJECT_TITLE}} (Google ADK & A2UI Python Agent)

This is a Python agent service built with the **Google Agent Development Kit (ADK)** pattern, providing dynamic **Agent-to-User Interface (A2UI)** structured schema generation and FastAPI streaming.

## Getting Started

### 1. Prerequisite: Install `uv`
Ensure you have `uv` installed:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Open .env and configure GEMINI_API_KEY
```

### 3. Sync Dependencies
```bash
uv sync
```

### 4. Run CLI Agent
```bash
uv run python src/agent.py
```

### 5. Run FastAPI Backend Server
```bash
uv run uvicorn src.server:app --reload --port 8000
uv run uvicorn weather_agent.server:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 6. Run Unit Tests
```bash
uv run pytest
```
