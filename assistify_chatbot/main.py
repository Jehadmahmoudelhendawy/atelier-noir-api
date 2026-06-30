import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from agent import ChatbotAgent

load_dotenv()

app = FastAPI(title="Assistify Chatbot Microservice")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ChatbotAgent()

# Load products once for matching
dir_path = os.path.dirname(os.path.abspath(__file__))
products_path = os.path.join(dir_path, "products.json")
products_list = []
if os.path.exists(products_path):
    try:
        with open(products_path, "r", encoding="utf-8") as f:
            products_list = json.load(f)
    except Exception as e:
        print("Failed to load products list:", e)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    conversation_id: Optional[Any] = None
    source: Optional[str] = "web"

class ChatResponse(BaseModel):
    success: bool
    response: str
    reply: str
    conversation_id: str
    products: list = []
    intent: str
    sentiment: str
    recommendations: list = []
    confidence: Dict[str, float] = {}
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

def match_products(message: str, reply: str) -> list:
    msg = message.lower()
    rep = reply.lower()
    text = msg + " " + rep
    
    matched = []
    for p in products_list:
        name = p.get('name', '').lower()
        color = p.get('color', '').lower()
        category = p.get('category_display', '').lower()
        
        # If product name or color + category combo is in conversation text
        if name in text:
            matched.append(p)
        elif color in text and (category in text or any(word in text for word in name.split())):
            matched.append(p)
            
    # De-duplicate
    unique_matched = []
    seen = set()
    for p in matched:
        pid = p.get('id')
        if pid not in seen:
            seen.add(pid)
            unique_matched.append({
                "id": p.get("id"),
                "name": p.get("name", ""),
                "price": p.get("price", 0),
                "currency": p.get("currency", "€"),
                "color": p.get("color", ""),
                "gender": p.get("gender", "unisex"),
                "image_url": p.get("image_url", ""),
                "category_display": p.get("category_display", "")
            })
            
    unique_matched.sort(key=lambda x: x.get('price', 0))
    return unique_matched[:5]

@app.post("/chat", response_model=ChatResponse)
@app.post("/api/chat", response_model=ChatResponse) # support both routes
async def chat_endpoint(request: ChatRequest):
    cid = str(request.conversation_id or "")
    session_id = f"user_{request.user_id}" if request.user_id else f"conv_{cid}"
    
    result = agent.process_message(request.message, session_id, source=request.source)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
    ai_response = result.get("response", "")
    matched_cards = match_products(request.message, ai_response)
    
    return ChatResponse(
        success=True,
        response=ai_response,
        reply=ai_response,
        conversation_id=cid,
        products=matched_cards,
        intent=result.get("intent", "inquiry"),
        sentiment=result.get("sentiment", "neutral"),
        recommendations=result.get("recommendations", []),
        confidence=result.get("confidence", {}),
        metadata=result.get("metadata", {})
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
