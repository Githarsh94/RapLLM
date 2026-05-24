import os
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _make_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)


supabase: Client = _make_client()


def create_conversation(title: str) -> dict:
    result = supabase.table("conversations").insert({"title": title, "status": "active"}).execute()
    return result.data[0]


def list_conversations() -> list[dict]:
    conversations = (
        supabase.table("conversations")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    for conv in conversations:
        count_result = (
            supabase.table("messages")
            .select("id", count="exact")
            .eq("conversation_id", conv["id"])
            .execute()
        )
        conv["message_count"] = count_result.count or 0
    return conversations


def get_conversation(conversation_id: str) -> Optional[dict]:
    result = supabase.table("conversations").select("*").eq("id", conversation_id).execute()
    return result.data[0] if result.data else None


def get_messages(conversation_id: str) -> list[dict]:
    return (
        supabase.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
        .data
    )


def save_message(conversation_id: str, role: str, content: str) -> dict:
    result = supabase.table("messages").insert(
        {"conversation_id": conversation_id, "role": role, "content": content}
    ).execute()
    message = result.data[0]
    supabase.table("conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()
    return message


def cancel_conversation(conversation_id: str) -> dict:
    result = supabase.table("conversations").update({"status": "cancelled"}).eq("id", conversation_id).execute()
    return result.data[0]
