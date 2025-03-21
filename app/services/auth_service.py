from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Request
# from fastapi import security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

from app.core.logger_config import get_logger
from app.database.database import get_db
from app.core.load_env import ENVConfig
from app.exceptions.JWTTokenExpiredException import JWTTokenExpiredException
from app.exceptions.UserNotFoundException import UserNotFoundException
from app.exceptions.MalformedJWTException import MalformedJWTException
from app.exceptions.UserNotAuthorizedException import UserNotAuthorizedException
from app.models.user import User
from app.schemas.user import AuthRequest, UserCreate, UserResponse


logger = get_logger(__name__)

security = HTTPBearer()
# Password hashing context
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated='auto')

# For extracting bearer token from header
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login', scheme_name="Bearer")

# JWT expiration time
JWT_EXPIRATION_DELTA = timedelta(milliseconds=ENVConfig.JWT_EXPIRATION)

class AuthService:
    """Service for handling authentication-related operations."""

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify if the provided plain password matches the hashed password."""
        return bcrypt_context.verify(plain_password, hashed_password)

    @staticmethod
    async def get_password_hash(password: str) -> str:
        """Generate a hash for the provided password."""
        return bcrypt_context.hash(password)

    @staticmethod
    async def create_access_token(email: str) -> str:
        """
        Create a JWT access token for the given email.
        
        Args:
            email: User's email address
            
        Returns:
            JWT token as string
        """
        expires = datetime.now(timezone.utc) + JWT_EXPIRATION_DELTA

        payload = {
            "sub": email,
            "exp": expires
        }

        return jwt.encode(payload, ENVConfig.JWT_SECRET_KEY, algorithm=ENVConfig.JWT_ALGORITHM)

    @staticmethod
    async def is_token_expired(token_expiry: datetime) -> bool:
        """
        Check if a token has expired.
        
        Args:
            token_expiry: Datetime of token expiration
            
        Returns:
            True if token has expired, False otherwise
        """
        return token_expiry < datetime.now(timezone.utc)

    @staticmethod
    async def load_user_from_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Load a user from the database by email.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_current_user(
        # token: Annotated[str, Depends(oauth2_bearer)],
        db: Annotated[AsyncSession, Depends(get_db)],
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> User:
        """
        Validate JWT token and return the current user.
        
        Args:
            token: JWT token
            db: Database session
            
        Returns:
            User object
            
        Raises:
            MalformedJWTException: If token is invalid
            JWTTokenExpiredException: If token has expired
            UserNotFoundException: If user not found
        """
        token = credentials.credentials
        try:
            # Decode the JWT token
            payload = jwt.decode(
                token, 
                ENVConfig.JWT_SECRET_KEY, 
                algorithms=[ENVConfig.JWT_ALGORITHM]
            )
            
            # Extract email and expiration from payload
            email: str = payload.get("sub")
            exp_timestamp: int = payload.get("exp")
            
            # Validate payload contents
            if email is None or exp_timestamp is None:
                logger.warning("Missing required fields in token")
                raise MalformedJWTException("Missing required fields in token")
            
            # Convert exp timestamp to datetime
            expiry_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            
            # Check token expiration
            if await AuthService.is_token_expired(expiry_time):
                logger.warning("JWT Token has expired")
                raise JWTTokenExpiredException(token)
            
            # Load user from database
            user = await AuthService.load_user_from_email(db, email)
            if user is None:
                logger.warning(f"User : {email} not found")
                raise UserNotFoundException(email=email)
            
            return user
            
        except JWTError as e:
            logger.warning("Invalid JWT Token")
            raise MalformedJWTException(f"Invalid token: {str(e)}")
    
    @staticmethod 
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: User's password

        Returns:
            User object if authentication is successful, None otherwise
        """
        user = await AuthService.load_user_from_email(db, email)
        if user is None:
            logger.warning(f"User : {email} not found")
            raise UserNotFoundException(email=email)
        
        if not await AuthService.verify_password(password, user.hashed_password):
            logger.warning(f"User {email} is not authorized")
            raise UserNotAuthorizedException(f"User: {email} is not authorized")
        return user
    
    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate) -> UserResponse:
        """
        Create a new user.
        
        Args:
            user: UserResponse object
            db: Database session
            
        Returns:
            UserResponse object
        """
        # Convert Pydantic model to dictionary
        user_data = user.model_dump()
        
        # Hash the password and remove plain text password
        user_data["hashed_password"] = await AuthService.get_password_hash(user_data["password"])
        user_data.pop("password")
        
        # Add additional fields to the dictionary
        user_data["role"] = "USER"  # Match the enum value in your DB model
        user_data["is_active"] = True
        
        # Create SQLAlchemy model instance
        new_user = User(**user_data)
        
        # Add to database and commit
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return UserResponse.model_validate(new_user.__dict__)
    