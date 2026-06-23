"""Application factory."""
from flask import Flask
from config import config_map


def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_map[config_name])

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
        return {"current_user": get_current_user()}

    @app.shell_context_processor
    def ctx():
        return {"app": app}

    return app
