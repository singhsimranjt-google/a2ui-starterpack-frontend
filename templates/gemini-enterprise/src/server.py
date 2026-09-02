import sys
import os
# Ensure project root is in python path so 'from src...' imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import Agent
from src.config import config

app = FastAPI(title="Gemini Enterprise Agent API")

# Allow the React frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent (this will use Vertex AI from your .env!)
agent = Agent()

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
        
    print(f"Received prompt from React: {request.prompt}")
    
    # Run the agent logic
    response = await agent.generate_response(request.prompt)
    
    # Return it in the format the React app expects
    print(f"Sending response: {response}")
    return response

if __name__ == "__main__":
    print(f"Starting server on http://127.0.0.1:8080")
    uvicorn.run("src.server:app", host="127.0.0.1", port=8080, reload=True)
