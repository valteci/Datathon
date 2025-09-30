import os

class Config:
    """Configuração base (usada como padrão)."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://user:password@localhost:5432/meubanco"
    )

class TestingConfig(Config):
    """Configurações para testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Configurações para produção."""
    DEBUG = False
    #SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")