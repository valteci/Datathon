# src/__init__.py
import os
import logging
from flask import Flask
from src.routes import bp as main_bp
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
except Exception:
    ProxyFix = None

def create_app(config_class: str | type = None):
    app = Flask(__name__)

    # 1) Escolha da configuração: env > parâmetro > Development (fallback)
    selected = os.getenv("APP_CONFIG", None) or config_class or "config.DevelopmentConfig"
    app.config.from_object(selected)

    # 2) Blueprints
    app.register_blueprint(main_bp)

    # 3) (Opcional) ProxyFix se estiver atrás de proxy (X-Forwarded-For/Proto)
    if ProxyFix and app.config.get("USE_PROXY_FIX", True):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # 4) (Opcional) Integra o logger do Flask ao do Gunicorn
    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    return app
