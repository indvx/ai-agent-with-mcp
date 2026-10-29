# AI Agent with MCP (SQLite Edition)

An intelligent AI agent powered by LangGraph and Model Context Protocol (MCP) that provides a FastAPI chat interface, pure SQLite database operations, and database import capabilities.

## Overview

This project provides an AI agent system for database exploration and interaction:
- **LangGraph**: Orchestrates stateful, multi-step conversation and tool calling workflows.
- **Model Context Protocol (MCP)**: Standardized protocol providing safe database inspection and query tools to the LLM.
- **FastAPI**: Modern asynchronous REST API framework.
- **SQLite**: Self-contained, zero-configuration local database backend.
- **Database Import**: Upload SQLite files (`.db`, `.sqlite`) or SQL scripts (`.sql`) directly via REST API or MCP tool.
- **OpenAI API**: Advanced GPT models for conversation, report generation, and data queries.

## Architecture

```
FastAPI Application (Port 8000)
    ├── /chat endpoints
    │   ├── POST / (AI agent chat with thread persistence)
    │   └── POST /stream (streaming chat response)
    ├── /database endpoints
    │   ├── GET /info (active database metadata and table list)
    │   ├── GET /tables (all tables with row and column counts)
    │   ├── GET /tables/{table_name} (detailed table schema and column types)
    │   └── POST /import (upload .db, .sqlite, or .sql files)
    ├── GET / (welcome message)
    └── GET /health (health check)

MCP Server (Port 8001 - FastMCP)
    ├── count_tables (count total tables in active SQLite database)
    ├── get_table_names (search and list tables with pagination)
    ├── get_table_details (detailed table definition with columns, types, and row count)
    ├── count_fields (count columns in a table)
    ├── get_fields (list column names excluding sensitive fields)
    ├── count_records_table (count records with optional column filtering)
    └── list_records (query table records with pagination and sorting)

Database Layer
    └── app.db (SQLite database managed via standard library sqlite3)
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

## Installation

### Prerequisites
- Python 3.11 or higher
- OpenAI API key

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
   Edit `.env` with your settings:
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
In one terminal, start the MCP server:
```bash
python -m mcp.server
```
The server will run on `http://0.0.0.0:8001`.

### 2. Start the FastAPI App
In another terminal, start the REST API:
```bash
uvicorn main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Database Import & Inspection

### Uploading a Database via REST API
Import a `.db`, `.sqlite`, or `.sql` dump directly:
```bash
# Upload an SQL dump
curl -X POST "http://localhost:8000/database/import" \
  -F "file=@dump.sql"

# Upload an SQLite database file
curl -X POST "http://localhost:8000/database/import" \
  -F "file=@company.db"
```

### Inspecting Active Database & Tables
```bash
# Check active database info
curl "http://localhost:8000/database/info"

# List all tables with row and column counts
curl "http://localhost:8000/database/tables"

# Get schema and column details for a specific table
curl "http://localhost:8000/database/tables/employees"
```

## Running Tests

Run the full pytest suite:
```bash
pytest test/
```

## License

This project is open source and available under the MIT License.
