"""
Application factory — creates and configures the Flask app.

Using the factory pattern allows multiple app instances (testing, production)
and avoids circular imports through deferred extension initialization.
"""

import logging
import os

import sentry_sdk
import structlog
from flask import Flask, render_template
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import get_config
from app.extensions import cors, csrf, db, limiter, login_manager, migrate


def create_app(env: str = "development") -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load configuration
    config_class = get_config(env)
    app.config.from_object(config_class)

    if env == "production":
        config_class.validate()

    _configure_logging(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _init_sentry(app)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["ML_ARTIFACTS_DIR"], exist_ok=True)

    app.logger.info("CareerGuide app created", extra={"env": env})
    return app


def _configure_logging(app: Flask) -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.DEBUG if app.config.get("DEBUG") else logging.INFO)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}},
    )


def _register_blueprints(app: Flask) -> None:
    from app.routes.admin import admin_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.careers import careers_bp
    from app.routes.colleges import colleges_bp
    from app.routes.notifications import notifications_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(recommendations_bp, url_prefix="/recommendations")
    app.register_blueprint(colleges_bp, url_prefix="/colleges")
    app.register_blueprint(careers_bp, url_prefix="/careers")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    # Root route
    @app.route("/")
    def index():
        return render_template("landing.html")

    @app.route("/health")
    def health():
        return {"status": "ok", "version": app.config.get("ML_MODEL_VERSION", "v1")}


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return render_template("errors/500.html"), 500


def _register_context_processors(app: Flask) -> None:
    from app.utils.i18n import get_locale, get_translations

    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config["APP_NAME"],
            "google_maps_key": app.config["GOOGLE_MAPS_API_KEY"],
            "locale": get_locale(),
            "t": get_translations(),
            "supported_languages": app.config["SUPPORTED_LANGUAGES"],
        }


def _init_sentry(app: Flask) -> None:
    dsn = app.config.get("SENTRY_DSN")
    if dsn and not app.config.get("TESTING"):
        sentry_sdk.init(
            dsn=dsn,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.2,
            environment=os.getenv("FLASK_ENV", "development"),
        )
