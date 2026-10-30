# AI Agent with MCP (SQLite Edition)

An intelligent AI agent powered by LangGraph and the Model Context Protocol (MCP) providing a FastAPI streaming chat interface, dynamic SQLite database management, and safe database inspection tools.

## Overview

This project provides an AI agent system for database exploration, querying, and multi-database management:
- **LangGraph**: Orchestrates agent workflows, tool execution, and token usage accounting.
- **Model Context Protocol (MCP)**: Implements FastMCP over HTTP streaming to expose safe inspection and retrieval tools to the LLM.
- **FastAPI**: REST API framework serving streaming chat endpoints and database management APIs.
- **SQLite Database Management**: Multi-database catalog system storing database metadata in `app.db` and active database files in `databases/`.
- **Database Import**: Upload SQLite files (`.db`, `.sqlite`, `.sqlite3`) or SQL dumps (`.sql`) with automatic SQL dialect sanitization.
- **Rate Limiting**: Protects streaming endpoints using SlowAPI.

## System Architecture

```text
FastAPI Application (Port 8000)
    ├── /chat
    │   └── POST /stream (streaming chat response with tool execution via SSE, rate-limited)
    ├── /database
    │   ├── POST /import (upload .db, .sqlite, .sqlite3, or .sql files)
    │   ├── GET /list (list all registered databases with active status)
    │   ├── PUT /{db_identifier} (activate or toggle default database)
    │   ├── DELETE /{db_identifier} (delete database record and physical file)
    │   ├── GET /info (active database metadata and table summary)
    │   ├── GET /tables (all tables with row and column counts)
    │   └── GET /tables/{table_name} (detailed schema, column types, and constraints)
    ├── GET / (welcome message)
    └── GET /health (health check)

MCP Server (Port 8001 - FastMCP HTTP Streaming)
    ├── count_tables (count total non-system tables in active database)
    ├── get_table_names (search and list table names)
    ├── get_fields (list column names excluding sensitive credential fields)
    ├── get_table_details (detailed table definition with columns, types, nullability, PK, and row count)
    ├── list_records (query table records with field selection, pagination, and sorting)
    └── count_records_table (count matching records with column filtering)

Storage Layer
    ├── app.db (system catalog tracking database metadata and status)
    └── databases/ (directory holding individual SQLite database files)
```

## Tech Stack

- Python 3.11+
- FastAPI 0.136.3
- LangGraph 1.2.1
- LangChain 1.3.1
- LangChain-OpenAI 1.2.2
- LangChain-MCP-Adapters 0.2.2
- FastMCP / MCP 1.27.1
- SlowAPI 0.1.9
- Pytest 9.0.3

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- OpenAI API key

### 1. Setup Environment
```bash
cd ai-agent-with-mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Copy the example configuration file:
```bash
cp .env-example .env
```

Configure `.env` with your values:
```env
MCP_HOST="0.0.0.0"
MCP_PORT="8001"
MCP_URL="http://localhost:8001/mcp"
SQLITE_DB_PATH="app.db"
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4o"
```

## Running the Application

### 1. Start the MCP Server
In the first terminal, start the FastMCP tool server using Uvicorn:
```bash
uvicorn mcp_module.server:app --port 8001 --reload
```
The MCP server starts listening on `http://0.0.0.0:8001/mcp`.

### 2. Start the FastAPI Application
In a second terminal, start the API server:
```bash
uvicorn main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## API Reference & Examples

### Chat Streaming Endpoint

Submit natural language database queries via Server-Sent Events (SSE):
```bash
curl -N -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many tables are there in the database?"}'
```

### Database Management Endpoints

#### 1. Import a Database or SQL Dump
```bash
# Upload an SQLite file (.db, .sqlite)
curl -X POST "http://localhost:8000/database/import?is_active=true" \
  -F "file=@sample.db"

# Upload an SQL dump file (.sql)
curl -X POST "http://localhost:8000/database/import?is_active=true" \
  -F "file=@schema.sql"
```

#### 2. List Registered Databases
```bash
curl "http://localhost:8000/database/list"
```

#### 3. Set Active Database
```bash
curl -X PUT "http://localhost:8000/database/sample" \
  -H "Content-Type: application/json" \
  -d '{"status": 1}'
```

#### 4. Delete Database
```bash
curl -X DELETE "http://localhost:8000/database/sample"
```

### Database Inspection Endpoints

```bash
# Get active database information and table summary
curl "http://localhost:8000/database/info"

# List all tables with row and column counts
curl "http://localhost:8000/database/tables"

# Get schema and column details for a specific table
curl "http://localhost:8000/database/tables/employees"
```

## Running Tests

Execute the automated test suite with pytest:
```bash
pytest test/
```

## License

This project is licensed under the MIT License.
