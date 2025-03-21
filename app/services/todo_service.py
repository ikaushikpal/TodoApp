from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import BackgroundTasks, Depends
from redis import Redis
from sqlalchemy import delete, func, and_, select, desc, asc, text, exists
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger_config import get_logger
from app.database.database import get_db
from app.database.redis_cahce import get_redis_cache, serializer
from app.exceptions import TodoNotFoundException
from app.exceptions.UserNotAuthorizedException import UserNotAuthorizedException
from app.models.todo import Todo
from app.models.user import User
from app.schemas.page import Page
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

logger = get_logger(__name__)


class TodoService:
    """Service for managing Todo items in the application."""

    def __init__(
        self,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis_cache),
    ):
        self.background_tasks = background_tasks
        self.db = db
        self.redis = redis

    def get_todo_service(
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis_cache),
    ):
        """Factory method to create a TodoService instance."""
        logger.info("Creating a new TodoService instance.")
        return TodoService(background_tasks, db, redis)

    @staticmethod
    def _generate_cache_key(*args) -> str:
        """Generate a consistent Redis cache key from arguments."""
        cache_key = ":".join(str(arg) for arg in args)
        logger.debug(f"Generated cache key: {cache_key}")
        return cache_key

    async def cache_data(self, key: str, data, ex: int = 60) -> None:
        """Store data in Redis asynchronously with error handling."""
        try:
            serialized_data = serializer.serialize(data.model_dump())
            await self.redis.set(key, serialized_data, ex=ex)
            logger.debug(f"Data cached successfully with key: {key}")
        except Exception as e:
            logger.error(f"Failed to cache data: {e}")

    async def _create_todo_page(
        self,
        query,
        owner_id: Optional[str] = None,
        is_complete: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Page[TodoResponse]:
        """
        Helper method to create a page of todos based on query parameters.
        """
        logger.info("Creating a page of todos.")
        if owner_id is not None:
            query = query.filter(Todo.owner_id == owner_id)
            logger.debug(f"Filtering todos by owner_id: {owner_id}")

        if is_complete is not None:
            query = query.filter(Todo.complete == is_complete)
            logger.debug(f"Filtering todos by completion status: {is_complete}")

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        todo_count = result.scalar()
        logger.debug(f"Total todos found: {todo_count}")

        # Apply ordering and pagination
        query = (
            query.order_by(
                desc(Todo.priority), asc(Todo.complete), desc(Todo.created_at)
            )
            .offset(offset)
            .limit(limit)
        )

        todos = await self.db.execute(query)
        todos = todos.scalars().all()
        logger.debug(f"Retrieved {len(todos)} todos from the database.")

        # Convert to response objects
        todos_response = [TodoResponse.model_validate(todo.__dict__) for todo in todos]
        logger.info("Successfully created a page of todos.")
        return Page.create(todos_response, offset, limit, todo_count)

    async def get_all_todos(
        self, user: User, limit: int = 10, offset: int = 0
    ) -> Page[TodoResponse]:
        """
        Get all todos with pagination.
        """
        logger.info(f"Fetching all todos for user: {user.id}")
        if user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to fetch all todos.")
            raise UserNotAuthorizedException()

        cache_key = self._generate_cache_key(
            "todos", "all", f"limit-{limit}", f"offset-{offset}"
        )
        cached_todos = await self.redis.get(cache_key)
        if cached_todos:
            logger.debug("Returning todos from cache.")
            return Page[TodoResponse].model_validate(
                serializer.deserialize(cached_todos)
            )

        query = select(Todo)
        todo_pages = await self._create_todo_page(query, limit=limit, offset=offset)
        self.background_tasks.add_task(self.cache_data, cache_key, todo_pages, 300)
        logger.info("Successfully fetched all todos from the database.")
        return todo_pages

    async def get_todo(self, user: User, id: int) -> TodoResponse:
        """
        Get a single todo by ID.
        """
        logger.info(f"Fetching todo with ID: {id} for user: {user.id}")
        cache_key = self._generate_cache_key("todo", id)
        cached_todo = await self.redis.get(cache_key)
        if cached_todo:
            logger.debug("Returning todo from cache.")
            return TodoResponse.model_validate(serializer.deserialize(cached_todo))

        result = await self.db.execute(select(Todo).filter(Todo.id == id))
        todo = result.scalars().first()

        if todo is None:
            logger.error(f"Todo with ID {id} not found.")
            raise TodoNotFoundException(id)

        if todo.owner_id != user.id and user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to access todo {id}.")
            raise UserNotAuthorizedException()

        todo = TodoResponse.model_validate(todo.__dict__)
        self.background_tasks.add_task(self.cache_data, cache_key, todo, 300)
        logger.info("Successfully fetched todo from the database.")
        return todo

    async def create_todo(self, user: User, new_todo: TodoCreate) -> TodoResponse:
        """
        Create a new todo.
        """
        logger.info(f"Creating a new todo for user: {user.id}")
        new_todo_data = new_todo.model_dump()
        new_todo_data["owner_id"] = user.id

        todo = Todo(**new_todo_data)
        self.db.add(todo)
        await self.db.commit()
        await self.db.refresh(todo)
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        logger.info("Successfully created a new todo.")
        return TodoResponse.model_validate(todo.__dict__)

    async def update_todo(
        self, user: User, todo_id: int, update_todo: TodoUpdate
    ) -> TodoResponse:
        """
        Update an existing todo.
        """
        logger.info(f"Updating todo with ID: {todo_id} for user: {user.id}")
        result = await self.db.execute(select(Todo).filter(Todo.id == todo_id))
        todo = result.scalars().first()

        if todo is None:
            logger.error(f"Todo with ID {todo_id} not found.")
            raise TodoNotFoundException(todo_id)

        if todo.owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to update todo {todo_id}."
            )
            raise UserNotAuthorizedException()

        # Update todo fields
        for field, value in update_todo.model_dump().items():
            setattr(todo, field, value)

        if todo.complete and todo.finished_at is None:
            todo.finished_at = datetime.now(timezone.utc)
            logger.debug(f"Marking todo {todo_id} as completed.")

        if not todo.complete and todo.finished_at:
            todo.finished_at = None
            logger.debug(f"Marking todo {todo_id} as uncompleted.")

        await self.db.commit()
        await self.db.refresh(todo)
        await self.redis.delete(self._generate_cache_key("todo", todo_id))
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        logger.info("Successfully updated the todo.")
        return TodoResponse.model_validate(todo.__dict__)

    async def delete_todo(self, user: User, id: int) -> None:
        """
        Delete a todo by ID.
        """
        logger.info(f"Deleting todo with ID: {id} for user: {user.id}")
        result = await self.db.execute(select(Todo).filter(Todo.id == id))
        todo = result.scalars().first()

        if todo is None:
            logger.error(f"Todo with ID {id} not found.")
            raise TodoNotFoundException(id)

        if todo.owner_id != user.id and user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to delete todo {id}.")
            raise UserNotAuthorizedException()

        await self.db.delete(todo)
        await self.db.commit()
        await self.redis.delete(self._generate_cache_key("todo", id))
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        logger.info("Successfully deleted the todo.")

    async def delete_all_todos(self, user: User, owner_id: str) -> int:
        """
        Delete all todos for a specific owner.
        """
        logger.info(f"Deleting all todos for owner: {owner_id}")
        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to delete todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        stmt = delete(Todo).where(Todo.owner_id == owner_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        logger.info(f"Successfully deleted {result.rowcount} todos.")
        return result.rowcount

    async def get_user_todos(
        self, user: User, owner_id: str, limit: int = 10, offset: int = 0
    ) -> Page[TodoResponse]:
        """
        Get all todos for a specific owner with pagination.
        """
        logger.info(f"Fetching todos for owner: {owner_id}")
        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to fetch todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        cache_key = self._generate_cache_key(
            "todos", "user", f"owner-{owner_id}", f"limit-{limit}", f"offset-{offset}"
        )
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Returning todos from cache.")
            return Page[TodoResponse].model_validate(
                serializer.deserialize(cached_data)
            )

        query = select(Todo)
        todo_page = await self._create_todo_page(
            query, owner_id=owner_id, limit=limit, offset=offset
        )

        self.background_tasks.add_task(self.cache_data, cache_key, todo_page, 300)
        logger.info("Successfully fetched todos from the database.")
        return todo_page

    async def get_completed_todos(
        self, user: User, owner_id: str, limit: int = 10, offset: int = 0
    ) -> Page[TodoResponse]:
        """
        Get completed todos for a specific owner with pagination.
        """
        logger.info(f"Fetching completed todos for owner: {owner_id}")
        cache_key = self._generate_cache_key(
            "todos",
            "completed",
            f"owner-{owner_id}",
            f"limit-{limit}",
            f"offset-{offset}",
        )
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Returning completed todos from cache.")
            return Page[TodoResponse].model_validate(
                serializer.deserialize(cached_data)
            )

        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to fetch completed todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        query = select(Todo)
        todo_page = await self._create_todo_page(
            query, owner_id=owner_id, is_complete=True, limit=limit, offset=offset
        )

        self.background_tasks.add_task(self.cache_data, cache_key, todo_page, 300)
        logger.info("Successfully fetched completed todos from the database.")
        return todo_page

    async def get_uncompleted_todos(
        self, user: User, owner_id: str, limit: int = 10, offset: int = 0
    ) -> Page[TodoResponse]:
        """
        Get uncompleted todos for a specific owner with pagination.
        """
        logger.info(f"Fetching uncompleted todos for owner: {owner_id}")
        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to fetch uncompleted todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        cache_key = self._generate_cache_key(
            "todos",
            "uncompleted",
            f"owner-{owner_id}",
            f"limit-{limit}",
            f"offset-{offset}",
        )
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Returning uncompleted todos from cache.")
            return Page[TodoResponse].model_validate(
                serializer.deserialize(cached_data)
            )

        query = select(Todo)
        todo_page = await self._create_todo_page(
            query, owner_id=owner_id, is_complete=False, limit=limit, offset=offset
        )

        self.background_tasks.add_task(self.cache_data, cache_key, todo_page, 300)
        logger.info("Successfully fetched uncompleted todos from the database.")
        return todo_page

    async def delete_completed_todos(self, user: User, owner_id: str) -> int:
        """
        Delete all completed todos for a specific owner.
        """
        logger.info(f"Deleting completed todos for owner: {owner_id}")
        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to delete completed todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        stmt = delete(Todo).where(
            and_(Todo.owner_id == owner_id, Todo.complete == True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        await self.redis.delete(
            self._generate_cache_key("todos", "completed", f"owner-{owner_id}", "*")
        )
        await self.redis.delete(
            self._generate_cache_key("todos", "user", f"owner-{owner_id}", "*")
        )
        logger.info(f"Successfully deleted {result.rowcount} completed todos.")
        return result.rowcount

    async def search_by_fulltext(
        self,
        user: User,
        owner_id: str,
        search_term: str,
        limit: int = 10,
        offset: int = 0,
    ) -> Page[TodoResponse]:
        """
        Search todos using full-text search.
        """
        logger.info(f"Searching todos for owner: {owner_id} with term: {search_term}")
        if owner_id != user.id and user.role != "ADMIN":
            logger.warning(
                f"User {user.id} is not authorized to search todos for owner {owner_id}."
            )
            raise UserNotAuthorizedException()

        query = (
            select(Todo)
            .filter(Todo.owner_id == owner_id)
            .where(text("MATCH(title, description) AGAINST(:search_term)"))
        ).params(search_term=search_term)

        # Get total count before applying pagination
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total_count = result.scalar()
        logger.debug(f"Total todos found: {total_count}")

        # Apply default sorting and pagination
        query = (
            query.order_by(
                desc(Todo.priority), asc(Todo.complete), desc(Todo.created_at)
            )
            .offset(offset)
            .limit(limit)
        )

        results = await self.db.execute(query)
        todos = results.scalars().all()
        logger.debug(f"Retrieved {len(todos)} todos from the database.")

        # Convert to response objects
        todos_response = [TodoResponse.model_validate(todo.__dict__) for todo in todos]
        logger.info("Successfully searched todos.")
        return Page.create(todos_response, offset, limit, total_count)
