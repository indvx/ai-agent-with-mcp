# AI Agent with MCP

A lightweight FastAPI-based chatbot demo that uses LangGraph, LangChain, OpenAI, and MCP to connect a chat endpoint to MySQL database operations.

## Overview

This repository demonstrates a minimal integration between:
- **FastAPI**: HTTP API server
- **LangGraph**: workflow orchestration for AI states
- **LangChain / OpenAI**: AI chat model integration
- **MCP (Model Context Protocol)**: tool access layer for database operations
- **SlowAPI**: rate limiting on the chat endpoint

## Features

- FastAPI `/chat/` endpoint for AI queries
- LangGraph state graph for request processing
- OpenAI `gpt-3.5-turbo` model integration
- MCP tool server exposing MySQL CRUD utilities
- Rate limiting on chat requests (5/minute)

## Installation

### Prerequisites

- Python 3.8+
- MySQL database available
- OpenAI API key
- `python -m venv` virtual environment support

### Setup

```bash
git clone https://github.com/indvx/ai-agent-with-mcp.git
cd ai-agent-with-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env-example .env
```

Edit `.env` and set your MySQL, OpenAI, and MCP configuration values.

### Run the MCP server

```bash
python mcp/server.py
```

### Run the FastAPI server

```bash
uvicorn main:app --reload
```

## Project Structure

```
ai-agent-with-mcp/
├── main.py                  # FastAPI app entry point
├── database.py              # SQLAlchemy engine and session factory
├── mcp/
│   ├── client.py            # Example MCP client usage
│   └── server.py            # MCP tool server exposing MySQL tools
├── routers/
│   └── chat.py              # /chat endpoint with rate limiting
├── schemas/
│   └── chat.py              # Pydantic schema for chat requests
├── service/
│   └── langgraph_service.py # LangGraph + MCP chat integration
├── requirements.txt         # Python dependencies
└── .env-example             # Example environment variables
```

## API Endpoints

- `GET /` — welcome message
- `GET /health` — health check
- `POST /chat/` — chat query endpoint

## Chat Usage

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all records in my_table"}'
```

Response example:

```json
{
  "answer": "...",
  "token_usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "total_tokens": 0
  }
}
```

## MCP Server Tools

The MCP server currently exposes these tools for MySQL operations:

- `add_record(table: str, data: dict)`
- `list_records(table: str)`
- `update_record(table: str, record_id: int, data: dict)`
- `delete_record(table: str, record_id: int)`
- `get_tables()`
- `get_fields(table: str)`

## Configuration

Key environment variables in `.env`:

- `MCP_HOST` — MCP server hostname
- `MCP_PORT` — MCP server port
- `MCP_URL` — MCP server URL
- `MYSQL_HOST` — MySQL hostname
- `MYSQL_PORT` — MySQL port
- `MYSQL_USER` — MySQL username
- `MYSQL_PASSWORD` — MySQL password
- `MYSQL_DATABASE` — MySQL database name
- `OPENAI_API_KEY` — OpenAI API key
- `OPENAI_MODEL` — OpenAI model name (default: `gpt-3.5-turbo`)

## Notes

- This project does not currently implement authentication or RBAC.
- `database.py` configures SQLAlchemy but the current chat flow uses the MCP server for database operations.
- `mcp/server.py` currently hard-codes `python_dummy` for the schema lookup used by `get_tables()` and `get_fields()`.
