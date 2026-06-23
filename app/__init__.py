"""Application factory."""
from flask import Flask
from config import config_map


def create_app(config_name="development"):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_map[config_name])

    from app.main import main_bp
    app.register_blueprint(main_bp)

    @app.shell_context_processor
    def ctx():
        return {"app": app}

    return app
