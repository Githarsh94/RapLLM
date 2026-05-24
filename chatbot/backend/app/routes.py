import json
import sys

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
from . import gemini_client as _gc
from .gemini_client import (
    client,
    llm_logger,
    llm_logger_image,
    format_messages_for_gemini,
    image_generation_config,
)

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


_IMAGE_UNAVAILABLE_WARNING = "Image generation is not supported on this plan or model."
_NO_RESPONSE_MESSAGE = (
    "The model was also unable to generate a text response for this request. "
    "Please try rephrasing your prompt."
)


def _wrap_with_warning(text: str) -> str:
    """Plain text response + image-unavailable warning."""
    return json.dumps({
        "__gemini_parts": True,
        "parts": [
            {"type": "warning", "text": _IMAGE_UNAVAILABLE_WARNING + " Here is a text response instead."},
            {"type": "text",    "text": text},
        ],
    })


def _make_no_response_content() -> str:
    """Used when image model is unavailable AND text model also returned no content."""
    return json.dumps({
        "__gemini_parts": True,
        "parts": [
            {"type": "warning", "text": _IMAGE_UNAVAILABLE_WARNING},
            {"type": "warning", "text": _NO_RESPONSE_MESSAGE},
        ],
    })


async def _call_model(contents, conversation_id, message_id, model: str | None = None) -> str:
    """Route to the appropriate Gemini model.

    If `model` is explicitly specified by the user, skip the image probe entirely
    and call that model directly as a text model.

    Otherwise: try image model first (probed once, result cached); fall back to
    text model permanently if unavailable.  Warning blocks are only attached on
    the single probe-and-fail call.
    """
    if model is not None:
        # User-selected model — call it directly, no image probe
        from llm_logger import LLMLogger as _LLMLogger
        import os as _os
        custom_logger = _LLMLogger(
            ingestion_url=_os.getenv("INGESTION_URL", "http://localhost:8001"),
            model_name=model,
            provider="google",
        )
        try:
            text, _ = await custom_logger.call(
                contents=contents,
                conversation_id=conversation_id,
                message_id=message_id,
                gemini_client=client,
            )
            return text
        except Exception as e:
            print(
                f"[routes] user-selected model '{model}' failed "
                f"({type(e).__name__}): {e}",
                file=sys.stderr,
            )
            raise

    just_discovered_fallback = False

    if _gc._image_model_available is not False:
        try:
            text, _ = await llm_logger_image.call(
                contents=contents,
                conversation_id=conversation_id,
                message_id=message_id,
                gemini_client=client,
                config=image_generation_config,
            )
            _gc._image_model_available = True
            return text
        except Exception as e:
            print(f"[routes] image model unavailable ({e}), using text model for all future requests", file=sys.stderr)
            _gc._image_model_available = False
            just_discovered_fallback = True

    # Route to text model — either permanently (cached) or as fallback on discovery
    try:
        text, _ = await llm_logger.call(
            contents=contents,
            conversation_id=conversation_id,
            message_id=message_id,
            gemini_client=client,
        )
        # Only wrap with warning on the discovery call; all later calls are clean
        if just_discovered_fallback:
            return _wrap_with_warning(text)
        return text
    except Exception:
        if just_discovered_fallback:
            # Image model unavailable AND text model returned no content
            return _make_no_response_content()
        raise  # Genuine text-model error on a normal request → let routes return 502


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

    try:
        response_text = await _call_model(
            contents=contents,
            conversation_id=conversation_id,
            message_id=user_msg["id"],
            model=body.model or None,
        )
    except Exception as e:
        print(
            f"[routes] 502 for conversation {conversation_id} "
            f"(model={body.model or 'default'}, {type(e).__name__}): {e}",
            file=sys.stderr,
        )
        raise HTTPException(status_code=502, detail=str(e))

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
