from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Models for request/response
class ChatMessage(BaseModel):
    content: str
    role: str = "user"
    timestamp: Optional[str] = None

class ChatSession(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str
    is_active: bool
    messages: List[Dict[str, Any]] = []

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None