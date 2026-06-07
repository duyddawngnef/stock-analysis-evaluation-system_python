"""
app.py — Flask application entry point.

Dữ liệu thật từ vnstock qua module1, module2, module3.
Cache được lưu trong thư mục data/ (TTL 24h).
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
