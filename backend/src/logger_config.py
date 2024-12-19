import logging
from logging.handlers import RotatingFileHandler
from src.config import LOGGER_MAX_BYTES, LOGGER_BACKUP_COUNT

def setup_logger():
    logger = logging.getLogger("ApplicationLogger")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        "app.log", maxBytes=LOGGER_MAX_BYTES, backupCount=LOGGER_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
    return logger

logger = setup_logger()