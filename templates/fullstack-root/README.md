# {{PROJECT_TITLE}} (Full-Stack A2UI + Google ADK App)

This is a full-stack project combining a **{{FRONTEND_TYPE}}** frontend client with a **Google ADK & A2UI Python** agent backend.

## Project Structure
```text
{{PROJECT_NAME}}/
├── frontend/        # {{FRONTEND_TYPE}} client rendering dynamic A2UI schemas
├── backend/         # Google ADK Python Agent streaming A2UI action cards
├── package.json     # Orchestration scripts
└── README.md
```

## Quick Start

### 1. Setup Backend
```bash
cd backend
cp .env.example .env
# Edit .env to set your GEMINI_API_KEY
uv sync
uv run uvicorn src.server:app --reload --port 8000
```

### 2. Setup Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev # (or npm start for Angular)
```

Open your browser at:
- Frontend: `http://localhost:5173/` (React) or `http://localhost:4200/` (Angular)
- Backend API Docs: `http://localhost:8000/docs`
