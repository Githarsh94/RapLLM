import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from llm_logger import LLMLogger

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# gemini-3.5-flash is the reliable text-only model.
# gemini-2.5-flash-image supports native image generation (requires image-capable API access).
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.5-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

llm_logger = LLMLogger(
    ingestion_url=os.getenv("INGESTION_URL", "http://localhost:8001"),
    model_name=TEXT_MODEL,
    provider="google",
)

llm_logger_image = LLMLogger(
    ingestion_url=os.getenv("INGESTION_URL", "http://localhost:8001"),
    model_name=IMAGE_MODEL,
    provider="google",
)

# Only passed to the image model — causes failures if sent to text-only models
image_generation_config = types.GenerateContentConfig(
    response_modalities=["TEXT", "IMAGE"]
)

# Cached after first attempt: True = image model works, False = not available
_image_model_available: bool | None = None


def format_messages_for_gemini(messages: list[dict]) -> list[types.Content]:
    return [
        types.Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[types.Part.from_text(text=msg["content"])],
        )
        for msg in messages
    ]
