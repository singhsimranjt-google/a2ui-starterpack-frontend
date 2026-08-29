"""FastAPI Backend Server for Google ADK & A2UI Streaming."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from src.config import config
from src.agent import ADKAgent
from src.agent_executor import A2UIWidget

app = FastAPI(
    title=f"{config.agent_name} API",
    description="FastAPI Backend for Google ADK Agent streaming A2UI Schemas",
    version="0.1.0"
)

# Enable CORS for frontend clients (Angular: 4200, React: 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ADKAgent()

class PromptRequest(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    success: bool
    widgets: List[A2UIWidget]


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "agent": config.agent_name,
        "model": config.model_name
    }


@app.post("/api/agent/chat", response_model=PromptResponse)
def execute_agent_chat(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    widgets = agent.execute_intent(request.prompt)
    return PromptResponse(success=True, widgets=widgets)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host=config.server_host, port=config.server_port, reload=True)
