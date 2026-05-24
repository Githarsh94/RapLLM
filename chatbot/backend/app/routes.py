from fastapi import APIRouter, HTTPException

from .models import (
    CreateConversationRequest,
    SendMessageRequest,
    ConversationResponse,
    MessageResponse,
)
from .database import (
    create_conversation,
    list_conversations,
    get_conversation,
    get_messages,
    save_message,
    cancel_conversation,
)
from .gemini_client import client, llm_logger, format_messages_for_gemini

router = APIRouter()


def _to_conv_response(conv: dict, messages: list[dict] | None = None) -> ConversationResponse:
    return ConversationResponse(
        id=conv["id"],
        title=conv["title"],
        status=conv["status"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        message_count=conv.get("message_count"),
        messages=(
            [
                MessageResponse(
                    id=m["id"],
                    conversation_id=m["conversation_id"],
                    role=m["role"],
                    content=m["content"],
                    created_at=m["created_at"],
                )
                for m in messages
            ]
            if messages is not None
            else None
        ),
    )


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation_endpoint(body: CreateConversationRequest):
    conv = create_conversation(body.title or "New Conversation")
    return _to_conv_response(conv)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations_endpoint():
    return [_to_conv_response(c) for c in list_conversations()]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(conversation_id: str):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _to_conv_response(conv, get_messages(conversation_id))


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: str, body: SendMessageRequest):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot send messages to a cancelled conversation")

    user_msg = save_message(conversation_id, "user", body.content)

    all_messages = get_messages(conversation_id)
    contents = format_messages_for_gemini(all_messages)

    response_text, _ = await llm_logger.call(
        contents=contents,
        conversation_id=conversation_id,
        message_id=user_msg["id"],
        gemini_client=client,
    )

    assistant_msg = save_message(conversation_id, "assistant", response_text)

    return MessageResponse(
        id=assistant_msg["id"],
        conversation_id=assistant_msg["conversation_id"],
        role=assistant_msg["role"],
        content=assistant_msg["content"],
        created_at=assistant_msg["created_at"],
    )


@router.patch("/conversations/{conversation_id}/cancel", response_model=ConversationResponse)
async def cancel_conversation_endpoint(conversation_id: str):
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = cancel_conversation(conversation_id)
    return _to_conv_response(updated)
