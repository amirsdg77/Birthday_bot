"""
LLM Service — handles Gemini API connection via LangChain.
Swap the model name in .env (GEMINI_MODEL) to change the model.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    """
    Returns a configured ChatGoogleGenerativeAI instance.
    Model and temperature are pulled from .env via settings.
    """
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.TEMPERATURE,
        max_output_tokens=settings.MAX_TOKENS,
    )
