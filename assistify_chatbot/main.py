from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from agent import ChatbotAgent

load_dotenv()

app = FastAPI(title="Assistify Chatbot Microservice")
agent = ChatbotAgent()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    source: Optional[str] = "web"

class ChatResponse(BaseModel):
    success: bool
    response: str
    intent: str
    sentiment: str
    recommendations: list = []
    confidence: Dict[str, float] = {}
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = f"user_{request.user_id}" if request.user_id else f"conv_{request.conversation_id}"
    
    result = agent.process_message(request.message, session_id, source=request.source)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
    return ChatResponse(
        success=True,
        response=result.get("response", ""),
        intent=result.get("intent", "inquiry"),
        sentiment=result.get("sentiment", "neutral"),
        recommendations=result.get("recommendations", []),
        confidence=result.get("confidence", {}),
        metadata=result.get("metadata", {})
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
