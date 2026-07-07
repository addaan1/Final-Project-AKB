"""Application factory."""
import os

from flask import Flask

from config import config_map, env_flag


def _resolve_config_name(config_name: str | None) -> str:
    """Resolve app config from explicit arg or APP_CONFIG env."""
    selected = (config_name or os.environ.get("APP_CONFIG") or "development").lower()
    return selected if selected in config_map else "development"


def create_app(config_name=None):
    resolved_config = _resolve_config_name(config_name)
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_map[resolved_config])
    app.config["APP_CONFIG"] = os.environ.get("APP_CONFIG", resolved_config)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", app.config["SECRET_KEY"])
    app.config["DEBUG"] = env_flag("FLASK_DEBUG", app.config.get("DEBUG", False))
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID", app.config.get("GOOGLE_CLIENT_ID", ""))
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET", app.config.get("GOOGLE_CLIENT_SECRET", ""))
    app.config["GOOGLE_REDIRECT_URI"] = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        app.config.get("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/auth/google/callback"),
    )
    app.config["DEMO_ONLY"] = env_flag("DEMO_ONLY", app.config.get("DEMO_ONLY", False))
    app.config["ALLOW_REGISTRATION"] = env_flag("ALLOW_REGISTRATION", app.config.get("ALLOW_REGISTRATION", True))
    app.config["ALLOW_WAITLIST"] = env_flag("ALLOW_WAITLIST", app.config.get("ALLOW_WAITLIST", True))
    app.config["ALLOW_OAUTH"] = env_flag("ALLOW_OAUTH", app.config.get("ALLOW_OAUTH", True))
    app.config["PERSIST_LOCAL_WRITES"] = env_flag("PERSIST_LOCAL_WRITES", app.config.get("PERSIST_LOCAL_WRITES", True))

    from app.main import main_bp
    app.register_blueprint(main_bp)

    # Seed demo users (idempotent)
    from app.auth import seed_demo_users
    seed_demo_users()

    # Initialize OAuth (skip if credentials missing)
    from app.auth import init_oauth
    init_oauth(app)

    # Context processor: inject current_user ke semua template
    from app.auth import get_current_user

    @app.context_processor
    def inject_user():
        return {
            "current_user": get_current_user(),
            "demo_only": app.config.get("DEMO_ONLY", False),
            "allow_registration": app.config.get("ALLOW_REGISTRATION", True),
            "allow_waitlist": app.config.get("ALLOW_WAITLIST", True),
            "allow_oauth": app.config.get("ALLOW_OAUTH", True),
            "persist_local_writes": app.config.get("PERSIST_LOCAL_WRITES", True),
        }

    @app.shell_context_processor
    def ctx():
        return {"app": app}

    return app
