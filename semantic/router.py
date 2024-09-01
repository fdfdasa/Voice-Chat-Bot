# semantic/router.py

from flask import Flask
from .route import semantic_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(semantic_bp, url_prefix='/semantic')
    return app
