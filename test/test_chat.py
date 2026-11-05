"""Tests for the chat endpoints."""

from unittest.mock import AsyncMock, patch


def test_chat_endpoint(client):
    """Verify the chat endpoint calls the agent and returns a valid response."""
    mock_response = {
        "answer": "Hello, how can I help you?",
        "token_usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        "tool_calls": [],
    }

    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = mock_response

    with patch("routers.chat.service.initialize", new_callable=AsyncMock), \
         patch("routers.chat.service.build_pipeline", return_value=mock_graph):
        response = client.post("/chat/", json={"query": "Hello"})
        assert response.status_code == 200
        assert response.json() == mock_response
