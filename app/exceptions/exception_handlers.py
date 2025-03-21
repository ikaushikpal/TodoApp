from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from aiomysql import MySQLError

from app.core.logger_config import get_logger

# Configure logger
logger = get_logger(__name__)

async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Extract detailed information from the IntegrityError
    error_message = str(exc.orig)
    if "Duplicate entry" in error_message:
        # Extract the duplicate value and constraint name
        duplicate_value = error_message.split("'")[1]
        constraint_name = error_message.split("key '")[1].split("'")[0]
        detail = f"Duplicate value '{duplicate_value}' for constraint '{constraint_name}'."
    else:
        detail = "A database integrity error occurred."

    # Log the error
    logger.warning(f"IntegrityError: {error_message}")

    return JSONResponse(
        status_code=400,
        content={"detail": detail},
    )

async def mysql_error_handler(request: Request, exc: MySQLError):
    # Handle MySQL-specific errors
    error_message = str(exc)
    logger.warning(f"MySQLError: {error_message}")

    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred."},
    )

async def generic_exception_handler(request: Request, exc: Exception):
    # Handle all other exceptions
    error_message = str(exc)
    logger.warning(f"Unhandled Exception: {error_message}")

    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )