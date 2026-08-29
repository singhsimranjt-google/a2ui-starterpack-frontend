# {{PROJECT_TITLE}} (Gemini Enterprise Agent & Renderer)

This project contains Python backend code for **Gemini Enterprise (GE)** integration. Because Gemini Enterprise natively renders cards, widgets, and enterprise UI actions within its portal and extensions, only Python agent and custom renderer code is generated.

## Features
- **Native GE Action Cards**: Generates Gemini Enterprise formatted action buttons and verification badges.
- **Enterprise Grounding & Citations**: Pre-structured citation formats for enterprise datastores.
- **`uv` Package Management**: Fast, reproducible Python dependency resolution.

## Getting Started

### 1. Configure Environment
```bash
cp .env.example .env
# Set your GEMINI_API_KEY and GCP Project credentials
```

### 2. Sync Dependencies with `uv`
```bash
uv sync
```

### 3. Run Sample Agent & Renderer
```bash
uv run python src/agent.py
```

### 4. Run Pytest Suite
```bash
uv run pytest
```
