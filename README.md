# goog-adk-a2ui-starter

> 🚀 **Official Scaffolding CLI for Google Agent Development Kit (ADK) & Agent-to-User Interface (A2UI) Applications**

`goog-adk-a2ui-starter` provides an instant, zero-dependency scaffolding workflow for creating:
1. **Frontend Applications**: Standalone **Angular** or **React + Vite (TypeScript)** clients ready to render streaming A2UI schema cards.
2. **Python Agents**: **Google ADK + A2UI** agents with FastAPI backend servers, managed by `uv`.
3. **Gemini Enterprise (GE) Agents**: Dedicated Python agent code and custom response renderers for **Gemini Enterprise**.
4. **Full-Stack Applications**: Composed Frontend + Python ADK agent monorepo.

---

## ⚡ Quick Start

Run instantly without global installation:

```bash
npx goog-adk-a2ui-starter
```

or via npm:

```bash
npm create goog-adk-a2ui-starter
```

---

## 🎯 Selection Flow & Options

```text
┌────────────────────────────────────────────────────────┐
│               goog-adk-a2ui-starter                    │
│   Scaffolding Angular, React, Python & GE UI Agents    │
└────────────────────────────────────────────────────────┘

? What do you want to create?
  ❯ Frontend (Angular / React)
    Python Agent (Google ADK + A2UI / Gemini Enterprise)
    Full stack (Frontend + Python Agent)

[Frontend Selection]
  ? Which frontend?
    ❯ Angular (Standalone Component Architecture)
      React (React 18/19 + TypeScript + Vite)

[Python Selection]
  ? Which agent / renderer architecture?
    ❯ Google ADK + A2UI Agent (Standard FastAPI/SSE + A2UI Payload)
      Gemini Enterprise (GE Renderer - Python code only)

[Full Stack Selection]
  ? Which frontend framework for full-stack?
    ❯ Angular
      React
```

---

## 📁 Generated Project Layouts

### 1. Frontend: Angular (`angular`)
```text
my-angular-app/
├── src/
│   ├── app/
│   │   ├── app.component.ts      # A2UI reactive Signal state & event triggers
│   │   ├── app.component.html    # Action card stream template
│   │   └── app.component.css
│   ├── index.html
│   ├── main.ts                   # Standalone bootstrap
│   └── styles.css
├── angular.json
├── package.json
└── tsconfig.json
```
**Start Command**:
```bash
cd my-angular-app
npm install
npm start
```

---

### 2. Frontend: React (`react`)
```text
my-react-app/
├── src/
│   ├── components/
│   │   └── A2UIRenderer.tsx      # Schema-driven dynamic UI card renderer
│   ├── App.tsx                   # Interactive ADK intent dispatcher
│   ├── App.css
│   ├── index.css
│   └── main.tsx
├── vite.config.ts
├── package.json
└── tsconfig.json
```
**Start Command**:
```bash
cd my-react-app
npm install
npm run dev
```

---

### 3. Python: Google ADK + A2UI (`python`)
```text
my-python-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py                  # Google ADK agent with Gemini reasoning
│   └── server.py                 # FastAPI SSE streaming server
├── tests/
│   └── test_agent.py
├── pyproject.toml                # uv package manager configuration
├── .env.example
└── README.md
```
**Start Command**:
```bash
cd my-python-agent
cp .env.example .env
uv sync
uv run uvicorn src.server:app --reload --port 8000
```

---

### 4. Python: Gemini Enterprise (`gemini-enterprise`)
*Note: Because Gemini Enterprise handles UI rendering natively in its enterprise portal and extensions, only Python agent logic and enterprise renderers are generated.*

```text
my-ge-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py                  # GE Agent with enterprise tools & grounding
│   └── ge_renderer.py            # Gemini Enterprise action card serializer
├── tests/
│   └── test_agent.py
├── pyproject.toml                # uv configuration
├── .env.example
└── README.md
```
**Start Command**:
```bash
cd my-ge-agent
cp .env.example .env
uv sync
uv run python src/agent.py
```

---

### 5. Full-Stack (`fullstack`)
```text
my-fullstack-app/
├── frontend/                     # Angular or React application
├── backend/                      # Google ADK + A2UI Python agent
├── package.json                  # Root orchestration scripts
└── README.md
```
**Start Command**:
```bash
cd my-fullstack-app

# Terminal 1 (Backend):
cd backend && cp .env.example .env && uv sync && uv run uvicorn src.server:app --reload --port 8000

# Terminal 2 (Frontend):
cd frontend && npm install && npm run dev
```

---

## 🛠 Documentation
- Complete Architecture: [architecture.md](architecture.md)
- Complete Implementation Plan & Server Commands: [plan.md](plan.md)

---

## 📜 License
Apache-2.0
