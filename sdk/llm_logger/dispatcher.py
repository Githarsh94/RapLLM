import sys
import httpx
from .models import InferenceLogPayload


class LogDispatcher:
    def __init__(self, ingestion_url: str):
        self.ingestion_url = ingestion_url.rstrip("/")

    async def dispatch(self, payload: InferenceLogPayload) -> None:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.ingestion_url}/ingest/log",
                    json=payload.model_dump(mode="json"),
                    timeout=5.0,
                )
        except Exception as e:
            print(f"[llm_logger] dispatch failed: {e}", file=sys.stderr)
