from dotenv import load_dotenv
import os
from src.logger_config import logger

try:
    load_dotenv()
except Exception as e:
    logger.error(f"Error happened during loading .env file:{e}",exc_info=True)

try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found")
except Exception as e:
    logger.error(f"Error happened during loading LLM api key from .env file:{e}",exc_info=True)