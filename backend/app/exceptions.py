"""Global exception definitions and handlers."""
import logging
import traceback

from flask import jsonify

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BpmnParseError(AppException):
    """Raised when BPMN file parsing fails."""
    def __init__(self, message: str = "Failed to parse BPMN file"):
        super().__init__(message, 400)


class RenderError(AppException):
    """Raised when rendering fails."""
    def __init__(self, message: str = "Failed to render BPMN diagram"):
        super().__init__(message, 500)


class FileValidationError(AppException):
    """Raised when file validation fails."""
    def __init__(self, message: str = "Invalid file"):
        super().__init__(message, 400)


def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(AppException)
    def handle_app_exception(error):
        logger.warning("AppException: %s (status=%d)", error.message, error.status_code)
        return jsonify({"success": False, "error": error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(413)
    def handle_too_large(_error):
        return jsonify({"success": False, "error": "File too large (max 16MB)"}), 413

    @app.errorhandler(500)
    def handle_internal_error(_error):
        logger.error("Internal server error: %s", traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500
