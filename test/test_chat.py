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


def test_chat_stream_endpoint(client):
    """Verify the streaming chat endpoint returns an SSE stream."""
    async def mock_astream_events(inputs, version):
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": AsyncMock(content="Hello streaming world")},
        }

    mock_graph = AsyncMock()
    mock_graph.astream_events = mock_astream_events

    with patch("routers.chat.service.initialize", new_callable=AsyncMock), \
         patch("routers.chat.service.build_pipeline", return_value=mock_graph):
        response = client.post("/chat/stream", json={"query": "Hello"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert "Hello streaming world" in response.text


def test_chat_validation_empty_query(client):
    """Verify that empty or whitespace-only queries are rejected with 422."""
    response = client.post("/chat/", json={"query": ""})
    assert response.status_code == 422

    response = client.post("/chat/", json={"query": "   "})
    assert response.status_code == 422
