import asyncio
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

from .models import InferenceLogPayload
from .dispatcher import LogDispatcher


class LLMLogger:
    def __init__(
        self,
        ingestion_url: str,
        model_name: str = "gemini-3.5-flash",
        provider: str = "google",
    ):
        self.model_name = model_name
        self.provider = provider
        self.dispatcher = LogDispatcher(ingestion_url)

    async def call(
        self,
        contents: list,
        conversation_id: str,
        gemini_client,
        message_id: Optional[str] = None,
    ) -> Tuple[str, InferenceLogPayload]:
        request_timestamp = datetime.now(timezone.utc)
        start = time.monotonic()

        input_preview = ""
        if contents:
            last = contents[-1]
            # Handle google.genai types.Content objects
            if hasattr(last, "parts"):
                parts = last.parts
                if parts and hasattr(parts[0], "text"):
                    input_preview = (parts[0].text or "")[:500]
            elif isinstance(last, dict):
                parts = last.get("parts", [])
                if parts:
                    part = parts[0]
                    text = part.get("text", "") if isinstance(part, dict) else str(part)
                    input_preview = text[:500]

        try:
            response = await gemini_client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            response_timestamp = datetime.now(timezone.utc)

            output_text = response.text
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
            total_tokens = getattr(usage, "total_token_count", None)

            payload = InferenceLogPayload(
                conversation_id=conversation_id,
                message_id=message_id,
                model=self.model_name,
                provider=self.provider,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                status="success",
                input_preview=input_preview,
                output_preview=output_text[:500] if output_text else None,
                raw_metadata={},
            )
            asyncio.create_task(self.dispatcher.dispatch(payload))
            return output_text, payload

        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            response_timestamp = datetime.now(timezone.utc)

            payload = InferenceLogPayload(
                conversation_id=conversation_id,
                message_id=message_id,
                model=self.model_name,
                provider=self.provider,
                latency_ms=latency_ms,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                status="error",
                error_message=str(e),
                input_preview=input_preview,
                raw_metadata={},
            )
            asyncio.create_task(self.dispatcher.dispatch(payload))
            raise
