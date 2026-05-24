from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InferenceLogPayload(BaseModel):
    conversation_id: str
    message_id: Optional[str] = None
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    request_timestamp: datetime
    response_timestamp: datetime
    status: str
    error_message: Optional[str] = None
    input_preview: str
    output_preview: Optional[str] = None
    raw_metadata: Optional[dict] = {}
