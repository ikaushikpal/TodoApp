from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
class ENVConfig: 
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")
    USER = os.getenv("USER")
    PASSWORD = os.getenv("PASSWORD")
    DATABASE = os.getenv("DATABASE")

    DATABASE_URL = f"mysql+aiomysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION"))

    REDIS_URL = os.getenv("REDIS_URL")