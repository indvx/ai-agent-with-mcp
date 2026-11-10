# AI Agent with MCP

An intelligent AI agent backend powered by LangGraph and Model Context Protocol (MCP) providing a FastAPI-based conversational interface with streaming responses and database tool execution.

## Overview

This project implements a streamlined AI agent system that combines:
- **LangGraph**: For orchestrating stateful, multi-step agent workflows.
- **Model Context Protocol (MCP)**: For standardized integration with backend database tools over HTTP streaming.
- **FastAPI**: Modern, fast web framework with automatic API documentation.
- **Multi-Provider LLM Support**: Unified LLM client supporting Groq, OpenAI, and Google Gemini.
- **Centralized Configuration**: Settings loaded via Pydantic `BaseSettings` (`core/config.py`).

## Features

- 🤖 **AI Agent**: Intelligent agent powered by configurable LLMs with MCP tool integration.
- 🔄 **LangGraph Pipeline**: State-based workflow for multi-turn agent conversations.
- 🛠️ **MCP Integration**: Standardized tool protocol for database inspection and queries via `MCP_URL`.
- ⚡ **Streaming & Standard Endpoints**: Supports full response (`POST /chat/`) and server-sent event streaming (`POST /chat/stream`).
- ⚡ **Response Caching**: In-memory TTL query caching and LLM prompt memoization for zero-token identical queries.
- 📊 **Rate Limiting**: Configurable request throttling (5 requests/minute default) via SlowAPI.
- 📈 **Token Usage Tracking**: Monitors LLM token consumption per request.
- 🚀 **FastAPI Server**: REST API with automatic Swagger UI and ReDoc documentation.

## Architecture

```
FastAPI Server
    ├── /chat endpoints (rate-limited)
    │   ├── POST / (AI agent chat endpoint)
    │   └── POST /stream (streaming response over SSE)
    ├── / endpoint (welcome message)
    └── /health endpoint (liveness check)

LanggraphService (AI Agent)
    ├── MCP Client (connects to external FastMCP server via MCP_URL)
    ├── MainState (question, answer, token_usage, tool_calls)
    ├── LangGraph Pipeline
    │   └── chat node (invokes LLM bound with dynamic MCP tools)
    └── Token Usage Tracking (tracks input, output, and total tokens)
```

## Tech Stack

- **Python 3.10+**
- **FastAPI**: Asynchronous web framework.
- **LangGraph**: State graph orchestration for the AI agent.
- **LangChain**: LLM abstractions and agent workflows.
- **LangChain-OpenAI**: OpenAI and Groq (OpenAI-compatible) integrations.
- **LangChain-Google-GenAI**: Google Gemini integration.
- **LangChain-MCP-Adapters**: Multi-server MCP client support.
- **SlowAPI**: Rate limiting for endpoints.
- **Pydantic / Pydantic-Settings**: Environment configuration management.

## Installation

### Prerequisites
- Python 3.10 or higher.
- LLM API key (Groq, OpenAI, or Google Gemini).
- MCP database tool server running and accessible via `MCP_URL`.

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/indvx/ai-agent-with-mcp.git
   cd ai-agent-with-mcp
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env-example .env
   ```
   Edit `.env` with your configuration:
   ```env
   # LLM Provider: "groq", "openai", or "gemini"
   LLM_PROVIDER="groq"
   LLM_MODEL="openai/gpt-oss-20b"
   LLM_BASE_URL="https://api.groq.com/openai/v1"
   LLM_API_KEY="your_llm_api_key"
   LLM_TEMPERATURE=0.3

   # FastMCP Server URL
   MCP_URL="http://localhost:8001/mcp"
   ```

## Project Structure

```
ai-agent-with-mcp/
├── main.py                          # FastAPI app entry point and health checks
├── core/
│   ├── config.py                    # Centralized application settings (Pydantic BaseSettings)
│   └── logger.py                    # Centralized logging configuration and logger factory
├── routers/
│   └── chat.py                      # AI chat endpoints (POST /chat/ and POST /chat/stream)
├── service/
│   ├── llm_service.py               # LLM factory supporting Groq, OpenAI, and Gemini
│   └── langgraph_service.py         # LangGraph workflow, TTL query cache & streamable MCP client
├── schemas/
│   └── chat.py                      # Chat request validation schema
├── requirements.txt                 # Python dependencies
├── .env-example                     # Environment variables template
├── .gitignore                       # Git ignore rules
└── README.md                        # Documentation
```

## Usage

### Running the Server

```bash
uvicorn main:app --reload --port 8000
```

- Server: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- Alternative Docs: `http://localhost:8000/redoc` (ReDoc)

### API Endpoints

#### 1. Welcome Message
```bash
curl http://localhost:8000/
# Response: {"message": "Welcome to mcp chat"}
```

#### 2. Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

#### 3. Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How many records are in the employees table?"}'
```

#### 4. Streaming Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Provide a summary report of employee departments"}'
```

## Environment Configuration

| Variable | Description | Example / Default |
|----------|-------------|-------------------|
| `LLM_PROVIDER` | LLM provider (`groq`, `openai`, `gemini`) | `groq` |
| `LLM_MODEL` | LLM model identifier | `openai/gpt-oss-20b` |
| `LLM_BASE_URL` | Base URL for OpenAI-compatible API | `https://api.groq.com/openai/v1` |
| `LLM_API_KEY` | Provider API key | **Required** |
| `LLM_TEMPERATURE` | Sampling temperature | `0.3` |
| `MCP_URL` | FastMCP streaming server endpoint URL | `http://localhost:8001/mcp` |
| `LOG_LEVEL` | Application logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `CACHE_TTL_SECONDS` | Query response cache duration in seconds (`0` to disable) | `300` |
| `CACHE_MAX_SIZE` | Maximum cached query entries in memory | `500` |

## Troubleshooting

### MCP Connection Error
- Ensure the external MCP tool server is running and accessible at `MCP_URL`.
- Verify network connectivity between the FastAPI server and the MCP server.

### LLM API Error
- Verify that `LLM_API_KEY` is set correctly for the chosen `LLM_PROVIDER`.
- Ensure `LLM_MODEL` and `LLM_BASE_URL` match your provider configuration.
- Check API quota and rate limits with your LLM provider.

### Rate Limiting Error (429)
- Default rate limit is 5 requests per minute per IP address.
- Adjust the rate limiter decorator in `routers/chat.py` if higher throughput is required.

## License

This project is open source and available under the MIT License.
