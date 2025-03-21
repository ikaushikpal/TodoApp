# app/main.py
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from app.core.logger_config import get_logger
from app.database.redis_cahce import close_redis, init_redis
from app.exceptions.exception_handlers import (
    integrity_error_handler,
    mysql_error_handler,
    generic_exception_handler,
)
from sqlalchemy.exc import IntegrityError
from aiomysql import MySQLError
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as user_router
from app.api.routers.todos import router as todo_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import SecurityScheme

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    
    yield
    
    await close_redis()
    logger.info("Application is closing...")


logger.info("Application is starting...")
app = FastAPI(lifespan=lifespan)

# Register exception handlers
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(MySQLError, mysql_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include your routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(todo_router)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Outgoing response: {response.status_code}")

    return response

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://example.com"],  # List of allowed origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="TodoApp API",  # Title of your API
        version="1.0.0",  # Version of your API
        description="""
        TodoApp API Documentation

        This is the official API documentation for the **TodoApp**, a FastAPI-based application for managing todos and users.

        Features:
        - User Authentication: Register, login, and manage user profiles.
        - Todo Management: Create, read, update, and delete todos.
        - Full-Text Search: Search for users and todos using advanced search queries.
        - Redis Caching: Improve performance with Redis-based caching.

        Authentication:
        - Use the **Login** endpoint to obtain a JWT token.
        - Include the token in the `Authorization` header for protected endpoints.

        Example:
        ```bash
        curl -X 'GET' 'http://localhost:8000/api/v1/todos' \\
          -H 'accept: application/json' \\
          -H 'Authorization: Bearer <your-jwt-token>'
        ```

        Links:
        - [GitHub Repository](https://github.com/ikaushikpal/TodoApp)
        - [Swagger UI](http://localhost:8000/docs)
        - [ReDoc](http://localhost:8000/redoc)
        """,
        routes=app.routes,
    )

    # Add a custom security scheme for JWT token
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your JWT token here.",
        }
    }

    # Apply the security scheme to specific endpoints
    protected_paths = [
        "/api/v1/auth",  # GET /api/v1/auth
        "/api/v1/users",  # GET /api/v1/users
        "/api/v1/users/{user_id}",  # GET /api/v1/users/{user_id}
        "/api/v1/users/{user_id}",  # PUT /api/v1/users/{user_id}
        "/api/v1/users/{user_id}",  # DELETE /api/v1/users/{user_id}
        "/api/v1/users/search",  # GET /api/v1/users/search
        "/api/v1/users/{user_id}/password",  # PATCH /api/v1/users/{user_id}/password
        "/api/v1/users/{user_id}/role",  # PATCH /api/v1/users/{user_id}/role
        "/api/v1/todos",  # GET /api/v1/todos
        "/api/v1/todos",  # POST /api/v1/todos
        "/api/v1/todos/user/{user_id}/uncompleted",  # GET /api/v1/todos/user/{user_id}/uncompleted
        "/api/v1/todos/user/{user_id}/completed",  # GET /api/v1/todos/user/{user_id}/completed
        "/api/v1/todos/user/{user_id}/completed",  # DELETE /api/v1/todos/user/{user_id}/completed
        "/api/v1/todos/user/{user_id}/search",  # GET /api/v1/todos/user/{user_id}/search
        "/api/v1/todos/user/{user_id}",  # GET /api/v1/todos/user/{user_id}
        "/api/v1/todos/{todo_id}",  # GET /api/v1/todos/{todo_id}
        "/api/v1/todos/{todo_id}",  # PUT /api/v1/todos/{todo_id}
        "/api/v1/todos/{todo_id}",  # DELETE /api/v1/todos/{todo_id}
    ]

    for path in protected_paths:
        if path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi