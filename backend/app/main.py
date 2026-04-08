"""Flask application factory."""
import logging
import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from .config import Config
from .exceptions import register_error_handlers
from .routes.api import api_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
        static_url_path="/static",
    )
    app.config.from_object(Config)

    # CORS — configurable via CORS_ORIGINS env var
    # Defaults to "*" for local dev; production should set explicit origins
    cors_origins = Config.CORS_ORIGINS
    if cors_origins == "*":
        logger.warning(
            "CORS_ORIGINS is set to '*' (allow all). "
            "Set CORS_ORIGINS env var to restrict origins in production."
        )
    else:
        cors_origins = [o.strip() for o in cors_origins.split(",")]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Init directories
    Config.init_dirs()

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    app.register_blueprint(api_bp)

    # Serve frontend
    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    logger.info("BPMN-to-Image Converter app initialized")
    return app
