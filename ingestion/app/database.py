import os
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


def insert_inference_log(payload_dict: dict) -> dict:
    for field in ("request_timestamp", "response_timestamp"):
        val = payload_dict.get(field)
        if val is not None and hasattr(val, "isoformat"):
            payload_dict[field] = val.isoformat()

    result = supabase.table("inference_logs").insert(payload_dict).execute()
    if not result.data:
        raise RuntimeError("Insert returned no data")
    return result.data[0]
