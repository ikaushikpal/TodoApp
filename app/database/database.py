from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.load_env import ENVConfig
from app.core.logger_config import get_logger


# Configure logger
logger = get_logger(__name__)

# MySQL Connection URL format for async:
# mysql+aiomysql://username:password@host:port/database
DATABASE_URL = ENVConfig.DATABASE_URL

# Create the SQLAlchemy async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set echo=False in production
    pool_size=10,  # Number of connections to keep open in the pool
    max_overflow=20,  # Number of connections to allow beyond the pool_size
    pool_timeout=30,  # Maximum time (in seconds) to wait for a connection from the pool
    pool_recycle=3600,  # Recycle connections after 1 hour (to avoid stale connections)
    pool_pre_ping=True,  # Enable connection health checks
)

# Log database connection pool initialization
logger.info("Database connection pool initialized.")

# Create an async session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,  # Use AsyncSession for async support
    expire_on_commit=False,  # Prevent attributes from expiring after commit
    autocommit=False,
    autoflush=False,
)

# Define the Base class
Base = declarative_base()

# Import models after Base is defined
from app.core.logger_config import get_logger
from app.models.user import User
from app.models.todo import Todo

# Dependency to get the async session in FastAPI
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()