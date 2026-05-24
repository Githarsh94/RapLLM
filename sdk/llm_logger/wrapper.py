import asyncio
import base64
import json
import time
from datetime import datetime, timezone
from typing import Optional, Tuple

from .models import InferenceLogPayload
from .dispatcher import LogDispatcher


class LLMLogger:
    def __init__(
        self,
        ingestion_url: str,
        model_name: str = "gemini-2.5-flash-image",
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
        config=None,
    ) -> Tuple[str, InferenceLogPayload]:
        request_timestamp = datetime.now(timezone.utc)
        start = time.monotonic()

        input_preview = ""
        if contents:
            last = contents[-1]
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
            call_kwargs: dict = {"model": self.model_name, "contents": contents}
            if config is not None:
                call_kwargs["config"] = config

            response = await gemini_client.aio.models.generate_content(**call_kwargs)
            latency_ms = int((time.monotonic() - start) * 1000)
            response_timestamp = datetime.now(timezone.utc)

            # Parse all parts — a response can contain text, images, or both
            text_parts: list[str] = []
            image_parts: list[dict] = []

            for part in (response.parts or []):
                if part.text:
                    text_parts.append(part.text)
                elif part.inline_data is not None:
                    img_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                    image_parts.append({
                        "type": "image",
                        "data": img_b64,
                        "mime_type": part.inline_data.mime_type or "image/png",
                    })

            if not text_parts and not image_parts:
                raise ValueError(
                    "Model returned no content. The request may have been blocked or unsupported."
                )

            if image_parts:
                # Encode as structured JSON so the frontend can render images
                structured: list[dict] = [{"type": "text", "text": t} for t in text_parts]
                structured += image_parts
                output_text = json.dumps({"__gemini_parts": True, "parts": structured})
                output_preview = ("[image]" + (" " + " ".join(text_parts))[:400]).strip()
            else:
                output_text = "".join(text_parts)
                output_preview = output_text[:500]

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
                output_preview=output_preview,
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
