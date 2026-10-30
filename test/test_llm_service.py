import os
import pytest
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from service.llm_service import LLMService


def test_llm_service_initialization_with_explicit_provider():
    service = LLMService(provider="gemini")
    assert service.provider == "gemini"


def test_llm_service_openai_chat_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    service = LLMService(provider="openai")
    model = service.get_chat_model()

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-4o-mini"
    assert model.openai_api_key.get_secret_value() == "test-openai-key"


def test_llm_service_groq_chat_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    service = LLMService(provider="groq")
    model = service.get_chat_model()


def test_llm_service_gemini_chat_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-flash")

    service = LLMService(provider="gemini")
    model = service.get_chat_model()

    assert isinstance(model, ChatGoogleGenerativeAI)
    assert model.model == "gemini-1.5-flash"


def test_llm_service_unsupported_provider():
    service = LLMService(provider="unsupported_vendor")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        service.get_chat_model()


def test_provider_detection_prefers_openai_key_when_present(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test-groq")

    service = LLMService()
    assert service.provider == "openai"


def test_provider_detection_uses_groq_when_openai_key_absent(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test-groq")

    service = LLMService()
    assert service.provider == "groq"


def test_provider_detection_honors_explicit_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")

    service = LLMService()
    assert service.provider == "groq"


def test_openai_model_fallback_for_groq_naming(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "openai/gpt-oss-20b")

    service = LLMService(provider="openai")
    model = service.get_chat_model()
    # Should safely sanitize to gpt-4o when hitting OpenAI directly
    assert model.model_name == "gpt-4o"
