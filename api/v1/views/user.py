#!/usr/bin/python3
"""user module to handle user routes"""
from api.v1.views import app_views
from models import storage
from flask import jsonify, abort, request
from models.user import User


@app_views.route('/users', methods=['GET'], strict_slashes=False)
def users():
    """retrieve all users"""
    all_users = storage.all(User).values()

    return jsonify([user.to_dict() for user in all_users])

@app_views.route('/users/<user_id>', methods=['GET'], strict_slashes=False)
def get_user(user_id):
    """retrieve one user using id"""
    user = storage.get(User, user_id)
    if not user:
        abort(404)

    return jsonify(user.to_dict())

@app_views.route('/users/<user_id>', methods=['DELETE'], strict_slashes=False)
def delete_user(user_id):
    """delete a user using id"""
    user = storage.get(User, user_id)
    if not user:
        abort(404)

    storage.delete(user)
    storage.save()
    return jsonify({}),200

@app_views.route('/users', methods=['POST'], strict_slashes=False)
def create_user():
    """create new user"""
    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")

    if "email" not in data:
        abort(400, "Missing email")

    if "password" not in data:
        abort(400, "Missing password")

    user = User(email=data["email"], password=data["password"])
    user.save()

    return jsonify(user.to_dict()), 201

@app_views.route('/users/<user_id>', methods=['PUT'], strict_slashes=False)
def update_user(user_id):
    """update a user using id"""
    user = storage.get(User, user_id)
    if not user:
        abort(404)

    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")

    for key, value in data.items():
        if key not in ["id", "email", "created_at", "updated_at"]:
            setattr(user, key, value)

    user.save()
    return jsonify(user.to_dict()), 200
