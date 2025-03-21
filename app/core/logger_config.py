import logging
import os
from logging.handlers import TimedRotatingFileHandler

# Ensure logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log Format
log_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name: str):
    """
    Returns a logger with the given name while maintaining the same logging config.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all logs (DEBUG and above)

    # Console Handler (Logs to Console)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    # File Handler (Logs to a File, Rotates Daily)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=7,  # Keep logs for the last 7 days
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    # Prevent duplicate logs
    if not logger.hasHandlers():
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
