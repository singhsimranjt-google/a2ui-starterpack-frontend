"""FastAPI Backend Server for Google ADK & A2UI Weather Agent."""

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
    description="FastAPI Backend for Google ADK Weather Agent streaming A2UI Basic Catalog Schemas",
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


class PromptRequest(BaseModel):
    prompt: str


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


@app.post("/api/agent/chat", response_model=PromptResponse)
async def execute_agent_chat(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    if hasattr(root_agent, "generate_response") and callable(
        getattr(root_agent, "generate_response")
    ):
        res = await root_agent.generate_response(request.prompt)
        return PromptResponse(success=True, text=res["text"], a2ui=res.get("a2ui"))

    if not genai_client:
        return PromptResponse(
            success=True,
            text="⚠️ **Gemini API Key Required**: Please configure `GEMINI_API_KEY` in your environment or `.env` file.",
            a2ui=None,
        )

    try:
        response = genai_client.models.generate_content(
            model=root_agent.model,
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=root_agent.instruction,
                temperature=0.2,
                max_output_tokens=8192,
                tools=getattr(root_agent, "tools", None),
            ),
        )
        raw_text = response.text or ""
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
