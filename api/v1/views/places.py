#!/usr/bin/python3
"""places module to handle places routes"""
from api.v1.views import app_views
from models import storage
from flask import jsonify, abort, request
from models.place import Place


@app_views.route('/places', methods=['GET'], strict_slashes=False)
def places():
    """retrieve all places"""
    all_places = storage.all(Place).values()

    return jsonify([place.to_dict() for place in all_places])

@app_views.route('/places/<place_id>', methods=['GET'], strict_slashes=False)
def get_place(place_id):
    """retrieve one place using id"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)

    return jsonify(place.to_dict())

@app_views.route('/places/<place_id>', methods=['DELETE'], strict_slashes=False)
def delete_place(place_id):
    """delete a place using id"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)

    storage.delete(place)
    storage.save()
    return jsonify({}),200

@app_views.route('/places', methods=['POST'], strict_slashes=False)
def create_place():
    """create new place"""
    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")

    if "name" not in data:
        abort(400, "Missing name")

    place = Place(name=data["name"])
    place.save()

    return jsonify(place.to_dict()), 201

@app_views.route('/places/<place_id>', methods=['PUT'], strict_slashes=False)
def update_place(place_id):
    """update a place using id"""
    place = storage.get(Place, place_id)
    if not place:
        abort(404)

    data = request.get_json(silent=True)
    if data is None:
        abort(400, description="Not a JSON")

    for key, value in data.items():
        if key not in ['id', 'created_at', 'updated_at']:
            setattr(place, key, value)

    place.save()
    return jsonify(place.to_dict()), 200
