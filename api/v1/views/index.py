#!/usr/bin/python3
"""views routes"""
from api.v1.views import app_views
from flask import jsonify
from models import storage

# classes
from models.city import City
from models.place import Place
from models.review import Review
from models.state import State
from models.user import User
from models.amenity import Amenity



classes = {"amenities": Amenity, "cities": City,
           "places": Place, "reviews": Review, "states": State,
           "users": User}

@app_views.route('/status', strict_slashes=False)
def status():
    return jsonify({"status": "Ok"})

@app_views.route('/stats', strict_slashes=False)
def stats():
    """Return the number of each objects by type."""
    result = {}

    for key, cls in classes.items():
        count = storage.count(cls=cls)
        result[key] = count

    return jsonify(result)
