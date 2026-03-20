#!/usr/bin/python3
"""handles all default RESTFul API actions for states"""
from api.v1.views import app_views
from models import storage
from flask import jsonify, abort, request
from models.state import State


@app_views.route('/states', methods=['GET'], strict_slashes=False)
def states():
    """retrieve all states"""
    all_states = storage.all(State).values()

    return jsonify([state.to_dict() for state in all_states])

@app_views.route('/states/<state_id>', methods=['GET'], strict_slashes=False)
def get_state(state_id):
    """retrieve one state using id"""
    state = storage.get(State, state_id)

    if not state:
        abort(404)

    return jsonify(state.to_dict())

@app_views.route('/states/<state_id>', methods=['DELETE'], strict_slashes=False)
def delete_state(state_id):
    """delete a state using id"""
    state = storage.get(State, state_id)

    if not state:
        abort(404)

    storage.delete(state)
    storage.save()
    return jsonify({}),200    

@app_views.route('/states', methods=['POST'], strict_slashes=False)
def create_state():
    """create new state"""
    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")
    if "name" not in data:
        abort(400, "Missing name")

    state = State(name=data["name"])
    state.save()

    return jsonify(state.to_dict()), 201

@app_views.route('/states/<state_id>', methods=['PUT'], strict_slashes=False)
def update_state(state_id):
    """update a state using id"""
    data = request.get_json(silent=True)

    if data is None:
        abort(400, description="Not a JSON")

    state = storage.get(State, state_id)
    if state is None:
        abort(404)

    rejected = ["id", "created_at", "updated_at"]
    for k, v in data.items():
        if k in rejected:
            continue

        setattr(state, k, v)

    state.save()
    return jsonify(state.to_dict()), 200
