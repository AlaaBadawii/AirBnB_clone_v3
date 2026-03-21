#!/usr/bin/python3
"""This module defines the Flask application for the API."""
from flask import Flask, jsonify
from models import storage
from os import getenv
from api.v1.views import app_views
from flask_cors import CORS

app = Flask(__name__)

cors = CORS()
cors.init_app(app=app, resources={r"/*": {"origins": "0.0.0.0"}})

app.register_blueprint(app_views)


@app.teardown_appcontext
def close_conn(error):
    """Close storage connnection after each request"""
    storage.close()

@app.errorhandler(404)
def Not_found(error):
    """Return a JSON 404 response for missing API resources."""
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    host = getenv("HBNB_API_HOST", "0.0.0.0")
    port = getenv("HBNB_API_PORT", 5000)
    app.run(host=host, port=int(port), threaded=True)
