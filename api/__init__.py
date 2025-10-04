from sanic import Sanic
from .routes.risk import bp as risk_blueprint
from .routes.health import bp as health_blueprint


def create_app():
    """
    Application factory to create and configure the Sanic app.
    """
    app = Sanic("SatelliteTrackerAPI")

    # Configure OpenAPI/Swagger documentation
    app.config.OAS_URL_PREFIX = "/swagger"
    app.config.OAS_UI_DEFAULT = "swagger"
    app.config.OAS_TITLE = "Satellite Tracker API"

    # Register blueprints
    app.blueprint(risk_blueprint)
    app.blueprint(health_blueprint)

    return app
