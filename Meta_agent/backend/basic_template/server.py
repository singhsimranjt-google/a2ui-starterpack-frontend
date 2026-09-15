"""FastAPI Backend Server for Google ADK & A2UI Pizza Agent."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types, Client
from pydantic import BaseModel

from . import a2ui_utils
from .agent import root_agent
from .config import config

app = FastAPI(
    title=f"{config.agent_name} API",
    description="FastAPI Backend for Google ADK Pizza Agent streaming A2UI Basic Catalog Schemas",
    version="0.1.0",
)

# Enable CORS for Angular (4200) frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# genai_client = Client(api_key=config.api_key) if config.api_key else None
try:
    genai_client = Client()
except Exception:
    genai_client = None


class PromptResponse(BaseModel):
    success: bool
    text: str
    a2ui: Optional[List[Dict[str, Any]]] = None


@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "agent": root_agent.name,
        "model": root_agent.model,
        "catalog": "Basic Catalog v0.9",
    }


@app.get("/api/agent/info")
def agent_info():
    """
    Single source of truth for this agent's identity.

    Any frontend (Angular, React, CLI, ...) reads its display name from here at runtime,
    so the generator never has to rewrite frontend source files.
    """
    return {
        "id": config.agent_id,
        "name": config.agent_name,
        "description": config.agent_description,
        "model": root_agent.model,
    }

# Create a global variable to store the persistent chat session
class PromptRequest(BaseModel):
    prompt: str
    action: Optional[Dict[str, Any]] = None
    session_id: str = "default_session"  # Add this!

# Replace `chat_session = None` with a dictionary
active_sessions = {}

@app.post("/api/agent/chat", response_model=PromptResponse)
async def execute_agent_chat(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    prompt_text = request.prompt
    if request.action:
        prompt_text += f"\n\n[USER ACTION TRIGGERED]: {request.action}"

    if not genai_client:
        return PromptResponse(
            success=True,
            text="⚠️ **Gemini API Key Required**",
            a2ui=None,
        )

    try:
        # print("\n" + "="*50)
        # print("🚀 [LLM REQUEST] PROMPT SENT TO MODEL:")
        # print(prompt_text)
        # print("="*50)
        
        session_id = request.session_id
        
        # Initialize a new chat session for this specific user if they don't have one
        if session_id not in active_sessions:
            active_sessions[session_id] = genai_client.chats.create(
                model=root_agent.model,
                config=types.GenerateContentConfig(
                    system_instruction=root_agent.instruction,
                    temperature=0.2,
                    max_output_tokens=8192,
                    tools=getattr(root_agent, "tools", None),
                )
            )
        
        # Grab the specific user's chat session
        user_chat_session = active_sessions[session_id]
        
        # Send the message using their personal persistent session
        response = user_chat_session.send_message(prompt_text)
        raw_text = response.text or ""
        
        # print("\n" + "="*50)
        # print("🤖 [LLM RESPONSE] RAW TEXT RECEIVED:")
        # print(raw_text)
        # print("="*50)
        
        clean_text, a2ui_data = a2ui_utils.parse_a2ui_response(raw_text)
        return PromptResponse(success=True, text=clean_text, a2ui=a2ui_data)
    except Exception as e:
        return PromptResponse(
            success=False, text=f"Error during model generation: {str(e)}", a2ui=None
        )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "weather_agent.server:app",
        host=config.server_host,
        port=config.server_port,
        reload=True,
    )
