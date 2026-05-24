import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

from llm_logger import LLMLogger

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

llm_logger = LLMLogger(
    ingestion_url=os.getenv("INGESTION_URL", "http://localhost:8001"),
    model_name="gemini-3.5-flash",
    provider="google",
)


def format_messages_for_gemini(messages: list[dict]) -> list[types.Content]:
    return [
        types.Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[types.Part.from_text(text=msg["content"])],
        )
        for msg in messages
    ]
