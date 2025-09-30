from src import create_app

# Em produção, defina via env var APP_CONFIG=config.ProductionConfig
APP_CONFIG = "config.ProductionConfig"
app = create_app(APP_CONFIG)
