# AI Agent with MCP

An intelligent AI agent powered by LangGraph and Model Context Protocol (MCP) that provides a FastAPI-based chat interface with JWT authentication, role-based access control (RBAC), and database operations.

## Overview

This project implements a production-ready AI agent system that combines:
- **LangGraph**: For orchestrating stateful, multi-step agent workflows.
- **Model Context Protocol (MCP)**: For standardized integration with backend database operations.
- **FastAPI**: Modern, fast web framework with automatic API documentation.
- **OpenAI API**: Advanced language model capabilities (GPT models).
- **JWT Authentication**: Secure token-based user authentication.
- **Role-Based Access Control (RBAC)**: Fine-grained permission management.
- **SQLAlchemy ORM**: Database abstraction layer with MySQL and SQLite support.

## Features

- 🤖 **AI Agent**: Intelligent agent powered by GPT models with MCP tool integration.
- 🧠 **Conversation Memory**: State persistence across interactions using LangGraph `MemorySaver` (thread-based tracking).
- 🔄 **LangGraph Pipeline**: State-based workflow for multi-turn agent conversations.
- 🛠️ **MCP Integration**: Standardized tool protocol for database operation execution.
- 🚀 **FastAPI Server**: Modern REST API with automatic documentation.
- 🔐 **JWT Authentication**: Secure user authentication with access & refresh tokens.
- 👥 **Role-Based Access Control**: Multi-tier permission system (admin, manager, user).
- 💾 **MySQL & SQLite Support**: SQLAlchemy ORM with connection pooling.
- 📊 **Rate Limiting**: Configurable request throttling (5 requests/minute default).
- 📈 **Token Usage Tracking**: Monitors OpenAI API token consumption per request.
- 🛡️ **Permission Management**: Granular permission control at endpoint level.
- 🔄 **Token Refresh**: Support for access token refresh without re-authentication.
- 🗑️ **Token Revocation**: Logout functionality with refresh token blacklisting.

## Architecture

```
FastAPI Server
    ├── /auth endpoints
    │   ├── POST /register (user registration)
    │   ├── POST /login (JWT token generation)
    │   ├── POST /refresh (refresh access token)
    │   ├── POST /logout (token revocation)
    │   └── GET /me (current user profile)
    ├── /users endpoints
    │   ├── GET / (list all users, requires 'user:read' or 'user:manage' permission)
    │   ├── GET /{user_id} (get user by ID, requires authentication)
    │   └── DELETE /{user_id} (delete user, requires 'admin' role)
    ├── /roles endpoints
    │   ├── GET / (list roles, requires 'user:read' permission)
    │   ├── POST /assign (assign role to user, requires 'role:manage' permission)
    │   └── POST /permission (assign permission to role, requires 'role:manage' permission)
    ├── /chat endpoints (rate-limited)
    │   ├── POST / (AI agent chat, requires 'chat:use' permission)
    │   └── POST /stream (AI agent streaming chat, public/rate-limited)
    ├── / endpoint (welcome message)
    └── /health endpoint (health check)
        
Database Layer (SQLAlchemy ORM)
    ├── Users (with hashed passwords, active/verified flags)
    ├── Roles (admin, manager, user)
    ├── Permissions (fine-grained access control)
    ├── UserRoles (many-to-many relationship)
    ├── RolePermissions (many-to-many relationship)
    └── RefreshTokens (token management & revocation)

LanggraphService (AI Agent)
    ├── MCP Client (connects to external MCP server for tools)
    ├── MainState (question, answer, token_usage, tool_calls, messages)
    ├── MemorySaver (persists conversation state per thread_id)
    ├── LangGraph Pipeline
    │   └── chat node (processes queries with LLM)
    └── Token Usage Tracking (tracks OpenAI consumption)
```

## Tech Stack

- **Python 3.x**
- **FastAPI 0.136.3**: Web framework with async support.
- **LangGraph 1.2.1**: Agent workflow orchestration.
- **LangChain 1.3.1**: LLM framework and agents.
- **LangChain-OpenAI 1.2.2**: OpenAI integration.
- **LangChain-MCP-Adapters 0.2.2**: MCP protocol support.
- **MCP 1.27.1**: Model Context Protocol.
- **SQLAlchemy 2.0.50**: ORM for database operations.
- **MySQL Connector 9.7.0**: MySQL connectivity.
- **PyMySQL 1.2.0**: Pure Python MySQL driver.
- **PyJWT 2.13.0**: JWT token encoding/decoding.
- **pwdlib 0.3.0**: Password hashing with Argon2.
- **SlowAPI 0.1.9**: Rate limiting.
- **Pydantic**: Data validation.

## Installation

### Prerequisites
- Python 3.8 or higher.
- MySQL 5.7+ database running (or SQLite for testing).
- OpenAI API key (for GPT model access).
- MCP server running on localhost:8001 (optional, for agent tools).

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
   MCP_HOST=localhost
   MCP_PORT=8001
   MCP_URL=http://localhost:8001/mcp

   # DB Connection
   DB_CONNECTION=mysql+pymysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DATABASE=ai_agent_with_mcp

   # OpenAI Configuration
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-3.5-turbo

   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

5. **Initialize the database**
   ```bash
   # Run database migrations to create tables
   alembic upgrade head

   # Run seed script to create default roles and permissions
   python -m script.seed
   ```

## MCP Database Tools

The MCP server provides standard interfaces for the AI agent to query and explore the database safely:
- `count_records_table`: Count records with optional filtering.
- `list_records`: List records with pagination, sorting, and filtering.
- `count_all_tables`: Get the total number of tables in the database.
- `get_table_names`: List all tables available in the schema.
- `get_fields`: Get column definitions (name, type, nullability) for a table.
- `count_fields`: Count the total number of columns in a table.

## Project Structure

```
ai-agent-with-mcp/
├── alembic/                         # Database migration scripts and environment
├── alembic.ini                      # Alembic configuration file
├── main.py                          # FastAPI app entry point
├── database.py                      # SQLAlchemy engine, session factory
├── core/
│   └── security.py                 # JWT token handling, password hashing, authorization
├── routers/
│   ├── auth.py                     # Authentication endpoints (register, login, refresh, logout)
│   ├── chat.py                     # AI chat endpoints (POST /chat/ and POST /chat/stream)
│   ├── user.py                     # User management endpoints
│   └── role.py                     # Role & permission management endpoints
├── service/
│   ├── base_service.py             # Base service with database session
│   ├── auth.py                     # Authentication business logic (JWT, password verification)
│   ├── user.py                     # User service operations
│   ├── role.py                     # Role service operations
│   ├── langgraph_service.py        # AI agent orchestration with LangGraph
│   └── utility.py                  # Utility functions
├── schemas/
│   ├── auth.py                     # RegisterRequest, LoginRequest, RefreshTokenRequest
│   ├── chat.py                     # Chat query schema
│   ├── role.py                     # Role response schemas
│   └── users.py                    # User response schemas
├── sql/
│   ├── models/
│   │   ├── users.py               # User table model with password hashing
│   │   ├── role.py                # Role table model
│   │   ├── permission.py          # Permission table model
│   │   ├── user_roles.py          # UserRole junction table (many-to-many)
│   │   ├── role_permission.py     # RolePermission junction table (many-to-many)
│   │   └── refresh_tokens.py      # RefreshToken table model (for revocation)
│   └── crud/
│       ├── users.py               # User CRUD operations (create, read, verify password)
│       ├── role.py                # Role CRUD operations
│       └── refresh_token.py       # RefreshToken CRUD operations
├── script/
│   ├── __init__.py
│   └── seed.py                     # Database seeding (roles, permissions, admin user)
├── static/
│   └── logo.svg                    # API documentation logo
├── test/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration and dependency injection overrides
│   ├── test_main.py                # Health checks & basic routing tests
│   └── users/
│       └── test_user.py            # User registration and management tests
├── requirements.txt                # Python dependencies
├── .env-example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Usage

### Running the Server

```bash
# Start the FastAPI server
uvicorn main:app --reload

# Server available at http://localhost:8000
# API docs: http://localhost:8000/docs (Swagger UI)
# Alternative docs: http://localhost:8000/redoc (ReDoc)
```

### Running the MCP Server

```bash
# Start the FastMCP server for database tools
python -m mcp.server

# MCP Server runs on http://localhost:8001 (based on .env config)
```

### API Examples

**Welcome Message:**
```bash
curl http://localhost:8000/
# Response: {"message": "Welcome to mcp chat"}
```

## How It Works

### Authentication Flow
1. User registers with email, password, and password confirmation.
2. User is assigned default "user" role.
3. Password is hashed using Argon2.
4. Access & refresh tokens are generated (JWT).
5. Login validates credentials and generates new tokens.
6. Refresh token can generate new access tokens without password.
7. Logout revokes the refresh token.

### Authorization Flow
1. Protected endpoints check JWT token validity.
2. SecurityHandler decodes and validates token.
3. User roles and permissions are retrieved from database.
4. Endpoint checks if user has required permission or role.
5. Returns 403 Forbidden if user lacks necessary permissions/roles.

### AI Chat Flow
1. User sends query to `/chat/` with valid JWT token.
2. Permission check: requires "chat:use" permission.
3. Rate limiter: 5 requests per minute per IP.
4. LanggraphService initializes MCP client for tools.
5. LangGraph pipeline processes question:
   - State retrieved via `MemorySaver` using `thread_id`.
   - MainState created/updated with user query.
   - ask_question node invokes OpenAI LLM with MCP tools.
   - Tools are executed (database operations).
   - LLM synthesizes response and updated state is saved.
6. Token usage and tool calls are tracked and returned.

## Database Schema

### Users Table
- id (PK)
- full_name
- email (unique)
- password_hash
- is_active (default: True)
- is_verified (default: False)
- created_at
- updated_at
- relationships: roles (many-to-many)

### Roles Table
- id (PK)
- name (unique)
- is_default (default: False)
- relationships: permissions (many-to-many), users (many-to-many)

### Permissions Table
- id (PK)
- name (unique) - e.g., "user:read", "chat:use", "role:manage"
- relationships: roles (many-to-many)

### UserRoles Table (Junction)
- user_id (FK)
- role_id (FK)

### RolePermissions Table (Junction)
- role_id (FK)
- permission_id (FK)

### RefreshTokens Table
- id (PK)
- user_id (FK)
- jti (unique) - JWT ID for revocation
- token
- revoked (default: False)
- expires_at
- created_at

## Permissions Reference

| Permission | Description |
|------------|-------------|
| `user:create` | Create new users |
| `user:read` | Read user information |
| `user:update` | Update user details |
| `user:delete` | Delete users |
| `role:manage` | Manage roles and permissions |
| `permission:manage` | Manage permission assignments |
| `chat:use` | Use AI chat functionality |

## Default Roles & Permissions

### Admin Role
- All permissions enabled.

### Manager Role
- user:read
- user:update

### User Role
- user:read (Note: By default in `script/seed.py`, `chat:use` is not included in the seeded default role).

## Rate Limiting

- `/chat/` and `/chat/stream` endpoints: 5 requests per minute per IP address (SlowAPI).
- Exceeding limit returns 429 (Too Many Requests).

## Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_CONNECTION` | Database connection driver | `mysql+pymysql` |
| `MYSQL_HOST` | MySQL hostname | `localhost` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | `root` |
| `MYSQL_DATABASE` | Database name | `ai_agent_with_mcp` |
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `OPENAI_MODEL` | OpenAI model | `gpt-3.5-turbo` |
| `SECRET_KEY` | JWT secret key | **Required** |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `MCP_HOST` | MCP server hostname | `localhost` |
| `MCP_PORT` | MCP server port | `8001` |
| `MCP_URL` | MCP server URL | `http://localhost:8001/mcp` |

## Troubleshooting

### Database Connection Error
- Verify MySQL is running: `mysql -h localhost -u root -p`
- Check credentials in `.env`
- Ensure database exists: `CREATE DATABASE ai_agent_with_mcp;`
- Verify connection string format in `database.py`

### JWT Token Error
- Ensure `SECRET_KEY` is set in `.env`
- Verify token format: `Authorization: Bearer <token>`
- Check token expiry using JWT debugger at jwt.io
- Refresh token if expired: use `/auth/refresh` endpoint

### Permission Denied (403)
- Verify user has required role: check `/auth/me` endpoint.
- Verify role has required permission: check database `role_permissions` table.
- Check permission name matches exactly (case-sensitive).

### MCP Connection Error
- Ensure MCP server running on configured `MCP_URL`
- Verify network connectivity
- Check `MCP_HOST` and `MCP_PORT` in `.env`

### OpenAI API Error
- Verify `OPENAI_API_KEY` is correct
- Check API quota and rate limits
- Ensure model in `OPENAI_MODEL` is valid
- Monitor token usage in response

### Rate Limiting Error (429)
- Wait before making new requests.
- Check X-RateLimit-Remaining header.
- Adjust rate limit in `routers/chat.py` if needed.

## Contributing

Feel free to submit issues and pull requests to improve this project.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open a GitHub issue in the repository.

---

**Repository**: [indvx/ai-agent-with-mcp](https://github.com/indvx/ai-agent-with-mcp)
