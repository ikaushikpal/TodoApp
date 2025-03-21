from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status, HTTPException

from app.core.logger_config import get_logger
from app.exceptions.UserNotAuthorizedException import UserNotAuthorizedException
from app.models.user import User
from app.schemas.page import Page
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
from app.services.auth_service import AuthService
from app.services.todo_service import TodoService

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])
todo_service_dependency = Annotated[TodoService, Depends(TodoService.get_todo_service)]
logger = get_logger(__name__)


@router.get("", response_model=Page[TodoResponse])
async def get_all_todos(
    todo_service: todo_service_dependency,
    curr_user: User = Depends(AuthService.get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    logger.info(
        f"Fetching all todos for user {curr_user.id} with limit={limit}, offset={offset}"
    )
    return await todo_service.get_all_todos(curr_user, limit, offset)


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def add_new_todo(
    todo_service: todo_service_dependency,
    new_todo: TodoCreate,
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"User {curr_user.id} is adding a new todo: {new_todo}")
    return await todo_service.create_todo(curr_user, new_todo)


@router.get("/user/{user_id}/uncompleted", response_model=Page[TodoResponse])
async def get_user_uncompleted_todos(
    todo_service: todo_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"Fetching uncompleted todos for user {user_id} by {curr_user.id}")
    return await todo_service.get_uncompleted_todos(curr_user, user_id, limit, offset)


@router.get("/user/{user_id}/completed", response_model=Page[TodoResponse])
async def get_user_completed_todos(
    todo_service: todo_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"Fetching completed todos for user {user_id} by {curr_user.id}")
    return await todo_service.get_completed_todos(curr_user, user_id, limit, offset)


@router.get("/user/{user_id}/search", response_model=Page[TodoResponse])
async def search(
    todo_service: todo_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    search_term: str = Query(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(
        f"User {curr_user.id} is searching todos for user {user_id} with term '{search_term}'"
    )
    return await todo_service.search_by_fulltext(
        curr_user, user_id, search_term, limit, offset
    )


@router.get("/user/{user_id}", response_model=Page[TodoResponse])
async def get_user_todos(
    todo_service: todo_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"Fetching all todos for user {user_id} by {curr_user.id}")
    return await todo_service.get_user_todos(curr_user, user_id, limit, offset)


@router.delete(
    "/user/{user_id}/completed",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_completed(
    todo_service: todo_service_dependency,
    user_id: str = Path(min_length=36, max_length=36),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"User {curr_user.id} is deleting completed todos for user {user_id}")
    await todo_service.delete_completed_todos(curr_user, user_id)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_service: todo_service_dependency,
    todo_id: int = Path(),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"User {curr_user.id} is fetching todo {todo_id}")
    todo = await todo_service.get_todo(curr_user, todo_id)
    if not todo:
        logger.warning(f"Todo {todo_id} not found for user {curr_user.id}")
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_service: todo_service_dependency,
    update_todo_obj: TodoUpdate,
    todo_id: int = Path(),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(
        f"User {curr_user.id} is updating todo {todo_id} with {update_todo_obj}"
    )
    return await todo_service.update_todo(curr_user, todo_id, update_todo_obj)


@router.delete(
    "/{todo_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT
)
async def delete_todo(
    todo_service: todo_service_dependency,
    todo_id: int = Path(),
    curr_user: User = Depends(AuthService.get_current_user),
):
    logger.info(f"User {curr_user.id} is deleting todo {todo_id}")
    await todo_service.delete_todo(curr_user, todo_id)
