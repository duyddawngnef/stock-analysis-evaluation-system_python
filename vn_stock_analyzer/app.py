"""
app.py — Flask application entry point.

Development mode uses fake_data.py for all data.
To switch to real modules, update imports in routes/api_routes.py.
"""

from flask import Flask
from routes.trang_routes import trang_bp
from routes.api_routes import api_bp
from routes.export_routes import export_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "vn-stock-analyzer-dev-key"

    # Register blueprints
    app.register_blueprint(trang_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(export_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
