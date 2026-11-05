import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import settings


class LLMService:
    """Factory service for chat models and raw API clients across LLM providers, supports OpenAI, Google Gemini."""

    def __init__(self):
        self._provider = settings.llm_provider.strip().lower()
        self._temperature = float(settings.llm_temperature)
        self._api_key = settings.llm_api_key.strip()
        self._base_url = settings.llm_base_url.strip() if settings.llm_base_url else None
        self._model = settings.llm_model.strip()

    def openai_chat_model(self) -> ChatOpenAI:
        """Builds an OpenAI ChatOpenAI instance."""

        return ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            temperature=self._temperature,
        )

    def gemini_chat_model(self) -> ChatGoogleGenerativeAI:
        """Builds a Google Gemini ChatGoogleGenerativeAI instance."""
        return ChatGoogleGenerativeAI(
            model=self._model,
            google_api_key=self._api_key,
            temperature=self._temperature,
        )

    def get_chat_model(self) -> BaseChatModel:
        """Returns the appropriate LangChain chat model based on the active provider."""
        if self._provider == "gemini":
            return self.gemini_chat_model()
        return self.openai_chat_model()