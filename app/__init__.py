import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_wtf.csrf import CSRFProtect


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.config.Config')

    # Initialize CSRF protection
    csrf = CSRFProtect(app)

    # Configure logging
    if not app.debug:
        # Ensure logs directory exists
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # Register routes
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
