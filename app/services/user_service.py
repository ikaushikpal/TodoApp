from fastapi import BackgroundTasks, Depends
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text, delete
from sqlalchemy.orm import selectinload

from app.core.logger_config import get_logger
from app.database.database import get_db
from app.database.redis_cahce import get_redis_cache, serializer
from app.exceptions.UserNotAuthorizedException import UserNotAuthorizedException
from app.exceptions.UserNotFoundException import UserNotFoundException
from app.models.user import User
from app.schemas.page import Page
from app.schemas.user import (
    PasswordUpdate,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth_service import AuthService

logger = get_logger(__name__)


class UserService:
    def __init__(
        self,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis_cache),
    ):
        self.background_tasks = background_tasks
        self.db = db
        self.redis = redis

    def get_user_service(
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis_cache),
    ):
        """Factory method to create a UserService instance."""
        logger.info("Creating a new UserService instance.")
        return UserService(background_tasks, db, redis)

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

    async def _create_user_page(
        self, query, limit: int = 10, offset: int = 0
    ) -> Page[UserResponse]:
        """
        Helper method to create a page of users based on query parameters.
        """
        logger.info("Creating a page of users.")
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        user_count = result.scalar()
        logger.debug(f"Total users found: {user_count}")

        # Apply pagination
        query = query.offset(offset).limit(limit)
        users = await self.db.execute(query)
        users = users.scalars().all()
        logger.debug(f"Retrieved {len(users)} users from the database.")

        # Convert to response objects
        users_response = [UserResponse.model_validate(user.__dict__) for user in users]
        logger.info("Successfully created a page of users.")
        return Page.create(users_response, offset, limit, user_count)

    async def get_all_users(
        self, user: User, limit: int = 10, offset: int = 0
    ) -> Page[UserResponse]:
        """
        Get all users with pagination.
        """
        logger.info(f"Fetching all users for admin: {user.id}")
        if user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to fetch all users.")
            raise UserNotAuthorizedException()

        cache_key = self._generate_cache_key(
            "users", "all", f"limit-{limit}", f"offset-{offset}"
        )
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Returning users from cache.")
            return Page[UserResponse].model_validate(
                serializer.deserialize(cached_data)
            )

        query = select(User)
        users_page = await self._create_user_page(query, limit=limit, offset=offset)

        self.background_tasks.add_task(self.cache_data, cache_key, users_page)
        logger.info("Successfully fetched all users from the database.")
        return users_page

    async def get_user(self, user: User, user_id: str) -> UserResponse:
        """
        Get a single user by ID.
        """
        logger.info(f"Fetching user with ID: {user_id} for user: {user.id}")
        if user.role != "ADMIN" and user.id != user_id:
            logger.warning(f"User {user.id} is not authorized to fetch user {user_id}.")
            raise UserNotAuthorizedException()

        cache_key = self._generate_cache_key("user", user_id)
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            logger.debug("Returning user from cache.")
            return UserResponse.model_validate(serializer.deserialize(cached_data))

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException(id=user_id)

        user_response = UserResponse.model_validate(user.__dict__)
        self.background_tasks.add_task(self.cache_data, cache_key, user_response)
        logger.info("Successfully fetched user from the database.")
        return user_response

    async def update_user(
        self, user: User, user_id: str, update_user: UserUpdate
    ) -> UserResponse:
        """
        Update an existing user.
        """
        logger.info(f"Updating user with ID: {user_id} for user: {user.id}")
        if user.role != "ADMIN" and user.id != user_id:
            logger.warning(
                f"User {user.id} is not authorized to update user {user_id}."
            )
            raise UserNotAuthorizedException()

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException(id=user_id)

        # Update user fields
        for field, value in update_user.model_dump(exclude={"id"}).items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        user_response = UserResponse.model_validate(user.__dict__)

        # Invalidate cache
        await self.redis.delete(self._generate_cache_key("user", user_id))
        await self.redis.delete(self._generate_cache_key("users", "all", "*"))
        logger.info("Successfully updated the user.")
        return user_response

    async def delete_user(self, user: User, user_id: str) -> None:
        """
        Delete a user by ID.
        """
        logger.info(f"Deleting user with ID: {user_id} for user: {user.id}")
        if user.role != "ADMIN" and user.id != user_id:
            logger.warning(
                f"User {user.id} is not authorized to delete user {user_id}."
            )
            raise UserNotAuthorizedException()

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException(id=user_id)

        await self.db.execute(delete(User).where(User.id == user_id))
        await self.db.commit()

        # Invalidate cache
        await self.redis.delete(self._generate_cache_key("user", user_id))
        await self.redis.delete(self._generate_cache_key("users", "all", "*"))
        await self.redis.delete(self._generate_cache_key("todos", "all", "*"))
        await self.redis.delete(
            self._generate_cache_key("todos", "user", f"owner-{user_id}", "*")
        )
        logger.info("Successfully deleted the user.")

    async def update_password(
        self, user: User, user_id: str, new_password: PasswordUpdate
    ) -> UserResponse:
        """
        Update a user's password.
        """
        logger.info(f"Updating password for user: {user_id}")
        if user.id != user_id:
            logger.warning(
                f"User {user.id} is not authorized to update password for user {user_id}."
            )
            raise UserNotAuthorizedException()

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException(id=user_id)

        user.hashed_password = await AuthService.get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        # Invalidate cache
        await self.redis.delete(self._generate_cache_key("user", user_id))
        await self.redis.delete(self._generate_cache_key("users", "all", "*"))
        logger.info("Successfully updated the user's password.")
        return UserResponse.model_validate(user.__dict__)

    async def change_user_role(
        self, user: User, user_id: str, new_role: RoleUpdate
    ) -> UserResponse:
        """
        Change a user's role.
        """
        logger.info(f"Changing role for user: {user_id}")
        if user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to change roles.")
            raise UserNotAuthorizedException()

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException(id=user_id)

        # Update user role
        for field, value in new_role.model_dump().items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        user_response = UserResponse.model_validate(user.__dict__)

        # Invalidate cache
        await self.redis.delete(self._generate_cache_key("user", user_id))
        await self.redis.delete(self._generate_cache_key("users", "all", "*"))
        logger.info("Successfully changed the user's role.")
        return user_response

    async def search_users(
        self, user: User, search_term: str, limit: int = 10, offset: int = 0
    ) -> Page[UserResponse]:
        """
        Search users using full-text search.
        """
        logger.info(f"Searching users with term: {search_term}")
        if user.role != "ADMIN":
            logger.warning(f"User {user.id} is not authorized to search users.")
            raise UserNotAuthorizedException()

        query = (
            select(User)
            .where(
                text(
                    "MATCH(id, username, email, first_name, last_name, country_code, phone_number) AGAINST(:search_term)"
                )
            )
            .params(search_term=search_term)
        )

        logger.debug(f"Executing search query for term: {search_term}")
        return await self._create_user_page(query, limit, offset)
