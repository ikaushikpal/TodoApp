from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.core.logger_config import get_logger
from app.schemas.user import AuthRequest, UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.database.database import get_db, User
from app.exceptions import UserNotAuthorizedException

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = get_logger(__name__)


@router.get("", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_current_user(curr_user: User = Depends(AuthService.get_current_user)):
    """Fetch the currently authenticated user."""
    logger.info(f"User '{curr_user.email}' fetched their profile.")
    return UserResponse.model_validate(curr_user.__dict__)


@router.post("/login", response_model=dict)
async def login(
    # form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    form_data: AuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate user and generate access token."""
    logger.info(f"Login attempt for user: {form_data.email}")
    user = await AuthService.authenticate_user(
        db, form_data.email, form_data.password
    )

    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = await AuthService.create_access_token(user.email)
    logger.info(f"User '{user.email}' logged in successfully.")
    return {"access_token": token, "token_type": "bearer"}


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register_user(
    new_user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Register a new user."""
    logger.info(f"New user registration attempt: {new_user.email}")

    try:
        user = await AuthService.create_user(db, new_user)
        logger.info(f"User '{user.email}' registered successfully.")
        return user
    except Exception as e:
        logger.error(f"Error registering user '{new_user.email}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
        )
