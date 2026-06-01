# AI Agent with MCP

An intelligent AI agent powered by LangGraph and Model Context Protocol (MCP) that provides a FastAPI-based chat interface with authentication, role-based access control, and database operations through OpenAI integration.

## Overview

This project implements an AI-driven agent that leverages:
- **LangGraph**: For building stateful, multi-step agent workflows
- **Model Context Protocol (MCP)**: For standardized tool integration with backend services
- **FastAPI**: For high-performance REST API with automatic OpenAPI documentation
- **OpenAI API**: For advanced language model capabilities
- **JWT Authentication**: For secure user authentication
- **Role-Based Access Control**: For managing user permissions

## Features

- 🤖 **AI Agent**: Intelligent agent powered by GPT models with MCP tool integration
- 🔄 **LangGraph Pipeline**: State-based workflow management for multi-turn conversations
- 🛠️ **MCP Integration**: Standardized tool protocol for database operations
- 🚀 **FastAPI Server**: Modern, fast web framework with automatic API documentation
- 🔐 **Authentication & Authorization**: JWT-based user authentication with role management
- 👥 **User Management**: Complete user lifecycle management with roles and permissions
- 💾 **Database Support**: MySQL integration with SQLAlchemy ORM for data operations
- 📊 **Health Checks**: Built-in health monitoring endpoints
- 📈 **Token Usage Tracking**: Monitors and tracks OpenAI API token consumption

## Architecture

```
FastAPI Server
    ├── /auth endpoints (authentication)
    ├── /user endpoints (user management)
    ├── /role endpoints (role management)
    ├── /chat endpoint (rate limited, AI-powered)
    ├── /health endpoint
    └── LanggraphService
        ├── MCP Client (connects to MCP server)
        └── LangGraph Pipeline
            ├── State Management (MainState)
            ├── Agent with OpenAI LLM
            └── Tool Execution (via MCP)
```

## Tech Stack

- **Python 3.x**
- **FastAPI 0.136.3**: Web framework with built-in validation
- **LangGraph 1.2.1**: Agent workflow orchestration
- **LangChain 1.3.1**: LLM framework
- **LangChain-OpenAI 1.2.2**: OpenAI integration
- **LangChain-MCP-Adapters 0.2.2**: MCP protocol support
- **MCP 1.27.1**: Model Context Protocol
- **MySQL Connector 9.7.0 & PyMySQL 1.2.0**: Database connectivity
- **SlowAPI 0.1.9**: Rate limiting
- **SQLAlchemy 2.0.50**: ORM and database toolkit
- **PyJWT 2.13.0**: JWT token management
- **pwdlib 0.3.0**: Password hashing with Argon2

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- MySQL database (for database operations)
- MCP server running on localhost:8001 (for agent tools)

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
   MCP_URL='http://localhost:8001/mcp'

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

5. **Initialize the database** (optional - seed with initial data)
   ```bash
   python -m utils.seed
   ```

## Project Structure

```
ai-agent-with-mcp/
├── main.py                      # FastAPI application & router setup
├── database.py                  # Database configuration & session management
├── core/
│   └── security.py             # Security utilities (JWT, password hashing)
├── routers/
│   ├── __init__.py
│   ├── chat.py                 # Chat endpoint (AI agent interaction)
│   ├── auth.py                 # Authentication endpoints
│   ├── user.py                 # User management endpoints
│   └── role.py                 # Role management endpoints
├── service/
│   ├── __init__.py
│   ├── base_service.py         # Base service class
│   ├── auth.py                 # Authentication business logic
│   ├── user.py                 # User business logic
│   ├── role.py                 # Role business logic
│   ├── langgraph_service.py    # LangGraph agent orchestration
│   └── utility.py              # Utility functions
├── schemas/
│   ├── auth.py                 # Auth request/response schemas
│   ├── chat.py                 # Chat request/response schemas
│   ├── role.py                 # Role schemas
│   └── users.py                # User schemas
├── sql/
│   ├── models/                 # SQLAlchemy ORM models
│   └── crud/                   # Database CRUD operations
├── utils/
│   ├── __init__.py
│   └── seed.py                 # Database seeding utility
├── requirements.txt             # Python dependencies
├── .env-example                # Environment variables template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## File Descriptions

### Core Application
- **`main.py`**: FastAPI application entry point with router inclusions
- **`database.py`**: Database configuration, session factory, and connection management

### Core Security (`core/`)
- **`core/security.py`**: JWT token handling, password hashing, and authentication utilities

### API Routes (`routers/`)
- **`routers/chat.py`**: POST `/chat` endpoint for AI agent interaction with rate limiting
- **`routers/auth.py`**: Authentication endpoints (login, register, token validation)
- **`routers/user.py`**: User management endpoints (create, read, update, delete)
- **`routers/role.py`**: Role management endpoints for RBAC

### Business Logic (`service/`)
- **`service/base_service.py`**: Base service class with common functionality
- **`service/auth.py`**: Authentication service (login, registration, token management)
- **`service/user.py`**: User service operations
- **`service/role.py`**: Role service operations
- **`service/langgraph_service.py`**: Core agent service with:
  - `MainState`: TypedDict for conversation state
  - `LanggraphService`: Agent orchestration with MCP client
- **`service/utility.py`**: Utility service functions

### Data Models & Schemas
- **`schemas/`**: Pydantic models for request/response validation
  - `auth.py`: Login, registration schemas
  - `chat.py`: Chat request/response schemas
  - `role.py`: Role schemas
  - `users.py`: User schemas
- **`sql/models/`**: SQLAlchemy ORM models for database tables
- **`sql/crud/`**: CRUD operations for database interactions

### Utilities (`utils/`)
- **`utils/seed.py`**: Database seeding script for initial data population

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

**User Registration:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "secure_password"
  }'
```

**User Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "secure_password"
  }'
# Response: {"access_token": "jwt_token_here", "token_type": "bearer"}
```

**Chat Query** (requires JWT token):
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{"query": "What are my recent database records?"}'
```

**Response:**
```json
{
  "answer": "Based on your recent records...",
  "token_usage": {
    "input_tokens": 150,
    "output_tokens": 85,
    "total_tokens": 235
  }
}
```

## How It Works

1. **User Authentication**: User registers/logs in via `/auth/register` or `/auth/login`
2. **JWT Token**: Backend generates JWT token for authenticated sessions
3. **Chat Request**: User sends query to `/chat` endpoint with JWT token
4. **Authorization**: Request is validated against user's roles and permissions
5. **Service Initialization**: LanggraphService initializes MCP client
6. **Pipeline Execution**: 
   - Question is passed to the LangGraph pipeline
   - `MainState` is created with the user's question
7. **Agent Processing**:
   - Agent retrieves available tools from MCP server
   - Agent uses OpenAI LLM to determine which tools to use
   - Tools are executed (e.g., database queries via MCP)
   - LLM synthesizes final response from tool results
8. **Response**: AI-generated answer with token usage stats is returned to client

## Rate Limiting

The `/chat` endpoint is rate limited using SlowAPI. Configuration can be adjusted in `main.py` or `routers/chat.py`. Exceeding the limit will result in a 429 (Too Many Requests) response.

## Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | MCP server hostname | `localhost` |
| `MCP_PORT` | MCP server port | `8001` |
| `MCP_URL` | MCP server full URL | `http://localhost:8001/mcp` |
| `MYSQL_HOST` | MySQL server hostname | `localhost` |
| `MYSQL_PORT` | MySQL server port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | `root` |
| `MYSQL_DATABASE` | Database name | `python_dummy` |
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |

## Dependencies

See `requirements.txt` for the complete list. Key dependencies:

### Web & API
- `fastapi[standard]`: Web framework and utilities
- `uvicorn`: ASGI server

### AI & LLM
- `langchain`: LLM framework
- `langchain-openai`: OpenAI integration
- `langgraph`: Agent orchestration
- `langchain-mcp-adapters`: MCP support

### Database
- `mysql-connector-python`: MySQL connectivity
- `PyMySQL`: Pure Python MySQL driver
- `SQLAlchemy`: ORM and database toolkit

### Security & Authentication
- `PyJWT`: JWT token handling
- `pwdlib[argon2]`: Password hashing with Argon2

### Utilities
- `slowapi`: Rate limiting
- `mcp`: Model Context Protocol

## Development

### Adding New Endpoints

1. Create a new file in the `routers/` directory
2. Define FastAPI router with endpoints
3. Create corresponding service in `service/` directory
4. Define request/response schemas in `schemas/` directory
5. Include the router in `main.py`:
   ```python
   from routers import my_feature
   app.include_router(my_feature.router)
   ```

### Adding MCP Tools

1. Ensure your MCP server is running and exposing tools
2. Tools are automatically discovered via the MCP client in `LanggraphService`
3. The agent will have access to all exposed MCP tools

### Extending the Agent

Modify `service/langgraph_service.py` to:
- Add system prompts to guide agent behavior
- Implement custom node functions in the pipeline
- Add pre/post-processing steps
- Extend `MainState` with additional state fields

### Database Seeding

Run the seed script to populate initial data:
```bash
python -m utils.seed
```

## Troubleshooting

### MCP Connection Error
- Ensure MCP server is running on the configured host/port
- Check `MCP_URL` in `.env` (should match MCP server address)
- Verify network connectivity between application and MCP server

### OpenAI API Error
- Verify `OPENAI_API_KEY` is correct and has sufficient quota
- Check API rate limits and usage
- Ensure model name in `OPENAI_MODEL` is valid and accessible
- Monitor token usage in response payloads

### Database Connection Error
- Verify MySQL is running and accessible
- Check credentials in `.env` match your database setup
- Ensure target database exists
- Test connection: `mysql -h localhost -u root -p`

### Authentication/Authorization Error
- Verify JWT token is valid and not expired
- Check user has required role/permissions
- Review role assignments in database
- Ensure token is included in Authorization header: `Bearer <token>`

### Rate Limiting Errors
- Wait before making new requests (check 429 response headers)
- Adjust rate limits in `routers/chat.py` if needed
- Consider implementing request queuing for high-volume scenarios

## API Documentation

Once the server is running, you can access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

Feel free to submit issues and pull requests to improve this project.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open a GitHub issue in the repository.

---

**Repository**: [indvx/ai-agent-with-mcp](https://github.com/indvx/ai-agent-with-mcp)
