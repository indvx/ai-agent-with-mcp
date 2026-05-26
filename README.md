# AI Agent with MCP

An intelligent AI agent powered by LangGraph and Model Context Protocol (MCP) that provides a FastAPI-based chat interface with database operations and OpenAI integration.

## Overview

This project implements an AI-driven agent that leverages:
- **LangGraph**: For building stateful, multi-step agent workflows
- **Model Context Protocol (MCP)**: For standardized tool integration with backend services
- **FastAPI**: For high-performance REST API and WebSocket support
- **OpenAI API**: For advanced language model capabilities

## Features

- 🤖 **AI Agent**: Intelligent agent powered by GPT models with MCP tool integration
- 🔄 **LangGraph Pipeline**: State-based workflow management for multi-turn conversations
- 🛠️ **MCP Integration**: Standardized tool protocol for database operations
- 🚀 **FastAPI Server**: Modern, fast web framework with automatic API documentation
- 🔐 **Rate Limiting**: Built-in request throttling (5 requests/minute for chat endpoint)
- 💾 **Database Support**: MySQL integration for data operations
- 📊 **Health Checks**: Built-in health monitoring endpoints

## Architecture

```
FastAPI Server
    ├── /chat endpoint (rate limited)
    ├── /health endpoint
    └── LanggraphService
        ├── MCP Client (connects to MCP host)
        └── LangGraph Pipeline
            ├── State Management
            └── Agent with OpenAI LLM
```

## Tech Stack

- **Python 3.x**
- **FastAPI 0.136.3**: Web framework
- **LangGraph 1.2.1**: Agent workflow orchestration
- **LangChain 1.3.1**: LLM framework
- **LangChain-OpenAI 1.2.2**: OpenAI integration
- **LangChain-MCP-Adapters 0.2.2**: MCP protocol support
- **MCP 1.27.1**: Model Context Protocol
- **MySQL Connector 9.7.0**: Database connectivity
- **SlowAPI 0.1.9**: Rate limiting

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- MySQL database (optional, for database operations)
- MCP server running on localhost:8001 (required for agent tools)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/indvx/ai-agent-with-mcp.git
   cd ai-agent-with-mcp
   ```

2. **Create a virtual environment**
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
   # MCP Configuration
   MCP_HOST='localhost'
   MCP_PORT='8001'

   # MySQL Database Configuration
   MYSQL_HOST="localhost"
   MYSQL_PORT="3306"
   MYSQL_USER="root"
   MYSQL_PASSWORD="root"
   MYSQL_DATABASE="python_dummy"

   # OpenAI Configuration
   OPENAI_API_KEY='your-api-key-here'
   OPENAI_MODEL='gpt-3.5-turbo'  # or 'gpt-4', 'gpt-4-turbo', etc.
   ```

## Project Structure

```
ai-agent-with-mcp/
├── main.py                 # FastAPI application & endpoints
├── langgraph_service.py    # LangGraph agent orchestration
├── requirements.txt        # Python dependencies
├── .env-example           # Environment variables template
├── .gitignore            # Git ignore rules
├── mcp/                  # MCP server implementations (future)
└── README.md             # This file
```

## File Descriptions

### `main.py`
FastAPI application with:
- **GET `/`**: Welcome message
- **GET `/health`**: Health check endpoint
- **POST `/chat`**: Chat interface (rate limited to 5 requests/minute)

```python
# Usage example
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here"}'
```

### `langgraph_service.py`
Core agent service containing:
- **MainState**: TypedDict for conversation state management
- **LanggraphService**: Main service class handling:
  - MCP client initialization
  - Agent question processing with OpenAI LLM
  - LangGraph pipeline construction

### `requirements.txt`
All Python package dependencies required for the project.

## Usage

### Running the Server

```bash
# Start the FastAPI server
uvicorn main:app --reload

# Server will be available at http://localhost:8000
# API documentation: http://localhost:8000/docs (Swagger UI)
# Alternative docs: http://localhost:8000/redoc (ReDoc)
```

### Making API Requests

**Health Check:**
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

**Chat Query:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my recent database records?"}'
```

**Response:**
```json
{
  "answer": "Based on your recent records..."
}
```

## How It Works

1. **Request**: User sends a chat query to the `/chat` endpoint
2. **Initialization**: LanggraphService initializes the MCP client
3. **Pipeline**: LangGraph builds/retrieves the conversation pipeline
4. **Agent Execution**: 
   - Question is passed to the agent
   - Agent retrieves available tools from MCP server
   - Agent uses OpenAI LLM to decide which tools to use
   - Tools are executed (e.g., database queries)
   - LLM synthesizes final response
5. **Response**: AI-generated answer is returned to the client

## Rate Limiting

The `/chat` endpoint is rate limited to **5 requests per minute** per IP address using SlowAPI. Exceeding this limit will result in a 429 (Too Many Requests) response.

## Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | MCP server hostname | `localhost` |
| `MCP_PORT` | MCP server port | `8001` |
| `MYSQL_HOST` | MySQL server hostname | `localhost` |
| `MYSQL_PORT` | MySQL server port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | `root` |
| `MYSQL_DATABASE` | Database name | `python_dummy` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |

## Dependencies

See `requirements.txt` for the complete list. Key dependencies:
- FastAPI & Uvicorn for web server
- LangGraph & LangChain for AI orchestration
- MCP adapters for tool integration
- MySQL connector for database operations
- SlowAPI for rate limiting

## Development

### Adding New MCP Tools

1. Implement MCP server in the `mcp/` directory
2. Register it in `LanggraphService.initialize()` method
3. Tools will be automatically available to the agent

### Extending the Agent

Modify `langgraph_service.py` to:
- Add system prompts to guide agent behavior
- Implement custom node functions
- Add intermediate processing steps

## Troubleshooting

**MCP Connection Error:**
- Ensure MCP server is running on `localhost:8001`
- Check `MCP_HOST` and `MCP_PORT` in `.env`

**OpenAI API Error:**
- Verify `OPENAI_API_KEY` is correct
- Check API quota and rate limits
- Ensure model name is valid

**Database Connection Error:**
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists

**Rate Limiting Errors:**
- Wait before making new requests
- Configure SlowAPI in `main.py` if needed

## Contributing

Feel free to submit issues and pull requests to improve this project.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open a GitHub issue in the repository.

---

**Repository**: [indvx/ai-agent-with-mcp](https://github.com/indvx/ai-agent-with-mcp)
