from flask import Flask
#from src.extensions import db
from src.routes import bp as main_bp

def create_app(config_class="config.DevelopmentConfig"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # inicializar banco de dados
    #db.init_app(app)

    # registrar rotas (blueprints)
    app.register_blueprint(main_bp)

    # qualquer outra inicialização (cache, autenticação, etc.)
    return app
