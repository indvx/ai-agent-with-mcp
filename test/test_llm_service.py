"""Tests for LLMService chat model initialization."""

from unittest.mock import patch
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from service.llm_service import LLMService


def test_openai_chat_model():
    """Verify openai chat model is returned for default/openai provider."""
    with patch("service.llm_service.settings.llm_provider", "openai"), \
         patch("service.llm_service.settings.llm_api_key", "test-api-key"), \
         patch("service.llm_service.settings.llm_model", "gpt-4o"), \
         patch("service.llm_service.settings.llm_base_url", "https://api.openai.com/v1"), \
         patch("service.llm_service.settings.llm_temperature", 0.5):
        service = LLMService()
        model = service.get_chat_model()
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o"
        assert model.temperature == 0.5


def test_gemini_chat_model():
    """Verify gemini chat model is returned when provider is gemini."""
    with patch("service.llm_service.settings.llm_provider", "gemini"), \
         patch("service.llm_service.settings.llm_api_key", "test-gemini-key"), \
         patch("service.llm_service.settings.llm_model", "gemini-1.5-flash"), \
         patch("service.llm_service.settings.llm_base_url", None), \
         patch("service.llm_service.settings.llm_temperature", 0.2):
        service = LLMService()
        model = service.get_chat_model()
        assert isinstance(model, ChatGoogleGenerativeAI)
        assert model.model == "gemini-1.5-flash"
        assert model.temperature == 0.2
