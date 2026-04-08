"""Application configuration."""
import logging
import os

logger = logging.getLogger(__name__)


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
    OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
    ALLOWED_EXTENSIONS = {"bpmn", "xml"}
    DEFAULT_OUTPUT_FORMAT = "png"
    DEFAULT_DPI = 150
    DEFAULT_PADDING = 40
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    @classmethod
    def init_dirs(cls):
        """Ensure required directories exist."""
        for folder in [cls.UPLOAD_FOLDER, cls.OUTPUT_FOLDER]:
            os.makedirs(folder, exist_ok=True)
            logger.info("Ensured directory exists: %s", folder)
