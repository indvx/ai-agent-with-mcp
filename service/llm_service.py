import os
from typing import Optional
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class LLMService:
    """Factory service for chat models and raw API clients across LLM providers.

    Supports OpenAI, Google Gemini, and Groq (via OpenAI-compatible API).
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    def openai_chat_model(self, temperature: Optional[float] = None) -> ChatOpenAI:
        """Builds an OpenAI ChatOpenAI instance."""
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        temp = self.temperature if temperature is None else temperature

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
        )

    def groq_chat_model(self, temperature: Optional[float] = None) -> ChatOpenAI:
        """Builds a ChatOpenAI instance pointing to Groq's OpenAI-compatible API."""
        model_name = os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        temp = self.temperature if temperature is None else temperature

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
        )

    def gemini_chat_model(self, temperature: Optional[float] = None) -> ChatGoogleGenerativeAI:
        """Builds a Google Gemini ChatGoogleGenerativeAI instance."""
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        temp = self.temperature if temperature is None else temperature

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temp,
            max_retries=2,
        )

    def get_chat_model(
        self,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> BaseChatModel:
        """Returns the appropriate LangChain chat model based on the active provider."""
        target_provider = (provider or self.provider).lower()

        if target_provider == "groq":
            return self.groq_chat_model(temperature=temperature)
        if target_provider == "gemini":
            return self.gemini_chat_model(temperature=temperature)
        if target_provider == "openai":
            return self.openai_chat_model(temperature=temperature)

        raise ValueError(f"Unsupported LLM provider: {target_provider}. Expected 'openai', 'groq', or 'gemini'.")