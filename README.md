# AI Agent with MCP

An intelligent AI agent powered by LangGraph and Model Context Protocol (MCP) that provides a FastAPI-based chat interface with JWT authentication, role-based access control (RBAC), and database operations integrated with OpenAI's language models.

## Overview

This project implements a production-ready AI agent system that combines:
- **LangGraph**: For orchestrating stateful, multi-step agent workflows
- **Model Context Protocol (MCP)**: For standardized integration with backend database operations
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **OpenAI API**: Advanced language model capabilities (GPT models)
- **JWT Authentication**: Secure token-based user authentication
- **Role-Based Access Control (RBAC)**: Fine-grained permission management
- **SQLAlchemy ORM**: Database abstraction layer with MySQL support

## Features

- 🤖 **AI Agent**: Intelligent agent powered by GPT models with MCP tool integration
- 🔄 **LangGraph Pipeline**: State-based workflow for multi-turn agent conversations
- 🛠️ **MCP Integration**: Standardized tool protocol for database operation execution
- 🚀 **FastAPI Server**: Modern REST API with automatic documentation
- 🔐 **JWT Authentication**: Secure user authentication with access & refresh tokens
- 👥 **Role-Based Access Control**: Multi-tier permission system (admin, manager, user)
- 💾 **MySQL Database**: SQLAlchemy ORM with connection pooling
- 📊 **Rate Limiting**: Configurable request throttling (5 requests/minute default)
- 📈 **Token Usage Tracking**: Monitors OpenAI API token consumption per request
- 🛡️ **Permission Management**: Granular permission control at endpoint level
- 🔄 **Token Refresh**: Support for access token refresh without re-authentication
- 🗑️ **Token Revocation**: Logout functionality with refresh token blacklisting

## Architecture

```
FastAPI Server
    ├── /auth endpoints
    │   ├── POST /register (user registration)
    │   ├── POST /login (JWT token generation)
    │   ├── POST /refresh (refresh access token)
    │   ├── POST /logout (token revocation)
    │   └── GET /me (current user profile)
    ├── /users endpoints (RBAC protected)
    │   ├── GET / (list all users)
    │   ├── GET /{user_id} (get user by ID)
    │   └── DELETE /{user_id} (delete user)
    ├── /roles endpoints (RBAC protected)
    │   ├── GET / (list roles)
    │   ├── POST /assign (assign role to user)
    │   └── POST /permission (assign permission to role)
    ├── /chat endpoint (rate-limited, permission-protected)
    │   └── POST / (AI agent chat)
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
    ├── MainState (question, answer, token_usage)
    ├── LangGraph Pipeline
    │   └── ask_question node (processes queries with LLM)
    └── Token Usage Callback (tracks OpenAI consumption)
```

## Tech Stack

- **Python 3.x**
- **FastAPI 0.136.3**: Web framework with async support
- **LangGraph 1.2.1**: Agent workflow orchestration
- **LangChain 1.3.1**: LLM framework and agents
- **LangChain-OpenAI 1.2.2**: OpenAI integration
- **LangChain-MCP-Adapters 0.2.2**: MCP protocol support
- **MCP 1.27.1**: Model Context Protocol
- **SQLAlchemy 2.0.50**: ORM for database operations
- **MySQL Connector 9.7.0**: MySQL connectivity
- **PyMySQL 1.2.0**: Pure Python MySQL driver
- **PyJWT 2.13.0**: JWT token encoding/decoding
- **pwdlib 0.3.0**: Password hashing with Argon2
- **SlowAPI 0.1.9**: Rate limiting
- **Pydantic**: Data validation

## Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7+ database running
- OpenAI API key (for GPT model access)
- MCP server running on localhost:8001 (optional, for agent tools)

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
   # Database Configuration
   DB_CONNECTION=mysql+pymysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DATABASE=python_dummy

   # OpenAI Configuration
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=gpt-3.5-turbo

   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7

   # MCP Configuration
   MCP_HOST=localhost
   MCP_PORT=8001
   MCP_URL=http://localhost:8001/mcp
   ```

5. **Initialize the database**
   ```bash
   # Run seed script to create tables and default roles
   python -m utils.seed
   ```

## Project Structure

```
ai-agent-with-mcp/
├── main.py                          # FastAPI app entry point
├── database.py                      # SQLAlchemy engine, session factory
├── core/
│   └── security.py                 # JWT token handling, password hashing, authorization
├── routers/
│   ├── auth.py                     # Authentication endpoints (register, login, refresh, logout)
│   ├── chat.py                     # AI chat endpoint (rate-limited, permission-protected)
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
├── utils/
│   ├── __init__.py
│   └── seed.py                     # Database seeding (roles, permissions, admin user)
├── requirements.txt                # Python dependencies
├── .env-example                    # Environment variables template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## File Descriptions

### Core Application
- **`main.py`**: FastAPI application entry point. Includes all routers (auth, chat, user, role).
- **`database.py`**: SQLAlchemy engine configuration with MySQL connection pooling, SessionLocal for dependency injection, Base for ORM models.

### Security & Authentication (`core/`)
- **`core/security.py`**: 
  - `JWTBearer`: HTTPBearer for token extraction from requests
  - `SecurityHandler`: JWT decoding, user retrieval, role/permission validation
  - `has_roles()`: Decorator to check user roles
  - `has_permissions()`: Decorator to check granular permissions
  - `get_current_user()`: Dependency for protected endpoints

### API Routes (`routers/`)
- **`routers/auth.py`**: 
  - `POST /auth/register`: User registration with default role
  - `POST /auth/login`: Login returns access & refresh tokens
  - `POST /auth/refresh`: Generate new access token from refresh token
  - `POST /auth/logout`: Revoke refresh token
  - `GET /auth/me`: Get current user profile
  
- **`routers/chat.py`**: 
  - `POST /chat/`: AI chat endpoint (requires "chat:use" permission)
  - Rate limited to 5 requests/minute
  - Returns: `{answer: str, token_usage: dict}`

- **`routers/user.py`**: 
  - `GET /users/`: List all users (requires "user:read" permission)
  - `GET /users/{user_id}`: Get user by ID (requires "user:read" permission)
  - `DELETE /users/{user_id}`: Delete user (requires "user:delete" permission)

- **`routers/role.py`**: 
  - `GET /roles/`: List roles (requires "role:manage" permission)
  - `POST /roles/assign`: Assign role to user (requires "role:manage" permission)
  - `POST /roles/permission`: Assign permission to role (requires "role:manage" permission)

### Business Logic Services (`service/`)
- **`service/base_service.py`**: Base service class with database session injection
- **`service/auth.py`**: 
  - `register()`: Create user with default role
  - `login()`: Validate credentials, generate JWT tokens
  - `refresh_token()`: Issue new access token
  - `logout()`: Revoke refresh token
  - `create_jwt_token()`: Generate access/refresh tokens with expiry
  - `decode_token()`: Validate and decode JWT

- **`service/user.py`**: User operations
- **`service/role.py`**: Role and permission operations
- **`service/langgraph_service.py`**: 
  - `MainState`: TypedDict with question, answer, token_usage
  - `initialize()`: Initialize MCP client for tool access
  - `ask_question()`: Process user query through OpenAI with MCP tools
  - `build_pipeline()`: Construct LangGraph pipeline

### Data Models & Schemas (`schemas/`, `sql/models/`, `sql/crud/`)

**Schemas (Pydantic):**
- `schemas/auth.py`: RegisterRequest, LoginRequest, RefreshTokenRequest
- `schemas/chat.py`: Chat query schema
- `schemas/users.py`: UserResponse schema
- `schemas/role.py`: RoleResponse schema

**Database Models (SQLAlchemy):**
- `sql/models/users.py`: User table with password hashing
- `sql/models/role.py`: Role table (admin, manager, user)
- `sql/models/permission.py`: Permission table (granular actions like "user:read", "chat:use")
- `sql/models/user_roles.py`: Many-to-many relationship between users and roles
- `sql/models/role_permission.py`: Many-to-many relationship between roles and permissions
- `sql/models/refresh_tokens.py`: RefreshToken table for token management & revocation

**CRUD Operations:**
- `sql/crud/users.py`: Create user, get user, verify password
- `sql/crud/role.py`: Get role, assign permissions
- `sql/crud/refresh_token.py`: Create/update refresh token, validate token

### Utilities (`utils/`)
- **`utils/seed.py`**: Initializes database with:
  - Permissions: user:create, user:read, user:update, user:delete, role:manage, permission:manage, chat:use
  - Roles: admin (all permissions), manager (limited), user (read-only)
  - Admin user: admin@test.com / Admin@123

## Usage

### Running the Server

```bash
# Start the FastAPI server
uvicorn main:app --reload

# Server available at http://localhost:8000
# API docs: http://localhost:8000/docs (Swagger UI)
# Alternative docs: http://localhost:8000/redoc (ReDoc)
```

### API Examples

**Health Check:**
```bash
curl http://localhost:8000/health
# Response: {"status": "ok"}
```

**Welcome Message:**
```bash
curl http://localhost:8000/
# Response: {"message": "Welcome to mcp chat"}
```

**Register User:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
# Response: {
#   "message": "User registered successfully",
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }
```

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "Admin@123"
  }'
# Response: {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }
```

**Get Current User:**
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <access_token>"
# Response: {
#   "id": 1,
#   "full_name": "Admin",
#   "email": "admin@test.com",
#   "is_active": true,
#   "is_verified": true,
#   "roles": [{"id": 1, "name": "admin"}]
# }
```

**Chat with AI Agent (Requires "chat:use" permission):**
```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"query": "What are recent database records?"}'
# Response: {
#   "answer": "Based on your query...",
#   "token_usage": {
#     "input_tokens": 150,
#     "output_tokens": 85,
#     "total_tokens": 235
#   }
# }
```

**List Users (Requires "user:read" permission):**
```bash
curl -X GET "http://localhost:8000/users/" \
  -H "Authorization: Bearer <admin_token>"
```

**Refresh Access Token:**
```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
# Response: {
#   "access_token": "new_jwt_token",
#   "token_type": "bearer"
# }
```

**Logout (Revoke Token):**
```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer <access_token>"
# Response: {"message": "Logged out successfully"}
```

## How It Works

### Authentication Flow
1. User registers with email and password
2. User is assigned default "user" role
3. Password is hashed using Argon2
4. Access & refresh tokens are generated (JWT)
5. Login validates credentials and generates new tokens
6. Refresh token can generate new access tokens without password
7. Logout revokes the refresh token

### Authorization Flow
1. Protected endpoints check JWT token validity
2. SecurityHandler decodes and validates token
3. User roles and permissions are retrieved from database
4. Endpoint checks if user has required permission
5. Returns 403 Forbidden if insufficient permissions

### AI Chat Flow
1. User sends query to `/chat/` with valid JWT token
2. Permission check: requires "chat:use" permission
3. Rate limiter: 5 requests per minute per IP
4. LanggraphService initializes MCP client for tools
5. LangGraph pipeline processes question:
   - MainState created with user query
   - ask_question node invokes OpenAI LLM with MCP tools
   - Tools are executed (database operations)
   - LLM synthesizes response
6. Token usage is tracked and returned

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
- All permissions enabled

### Manager Role
- user:read
- user:update

### User Role
- user:read
- chat:use

## Rate Limiting

- `/chat/` endpoint: 5 requests per minute per IP address (SlowAPI)
- Exceeding limit returns 429 (Too Many Requests)

## Environment Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_CONNECTION` | Database driver | `mysql+pymysql` |
| `MYSQL_HOST` | MySQL hostname | `localhost` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | `root` |
| `MYSQL_DATABASE` | Database name | `python_dummy` |
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
- Ensure database exists: `CREATE DATABASE python_dummy;`
- Verify connection string format in `database.py`

### JWT Token Error
- Ensure `SECRET_KEY` is set in `.env`
- Verify token format: `Authorization: Bearer <token>`
- Check token expiry using JWT debugger at jwt.io
- Refresh token if expired: use `/auth/refresh` endpoint

### Permission Denied (403)
- Verify user has required role: check `/auth/me` endpoint
- Verify role has required permission: check database `role_permissions` table
- Check permission name matches exactly (case-sensitive)

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
- Wait before making new requests
- Check X-RateLimit-Remaining header
- Adjust rate limit in `routers/chat.py` if needed

## Contributing

Feel free to submit issues and pull requests to improve this project.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open a GitHub issue in the repository.

---

**Repository**: [indvx/ai-agent-with-mcp](https://github.com/indvx/ai-agent-with-mcp)
