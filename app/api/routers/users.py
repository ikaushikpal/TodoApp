from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from app.core.logger_config import get_logger
from app.database.redis_cahce import get_redis_cache, serializer
from app.models.user import User
from app.schemas.page import Page
from app.schemas.user import UserResponse, UserUpdate, PasswordUpdate, RoleUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])
user_service_dependency = Annotated[UserService, Depends(UserService.get_user_service)]
logger = get_logger(__name__)


@router.get("", response_model=Page[UserResponse])
async def get_all_users(
    user_service: user_service_dependency,
    curr_user: User = Depends(AuthService.get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Fetch all users with pagination."""
    logger.info(
        f"User '{curr_user.email}' is fetching all users (limit={limit}, offset={offset})."
    )
    return await user_service.get_all_users(curr_user, limit, offset)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_service: user_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Fetch a specific user, with caching."""
    logger.info(f"User '{curr_user.email}' is fetching user '{user_id}'.")
    return await user_service.get_user(curr_user, user_id)


@router.get("/search", response_model=Page[UserResponse])
async def search_users_endpoint(
    user_service: user_service_dependency,
    search_term: str = Query(..., description="Search term for users"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Search for users based on a search term."""
    logger.info(
        f"User '{curr_user.email}' is searching users with term '{search_term}' (limit={limit}, offset={offset})."
    )
    return await user_service.search_users(curr_user, search_term, limit, offset)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    update_user: UserUpdate,
    user_service: user_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Update user details."""
    logger.info(f"User '{curr_user.email}' is updating user '{user_id}'.")
    return await user_service.update_user(curr_user, user_id, update_user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_service: user_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Delete a user."""
    logger.warning(f"User '{curr_user.email}' is deleting user '{user_id}'.")
    await user_service.delete_user(curr_user, user_id)

@router.patch("/{user_id}/password", response_model=UserResponse)
async def update_password(
    user_service: user_service_dependency,
    new_password: PasswordUpdate,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Update a user's password."""
    logger.info(f"User '{curr_user.email}' is updating password for user '{user_id}'.")
    return await user_service.update_password(curr_user, user_id, new_password)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_service: user_service_dependency,
    new_role: RoleUpdate,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    """Change a user's role."""
    logger.info(f"User '{curr_user.email}' is changing role for user '{user_id}'.")
    return await user_service.change_user_role(curr_user, user_id, new_role)
