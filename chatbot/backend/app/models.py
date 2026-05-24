from pydantic import BaseModel
from typing import Optional


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    messages: Optional[list[MessageResponse]] = None
    message_count: Optional[int] = None
